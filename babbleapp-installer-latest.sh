#!/bin/bash

# Check if running on a supported operating system
if [[ "$OSTYPE" != "linux-gnu"* ]] && [[ "$OSTYPE" != "darwin"* ]]; then    
    echo "Error: This script is only compatible with Linux and macOS operating systems."    
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then    
    echo "Error: Python is not installed. Please install Python 3.8 or higher."    
    exit 1
fi  
    
python_version_major=$(python3 -c 'import platform; print(platform.python_version_tuple()[0])')
python_version_minor=$(python3 -c 'import platform; print(platform.python_version_tuple()[1])')
if (( python_version_major < 3 || python_version_minor < 8 )); then    
    echo "Error: Your Python version is too low! Please install 3.8 or higher."    
    exit 1
fi

install_dir="$HOME/.local/share/project-babble"
bin_dir="$HOME/.local/bin"

# Create installation directory if it doesn't exist
mkdir -p "$install_dir"

# Function to install requirements
install_requirements() {
    cd "$install_dir"
    cd BabbleApp
    echo "Installing requirements..."
    # Create a temporary requirements file without the Windows-only package
    grep -v "onnxruntime-directml" requirements.txt > unix_requirements.txt
    pip install -r unix_requirements.txt --quiet
    rm unix_requirements.txt
}

# Function to get the latest commit hash
get_latest_commit() {
    git fetch origin main
    git rev-parse origin/main
}

# Function to get the current commit hash
get_current_commit() {
    git rev-parse HEAD
}

# Function to update the repository
update_repo() {
    echo "Checking for updates..."
    git fetch origin main
    local_commit=$(get_current_commit)
    remote_commit=$(get_latest_commit)
    
    if [ "$local_commit" != "$remote_commit" ]; then
        echo "New version available"
        echo "Current commit: ${local_commit:0:8}"
        echo "Latest commit: ${remote_commit:0:8}"
        echo "Updating to the latest version..."
        git checkout main
        git pull origin main
        echo "Updating dependencies..."
        source venv/bin/activate
        install_requirements
        deactivate
        echo "Project Babble has been updated successfully to commit ${remote_commit:0:8}!"
    else
        echo "Project Babble is already at the latest commit: ${local_commit:0:8}"
    fi
}

# Ensure we're in the correct directory
cd "$install_dir"
cd BabbleApp

# Create venv if it does not exist
if ! [ -d "venv" ]; then
    python3 -m venv venv
fi

# Use the correct activation script based on OS
source venv/bin/activate
update_repo
echo "Verifying dependencies. This might take a second!"
install_requirements
echo "Starting Babble app..."
python3 babbleapp.py