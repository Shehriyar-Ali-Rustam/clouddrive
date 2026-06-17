"""Capture the 'Shared with me' screenshot reliably (API setup + Playwright login)."""
import os
import uuid
import urllib.request
import json

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
IMGDIR = os.path.join(os.path.dirname(__file__), "img")
S = uuid.uuid4().hex[:6]
A, B, PW = f"sara_{S}@uni.edu", f"omar_{S}@uni.edu", "demo1234"


def post(path, data, token=None, form=False):
    if form:
        body = "&".join(f"{k}={v}" for k, v in data.items()).encode()
        ct = "application/x-www-form-urlencoded"
    else:
        body = json.dumps(data).encode()
        ct = "application/json"
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", ct)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    return json.loads(urllib.request.urlopen(req).read())


def put(url, content, ct):
    req = urllib.request.Request(url, data=content, method="PUT")
    req.add_header("Content-Type", ct)
    urllib.request.urlopen(req)


# --- set up data via API ---
tokA = post("/api/auth/signup", {"email": A, "password": PW})["access_token"]
post("/api/auth/signup", {"email": B, "password": PW})
for name in ["Project Report.pdf", "Lecture Notes.docx"]:
    t = post("/api/files/init", {"name": name, "size": 12, "content_type": "application/pdf"}, tokA)
    put(t["upload_url"], b"shared bytes", "application/pdf")
    post(f"/api/files/{t['file_id']}/complete", {}, tokA)
    post("/api/shares", {"file_id": t["file_id"], "email": B}, tokA)
print("data ready; B has 2 shared files")

# --- screenshot B's shared view ---
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox"])
    page = browser.new_context(viewport={"width": 1280, "height": 620}).new_page()
    page.goto(BASE, wait_until="load")
    page.fill("#email", B)
    page.fill("#password", PW)
    page.click("#auth-btn")
    page.wait_for_selector("#app-screen:not(.hidden)", timeout=15000)
    page.click("#view-shared")
    page.wait_for_function("document.querySelectorAll('.file-card').length >= 2", timeout=15000)
    page.wait_for_timeout(600)
    page.screenshot(path=f"{IMGDIR}/05_shared_with_me.png")
    browser.close()
print("captured shared-with-me")
