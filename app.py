#!/usr/bin/env python3
import os
import json
import platform
from datetime import datetime, date
from pathlib import Path
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from pdf2image import convert_from_path
from PIL import Image

# ----------------------
# Config
# ----------------------
BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "app.db"
UPLOAD_DIR = BASE_DIR / "uploads"

(UPLOAD_DIR / "todays_paper").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "namma_tumkur").mkdir(parents=True, exist_ok=True)

# POPPLER PATH (Windows)
POPPLER_PATH = None
if platform.system() == "Windows":
    POPPLER_PATH = r"C:\Users\WIN11\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

def env(key, default=None):
    val = os.getenv(key)
    return val if val not in (None, "", "None") else default

app = Flask(__name__)

app.config["SECRET_KEY"] = env("SECRET_KEY", "change-me")
app.config["ADMIN_USERNAME"] = env("ADMIN_USERNAME", "admin")
app.config["ADMIN_PASSWORD"] = env("ADMIN_PASSWORD", "admin123")
app.config["ADMIN_SLUG"] = env("ADMIN_SLUG", "login-admin")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

db = SQLAlchemy(app)

# ----------------------
# Models
# ----------------------
class Issue(db.Model):
    __tablename__ = "issues"
    id = db.Column(db.Integer, primary_key=True)
    paper = db.Column(db.String(50), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("paper", "issue_date", name="uix_paper_date"),
    )

    pages = db.relationship(
        "Page",
        backref="issue",
        cascade="all, delete-orphan",
        order_by="Page.page_no"
    )

    def folder(self):
        return UPLOAD_DIR / self.paper / self.issue_date.strftime("%Y-%m-%d")

class Page(db.Model):
    __tablename__ = "pages"
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False)
    page_no = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)

class Block(db.Model):
    __tablename__ = "blocks"
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey("pages.id"), nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)

Page.blocks = db.relationship(
    "Block", backref="page", cascade="all, delete-orphan"
)

with app.app_context():
    db.create_all()

# ----------------------
# Helpers
# ----------------------
def admin_logged_in():
    return session.get("is_admin") is True

def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not admin_logged_in():
            flash("You must log in as admin.", "error")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapper

def ensure_issue_folder(issue):
    folder = issue.folder()
    folder.mkdir(parents=True, exist_ok=True)
    return folder

# ----------------------
# Public Routes
# ----------------------
@app.route("/")
def index():
    today = date.today()
    return render_template(
        "index.html",
        today=today,
        todays_issue=Issue.query.filter_by(paper="todays_paper", issue_date=today).first(),
        tumkur_issue=Issue.query.filter_by(paper="namma_tumkur", issue_date=today).first()
    )

@app.route("/issue/<paper>/<datestr>")
def view_issue(paper, datestr):
    try:
        issue_date = datetime.strptime(datestr, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date.", "error")
        return redirect(url_for("index"))

    issue = Issue.query.filter_by(paper=paper, issue_date=issue_date).first()
    if not issue:
        flash("Issue not found.", "error")
        return redirect(url_for("index"))

    return render_template(
        "issue.html",
        issue_date=issue_date,
        paper_name=paper.replace("_", " ").title(),
        todays_issue=issue if paper == "todays_paper" else None,
        tumkur_issue=issue if paper == "namma_tumkur" else None
    )

@app.route("/media/<paper>/<datestr>/<path:filename>")
def media(paper, datestr, filename):
    return send_from_directory(
        UPLOAD_DIR / paper / datestr,
        secure_filename(filename),
        as_attachment=False
    )

# ----------------------
# Admin Routes
# ----------------------
ADMIN_SLUG = app.config["ADMIN_SLUG"].strip("/")

@app.route(f"/{ADMIN_SLUG}/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (
            request.form.get("username") == app.config["ADMIN_USERNAME"]
            and request.form.get("password") == app.config["ADMIN_PASSWORD"]
        ):
            session["is_admin"] = True
            flash("Welcome back!", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials.", "error")
    return render_template("admin_login.html")

@app.route(f"/{ADMIN_SLUG}/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out.", "info")
    return redirect(url_for("index"))

@app.route(f"/{ADMIN_SLUG}/")
@admin_required
def admin_dashboard():
    return render_template(
        "admin_dashboard.html",
        issues=Issue.query.order_by(Issue.issue_date.desc()).all()
    )

# ----------------------
# PDF Upload (PNG – CLEAR TEXT)
# ----------------------
@app.route(f"/{ADMIN_SLUG}/upload", methods=["POST"])
@admin_required
def admin_upload():
    paper = request.form.get("paper")
    issue_date = datetime.strptime(request.form.get("issue_date"), "%Y-%m-%d").date()
    pdf = request.files.get("pdf")

    if not pdf or not pdf.filename.lower().endswith(".pdf"):
        flash("Please upload a valid PDF.", "error")
        return redirect(url_for("admin_dashboard"))

    issue = Issue.query.filter_by(paper=paper, issue_date=issue_date).first()
    if not issue:
        issue = Issue(paper=paper, issue_date=issue_date)
        db.session.add(issue)
        db.session.commit()

    folder = ensure_issue_folder(issue)
    pdf_path = folder / secure_filename(pdf.filename)
    pdf.save(pdf_path)

    Page.query.filter_by(issue_id=issue.id).delete()
    db.session.commit()

    try:
        images = convert_from_path(
            pdf_path,
            dpi=450,
            poppler_path=POPPLER_PATH
        )
    except Exception as e:
        flash(f"PDF conversion failed: {e}", "error")
        return redirect(url_for("admin_dashboard"))

    for i, img in enumerate(images, start=1):
        fname = f"page_{i}.png"
        img.save(folder / fname, format="PNG")

        db.session.add(Page(
            issue_id=issue.id,
            page_no=i,
            filename=fname
        ))

    db.session.commit()
    flash(f"Issue uploaded successfully ({len(images)} pages).", "success")
    return redirect(url_for("admin_dashboard"))

# ----------------------
# Delete Issue
# ----------------------
@app.route(f"/{ADMIN_SLUG}/delete/<int:issue_id>", methods=["POST"])
@admin_required
def admin_delete_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    folder = issue.folder()

    if folder.exists():
        for f in folder.glob("*"):
            f.unlink()
        folder.rmdir()

    db.session.delete(issue)
    db.session.commit()
    flash("Issue deleted.", "info")
    return redirect(url_for("admin_dashboard"))

# ----------------------
# Blocks
# ----------------------
@app.route(f"/{ADMIN_SLUG}/block_selector/<int:issue_id>")
@admin_required
def admin_block_selector(issue_id):
    return render_template("block_selector.html", issue=Issue.query.get_or_404(issue_id))

@app.route(f"/{ADMIN_SLUG}/save_blocks/<int:issue_id>", methods=["POST"])
@admin_required
def save_blocks(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    blocks = json.loads(request.form.get("blocks_data", "[]"))

    for page in issue.pages:
        Block.query.filter_by(page_id=page.id).delete()

    for b in blocks:
        db.session.add(Block(**b))

    db.session.commit()
    flash("Blocks saved successfully.", "success")
    return redirect(url_for("admin_block_selector", issue_id=issue.id))

@app.route("/block/<int:block_id>")
def view_block(block_id):
    block = Block.query.get_or_404(block_id)
    return render_template(
        "block_view.html",
        block=block,
        page=block.page,
        issue=block.page.issue
    )

# ----------------------
# Run
# ----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
