import os
import random

class MediaManager:
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.mov', '.avi', '.webm'}

    def __init__(self, root_dir, shuffle=True, use_local_media=True, google_albums=None, shared_albums=None):
        self.root_dir = root_dir
        self.shuffle = shuffle
        self.use_local_media = use_local_media
        self.google_albums = google_albums or []
        self.shared_albums = shared_albums or []
        self.media_list = []
        self.current_index = -1
        self.refresh()

    def refresh(self):
        """Recursively scans root directory, Google Photos API directories, and Shared Album directories."""
        new_media_list = []
        scanned_dirs = set()

        # 1. Scan local media_root if enabled
        sources = []
        if self.use_local_media and self.root_dir:
            sources.append(self.root_dir)

        # 2. Scan Google Photos API destination directories
        for album in self.google_albums:
            if album.get('destination_dir'):
                sources.append(album.get('destination_dir'))

        # 3. Scan Google Shared Album destination directories (3rd source)
        for album in self.shared_albums:
            if album.get('destination_dir'):
                sources.append(album.get('destination_dir'))

        for src in sources:
            abs_src = os.path.abspath(src)
            if abs_src not in scanned_dirs and os.path.exists(src):
                scanned_dirs.add(abs_src)
                for root, _, files in os.walk(src):
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in self.IMAGE_EXTENSIONS or ext in self.VIDEO_EXTENSIONS:
                            full_path = os.path.join(root, file)
                            is_video = ext in self.VIDEO_EXTENSIONS
                            new_media_list.append({'path': full_path, 'is_video': is_video})
        
        # Deduplicate by path
        seen_paths = set()
        unique_media_list = []
        for item in new_media_list:
            if item['path'] not in seen_paths:
                seen_paths.add(item['path'])
                unique_media_list.append(item)

        self.media_list = unique_media_list
        if self.shuffle:
            random.shuffle(self.media_list)
        
        self.current_index = -1
        print(f"MediaManager: Found {len(self.media_list)} total media items from all enabled sources.")

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
