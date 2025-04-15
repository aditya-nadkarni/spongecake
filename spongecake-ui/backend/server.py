import logging
import os
import subprocess
import sys
import threading
import queue
import time
import uuid
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple, Any, Union

from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
from marshmallow import ValidationError
from spongecake import Desktop, AgentStatus
from dotenv import load_dotenv
import json 
# Import from local modules
from config import Config, setup_logging
from schemas import RequestSchemas
from utils import is_port_available, find_available_port, PortNotAvailableError

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()

# Custom logging handler that captures logs and sends them to a queue for streaming
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        # Define the format for log messages (module - level - message)
        self.formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

    def emit(self, record):
        # Format the log message according to our formatter
        formatted_msg = self.formatter.format(record)
        
        # Only capture logs from the Spongecake SDK modules (filtering)
        if record.name.startswith('spongecake'):
            # Print to console for debugging/monitoring
            print(f"CAPTURED LOG: {formatted_msg}")
            
            # Convert log to a standardized JSON format with type and message
            # This ensures all messages in the queue have a consistent structure
            log_data = {
                "type": "log",  # Identifies this as a log message (vs. result or complete)
                "message": formatted_msg + "\n"  # Add newline for better display
            }
            # Add the JSON-formatted log to the queue for streaming
            self.log_queue.put(json.dumps(log_data))


class SpongecakeServer:
    """Main server class for the Spongecake application."""

    def __init__(self, host: str = "0.0.0.0", port: int = Config.FLASK_PORT):
        """Initialize the server with Flask app and configuration."""
        self.app = Flask(__name__)
        # Dictionary to store active log streaming sessions
        self.active_sessions = {}
        self.active_threads = {}
        CORS(self.app)
        self.desktop = None
        self.novnc_port = None
        self.novnc_process = None
        self.host = host
        self.port = port
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Set up the API routes."""

        self.app.route("/api/start-container", methods=["POST"])(self.api_start_container)
        self.app.route("/api/run-agent", methods=["POST"])(self.api_run_agent)

        self.app.route("/api/logs/<session_id>", methods=["GET"])(self.stream_logs)
        self.app.route("/api/cancel-agent/<session_id>", methods=["POST"])(self.cancel_agent)
        self.app.route("/api/health", methods=["GET"])(self.health_check)
    
    def start_novnc_server(
        self,
        novnc_path: str = Config.NOVNC_PATH,
        port: Optional[int] = None,
        vnc_host: str = Config.VNC_HOST,
        vnc_port: Union[str, int] = "6080"
    ) -> Tuple[subprocess.Popen, int]:
        """Launch websockify with noVNC as a background process. The noVNC server is used so that the client can connect to it and view the desktop running in a Docker container
        
        Args:
            novnc_path: Path to the noVNC installation
            port: Optional port to use, will find an available one if None
            vnc_host: VNC host address
            vnc_port: VNC port number
            
        Returns:
            Tuple containing the process object and the port used
        """
        # Find an available port if none specified
        if port is None:
            port = find_available_port(Config.NOVNC_BASE_PORT, Config.MAX_PORT_ATTEMPTS)
        else:
            port = int(port)
            if not is_port_available(port):
                logger.warning(f"Port {port} is not available, finding another one")
                port = find_available_port(Config.NOVNC_BASE_PORT, Config.MAX_PORT_ATTEMPTS)
        
        cmd = [
            "python", "-m", "websockify",
            "--web", novnc_path,
            str(port),
            f"{vnc_host}:{vnc_port}"
        ]
        
        try:
            process = subprocess.Popen(cmd)
            logger.info(f"NoVNC process started on port {port} (PID={process.pid})")
            return process, port
        except Exception as e:
            logger.error(f"Failed to start noVNC server: {e}")
            raise
    
    def start_container_if_needed(self, host="", logs: Optional[List[str]] = None) -> Tuple[List[str], int]:
        """Creates a Desktop() object if we don't already have one and starts the container + noVNC server.
        
        Args:
            logs: Optional list to append log messages to
            
        Returns:
            Tuple containing logs and the noVNC port
        """
        if logs is None:
            logs = []
        
        try:
            # 1) Start the Spongecake Desktop container
            self.desktop = Desktop(name=Config.CONTAINER_NAME, host=host if host != '' else None)
            container = self.desktop.start()
            logs.append(f"🍰 Container started: {container}")
            logger.info(f"🍰 Container started: {container}")
            
            # 2) Start noVNC with dynamic port allocation
            self.novnc_process, self.novnc_port = self.start_novnc_server(
                vnc_port=str(self.desktop.vnc_port)
            )
            
            logs.append(
                f"Started noVNC server on http://localhost:{self.novnc_port}/vnc.html "
                f"with vnc_port {self.desktop.vnc_port}"
            )
            logger.info(
                f"Started noVNC server on http://localhost:{self.novnc_port}/vnc.html "
                f"with vnc_port {self.desktop.vnc_port}"
            )
            
            return logs, self.novnc_port
            
        except Exception as e:
            error_msg = f"Failed to start container: {e}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            logs.append(f"❌ {error_msg}")
            return logs, None

    
    # -------------------------
    # Handlers for desktop agent statuses
    # There are four handlers so that developers can customize how to handle the different statuses:
    # complete_handler: Checks if the agent is complete and returns the result
    # needs_input_handler: Returns user input to the front-end (same as above)
    # needs_safety_check_handler: Checks if the agent needs a safety check, and returns an object with a pendingSafetyCheck flag set to true
    # error_handler: Handles any errors in agent execution
    # -------------------------
    result = [None]

    def complete_handler(self, data):
        """COMPLETE -- Handle successful task data (just print out success message in this case)"""
        for msg in data.output:
            if hasattr(msg, "content"):
                text_parts = [part.text for part in msg.content if hasattr(part, "text")]
                self.result[0] = text_parts
        
    def needs_input_handler(self, messages):
        """NEEDS_INPUT -- Get input from the user, and pass it back to `action`"""
        for msg in messages:
            if hasattr(msg, "content"):
                text_parts = [part.text for part in msg.content if hasattr(part, "text")]
                self.result[0] = text_parts

    def needs_safety_check_handler(self, safety_checks, pending_call):
        # Check if the user has already acknowledged safety checks (set this flag in run_agent_action)
        if getattr(self, "safety_ack", False):
            # Instead of calling pending_call(True) (which relies on a callback you don't have),
            # just return True to indicate that it's okay to continue.
            return True

        # Otherwise, capture the safety check messages to relay them to the front-end:
        safety_messages = [check.message for check in safety_checks if hasattr(check, "message")]
        self.result[0] = [{"pendingSafetyCheck": True, "messages": safety_messages}] # safety_messages
        # Returning False tells the agent to wait until safety checks are acknowledged
        return False

    def error_handler(self, error_message):
        """ERROR -- Handle errors (just print it out in this case)"""
        print(f"😱 ERROR: {error_message}")
        self.result[0] = None  # Just return None on error

    def run_agent_action(self, user_prompt: str, auto_mode: bool = False, safety_ack: bool = False, log_queue=None, stop_event=None) -> Dict[str, Any]:
        """Run the agent logic in the Spongecake Desktop.
        
        Args:
            user_prompt: The user's prompt to the agent
            auto_mode: Whether to run in auto mode (ignore safety checks)
            safety_ack: Whether safety checks have been acknowledged
            log_queue: Queue to send logs to for streaming
            
        Returns:
            Dictionary containing logs and agent response
        """
        logs = []
        
        # We don't need to manually add logs to the queue anymore since
        # the QueueHandler will capture all Spongecake SDK logs automatically
        log_msg = "\n👾 Performing desktop action..."
        logs.append(log_msg)
        
        formatted_prompt = f"{user_prompt}\n{Config.DEFAULT_PROMPT_SUFFIX}"
        
        agent_response = None
        
        # Run the agent in auto or interactive mode
        try:
            # Create a wrapper for desktop.action that checks the stop_event
            def run_with_cancellation_check():
                # Run the agent action
                if auto_mode:
                    return self.desktop.action(input_text=formatted_prompt, ignore_safety_and_input=True, stop_event=stop_event)
                else:
                    return self.desktop.action(
                        input_text=formatted_prompt,
                        complete_handler=self.complete_handler,
                        needs_input_handler=self.needs_input_handler,
                        needs_safety_check_handler=self.needs_safety_check_handler,
                        acknowledged_safety_checks=safety_ack,
                        error_handler=self.error_handler,
                        stop_event=stop_event
                    )
            
            # Run the action with cancellation check
            status, data = run_with_cancellation_check()
            
            if status == AgentStatus.ERROR:
                log_msg = f"❌ Error in agent action: {data}"
                logs.append(log_msg)
                agent_response = None
            else:
                log_msg = f"✅ Agent status: {status}"
                logs.append(log_msg)
                
        except Exception as exc:
            error_msg = f"❌ Exception while running action: {exc}"
            logs.append(error_msg)
            logger.error(error_msg, exc_info=True)
        
        log_msg = "Done.\n"
        logs.append(log_msg)
        agent_response = self.result[0]

        if (isinstance(agent_response, list) and agent_response and 
            isinstance(agent_response[0], dict) and agent_response[0].get("pendingSafetyCheck")):
            # Safety check is pending, return that directly as a JSON string.
            return {
                "logs": logs,
                "agent_response": json.dumps({
                    'pendingSafetyCheck': True,
                    'messages': ["We've spotted something that might cause the agent to behave unexpectedly! Please acknowledge this to proceed.\n\n > *Type 'ack' to acknowledge and proceed.*"]
                })
            }
        else:
            # Otherwise, return the standard agent response.
            return {
                "logs": logs,
                "agent_response": agent_response[0]
        }

    def api_start_container(self):
        """API endpoint to start the container and noVNC server.
        
        Returns:
            JSON response with logs and noVNC port
        """
        data = request.get_json()
        host = data.get("host", "")
        logs, port = self.start_container_if_needed(host)
        return jsonify({
            "logs": logs,
            "novncPort": port
        })
    
    def stream_logs(self, session_id):
        """Stream logs for a specific session using Server-Sent Events (SSE).
        
        This endpoint establishes a persistent connection with the client and
        streams log messages in real-time as they are generated by the agent, 
        so the client can see the agent's actions in real time.
        
        Args:
            session_id: The unique session ID to stream logs for
            
        Returns:
            A streaming SSE response with logs formatted as JSON
        """
        # Verify the session exists before attempting to stream logs
        if session_id not in self.active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        # Get the queue associated with this session
        log_queue = self.active_sessions[session_id]
        
        # Generator function that yields log messages as SSE events
        def generate():
            while True:
                try:
                    # Try to get a message from the queue with a 1-second timeout
                    # This allows us to periodically send heartbeats if no logs are available
                    msg = log_queue.get(timeout=1)
                    
                    try:
                        # Parse the message as JSON (all our messages should be JSON)
                        parsed_msg = json.loads(msg)
                        
                        # Check if this is the end of the stream signal
                        if parsed_msg.get("type") == "complete":
                            # Send the complete message and exit the generator
                            yield f"data: {msg}\n\n"
                            break
                        else:
                            # For all other message types (log, result), pass through as is
                            yield f"data: {msg}\n\n"
                    except:
                        # Log parsing errors but don't crash the stream
                        logger.error(f"Error parsing log message: {msg}")
                        
                except queue.Empty:
                    # If no messages in queue for 1 second, send a heartbeat
                    # This keeps the connection alive and prevents timeouts
                    yield "data: {\"type\": \"heartbeat\"}\n\n"
        
        # Create a streaming response with proper SSE headers
        response = Response(stream_with_context(generate()), 
                           content_type='text/event-stream')
        # Disable caching to ensure real-time updates
        response.headers['Cache-Control'] = 'no-cache'
        # Disable buffering for Nginx (if used)
        response.headers['X-Accel-Buffering'] = 'no'
        return response

    def api_run_agent(self):
        """API endpoint to run an agent action.
        
        Returns:
            JSON response with logs, agent response, and noVNC port
        """
        try:
            # Validate request data
            schema = RequestSchemas.AgentRequestSchema()
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
                
            try:
                validated_data = schema.load(data)
            except ValidationError as err:
                return jsonify({"error": err.messages}), 400
            
            messages = validated_data.get("messages", "")
            auto_mode = validated_data.get("auto_mode", False)
            safety_ack = validated_data.get("safety_acknowledged", False)
            
            # Create a new session for log streaming
            session_id = str(uuid.uuid4())
            log_queue = queue.Queue()
            self.active_sessions[session_id] = log_queue

            # Create a stop event for cancellation
            stop_event = threading.Event()
            
            # Start agent action in a background thread
            thread = threading.Thread(
                    target=self._run_agent_in_thread,
                    args=(messages, auto_mode, safety_ack, log_queue, session_id, stop_event)
                )
            try:
                thread.daemon = True
                thread.start()
                # Store both the thread and the stop_event for cancellation
                self.active_threads[session_id] = {
                    'thread': thread,
                    'stop_event': stop_event
                }
            except Exception as e:
                print("\n------\n PROCESS STOPPED \n------\n")
                # thread.stop() is not a standard method, use stop_event instead
                stop_event.set()
            
            # Return session ID to frontend for connecting to log stream
            return jsonify({
                "session_id": session_id,
                "novncPort": self.novnc_port
            })
            
        except Exception as e:
            logger.error(f"Error in api_run_agent: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500
            
    def _run_agent_in_thread(self, messages, auto_mode, safety_ack, log_queue, session_id, stop_event=None):
        """Run agent action in a background thread and stream logs."""
        # Set up log capture for all Spongecake SDK modules
        # This captures logs from both spongecake.desktop and spongecake.agent
        queue_handler = QueueHandler(log_queue)
        
        # Get the root logger to capture all logs
        root_logger = logging.getLogger()
        
        # Store original handlers and level to restore later
        original_handlers = root_logger.handlers.copy()
        original_level = root_logger.level
        
        # Set to DEBUG level to capture all logs
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(queue_handler)
        
        # Also set specific loggers to DEBUG level
        logging.getLogger('spongecake').setLevel(logging.DEBUG)
        logging.getLogger('spongecake.desktop').setLevel(logging.DEBUG)
        logging.getLogger('spongecake.agent').setLevel(logging.DEBUG)
        
        # Send an initial log message
        log_queue.put("Starting Spongecake agent action...")
        print("Starting Spongecake agent action...")
        
        try:
            # Run the agent action
            result = self.run_agent_action(
                messages, 
                auto_mode=auto_mode, 
                safety_ack=safety_ack,
                log_queue=log_queue,
                stop_event=stop_event
            )
            
            # Send the final result to the log queue as a JSON string
            # The 'type' field identifies this as a result message (vs. log or complete)
            # The 'data' field contains the actual agent response data
            result_json = json.dumps({
                "type": "result",
                "data": result  # Contains agent_response and any other result data
            })
            log_queue.put(result_json)
            
        except Exception as e:
            # Log the error and send it to the client
            error_msg = f"Error in agent thread: {str(e)}"
            logger.exception(error_msg)
            
            # First send the error as a log message for debugging purposes
            # This will show up in the log stream with type 'log'
            log_queue.put(json.dumps({
                "type": "log",
                "message": error_msg  # Detailed error message for debugging
            }))
            
            # Then send a formal error result that the frontend can handle
            # This has type 'result' so the frontend knows it's the final response
            log_queue.put(json.dumps({
                "type": "result",
                "data": {
                    "error": error_msg,  # Technical error details 
                    "agent_response": f"Error: {str(e)}"  # User-friendly error message
                }
            }))
            
        finally:
            # Print information about logs captured
            print("\n==== FINISHED CAPTURING LOGS ====")
            
            # Restore original log level and handlers
            root_logger.setLevel(original_level)
            root_logger.removeHandler(queue_handler)
            
            # Restore original handlers if they were removed
            for handler in original_handlers:
                if handler not in root_logger.handlers:
                    root_logger.addHandler(handler)
                    
            print("Restored original logger configuration")
            
            # Signal the end of the stream with a special 'complete' message
            # This tells the frontend that no more logs or results will be coming
            # The stream_logs generator will break its loop when it sees this message
            log_queue.put(json.dumps({
                "type": "complete", 
                "message": "Task completed"
            }))
            
            # Clean up after a delay to ensure all messages are processed
            def cleanup_session():
                time.sleep(60)  # Keep session alive for 1 minute after completion
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
            
            cleanup_thread = threading.Thread(target=cleanup_session)
            cleanup_thread.daemon = True
            cleanup_thread.start()
    
    def cancel_agent(self, session_id):
        """API endpoint to cancel a running agent action.
        
        Args:
            session_id: The session ID of the agent action to cancel
            
        Returns:
            JSON response with cancellation status
        """
        logger.info(f"Received cancellation request for session {session_id}")  
        
        # Check if the session exists
        if session_id not in self.active_sessions:
            return jsonify({"error": "Session not found"}), 404
            
        # Get the log queue for this session
        log_queue = self.active_sessions[session_id]
        
        # Send cancellation message to the log stream
        log_queue.put(json.dumps({
            "type": "log",
            "message": "Cancellation requested by user\n"
        }))
        
        # Trigger the stop event to halt the thread execution
        if session_id in self.active_threads:
            logger.info(f"Setting stop event for session {session_id}")
            thread_info = self.active_threads[session_id]
            if 'stop_event' in thread_info:
                thread_info['stop_event'].set()
                
                # Wait a short time for the thread to respond to the stop event
                if 'thread' in thread_info:
                    thread = thread_info['thread']
                    thread.join(timeout=0.5)  # Wait up to 0.5 seconds for the thread to finish
                    
                    # Log whether the thread actually stopped
                    if thread.is_alive():
                        logger.warning(f"Thread for session {session_id} is still running after stop event")
                    else:
                        logger.info(f"Thread for session {session_id} successfully stopped")
        
        # Send a result indicating cancellation
        log_queue.put(json.dumps({
            "type": "result",
            "data": {"agent_response": "Agent action cancelled by user"}
        }))
        
        # Signal end of stream
        log_queue.put(json.dumps({
            "type": "complete", 
            "message": "Task cancelled"
        }))
        
        # Clean up the session
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.active_threads:
            del self.active_threads[session_id]
        
        logger.info(f"Agent action cancelled for session {session_id}")
        
        return jsonify({
            "status": "success",
            "message": "Agent action cancelled"
        })
    
    def health_check(self):
        """API endpoint to check the health of the server.
        
        Returns:
            JSON response with server status
        """
        status = {
            "status": "healthy",
            "container_running": self.desktop is not None,
            "novnc_port": self.novnc_port
        }
        return jsonify(status)

    def cleanup(self):
        """Clean up resources when the server is shutting down."""
        logger.info("Cleaning up resources...")
        
        if self.novnc_process:
            try:
                self.novnc_process.terminate()
                logger.info(f"Terminated noVNC process (PID={self.novnc_process.pid})")
            except Exception as e:
                logger.error(f"Error terminating noVNC process: {e}")
        
        if self.desktop:
            try:
                self.desktop.stop()
                logger.info("Stopped desktop container")
            except Exception as e:
                logger.error(f"Error stopping desktop container: {e}")
    
    def run(self):
        """Run the Flask server."""
        try:
            logger.info(f"Starting Spongecake server on {self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=True)
        finally:
            self.cleanup()


# Create a server instance when this module is imported
server = SpongecakeServer()

if __name__ == "__main__":
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    finally:
        server.cleanup()
