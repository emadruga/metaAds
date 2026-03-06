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
custom_domain          = "metads.app"
acm_certificate_arn    = "arn:aws:acm:us-east-1:645069181643:certificate/d89a893a-5230-433f-bbc8-f028c64dbe63"
cloudfront_price_class = "PriceClass_100"

# CORS — allow both CloudFront origin and custom domain
cors_allow_origins = [
  "https://d3ba787xl1d882.cloudfront.net",
  "https://metads.app",
  "https://www.metads.app"
]

# Monitoring
cloudwatch_log_retention_days = 7
alarm_email                   = "emadruga@gmail.com"

# Admin users (Clerk user IDs) — fallback when JWT template is not configured
admin_user_ids = "user_392VMP1wtMQyC9ZZLG8FgeFqxAq"
