"""
Generates CloudDrive_Technical_Report.pdf — the full project report:
introduction, architecture, flow diagrams, data model, tech stack, security,
real UI screenshots, deployment, testing, CI/CD, cost, and conclusion.

Run:  python docs/generate_report.py   (after capture_screenshots.py)
"""
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether,
)
from reportlab.platypus.doctemplate import NextPageTemplate
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Group

HERE = os.path.dirname(__file__)
IMG = os.path.join(HERE, "img")
OUT = os.path.join(HERE, "CloudDrive_Technical_Report.pdf")

# palette
INK = HexColor("#1f2937")
MUTED = HexColor("#6b7280")
BRAND = HexColor("#2563eb")
BRAND_D = HexColor("#1d4ed8")
LIGHT = HexColor("#eef2ff")
LINE = HexColor("#e5e7eb")
GREEN = HexColor("#059669")
AMBER = HexColor("#b45309")

MARGIN = 46
CW = A4[0] - 2 * MARGIN   # content width

# ---------------- styles ----------------
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                    fontSize=16, textColor=BRAND, spaceBefore=6, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                    fontSize=12, textColor=INK, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontName="Helvetica",
                      fontSize=9.5, leading=14, textColor=INK, spaceAfter=6)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=8, textColor=MUTED)
CAP = ParagraphStyle("CAP", parent=BODY, fontSize=8, textColor=MUTED,
                     alignment=TA_CENTER, spaceBefore=3, spaceAfter=10)
BULLET = ParagraphStyle("BULLET", parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=3)
TH = ParagraphStyle("TH", parent=BODY, fontName="Helvetica-Bold", fontSize=9,
                    textColor=white, leading=12)
TD = ParagraphStyle("TD", parent=BODY, fontSize=8.7, leading=12, spaceAfter=0)
TDB = ParagraphStyle("TDB", parent=TD, fontName="Helvetica-Bold")


# ---------------- helpers ----------------
def para(t, st=BODY):
    return Paragraph(t, st)


def bullets(items):
    return [Paragraph(f"• {t}", BULLET) for t in items]


def table(headers, rows, col_widths):
    data = [[Paragraph(h, TH) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), TD) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f8fafc")]),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
    ]
    t.setStyle(TableStyle(style))
    return t


def screenshot(name, caption, max_w=CW, max_h=300):
    path = os.path.join(IMG, name)
    iw, ih = ImageReader(path).getSize()
    w = max_w
    h = w * ih / iw
    if h > max_h:
        h = max_h
        w = h * iw / ih
    img = Image(path, width=w, height=h)
    img.hAlign = "CENTER"
    # frame the image with a light border via a 1-cell table
    framed = Table([[img]], colWidths=[w])
    framed.hAlign = "CENTER"
    framed.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.7, LINE),
                                ("TOPPADDING", (0, 0), (-1, -1), 0),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    return KeepTogether([framed, para(caption, CAP)])


def _arrow(d, x1, y, x2):
    d.add(Line(x1, y, x2 - 6, y, strokeColor=BRAND, strokeWidth=1.3))
    d.add(Polygon([x2 - 6, y - 3.5, x2, y, x2 - 6, y + 3.5], fillColor=BRAND, strokeColor=BRAND))


def _box(d, x, y, w, h, title, subs, fill=LIGHT, stroke=BRAND, tcolor=BRAND_D):
    d.add(Rect(x, y, w, h, rx=6, ry=6, fillColor=fill, strokeColor=stroke, strokeWidth=1))
    d.add(String(x + w / 2, y + h - 15, title, textAnchor="middle",
                 fontName="Helvetica-Bold", fontSize=8.5, fillColor=tcolor))
    yy = y + h - 27
    for s in subs:
        d.add(String(x + w / 2, yy, s, textAnchor="middle",
                     fontName="Helvetica", fontSize=7, fillColor=MUTED))
        yy -= 9


def pipeline(steps, width=CW, box_h=50):
    """Horizontal boxes connected by arrows. steps = [(title,[subs]), ...]"""
    n = len(steps)
    gap = 16
    bw = (width - gap * (n - 1)) / n
    d = Drawing(width, box_h + 6)
    x = 0
    for i, (title, subs) in enumerate(steps):
        _box(d, x, 3, bw, box_h, title, subs)
        if i < n - 1:
            _arrow(d, x + bw, 3 + box_h / 2, x + bw + gap)
        x += bw + gap
    return d


def architecture_diagram(width=CW):
    """Layered architecture: Browser -> ALB/CDN -> API(ECS) -> {S3, RDS}."""
    d = Drawing(width, 250)
    cx = width / 2
    # Browser
    _box(d, cx - 70, 210, 140, 34, "User Browser", ["React-style SPA"])
    _arrow_v(d, cx, 210, 196)
    # Edge / LB
    _box(d, cx - 110, 162, 220, 34, "CloudFront + Load Balancer (ALB)",
         ["HTTPS, caching, traffic distribution"], fill=HexColor("#fff7ed"), stroke=AMBER, tcolor=AMBER)
    _arrow_v(d, cx, 162, 148)
    # API
    _box(d, cx - 130, 104, 260, 40, "Stateless API  —  FastAPI on ECS Fargate",
         ["JWT auth · pre-signed URLs · autoscaling 1->4"], fill=LIGHT, stroke=BRAND)
    # to S3 and RDS
    s3x, rdsx = width * 0.22, width * 0.78
    d.add(Line(cx - 60, 104, s3x, 70, strokeColor=BRAND, strokeWidth=1.2))
    d.add(Line(cx + 60, 104, rdsx, 70, strokeColor=BRAND, strokeWidth=1.2))
    _box(d, s3x - 78, 30, 156, 40, "Amazon S3",
         ["File bytes (versioned,", "encrypted, private)"], fill=HexColor("#f0fdf4"), stroke=GREEN, tcolor=GREEN)
    _box(d, rdsx - 78, 30, 156, 40, "Amazon RDS (PostgreSQL)",
         ["Metadata: users,", "files, shares"], fill=HexColor("#eef2ff"), stroke=BRAND)
    # browser-> S3 direct (pre-signed)
    d.add(Line(cx - 70, 224, s3x, 70, strokeColor=GREEN, strokeWidth=0.9, strokeDashArray=[3, 3]))
    d.add(String(s3x, 150, "pre-signed PUT/GET", textAnchor="middle",
                 fontName="Helvetica-Oblique", fontSize=6.5, fillColor=GREEN))
    return d


def _arrow_v(d, x, y_top, y_bot):
    d.add(Line(x, y_top, x, y_bot + 6, strokeColor=BRAND, strokeWidth=1.3))
    d.add(Polygon([x - 3.5, y_bot + 6, x + 3.5, y_bot + 6, x, y_bot], fillColor=BRAND, strokeColor=BRAND))


# ---------------- document ----------------
def header_footer(canvas, doc):
    canvas.saveState()
    # header line (skip on cover)
    if doc.page > 1:
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, A4[1] - 30, "CloudDrive — Technical Report")
        canvas.setStrokeColor(LINE)
        canvas.line(MARGIN, A4[1] - 34, A4[0] - MARGIN, A4[1] - 34)
    # footer
    canvas.setStrokeColor(LINE)
    canvas.line(MARGIN, 34, A4[0] - MARGIN, 34)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 24, "github.com/Shehriyar-Ali-Rustam/clouddrive")
    canvas.drawRightString(A4[0] - MARGIN, 24, "Page %d" % doc.page)
    canvas.restoreState()


def cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BRAND)
    canvas.rect(0, A4[1] - 250, A4[0], 250, fill=1, stroke=0)
    # cloud logo
    canvas.setFillColor(white)
    canvas.roundRect(MARGIN, A4[1] - 150, 70, 70, 16, fill=1, stroke=0)
    canvas.setFillColor(BRAND)
    cx, cy = MARGIN + 35, A4[1] - 120
    canvas.circle(cx - 11, cy, 10, fill=1, stroke=0)
    canvas.circle(cx + 7, cy + 4, 13, fill=1, stroke=0)
    canvas.circle(cx + 15, cy, 9, fill=1, stroke=0)
    canvas.rect(cx - 20, cy - 14, 38, 12, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 34)
    canvas.drawString(MARGIN + 86, A4[1] - 110, "CloudDrive")
    canvas.setFont("Helvetica", 15)
    canvas.drawString(MARGIN + 88, A4[1] - 132, "Technical Report")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(MARGIN, A4[1] - 200, "Scalable File Storage on AWS — a Mini Google Drive")
    canvas.drawString(MARGIN, A4[1] - 216, "Final-Year Cloud Computing Project")
    header_footer(canvas, doc)
    canvas.restoreState()


def build():
    doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=58, bottomMargin=44)
    frame = Frame(MARGIN, 44, CW, A4[1] - 58 - 44, id="main")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[Frame(MARGIN, 44, CW, 524, id="c")], onPage=cover),
        PageTemplate(id="body", frames=[frame], onPage=header_footer),
    ])

    e = []  # story
    # after the cover's page break, switch to the body template
    e.append(NextPageTemplate("body"))

    # ===== COVER PAGE CONTENT (below the band) =====
    e.append(Spacer(1, 12))
    e.append(para("Author: Shehriyar Ali Rustam", BODY))
    e.append(para("Repository: github.com/Shehriyar-Ali-Rustam/clouddrive", SMALL))
    e.append(Spacer(1, 10))
    e.append(para(
        "CloudDrive is a cloud-based file-storage web application — a simplified Google Drive — "
        "that lets users securely upload, organise, download and share files. It is built to "
        "demonstrate core cloud-computing principles: object storage, pre-signed URLs, a managed "
        "database, stateless auto-scaling services, infrastructure as code, and CI/CD.", BODY))
    e.append(Spacer(1, 6))
    e.append(table(["Aspect", "Summary"], [
        ["Type", "Full-stack web application (REST API + SPA)"],
        ["Cloud storage", "Amazon S3 (live) with pre-signed URLs"],
        ["Deployment", "Render / Docker + AWS ECS (Terraform); live demo via tunnel"],
        ["Tests", "19 automated tests (all passing)"],
        ["Status", "Working, deployed, and version-controlled on GitHub"],
    ], [CW * 0.28, CW * 0.72]))
    e.append(PageBreak())

    # ===== 1. INTRODUCTION =====
    e.append(para("1. Introduction", H1))
    e.append(para("1.1 Problem Statement", H2))
    e.append(para(
        "Storing and sharing files across devices and people is a universal need. Traditional "
        "approaches that stream every file through an application server do not scale: the server "
        "becomes a bottleneck and a single point of failure. CloudDrive solves this using cloud "
        "object storage and pre-signed URLs, keeping the application server stateless and "
        "horizontally scalable.", BODY))
    e.append(para("1.2 Objectives", H2))
    e.extend(bullets([
        "Provide secure user accounts with authentication and per-user isolation.",
        "Allow uploading, downloading, organising and deleting files in the cloud.",
        "Enable sharing — both with registered users and via public expiring links.",
        "Demonstrate a scalable, cloud-native architecture (S3, RDS, ECS, IAM).",
        "Automate infrastructure (Terraform) and delivery (CI/CD).",
    ]))
    e.append(para("1.3 Scope", H2))
    e.append(para(
        "The system covers authentication, file/folder management, quotas, sharing, and a polished "
        "web UI. It runs in two interchangeable modes — a local mode (SQLite + disk) for offline "
        "development and an AWS mode (S3 + PostgreSQL) for the cloud — selected by configuration "
        "with no code changes.", BODY))

    # ===== 2. KEY FEATURES =====
    e.append(para("2. Key Features", H1))
    e.append(table(["Feature", "Description"], [
        ["Authentication", "Email + password sign-up/login, JWT tokens, bcrypt-hashed passwords"],
        ["File upload/download", "Browser transfers bytes directly to storage via pre-signed URLs"],
        ["Organisation", "Files and folders, isolated per user"],
        ["Sharing", "Share with a registered user, or create a public expiring link"],
        ["Storage quota", "Per-user limit with a live usage bar"],
        ["Versioning", "S3 bucket versioning keeps previous file versions"],
        ["Two run modes", "Local (SQLite+disk) and Cloud (S3+PostgreSQL) via one setting"],
    ], [CW * 0.26, CW * 0.74]))

    # ===== 3. ARCHITECTURE =====
    e.append(para("3. System Architecture", H1))
    e.append(para(
        "The design separates concerns cleanly: the database stores only metadata (who owns what, "
        "file names, sizes, storage keys, share rules) while Amazon S3 stores the actual file "
        "bytes. The browser talks directly to S3 for the heavy data transfer.", BODY))
    e.append(architecture_diagram())
    e.append(para("Figure 1: High-level cloud architecture.", CAP))
    e.append(para("3.1 Components", H2))
    e.append(table(["Component", "Technology", "Responsibility"], [
        ["Frontend", "HTML/CSS/JS SPA", "Dashboard UI, upload flow, sharing"],
        ["API", "FastAPI on ECS Fargate", "Auth, metadata, pre-signed URL issuing"],
        ["File storage", "Amazon S3", "Stores file bytes; versioned & encrypted"],
        ["Database", "PostgreSQL (RDS) / SQLite", "Users, files, folders, shares"],
        ["Load balancer", "Application Load Balancer", "Distributes traffic, health checks"],
        ["Auth", "JWT + bcrypt", "Stateless authentication"],
        ["IaC", "Terraform", "Provisions the entire AWS stack"],
    ], [CW * 0.22, CW * 0.30, CW * 0.48]))

    # ===== 4. UPLOAD FLOW =====
    e.append(para("4. The Pre-signed URL Upload Flow", H1))
    e.append(para(
        "This is the central cloud concept. The API never streams file bytes; it only issues a "
        "short-lived, signed permission slip (a pre-signed URL) and the browser uploads directly "
        "to S3. This keeps the API lightweight and horizontally scalable.", BODY))
    e.append(pipeline([
        ("1. Init", ["Browser tells API", "name + size"]),
        ("2. Ticket", ["API checks quota,", "returns pre-signed URL"]),
        ("3. Upload", ["Browser PUTs bytes", "directly to S3"]),
        ("4. Complete", ["API marks done,", "updates quota"]),
    ]))
    e.append(para("Figure 2: Three-step pre-signed upload sequence.", CAP))

    # ===== 5. DATA MODEL =====
    e.append(para("5. Data Model", H1))
    e.append(para("Four tables capture all metadata. File bytes live in S3, referenced by a storage key.", BODY))
    e.append(table(["Table", "Key Fields", "Purpose"], [
        ["users", "id, email, password_hash, storage_used, storage_quota", "Accounts & quota"],
        ["folders", "id, name, owner_id, parent_id", "Folder hierarchy"],
        ["files", "id, name, s3_key, size, owner_id, folder_id, uploaded", "File metadata"],
        ["shares", "id, file_id, shared_with_user_id, public_token, expires_at", "Sharing rules"],
    ], [CW * 0.14, CW * 0.52, CW * 0.34]))

    # ===== 6. TECH STACK =====
    e.append(para("6. Technology Stack", H1))
    e.append(para("A full illustrated list (with icons) is in CloudDrive_Tech_Stack.pdf. Summary:", BODY))
    e.append(table(["Layer", "Tools & Services"], [
        ["Language/Backend", "Python 3.12, FastAPI, Uvicorn, SQLAlchemy, Pydantic"],
        ["Frontend", "HTML5, CSS3, Vanilla JavaScript"],
        ["Security", "JWT (python-jose), bcrypt"],
        ["Storage/DB", "Amazon S3, PostgreSQL, SQLite, psycopg2, boto3"],
        ["AWS", "S3, IAM, RDS, ECS Fargate, ALB, VPC, ECR"],
        ["DevOps", "Terraform, Docker, GitHub Actions, Git, pytest"],
        ["Hosting", "Render, Cloudflare Tunnel"],
    ], [CW * 0.26, CW * 0.74]))

    # ===== 7. SECURITY =====
    e.append(para("7. Security Model", H1))
    e.append(table(["Control", "How it protects the system"], [
        ["Password hashing", "bcrypt one-way hashes; plaintext never stored"],
        ["JWT auth", "Signed, expiring bearer tokens on every API call"],
        ["Pre-signed URLs", "Time-limited (15 min), scoped to a single object"],
        ["Private bucket", "S3 blocks all public access; encrypted at rest (AES-256)"],
        ["IAM least-privilege", "API role may touch only this one bucket"],
        ["Per-user isolation", "Every query filtered by owner_id"],
        ["Quota enforcement", "Prevents a single user exhausting storage"],
    ], [CW * 0.26, CW * 0.74]))

    # ===== 8. USER INTERFACE (screenshots) =====
    e.append(PageBreak())
    e.append(para("8. User Interface", H1))
    e.append(para("The following are real screenshots of the running application (storage badge shows S3).", BODY))
    e.append(screenshot("01_login.png", "Figure 3: Sign-up / login screen.", max_h=260))
    e.append(screenshot("02_dashboard.png", "Figure 4: Dashboard — files on AWS S3, quota bar, type icons.", max_h=300))
    e.append(screenshot("03_share_modal.png", "Figure 5: Share dialog — share with a user or create a public link.", max_h=300))
    e.append(screenshot("04_public_link.png", "Figure 6: A generated public expiring link.", max_h=300))
    e.append(screenshot("05_shared_with_me.png", "Figure 7: 'Shared with me' — files another user shared.", max_h=260))

    # ===== 9. DEPLOYMENT =====
    e.append(para("9. Cloud Deployment", H1))
    e.append(para(
        "Files are stored in a real Amazon S3 bucket using pre-signed URLs. The application can be "
        "run/deployed three ways, all sharing the same S3 storage:", BODY))
    e.append(pipeline([
        ("Local", ["SQLite + disk", "or S3 mode"]),
        ("Render", ["Permanent URL", "+ managed Postgres"]),
        ("AWS ECS", ["Docker image,", "autoscaling (Terraform)"]),
    ], box_h=46))
    e.append(para("Figure 8: Deployment options (all use Amazon S3 for files).", CAP))
    e.append(para(
        "For demonstrations, a Cloudflare tunnel exposes the local app on a public HTTPS URL so it "
        "can be opened from any device. The full AWS stack is defined in Terraform (validated) and "
        "deploys via the CI/CD pipeline below.", BODY))

    # ===== 10. TESTING =====
    e.append(para("10. Testing", H1))
    e.append(para("Nineteen automated tests (pytest) cover the critical paths and security:", BODY))
    e.append(table(["Area", "Examples", "Tests"], [
        ["Authentication", "signup, login, wrong password, duplicate email", "6"],
        ["Files", "upload lifecycle, listing, quota, delete, isolation", "7"],
        ["Sharing & security", "user share, public link, tampered/expired URL", "6"],
    ], [CW * 0.24, CW * 0.56, CW * 0.20]))
    e.append(para("All 19 tests pass and run automatically on every push via GitHub Actions.", SMALL))

    # ===== 11. CI/CD =====
    e.append(para("11. CI/CD Pipeline", H1))
    e.append(pipeline([
        ("git push", ["Code to GitHub"]),
        ("CI: Tests", ["Run all 19 tests"]),
        ("Build", ["Docker image", "-> Amazon ECR"]),
        ("Deploy", ["Rolling update", "on ECS"]),
    ], box_h=46))
    e.append(para("Figure 9: Continuous integration & deployment flow.", CAP))

    # ===== 12. COST =====
    e.append(para("12. Cost & Free Tier", H1))
    e.append(table(["Service", "Cost note"], [
        ["Amazon S3", "Free tier: 5 GB + 20k GETs + 2k PUTs — demo cost ~ $0"],
        ["IAM / ECR", "Free"],
        ["RDS (db.t3.micro)", "Free-tier eligible for 12 months"],
        ["ALB / NAT / ECS", "Billed hourly — destroyed after demos via 'terraform destroy'"],
        ["Render / Tunnel", "Free tiers"],
    ], [CW * 0.28, CW * 0.72]))

    # ===== 13. CONCLUSION =====
    e.append(para("13. Conclusion & Future Work", H1))
    e.append(para(
        "CloudDrive delivers a complete, working, and tested cloud application that demonstrates "
        "the key principles of cloud computing — object storage, pre-signed URLs, managed "
        "databases, stateless scalable services, least-privilege security, infrastructure as code, "
        "and automated delivery. It runs on real AWS S3 and is fully reproducible from version "
        "control.", BODY))
    e.extend(bullets([
        "Future: multipart upload for very large files (S3 multipart + Lambda confirm).",
        "Future: file previews and full-text search over metadata.",
        "Future: organisation/team workspaces and granular permissions.",
    ]))
    e.append(Spacer(1, 8))
    e.append(para("Appendix — Run locally:  bash run.sh   ·   Run tests:  bash run_tests.sh   ·   "
                  "Public demo:  bash demo.sh", SMALL))

    doc.build(e)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
