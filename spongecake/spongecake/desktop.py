import docker
from docker.errors import NotFound, ImageNotFound, APIError
import requests
import time
import base64
from openai import OpenAI

import os
import requests
import subprocess  # Import subprocess module


from . import _exceptions

# -------------------------
# Container Management Functions
# -------------------------
class Desktop:

    def __init__(self, name: str = "newdesktop", docker_image: str = "spongebox/spongecake:latest", vnc_port: int = 5900, api_port: int = 8000, openai_api_key: str = None):
        # Set container info
        self.container_name = name  # Set container name for use in methods
        self.docker_image = docker_image # Set image name to start container
        self.display = ":99"

        # Set up access ports
        self.vnc_port = vnc_port
        self.api_port = api_port

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

    def start(self):
        """
        Starts the container if it's not already running.
        Maps the VNC port and API port.
        """
        try:
            # Check to see if the container already exists
            container = self.docker_client.containers.get(self.container_name)
            print(f"⏰ Container '{self.container_name}' found with status '{container.status}'.")

            # If it's not running, start it
            if container.status != "running":
                print(f"Container '{self.container_name}' is not running. Starting...")
                container.start()
            else:
                print(f"Container '{self.container_name}' is already running.")

        except NotFound:
            # The container does not exist yet. Create it and pull the image first.
            print(f"Container '{self.container_name}' not found. Creating and starting a new container...")

            # Always attempt to pull the latest version of the image
            try:
                self.docker_client.images.pull(self.docker_image)
            except APIError as e:
                print("Failed to pull image. Attempting to start container...")

            # Try running a new container from the (hopefully just-pulled) image
            try:
                container = self.docker_client.containers.run(
                    self.docker_image,
                    detach=True,
                    name=self.container_name,
                    ports={
                        f"{self.vnc_port}/tcp": self.vnc_port,
                        f"{self.api_port}/tcp": self.api_port,
                    }
                )
            except ImageNotFound:
                # If for some reason the image is still not found locally,
                # try pulling again explicitly and run once more.
                print(f"Image '{self.docker_image}' not found locally. Pulling now...")
                try:
                    self.docker_client.images.pull(self.docker_image)
                except APIError as e:
                    raise RuntimeError(
                        f"Failed to find or pull image '{self.docker_image}'. Unable to start container."
                        f"Docker reported: {str(e)}"
                    ) from e

                container = self.docker_client.containers.run(
                    self.docker_image,
                    detach=True,
                    name=self.container_name,
                    ports={
                        f"{self.vnc_port}/tcp": self.vnc_port,
                        f"{self.api_port}/tcp": self.api_port,
                    }
                )

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
            print(f"Container '{self.container_name}' stopped and removed.")
        except docker.errors.NotFound:
            print(f"Container '{self.container_name}' not found.")

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
            print("Command Output:", result.output.decode())

        return {
            "result": result.output.decode() if result.output else "",
            "returncode": result.exit_code
        }

    # ----------------------------------------------------------------
    # CLICK
    # ----------------------------------------------------------------
    def click(self, x: int, y: int, click_type: str = "left"):
        """
        Move the mouse to (x, y) and click the specified button.
        click_type can be 'left', 'middle', or 'right'.
        """
        click_type_map = {"left": 1, "middle": 2, "wheel": 2, "right": 3}
        t = click_type_map.get(click_type.lower(), 1)

        print(f"Action: click at ({x}, {y}) with button '{click_type}' -> mapped to {t}")
        cmd = f"export DISPLAY={self.display} && xdotool mousemove {x} {y} click {t}"
        self.exec(cmd)

    # ----------------------------------------------------------------
    # SCROLL
    # ----------------------------------------------------------------
    def scroll(self, x: int, y: int, scroll_x: int = 0, scroll_y: int = 0):
        """
        Move to (x, y) and scroll horizontally (scroll_x) or vertically (scroll_y).
        Negative scroll_y -> scroll up, positive -> scroll down.
        Negative scroll_x -> scroll left, positive -> scroll right (button 6 or 7).
        """
        print(f"Action: scroll at ({x}, {y}) with offsets (scroll_x={scroll_x}, scroll_y={scroll_y})")
        # Move mouse to position
        move_cmd = f"export DISPLAY={self.display} && xdotool mousemove {x} {y}"
        self.exec(move_cmd)

        # Vertical scroll (button 4 = up, button 5 = down)
        if scroll_y != 0:
            button = 4 if scroll_y < 0 else 5
            clicks = int(abs(scroll_y)/100)
            for _ in range(4):
                scroll_cmd = f"export DISPLAY={self.display} && xdotool click {button}"
                self.exec(scroll_cmd)

        # Horizontal scroll (button 6 = left, button 7 = right)
        if scroll_x != 0:
            button = 6 if scroll_x < 0 else 7
            clicks = int(abs(scroll_x)/100)
            for _ in range(4):
                scroll_cmd = f"export DISPLAY={self.display} && xdotool click {button}"
                self.exec(scroll_cmd)

    # ----------------------------------------------------------------
    # KEYPRESS
    # ----------------------------------------------------------------
    def keypress(self, keys: list[str]):
        """
        Press (and possibly hold) keys in sequence. Allows pressing
        Ctrl/Shift down, pressing other keys, then releasing them.
        Example: keys=["CTRL","F"] -> Ctrl+F
        """
        print(f"Action: keypress with keys: {keys}")

        ctrl_pressed = False
        shift_pressed = False

        for k in keys:
            print(f"  - key '{k}'")

            # Check modifiers
            if k.upper() == 'CTRL':
                print("    => holding down CTRL")
                self.exec(f"export DISPLAY={self.display} && xdotool keydown ctrl")
                ctrl_pressed = True
            elif k.upper() == 'SHIFT':
                print("    => holding down SHIFT")
                self.exec(f"export DISPLAY={self.display} && xdotool keydown shift")
                shift_pressed = True
            # Check special keys
            elif k.lower() == "enter":
                self.exec(f"export DISPLAY={self.display} && xdotool key Return")
            elif k.lower() == "space":
                self.exec(f"export DISPLAY={self.display} && xdotool key space")
            else:
                # For normal alphabetic or punctuation
                lower_k = k.lower()  # xdotool keys are typically lowercase
                self.exec(f"export DISPLAY={self.display} && xdotool key '{lower_k}'")

        # Release modifiers
        if ctrl_pressed:
            print("    => releasing CTRL")
            self.exec(f"export DISPLAY={self.display} && xdotool keyup ctrl")
        if shift_pressed:
            print("    => releasing SHIFT")
            self.exec(f"export DISPLAY={self.display} && xdotool keyup shift")

    # ----------------------------------------------------------------
    # TYPE
    # ----------------------------------------------------------------
    def type_text(self, text: str):
        """
        Type a string of text (like using a keyboard) at the current cursor location.
        """
        print(f"Action: type text: {text}")
        cmd = f"export DISPLAY={self.display} && xdotool type '{text}'"
        self.exec(cmd)
    
    # ----------------------------------------------------------------
    # TAKE SCREENSHOT
    # ----------------------------------------------------------------
    def get_screenshot(self):
        """
        Takes a screenshot of the current desktop.
        Returns the base64-encoded PNG screenshot as a string.
        """
        # The command:
        # 1) Sets DISPLAY to :99 (as Xvfb is running on :99 in your Dockerfile)
        # 2) Runs 'import -window root png:- | base64'
        # 3) The -w 0 option on base64 ensures no line wrapping (optional)
        
        command = (
            "export DISPLAY=:99 && "
            "import -window root png:- | base64 -w 0"
        )

        # We run docker exec, passing the above shell command
        # Note: we add 'bash -c' so we can use shell pipes
        proc = subprocess.run(
            ["docker", "exec", self.container_name, "bash", "-c", command],
            capture_output=True,
            text=True
        )

        if proc.returncode != 0:
            raise RuntimeError(
                f"Screenshot command failed:\nSTDERR: {proc.stderr}\n"
            )

        # proc.stdout is now our base64-encoded screenshot
        return proc.stdout.strip()

    # -------------------------
    # OpenAI Agent Integration
    # -------------------------

    def handle_model_action(self, action):
        """
        Given a computer action (e.g., click, double_click, scroll, etc.),
        execute the corresponding operation on the Docker environment.
        """
        action_type = action.type

        try:
            match action_type:
            
                case "click":
                    x, y = int(action.x), int(action.y)
                    self.click(x,y,action.button)

                case "scroll":
                    x, y = int(action.x), int(action.y)
                    scroll_x, scroll_y = int(action.scroll_x), int(action.scroll_y)
                    self.scroll(x, y, scroll_x=scroll_x, scroll_y=scroll_y)
                
                case "keypress":
                    keys = action.keys
                    self.keypress(keys)
                
                case "type":
                    text = action.text
                    self.type_text(text)
                
                case "wait":
                    time.sleep(2)

                case "screenshot":
                    # Nothing to do as screenshot is taken at each turn
                    screenshot_bytes = self.get_screenshot()
                    return screenshot_bytes
                
                # Handle other actions here

                case _:
                    print(f"Unrecognized action: {action}")

        except Exception as e:
            print(f"Error handling action {action}: {e}")

    def computer_use_loop(self, response):
        """
        Run the loop that executes computer actions until no 'computer_call' is found,
        handling pending safety checks BEFORE actually executing the call.
        
        Returns:
            (response, messages, safety_checks, pending_call)
            - response: the latest (or final) response object
            - messages: a list of "message" items if user input is requested (or None)
            - safety_checks: a list of pending safety checks if any (or None)
            - pending_call: if there's exactly one computer_call that was paused
                due to safety checks, return that here so the caller can handle it
                after the user acknowledges the checks.
        """
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
            print("No actionable computer_call or interactive prompt found. Finishing loop.")
            return response, None, None, None

        # If we got here, that means there's a computer_call *without* any safety checks,
        # so we can proceed to execute it right away.

        # Execute the call
        self.handle_model_action(computer_call.action)
        time.sleep(1)  # small delay to allow environment changes

        # Take a screenshot
        screenshot_base64 = self.get_screenshot()
        image_data = base64.b64decode(screenshot_base64)
        with open("output_image.png", "wb") as f:
            f.write(image_data)
        print("* Saved image data.")

        # Now send that screenshot back as `computer_call_output`
        new_response = self.openai_client.responses.create(
            model="computer-use-preview",
            previous_response_id=response.id,
            tools=[
                {
                    "type": "computer_use_preview",
                    "display_width": 1024,
                    "display_height": 768,
                    "environment": "linux"
                }
            ],
            input=[
                {
                    "call_id": computer_call.call_id,
                    "type": "computer_call_output",
                    "output": {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{screenshot_base64}"
                    }
                }
            ],
            truncation="auto"
        )

        # Recurse with the updated response
        return self.computer_use_loop(new_response)


    def action(self, input=None, user_input=None, safety_checks=None, pending_call=None):
        """
        Execute an action in the container environment. The action can be:
        - A brand-new user command
        - A continued conversation with user_input
        - A resumed computer_call (pending_call) that was previously halted for safety checks

        Args:
            input: A string command or a "stored response" object from the model
            user_input: Optional text if the agent asked for user input
            safety_checks: A list of safety check objects that were acknowledged
            pending_call: A computer_call object we previously returned to the user (due to safety checks)
                        that now needs to be executed and followed with a screenshot, etc.

        Returns:
            dict: with "result", optional "needs_input", and "safety_checks" (list of checks if any).
        """
        # If the user is resuming a pending computer_call after acknowledging safety checks,
        # let's do that logic directly, bypassing normal text-based input.
        if pending_call:
            # We directly run that call; note that we do NOT pass user_input to the model
            # because we are continuing the same call with "acknowledged_safety_checks".
            return self._execute_and_continue_call(input, pending_call, safety_checks)

        # Otherwise, we do the normal "text-based" logic:
        def build_input_dict(role, content, checks=None):
            payload = {"role": role, "content": content}
            if checks:
                payload["safety_checks"] = checks
            return payload

        def create_response(new_input, previous_response_id=None):
            params = {
                "model": "computer-use-preview",
                "tools": [{
                    "type": "computer_use_preview",
                    "display_width": 1024,
                    "display_height": 768,
                    "environment": "linux"
                }],
                "input": [new_input],
                "truncation": "auto",
            }
            if previous_response_id is None:
                params["reasoning"] = {"generate_summary": "concise"}
            else:
                params["previous_response_id"] = previous_response_id
            return self.openai_client.responses.create(**params)

        # Normal flow if we have no pending_call
        if user_input is None:
            # brand-new action
            new_input = build_input_dict("user", input, safety_checks)
            response = create_response(new_input)
        else:
            # continuing from prior response
            new_input = build_input_dict("user", user_input, safety_checks)
            # 'input' here is assumed to be a response object with an id
            response = create_response(new_input, previous_response_id=input.id)

        output, messages, checks, pending_call = self.computer_use_loop(response)

        # If there is a pending call (with checks?), or if messages exist, we surface them
        if pending_call and checks:
            # Return so the user can see the checks and ack them in handle_action
            return {
                "result": output,
                "needs_input": messages or [],
                "safety_checks": checks,  # pass the entire check list
                "pending_call": pending_call
            }

        if messages:
            # The agent wants user text input
            return {
                "result": output,
                "needs_input": messages,
                "safety_checks": checks or []
            }

        # Otherwise, no user input is needed. Return final or in-progress with any checks
        return {
            "result": output,
            "safety_checks": checks or []
        }


    def _execute_and_continue_call(self, input, computer_call, safety_checks):
        """
        Helper for 'action': directly executes a 'computer_call' after user acknowledged
        safety checks. Then performs the screenshot step, sending 'acknowledged_safety_checks'
        in the computer_call_output.
        """
        # Actually execute the call
        self.handle_model_action(computer_call.action)
        time.sleep(1)

        # Take a screenshot
        screenshot_base64 = self.get_screenshot()
        image_data = base64.b64decode(screenshot_base64)
        with open("output_image.png", "wb") as f:
            f.write(image_data)
        print("* Saved image data.")

        # Now, create a new response with an acknowledged_safety_checks field
        # in the computer_call_output
        new_response = self.openai_client.responses.create(
            model="computer-use-preview",
            previous_response_id=input.id,
            tools=[
                {
                    "type": "computer_use_preview",
                    "display_width": 1024,
                    "display_height": 768,
                    "environment": "linux"
                }
            ],
            input=[
                {
                    "call_id": computer_call.call_id,
                    "type": "computer_call_output",
                    "acknowledged_safety_checks": [
                        {
                            "id": check.id,
                            "code": check.code,
                            "message": getattr(check, "message_str", "Safety check message")
                        }
                        for check in safety_checks
                    ],
                    "output": {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{screenshot_base64}"
                    }
                }
            ],
            truncation="auto"
        )

        # Then re-enter the loop with the new response to see if more calls or messages appear
        output, messages, checks, pending_call = self.computer_use_loop(new_response)

        result = {
            "result": output
        }
        if pending_call and checks:
            result["pending_call"] = pending_call
            result["safety_checks"] = checks
        elif messages:
            result["needs_input"] = messages
            result["safety_checks"] = checks or []
        else:
            result["safety_checks"] = checks or []

        return result

    def auto_generate_input(self, question: str, action_input: str) -> str:
        """Generate an automated response to agent questions using OpenAI.
        
        Args:
            question: The question asked by the agent
            action_input: The original action input that led to this interaction
            
        Returns:
            str: An appropriate response to the agent's question
        """
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant generating responses to questions in the context of desktop automation tasks. Keep responses concise and direct."},
                {"role": "user", "content": f"Original task: {action_input}\nAgent question: {question}\nPlease provide a suitable response to help complete this task."}
            ]
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating automated response: {str(e)}")
            return "continue"
            
    def extract_and_print_safety_checks(self, result):
        checks = result.get("safety_checks") or []
        for check in checks:
            # If each check has a 'message' attribute with sub-parts
            if hasattr(check, "message"):
                # Gather text for printing
                print(f"Pending Safety Check: {check.message}")
        return checks

    def handle_action(self, action_input, stored_response=None, user_input=None, ignore_safety_and_input=False):
        """
        Demo function to call and manage `action` loop and responses
        
        1) Call the desktop.action method to handle commands or continue interactions
        2) Print out agent prompts and safety checks
        3) If there's user input needed, prompt
        4) If there's a pending computer call with safety checks, ask user for ack, then continue
        5) Repeat until no further action is required
        """
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
                if ignore_safety_and_input:
                    # Extract the question from needs_input
                    question = ""
                    for msg in needs_input:
                        if hasattr(msg, "content"):
                            text_parts = [part.text for part in msg.content if hasattr(part, "text")]
                            question = ' '.join(text_parts)
                    
                    print(f"Agent asks: {question}")
                    print("Auto-generating response using OpenAI...")
                    
                    # Generate response using OpenAI
                    auto_response = self.auto_generate_input(question, action_input)
                    print(f"Auto-generated response: {auto_response}")
                    
                    result = self.action(input=result["result"], user_input=auto_response, safety_checks=safety_checks)
                    continue
                else:
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

            # If there's a pending call with checks, either get user acknowledgment or auto-proceed if ignore_safety_checks is True
            if pending_call and safety_checks:
                if ignore_safety_and_input:
                    print("Safety checks ignored. Automatically proceeding with the computer call...")
                    result = self.action(input=result["result"], pending_call=pending_call, safety_checks=safety_checks)
                    continue
                else:
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