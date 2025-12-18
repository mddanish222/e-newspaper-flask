# E‑Newspaper (Flask)

A light-theme e‑newspaper site with a **secret admin panel**, date-based issues, and image uploads.

## Features
- Public site:
  - Pick a date to read the issue
  - Responsive light UI
  - Lazy-loaded page images
- Secret Admin:
  - Hidden under a secret slug path (default: `/_paper-admin-8f2b9c`)
  - Login with username/password
  - Upload pages (PNG/JPG/WEBP) for a given date
  - Delete entire issues

## Quick Start (Local)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export SECRET_KEY="replace-me"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="strongpassword"
export ADMIN_SLUG="_ultra-secret-12345"
python app.py
# visit http://localhost:5000
# admin login: http://localhost:5000/_ultra-secret-12345/login
```

## Deploy to Render
1. Push this folder to a new Git repo.
2. Create a new **Web Service** on Render:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
3. Add **Environment Variables**:
   - `SECRET_KEY` = a long random string
   - `ADMIN_USERNAME` / `ADMIN_PASSWORD`
   - `ADMIN_SLUG` = an unguessable path, e.g. `_my-admin-9c2e`
4. Create a **Persistent Disk** (1–5 GB) and mount it at `/opt/render/project/src/uploads`
5. Done. Your public site stays the same; admin is only visible if you know the slug path.

## How to Use
- Admin uploads images for a given date (pages in order). Files are stored under `uploads/newspapers/YYYY-MM-DD/`.
- Public readers open the homepage, choose a date, and view pages.

## Notes
- This app uses SQLite. For heavy use, consider Postgres and storing images on S3.
- Keep your `ADMIN_SLUG` secret and change default credentials.
