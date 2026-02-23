# =============================================================================
# MetaAds Serverless Infrastructure - Main Configuration
# =============================================================================
#
# This Terraform configuration deploys the complete serverless infrastructure
# for the MetaAds competitive intelligence application:
#
#   - DynamoDB (single-table design)
#   - S3 (frontend hosting + Lambda packages)
#   - CloudFront (CDN + HTTPS)
#   - IAM (least-privilege roles)
#   - Secrets Manager (Meta API + Clerk keys)
#   - Lambda (placeholder functions, populated in Phase 3)
#   - API Gateway HTTP API (populated in Phase 3)
#   - CloudWatch (monitoring + alarms)
#
# Usage:
#   terraform init
#   terraform plan -var-file="dev.tfvars"
#   terraform apply -var-file="dev.tfvars"
#
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state in S3 with DynamoDB locking
  # Uncomment after creating the backend resources manually (see README)
  # backend "s3" {
  #   bucket         = "metaads-terraform-state"
  #   key            = "metaads/terraform.tfstate"
  #   region         = "us-east-1"
  #   profile        = "metads"
  #   dynamodb_table = "metaads-terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = local.common_tags
  }
}

# Data source: current AWS account and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
