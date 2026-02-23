# =============================================================================
# Terraform Outputs
# =============================================================================
#
# These values are needed by subsequent phases:
#   - Phase 2: DynamoDB table name for repository layer
#   - Phase 3: IAM role ARNs for Lambda functions
#   - Phase 5: Secret ARNs for collector
#   - Phase 6: S3 bucket + CloudFront distribution for frontend deploy
#
# =============================================================================

# -----------------------------------------------------------------------------
# DynamoDB
# -----------------------------------------------------------------------------

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.main.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.main.arn
}

# -----------------------------------------------------------------------------
# S3
# -----------------------------------------------------------------------------

output "frontend_bucket_name" {
  description = "S3 bucket name for frontend static files"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_bucket_arn" {
  description = "S3 bucket ARN for frontend"
  value       = aws_s3_bucket.frontend.arn
}

output "lambda_bucket_name" {
  description = "S3 bucket name for Lambda deployment packages"
  value       = aws_s3_bucket.lambda_packages.id
}

# -----------------------------------------------------------------------------
# CloudFront
# -----------------------------------------------------------------------------

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront domain name (frontend URL)"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "frontend_url" {
  description = "Full frontend URL"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

# -----------------------------------------------------------------------------
# IAM Roles
# -----------------------------------------------------------------------------

output "lambda_api_role_arn" {
  description = "IAM role ARN for API Lambda functions"
  value       = aws_iam_role.lambda_api.arn
}

output "lambda_collector_role_arn" {
  description = "IAM role ARN for collection Lambda functions"
  value       = aws_iam_role.lambda_collector.arn
}

output "lambda_authorizer_role_arn" {
  description = "IAM role ARN for Lambda authorizer"
  value       = aws_iam_role.lambda_authorizer.arn
}

# -----------------------------------------------------------------------------
# Secrets Manager
# -----------------------------------------------------------------------------

output "meta_api_secret_arn" {
  description = "Secrets Manager ARN for Meta API credentials"
  value       = aws_secretsmanager_secret.meta_api.arn
}

output "clerk_secret_arn" {
  description = "Secrets Manager ARN for Clerk authentication keys"
  value       = aws_secretsmanager_secret.clerk.arn
}

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------

output "alarm_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms (empty if no email configured)"
  value       = var.alarm_email != "" ? aws_sns_topic.alarms[0].arn : ""
}

# -----------------------------------------------------------------------------
# Account Info
# -----------------------------------------------------------------------------

output "aws_account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}
