# ☁️ CloudDrive — Scalable File Storage on AWS

> A "Mini Google Drive": upload, organise, and securely share files.
> Built as a final-year **Cloud Computing** project. Demonstrates object
> storage, pre-signed URLs, a metadata database, JWT authentication,
> per-user quotas, file sharing, Infrastructure-as-Code, and a clean
> deployable architecture for **AWS**.

---

## ✨ What it does

| Feature | How it works |
|---|---|
| 🔐 **Auth** | Email + password, JWT bearer tokens (bcrypt-hashed passwords) |
| ⬆️ **Upload** | Browser uploads bytes **directly to storage** via a pre-signed URL |
| ⬇️ **Download** | Short-lived pre-signed GET URL — secure & scalable |
| 📁 **Organise** | Files & folders, per-user isolation |
| 🔗 **Share** | Share with another user, or create a **public expiring link** |
| 📊 **Quota** | Per-user storage limit, live usage bar |
| 🗑️ **Manage** | Rename / delete, quota auto-adjusts |
| 🏗️ **Versioning** | Enabled on the S3 bucket (keeps old versions) |

## 🧠 The one idea that makes it "cloud"

The API server **never streams file bytes**. To upload:

```
1. Browser → API:   "I want to upload report.pdf (2 MB)"
2. API → Browser:   a PRE-SIGNED URL  (a temporary, signed permission slip)
3. Browser → S3:    PUT the bytes directly to storage
4. Browser → API:   "done!"  → API updates metadata + quota
```

Because the heavy data path skips the API, you can run many small,
**stateless** API containers behind a load balancer and autoscale them — the
core of elastic cloud design.

## 🏃 Run it locally (no AWS account needed)

The project ships with a **local storage backend** that emulates S3 pre-signed
URLs on your own disk, so the *entire* app — including the upload flow — runs
offline. Perfect for development and the live demo.

```bash
cd "cloud project"
bash run.sh
```

Then open **http://localhost:8000**, sign up, and start uploading.

> `run.sh` creates a virtualenv, installs dependencies, copies `.env`, and
> starts the server. To do it manually:
> ```bash
> python3 -m venv .venv && source .venv/bin/activate
> pip install -r requirements.txt
> cp .env.example .env
> uvicorn backend.main:app --reload
> ```

## ✅ Run the tests

19 automated tests cover auth, the full pre-signed upload/download lifecycle,
quota enforcement, per-user isolation, sharing, public links, and signed-URL
security:

```bash
bash run_tests.sh
```

## 🔄 CI/CD (GitHub Actions)

Two pipelines live in [.github/workflows/](.github/workflows/):

| Workflow | Trigger | What it does |
|---|---|---|
| [`ci.yml`](.github/workflows/ci.yml) | every push / PR | install deps, run all tests |
| [`deploy.yml`](.github/workflows/deploy.yml) | push to `main` (or manual) | build Docker image → push to **ECR** → rolling **ECS** deploy |

The deploy pipeline uses **GitHub OIDC** for keyless AWS auth. Configure these
in your repo (Settings → Secrets/Variables → Actions):

- Secret `AWS_ROLE_ARN` — an IAM role the workflow may assume.
- Variables `AWS_REGION`, `ECR_REPOSITORY`, `ECS_CLUSTER`, `ECS_SERVICE`
  (the last three come from `terraform output`).

## ☁️ Switch to real AWS S3

1. Create an S3 bucket (or run the Terraform in [`infra/`](infra/main.tf)).
2. Edit `.env`:
   ```env
   STORAGE_BACKEND=s3
   S3_BUCKET=your-bucket-name
   AWS_REGION=us-east-1
   DATABASE_URL=postgresql+psycopg2://user:pass@your-rds-host:5432/clouddrive
   ```
3. Make sure AWS credentials are available (env vars, `~/.aws/`, or an ECS task
   role in production).
4. Restart. **Nothing else changes** — same code, same UI, same upload flow.

## 🗂️ Project structure

```
cloud project/
├── backend/
│   ├── main.py        # FastAPI app + all endpoints
│   ├── config.py      # env-driven settings (local ↔ cloud)
│   ├── database.py    # SQLAlchemy (SQLite ↔ RDS Postgres)
│   ├── models.py      # User / Folder / File / Share tables
│   ├── schemas.py     # request/response contracts
│   ├── auth.py        # JWT + bcrypt
│   └── storage.py     # ★ S3 vs local pre-signed-URL abstraction
├── frontend/
│   ├── index.html     # dashboard UI
│   ├── style.css      # modern styling
│   └── app.js         # upload flow, sharing, drag & drop
├── infra/             # full AWS Terraform stack (see infra/DEPLOY.md)
│   ├── network.tf     #   VPC, subnets, NAT, security groups
│   ├── storage.tf     #   S3 bucket
│   ├── database.tf    #   RDS PostgreSQL
│   ├── ecs.tf         #   ECS Fargate service + CPU autoscaling
│   ├── alb.tf         #   Application Load Balancer
│   ├── iam.tf         #   least-privilege roles
│   └── ...            #   ecr.tf, variables.tf, outputs.tf, DEPLOY.md
├── tests/             # 19 pytest tests (auth, upload, sharing, security)
├── Dockerfile         # container for ECS Fargate
├── requirements.txt
├── run.sh             # one-command local launcher
├── run_tests.sh       # run the test suite
└── ARCHITECTURE.md    # diagrams + viva talking points
```

## 🔌 API reference (quick)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/signup` | create account → JWT |
| POST | `/api/auth/login` | log in → JWT |
| GET | `/api/auth/me` | current user + quota |
| POST | `/api/files/init` | get pre-signed upload URL |
| POST | `/api/files/{id}/complete` | mark upload done |
| GET | `/api/files` | list my files |
| GET | `/api/files/{id}/download` | pre-signed download URL |
| DELETE | `/api/files/{id}` | delete |
| POST | `/api/shares` | share with user / public link |
| GET | `/api/public/{token}` | public download |

Interactive API docs auto-generated at **http://localhost:8000/docs**.

## 🎓 For the report / viva

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for diagrams, the AWS deployment
plan (ECS Fargate + ALB + autoscaling + RDS + CloudFront), the security model
(IAM least-privilege, pre-signed URLs, encrypted-at-rest), and a ready-made
list of questions an examiner might ask with answers.

## 🛠️ Tech stack

Python · FastAPI · SQLAlchemy · JWT · boto3 · Vanilla JS · AWS S3 · RDS ·
ECS Fargate · Terraform · Docker
