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
    <source media="(prefers-color-scheme: dark)" srcset="./static/linkedin-example.gif" />
    <img 
      alt="[coming soon] Shows a demo of spongecake in action" 
      src="./static/linkedin-example.gif" 
      style="width: 100%; max-width: 700px;"
    />
  </picture>
  <p style="font-size: 1.2em; margin-top: 10px; text-align: center; color: gray;">
    Using spongecake to automate linkedin prospecting (see examples/linkedin_example.py)
  </p>
</div>

[![PyPI version](https://img.shields.io/pypi/v/spongecake.svg)](https://pypi.org/project/spongecake/)
![PyPI - License](https://img.shields.io/pypi/l/spongecake)
[![Documentation](https://img.shields.io/badge/documentation-link-brightgreen?style=flat)](https://docs.spongecake.ai/quickstart)
![GitHub repo size](https://img.shields.io/github/repo-size/aditya-nadkarni/spongecake)
[![GitHub stars](https://img.shields.io/github/stars/aditya-nadkarni/spongecake)](https://img.shields.io/github/stars/aditya-nadkarni/spongecake)


## Table of Contents
1. [What is spongecake?](#what-is-spongecake)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Demos](#demos)
    1. [Linkedin Prospecting](#linkedin-prospecting)
    2. [Amazon Shopping](#amazon-shopping)
5. [\(Optional\) Building & Running the Docker Container](#optional-building--running-the-docker-container)
6. [Connecting to the Virtual Desktop](#connecting-to-the-virtual-desktop)
7. [Contributing](#contributing)
8. [Roadmap](#roadmap)
9. [Team](#team)

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
   ```
2. **Set up a Python virtual environment and install the spongecake package**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate

   python3 -m pip install --upgrade spongecake
   python3 -m pip install --upgrade dotenv
   python3 -m pip install --upgrade openai  
   ```

3. **Start docker, update your OpenAI keys, and run the example script**:  
  Run docker desktop ([install here if needed](https://docs.docker.com/desktop/setup/install/mac-install/))

    Update OpenAI key
    ```bash
    cd examples 
    cp .env.example .env
    ```
    Then update OPENAI_API_KEY in the .env file to your OpenAI key in the API platform: https://platform.openai.com/settings (find API keys in the left nav bar)

    Then run the example script: 
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
    <source media="(prefers-color-scheme: dark)" srcset="./static/linkedin-example.gif" />
    <img 
      alt="[coming soon] Shows a demo of spongecake in action" 
      src="./static/linkedin-example.gif" 
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
    <source media="(prefers-color-scheme: dark)" srcset="./static/amazon-example.gif" />
    <img 
      alt="[coming soon] Shows a demo of spongecake in action" 
      src="./static/amazon-example.gif" 
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
    <source media="(prefers-color-scheme: dark)" srcset="./static/data-entry-example.gif" />
    <img 
      alt="[coming soon] Shows a demo of spongecake in action "
      src="./static/data-entry-example.gif" 
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



# Computer Use Agent Best Practices
- Reliability is still not great for computer-use agents. If you want better reliability, the best thing is to write GOOD prompts and SPLIT up your meaty prompts/tasks into smaller chunks
- Good prompts generally have the following properties: 
  - **STOP** conditions (e.g., You should ALWAYS stop when you see the bottom of the page)
  - **INTERACTION** conditions (e.g., You should NEVER scroll up)
  - **RETURN** format/structure (e.g., Always return a JSON object with this structure 'example' : ['value1', 'value2'])
  - See these properties in action in examples like `examples/linkedin_example.py` or `examples/amazon_example.py`
- When building your agents with spongecake, we recommend having your VM pulled up in a VNC viewer so you can jump in and control the desktop if needed (see [Connecting to the Virtual Desktop](#connecting-to-the-virtual-desktop))
- Think about what tasks can be done concurrently. E.g., can multiple agents work together to fill out a form? Or what if agent 1 performs actions on page 1, agent 2 performs actions on page 2, and so forth? We're working on making it easier to spin up agents concurrently 

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

## Benchmarks 
[coming soon - will compare against Operator, WebVoyager etc]

## Team

<div align="center">
  <img src="./static/team.png" width="200"/>
</div>

<div align="center">
Made with 🍰 in San Francisco
</div>
