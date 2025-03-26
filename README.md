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

## What is spongecake?

🍰 **spongecake** is the easiest way to launch OpenAI-powered “computer use” agents that scrape, fill out forms, and interact with websites or local apps. It simplifies:
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
