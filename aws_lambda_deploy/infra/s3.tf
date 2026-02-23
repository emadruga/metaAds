# =============================================================================
# S3 Buckets
# =============================================================================
#
# 1. Frontend bucket: Hosts Vue 3 SPA static files (served via CloudFront OAC)
# 2. Lambda bucket: Stores Lambda deployment packages (.zip)
#
# =============================================================================

# -----------------------------------------------------------------------------
# Frontend Hosting Bucket
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "frontend" {
  bucket        = "${local.name_prefix}-frontend-${data.aws_caller_identity.current.account_id}"
  force_destroy = var.environment == "dev" # Allow easy teardown in dev

  tags = {
    Name = "${local.name_prefix}-frontend"
  }
}

# Block ALL public access - CloudFront OAC is the only access path
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning for rollback capability
resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption (AES-256, free)
resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# CORS for frontend assets (needed for font loading, etc.)
resource "aws_s3_bucket_cors_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    max_age_seconds = 3600
  }
}

# -----------------------------------------------------------------------------
# Lambda Deployment Packages Bucket
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "lambda_packages" {
  bucket        = "${local.name_prefix}-lambda-${data.aws_caller_identity.current.account_id}"
  force_destroy = var.environment == "dev"

  tags = {
    Name = "${local.name_prefix}-lambda-packages"
  }
}

resource "aws_s3_bucket_public_access_block" "lambda_packages" {
  bucket = aws_s3_bucket.lambda_packages.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "lambda_packages" {
  bucket = aws_s3_bucket.lambda_packages.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_packages" {
  bucket = aws_s3_bucket.lambda_packages.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Lifecycle rule: expire old Lambda packages after 30 days
resource "aws_s3_bucket_lifecycle_configuration" "lambda_packages" {
  bucket = aws_s3_bucket.lambda_packages.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    filter {} # Apply to all objects in the bucket

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
