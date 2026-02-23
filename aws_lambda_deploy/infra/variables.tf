# =============================================================================
# Variables for MetaAds Serverless Infrastructure
# =============================================================================

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to use"
  type        = string
  default     = "metads"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be 'dev' or 'prod'."
  }
}

variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "metaads"
}

# -----------------------------------------------------------------------------
# DynamoDB
# -----------------------------------------------------------------------------

variable "dynamodb_pitr_enabled" {
  description = "Enable Point-in-Time Recovery for DynamoDB"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Lambda
# -----------------------------------------------------------------------------

variable "lambda_runtime" {
  description = "Python runtime for Lambda functions"
  type        = string
  default     = "python3.11"
}

variable "lambda_memory_mb" {
  description = "Default memory for Lambda functions (MB)"
  type        = number
  default     = 256
}

variable "lambda_timeout_api" {
  description = "Timeout for API-facing Lambda functions (seconds)"
  type        = number
  default     = 15
}

variable "lambda_timeout_collector" {
  description = "Timeout for collection worker Lambda (seconds)"
  type        = number
  default     = 900
}

variable "lambda_collector_concurrency" {
  description = "Max concurrent collection workers (prevents Meta API rate limit abuse)"
  type        = number
  default     = 5
}

# -----------------------------------------------------------------------------
# API Gateway
# -----------------------------------------------------------------------------

variable "api_throttle_burst" {
  description = "API Gateway throttle burst limit (requests)"
  type        = number
  default     = 100
}

variable "api_throttle_rate" {
  description = "API Gateway throttle sustained rate (requests/second)"
  type        = number
  default     = 50
}

variable "cors_allow_origins" {
  description = "Allowed CORS origins for API Gateway (set to CloudFront domain after first apply)"
  type        = list(string)
  # Default to wildcard so `terraform apply` works before CloudFront domain is known.
  # Replace in tfvars after first apply:
  #   dev.tfvars:  cors_allow_origins = ["https://<dist>.cloudfront.net"]
  #   prod.tfvars: cors_allow_origins = ["https://yourdomain.com"]
  default = ["*"]
}

# -----------------------------------------------------------------------------
# CloudFront / Domain
# -----------------------------------------------------------------------------

variable "custom_domain" {
  description = "Custom domain for CloudFront (optional, leave empty to skip)"
  type        = string
  default     = ""
}

variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100" # US, Canada, Europe only (cheapest)
}

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------

variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "alarm_email" {
  description = "Email for CloudWatch alarm notifications (optional)"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}

locals {
  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })

  # Resource naming convention: {project}-{resource}-{env}
  name_prefix = "${var.project_name}-${var.environment}"
}
