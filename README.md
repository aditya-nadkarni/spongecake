<div align="center">
  <img 
    src="./static/spongecake-light.png" 
    alt="spongecake logo" 
    width="700" 
  >
</div>


<h1 align="center">Open source SDK to launch OpenAI computer use agents</h1>
<div style="text-align: center;">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./static/spongecake-demo.gif" />
    <img 
      alt="[coming soon] Shows a demo of spongecake in action" 
      src="./static/spongecake-demo.gif" 
      style="width: 100%; max-width: 700px;"
    />
  </picture>
  <p style="font-size: 1.2em; margin-top: 10px; text-align: center; color: gray;">
    Using spongecake to fill out a form 
  </p>
</div>


## What is spongecake?

**spongecake** is the easiest way to launch OpenAI-powered “computer use” agents. It simplifies:
- **Spinning up** a Docker container with a virtual desktop (including Xfce, VNC, etc.).
- **Controlling** that virtual desktop programmatically using an SDK (click, scroll, keyboard actions).
- **Integrating** with OpenAI to drive an agent that can interact with a real Linux-based GUI.

---

## Prerequisites

You’ll need the following to get started (click to download):
- [**Docker**](https://docs.docker.com/get-docker/)  
- [**OpenAI API Key**](https://platform.openai.com/)

# Quick Start

1. **Clone the repo** (if you haven’t already):
   ```bash
   git clone https://github.com/aditya-nadkarni/spongecake.git
   cd spongecake/test
   ```
2. **Set up a Python virtual environment and install the spongecake package**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate

   python3 -m pip install --upgrade spongecake
   python3 -m pip install --upgrade dotenv
   python3 -m pip install --upgrade openai  # Make sure you have the latest version of openai for the responses API
   ```
3. **Run the test script**:  
   ```bash
   cd test # If needed
   ```
   ```bash
   python3 test.py
   ```
   Feel free to edit the `test.py` script to try out your own commands.  
   <br>
   > **Note:** This deploys a Docker container in your local Docker environment. If the spongecake default image isn't available, it will pull the image from Docker Hub.

4. **Create your own scripts**:
  The test script is largely for demonstration purposes. To make this work for own use cases, create your own scripts using the SDK or integrate it into your own systems.

---

# (Optional) Building & Running the Docker Container

If you want to manually build and run the included Docker image for a virtual desktop environment you can follow these steps. To make your own changes to the docker container, fork the repository and edit however you need. This is perfect for adding dependencies specific to your workflows.

1. **Navigate to the Docker folder** (e.g., `cd spongecake/docker`).
2. **Build the image**:
   ```bash
   docker build -t <name of your image> .
   ```
3. **Run the container**:
   ```bash
   docker run -d -p 5900:5900 --name <name of your container> <name of your image>
   ```
   - This starts a container that you name and exposes VNC on port **5900**.

4. **Shell into the container** (optional):
   ```bash
   docker exec -it <name of your container> bash
   ```
   This is useful for debugging, installing extra dependencies, etc.

5. You can then specify the name of your container / image when using the SDK

---

# Connecting to the Virtual Desktop
**If you're working on a mac**:
1. Right click `Finder` and select `Connect to server...`  
      OR  
   In the `Finder` window, navigate to `Go > Connect to server...` in the menu bar
2. Enter the VNC host and port - should be `vnc://localhost:5900` in the default container
3. It will ask for a password, which will be set to "`secret`" in the default docker container
4. Your mac will connect to the VNC server. You can view and control the container's desktop through here

**Other options**:
1. **Install a VNC Viewer**, such as [TigerVNC](https://tigervnc.org/) or [RealVNC](https://www.realvnc.com/en/connect/download/viewer/).
2. **Open the VNC client** and connect to:
   ```
   localhost:5900
   ```
3. Enter the password when needed (set to "`secret`" in the default docker container).

---

<br>
<br>

# Documentation

## Desktop Client Documentation

Below is the **Desktop** class, which provides functionality for managing and interacting with a Docker container that simulates a Linux desktop environment. This class enables you to control mouse/keyboard actions, retrieve screenshots, and integrate with OpenAI for higher-level agent logic.

---

## Class: `Desktop`

**Arguments**:
1. **name** *(str)*: A unique name for the container. Defaults to `"newdesktop"`. This should be unique for different containers
2. **docker_image** *(str)*: The Docker image name to pull/run if not already available. Defaults to `"spongebox/spongecake:latest"`.
3. **vnc_port** *(int)*: The host port mapped to the container’s VNC server. Defaults to **5900**.
4. **api_port** *(int)*: The host port mapped to the container’s internal API. Defaults to **8000**.
5. **openai_api_key** *(str)*: An optional API key for OpenAI. If not provided, the class attempts to read `OPENAI_API_KEY` from the environment.

**Raises**:
- **SpongecakeException** if any port is in use.
- **SpongecakeException** if no OpenAI API key is supplied.

**Description**: Creates a Docker client, sets up container parameters, and initializes an internal OpenAI client for agent integration.

---

### **`start()`**

```python
def start(self) -> Container:
    """
    Starts the container if it's not already running.
    """
```

**Behavior**:
- Starts the docker container thats initialized in the Desktop() constructor
- Checks if a container with the specified `name` already exists.
- If the container exists but is not running, it starts it.  
  Note: In this case, it will not pull the latest image
- If the container does not exist, the method attempts to run it:
  - It will attempt to pull the latest image before starting the container
- Waits a short time (2 seconds) for services to initialize.
- Returns the running container object.

**Returns**:
- A Docker `Container` object representing the running container.

**Exceptions**:
- **RuntimeError** if it fails to find or pull the specified image
- **docker.errors.APIError** For any issue with running the container
---

### **`stop()`**

```python
def stop(self) -> None:
    """
    Stops and removes the container.
    """
```

**Behavior**:
- Stops + removes the container.
- Prints a status message.
- If the container does not exist, prints a warning.

**Returns**:
- `None`

---

### **`exec(command)`**

```python
def exec(self, command: str) -> dict:
    """
    Runs a shell command inside the container.
    """
```

**Arguments**:
- **command** *(str)*: The shell command to execute.

**Behavior**:
- Runs a shell command in the docker container
- Captures stdout and stderr.
- Logs the command output.

**Returns**:
A dictionary with:
```json
{
  "result": (string output),
  "returncode": (integer exit code)
}
```

---

## Desktop Actions

### **`click(x, y, click_type="left")`**

```python
def click(self, x: int, y: int, click_type: str = "left") -> None:
    """
    Move the mouse to (x, y) and click the specified button.
    click_type can be 'left', 'middle', or 'right'.
    """
```

**Arguments**:
- **x, y** *(int)*: The screen coordinates to move the mouse.
- **click_type** *(str)*: The mouse button to click (`"left"`, `"middle"`, or `"right"`).

**Returns**:
- `None`

---

### **`scroll(x, y, scroll_x=0, scroll_y=0)`**

```python
def scroll(
    self,
    x: int,
    y: int,
    scroll_x: int = 0,
    scroll_y: int = 0
) -> None:
    """
    Move to (x, y) and scroll horizontally or vertically.
    """
```

**Arguments**:
- **x, y** *(int)*: The screen coordinates to move the mouse.
- **scroll_x** *(int)*: Horizontal scroll offset.
  - Negative => Scroll left (button 6)
  - Positive => Scroll right (button 7)
- **scroll_y** *(int)*: Vertical scroll offset.
  - Negative => Scroll up (button 4)
  - Positive => Scroll down (button 5)

**Behavior**:
- Moves the mouse to `(x, y)`.
- Scrolls by scroll_x and scroll_y

**Returns**:
- `None`

---

### **`keypress(keys: list[str])`**

```python
def keypress(self, keys: list[str]) -> None:
    """
    Press (and possibly hold) keys in sequence.
    """
```

**Arguments**:
- **keys** *(list[str])*: A list of keys to press. Example: `["CTRL", "f"]` for Ctrl+F.

**Behavior**:
- Executes a keypress
- Supports shortcuts like Ctrl+Fs

**Returns**:
- `None`

---

### **`type_text(text: str)`**

```python
def type_text(self, text: str) -> None:
    """
    Type a string of text (like using a keyboard) at the current cursor location.
    """
```

**Arguments**:
- **text** *(str)*: The string of text to type.

**Behavior**:
- Types a string of text at the current cursor location.

**Returns**:
- `None`

---

### **`get_screenshot()`**

```python
def get_screenshot(self) -> str:
    """
    Takes a screenshot of the current desktop.
    Returns the base64-encoded PNG screenshot.
    """
```

**Behavior**:
- Takes a screenshot as a png
- Captures the base64 result.
- Returns that base64 string.

**Returns**:
- *(str)*: A base64-encoded PNG screenshot.

**Exceptions**:
- **RuntimeError** if the screenshot command fails.

---

## OpenAI Agent Integration

### **`action(input=None, user_input=None, safety_checks=None, pending_call=None)`**

 > Check out the [guide for using this function](#-guide-using-the-action-command) for more details

```python
def action(self, input=None, user_input=None, safety_checks=None, pending_call=None) -> dict:
    """
    Execute an action in the container environment. The action can be:
    - A brand-new user command
    - A continued conversation with user_input
    - A resumed computer_call (pending_call) that was previously halted for safety checks

    """
```

**Purpose**  
Allows the agent to perform actions in the container environment. It can either start a new command, continue a text-based conversation, or resume a previously halted computer call that needed safety checks.

**How It Works**  
1. **Normal text flow**:  
   - If you provide a brand-new command (`input`) without `user_input`, the agent starts a fresh action.  
   - If there’s existing conversation context (`input` as a stored response) and you provide `user_input`, the agent continues the dialogue.  

2. **Resuming a pending call**:  
   - If there’s a halted `pending_call` (from a previous safety check), the agent executes that call immediately instead of continuing text-based interaction.  

**Arguments**:

- **`input`**  
  A string command or a stored response object from the agent. If no conversation is ongoing, pass a simple text command to start. If continuing a session, pass the previous agent response.  

- **`user_input`**  
  Text you enter when the agent asks a follow-up question. Only needed if the agent specifically requests more info.  

- **`safety_checks`**  
  A list of safety check objects that you’ve acknowledged. If the agent previously flagged something for user approval, pass those checks back to proceed.

- **`pending_call`**  
  A call object returned in a prior response, indicating a system action is paused until safety checks are acknowledged. Once acknowledged, pass this object here to resume.

**Returns**:

A dictionary that may contain:
```json
{
  "result": { ... },           // The agent's current output or state
  "needs_input": [ ... ],      // (optional) Messages prompting the user for more input
  "safety_checks": [ ... ],    // (optional) Safety checks that must be acknowledged
  "pending_call": { ... }      // (optional) An action waiting for safety check confirmation
}
```

- **`result`**  
  The most recent output or actions from the agent.  

- **`needs_input`**  
  If present, the agent is prompting you for more information (a text message).  

- **`safety_checks`**  
  If present, you must confirm these checks to continue.  

- **`pending_call`**  
  If present, pass this object back into `action` along with any acknowledged checks to finalize the pending action.  

Use this function whenever you want the agent to do something in the desktop environment or continue an ongoing conversation. If the response indicates that user input or safety checks are required, provide them and call `action` again.

---

### **`handle_action(action_input, stored_response=None, user_input=None)`**

```python
def handle_action(self, action_input, stored_response=None, user_input=None):
    """
    Demo function to call and manage `action` loop and responses
    
    1) Call the desktop.action method to handle commands or continue interactions
    2) Print out agent prompts and safety checks
    3) If there's user input needed, prompt
    4) If there's a pending computer call with safety checks, ask user for ack, then continue
    5) Repeat until no further action is required
    """
```

**Purpose**  
Provides a simple, interactive loop for handling agent actions in the container environment. It repeatedly calls the `action` function, checks for agent prompts, requests user input when necessary, and manages safety checks or computer calls.

**Arguments**:
- **`action_input`** (str):  
  Your initial command or prompt to send to the agent.
- **`stored_response`** (object, optional):  
  A previously stored agent response you can resume from, if available.
- **`user_input`** (str, optional):  
  Any immediate user input to continue a prior conversation.

**How it works**:
1. **Initial call**:  
   Starts by calling `action` with the given `action_input` (or `stored_response`, if provided).
2. **Event loop**:  
   - Displays any messages the agent wants you to see (prompts or safety checks).  
   - If the agent needs more user input (`needs_input`), it prompts you and re-calls `action`.  
   - If there’s a pending computer call and safety checks to acknowledge, you can confirm them and proceed.  
3. **Completion**:  
   Repeats until no further input is required and no more calls are pending, returning the final result.

Use this function in a console or interactive environment to easily step through the agent’s conversation flow.

---

## 🚀 Guide: Using the `action` Command

The action function lets your agent perform tasks, manage conversations, and handle security checks in a flexible way. Whether you're building an interactive app or automating workflows behind the scenes. While many examples assume an interactive loop (where the user is asked for follow-up input and safety acknowledgments), you can structure it any way you like as long as you pass the right parameters back into `action`.

### 📌 Quick Overview

The `action` function accepts:

- **`input`**: A string command _or_ a previous result object (to keep the conversation going).  
<br>  

**Used when the initial `action` command needs more input or security checks**:
- **`user_input`**: Optional text from the user (if the agent asked for more info).  
- **`safety_checks`**: A list of checks acknowledged by the user.  
- **`pending_call`**: A “computer call” that was paused for safety checks and now needs execution.

It returns a dictionary that may contain:

- **`result`**: The agent’s output or partial response.  
- **`needs_input`**: A list of messages if the agent requests user text.  
- **`safety_checks`**: Any new safety checks the user must confirm.  
- **`pending_call`**: A call that’s awaiting user acknowledgment before it can execute.


### 🌀 Handling the Workflow (Interactive Example)

Imagine you're building something interactive—a command-line app, a chatbot, or even a simple UI. Your workflow might look like this:

1. **Start** by calling `action` with a user's command.
2. **Check** the returned dictionary for:  
   - `needs_input`: If present, the agent needs more input, collect that input from the user, then call `action` again.
     > 📝 **Important**: In this case, pass the full previously returned `result` into the `input` parameter when continuing 

   - `pending_call` + `safety_checks`: If both exist, confirm the checks and re-invoke `action` with `pending_call`.  
3. **Repeat** until the dictionary has no further `needs_input` or `pending_call`.  

Here’s a *short* pseudo-code example:

```python
result = agent.action(input="Open a file")

while True:
    if result.get("needs_input"):
        # Gather user input (could be from any source!)
        user_text = get_user_input_somehow()
        result = agent.action(
            input=result["result"], # Pass in the previously returned result object
            user_input=user_text,
            safety_checks=result.get("safety_checks")
        )
        continue
    
    if result.get("pending_call") and result.get("safety_checks"):
        # Confirm checks, then proceed
        confirm_safety_checks()
        result = agent.action(
            input=result["result"],
            pending_call=result["pending_call"],
            safety_checks=result["safety_checks"]
        )
        continue
    
    # Done if nothing else is needed
    break

print("Final result:", result["result"])
```


### 🤖 Automated (non-interactive) and Custom Workflows

You don’t **have** to prompt the user directly. For instance:

- You might store safety checks in a database or queue them for review.  
- You could automatically approve certain checks if your use case allows it.  
- You could read user input from a file or a GUI, rather than the console.

Regardless of how you gather approvals or input, your code must **still** supply the correct parameters back to `action` whenever you’re ready to continue. The workflow remains the same: pass in any `user_input`, previously returned `safety_checks`, or `pending_call` so the agent knows how to proceed.


### 4. Key Takeaways

- **After safety checks:** always pass back any relevant `safety_checks` or `pending_call` when resuming.
- **When agent needs input:** Handle `needs_input` by gathering user text (or any logic you choose), then call `action` again. Pass in the previously returned `result` object in the input argument.
- **Stop** once there’s no more needed input or calls.  

---

# Appendix

## Contributing

Feel free to open issues for any feature requests or if you encounter any bugs! We love and appreciate contributions of all forms.

### Pull Request Guidelines
1. **Fork the repo** and **create a new branch** from `main`.
2. **Commit changes** with clear and descriptive messages.
3. **Include tests**, if possible. If adding a feature or fixing a bug, please include or update the relevant tests.
4. **Open a Pull Request** with a clear title and description explaining your work.

## Roadmap

- Support for other computer-use agents
- Support for browser-only envrionments
- Integrating human-in-the-loop
- (and much more...)

## Team

<div align="center">
  <img src="./static/team.png" width="200"/>
</div>

<div align="center">
Made with ❤️ in San Francisco
</div>
