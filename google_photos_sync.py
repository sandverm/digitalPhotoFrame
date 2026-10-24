import os
import time
import json
import threading

class GooglePhotosSync:
    def __init__(self, config):
        self.config = config.get('google_photos', {})
        self.enabled = self.config.get('enabled', False)
        self.sync_interval_hours = self.config.get('sync_interval_hours', 24)
        self.albums = self.config.get('albums', [])
        self._stop_event = threading.Event()
        self._thread = None

    def start(self, on_new_media_callback=None):
        if not self.enabled:
            print("Google Photos sync is disabled in config.json.")
            return

        if not self.albums:
            print("Google Photos sync enabled, but no albums configured.")
            return

        print(f"Starting Google Photos sync service (Interval: {self.sync_interval_hours} hours)...")
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
                print(f"Error during Google Photos sync: {e}")

            interval_seconds = max(1, self.sync_interval_hours) * 3600
            for _ in range(int(interval_seconds / 10)):
                if self._stop_event.is_set():
                    break
                time.sleep(10)

    def sync_once(self):
        print("Executing Google Photos synchronization...")
        credentials_file = self.config.get('client_secrets_file', 'client_secret.json')
        
        if not os.path.exists(credentials_file):
            print(f"Google Photos credentials file '{credentials_file}' not found.")
            return

        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            import requests
        except ImportError as e:
            print(f"Google API libraries missing: {e}")
            return

        SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
        creds = None
        token_path = 'token.json'

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Failed to refresh Google credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.isatty(0):
                    print("Interactive authentication required for Google Photos, but running non-interactively.")
                    return
                print("Starting Google Photos OAuth authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                try:
                    # Try local server first (works if Pi has desktop browser)
                    creds = flow.run_local_server(port=0, open_browser=True)
                except Exception as local_err:
                    print(f"Local server auth failed ({local_err}). Falling back to console / copy-paste auth...")
                    creds = flow.run_console()

            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        headers = {'Authorization': f'Bearer {creds.token}'}

        for album_conf in self.albums:
            album_name = album_conf.get('album_name')
            dest_dir = album_conf.get('destination_dir')

            if not album_name or not dest_dir:
                continue

            os.makedirs(dest_dir, exist_ok=True)
            print(f"Syncing Google Photos album '{album_name}' -> '{dest_dir}'")

            album_id = self._find_album_id(headers, album_name)
            if not album_id:
                print(f"Google Photos album '{album_name}' not found.")
                continue

            self._download_album_media(headers, album_id, dest_dir)

    def _find_album_id(self, headers, target_name):
        import requests
        pageToken = None
        while True:
            url = 'https://photoslibrary.googleapis.com/v1/albums'
            params = {'pageSize': 50}
            if pageToken:
                params['pageToken'] = pageToken
            res = requests.get(url, headers=headers, params=params)
            if res.status_code != 200:
                print(f"Error listing albums: {res.text}")
                break
            data = res.json()
            for album in data.get('albums', []):
                if album.get('title') == target_name:
                    return album.get('id')
            pageToken = data.get('nextPageToken')
            if not pageToken:
                break
        return None

    def _download_album_media(self, headers, album_id, dest_dir):
        import requests
        pageToken = None
        while True:
            url = 'https://photoslibrary.googleapis.com/v1/mediaItems:search'
            body = {'albumId': album_id, 'pageSize': 100}
            if pageToken:
                body['pageToken'] = pageToken

            res = requests.post(url, headers=headers, json=body)
            if res.status_code != 200:
                print(f"Error searching media items: {res.text}")
                break

            data = res.json()
            items = data.get('mediaItems', [])

            for item in items:
                filename = item.get('filename')
                base_url = item.get('baseUrl')

                if not filename or not base_url:
                    continue

                dest_path = os.path.join(dest_dir, filename)
                if os.path.exists(dest_path):
                    continue

                is_video = 'video' in item.get('mimeType', '')
                download_url = base_url + ('=dv' if is_video else '=d')

                try:
                    print(f"Downloading Google Photo: {filename}")
                    r = requests.get(download_url, stream=True, timeout=30)
                    if r.status_code == 200:
                        with open(dest_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                except Exception as e:
                    print(f"Failed to download {filename}: {e}")

            pageToken = data.get('nextPageToken')
            if not pageToken:
                break
