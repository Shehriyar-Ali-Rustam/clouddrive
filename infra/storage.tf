# ============================================================
#  S3 — file storage (the actual file bytes)
#  Private bucket; reachable only through time-limited pre-signed URLs.
# ============================================================

resource "aws_s3_bucket" "files" {
  bucket = var.bucket_name
  tags   = local.tags
}

# Keep old versions of every file (the "file versioning" feature).
resource "aws_s3_bucket_versioning" "files" {
  bucket = aws_s3_bucket.files.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt objects at rest.
resource "aws_s3_bucket_server_side_encryption_configuration" "files" {
  bucket = aws_s3_bucket.files.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block ALL public access — pre-signed URLs are the only way in.
resource "aws_s3_bucket_public_access_block" "files" {
  bucket                  = aws_s3_bucket.files.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CORS so the browser can PUT/GET directly via pre-signed URLs.
resource "aws_s3_bucket_cors_configuration" "files" {
  bucket = aws_s3_bucket.files.id
  cors_rule {
    allowed_methods = ["GET", "PUT"]
    allowed_origins = ["*"] # tighten to your CloudFront/frontend domain in prod
    allowed_headers = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Lifecycle: move noncurrent versions to cheaper storage after 30 days.
resource "aws_s3_bucket_lifecycle_configuration" "files" {
  bucket = aws_s3_bucket.files.id
  rule {
    id     = "archive-old-versions"
    status = "Enabled"
    filter {} # empty filter = applies to all objects in the bucket
    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }
  }
}
