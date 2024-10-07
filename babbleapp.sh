#!/bin/bash

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then    
    echo "Error: This script is only compatible with Linux operating systems."    
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then    
    echo "Error: Python is not installed. Please install Python 3.11 or higher."    
    exit
fi  
    
python_version_major=$(python3 -c 'import platform; print(platform.python_version_tuple()[0])')
python_version_minor=$(python3 -c 'import platform; print(platform.python_version_tuple()[1])')
if (( python_version_major < 3 || python_version_minor < 11 )); then    
    echo "Error: Your Python version is too low! Please install 3.11 or higher."    
    exit 1
fi

# Set installation directory
install_dir="$HOME/.local/share/project-babble"

# Function to install requirements
install_requirements() {
    # Create a temporary requirements file without the Windows-only package
    grep -v "onnxruntime-directml" requirements.txt > linux_requirements.txt
    pip install -r linux_requirements.txt --quiet
    rm linux_requirements.txt
}

# Function to update the repository
update_repo() {    
    echo "Checking for updates..."    
    git fetch    
    if [ "$(git rev-parse HEAD)" != "$(git rev-parse @{u})" ]; then        
        echo "Updates found. Pulling changes..."        
        git pull        
        echo "Updating dependencies..."        
        source venv/bin/activate        
        install_requirements       
        deactivate        

        # Add babbleapp.sh to PATH    
        mkdir -p "$HOME/.local/bin"    
        ln -s "$install_dir/babbleapp.sh" "$HOME/.local/bin/babble-app"    
        chmod +x "$HOME/.local/bin/babble-app"

        # Add ~/.local/bin to PATH if not already present    
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then        
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"            
            echo "Please restart your terminal or run 'source ~/.bashrc' to update your PATH."    
        fi

        echo "Project Babble has been updated successfully!"    
    else        
        echo "Project Babble is already up to date."    
    fi
}

cd $install_dir
update_repo
source venv/bin/activate  
cd BabbleApp
echo "Verifying dependencies. This might take a second!"
install_requirements
echo "Starting Babble app..."
python3 babbleapp.py