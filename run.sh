#!/bin/bash
# run.sh - Launch the Digital Photo Frame application on the HDMI display and keep screen awake

# Ensure we are in the project directory
cd "$(dirname "$0")"

# Set display to primary X11 / HDMI screen if not already set
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/pi/.Xauthority}"

# Disable screen blanking, screensaver, and power saving (DPMS)
xset s off
xset -dpms
xset s noblank

# Launch the application
python3 main.py
