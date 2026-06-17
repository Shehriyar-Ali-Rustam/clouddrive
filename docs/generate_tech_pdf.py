"""
Generates CloudDrive_Tech_Stack.pdf — a technical document listing every tool
and cloud service used, each with a custom vector icon drawn programmatically
(no external image files; every icon is hand-built here with reportlab).

Run:  python docs/generate_tech_pdf.py
"""
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas

W, H = A4
MARGIN = 46
OUT = os.path.join(os.path.dirname(__file__), "CloudDrive_Tech_Stack.pdf")

# ---- palette ----
INK = HexColor("#1f2937")
MUTED = HexColor("#6b7280")
BRAND = HexColor("#2563eb")
LIGHT = HexColor("#eef2ff")
LINE = HexColor("#e5e7eb")

# brand-ish colors per tool
C = {
    "python": HexColor("#3776AB"), "fastapi": HexColor("#059669"),
    "uvicorn": HexColor("#6d28d9"), "sqlalchemy": HexColor("#b91c1c"),
    "pydantic": HexColor("#e11d48"), "html": HexColor("#e34f26"),
    "css": HexColor("#1572b6"), "js": HexColor("#eab308"),
    "jwt": HexColor("#d946ef"), "bcrypt": HexColor("#475569"),
    "s3": HexColor("#569A31"), "postgres": HexColor("#336791"),
    "sqlite": HexColor("#0f80cc"), "psycopg": HexColor("#336791"),
    "boto3": HexColor("#FF9900"), "iam": HexColor("#DD344C"),
    "rds": HexColor("#3334B9"), "ecs": HexColor("#FF9900"),
    "alb": HexColor("#8C4FFF"), "vpc": HexColor("#E7157B"),
    "ecr": HexColor("#FF9900"), "terraform": HexColor("#7B42BC"),
    "docker": HexColor("#2496ED"), "ghactions": HexColor("#2088FF"),
    "git": HexColor("#F05032"), "pytest": HexColor("#0A9EDC"),
    "render": HexColor("#000000"), "cloudflare": HexColor("#F38020"),
}


# ----------------------------------------------------------------------
#  ICON PRIMITIVES — each draws an s x s icon with bottom-left at (x, y)
# ----------------------------------------------------------------------
def _bg(c, x, y, s, color, r=None):
    c.setFillColor(color)
    c.roundRect(x, y, s, s, r or s * 0.24, fill=1, stroke=0)


def _letter(c, x, y, s, txt, color, fg=white):
    _bg(c, x, y, s, color)
    c.setFillColor(fg)
    fs = s * (0.5 if len(txt) <= 2 else 0.34)
    c.setFont("Helvetica-Bold", fs)
    c.drawCentredString(x + s / 2, y + s / 2 - fs * 0.35, txt)


def ic_cloud(c, x, y, s, color=BRAND, fg=white):
    _bg(c, x, y, s, color)
    c.setFillColor(fg)
    cx, cy = x + s / 2, y + s * 0.42
    c.circle(cx - s * 0.16, cy, s * 0.15, fill=1, stroke=0)
    c.circle(cx + s * 0.10, cy + s * 0.06, s * 0.18, fill=1, stroke=0)
    c.circle(cx + s * 0.20, cy, s * 0.13, fill=1, stroke=0)
    c.rect(x + s * 0.30, y + s * 0.30, s * 0.42, s * 0.16, fill=1, stroke=0)


def ic_bucket(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setFillColor(fg)
    p = c.beginPath()
    p.moveTo(x + s * 0.28, y + s * 0.68)
    p.lineTo(x + s * 0.72, y + s * 0.68)
    p.lineTo(x + s * 0.64, y + s * 0.30)
    p.lineTo(x + s * 0.36, y + s * 0.30)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.setStrokeColor(color); c.setLineWidth(s * 0.04)
    c.line(x + s * 0.31, y + s * 0.55, x + s * 0.69, y + s * 0.55)


def ic_cylinder(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setStrokeColor(fg); c.setFillColor(fg); c.setLineWidth(s * 0.045)
    w = s * 0.44
    cx = x + s / 2
    top, bot = y + s * 0.70, y + s * 0.32
    eh = s * 0.10
    c.ellipse(cx - w / 2, top - eh, cx + w / 2, top + eh, fill=1, stroke=0)
    c.setStrokeColor(fg)
    c.line(cx - w / 2, top, cx - w / 2, bot)
    c.line(cx + w / 2, top, cx + w / 2, bot)
    c.setFillColor(color)
    c.ellipse(cx - w / 2, bot - eh, cx + w / 2, bot + eh, fill=1, stroke=1)


def ic_shield(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setFillColor(fg)
    p = c.beginPath()
    p.moveTo(x + s * 0.5, y + s * 0.74)
    p.lineTo(x + s * 0.72, y + s * 0.62)
    p.lineTo(x + s * 0.72, y + s * 0.40)
    p.lineTo(x + s * 0.5, y + s * 0.26)
    p.lineTo(x + s * 0.28, y + s * 0.40)
    p.lineTo(x + s * 0.28, y + s * 0.62)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.setStrokeColor(color); c.setLineWidth(s * 0.05)
    c.line(x + s * 0.40, y + s * 0.50, x + s * 0.47, y + s * 0.42)
    c.line(x + s * 0.47, y + s * 0.42, x + s * 0.61, y + s * 0.58)


def ic_key(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setStrokeColor(fg); c.setFillColor(fg); c.setLineWidth(s * 0.06)
    c.circle(x + s * 0.36, y + s * 0.56, s * 0.12, fill=0, stroke=1)
    c.line(x + s * 0.45, y + s * 0.47, x + s * 0.70, y + s * 0.30)
    c.line(x + s * 0.62, y + s * 0.38, x + s * 0.68, y + s * 0.44)
    c.line(x + s * 0.55, y + s * 0.45, x + s * 0.61, y + s * 0.51)


def ic_lock(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setStrokeColor(fg); c.setLineWidth(s * 0.06)
    c.arc(x + s * 0.37, y + s * 0.50, x + s * 0.63, y + s * 0.74, startAng=0, extent=180)
    c.setFillColor(fg)
    c.roundRect(x + s * 0.33, y + s * 0.30, s * 0.34, s * 0.26, s * 0.04, fill=1, stroke=0)


def ic_container(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setFillColor(fg)
    for i in range(3):
        c.roundRect(x + s * (0.30 + i * 0.135), y + s * 0.50, s * 0.10, s * 0.12, 1, fill=1, stroke=0)
    c.roundRect(x + s * 0.30, y + s * 0.34, s * 0.40, s * 0.12, 1, fill=1, stroke=0)


def ic_cubes(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setFillColor(fg)
    sz = s * 0.13
    for (cx, cy) in [(0.34, 0.52), (0.50, 0.52), (0.34, 0.34), (0.50, 0.34), (0.66, 0.43)]:
        c.roundRect(x + s * cx, y + s * cy, sz, sz, 1, fill=1, stroke=0)


def ic_play(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setStrokeColor(fg); c.setLineWidth(s * 0.055)
    c.circle(x + s * 0.5, y + s * 0.5, s * 0.20, fill=0, stroke=1)
    c.setFillColor(fg)
    p = c.beginPath()
    p.moveTo(x + s * 0.45, y + s * 0.40)
    p.lineTo(x + s * 0.45, y + s * 0.60)
    p.lineTo(x + s * 0.60, y + s * 0.50)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def ic_branch(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setStrokeColor(fg); c.setFillColor(fg); c.setLineWidth(s * 0.05)
    c.line(x + s * 0.36, y + s * 0.34, x + s * 0.36, y + s * 0.62)
    c.line(x + s * 0.36, y + s * 0.46, x + s * 0.62, y + s * 0.62)
    for (cx, cy) in [(0.36, 0.34), (0.36, 0.66), (0.64, 0.66)]:
        c.setFillColor(fg)
        c.circle(x + s * cx, y + s * cy, s * 0.075, fill=1, stroke=0)


def ic_check(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setStrokeColor(fg); c.setLineWidth(s * 0.09)
    p = c.beginPath()
    p.moveTo(x + s * 0.32, y + s * 0.50)
    p.lineTo(x + s * 0.45, y + s * 0.36)
    p.lineTo(x + s * 0.70, y + s * 0.66)
    c.drawPath(p, fill=0, stroke=1)


def ic_nodes(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setStrokeColor(fg); c.setFillColor(fg); c.setLineWidth(s * 0.045)
    pts = [(0.34, 0.62), (0.66, 0.62), (0.5, 0.34)]
    c.line(x + s * pts[0][0], y + s * pts[0][1], x + s * pts[1][0], y + s * pts[1][1])
    c.line(x + s * pts[0][0], y + s * pts[0][1], x + s * pts[2][0], y + s * pts[2][1])
    c.line(x + s * pts[1][0], y + s * pts[1][1], x + s * pts[2][0], y + s * pts[2][1])
    for (cx, cy) in pts:
        c.circle(x + s * cx, y + s * cy, s * 0.07, fill=1, stroke=0)


def ic_bolt(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setFillColor(fg)
    p = c.beginPath()
    p.moveTo(x + s * 0.54, y + s * 0.72)
    p.lineTo(x + s * 0.34, y + s * 0.46)
    p.lineTo(x + s * 0.48, y + s * 0.46)
    p.lineTo(x + s * 0.44, y + s * 0.28)
    p.lineTo(x + s * 0.66, y + s * 0.54)
    p.lineTo(x + s * 0.52, y + s * 0.54)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def ic_balance(c, x, y, s, color, fg=white):
    _bg(c, x, y, s, color)
    c.setStrokeColor(fg); c.setFillColor(fg); c.setLineWidth(s * 0.045)
    c.line(x + s * 0.5, y + s * 0.30, x + s * 0.5, y + s * 0.68)
    c.line(x + s * 0.28, y + s * 0.62, x + s * 0.72, y + s * 0.62)
    c.line(x + s * 0.28, y + s * 0.62, x + s * 0.28, y + s * 0.46)
    c.line(x + s * 0.72, y + s * 0.62, x + s * 0.72, y + s * 0.46)
    c.line(x + s * 0.40, y + s * 0.30, x + s * 0.60, y + s * 0.30)


# dispatcher: key -> (drawer, color)
ICONS = {
    "python": ic_bolt, "fastapi": ic_bolt, "uvicorn": ic_bolt,
    "sqlalchemy": None, "pydantic": None, "html": None, "css": None, "js": None,
    "jwt": ic_key, "bcrypt": ic_lock,
    "s3": ic_bucket, "postgres": ic_cylinder, "sqlite": ic_cylinder,
    "psycopg": ic_cylinder, "boto3": None,
    "iam": ic_shield, "rds": ic_cylinder, "ecs": ic_container,
    "alb": ic_balance, "vpc": ic_nodes, "ecr": ic_container,
    "terraform": ic_cubes, "docker": ic_container, "ghactions": ic_play,
    "git": ic_branch, "pytest": ic_check, "render": None, "cloudflare": ic_cloud,
}
LETTERS = {"sqlalchemy": "SQL", "pydantic": "PyD", "html": "</>", "css": "CSS",
           "js": "JS", "boto3": "b3", "python": "Py", "render": "R"}


def draw_icon(c, key, x, y, s):
    color = C.get(key, BRAND)
    fn = ICONS.get(key)
    if fn is None:
        _letter(c, x, y, s, LETTERS.get(key, key[:2].upper()), color)
    elif key == "python":  # python gets a letter badge, others a glyph
        _letter(c, x, y, s, "Py", color)
    else:
        fn(c, x, y, s, color)


# ----------------------------------------------------------------------
#  CONTENT
# ----------------------------------------------------------------------
SECTIONS = [
    ("Backend & Language", [
        ("python", "Python 3.12", "Core programming language for the backend"),
        ("fastapi", "FastAPI", "High-performance async web framework (the REST API)"),
        ("uvicorn", "Uvicorn", "ASGI server that runs the FastAPI app"),
        ("sqlalchemy", "SQLAlchemy", "ORM — maps Python objects to database tables"),
        ("pydantic", "Pydantic", "Request/response validation and settings"),
    ]),
    ("Frontend", [
        ("html", "HTML5", "Structure of the single-page dashboard UI"),
        ("css", "CSS3", "Styling — responsive, modern Google-Drive-like design"),
        ("js", "JavaScript (Vanilla)", "Upload flow, drag & drop, sharing, view logic"),
    ]),
    ("Security & Authentication", [
        ("jwt", "JWT (python-jose)", "Stateless bearer-token authentication"),
        ("bcrypt", "bcrypt", "One-way password hashing (never stored in plain text)"),
    ]),
    ("Storage, Database & SDK", [
        ("s3", "AWS S3", "Object storage for file bytes (via pre-signed URLs)"),
        ("postgres", "PostgreSQL", "Production metadata database (users, files, shares)"),
        ("sqlite", "SQLite", "Zero-setup local database for development/demo"),
        ("psycopg", "psycopg2", "PostgreSQL driver used in production"),
        ("boto3", "boto3", "AWS SDK for Python — generates S3 pre-signed URLs"),
    ]),
    ("AWS Cloud Infrastructure", [
        ("s3", "Amazon S3", "Versioned, encrypted, private file storage"),
        ("iam", "AWS IAM", "Least-privilege roles & policies for secure access"),
        ("rds", "Amazon RDS", "Managed PostgreSQL database (Terraform)"),
        ("ecs", "Amazon ECS Fargate", "Serverless containers, auto-scaling 1->4 (Terraform)"),
        ("alb", "Application Load Balancer", "Distributes traffic across API containers"),
        ("vpc", "Amazon VPC", "Isolated network: public/private subnets, NAT"),
        ("ecr", "Amazon ECR", "Private Docker image registry"),
    ]),
    ("DevOps, IaC & Tooling", [
        ("terraform", "Terraform", "Infrastructure as Code — builds the whole AWS stack"),
        ("docker", "Docker", "Containerizes the app for portable deployment"),
        ("ghactions", "GitHub Actions", "CI/CD — runs tests, builds & deploys on push"),
        ("git", "Git & GitHub", "Version control and code hosting"),
        ("pytest", "pytest", "Automated test suite (19 tests: auth, upload, sharing)"),
    ]),
    ("Hosting & Networking", [
        ("render", "Render", "Cloud platform for permanent deployment + managed DB"),
        ("cloudflare", "Cloudflare Tunnel", "Public HTTPS URL for the live demo"),
    ]),
]


def footer(c, page):
    c.setStrokeColor(LINE); c.setLineWidth(0.6)
    c.line(MARGIN, 38, W - MARGIN, 38)
    c.setFont("Helvetica", 7.5); c.setFillColor(MUTED)
    c.drawString(MARGIN, 28, "CloudDrive — Technical Stack & Services")
    c.drawRightString(W - MARGIN, 28, "github.com/Shehriyar-Ali-Rustam/clouddrive   ·   Page %d" % page)


def wrap(c, text, font, size, maxw):
    c.setFont(font, size)
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if c.stringWidth(t, font, size) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def main():
    c = canvas.Canvas(OUT, pagesize=A4)
    page = 1

    # ---------- cover header ----------
    c.setFillColor(BRAND)
    c.rect(0, H - 150, W, 150, fill=1, stroke=0)
    ic_cloud(c, MARGIN, H - 116, 64, color=white, fg=BRAND)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(MARGIN + 84, H - 78, "CloudDrive")
    c.setFont("Helvetica", 13)
    c.drawString(MARGIN + 86, H - 98, "Technical Stack & Cloud Services")
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN + 86, H - 116, "Scalable file storage on AWS  ·  Final-year Cloud Computing project")

    y = H - 150 - 30
    c.setFillColor(INK); c.setFont("Helvetica", 9.5)
    intro = ("This document lists every technology, framework and cloud service used to build "
             "CloudDrive, grouped by layer. Each entry has a custom-drawn icon and a one-line "
             "description of its role in the system.")
    for ln in wrap(c, intro, "Helvetica", 9.5, W - 2 * MARGIN):
        c.drawString(MARGIN, y, ln); y -= 13
    y -= 10

    ROW = 30
    for title, items in SECTIONS:
        # section heading; ensure room for heading + 1 row
        if y < 70 + ROW:
            footer(c, page); c.showPage(); page += 1; y = H - 50
        c.setFillColor(LIGHT)
        c.roundRect(MARGIN, y - 18, W - 2 * MARGIN, 22, 5, fill=1, stroke=0)
        c.setFillColor(BRAND); c.setFont("Helvetica-Bold", 11.5)
        c.drawString(MARGIN + 10, y - 12, title)
        y -= 30

        for key, name, role in items:
            if y < 60:
                footer(c, page); c.showPage(); page += 1; y = H - 50
            s = 24
            draw_icon(c, key, MARGIN + 6, y - 18, s)
            c.setFillColor(INK); c.setFont("Helvetica-Bold", 10.5)
            c.drawString(MARGIN + 6 + s + 12, y - 6, name)
            c.setFillColor(MUTED); c.setFont("Helvetica", 8.8)
            c.drawString(MARGIN + 6 + s + 12, y - 17, role)
            c.setStrokeColor(LINE); c.setLineWidth(0.4)
            c.line(MARGIN + 6, y - 24, W - MARGIN, y - 24)
            y -= ROW

        y -= 8

    footer(c, page)
    c.save()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
