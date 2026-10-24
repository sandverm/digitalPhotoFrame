import sys
import json
import os
from media_manager import MediaManager
from google_photos_sync import GooglePhotosSync

# ---------------------------------------------------------
# PyQt5 Backend Implementation
# ---------------------------------------------------------
def run_pyqt5(config):
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QStackedWidget, QSizePolicy
        from PyQt5.QtCore import Qt, QTimer, QUrl
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
        from PyQt5.QtMultimediaWidgets import QVideoWidget
    except ImportError as e:
        print(f"PyQt5 or QtMultimedia import failed: {e}")
        return False

    class PyQt5PhotoFrame(QMainWindow):
        def __init__(self, cfg):
            super().__init__()
            self.config = cfg
            self.setWindowTitle("Digital Photo Frame (PyQt5)")
            self.setStyleSheet("background-color: black;")
            self.showFullScreen()
            
            self.media_manager = MediaManager(
                cfg.get('media_root', '/home/pi/Pictures'),
                shuffle=cfg.get('shuffle', True)
            )
            
            # Start Google Photos background sync service
            self.gp_sync = GooglePhotosSync(cfg)
            self.gp_sync.start(on_new_media_callback=lambda: self.media_manager.refresh())
            
            self.central_widget = QStackedWidget()
            self.setCentralWidget(self.central_widget)
            
            # Image Display
            self.image_label = QLabel()
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.central_widget.addWidget(self.image_label)
            
            # Video Display
            self.video_widget = QVideoWidget()
            self.player = QMediaPlayer()
            self.player.setVideoOutput(self.video_widget)
            self.central_widget.addWidget(self.video_widget)
            
            if hasattr(self.player, 'mediaStatusChanged'):
                self.player.mediaStatusChanged.connect(self.on_media_status_changed)
            elif hasattr(self.player, 'stateChanged'):
                self.player.stateChanged.connect(self.on_state_changed)
            
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.show_next)
            
            self.show_next()

        def closeEvent(self, event):
            if hasattr(self, 'gp_sync'):
                self.gp_sync.stop()
            event.accept()

        def show_next(self):
            self.timer.stop()
            self.player.stop()
            
            media = self.media_manager.get_next()
            if not media:
                self.image_label.setText("No media found in configured directory.")
                self.central_widget.setCurrentWidget(self.image_label)
                self.timer.start(30000)
                return

            print(f"Playing [PyQt5]: {media['path']}")
            
            if media['is_video']:
                self.central_widget.setCurrentWidget(self.video_widget)
                if hasattr(self.player, 'setSource'):
                    self.player.setSource(QUrl.fromLocalFile(media['path']))
                else:
                    self.player.setMedia(QMediaContent(QUrl.fromLocalFile(media['path'])))
                self.player.play()
            else:
                self.central_widget.setCurrentWidget(self.image_label)
                pixmap = QPixmap(media['path'])
                if pixmap.isNull():
                    print(f"Error loading image: {media['path']}")
                    self.show_next()
                    return
                    
                scaled_pixmap = pixmap.scaled(
                    self.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.timer.start(self.config.get('photo_duration', 10) * 1000)

        def on_media_status_changed(self, status):
            if status == QMediaPlayer.EndOfMedia:
                self.show_next()

        def on_state_changed(self, state):
            if state == QMediaPlayer.StoppedState and self.central_widget.currentWidget() == self.video_widget:
                pass

        def keyPressEvent(self, event):
            if event.key() == Qt.Key_Escape:
                self.close()
            elif event.key() == Qt.Key_Right or event.key() == Qt.Key_Space:
                self.show_next()

    app = QApplication(sys.argv)
    frame = PyQt5PhotoFrame(config)
    sys.exit(app.exec_())

# ---------------------------------------------------------
# Tkinter + VLC Backend Implementation
# ---------------------------------------------------------
def run_tkinter(config):
    try:
        import tkinter as tk
        from PIL import Image, ImageTk
        import vlc
    except ImportError as e:
        print(f"Tkinter / Pillow / VLC import failed: {e}")
        return False

    class TkinterPhotoFrame:
        def __init__(self, root, cfg):
            self.root = root
            self.config = cfg
            self.root.title("Digital Photo Frame (Tkinter)")
            self.root.attributes('-fullscreen', True)
            self.root.configure(background='black')
            
            self.media_manager = MediaManager(
                cfg.get('media_root', '/home/pi/Pictures'),
                shuffle=cfg.get('shuffle', True)
            )
            
            # Start Google Photos background sync service
            self.gp_sync = GooglePhotosSync(cfg)
            self.gp_sync.start(on_new_media_callback=lambda: self.media_manager.refresh())
            
            self.canvas = tk.Canvas(root, bg='black', highlightthickness=0)
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
            self.video_frame = tk.Frame(root, bg='black')
            
            self.vlc_instance = vlc.Instance('--no-xlib')
            self.player = self.vlc_instance.media_player_new()
            
            self.current_image_tk = None
            self.timer_id = None
            self.video_check_id = None
            
            self.root.bind("<Escape>", lambda e: self.quit())
            self.root.bind("<Right>", lambda e: self.show_next())
            self.root.bind("<space>", lambda e: self.show_next())
            
            self.show_next()

        def quit(self):
            if hasattr(self, 'gp_sync'):
                self.gp_sync.stop()
            self.player.stop()
            self.root.destroy()

        def show_next(self):
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
            if self.video_check_id:
                self.root.after_cancel(self.video_check_id)
                self.video_check_id = None
                
            self.player.stop()
            self.video_frame.pack_forget()
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
            media = self.media_manager.get_next()
            if not media:
                self.canvas.delete("all")
                self.canvas.create_text(
                    self.root.winfo_width() // 2, self.root.winfo_height() // 2,
                    text="No media found in configured directory.",
                    fill="white", font=("Arial", 20)
                )
                self.timer_id = self.root.after(30000, self.show_next)
                return

            print(f"Playing [Tkinter/VLC]: {media['path']}")
            
            if media['is_video']:
                self.canvas.pack_forget()
                self.video_frame.pack(fill=tk.BOTH, expand=True)
                self.video_frame.update()
                
                if os.name == 'nt':
                    self.player.set_hwnd(self.video_frame.winfo_id())
                else:
                    self.player.set_xwindow(self.video_frame.winfo_id())
                    
                m = self.vlc_instance.media_new(media['path'])
                self.player.set_media(m)
                self.player.play()
                
                self.check_video_end()
            else:
                try:
                    img = Image.open(media['path'])
                    win_width = self.root.winfo_width() or 800
                    win_height = self.root.winfo_height() or 600
                    
                    img.thumbnail((win_width, win_height), Image.Resampling.LANCZOS)
                    self.current_image_tk = ImageTk.PhotoImage(img)
                    
                    self.canvas.delete("all")
                    self.canvas.create_image(
                        win_width // 2, win_height // 2,
                        image=self.current_image_tk, anchor=tk.CENTER
                    )
                except Exception as e:
                    print(f"Error loading image {media['path']}: {e}")
                    self.show_next()
                    return
                    
                duration = self.config.get('photo_duration', 10) * 1000
                self.timer_id = self.root.after(duration, self.show_next)

        def check_video_end(self):
            state = self.player.get_state()
            if state in (vlc.State.Ended, vlc.State.Error) or not self.player.is_playing():
                self.show_next()
            else:
                self.video_check_id = self.root.after(500, self.check_video_end)

    root = tk.Tk()
    app = TkinterPhotoFrame(root, config)
    root.mainloop()
    return True

# ---------------------------------------------------------
# Main Entry Point & Backend Selector
# ---------------------------------------------------------
if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        config = {}

    backend = config.get('backend', 'auto').lower()
    print(f"Selected backend mode: {backend}")

    success = False

    if backend == 'pyqt5':
        success = run_pyqt5(config)
    elif backend == 'tkinter':
        success = run_tkinter(config)
    else:  # auto
        print("Attempting to launch PyQt5 backend...")
        success = run_pyqt5(config)
        if not success:
            print("PyQt5 unavailable or failed. Falling back to Tkinter + VLC backend...")
            success = run_tkinter(config)

    if not success:
        print("Error: Could not launch any available backend (PyQt5 or Tkinter).")
        print("Please run './setup.sh' to install required system dependencies.")
        sys.exit(1)
