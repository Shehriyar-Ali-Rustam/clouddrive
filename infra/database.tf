# ============================================================
#  RDS PostgreSQL — stores metadata only (users, files, shares).
#  Lives in private subnets; only the API security group can reach it.
# ============================================================

resource "aws_db_subnet_group" "main" {
  name       = "${local.name}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
  tags       = local.tags
}

resource "aws_db_instance" "metadata" {
  identifier     = "${local.name}-db"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 100 # autoscale storage up to 100 GB
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]

  multi_az            = false # set true in prod for HA
  publicly_accessible = false
  skip_final_snapshot = true # fine for a student demo; true prod keeps snapshots
  deletion_protection = false

  tags = merge(local.tags, { Name = "${local.name}-db" })
}

# The SQLAlchemy connection string the API container will use.
locals {
  database_url = "postgresql+psycopg2://${var.db_username}:${var.db_password}@${aws_db_instance.metadata.address}:5432/${var.db_name}"
}
