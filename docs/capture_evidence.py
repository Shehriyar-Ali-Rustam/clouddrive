"""
Captures evidence screenshots for the report:
  - img/gh_actions.png       GitHub Actions workflow list (public page)
  - img/gh_actions_run.png   a CI run detail
  - img/s3_bucket.png        terminal-style proof of files in the S3 bucket
  - img/docker.png           terminal-style proof of the running container
"""
import html
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(__file__)
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
ACTIONS_URL = "https://github.com/Shehriyar-Ali-Rustam/clouddrive/actions"
CI_RUN_URL = open("/tmp/ci_run_url.txt").read().strip()


def terminal_html(title, text):
    body = html.escape(text)
    return f"""<!doctype html><html><head><meta charset='utf-8'>
<style>
  body {{ margin:0; background:#0d1117; font-family:'DejaVu Sans Mono',monospace; }}
  .win {{ width:980px; margin:0; border-radius:10px; overflow:hidden;
          box-shadow:0 10px 40px rgba(0,0,0,.4); }}
  .bar {{ background:#21262d; padding:9px 14px; display:flex; align-items:center; gap:8px; }}
  .dot {{ width:12px; height:12px; border-radius:50%; display:inline-block; }}
  .r{{background:#ff5f56}} .y{{background:#ffbd2e}} .g{{background:#27c93f}}
  .title {{ color:#8b949e; font-size:13px; margin-left:10px; }}
  pre {{ color:#c9d1d9; font-size:13px; line-height:1.5; padding:16px 18px; margin:0;
         white-space:pre-wrap; word-break:break-word; }}
  .prompt {{ color:#58a6ff; }}
</style></head><body>
<div class='win'>
  <div class='bar'><span class='dot r'></span><span class='dot y'></span><span class='dot g'></span>
    <span class='title'>{html.escape(title)}</span></div>
  <pre>{body}</pre>
</div></body></html>"""


def shot_terminal(page, title, textfile, out):
    text = open(textfile).read()
    page.set_content(terminal_html(title, text))
    page.wait_for_timeout(300)
    el = page.query_selector(".win")
    el.screenshot(path=out)
    print("wrote", out)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox"])

        # terminal evidence images
        page = browser.new_context(viewport={"width": 1000, "height": 700},
                                   device_scale_factor=2).new_page()
        shot_terminal(page, "Amazon S3 — bucket contents (aws cli)", "/tmp/s3eos.txt",
                      os.path.join(IMG, "s3_bucket.png"))
        shot_terminal(page, "Docker — image & running container", "/tmp/dockeros.txt",
                      os.path.join(IMG, "docker.png"))

        # GitHub Actions (public repo)
        gh = browser.new_context(viewport={"width": 1300, "height": 950}).new_page()
        gh.goto(ACTIONS_URL, wait_until="domcontentloaded")
        gh.wait_for_timeout(3500)
        gh.screenshot(path=os.path.join(IMG, "gh_actions.png"))
        print("wrote gh_actions.png")

        gh.goto(CI_RUN_URL, wait_until="domcontentloaded")
        gh.wait_for_timeout(3500)
        gh.screenshot(path=os.path.join(IMG, "gh_actions_run.png"))
        print("wrote gh_actions_run.png")

        browser.close()


if __name__ == "__main__":
    main()
