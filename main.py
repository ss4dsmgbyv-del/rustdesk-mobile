# main.py
import os
import json
import uuid
import time
import base64
import threading
import requests

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.utils import platform

# Optional: filechooser from plyer for Android/iOS file picking
try:
    from plyer import filechooser, camera
except Exception:
    filechooser = None
    camera = None

# === CONFIG: update SERVER_URL if different ===
SERVER_URL = "https://rustdesk-render-server.onrender.com"
UNIVERSAL_PASSWORD = "@MadMax31"

# Local persistent storage for session id
DATA_FILE = "session.json"

def load_session():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_session(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f)

def ensure_session_id():
    data = load_session()
    sid = data.get("session_id")
    if not sid:
        sid = str(uuid.uuid4())[:12]
        data["session_id"] = sid
        save_session(data)
    return sid

class Root(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=12, spacing=12, **kwargs)
        self.session_id = ensure_session_id()
        self.registered = False
        self.last_status = ""
        self.upload_preview_path = None

        self.title = Label(text="[b]RustDesk (mobile) - Client[/b]", markup=True, size_hint_y=None, height=30)
        self.add_widget(self.title)

        self.id_label = Label(text=f"Session ID: [b]{self.session_id}[/b]", markup=True, size_hint_y=None, height=30)
        self.add_widget(self.id_label)

        self.pass_label = Label(text=f"Password: [b]{UNIVERSAL_PASSWORD}[/b]", markup=True, size_hint_y=None, height=30)
        self.add_widget(self.pass_label)

        self.status = Label(text="Status: ready", size_hint_y=None, height=30)
        self.add_widget(self.status)

        # Preview image
        self.preview = Image(size_hint=(1, 1), allow_stretch=True)
        self.add_widget(self.preview)

        btn_layout = BoxLayout(size_hint_y=None, height=48, spacing=8)
        self.btn_register = Button(text="Register Session (manual)")
        self.btn_register.bind(on_release=lambda _: threading.Thread(target=self.register_session, daemon=True).start())
        btn_layout.add_widget(self.btn_register)

        self.btn_pick = Button(text="Pick Image & Upload")
        self.btn_pick.bind(on_release=lambda _: threading.Thread(target=self.pick_and_upload, daemon=True).start())
        btn_layout.add_widget(self.btn_pick)

        self.btn_camera = Button(text="Take Photo (if available)")
        self.btn_camera.bind(on_release=lambda _: threading.Thread(target=self.capture_and_upload, daemon=True).start())
        btn_layout.add_widget(self.btn_camera)

        self.add_widget(btn_layout)

        # Auto register in background
        Clock.schedule_once(lambda dt: threading.Thread(target=self.background_register_loop, daemon=True).start())

    def set_status(self, text):
        self.last_status = text
        Clock.schedule_once(lambda dt: self.status.setter('text')(self.status, f"Status: {text}"))

    def background_register_loop(self):
        # Try to register every 10 seconds until success
        while not self.registered:
            try:
                self.set_status("Registering session...")
                r = requests.post(f"{SERVER_URL}/register", json={"session_id": self.session_id, "meta": {"platform": platform or "unknown"}} , timeout=12)
                if r.status_code == 200:
                    self.registered = True
                    self.set_status("Registered with server.")
                else:
                    self.set_status(f"Register failed: {r.status_code}")
            except Exception as e:
                self.set_status("Network error during register; retrying...")
            time.sleep(10)

    def register_session(self):
        try:
            self.set_status("Registering (manual)...")
            r = requests.post(f"{SERVER_URL}/register", json={"session_id": self.session_id, "meta": {"manual": True}}, timeout=12)
            if r.status_code == 200:
                self.registered = True
                self.set_status("Registered (manual).")
            else:
                self.set_status(f"Register error: {r.status_code}")
        except Exception as e:
            self.set_status(f"Register exception: {e}")

    def pick_and_upload(self):
        # Use plyer.filechooser if available
        if filechooser:
            try:
                paths = filechooser.open_file(title="Pick image", multiple=False)
                # filechooser returns asynchronously on some platforms; check
                if isinstance(paths, (list, tuple)) and paths:
                    path = paths[0]
                    if os.path.exists(path):
                        self.upload_image(path)
                        return
                # If returns nothing right away, user may have used callback path
                self.set_status("No file chosen.")
            except Exception as e:
                self.set_status(f"filechooser error: {e}")
        else:
            self.set_status("File picker not available on this platform.")

    def capture_and_upload(self):
        # Try to use plyer.camera if available
        if camera:
            try:
                # save to app folder
                outp = f"capture_{int(time.time())}.jpg"
                camera.take_picture(filename=outp, on_complete=lambda p: self._camera_done(p))
                self.set_status("Opening camera...")
            except Exception as e:
                self.set_status(f"Camera error: {e}")
        else:
            self.set_status("Camera not available via plyer.")

    def _camera_done(self, path):
        # plyer may call the callback with path
        if path and os.path.exists(path):
            self.upload_image(path)
        else:
            self.set_status("Camera capture failed or cancelled.")

    def upload_image(self, path):
        # preview
        try:
            self.preview.source = path
            self.preview.reload()
        except Exception:
            pass

        try:
            self.set_status("Preparing image...")
            with open(path, "rb") as f:
                b = f.read()
            b64 = base64.b64encode(b).decode()
            payload = {"session_id": self.session_id, "image": b64}
            self.set_status("Uploading...")
            r = requests.post(f"{SERVER_URL}/upload", json=payload, timeout=20)
            if r.status_code == 200:
                self.set_status("Upload OK.")
            else:
                self.set_status(f"Upload failed: {r.status_code}")
        except Exception as e:
            self.set_status(f"Upload exception: {e}")

class RustDeskApp(App):
    def build(self):
        return Root()

if __name__ == "__main__":
    RustDeskApp().run()
