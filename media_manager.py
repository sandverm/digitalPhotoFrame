import os
import random

class MediaManager:
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.mov', '.avi', '.webm'}

    def __init__(self, root_dir, shuffle=True):
        self.root_dir = root_dir
        self.shuffle = shuffle
        self.media_list = []
        self.current_index = -1
        self.refresh()

    def refresh(self):
        """Recursively scans the root directory for media files."""
        new_media_list = []
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.IMAGE_EXTENSIONS or ext in self.VIDEO_EXTENSIONS:
                    full_path = os.path.join(root, file)
                    is_video = ext in self.VIDEO_EXTENSIONS
                    new_media_list.append({'path': full_path, 'is_video': is_video})
        
        self.media_list = new_media_list
        if self.shuffle:
            random.shuffle(self.media_list)
        
        self.current_index = -1
        print(f"MediaManager: Found {len(self.media_list)} media items.")

    def get_next(self):
        """Returns the next media item in the list."""
        if not self.media_list:
            return None
        
        self.current_index += 1
        if self.current_index >= len(self.media_list):
            if self.shuffle:
                random.shuffle(self.media_list)
            self.current_index = 0
            
        return self.media_list[self.current_index]
