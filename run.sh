#!/bin/bash
# run.sh - Launch the Digital Photo Frame application on the HDMI display

# Ensure we are in the project directory
cd "$(dirname "$0")"

# Set display to primary X11 / HDMI screen if not already set
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/pi/.Xauthority}"

# Launch the application
python3 main.py
