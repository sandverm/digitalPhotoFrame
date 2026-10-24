Digital Photo Frame for Raspberry Pi

Requirements & Features:
1: Coding language: Python 3 and Bash.
2: Displays photos for configured duration or videos for full duration, then switches to the next media item.
3: Recursively scans configured media directory, picking random photos and videos from any sub-tree.
4: Supports multiple native Raspberry Pi OS backends (PyQt5 and Tkinter + VLC).
5: Google Photos synchronization support with album mapping, local directory destination, and configurable sync interval.

Configuration (`config.json`):
{
    "media_root": "/home/pi/Pictures",
    "photo_duration": 10,
    "shuffle": true,
    "backend": "auto",
    "google_photos": {
        "enabled": false,
        "sync_interval_hours": 24,
        "client_secrets_file": "client_secret.json",
        "albums": [
            {
                "album_name": "Family Album",
                "destination_dir": "/home/pi/Pictures/Family"
            }
        ]
    }
}

Setup:
1. Run setup script to install system dependencies:
   ./setup.sh

2. (Optional) To enable Google Photos sync:
   - Place your Google OAuth `client_secret.json` in the project root.
   - Run the standalone token generator to authorize via copy-paste link in any browser:
     python3 generate_token.py
   - Set `"enabled": true` and configure your album names and local destination directories in `config.json`.

3. Run the application:
   ./run.sh
