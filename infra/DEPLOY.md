# 🚀 Deploying CloudDrive to AWS

This folder is a complete Terraform stack that builds the whole production
architecture from `ARCHITECTURE.md`:

```
VPC (2 AZs) ─ public subnets ─ ALB + NAT
            └ private subnets ─ ECS Fargate (API, autoscaling 1→4) ─ RDS Postgres
S3 (files, versioned/encrypted) · ECR (image) · IAM least-privilege · CloudWatch logs
```

## Prerequisites
- An AWS account + the **AWS CLI** configured (`aws configure`).
- **Terraform ≥ 1.5** and **Docker** installed.
- A **billing alarm** set (Billing → Budgets) — do this first!

## Step 1 — Provision infrastructure
```bash
cd infra
terraform init

# bucket name must be globally unique; pick your own
terraform apply \
  -var="bucket_name=clouddrive-files-yourname-123" \
  -var="db_password=ChooseAStrongPassword123"
```
Terraform prints outputs including `ecr_repository_url` and `app_url`.

## Step 2 — Build & push the API image
```bash
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
REPO=$(terraform output -raw ecr_repository_url)

aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com

docker build -t clouddrive-api ..          # builds ../Dockerfile
docker tag clouddrive-api:latest $REPO:latest
docker push $REPO:latest
```

## Step 3 — Roll out the new image
```bash
aws ecs update-service \
  --cluster   $(terraform output -raw ecs_cluster) \
  --service   $(terraform output -raw ecs_service) \
  --force-new-deployment
```
Wait ~2 minutes for the task to become healthy, then open `terraform output app_url`.

## Step 4 — Demo the autoscaling (the wow moment)
Generate load and watch ECS scale from 1 → 4 tasks in the AWS console
(ECS → cluster → service → Tasks), or via CloudWatch CPU graphs:
```bash
# simple load with hey (or use k6 / artillery)
hey -z 120s -c 50 "$(terraform output -raw app_url)/api/health"
```

## Step 5 — TEAR DOWN (important — stops hourly billing!)
```bash
terraform destroy \
  -var="bucket_name=clouddrive-files-yourname-123" \
  -var="db_password=ChooseAStrongPassword123"
```

## What costs money while running
| Resource | Note |
|---|---|
| NAT Gateway | ~hourly + data — the main cost |
| RDS db.t3.micro | free-tier eligible for 12 months |
| ALB | ~hourly |
| ECS Fargate | per task-second |
| S3 / ECR / IAM / CloudWatch | negligible for a demo |

> 💡 **Tip for a cheaper demo:** you can show `terraform plan`/`apply` to prove
> the infra is real, screenshot the running app + autoscaling, then
> `terraform destroy` the same day. The graded artifacts are the code, the
> plan output, and the screenshots — not a perpetually-running stack.

## Files
| File | Purpose |
|---|---|
| `main.tf` | providers, locals, shared data |
| `variables.tf` | all inputs (region, sizes, db creds) |
| `network.tf` | VPC, subnets, NAT, security groups |
| `storage.tf` | S3 bucket |
| `database.tf` | RDS PostgreSQL |
| `ecr.tf` | container registry |
| `iam.tf` | least-privilege task roles |
| `alb.tf` | load balancer + target group |
| `ecs.tf` | Fargate service + CPU autoscaling |
| `outputs.tf` | values printed after apply |
