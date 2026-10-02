#!/bin/bash
# setup.sh - Install native Debian/Raspberry Pi OS system dependencies for Digital Photo Frame

echo "Updating package lists..."
sudo apt-get update

echo "Installing native system dependencies (PyQt5, Tkinter, PIL, VLC)..."
sudo apt-get install -y \
    python3-pyqt5 \
    python3-pyqt5.qtmultimedia \
    python3-tk \
    python3-pil \
    python3-vlc \
    vlc

echo "Setup complete! You can now run ./run.sh"
