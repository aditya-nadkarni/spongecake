Notes from looking into Windows set-up 
- Use UTM (https://www.utm.app/) to run virtual machines. 
- Download official windows iso from site
- Can use temporarily without product key but recommend purchasing if looking for long-term usage
- Will need to figure out how to install UTM via startup script (example here)
```bash
# Install Homebrew if not already installed (optional)
if ! command -v brew &> /dev/null; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install UTM
brew install --cask utm
```
- Apparently will need to create a UTM template. This should be created by creating a VM in UTM and then saving it as a template.
- Will need to point to a URL to download the ISO (example below - need to figure out how to handle long running process here, and communicating to the user)
```bash
# Define the download URL and destination path
ISO_URL="https://cdimage.ubuntu.com/releases/22.04/release/ubuntu-22.04.4-live-server-arm64.iso"
ISO_PATH="$HOME/Downloads/ubuntu-arm64.iso"

# Download the ISO if it doesn't exist
if [ ! -f "$ISO_PATH" ]; then
  echo "Downloading Ubuntu ISO..."
  curl -L "$ISO_URL" -o "$ISO_PATH"
fi
```

Then need to configure ISO path in UTM set-up
```bash
# Path to your UTM template (modify this as needed)
TEMPLATE_PATH="$HOME/Documents/UTM VMs/MyUbuntu.utm/Info.plist"

# Update the ISO path in the UTM configuration
/usr/libexec/PlistBuddy -c "Set :System:BootImage:Path $ISO_PATH" "$TEMPLATE_PATH"
```

Then the VM should be able to programatically start with (utmctl start "MyUbuntu"). You can also pass commands to it using SSH - but we need to look into that 


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

<h1 align="center">Open Source Operator for Computer Use</h1>
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
    Using spongecake to automate linkedin prospecting (see examples/linkedin_example.py)
  </p>
</div>

[![PyPI version](https://img.shields.io/pypi/v/spongecake.svg)](https://pypi.org/project/spongecake/)
![PyPI - License](https://img.shields.io/pypi/l/spongecake)
[![Documentation](https://img.shields.io/badge/documentation-link-brightgreen?style=flat)](https://docs.spongecake.ai/quickstart)
![GitHub repo size](https://img.shields.io/github/repo-size/aditya-nadkarni/spongecake)
[![GitHub stars](https://img.shields.io/github/stars/aditya-nadkarni/spongecake)](https://img.shields.io/github/stars/aditya-nadkarni/spongecake)
[![Discord](https://img.shields.io/discord/1357076134365233166?color=7289DA&label=Discord/Support&logo=discord&logoColor=white)](https://discord.gg/3KDmjAd98w)

## What is spongecake?

🍰 **spongecake** is the easiest way to create your own OpenAI Operator that can use computers. These agents can scrape, fill out forms, and interact with websites or local apps. It simplifies:
- **Spinning up** a Docker container with a virtual desktop (including Xfce, VNC, etc.).
- **Controlling** that virtual desktop programmatically using an SDK (click, scroll, keyboard actions).
- **Integrating** with OpenAI to drive an agent that can interact with a real Linux-based GUI.

--- 

# Quick Start

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
3. **Run the backend and frontend**:

    In the spongecake directory, run:
    ```bash
    cd spongecake-ui
    cd frontend
    npm run dev
    ```
    In a new terminal, run:
    ```bash
    cd spongecake-ui
    cd backend
    python server.py
    ```
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
