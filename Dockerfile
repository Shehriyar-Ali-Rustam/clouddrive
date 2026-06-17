# ------------------------------------------------------------
#  CloudDrive API container — pushed to AWS ECR, run on ECS Fargate
# ------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend

EXPOSE 8000

# In production set STORAGE_BACKEND=s3 and DATABASE_URL to RDS via env vars.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
