<div align="center">
  <img 
    src="../static/spongecake-light.png" 
    alt="spongecake logo" 
    width="700" 
  >
</div>


<h1 align="center">Open source SDK to launch OpenAI computer use agents</h1>
<div style="text-align: center;">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../static/linkedin-example.gif" />
    <img 
      alt="[coming soon] Shows a demo of spongecake in action" 
      src="../static/linkedin-example.gif" 
      style="width: 100%; max-width: 700px;"
    />
  </picture>
  <p style="font-size: 1.2em; margin-top: 10px; text-align: center; color: gray;">
    Using spongecake to automate linkedin prospecting (see examples/linkedin_example.py)
  </p>
</div>

## Table of Contents
1. [What is spongecake?](#what-is-spongecake)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Demos](#demos)
    1. [Linkedin Prospecting](#linkedin-prospecting)
    2. [Amazon Shopping](#amazon-shopping)
5. [\(Optional\) Building & Running the Docker Container](#optional-building--running-the-docker-container)
6. [Connecting to the Virtual Desktop](#connecting-to-the-virtual-desktop)
7. [Documentation](#documentation)
   1. [Desktop Client Documentation](#desktop-client-documentation)
      - [Class: `Desktop`](#class-desktop)
        - [start()](#start)
        - [stop()](#stop)
        - [exec()](#exec)
      - [Desktop Actions](#desktop-actions)
        - [click(x, y, click_type="left")](#clickx-y-click_typeleft)
        - [scroll(x, y, scroll_x=0, scroll_y=0)](#scrollx-y-scroll_x0-scroll_y0)
        - [keypress(keys: liststr)](#keypresskeys-liststr)
        - [type_text(text)](#type_texttext)
        - [get_screenshot()](#get_screenshot)
      - [OpenAI Agent Integration](#openai-agent-integration)
        - [action(...)](#actioninput_textnone-acknowledged_safety_checksfalse-ignore_safety_and_inputfalse-complete_handlernone-needs_input_handlernone-needs_safety_check_handlernone-error_handlernone)
        - [Guide: Using the `action` Command](#-guide-using-the-action-command)
8. [Contributing](#contributing)
9. [Roadmap](#roadmap)
10. [Team](#team)

## What is spongecake?

🍰 **spongecake** is the easiest way to launch OpenAI-powered “computer use” agents. It simplifies:
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
   cd spongecake/examples
   ```
2. **Set up a Python virtual environment and install the spongecake package**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate

   python3 -m pip install --upgrade spongecake
   python3 -m pip install --upgrade dotenv
   python3 -m pip install --upgrade openai  # Make sure you have the latest version of openai for the responses API
   ```
3. **Run the example script**:  
   ```bash
   cd examples # If needed
   ```
   ```bash
   python3 example.py
   ```
   Feel free to edit the `example.py` script to try out your own commands.  
   <br>
   > **Note:** This deploys a Docker container in your local Docker environment. If the spongecake default image isn't available, it will pull the image from Docker Hub.

4. **Create your own scripts**:
  The example script is largely for demonstration purposes. To make this work for own use cases, create your own scripts using the SDK or integrate it into your own systems.

---

# Demos

## LinkedIn Prospecting 

<div style="text-align: center;">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../static/linkedin-example.gif" />
    <img 
      alt="[coming soon] Shows a demo of spongecake in action" 
      src="../static/linkedin-example.gif" 
      style="width: 100%; max-width: 700px;"
    />
  </picture>
  <p style="font-size: 1.2em; margin-top: 10px; text-align: center; color: gray;">
    Using spongecake to automate linkedin prospecting (see examples/linkedin_example.py)
  </p>
</div>

## Amazon Shopping 

<div style="text-align: center;">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../static/amazon-example.gif" />
    <img 
      alt="[coming soon] Shows a demo of spongecake in action" 
      src="../static/amazon-example.gif" 
      style="width: 100%; max-width: 700px;"
    />
  </picture>
  <p style="font-size: 1.2em; margin-top: 10px; text-align: center; color: gray;">
    Using spongecake to automate amazon shopping (see examples/amazon_example.py)
  </p>
</div>

## Data Entry 

<div style="text-align: center;">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../static/data-entry-example.gif" />
    <img 
      alt="[coming soon] Shows a demo of spongecake in action" 
      src="../static/data-entry-example.gif" 
      style="width: 100%; max-width: 700px;"
    />
  </picture>
  <p style="font-size: 1.2em; margin-top: 10px; text-align: center; color: gray;">
    Using spongecake to automate data entry (see examples/data_entry_example.py)
  </p>
</div>



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

### **`action(input_text=None, acknowledged_safety_checks=False, ignore_safety_and_input=False, complete_handler=None, needs_input_handler=None, needs_safety_check_handler=None, error_handler=None)`**

 > Check out the [guide for using this function](#-guide-using-the-action-command) for more details

### Purpose

The `action` function lets you control the desktop environment via an agent, managing commands, user inputs, and security checks in a streamlined way.

### Arguments

- **`input_text`** *(str, optional)*:  
  New commands or responses to agent prompts.

- **`acknowledged_safety_checks`** *(bool, optional)*:  
  Set `True` after the user confirms pending security checks.

- **`ignore_safety_and_input`** *(bool, optional)*:  
  Automatically approves security checks and inputs. **Use cautiously.**

- **Handlers** *(callables, optional)*:  
  Customize how different statuses are handled:
  - **`complete_handler(data)`**: Final results.
  - **`needs_input_handler(messages)`**: Collects user input.
  - **`needs_safety_check_handler(safety_checks, pending_call)`**: Approves security checks.
  - **`error_handler(error_message)`**: Manages errors.

### How it works

The `action` function returns one of four statuses:

### Status Handling

- **COMPLETE**:  
  Task finished successfully. Handle final output.

- **ERROR**:  
  Review the returned error message and handle accordingly.

- **NEEDS_INPUT**:  
  Provide additional user input and call `action()` again with this input.

- **NEEDS_SECURITY_CHECK**:  
  Review security warnings and confirm with `acknowledged_safety_checks=True`.

Example workflow:
```python
status, data = agent.action(input_text="Open Chrome")

if status == AgentStatus.COMPLETE:
    print("Done:", data)
elif status == AgentStatus.ERROR:
    print("Error:", data)
elif status == AgentStatus.NEEDS_INPUT:
    user_reply = input(f"Input needed: {data}")
    agent.action(input_text=user_reply)
elif status == AgentStatus.NEEDS_SECURITY_CHECK:
    confirm = input(f"Security checks: {data['safety_checks']} Proceed? (y/N): ")
    if confirm.lower() == "y":
        agent.action(acknowledged_safety_checks=True)
    else:
        print("Action cancelled.")
```

### Auto Mode

Set `ignore_safety_and_input=True` for automatic handling of inputs and security checks. Use carefully as this bypasses user prompts and approvals.

### Using Handlers

Provide handler functions to automate status management, simplifying your code:

```python
agent.action(
    input_text="Open Chrome",
    complete_handler=lambda data: print("Done:", data),
    error_handler=lambda error: print("Error:", error),
    needs_input_handler=lambda msgs: input(f"Agent asks: {msgs}"),
    needs_safety_check_handler=lambda checks, call: input(f"Approve {checks}? (y/N): ").lower() == "y"
)
```

---
## 🚀 Guide: Using the `action` Command

The `action` function lets your agent execute tasks in the desktop environment. It handles:

- **Starting a new conversation** with a command.
- **Continuing a conversation** by supplying user input.
- **Acknowledging safety checks** for a pending call.
- **Auto-handling safety checks and input** if `ignore_safety_and_input=True`.
- **Custom handler delegation** for each status.

Internally, `action` manages state and either returns a `(status, data)` tuple for you to process or calls the appropriate handler if provided.

---

### 📌 Quick Overview

```python
def action(
    input_text=None,
    acknowledged_safety_checks=False,
    ignore_safety_and_input=False,
    complete_handler=None,
    needs_input_handler=None,
    needs_safety_check_handler=None,
    error_handler=None
):
    # ...
```

- **`input_text`** (str, optional):
  - A new command to start a conversation.
  - A user’s response if the agent has asked for more input.
  - `None` if you’re just confirming safety checks.

- **`acknowledged_safety_checks`** (bool, optional):
  - Indicates that the user has confirmed pending checks.
  - Only relevant if a **NEEDS_SECURITY_CHECK** status was returned previously.

- **`ignore_safety_and_input`** (bool, optional):
  - If `True`, the function automatically handles safety checks and input requests, requiring no user interaction.

- **Handlers** (callables, optional):
  - `complete_handler(data)`: Handles **COMPLETE**.
  - `needs_input_handler(messages)`: Handles **NEEDS_INPUT**.
  - `needs_safety_check_handler(checks, pending_call)`: Handles **NEEDS_SECURITY_CHECK**.
  - `error_handler(error_message)`: Handles **ERROR**.

**Return Value**:

- **A tuple** `(status, data)`, where:
  - **status** is one of:
    - **COMPLETE**: The agent finished successfully.
    - **ERROR**: An error occurred.
    - **NEEDS_INPUT**: The agent needs more user input.
    - **NEEDS_SECURITY_CHECK**: The agent needs confirmation for a risky action.
  - **data**:
    - **For COMPLETE**: The final response object.
    - **For ERROR**: An error message.
    - **For NEEDS_INPUT**: A list of messages asking for input.
    - **For NEEDS_SECURITY_CHECK**: A list of safety checks and the pending call.

When handlers are provided, `action` may not return a status in the usual way—it delegates behavior to those handlers.

---

### 🌀 Handling the Workflow (Interactive Example)

`action` covers multiple scenarios:

1. **Starting a conversation** with `input_text` (e.g., a command: “Open Chrome”).
2. **Continuing a conversation** by providing user input if the agent is waiting for it.
3. **Acknowledging safety checks** with `acknowledged_safety_checks=True` if the agent flagged a security concern.
4. **Auto-handling** if `ignore_safety_and_input=True`, which bypasses user checks.

When you call `action`, you get `(status, data)` back (unless you use handlers). Use `status` to decide your next move:

- **COMPLETE**:
  - The task is done. `data` contains the final response.
  - You can display or log it.

- **ERROR**:
  - `data` holds an error message explaining what went wrong.
  - You can retry, log, or show it to the user.

- **NEEDS_INPUT**:
  - The agent requires more information. Use `data` (often a list of prompts) to know what it wants.
  - Get input from the user, then call `action` again, **supplying that text in `input_text`**.

- **NEEDS_SECURITY_CHECK**:
  - The agent found a risky action. You must confirm it’s safe.
  - Call `action` again with **`acknowledged_safety_checks=True`** to proceed.
  - No extra `input_text` is required unless the agent specifically requests it.

Here’s a straightforward example:

```python
status, data = agent.action(input_text="Open Firefox")

if status == AgentStatus.COMPLETE:
    print("Done:", data)
elif status == AgentStatus.ERROR:
    print("Error:", data)
elif status == AgentStatus.NEEDS_INPUT:
    user_reply = input(f"Input needed: {data}")
    agent.action(input_text=user_reply)
elif status == AgentStatus.NEEDS_SECURITY_CHECK:
    confirm = input(f"Security checks: {data['safety_checks']} Proceed? (y/N): ")
    if confirm.lower() == "y":
        agent.action(acknowledged_safety_checks=True)
    else:
        print("Action cancelled.")
```

For a more robust loop-based approach:

```python
status, data = agent.action(input_text="Open a file")

while status in [AgentStatus.NEEDS_INPUT, AgentStatus.NEEDS_SECURITY_CHECK]:
    if status == AgentStatus.NEEDS_INPUT:
        user_reply = input(f"Agent needs more info: {data}")
        status, data = agent.action(input_text=user_reply)
    elif status == AgentStatus.NEEDS_SECURITY_CHECK:
        confirm = input(f"Security checks: {data['safety_checks']} Proceed? (y/N): ")
        if confirm.lower() == "y":
            status, data = agent.action(acknowledged_safety_checks=True)
        else:
            print("Action cancelled.")
            break

if status == AgentStatus.COMPLETE:
    print("Final result:", data)
elif status == AgentStatus.ERROR:
    print("Error:", data)
```

---

### 🤖 Automated (Non-Interactive) Mode

Set **`ignore_safety_and_input=True`** to:

- Automatically approve safety checks.
- Automatically generate responses to agent questions to continue with the prompt

This is useful for:
- Automated actions that must run without user interaction.
- Headless or server-based scenarios.

**CAUTION:** It is inherently risky because **you skip all manual confirmations and user input**. Ensure your applications and use cases are safe before using auto mode.

Example:

```python
status, data = agent.action(
    input_text="Open Chrome",
    ignore_safety_and_input=True
)

if status == AgentStatus.COMPLETE:
    print("Completed:", data)
elif status == AgentStatus.ERROR:
    print("Error:", data)
```

---

### Examples Using Handlers

You can avoid manual `if/else` checks by supplying **handlers** for each status. `action` will call them automatically:

- **`complete_handler(data)`**: Called when the agent finishes.
- **`needs_input_handler(messages)`**: Called if the agent wants more input.
- **`needs_safety_check_handler(safety_checks, pending_call)`**: Called if the agent flags a safety check.
- **`error_handler(error_message)`**: Called if something goes wrong.

#### Why Handlers?
- They allow **complex logic** in a more organized, modular style.
- They help you **integrate** with other tools or services, since each status is handled by a dedicated function.
- They reduce repeated conditional code in your main flow.

Example:

```python
result = [None]  # a mutable container to store final output or None

def complete_handler(data):
    """COMPLETE -- handle final results"""
    print("\n✅ Task completed successfully!")
    result[0] = data

def needs_input_handler(messages):
    """NEEDS_INPUT -- prompt the user and return the response"""
    for msg in messages:
        if hasattr(msg, "content"):
            text_parts = [part.text for part in msg.content if hasattr(part, "text")]
            print(f"\n💬 Agent asks: {' '.join(text_parts)}")

    user_says = input("Enter your response (or 'exit'/'quit'): ").strip()
    if user_says.lower() in ("exit", "quit"):
        print("Exiting as per user request.")
        result[0] = None
        return None
    return user_says

def needs_safety_check_handler(safety_checks, pending_call):
    """NEEDS_SAFETY_CHECK -- confirm or deny safety checks"""
    for check in safety_checks:
        if hasattr(check, "message"):
            print(f"☢️  Pending Safety Check: {check.message}")

    ack = input("Type 'ack' to confirm, or 'exit'/'quit': ").strip().lower()
    if ack in ("exit", "quit"):
        print("Exiting as per user request.")
        result[0] = None
        return False
    if ack == "ack":
        print("Acknowledged. Proceeding with the computer call...")
        return True
    return False

def error_handler(error_message):
    """ERROR -- print error and store None"""
    print(f"😱 ERROR: {error_message}")
    result[0] = None

# Provide handlers to `action`:
status, data = desktop.action(
    input_text="Open Chrome",
    complete_handler=complete_handler,
    needs_input_handler=needs_input_handler,
    needs_safety_check_handler=needs_safety_check_handler,
    error_handler=error_handler
)
```

When handlers are specified, `action` manages each status internally and continues until it hits **COMPLETE** or **ERROR** (unless you stop it prematurely).

---

### 4. Key Takeaways

1. **Scenarios**: Start new tasks, resume with user input, or confirm safety checks.
2. **Statuses**: Always handle COMPLETE, ERROR, NEEDS_INPUT, NEEDS_SECURITY_CHECK.
3. **Resuming**: Pass new input (`input_text`) or confirm checks (`acknowledged_safety_checks=True`) to continue.
4. **Auto-mode**: `ignore_safety_and_input=True` is convenient but risky.
5. **Handlers**: Offer a cleaner, more modular way to manage status-based logic.

> For any additional questions, contact [founders@passage-team.com](mailto:founders@passage-team.com)
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
  <img src="../static/team.png" width="200"/>
</div>

<div align="center">
Made with 🍰 in San Francisco
</div>
