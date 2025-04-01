import logging
import logging.config
import os
import socket
import subprocess
import sys
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple, Any, Union

from flask import Flask, jsonify, request
from flask_cors import CORS
from marshmallow import Schema, fields, ValidationError
from spongecake import Desktop, AgentStatus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spongecake_server.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class PortNotAvailableError(Exception):
    """Raised when a port is not available after multiple attempts."""
    pass


class Config:
    """Configuration settings for the Spongecake server."""
    NOVNC_BASE_PORT = 6080
    NOVNC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "noVNC-1.6.0")
    VNC_HOST = "localhost"
    FLASK_PORT = 5000
    CONTAINER_NAME = "computer_use_agent"
    MAX_PORT_ATTEMPTS = 100
    DEFAULT_PROMPT_SUFFIX = """
    If a user mentioned going to a website, always start by trying to go directly to the URL or using Bing instead of going to Google first.
    """


class RequestSchemas:
    """Request validation schemas for API endpoints."""
    
    class AgentRequestSchema(Schema):
        """Schema for agent action requests."""
        messages = fields.String(required=True)
        auto_mode = fields.Boolean(default=False)


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
        # v1 API endpoints
        self.app.route("/api/v1/start-container", methods=["POST"])(self.api_start_container)
        self.app.route("/api/v1/run-agent", methods=["POST"])(self.api_run_agent)
        self.app.route("/api/v1/health", methods=["GET"])(self.health_check)
        
        # For backward compatibility
        self.app.route("/api/start-container", methods=["POST"])(self.api_start_container)
        self.app.route("/api/run-agent", methods=["POST"])(self.api_run_agent)
        self.app.route("/api/health", methods=["GET"])(self.health_check)
    
    def is_port_available(self, port: int) -> bool:
        """Check if a port is available with proper socket configuration.
        
        Args:
            port: The port number to check
            
        Returns:
            bool: True if the port is available, False otherwise
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.bind(("0.0.0.0", int(port)))
                # Also check if we can connect to it
                s.listen(1)
                return True
            except (OSError, socket.error):
                return False
    
    def find_available_port(self, start_port: int = Config.NOVNC_BASE_PORT) -> int:
        """Find an available port starting from start_port.
        
        Args:
            start_port: The port number to start checking from
            
        Returns:
            int: An available port number
            
        Raises:
            PortNotAvailableError: If no available port is found after max attempts
        """
        current_port = start_port
        for _ in range(Config.MAX_PORT_ATTEMPTS):
            if self.is_port_available(current_port):
                return current_port
            current_port += 1
        
        error_msg = f"Could not find an available port after {Config.MAX_PORT_ATTEMPTS} attempts"
        logger.error(error_msg)
        raise PortNotAvailableError(error_msg)
    
    def start_novnc_server(
        self,
        novnc_path: str = Config.NOVNC_PATH,
        port: Optional[int] = None,
        vnc_host: str = Config.VNC_HOST,
        vnc_port: Union[str, int] = "5900"
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
            port = self.find_available_port()
        else:
            port = int(port)
            if not self.is_port_available(port):
                logger.warning(f"Port {port} is not available, finding another one")
                port = self.find_available_port()
        
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
        
        if self.desktop is not None:
            logs.append("Container already started.")
            return logs, self.novnc_port
        
        try:
            # 1) Start the Spongecake Desktop container
            self.desktop = Desktop(name=Config.CONTAINER_NAME)
            container = self.desktop.start()
            logs.append(f"🍰 Container started: {container}")
            
            # 2) Start noVNC with dynamic port allocation
            self.novnc_process, self.novnc_port = self.start_novnc_server(
                vnc_port=str(self.desktop.vnc_port)
            )
            
            logs.append(
                f"Started noVNC server on http://localhost:{self.novnc_port}/vnc.html "
                f"with vnc_port {self.desktop.vnc_port}"
            )
            
            return logs, self.novnc_port
            
        except Exception as e:
            error_msg = f"Failed to start container: {e}"
            logger.error(error_msg, exc_info=True)
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
