# RustDesk Mobile - client (Kivy)

This repo contains an Android client (Kivy) that:
- Generates/keeps a session ID
- Registers to Render server via POST /register
- Uploads images to POST /upload
- Shows session id + global password

Endpoints used:
- POST /register  { session_id: "...", meta: {...} }
- POST /upload    { session_id: "...", image: "<base64>" }

Build:
- GitHub Actions will build the APK automatically when you push to main.
- After the workflow completes, download the APK artifact.

Server: set `SERVER_URL` in `main.py` if your server url differs.
