#!/usr/bin/env bash

# Exit on error
set -e

# -----------------------------
# Define ANSI color codes
BOLD='\033[1m'
UNDERLINE='\033[4m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
RESET='\033[0m'
# -----------------------------

# Helper function to print big/warning messages
function print_warning {
  echo -e "${YELLOW}****************************************************************${RESET}"
  echo -e "${YELLOW}${BOLD}$1${RESET}"
  echo -e "${YELLOW}****************************************************************${RESET}"
}

function print_error {
  echo -e "${RED}****************************************************************${RESET}"
  echo -e "${RED}${BOLD}ERROR: $1${RESET}"
  echo -e "${RED}****************************************************************${RESET}"
}

function print_info {
  echo -e "${BLUE}${BOLD}$1${RESET}"
}

function print_success {
  echo -e "${GREEN}${BOLD}$1${RESET}"
}

# -------------
# Helper function to compare Python versions
check_python_version() {
    local desired_version="3.9"
    local installed_version
    installed_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")

    # We'll do a crude numeric comparison with sort -V
    if [[ $(echo -e "${installed_version}\n${desired_version}" | sort -V | head -n1) == "${desired_version}" ]]; then
        # installed_version >= desired_version
        return 0
    else
        return 1
    fi
}

# -----------------------------
# Detect OS
OS_TYPE="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="mac"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
    OS_TYPE="windows"
fi

print_info "Detected OS: $OS_TYPE"

# -----------------------------
# 1. Ensure Docker is installed
if [[ "$OS_TYPE" == "linux" ]]; then
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found. Installing Docker (Debian/Ubuntu style)..."

        # Update package info (Debian/Ubuntu). Modify for Fedora/etc. as needed.
        sudo apt-get update
        sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

        # Add Docker GPG key & repo
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
          | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
          https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" \
          | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Install Docker Engine
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
        print_success "Docker installation complete."
    else
        print_info "Docker is already installed."
    fi

    # 2. Ensure Docker daemon is running
    if ! sudo systemctl is-active docker >/dev/null; then
        print_info "Starting docker daemon..."
        sudo systemctl start docker
    fi
    print_success "Docker daemon is running."

elif [[ "$OS_TYPE" == "mac" ]]; then
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found. Please install Docker Desktop for macOS from:
  https://www.docker.com/products/docker-desktop/#:~:text=Download%20Docker%20Desktop
Then re-run this script after installation."
        exit 1
    else
        print_warning "Docker was found, but please ensure Docker Desktop is running."
    fi

elif [[ "$OS_TYPE" == "windows" ]]; then
    print_warning "Windows environment detected.
Please ensure Docker Desktop is installed and running before proceeding.
Download link: https://www.docker.com/products/docker-desktop/#:~:text=Download%20Docker%20Desktop
Then re-run this script from a suitable shell (Git Bash, etc.)"
    exit 1
else
    print_error "Unknown OS. Please install Docker manually."
    exit 1
fi

# -----------------------------
# 3. Check Python version (>= 3.9); attempt to install if on Linux
if check_python_version; then
    print_info "Python 3.9+ is already installed."
else
    if [[ "$OS_TYPE" == "linux" ]]; then
        print_warning "Python 3.9+ not found. Installing python3.9..."
        sudo apt-get update
        sudo apt-get install -y python3.9 python3.9-venv python3.9-dev
        print_success "Python 3.9 installed."
    else
        print_warning "Python 3.9+ is required, but not detected.
Please install it manually:
  macOS: https://www.python.org/downloads/macos/
  Windows: https://www.python.org/downloads/windows/
Then re-run this script."
        exit 1
    fi
fi

# -----------------------------
# 4. Create and activate virtual environment, then install dependencies
if command -v python3.9 &>/dev/null; then
    PY_CMD="python3.9"
else
    PY_CMD="python3"
fi

print_info "Creating virtual environment with $PY_CMD..."
$PY_CMD -m venv venv

# Activate the virtual environment
# (On Windows + Git Bash: 'source venv/Scripts/activate')
print_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
python -m pip install --upgrade pip

# Install required packages
print_info "Installing dependencies: spongecake, dotenv, openai..."
python -m pip install --upgrade spongecake dotenv openai

echo
echo -e "${GREEN}=============================================================${RESET}"
echo -e "${GREEN}${BOLD}Setup complete!${RESET}"
echo -e "${GREEN}=============================================================${RESET}"
echo
echo -e "To use your new virtual environment, run:"
echo -e "  ${CYAN}${BOLD}source venv/bin/activate${RESET}"
echo
echo -e "Please ensure ${CYAN}${BOLD}Docker Desktop${RESET} is running."
echo