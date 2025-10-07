#!/bin/bash
# setup.sh - Linux/macOS setup script for MediaHub Enhanced Final

echo "Setting up MediaHub Enhanced Final..."

# Check for Python 3
if ! command -v python3 &> /dev/null
then
    echo "Python 3 not found. Please install Python 3.9+."
    exit 1
fi

# Install pip dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install Python dependencies."
    exit 1
fi

echo "Setup complete. You can now run the application using run.sh"
