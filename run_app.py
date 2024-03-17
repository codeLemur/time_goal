#!/usr/bin/env python3

import os
import subprocess
from tkinter import Tk, messagebox


def activate_venv_and_run_script():
    venv_path = "/home/pi/repo/time_goal/venv/bin/activate"
    python_script_path = "/home/pi/repo/time_goal/goal_gui.py"

    # Check if both paths exist
    if not os.path.exists(venv_path) or not os.path.exists(python_script_path):
        messagebox.showerror("Error", "Paths not found. Please check the paths in the script.")
        return

    # Activate the virtual environment
    activate_command = f"source {venv_path}"
    subprocess.run(activate_command, shell=True)

    # Run the Python script
    run_command = f"python {python_script_path}"
    subprocess.run(run_command, shell=True)

if __name__ == "__main__":
    activate_venv_and_run_script()