import os
import re
import urllib.request
import hashlib
import time
import threading

class GoogleSharedAlbumSync:
    def __init__(self, config):
        self.config = config.get('google_shared_album', {})
        self.enabled = self.config.get('enabled', False)
        self.sync_interval_hours = self.config.get('sync_interval_hours', 24)
        self.albums = self.config.get('albums', [])
        self._stop_event = threading.Event()
        self._thread = None

    def start(self, on_new_media_callback=None):
        if not self.enabled:
            print("Google Shared Album sync is disabled in config.json.")
            return

        if not self.albums:
            print("Google Shared Album sync enabled, but no shared albums configured.")
            return

        print(f"Starting Google Shared Album sync service (Interval: {self.sync_interval_hours} hours)...")
        self._thread = threading.Thread(target=self._sync_loop, args=(on_new_media_callback,), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _sync_loop(self, callback):
        time.sleep(2)
        while not self._stop_event.is_set():
            try:
                self.sync_once()
                if callback:
                    callback()
            except Exception as e:
                print(f"Error during Google Shared Album sync: {e}")

            interval_seconds = max(1, self.sync_interval_hours) * 3600
            for _ in range(int(interval_seconds / 10)):
                if self._stop_event.is_set():
                    break
                time.sleep(10)

    def sync_once(self):
        print("Executing Google Shared Album synchronization...")
        for album in self.albums:
            share_url = album.get('share_url')
            dest_dir = album.get('destination_dir')

            if not share_url or not dest_dir:
                continue

            os.makedirs(dest_dir, exist_ok=True)
            print(f"Scraping shared album -> '{dest_dir}'")
            self._scrape_and_download(share_url, dest_dir)

    def _scrape_and_download(self, share_url, dest_dir):
        try:
            req = urllib.request.Request(
                share_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode('utf-8')

            pattern = r'\"(https://lh3\.googleusercontent\.com/pw/[a-zA-Z0-9_\-\=]{30,})\"'
            matches = list(set(re.findall(pattern, html)))

            print(f"Found {len(matches)} valid album photo URLs.")

            for base_url in matches:
                # Generate a stable unique ID from the photo base URL
                photo_id = hashlib.md5(base_url.encode('utf-8')).hexdigest()[:16]
                filename = f"google_shared_{photo_id}.jpg"
                dest_path = os.path.join(dest_dir, filename)

                # Skip if already downloaded and valid
                if os.path.exists(dest_path) and os.path.getsize(dest_path) > 15000:
                    continue

                success = False
                variants = [base_url + '=w1920-h1080', base_url + '=d']
                
                for download_url in variants:
                    if success:
                        break
                    try:
                        req_img = urllib.request.Request(
                            download_url,
                            headers={'User-Agent': 'Mozilla/5.0'}
                        )
                        with urllib.request.urlopen(req_img, timeout=20) as img_resp:
                            data = img_resp.read()
                            if len(data) > 15000:
                                with open(dest_path, 'wb') as f:
                                    f.write(data)
                                print(f"Successfully downloaded new shared photo ({photo_id})")
                                success = True
                    except Exception:
                        continue

        except Exception as e:
            print(f"Error scraping shared album: {e}")
