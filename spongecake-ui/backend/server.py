import logging
import os
import subprocess
import sys
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple, Any, Union

from flask import Flask, jsonify, request
from flask_cors import CORS
from marshmallow import ValidationError
from spongecake import Desktop, AgentStatus
from dotenv import load_dotenv

# Import from local modules
from config import Config, setup_logging
from schemas import RequestSchemas
from utils import is_port_available, find_available_port, PortNotAvailableError

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()


class SpongecakeServer:
    """Main server class for the Spongecake application."""

    def __init__(self, host: str = "0.0.0.0", port: int = Config.FLASK_PORT):
        """Initialize the server with Flask app and configuration."""
        self.app = Flask(__name__)
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
        self.app.route("/api/health", methods=["GET"])(self.health_check)
    

    
    def start_novnc_server(
        self,
        novnc_path: str = Config.NOVNC_PATH,
        port: Optional[int] = None,
        vnc_host: str = Config.VNC_HOST,
        vnc_port: Union[str, int] = "6080"
    ) -> Tuple[subprocess.Popen, int]:
        """Launch websockify with noVNC as a background process.
        
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
    
    def start_container_if_needed(self, logs: Optional[List[str]] = None) -> Tuple[List[str], int]:
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
            self.desktop = Desktop(name=Config.CONTAINER_NAME)
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

    def run_agent_action(self, user_prompt: str, auto_mode: bool = False) -> Dict[str, Any]:
        """Run the agent logic in the Spongecake Desktop.
        
        Args:
            user_prompt: The user's prompt to the agent
            auto_mode: Whether to run in auto mode (ignore safety checks)
            
        Returns:
            Dictionary containing logs and agent response
        """
        logs = []
        
        # Ensure container is running
        logs, _ = self.start_container_if_needed(logs)
        
        logs.append("\n👾 Performing desktop action...")
        
        formatted_prompt = f"{user_prompt}\n{Config.DEFAULT_PROMPT_SUFFIX}"
        
        agent_response = None
        
        # Run the agent in auto or interactive mode
        try:
            if auto_mode:
                status, data = self.desktop.action(input_text=formatted_prompt, ignore_safety_and_input=True)
            else:
                status, data = self.desktop.action(input_text=formatted_prompt, ignore_safety_and_input=False)
            
            if status == AgentStatus.ERROR:
                logs.append(f"❌ Error in agent action: {data}")
                agent_response = None
            else:
                logs.append(f"✅ Agent status: {status}")
                agent_response = str(data[0].content[0].text)
                
        except Exception as exc:
            error_msg = f"❌ Exception while running action: {exc}"
            logs.append(error_msg)
            logger.error(error_msg, exc_info=True)
        
        logs.append("Done.\n")
        
        return {
            "logs": logs,
            "agent_response": agent_response
        }

    def api_start_container(self):
        """API endpoint to start the container and noVNC server.
        
        Returns:
            JSON response with logs and noVNC port
        """
        logs, port = self.start_container_if_needed()
        return jsonify({
            "logs": logs,
            "novncPort": port
        })
    
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
            
            # Run the agent action
            result = self.run_agent_action(messages, auto_mode)
            
            # Include the noVNC port in the response
            result["novncPort"] = self.novnc_port
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in api_run_agent: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500
    
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
