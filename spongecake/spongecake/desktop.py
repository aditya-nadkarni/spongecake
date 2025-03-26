import docker
from docker.errors import NotFound, ImageNotFound, APIError
import requests
import socket
import time
import base64
import logging
import warnings
from openai import OpenAI
from .constants import AgentStatus

# Set up logger
logger = logging.getLogger(__name__)

import os
import requests
import subprocess  # Import subprocess module

from . import _exceptions
from .agent import Agent

# -------------------------
# Container Management Functions
# -------------------------
class Desktop:
    """
    Desktop class for managing a Docker container with a virtual desktop environment.
    
    The Desktop class handles container lifecycle (start, stop), and provides methods
    to interact with the desktop environment (click, type, scroll, etc.).
    
    Port handling:
    - Container ports are fixed at 5900 for VNC and 8000 for API
    - Local ports start at the specified values (default: 5900 for VNC, 8000 for API)
    - If a port conflict is detected during container startup, the system will
      automatically increment the port number and retry until an available port is found
    - This reactive approach handles concurrent situations where a port becomes
      unavailable between the initial check and the actual container startup
    """

    def __init__(self, name: str = "newdesktop", docker_image: str = "spongebox/spongecake:latest", vnc_port: int = 5900, api_port: int = 8000, marionette_port: int = 3838, socat_port: int = 2828, host: str = None, openai_api_key: str = None, create_agent: bool = True):
        """
        Initialize a new Desktop instance.
        
        Args:
            name: Name for the Docker container
            docker_image: Docker image to use for the container
            vnc_port: Starting local port for VNC (will auto-increment if in use during container startup)
            api_port: Starting local port for API (will auto-increment if in use during container startup)
            marionette_port: Starting local port for Marionette (will auto-increment if in use during container startup)
            socat_port: Starting local port for Socat (will auto-increment if in use during container startup)
            host: Hostname or IP address to connect to the API (default: localhost)
            openai_api_key: OpenAI API key for agent functionality
            create_agent: Whether to create an agent instance automatically
        """
        # Set container info
        self.container_name = name  # Set container name for use in methods
        self.docker_image = docker_image # Set image name to start container
        self.display = ":99"

        # Set up access ports
        self.vnc_port = vnc_port
        self.api_port = api_port
        self.marionette_port = marionette_port
        self.socat_port = socat_port
        self.host = host
        
        # API base URL will be set after container starts and ports are finalized
        self._update_api_base_url()

        # Create a Docker client from environment
        self.docker_client = docker.from_env()

        # Ensure OpenAI API key is available to use
        if openai_api_key is None:
            openai_api_key = os.environ.get("OPENAI_API_KEY")
        if openai_api_key is None:
            raise _exceptions.SpongecakeException("The openai_api_key client option must be set either by passing openai_api_key to the client or by setting the OPENAI_API_KEY environment variable")
        self.openai_api_key = openai_api_key

        # Set up OpenAI API key
        self.openai_client = OpenAI(api_key=openai_api_key)
        
        # Initialize agent if requested
        self._agent = None
        if create_agent:
            self._agent = Agent(desktop=self, openai_api_key=openai_api_key)

    def _increment_port(self, port):
        """
        Increment the port number by 1.
        
        Args:
            port: The port number to increment
            
        Returns:
            int: The incremented port number
        """
        port += 1
        if port > 65535:  # Maximum port number
            raise RuntimeError("No available ports found")
        return port
        
    def _update_api_base_url(self):
        """
        Update the API base URL based on current host and port.
        Should be called whenever api_port changes.
        If host is None, API calls will not be attempted.
        """
        if self.host is not None:
            self.api_base_url = f"http://{self.host}:{self.api_port}"
        else:
            self.api_base_url = None
        
    def start(self):
        """
        Starts the container if it's not already running.
        Maps the VNC port, API port, Marionette port, and Socat port. If the specified ports are in use,
        it will find available ports by incrementing the port number.
        
        Docker container always uses ports:
        - 5900 for VNC
        - 8000 for API
        - 2828 for Marionette
        - 2829 for Socat
        """
        # Hardcoded container ports
        CONTAINER_VNC_PORT = 5900
        CONTAINER_API_PORT = 8000
        CONTAINER_MARIONETTE_PORT = 2828
        CONTAINER_SOCAT_PORT = 2829
        
        try:
            # Check to see if the container already exists
            container = self.docker_client.containers.get(self.container_name)
            logger.info(f"⏰ Container '{self.container_name}' found with status '{container.status}'.")

            # If it's not running, start it
            if container.status != "running":
                logger.info(f"Container '{self.container_name}' is not running. Starting...")
                container.start()
            else:
                logger.info(f"Container '{self.container_name}' is already running.")

        except NotFound:
            # The container does not exist yet. Create it and pull the image first.
            logger.info(f"⏰ Creating and starting a new container '{self.container_name}'...")

            # Always attempt to pull the latest version of the image
            try:
                self.docker_client.images.pull(self.docker_image)
            except APIError as e:
                logger.warning("Failed to pull image. Attempting to start container...")

            # Try running a new container from the (hopefully just-pulled) image
            max_retries = 10  # Maximum number of retries for port conflicts
            retries = 0
            
            while retries < max_retries:
                try:
                    container = self.docker_client.containers.run(
                        self.docker_image,
                        detach=True,
                        name=self.container_name,
                        ports={
                            f"{CONTAINER_VNC_PORT}/tcp": self.vnc_port,
                            f"{CONTAINER_API_PORT}/tcp": self.api_port,
                            f"{CONTAINER_MARIONETTE_PORT}/tcp": self.marionette_port,
                            f"{CONTAINER_SOCAT_PORT}/tcp": self.socat_port,
                        }
                    )
                    # If we get here, the container started successfully
                    break
                    
                except APIError as e:
                    error_message = str(e)
                    if ("driver failed programming external connectivity on endpoint" in error_message and 
                        "port is already allocated" in error_message):
                        # Port conflict detected
                        if "0.0.0.0:" + str(self.vnc_port) in error_message:
                            # VNC port conflict
                            old_port = self.vnc_port
                            self.vnc_port = self._increment_port(self.vnc_port)
                            logger.info(f"VNC port {old_port} is in use, trying port {self.vnc_port}")
                        elif "0.0.0.0:" + str(self.api_port) in error_message:
                            # API port conflict
                            old_port = self.api_port
                            self.api_port = self._increment_port(self.api_port)
                            logger.info(f"API port {old_port} is in use, trying port {self.api_port}")
                        elif "0.0.0.0:" + str(self.marionette_port) in error_message:
                            # Marionette port conflict
                            old_port = self.marionette_port
                            self.marionette_port = self._increment_port(self.marionette_port)
                            logger.info(f"Marionette port {old_port} is in use, trying port {self.marionette_port}")
                        elif "0.0.0.0:" + str(self.socat_port) in error_message:
                            # Socat port conflict
                            old_port = self.socat_port
                            self.socat_port = self._increment_port(self.socat_port)
                            logger.info(f"Socat port {old_port} is in use, trying port {self.socat_port}")
                        else:
                            # Unknown port conflict, increment all ports
                            old_vnc = self.vnc_port
                            old_api = self.api_port
                            old_marionette = self.marionette_port
                            old_socat = self.socat_port
                            self.vnc_port = self._increment_port(self.vnc_port)
                            self.api_port = self._increment_port(self.api_port)
                            self.marionette_port = self._increment_port(self.marionette_port)
                            self.socat_port = self._increment_port(self.socat_port)
                            logger.info(f"Port conflict detected, trying new ports: VNC={self.vnc_port}, API={self.api_port}, Marionette={self.marionette_port}, Socat={self.socat_port}")
                        
                        # Increment retry counter
                        retries += 1
                        
                        # If we've reached the container name already exists, remove it
                        try:
                            existing = self.docker_client.containers.get(self.container_name)
                            existing.remove(force=True)
                            logger.info(f"Removed existing container '{self.container_name}'")
                        except NotFound:
                            pass
                    else:
                        # Other API error, not port-related
                        raise
                        
                except ImageNotFound:
                    # If for some reason the image is still not found locally,
                    # try pulling again explicitly and run once more.
                    logger.info(f"Pulling image '{self.docker_image}' now...")
                    try:
                        self.docker_client.images.pull(self.docker_image)
                    except APIError as e:
                        raise RuntimeError(
                            f"Failed to find or pull image '{self.docker_image}'. Unable to start container."
                            f"Docker reported: {str(e)}"
                        ) from e

                    # Try one more time after pulling, but still handle potential port conflicts
                    try:
                        container = self.docker_client.containers.run(
                            self.docker_image,
                            detach=True,
                            name=self.container_name,
                            ports={
                                f"{CONTAINER_VNC_PORT}/tcp": self.vnc_port,
                                f"{CONTAINER_API_PORT}/tcp": self.api_port,
                                f"{CONTAINER_MARIONETTE_PORT}/tcp": self.marionette_port,
                                f"{CONTAINER_SOCAT_PORT}/tcp": self.socat_port,
                            }
                        )
                        break  # Success, exit the retry loop
                    except APIError as port_error:
                        # Check if this is a port conflict error
                        error_message = str(port_error)
                        if ("driver failed programming external connectivity on endpoint" in error_message and 
                            "port is already allocated" in error_message):
                            # Handle port conflicts the same way as in the main loop
                            if "0.0.0.0:" + str(self.vnc_port) in error_message:
                                old_port = self.vnc_port
                                self.vnc_port = self._increment_port(self.vnc_port)
                                logger.info(f"VNC port {old_port} is in use, trying port {self.vnc_port}")
                            elif "0.0.0.0:" + str(self.api_port) in error_message:
                                old_port = self.api_port
                                self.api_port = self._increment_port(self.api_port)
                                logger.info(f"API port {old_port} is in use, trying port {self.api_port}")
                            elif "0.0.0.0:" + str(self.marionette_port) in error_message:
                                old_port = self.marionette_port
                                self.marionette_port = self._increment_port(self.marionette_port)
                                logger.info(f"Marionette port {old_port} is in use, trying port {self.marionette_port}")
                            elif "0.0.0.0:" + str(self.socat_port) in error_message:
                                old_port = self.socat_port
                                self.socat_port = self._increment_port(self.socat_port)
                                logger.info(f"Socat port {old_port} is in use, trying port {self.socat_port}")
                            else:
                                # Unknown port conflict, increment all ports
                                old_vnc = self.vnc_port
                                old_api = self.api_port
                                old_marionette = self.marionette_port
                                old_socat = self.socat_port
                                self.vnc_port = self._increment_port(self.vnc_port)
                                self.api_port = self._increment_port(self.api_port)
                                self.marionette_port = self._increment_port(self.marionette_port)
                                self.socat_port = self._increment_port(self.socat_port)
                                logger.info(f"Port conflict detected, trying new ports: VNC={self.vnc_port}, API={self.api_port}, Marionette={self.marionette_port}, Socat={self.socat_port}")
                            
                            # Increment retry counter
                            retries += 1
                            
                            # If we've reached the container name already exists, remove it
                            try:
                                existing = self.docker_client.containers.get(self.container_name)
                                existing.remove(force=True)
                                logger.info(f"Removed existing container '{self.container_name}'")
                            except NotFound:
                                pass
                        else:
                            # Other API error, not port-related
                            raise
            
            if retries >= max_retries:
                raise RuntimeError(f"Failed to start container after {max_retries} attempts due to port conflicts")
            
            # Update API base URL with the final port
            self._update_api_base_url()

            logger.info(f"🍰 spongecake container started: {container}    (VNC PORT: {self.vnc_port}; API PORT: {self.api_port}; Marionette PORT: {self.marionette_port}; Socat PORT: {self.socat_port})")
        # Give the container a brief moment to initialize its services
        time.sleep(2)
        return container

    def stop(self):
        """
        Stops and removes the container.
        """
        try:
            container = self.docker_client.containers.get(self.container_name)
            container.stop()
            container.remove()
            logger.info(f"Container '{self.container_name}' stopped and removed.")
        except docker.errors.NotFound:
            logger.info(f"Container '{self.container_name}' not found.")

    # -------------------------
    # DESKTOP ACTIONS
    # -------------------------

    # ----------------------------------------------------------------
    # RUN COMMANDS IN DESKTOP
    # ----------------------------------------------------------------
    def exec(self, command):
        # Wrap docker exec
        container = self.docker_client.containers.get(self.container_name)
        # Use /bin/sh -c to execute shell commands
        result = container.exec_run(["/bin/sh", "-c", command], stdout=True, stderr=True)
        if result.output:
            logger.debug(f"Command Output: {result.output.decode()}")

        return {
            "result": result.output.decode() if result.output else "",
            "returncode": result.exit_code
        }
        
    def _call_api_with_fallback(self, endpoint, method="post", json_data=None, fallback_cmd=None):
        """
        Call the API endpoint with fallback to exec if the API call fails.
        If host is None, directly use exec without attempting API call.
        
        Args:
            endpoint: API endpoint to call (e.g., '/action')
            method: HTTP method to use (default: 'post')
            json_data: JSON data to send with the request
            fallback_cmd: Command to execute if the API call fails
            
        Returns:
            API response or exec result
        """
        # If host is None or fallback_cmd is provided, use exec directly
        if self.host is None:
            if fallback_cmd:
                logger.debug(f"Host is None, using exec directly: {fallback_cmd}")
                return self.exec(fallback_cmd)
            else:
                raise RuntimeError("No host specified for API call and no fallback command provided")
        
        # Otherwise try API call with fallback to exec
        url = f"{self.api_base_url}{endpoint}"
        logger.debug(f"Calling API: {url} with data: {json_data}")
        
        try:
            if method.lower() == "post":
                response = requests.post(url, json=json_data, timeout=10)
            elif method.lower() == "get":
                response = requests.get(url, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.json()
            
        except (requests.RequestException, ValueError) as e:
            logger.warning(f"API call failed, falling back to exec: {str(e)}")
            if fallback_cmd:
                return self.exec(fallback_cmd)
            else:
                raise RuntimeError(f"API call failed and no fallback command provided: {str(e)}")

    # ----------------------------------------------------------------
    # CLICK
    # ----------------------------------------------------------------
    def click(self, x: int, y: int, click_type: str = "left"):
        """
        Move the mouse to (x, y) and click the specified button.
        click_type can be 'left', 'middle', or 'right'.
        """
        logger.info(f"Action: click at ({x}, {y}) with button '{click_type}'")
        
        # Prepare API request data
        json_data = {"type": "click", "x": x, "y": y, "button": click_type}
        
        # Prepare fallback command
        click_type_map = {"left": 1, "middle": 2, "wheel": 2, "right": 3}
        t = click_type_map.get(click_type.lower(), 1)
        fallback_cmd = f"export DISPLAY={self.display} && xdotool mousemove {x} {y} click {t}"
        
        # Call API with fallback
        return self._call_api_with_fallback(
            endpoint="/action",
            method="post",
            json_data=json_data,
            fallback_cmd=fallback_cmd
        )

    # ----------------------------------------------------------------
    # SCROLL
    # ----------------------------------------------------------------
    def scroll(self, x: int, y: int, scroll_x: int = 0, scroll_y: int = 0):
        """
        Move to (x, y) and scroll horizontally (scroll_x) or vertically (scroll_y).
        Negative scroll_y -> scroll up, positive -> scroll down.
        Negative scroll_x -> scroll left, positive -> scroll right (button 6 or 7).
        """
        logger.info(f"Action: scroll at ({x}, {y}) with offsets (scroll_x={scroll_x}, scroll_y={scroll_y})")
        
        # Prepare API request data
        json_data = {"type": "scroll", "x": x, "y": y, "scroll_x": scroll_x, "scroll_y": scroll_y}
        
        # Prepare fallback command
        fallback_cmds = [f"export DISPLAY={self.display} && xdotool mousemove {x} {y}"]
        
        # Vertical scroll (button 4 = up, button 5 = down)
        if scroll_y != 0:
            button = 4 if scroll_y < 0 else 5
            for _ in range(3):
                fallback_cmds.append(f"export DISPLAY={self.display} && xdotool click {button}")

        # Horizontal scroll (button 6 = left, button 7 = right)
        if scroll_x != 0:
            button = 6 if scroll_x < 0 else 7
            for _ in range(3):
                fallback_cmds.append(f"export DISPLAY={self.display} && xdotool click {button}")
        
        # Join fallback commands with semicolons
        fallback_cmd = " && ".join(fallback_cmds) if fallback_cmds else None
        
        # Call API with fallback
        return self._call_api_with_fallback(
            endpoint="/action",
            method="post",
            json_data=json_data,
            fallback_cmd=fallback_cmd
        )

    # ----------------------------------------------------------------
    # KEYPRESS
    # ----------------------------------------------------------------
    def keypress(self, keys: list[str]):
        """
        Press (and possibly hold) keys in sequence. Allows pressing
        Ctrl/Shift down, pressing other keys, then releasing them.
        Example: keys=["CTRL","F"] -> Ctrl+F
        """
        logger.info(f"Action: keypress with keys: {keys}")
        
        # Prepare API request data
        json_data = {"type": "keypress", "keys": keys}
        
        # Prepare fallback command
        fallback_cmds = []
        ctrl_pressed = False
        shift_pressed = False
        
        for k in keys:
            logger.info(f"  - key '{k}'")
            
            # Handle special modifiers
            if k.upper() == 'CTRL':
                logger.info("    => holding down CTRL")
                fallback_cmds.append(f"export DISPLAY={self.display} && xdotool keydown ctrl")
                ctrl_pressed = True
            elif k.upper() == 'SHIFT':
                logger.info("    => holding down SHIFT")
                fallback_cmds.append(f"export DISPLAY={self.display} && xdotool keydown shift")
                shift_pressed = True
            # Check special keys
            elif k.lower() == "enter":
                fallback_cmds.append(f"export DISPLAY={self.display} && xdotool key Return")
            elif k.lower() == "space":
                fallback_cmds.append(f"export DISPLAY={self.display} && xdotool key space")
            else:
                # For normal alphabetic or punctuation
                lower_k = k.lower()  # xdotool keys are typically lowercase
                fallback_cmds.append(f"export DISPLAY={self.display} && xdotool key '{lower_k}'")

        # Release modifiers
        if ctrl_pressed:
            logger.info("    => releasing CTRL")
            fallback_cmds.append(f"export DISPLAY={self.display} && xdotool keyup ctrl")
        if shift_pressed:
            logger.info("    => releasing SHIFT")
            fallback_cmds.append(f"export DISPLAY={self.display} && xdotool keyup shift")
            
        # Join fallback commands with semicolons
        fallback_cmd = " && ".join(fallback_cmds) if fallback_cmds else None
        
        # Call API with fallback
        return self._call_api_with_fallback(
            endpoint="/action",
            method="post",
            json_data=json_data,
            fallback_cmd=fallback_cmd
        )

    # ----------------------------------------------------------------
    # TYPE
    # ----------------------------------------------------------------
    def type_text(self, text: str):
        """
        Type a string of text (like using a keyboard) at the current cursor location.
        """
        logger.info(f"Action: type text: {text}")
        
        # Prepare API request data
        json_data = {"type": "type", "text": text}
        
        # Prepare fallback command
        fallback_cmd = f"export DISPLAY={self.display} && xdotool type '{text}'"
        
        # Call API with fallback
        return self._call_api_with_fallback(
            endpoint="/action",
            method="post",
            json_data=json_data,
            fallback_cmd=fallback_cmd
        )
    
    # ----------------------------------------------------------------
    # TAKE SCREENSHOT
    # ----------------------------------------------------------------
    def get_screenshot(self):
        """
        Takes a screenshot of the current desktop.
        Returns the base64-encoded PNG screenshot as a string.
        """
        logger.info("Action: take screenshot")
        
        # Prepare API request data
        json_data = {"type": "screenshot"}
        
        # Prepare fallback command
        fallback_cmd = f"export DISPLAY={self.display} && import -window root png:- | base64 -w 0"
        
        # Call API with fallback
        response = self._call_api_with_fallback(
            endpoint="/action",
            method="post",
            json_data=json_data,
            fallback_cmd=fallback_cmd
        )
        
        # Extract screenshot data from response
        if isinstance(response, dict) and "screenshot" in response:
            return response["screenshot"]
        elif isinstance(response, dict) and "result" in response:
            # If the response comes from the fallback command
            return response["result"]
        else:
            return None
    
    # ----------------------------------------------------------------
    # GOTO URL
    # ----------------------------------------------------------------
    def goto(self, url: str) -> None:
        """
        Open Firefox in the container and navigate to the specified URL.
        
        Args:
            url: The URL to navigate to (e.g., "https://example.com")
        """
        logger.info(f"Action: goto URL: {url}")
        # add `&` at the end to run Firefox in background and have `self.exec` return immediately
        command = f"export DISPLAY={self.display} && firefox-esr -new-tab {url} &"
        self.exec(command)

    # ----------------------------------------------------------------
    # WAIT
    # ----------------------------------------------------------------
    def wait(self, seconds: float = 2.0):
        """
        Wait for the specified number of seconds.
        """
        logger.info(f"Action: wait for {seconds} seconds")
        
        # Prepare API request data
        json_data = {"type": "wait", "seconds": seconds}
        
        # Prepare fallback command
        fallback_cmd = f"sleep {seconds}"
        
        # Call API with fallback
        return self._call_api_with_fallback(
            endpoint="/action",
            method="post",
            json_data=json_data,
            fallback_cmd=fallback_cmd
        )
    
    # -------------------------
    # Agent Integration
    # -------------------------
    
    def get_agent(self, create_if_none=True):
        """
        Get the agent associated with this desktop, or create one if it doesn't exist.
        
        Args:
            create_if_none: If True and no agent exists, create a new one
            
        Returns:
            An Agent instance
        """
        if self._agent is None and create_if_none:
            self._agent = Agent(desktop=self, openai_api_key=self.openai_api_key)
        return self._agent
    
    def set_agent(self, agent):
        """
        Set the agent for this desktop.
        
        Args:
            agent: An Agent instance
        """
        self._agent = agent
        if agent is not None:
            agent.set_desktop(self)

    def action_legacy(self, input=None, user_input=None, safety_checks=None, pending_call=None):
        """
        DEPRECATED wrapper for backwards compatibility.
        Translates old parameters to new 'action' signature.
        """
        warnings.warn(
            "action() with the old signature is deprecated and will be removed "
            "in a future release. Please use action() instead.",
            DeprecationWarning, 
            stacklevel=2
        )
        logger.warn(
            "action() with the old signature is deprecated and will be removed in a future release. Please use action() instead.",
        )

        # Translate old-style arguments into new-style ones
        input_text = user_input if user_input else input
        # If safety_checks is provided, we interpret that as acknowledged checks
        acknowledged_safety_checks = bool(safety_checks)
        # Decide if we're ignoring all checks
        ignore_safety_and_input = False

        # call the new function
        status, data = self.action(
            input_text=input_text,
            acknowledged_safety_checks=acknowledged_safety_checks,
            ignore_safety_and_input=ignore_safety_and_input,
            # Handlers can be passed in or left as None for the default behavior
        )

        # Convert the new function's return data back to the "old style" dict
        # so existing users still get what they're expecting
        if status == AgentStatus.COMPLETE:
            return {
                "result": data,             # old style calls this "result"
                "needs_input": [],
                "safety_checks": [],
                "pending_call": None
            }
        elif status == AgentStatus.NEEDS_INPUT:
            return {
                "result": None,
                "needs_input": data,        # data in the new style is a list of messages
                "safety_checks": [],
                "pending_call": None
            }
        elif status == AgentStatus.NEEDS_SAFETY_CHECK:
            safety_checks, pending_call = data
            return {
                "result": None,
                "needs_input": [],
                "safety_checks": safety_checks,
                "pending_call": pending_call
            }
        elif status == AgentStatus.ERROR:
            return {
                "result": None,
                "needs_input": [],
                "safety_checks": [],
                "pending_call": None,
                "error": data
            }

    def get_page_html(self, query="return document.documentElement.outerHTML;"):
        """
        Get the HTML content of the currently displayed webpage using Marionette.
        
        Args:
            query: JavaScript query to retrieve the HTML content. Defaults to retrieving the full DOM HTML.
        
        Returns:
            str: The HTML content of the current page, or an error message if retrieval fails.
        """
        return self.get_agent().get_page_html(query)
            
    def action(self, input_text=None, acknowledged_safety_checks=False, ignore_safety_and_input=False,
              complete_handler=None, needs_input_handler=None, needs_safety_check_handler=None, error_handler=None, tools=None, function_map=None, **kwargs):
        """
        New and improved action command: Execute an action in the desktop environment. This method delegates to the agent's action method.
        
        Args:
            input_text: Text input from the user. This can be:
                       - A new command to start a conversation
                       - A response to an agent's request for input
                       - None if acknowledging safety checks
            acknowledged_safety_checks: Whether safety checks have been acknowledged
                                       (only relevant if there's a pending call)
            ignore_safety_and_input: If True, automatically handle safety checks and input requests
                                    without requiring user interaction
            complete_handler: Function to handle COMPLETE status
                             Signature: (data) -> None
                             Returns: None (terminal state)
            needs_input_handler: Function to handle NEEDS_INPUT status
                                Signature: (messages) -> str
                                Returns: User input to continue with
            needs_safety_check_handler: Function to handle NEEDS_SAFETY_CHECK status
                                       Signature: (safety_checks, pending_call) -> bool
                                       Returns: Whether to proceed with the call (True) or not (False)
            error_handler: Function to handle ERROR status
                          Signature: (error_message) -> None
                          Returns: None (terminal state)
        
        Returns:
            Tuple of (status, data), where:
            - status is an AgentStatus enum value indicating the result
            - data contains relevant information based on the status
        """
        # Look for old-style keys in **kwargs:
        old_input = kwargs.get("input")
        user_input = kwargs.get("user_input")
        safety_checks = kwargs.get("safety_checks")
        pending_call = kwargs.get("pending_call")
        if type(acknowledged_safety_checks) == str:
            # using positional arguments in old style
            old_input = input_text
            user_input = acknowledged_safety_checks
            safety_checks = ignore_safety_and_input
            pending_call = complete_handler
        if any([old_input, user_input, safety_checks, pending_call]) or type(acknowledged_safety_checks) == str:
            warnings.warn(
                "Looks like you're using the old action() command - switch to action_legacy() if you need to maintain your current code, or switch to the new action method",
                DeprecationWarning, 
                stacklevel=2
            )
            return self.action_legacy(
                input=old_input,
                user_input=user_input,
                safety_checks=safety_checks,
                pending_call=pending_call
            )

        agent = self.get_agent()
        return agent.action(
            input_text=input_text, 
            acknowledged_safety_checks=acknowledged_safety_checks, 
            ignore_safety_and_input=ignore_safety_and_input,
            complete_handler=complete_handler,
            needs_input_handler=needs_input_handler,
            needs_safety_check_handler=needs_safety_check_handler,
            error_handler=error_handler,
            tools=tools,
            function_map=function_map
        )

    def extract_and_print_safety_checks(self, result):
        checks = result.get("safety_checks") or []
        for check in checks:
            # If each check has a 'message' attribute with sub-parts
            if hasattr(check, "message"):
                # Gather text for printing
                print(f"Pending Safety Check: {check.message}")
        return checks

    def handle_action(self, action_input, stored_response=None, user_input=None):
        """
        DEPRECATED: Method for handling old `action` method.
        
        Demo function to call and manage `action` loop and responses
        
        1) Call the desktop.action method to handle commands or continue interactions
        2) Print out agent prompts and safety checks
        3) If there's user input needed, prompt
        4) If there's a pending computer call with safety checks, ask user for ack, then continue
        5) Repeat until no further action is required
        """
        logger.warn(
            "Looks like you're using the old handle_action() command - switch to action_legacy() if you need to maintain your current code, or switch to the new action method: action()",
        )
        print(
            "Performing desktop action... see output_image.png to see screenshots "
            "OR connect to the VNC server to view actions in real time"
        )

        # Start the chain
        initial_input = stored_response if stored_response else action_input
        result = self.action(input=initial_input, user_input=user_input)

        while True:
            # Check if the agent is asking for user text input
            needs_input = result.get("needs_input")
            # Check for any pending computer_call we must run after acknowledging checks
            pending_call = result.get("pending_call")

            # Print any safety checks
            safety_checks = self.extract_and_print_safety_checks(result)

            # If the agent is asking for text input, handle that
            if needs_input:
                for msg in needs_input:
                    if hasattr(msg, "content"):
                        text_parts = [part.text for part in msg.content if hasattr(part, "text")]
                        print(f"Agent asks: {' '.join(text_parts)}")

                user_says = input("Enter your response (or 'exit'/'quit'): ").strip().lower()
                if user_says in ("exit", "quit"):
                    print("Exiting as per user request.")
                    return result

                # Call .action again with the user text, plus the previously extracted checks
                # They may or may not matter if there are no pending calls
                result = self.action(input=result["result"], user_input=user_says, safety_checks=safety_checks)
                continue

            # If there's a pending call with checks, the user must acknowledge them
            if pending_call and safety_checks:
                print(
                    "Please acknowledge the safety check(s) in order to proceed with the computer call."
                )
                ack = input("Type 'ack' to confirm, or 'exit'/'quit': ").strip().lower()
                if ack in ("exit", "quit"):
                    print("Exiting as per user request.")
                    return result
                if ack == "ack":
                    print("Acknowledged. Proceeding with the computer call...")
                    # We call 'action' again with the pending_call
                    # and pass along the same safety_checks to mark them as acknowledged
                    result = self.action(input=result["result"], pending_call=pending_call, safety_checks=safety_checks)
                    continue

            # If we reach here, no user input is needed & no pending call with checks
            # so presumably we are done
            return result