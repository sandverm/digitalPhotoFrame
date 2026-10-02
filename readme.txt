Digital Photo Frame for Raspberry Pi

Requirements & Features:
1: Coding language: Python 3 and Bash.
2: Displays photos for configured duration or videos for full duration, then switches to the next media item.
3: Recursively scans configured media directory, picking random photos and videos from any sub-tree.
4: Supports multiple native Raspberry Pi OS backends (PyQt5 and Tkinter + VLC) without heavy third-party wheels.

Backends available:
- "pyqt5": Uses native PyQt5 and QtMultimedia.
- "tkinter": Uses Python's built-in Tkinter + Pillow + VLC bindings.
- "auto": Automatically detects and uses the best available backend.

Setup:
1. Run setup script to install system dependencies:
   ./setup.sh

2. Configure media directory in config.json:
   {
       "media_root": "/home/pi/Pictures",
       "photo_duration": 10,
       "shuffle": true,
       "backend": "auto"
   }

3. Run the application:
   ./run.sh
