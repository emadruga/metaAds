# =============================================================================
# Development Environment Variables
# =============================================================================

environment   = "dev"
project_name  = "metaads"
aws_region    = "us-east-1"
aws_profile   = "metads"

# DynamoDB
dynamodb_pitr_enabled = true

# Lambda
lambda_runtime              = "python3.11"
lambda_memory_mb            = 256
lambda_timeout_api          = 15
lambda_timeout_collector    = 900
lambda_collector_concurrency = 5

# API Gateway
api_throttle_burst = 100
api_throttle_rate  = 50

# CloudFront
custom_domain        = ""
cloudfront_price_class = "PriceClass_100"

# Monitoring
cloudwatch_log_retention_days = 7
alarm_email                   = ""
