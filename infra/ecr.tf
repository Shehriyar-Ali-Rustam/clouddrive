# ============================================================
#  ECR — Docker registry for the API image.
#
#  Build & push (after `terraform apply` creates the repo):
#    aws ecr get-login-password --region us-east-1 \
#      | docker login --username AWS --password-stdin <acct>.dkr.ecr.us-east-1.amazonaws.com
#    docker build -t clouddrive-api ..
#    docker tag clouddrive-api:latest <repo_url>:latest
#    docker push <repo_url>:latest
# ============================================================

resource "aws_ecr_repository" "api" {
  name                 = "${local.name}-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # lets `terraform destroy` remove it even with images

  image_scanning_configuration {
    scan_on_push = true
  }
  tags = local.tags
}

# Keep only the 10 most recent images to control storage cost.
resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}
