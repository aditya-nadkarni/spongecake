#!/bin/bash
# Script to install the required dependencies for spongecake

echo "Installing spongecake dependencies..."

# Install the package in development mode
pip install -e ./spongecake

# Ensure marionette-driver is installed
pip install marionette-driver>=3.0.0

echo "Dependencies installed successfully!"
