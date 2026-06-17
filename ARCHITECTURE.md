# 🏗️ CloudDrive — Architecture & Viva Guide

This document is written so you can **explain and defend** the project. It
covers the design, the AWS deployment, the security model, and likely examiner
questions with answers.

---

## 1. High-level architecture (AWS production)

```
                         ┌──────────────┐
        User browser ───►│  CloudFront  │  CDN + HTTPS + caches the React UI
                         └──────┬───────┘
                                │
                 ┌──────────────┴───────────────┐
                 ▼                               ▼
        ┌─────────────────┐            ┌──────────────────────┐
        │  S3 (static UI) │            │  Application Load     │
        │  index/app/css  │            │  Balancer (ALB)       │
        └─────────────────┘            └──────────┬───────────┘
                                                  │  routes /api/*
                                       ┌──────────┴──────────┐
                                       ▼                     ▼
                                ┌─────────────┐       ┌─────────────┐
                                │ ECS Fargate │  ...  │ ECS Fargate │   API tasks
                                │  (API)      │       │  (API)      │   (autoscale 1→N)
                                └──────┬──────┘       └──────┬──────┘
                                       │                     │
                  ┌────────────────────┼─────────────────────┤
                  ▼                    ▼                     ▼
          ┌──────────────┐    ┌─────────────────┐   ┌──────────────┐
          │ RDS Postgres │    │  S3 (file bytes)│   │  Cognito/JWT │
          │  (metadata)  │    │  versioned,     │   │   auth       │
          │              │    │  encrypted      │   │              │
          └──────────────┘    └─────────────────┘   └──────────────┘
                                       ▲
                          pre-signed PUT/GET (browser ↔ S3 directly)
```

**Key separation:** the **database stores metadata** (who owns what, file name,
size, S3 key, share rules) while **S3 stores the actual bytes**. This is the
single most important architectural decision.

---

## 2. The pre-signed URL flow (explain this first in your viva)

```
 ┌─────────┐   1. init upload (name,size)   ┌─────────┐
 │ Browser │ ─────────────────────────────► │   API   │  checks quota,
 │         │ ◄───────────────────────────── │         │  writes metadata row,
 │         │   2. { pre-signed PUT URL }     └─────────┘  returns signed URL
 │         │
 │         │   3. PUT file bytes directly    ┌─────────┐
 │         │ ─────────────────────────────► │   S3    │  (API not involved)
 │         │ ◄───────────────────────────── │         │
 │         │
 │         │   4. complete                   ┌─────────┐
 │         │ ─────────────────────────────► │   API   │  marks uploaded=true,
 └─────────┘                                 └─────────┘  bills quota
```

**Why it matters:** the API stays *stateless* and *lightweight* — it only moves
small JSON, never gigabytes of file data. That is what lets us run many API
replicas and **autoscale** them horizontally.

> In this codebase, [`backend/storage.py`](backend/storage.py) implements this
> twice behind one interface: `S3Storage` (real AWS) and `LocalStorage` (HMAC-
> signed URLs served by our own `/api/blob/*` endpoints for the offline demo).

---

## 3. Components & AWS services

| Concern | Local demo | AWS production |
|---|---|---|
| File bytes | local disk | **S3** (versioned, AES-256 encrypted, private) |
| Metadata DB | SQLite | **RDS PostgreSQL** |
| Compute | uvicorn | **ECS Fargate** behind **ALB**, autoscaling |
| Static UI | served by API | **S3 + CloudFront** |
| Auth | JWT | JWT or **Cognito** |
| Secrets | `.env` | **Secrets Manager / SSM** + ECS task role |
| IaC | — | **Terraform** ([`infra/main.tf`](infra/main.tf)) |
| CI/CD | — | **GitHub Actions** → ECR → ECS |
| Monitoring | console logs | **CloudWatch** logs + alarms |

---

## 4. Scaling & elasticity

- **Stateless API** → put N copies behind the ALB; any task can serve any request.
- **Auto Scaling policy**: target ~60% CPU; ECS adds tasks (1 → 4) under load,
  removes them when idle.
- **S3** is effectively infinitely scalable and offloads all bulk data transfer.
- **RDS** handles only small metadata queries; add a read replica if needed.
- **ElastiCache (Redis)** is an optional add-on to cache hot metadata/sessions.

**Demo idea:** run a load test (`k6` / `artillery`) and screenshot ECS scaling
from 1 to 4 tasks in the AWS console. Strong evidence of "elasticity".

---

## 5. Security model

1. **Passwords** hashed with bcrypt — never stored in plaintext.
2. **JWT** bearer tokens authenticate every API call; expire after a set time.
3. **Pre-signed URLs** are time-limited (15 min) and scoped to one object — a
   leaked link dies quickly and grants no other access.
4. **S3 bucket is fully private** (`block public access`); the only way in is a
   pre-signed URL. Files encrypted at rest (AES-256).
5. **IAM least-privilege**: the API's role can only `GetObject/PutObject/
   DeleteObject` on **this one bucket** — nothing else in the account.
6. **Per-user isolation**: every query filters by `owner_id`; users can't see or
   touch each other's files unless explicitly shared.
7. **Quota enforcement** prevents a single user from exhausting storage.

---

## 6. Data model

```
users   (id, email, password_hash, storage_used, storage_quota)
folders (id, name, owner_id, parent_id)
files   (id, name, s3_key, size, content_type, owner_id, folder_id, uploaded)
shares  (id, file_id, shared_with_user_id, public_token, permission, expires_at)
```

- `files.s3_key` is the pointer into S3 (`u{user}/{uuid}_{name}`) — the UUID
  prevents name collisions and makes keys unguessable.
- A `share` row is either user-to-user (`shared_with_user_id`) or a public link
  (`public_token` + optional `expires_at`).

---

## 7. CI/CD pipeline (describe in report)

```
git push ──► GitHub Actions
               ├─ run tests / lint
               ├─ docker build  →  push image to Amazon ECR
               └─ aws ecs update-service --force-new-deployment
                       └─ ECS pulls new image, rolling deploy, zero downtime
```

---

## 8. Cost control (mention this — examiners like it)

- S3 + IAM in the Terraform are **free/near-free**.
- **RDS, ALB, NAT Gateway, ECS** bill per hour → run `terraform destroy` after
  the demo.
- Use `db.t3.micro` (free-tier) and set a **billing alarm at \$5** on day one.

---

## 9. Likely viva questions (with answers)

**Q: Why not upload files through your API server?**
A: It would force every byte through the API, making it a bottleneck and
stateful. Pre-signed URLs let the browser talk to S3 directly, so the API stays
stateless and horizontally scalable.

**Q: What exactly is a pre-signed URL?**
A: A normal S3 URL with a temporary signature in the query string proving the
API authorised this exact action (PUT/GET) on this exact object until an expiry
time. No AWS credentials are exposed to the browser.

**Q: How do you scale this?**
A: The API is stateless, so I run multiple Fargate tasks behind an ALB with an
auto-scaling policy on CPU. S3 and RDS handle data scaling.

**Q: Where are files actually stored vs the database?**
A: Bytes in S3; only metadata (name, size, owner, key, shares) in RDS. They're
linked by `s3_key`.

**Q: How is it secured?**
A: bcrypt passwords, JWT auth, private encrypted S3, time-limited scoped pre-
signed URLs, IAM least-privilege, and per-user `owner_id` isolation.

**Q: What happens if a pre-signed link leaks?**
A: It expires in ~15 minutes and only grants access to that single object — no
broader account or bucket access.

**Q: How would you make uploads resilient for huge files?**
A: Use S3 multipart upload (multiple pre-signed part URLs) and an S3 event →
Lambda to confirm completion.

**Q: Why SQLite locally but Postgres in the cloud?**
A: SQLite needs zero setup for development/demo; the code uses SQLAlchemy, so
switching to RDS Postgres is just a connection-string change.
