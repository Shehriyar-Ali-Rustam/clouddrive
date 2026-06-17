"""
Captures real screenshots of the running CloudDrive app using Playwright +
system Chrome. Saves PNGs into docs/img/ for use in the technical report.

Requires the app running on http://localhost:8000.
Run:  python docs/capture_screenshots.py
"""
import os
import uuid

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
IMGDIR = os.path.join(os.path.dirname(__file__), "img")
SAMPLES = "/tmp/cd_samples"
os.makedirs(IMGDIR, exist_ok=True)

SUFFIX = uuid.uuid4().hex[:6]
EMAIL_A = f"aisha_{SUFFIX}@uni.edu"
EMAIL_B = f"bilal_{SUFFIX}@uni.edu"
PW = "demo1234"

FILES = [
    f"{SAMPLES}/Project Report.pdf",
    f"{SAMPLES}/Lecture Notes.docx",
    f"{SAMPLES}/Budget 2026.xlsx",
    f"{SAMPLES}/vacation.png",
]


def signup(page, email):
    page.goto(BASE, wait_until="load")
    page.click("#tab-signup")
    page.fill("#email", email)
    page.fill("#password", PW)
    page.click("#auth-btn")
    page.wait_for_selector("#app-screen:not(.hidden)", timeout=15000)


def login(page, email):
    page.goto(BASE, wait_until="load")
    page.fill("#email", email)
    page.fill("#password", PW)
    page.click("#auth-btn")
    page.wait_for_selector("#app-screen:not(.hidden)", timeout=15000)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True,
                                    args=["--no-sandbox"])

        # ---------- 1. Login / landing screen ----------
        ctx = browser.new_context(viewport={"width": 1280, "height": 820})
        page = ctx.new_page()
        page.goto(BASE, wait_until="load")
        page.wait_for_selector("#auth-screen")
        page.screenshot(path=f"{IMGDIR}/01_login.png")
        print("captured login")

        # ---------- pre-create recipient B ----------
        signup(page, EMAIL_B)
        ctx.close()

        # ---------- 2. Dashboard (account A with files) ----------
        ctx = browser.new_context(viewport={"width": 1280, "height": 820})
        page = ctx.new_page()
        signup(page, EMAIL_A)
        page.set_input_files("#file-input", FILES)
        # wait for all uploads to land
        page.wait_for_function("document.querySelectorAll('.file-card').length >= 4",
                               timeout=30000)
        page.wait_for_timeout(800)
        page.screenshot(path=f"{IMGDIR}/02_dashboard.png")
        print("captured dashboard")

        # ---------- 3. Share modal ----------
        page.click('.file-card button[data-action="share"]')
        page.wait_for_selector("#share-modal:not(.hidden)")
        page.wait_for_timeout(300)
        page.screenshot(path=f"{IMGDIR}/03_share_modal.png")
        print("captured share modal")

        # ---------- 4. create a public link (shows the link box) ----------
        page.fill("#share-expiry", "24")
        page.click("button:has-text('Create link')")
        page.wait_for_selector("#public-link-box:not(.hidden)", timeout=10000)
        page.wait_for_timeout(400)
        page.screenshot(path=f"{IMGDIR}/04_public_link.png")
        print("captured public link")

        # ---------- share file with B (for the shared-with-me shot) ----------
        page.fill("#share-email", EMAIL_B)
        page.click("button:has-text('Share')")
        page.wait_for_timeout(800)
        ctx.close()

        # ---------- 5. Shared with me (account B) ----------
        ctx = browser.new_context(viewport={"width": 1280, "height": 820})
        page = ctx.new_page()
        login(page, EMAIL_B)
        page.click("#view-shared")
        page.wait_for_function("document.querySelectorAll('.file-card').length >= 1",
                               timeout=15000)
        page.wait_for_timeout(500)
        page.screenshot(path=f"{IMGDIR}/05_shared_with_me.png")
        print("captured shared-with-me")

        ctx.close()
        browser.close()
    print("DONE — screenshots in", IMGDIR)


if __name__ == "__main__":
    main()
