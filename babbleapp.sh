#!/bin/bash

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then    
    echo "Error: This script is only compatible with Linux operating systems."    
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then    
    echo "Error: Python is not installed. Please install Python 3.8 or higher."    
    exit
fi  
    
python_version_major=$(python3 -c 'import platform; print(platform.python_version_tuple()[0])')
python_version_minor=$(python3 -c 'import platform; print(platform.python_version_tuple()[1])')
if (( python_version_major < 3 || python_version_minor < 8 )); then    
    echo "Error: Your Python version is too low! Please install 3.8 or higher."    
    exit 1
fi

# Set installation directory
install_dir="$HOME/.local/share/project-babble"

# Function to install requirements
install_requirements() {
    cd $install_dir
    cd BabbleApp
    echo "Installing requirements..."
    # Create a temporary requirements file without the Windows-only package
    grep -v "onnxruntime-directml" requirements.txt > linux_requirements.txt
    pip install -r linux_requirements.txt --quiet
    rm linux_requirements.txt
}

# Function to get the latest release tag
get_latest_tag() {
    git fetch --tags
    git describe --tags --abbrev=0
}

# Function to update the repository
update_repo() {
    echo "Checking for updates..."
    git fetch --tags
    local_tag=$(git describe --tags --abbrev=0)
    remote_tag=$(git describe --tags --abbrev=0 origin/main)
    
    if [ "$local_tag" != "$remote_tag" ]; then
        echo "New version available: $remote_tag"
        echo "Current version: $local_tag"
        echo "Updating to the latest version..."
        git checkout "$remote_tag"
        echo "Updating dependencies..."
        source venv/bin/activate
        install_requirements
        deactivate
        echo "Project Babble has been updated successfully to version $remote_tag!"
    else
        echo "Project Babble is already at the latest version: $local_tag"
    fi
}


cd $install_dir
cd BabbleApp

# Create venv if it does not exists
if ! [ -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate  
update_repo
echo "Verifying dependencies. This might take a second!"
install_requirements
echo "Starting Babble app..."
python3 babbleapp.py