<div align="center">
  <picture>
    <source srcset="./static/spongecake-dark.png" media="(prefers-color-scheme: dark)">
    <img 
      src="./static/spongecake-light.png" 
      alt="spongecake logo" 
      width="700"
    >
  </picture>
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

## What is spongecake?

🍰 **spongecake** is the easiest way to launch OpenAI-powered “computer use” agents that scrape, fill out forms, and interact with websites or local apps. It simplifies:
- **Spinning up** a Docker container with a virtual desktop (including Xfce, VNC, etc.).
- **Controlling** that virtual desktop programmatically using an SDK (click, scroll, keyboard actions).
- **Integrating** with OpenAI to drive an agent that can interact with a real Linux-based GUI.

--- 

## Prerequisites

### Option A: Automatic Setup

1. **Clone this repository** (if you haven’t already):
   ```bash
   git clone https://github.com/aditya-nadkarni/spongecake.git
   cd spongecake
   ```
2. **Run the setup script**:
   ```bash
   chmod +x setup.sh  # May be required on Unix/macOS
   ./setup.sh
   ```
   - Installs dependencies and creates a Python virtual environment (venv) for you.
   - Prompts you if a dependency (like Docker) can’t be installed automatically.
   - If you install a dependency manually, re-run `./setup.sh` to continue.
3. **Activate the new venv**:
   ```bash
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

### Option B: Manual Setup

If you prefer to set things up yourself or the setup script fails:

- [**Docker**](https://docs.docker.com/get-docker/) (ensure it’s running)
- [**Python 3.9+**](https://www.python.org/downloads/)
- [**OpenAI API Key**](https://platform.openai.com/)
  > **Note:** Make sure Docker Desktop is running on macOS/Windows.

1. **Create and activate a Python venv**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
2. **Install spongecake and required packages**:
   ```bash
   pip install --upgrade spongecake dotenv openai
   ```
3. **Ensure Docker is running** and you have your OpenAI API Key ready.

---

# Quick Start

1. **Verify prerequisites are met** (Docker installed and running, Python 3.9+, OpenAI API key).
2. **Activate the Python venv** (either created by `setup.sh` or manually):
   ```bash
   source venv/bin/activate
   ```
3. **Create a `.env` file** (in the `examples` folder) and update your OpenAI key:
   ```bash
   cd examples
   cp .env.example .env
   # Edit .env to add OPENAI_API_KEY
   ```
   Update `OPENAI_API_KEY` in the `.env` file to your OpenAI API key found in the [API platform](https://platform.openai.com/settings) (find API keys in the left nav bar)  

4. **Run the example script**:
   ```bash
   python example.py
   ```
   - This deploys a Docker container locally and uses the `.env` for your OpenAI credentials.
   - If the default spongecake image isn’t present, Docker will pull it from Docker Hub.

   Feel free to edit `example.py` to try out your own commands.  
> **Note:** This deploys a Docker container in your local Docker environment. If the spongecake default image isn't available, it will pull the image from Docker Hub.
---

# Documentation

See [full documentation](https://docs.spongecake.ai/quickstart) for more details and examples.

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

## Form Filling 

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
    Using spongecake to automate form filling (see examples/data_entry_example.py)
  </p>
</div>


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
