import base64
import logging
import time
from typing import List, Dict, Any, Optional, Union, Tuple
from openai import OpenAI

# Import from constants module
from .constants import AgentStatus

# Set up logger
logger = logging.getLogger(__name__)

class Agent:
    """
    Agent class for integrating OpenAI's agent capabilities with a desktop environment.
    This class handles the agentic loop for controlling a desktop environment through
    natural language commands and visual feedback.
    
    The Agent maintains state internally, tracking conversation history, pending calls,
    and safety checks, making it easier to interact with the agent through a simple
    status-based API.
    """

    def __init__(self, desktop=None, openai_api_key=None):
        """
        Initialize an Agent instance.
        
        Args:
            desktop: A Desktop instance to control. Can be set later with set_desktop().
            openai_api_key: OpenAI API key for authentication. If None, will try to use
                           the one from the desktop or environment variables.
        """
        self.desktop = desktop
        
        # Set up OpenAI API key and client
        if openai_api_key is None and desktop is not None:
            openai_api_key = desktop.openai_api_key
            
        if openai_api_key is not None:
            self.openai_api_key = openai_api_key
            self.openai_client = OpenAI(api_key=openai_api_key)
        else:
            self.openai_api_key = None
            self.openai_client = None
            
        # Initialize state tracking
        self._response_history = []  # List of all responses from the API
        self._input_history = []     # List of all inputs sent to the API
        self._current_response = None  # Current response object
        self._pending_call = None     # Pending computer call that needs safety check acknowledgment
        self._pending_safety_checks = []  # Pending safety checks
        self._needs_input = []        # Messages requesting user input
        self._error = None            # Last error message, if any

    def set_desktop(self, desktop):
        """
        Set or update the desktop instance this agent controls.
        
        Args:
            desktop: A Desktop instance to control.
        """
        self.desktop = desktop
        
        # If we don't have an API key yet, try to get it from the desktop
        if self.openai_api_key is None and desktop.openai_api_key is not None:
            self.openai_api_key = desktop.openai_api_key
            self.openai_client = OpenAI(api_key=self.openai_api_key)

    def handle_model_action(self, action):
        """
        Given a computer action (e.g., click, double_click, scroll, etc.),
        execute the corresponding operation on the Desktop environment.
        
        Args:
            action: An action object from the OpenAI model response.
            
        Returns:
            Screenshot bytes if the action is a screenshot, None otherwise.
        """
        if self.desktop is None:
            raise ValueError("No desktop has been set for this agent.")
            
        action_type = action.type

        try:
            if action_type == "click":
                x, y = int(action.x), int(action.y)
                self.desktop.click(x, y, action.button)
            elif action_type == "scroll":
                x, y = int(action.x), int(action.y)
                scroll_x, scroll_y = int(action.scroll_x), int(action.scroll_y)
                self.desktop.scroll(x, y, scroll_x=scroll_x, scroll_y=scroll_y)
            elif action_type == "keypress":
                keys = action.keys
                self.desktop.keypress(keys)
            elif action_type == "type":
                text = action.text
                self.desktop.type_text(text)
            elif action_type == "wait":
                time.sleep(2)
            elif action_type == "screenshot":
                # Nothing to do as screenshot is taken at each turn
                screenshot_bytes = self.desktop.get_screenshot()
                return screenshot_bytes
            else:
                logger.info(f"Unrecognized action: {action}")

        except Exception as e:
            logger.error(f"Error handling action {action}: {e}")

    def _auto_generate_input(self, question: str, input_history=None) -> str:
        """Generate an automated response to agent questions using OpenAI.
        
        Args:
            question: The question asked by the agent
            input_history: The history of user inputs for context
            
        Returns:
            str: An appropriate response to the agent's question
        """
        try:
            # Extract original task and conversation history
            original_task = input_history[0].get('content', '') if input_history and len(input_history) > 0 else ''
            
            # Build conversation history
            conversation_history = ""
            if input_history and len(input_history) > 1:
                for i, inp in enumerate(input_history[1:], 1):
                    conversation_history += f"User input {i}: {inp.get('content', '')}\n"
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant generating responses to questions in the context of desktop automation tasks. Keep responses concise and direct."},
                {"role": "user", "content": f"Original task: {original_task}\nConversation history:\n{conversation_history}\nAgent question: {question}\nPlease provide a suitable response to help complete this task."}
            ]
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=100,
                temperature=0.7
            )
            
            auto_response = response.choices[0].message.content.strip()
            logger.info(f"Auto-generated response: {auto_response}")
            return auto_response
        except Exception as e:
            logger.error(f"Error generating automated response: {str(e)}")
            return "continue"

    def _is_message_asking_for_input(self, message, input_history=None):
        """
        Determine if a message from the agent is asking for more input or providing a final answer.
        Uses a lightweight GPT model to analyze the message content.
        
        Args:
            message: The message object from the agent
            input_history: Optional list of previous user inputs for context
            
        Returns:
            bool: True if the message is asking for more input, False if it's a final answer
        """
        if not self.openai_client:
            # If no OpenAI client is available, assume it needs input if it's a message
            return True
            
        # Extract text from the message
        message_text = ""
        if hasattr(message, "content"):
            text_parts = [part.text for part in message.content if hasattr(part, "text")]
            message_text = " ".join(text_parts)
        
        # If message is empty, assume it doesn't need input
        if not message_text.strip():
            return False
            
        # Prepare context from input history if available
        context = ""
        if input_history and len(input_history) > 0:
            last_inputs = input_history[-min(3, len(input_history)):]
            context = "Previous user inputs:\n" + "\n".join([f"- {inp.get('content', '')}" for inp in last_inputs])
        
        # Create prompt for the model
        prompt = f"""Analyze this message from an AI agent and determine if it's asking for more input (1) or providing a final answer (0).

{context}

Agent message: "{message_text}"

Is this message asking for more input from the user?
Respond with only a single digit: 1 (yes, asking for input) or 0 (no, providing final answer)."""
        
        try:
            # Make a lightweight call to the model
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using a lightweight model
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1,  # We only need a single digit
                temperature=0.0  # Deterministic response
            )
            
            # Extract the response
            result = response.choices[0].message.content.strip()
            
            # Parse the result
            if "1" in result:
                return True
            elif "0" in result:
                return False
            else:
                # If the model didn't return a clear 0 or 1, default to assuming input is needed
                logger.info(f"Unclear response from input detection model: {result}. Assuming input is needed.")
                return True
                
        except Exception as e:
            # If there's an error, default to assuming it needs input
            logger.error(f"Error determining if message needs input: {e}. Assuming input is needed.")
            return True
    
    def computer_use_loop(self, response, custom_tools=None, function_map=None):
        """
        Run the loop that executes computer actions until no 'computer_call' is found,
        handling pending safety checks BEFORE actually executing the call.
        Also handles function calls like get_page_html.
        
        Args:
            response: A response object from the OpenAI API.
            custom_tools: Optional list of additional tool definitions to include
            function_map: Optional dictionary mapping function names to callable functions
            
        Returns:
            (response, messages, safety_checks, pending_call)
            - response: the latest (or final) response object
            - messages: a list of "message" items if user input is requested (or None)
            - safety_checks: a list of pending safety checks if any (or None)
            - pending_call: if there's exactly one computer_call that was paused
                due to safety checks, return that here so the caller can handle it
                after the user acknowledges the checks.
            - needs_input: boolean indicating if messages require more input
        """
        if self.desktop is None:
            raise ValueError("No desktop has been set for this agent.")
            
        # Check for function calls and handle them
        function_calls = [item for item in response.output if item.type == "function_call"]
        if function_calls:
            import json
            input_messages = []
            
            for tool_call in function_calls:
                name = tool_call.name
                args = json.loads(tool_call.arguments) if hasattr(tool_call, 'arguments') and tool_call.arguments else {}
                
                # Dispatch to the appropriate function
                if name == "get_page_html":
                    result = self.get_page_html(**args)
                elif function_map and name in function_map:
                    # Use the provided function map for custom functions
                    logger.info(f"[TOOL CALL] Calling function: {name}, with arguments: {args}")
                    result = function_map[name](**args)
                else:
                    logger.info(f"[TOOL CALL] Function: {name} not found in function map. Unable to call.")
                    result = f"Function {name} not implemented"
                    
                # Add the result to input messages
                input_messages.append({
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": str(result)
                })
                
            # Create a new response with the function results
            new_response = self._create_response(
                input_data=input_messages,
                previous_response_id=response.id,
                custom_tools=custom_tools
            )
            
            # Add to response history
            self._response_history.append(new_response)
            self._current_response = new_response
            
            # Continue the loop with the new response
            return self.computer_use_loop(new_response, custom_tools=custom_tools, function_map=function_map)
        
        # Identify all message items (the agent wants text input)
        messages = [item for item in response.output if item.type == "message"]

        # Identify any computer_call items
        computer_calls = [item for item in response.output if item.type == "computer_call"]

        # For simplicity, assume the agent only issues ONE call at a time
        computer_call = computer_calls[0] if computer_calls else None

        # Identify all safety checks across items
        all_safety_checks = []
        for item in response.output:
            checks = getattr(item, "pending_safety_checks", None)
            if checks:
                all_safety_checks.extend(checks)

        # If there's a computer_call that also has safety checks,
        # we must return immediately so the user can acknowledge them first.
        # We'll do so by returning the "pending_call" plus the checks.
        if computer_call and all_safety_checks:
            return response, messages or None, all_safety_checks, computer_call

        # If there's no computer_call at all, but we do have messages or checks
        # we return them so the caller can handle user input or safety checks.
        if not computer_call:
            if messages or all_safety_checks:
                return response, messages or None, all_safety_checks or None, None
            # Otherwise, no calls, no messages, no checks => done
            logger.info("No actionable computer_call or interactive prompt found. Finishing loop.")
            return response, None, None, None

        # If we got here, that means there's a computer_call *without* any safety checks,
        # so we can proceed to execute it right away.

        # Execute the call
        self.handle_model_action(computer_call.action)
        time.sleep(1)  # small delay to allow environment changes

        # Take a screenshot
        screenshot_base64 = self.desktop.get_screenshot()
        image_data = base64.b64decode(screenshot_base64)
        with open("output_image.png", "wb") as f:
            f.write(image_data)
        logger.info("* Saved image data.")

        # Now send that screenshot back as `computer_call_output`
        call_output = self._build_input_dict(
            call_id=computer_call.call_id,
            output={
                "type": "input_image",
                "image_url": f"data:image/png;base64,{screenshot_base64}"
            }
        )
        
        new_response = self._create_response(
            input_data=call_output,
            previous_response_id=response.id,
            custom_tools=custom_tools
        )

        # Recurse with the updated response
        return self.computer_use_loop(new_response, custom_tools=custom_tools, function_map=function_map)

    @property
    def current_response(self):
        """Get the current response object."""
        return self._current_response
        
    @property
    def response_history(self):
        """Get the history of all responses."""
        return self._response_history.copy()
        
    @property
    def input_history(self):
        """Get the history of all inputs."""
        return self._input_history.copy()
        
    @property
    def pending_call(self):
        """Get the pending computer call, if any."""
        return self._pending_call
        
    @property
    def pending_safety_checks(self):
        """Get the pending safety checks, if any."""
        return self._pending_safety_checks.copy() if self._pending_safety_checks else []
        
    @property
    def needs_input(self):
        """Get the messages requesting user input, if any."""
        return self._needs_input.copy() if self._needs_input else []
        
    @property
    def error(self):
        """Get the last error message, if any."""
        return self._error
        
    def reset_state(self):
        """Reset the agent's state, clearing all history and pending items."""
        self._response_history = []
        self._input_history = []
        self._current_response = None
        self._pending_call = None
        self._pending_safety_checks = []
        self._needs_input = []
        self._error = None
        
    def action(self, input_text=None, acknowledged_safety_checks=False, ignore_safety_and_input=False,
               complete_handler=None, needs_input_handler=None, needs_safety_check_handler=None, error_handler=None,
               tools=None, function_map=None):
        """
        Execute an action in the desktop environment. This method handles different scenarios:
        - Starting a new conversation with a command
        - Continuing a conversation with user input
        - Acknowledging safety checks for a pending call
        - Automatically handling safety checks and input requests if ignore_safety_and_input is True
        - Using custom handlers for different statuses if provided
        - Processing custom tools and functions provided by the user
        
        The method maintains state internally and returns a simple status and relevant data,
        or delegates to the appropriate handler if provided.
        
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
            tools: List of additional tool definitions to make available to the model
                  Each tool should be a dictionary in the OpenAI function calling format
            function_map: Dictionary mapping function names to callable functions
                         Used when the model calls a function by name
        
        Returns:
            Tuple of (status, data), where:
            - status is an AgentStatus enum value indicating the result
            - data contains relevant information based on the status:
              - For COMPLETE: The final response object
              - For NEEDS_INPUT: List of messages requesting input
              - For NEEDS_SAFETY_CHECK: List of safety checks and the pending call
              - For ERROR: Error message
            
            If handlers are provided, this function may return different values based on the handler's execution.
        """
        if self.desktop is None:
            self._error = "No desktop has been set for this agent."
            error_result = AgentStatus.ERROR, self._error
            if error_handler:
                error_handler(self._error)
            return error_result
            
        try:
            # If we're ignoring safety and input, handle them automatically
            if ignore_safety_and_input:
                status, data = self._handle_action_with_auto_responses(input_text, tools=tools, function_map=function_map)
                # Even in auto mode, we should pass through handlers if provided
                return self._process_result_with_handlers(status, data, complete_handler, needs_input_handler, 
                                                        needs_safety_check_handler, error_handler, tools=tools, function_map=function_map)
            
            # Case 1: Acknowledging safety checks for a pending call
            if acknowledged_safety_checks and self._pending_call:
                status, data = self._handle_acknowledged_safety_checks(custom_tools=tools, function_map=function_map)
                return self._process_result_with_handlers(status, data, complete_handler, needs_input_handler, 
                                                        needs_safety_check_handler, error_handler, tools=tools, function_map=function_map)
                
            # Case 2: Continuing a conversation with user input
            if self._needs_input and input_text is not None:
                status, data = self._handle_user_input(input_text, tools=tools, function_map=function_map)
                return self._process_result_with_handlers(status, data, complete_handler, needs_input_handler, 
                                                        needs_safety_check_handler, error_handler, tools=tools, function_map=function_map)
                
            # Case 3: Starting a new conversation with a command
            if input_text is not None:
                status, data = self._handle_new_command(input_text, tools=tools, function_map=function_map)
                return self._process_result_with_handlers(status, data, complete_handler, needs_input_handler, 
                                                        needs_safety_check_handler, error_handler, tools=tools, function_map=function_map)
                
            # If we get here, there's no valid action to take
            self._error = "No valid action to take. Provide input text or acknowledge safety checks."
            error_result = AgentStatus.ERROR, self._error
            if error_handler:
                error_handler(self._error)
            return error_result
                
        except Exception as e:
            self._error = str(e)
            error_result = AgentStatus.ERROR, self._error
            if error_handler:
                error_handler(self._error)
            return error_result
            
    def _process_result_with_handlers(self, status, data, complete_handler, needs_input_handler, 
                                     needs_safety_check_handler, error_handler, tools=None, function_map=None):
        """Process a result with the appropriate handler if provided."""
        # If handlers are provided, use them to handle the different statuses
        if status == AgentStatus.COMPLETE and complete_handler:
            complete_handler(data)
            return status, data
            
        elif status == AgentStatus.NEEDS_INPUT and needs_input_handler:
            user_input = needs_input_handler(data)
            if user_input:
                # Continue with the provided input - pass all handlers
                return self.action(
                    input_text=user_input,
                    complete_handler=complete_handler,
                    needs_input_handler=needs_input_handler,
                    needs_safety_check_handler=needs_safety_check_handler,
                    error_handler=error_handler,
                    tools=tools,
                    function_map=function_map
                )
            return status, data
            
        elif status == AgentStatus.NEEDS_SAFETY_CHECK and needs_safety_check_handler:
            proceed = needs_safety_check_handler(data["safety_checks"], data["pending_call"])
            if proceed:
                # Continue with acknowledged safety checks - pass all handlers
                return self.action(
                    acknowledged_safety_checks=True,
                    complete_handler=complete_handler,
                    needs_input_handler=needs_input_handler,
                    needs_safety_check_handler=needs_safety_check_handler,
                    error_handler=error_handler,
                    tools=tools,
                    function_map=function_map
                )
            return status, data
            
        elif status == AgentStatus.ERROR and error_handler:
            error_handler(data)
            return status, data
            
        # If no handler or handler didn't take action, return the result
        return status, data
            
    def _handle_action_with_auto_responses(self, input_text, tools=None, function_map=None):
        """Handle an action with automatic responses to safety checks and input requests."""
        # Start with a new command if provided, or continue from current state
        if input_text is not None:
            status, data = self._handle_new_command(input_text, tools=tools, function_map=function_map)
        elif self._current_response:
            # Continue from current state
            status, data = AgentStatus.COMPLETE, self._current_response
        else:
            self._error = "No input provided and no current conversation to continue."
            return AgentStatus.ERROR, self._error
            
        # Loop until we get a COMPLETE status or hit an error
        max_iterations = 500  # Safety limit to prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Auto-response iteration {iteration}")
            
            if status == AgentStatus.COMPLETE:
                # We're done
                return status, data
                
            elif status == AgentStatus.NEEDS_SAFETY_CHECK:
                # Automatically acknowledge safety checks
                logger.info("Automatically acknowledging safety checks:")
                safety_checks = data["safety_checks"]
                for check in safety_checks:
                    if hasattr(check, "message"):
                        logger.info(f"- Pending safety check: {check.message}")
                
                # Handle the acknowledged safety checks
                status, data = self._handle_acknowledged_safety_checks(custom_tools=tools, function_map=function_map)
                
            elif status == AgentStatus.NEEDS_INPUT:
                # Generate an automatic response
                messages = data
                question = ""
                for msg in messages:
                    if hasattr(msg, "content"):
                        text_parts = [part.text for part in msg.content if hasattr(part, "text")]
                        question += " ".join(text_parts)
                
                # Generate an automatic response
                auto_response = self._auto_generate_input(question, self._input_history)
                
                # Continue with the auto-generated response
                status, data = self._handle_user_input(auto_response, tools=tools, function_map=function_map)
                
            elif status == AgentStatus.ERROR:
                # An error occurred
                return status, data
                
        # If we get here, we hit the iteration limit
        self._error = f"Exceeded maximum iterations ({max_iterations}) in auto-response mode."
        return AgentStatus.ERROR, self._error
            
    def _handle_new_command(self, command_text, tools=None, function_map=None):
        """Handle a new command from the user."""
        # Reset state for new conversation
        self._pending_call = None
        self._pending_safety_checks = []
        self._needs_input = []
        self._function_map = function_map or {}
        
        # Create input and response
        new_input = self._build_input_dict("user", command_text)
        self._input_history.append(new_input)
        
        response = self._create_response(new_input, custom_tools=tools)
        self._response_history.append(response)
        self._current_response = response
        
        # Process the response
        return self._process_response(response, custom_tools=tools, function_map=self._function_map)
        
    def _handle_user_input(self, input_text, tools=None, function_map=None):
        """Handle user input in response to an agent request."""
        if not self._current_response:
            self._error = "No active conversation to continue."
            return AgentStatus.ERROR, self._error
            
        # Update function map if provided
        if function_map:
            self._function_map = function_map
            
        # Create input and response
        new_input = self._build_input_dict("user", input_text)
        self._input_history.append(new_input)
        
        response = self._create_response(new_input, previous_response_id=self._current_response.id, custom_tools=tools)
        self._response_history.append(response)
        self._current_response = response
        
        # Clear the needs_input flag since we've provided input
        self._needs_input = []
        
        # Process the response
        return self._process_response(response, custom_tools=tools, function_map=self._function_map)
        
    def _handle_acknowledged_safety_checks(self, custom_tools=None, function_map=None):
        """Handle acknowledged safety checks for a pending call."""
        if not self._current_response or not self._pending_call or not self._pending_safety_checks:
            self._error = "No pending call or safety checks to acknowledge."
            return AgentStatus.ERROR, self._error
            
        # Update function map if provided
        if function_map:
            self._function_map = function_map
            
        # Execute the call with acknowledged safety checks
        self._execute_and_continue_call(self._current_response, self._pending_call, self._pending_safety_checks, custom_tools=custom_tools)
        
        # Clear the pending call and safety checks
        self._pending_call = None
        self._pending_safety_checks = []
        
        # Process the updated response
        return self._process_response(self._current_response, custom_tools=custom_tools, function_map=self._function_map)
        
    def get_page_html(self, query="return document.documentElement.outerHTML;", *args, **kwargs):
        """
        Get the HTML content of the currently displayed webpage using Marionette.
        
        Returns:
            str: The HTML content of the current page, or an error message if retrieval fails.
        """
        if self.desktop is None:
            return "Error: No desktop has been set for this agent."
            
        # Check if marionette_driver is available
        try:
            import json
            try:
                from marionette_driver.marionette import Marionette
            except ImportError:
                return "Error: marionette_driver package is not installed. Please install it with 'pip install marionette_driver'."
            
            # Connect to Marionette through the port forwarded by socat
            host = "localhost"
            port = self.desktop.marionette_port  # Use the marionette_port directly
            
            # logger.info(f"Connecting to Marionette server at {host}:{port}...")
            try:
                client = Marionette(host, port=port)
                # logger.info("Successfully connected to Marionette server.")

                client.start_session()
                # Execute JavaScript to get the full DOM HTML
                html = client.execute_script(query)
                
                # logger.info("Successfully retrieved page HTML")
                return html
            except ConnectionRefusedError:
                return f"Error: Could not connect to Marionette server at {host}:{port}. Make sure Firefox is running with marionette enabled."
            except Exception as e:
                error_message = f"Error in Marionette connection: {str(e)}"
                logger.error(error_message)
                return error_message
        except Exception as e:
            error_message = f"Unexpected error retrieving page HTML: {str(e)}"
            logger.error(error_message)
            return error_message
    
    def _process_response(self, response, custom_tools=None, function_map=None):
        """Process a response from the API and determine the next action."""
        output, messages, checks, pending_call = self.computer_use_loop(response, custom_tools=custom_tools, function_map=function_map)
        self._current_response = output
        
        # Update state based on the response
        if pending_call and checks:
            self._pending_call = pending_call
            self._pending_safety_checks = checks
            return AgentStatus.NEEDS_SAFETY_CHECK, {
                "safety_checks": checks,
                "pending_call": pending_call
            }
            
        if messages:
            # Check if any of the messages are asking for input
            needs_input = False
            for message in messages:
                if self._is_message_asking_for_input(message, self._input_history):
                    needs_input = True
                    break
                    
            if needs_input:
                # The message is asking for more input
                self._needs_input = messages
                return AgentStatus.NEEDS_INPUT, messages
            else:
                # The message is a final answer
                return AgentStatus.COMPLETE, output
            
        # If we get here, the action is complete
        return AgentStatus.COMPLETE, output

    def _build_input_dict(self, role=None, content=None, call_id=None, call_type=None, output=None, safety_checks=None, acknowledged_safety_checks=None):
        """
        Helper method to build an input dictionary for the OpenAI API.
        
        This method can build two types of input dictionaries:
        1. A standard message input with role and content (when role is provided)
        2. A computer_call_output input (when call_id and output are provided)
        
        Args:
            role: The role of the message (e.g., "user", "assistant") - for standard messages
            content: The content of the message - for standard messages
            call_id: The ID of the computer call - for computer_call_output
            call_type: The type of call, defaults to "computer_call_output" if call_id is provided
            output: The output data for computer_call_output
            safety_checks: Optional safety checks for standard messages
            acknowledged_safety_checks: Optional acknowledged safety checks for computer_call_output
            
        Returns:
            A dictionary with the message data
        """
        # Handle standard message input
        if role is not None:
            payload = {"role": role, "content": content}
            if safety_checks:
                payload["safety_checks"] = safety_checks
            return payload
            
        # Handle computer_call_output
        elif call_id is not None:
            payload = {
                "call_id": call_id,
                "type": call_type or "computer_call_output",
                "output": output
            }
            
            if acknowledged_safety_checks:
                payload["acknowledged_safety_checks"] = [
                    {
                        "id": check.id,
                        "code": check.code,
                        "message": getattr(check, "message", "Safety check message")
                    }
                    for check in acknowledged_safety_checks
                ]
                
            return payload
            
        else:
            raise ValueError("Either role or call_id must be provided")

    def _create_response(self, input_data, previous_response_id=None, reasoning=None, custom_tools=None):
        """
        Helper method to create a response from the OpenAI API.
        
        Args:
            input_data: The input to send to the API. Can be a single input dict or a list of input dicts.
            previous_response_id: Optional ID of a previous response to continue from
            reasoning: Optional reasoning configuration
            custom_tools: Optional list of additional tool definitions to include
            
        Returns:
            A response object from the OpenAI API
        """
        # Ensure input_data is a list
        if not isinstance(input_data, list):
            input_data = [input_data]
            
        # Define default tools
        default_tools = [
            {
                "type": "computer_use_preview",
                "display_width": self.desktop.screen_width,
                "display_height": self.desktop.screen_height,
                "environment": self.desktop.environment
            },
            # {
            #     "type": "function",
            #     "name": "get_page_html",
            #     "description": "Get the full HTML content of the currently displayed webpage. This is generally better than scrolling to see all content when you need the full context of a webpage.",
            #     "parameters": {
            #         "type": "object",
            #         "properties": {},
            #         "required": [],
            #         "additionalProperties": False
            #     }
            # }
        ]
        
        # Add custom tools if provided
        tools = default_tools.copy()
        if custom_tools:
            tools.extend(custom_tools)

        params = {
            "model": "computer-use-preview",
            "tools": tools,
            "input": input_data,
            "truncation": "auto",
        }
        
        # Add reasoning if provided or if no previous_response_id
        if reasoning:
            params["reasoning"] = reasoning
        elif previous_response_id is None:
            params["reasoning"] = {"generate_summary": "concise"}
            
        # Add previous_response_id if provided
        if previous_response_id:
            params["previous_response_id"] = previous_response_id
            
        try:
            return self.openai_client.responses.create(**params)
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error creating response: {str(e)}")
            logger.error(f"Error code: {getattr(e, 'code', 'N/A')}")
            logger.error(f"Error details: {getattr(e, 'json', {})}")
            logger.error(f"Stacktrace:\n{error_traceback}")
            raise

    def _execute_and_continue_call(self, input, computer_call, safety_checks, custom_tools=None, function_map=None):
        """
        Helper for 'action': directly executes a 'computer_call' after user acknowledged
        safety checks. Then performs the screenshot step, sending 'acknowledged_safety_checks'
        in the computer_call_output.
        
        Args:
            input: The input response object
            computer_call: The computer call to execute
            safety_checks: The safety checks that were acknowledged
            custom_tools: Optional list of additional tool definitions to include
        """
        if self.desktop is None:
            raise ValueError("No desktop has been set for this agent.")
            
        # Actually execute the call
        self.handle_model_action(computer_call.action)
        time.sleep(1)

        # Take a screenshot
        screenshot_base64 = self.desktop.get_screenshot()
        image_data = base64.b64decode(screenshot_base64)
        with open("output_image.png", "wb") as f:
            f.write(image_data)
        logger.info("* Saved image data.")

        # Now, create a new response with an acknowledged_safety_checks field
        # in the computer_call_output
        call_output = self._build_input_dict(
            call_id=computer_call.call_id,
            output={
                "type": "input_image",
                "image_url": f"data:image/png;base64,{screenshot_base64}"
            },
            acknowledged_safety_checks=safety_checks
        )
        
        new_response = self._create_response(
            input_data=call_output,
            previous_response_id=input.id,
            custom_tools=custom_tools,
        )
        
        # Add to response history
        self._response_history.append(new_response)
        self._current_response = new_response