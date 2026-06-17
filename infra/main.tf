# ============================================================
#  CloudDrive — AWS infrastructure (Terraform)
#
#  Provisions a FULL production stack:
#    network.tf   VPC, public/private subnets, NAT, security groups
#    storage.tf   S3 bucket (versioned, encrypted, private)
#    database.tf  RDS PostgreSQL (metadata)
#    ecr.tf       container registry for the API image
#    iam.tf       least-privilege task roles
#    alb.tf       Application Load Balancer
#    ecs.tf       ECS Fargate service + CPU auto-scaling
#    outputs.tf   useful values after apply
#
#  Usage:
#    terraform init
#    terraform apply -var="db_password=SomeStrongPass123"
#    ...demo...
#    terraform destroy        # ← IMPORTANT: stops hourly charges
#
#  Cost note: S3/IAM/ECR are ~free. VPC NAT Gateway, RDS, ALB, and ECS
#  bill per hour — destroy when you're done. Set a billing alarm first.
# ============================================================

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# Convenient name prefix + tags applied to everything.
locals {
  name = "${var.project}-${var.environment}"
  tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Look up availability zones in the chosen region.
data "aws_availability_zones" "available" {
  state = "available"
}
