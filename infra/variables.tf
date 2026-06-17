# ---- Inputs ----
variable "project" {
  description = "Project name, used as a prefix for resource names"
  default     = "clouddrive"
}

variable "environment" {
  description = "Deployment environment (dev/staging/prod)"
  default     = "dev"
}

variable "region" {
  default = "us-east-1"
}

variable "bucket_name" {
  description = "Globally-unique S3 bucket name for file storage"
  default     = "clouddrive-files-CHANGE-ME"
}

# --- Networking ---
variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

# --- Database ---
variable "db_name" {
  default = "clouddrive"
}

variable "db_username" {
  default = "clouddrive_admin"
}

variable "db_password" {
  description = "RDS master password (pass via -var or TF_VAR_db_password; never commit it)"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "db.t3.micro is free-tier eligible"
  default     = "db.t3.micro"
}

# --- API container ---
variable "container_port" {
  default = 8000
}

variable "api_cpu" {
  description = "Fargate CPU units (256 = 0.25 vCPU)"
  default     = 256
}

variable "api_memory" {
  description = "Fargate memory in MiB"
  default     = 512
}

variable "api_desired_count" {
  description = "Baseline number of API tasks"
  default     = 1
}

variable "api_max_count" {
  description = "Max API tasks the autoscaler may create"
  default     = 4
}
