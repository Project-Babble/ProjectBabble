#!/bin/bash

# Set virtual environment directory name
VENV_DIR="venv"

# Check if the virtual environment directory exists, create it if not
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Install or update packages from the requirements.txt file
echo "Installing or updating packages from requirements.txt..."
pip install --upgrade -r requirements.txt

# Run BabbleCPU.py
echo "Starting BabbleCPU..."
python BabbleCPU.py

# Deactivate the virtual environment
deactivate

