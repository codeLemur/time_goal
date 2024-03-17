#!/bin/bash

# Absolute path to the directory containing your virtual environment
VENV_DIR="/home/pi/repo/time_goal/venv/"

# Absolute path to your Python script
PYTHON_SCRIPT="/home/pi/repo/time_goal/goal_gui.py"

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Run the Python script
python3 "$PYTHON_SCRIPT"

# Deactivate the virtual environment
deactivate

