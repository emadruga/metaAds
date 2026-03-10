# =============================================================================
# IAM Roles - Least Privilege
# =============================================================================
#
# Separate roles for each Lambda function group.
# No wildcard (*) resource ARNs -- all scoped to specific resources.
#
# =============================================================================

# -----------------------------------------------------------------------------
# API Lambda Execution Role
# Used by: auth_handler, niches_handler, ads_handler, saved_handler
# Permissions: DynamoDB read/write, Secrets Manager read, CloudWatch Logs
# -----------------------------------------------------------------------------

resource "aws_iam_role" "lambda_api" {
  name = "${local.name_prefix}-lambda-api-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-lambda-api-role"
  }
}

# DynamoDB access for API Lambdas
resource "aws_iam_role_policy" "lambda_api_dynamodb" {
  name = "${local.name_prefix}-lambda-api-dynamodb"
  role = aws_iam_role.lambda_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBTableAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem",
          "dynamodb:BatchGetItem"
        ]
        Resource = [
          aws_dynamodb_table.main.arn,
          "${aws_dynamodb_table.main.arn}/index/*"
        ]
      }
    ]
  })
}

# Secrets Manager read access for API Lambdas (Clerk keys only)
resource "aws_iam_role_policy" "lambda_api_secrets" {
  name = "${local.name_prefix}-lambda-api-secrets"
  role = aws_iam_role.lambda_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SecretsManagerRead"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.clerk.arn,
          aws_secretsmanager_secret.meta_api.arn
        ]
      }
    ]
  })
}

# CloudWatch Logs for API Lambdas
resource "aws_iam_role_policy_attachment" "lambda_api_logs" {
  role       = aws_iam_role.lambda_api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# -----------------------------------------------------------------------------
# Collection Worker Lambda Role
# Used by: collect_trigger, collect_worker
# Permissions: DynamoDB read/write, Meta API secret, Lambda invoke, CloudWatch Logs
# -----------------------------------------------------------------------------

resource "aws_iam_role" "lambda_collector" {
  name = "${local.name_prefix}-lambda-collector-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-lambda-collector-role"
  }
}

# DynamoDB access for Collector (same as API, plus Scan for the scheduler)
resource "aws_iam_role_policy" "lambda_collector_dynamodb" {
  name = "${local.name_prefix}-lambda-collector-dynamodb"
  role = aws_iam_role.lambda_collector.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBTableAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem",
          "dynamodb:BatchGetItem"
        ]
        Resource = [
          aws_dynamodb_table.main.arn,
          "${aws_dynamodb_table.main.arn}/index/*"
        ]
      }
    ]
  })
}

# Secrets Manager read access for Collector (Meta API token + Clerk keys)
resource "aws_iam_role_policy" "lambda_collector_secrets" {
  name = "${local.name_prefix}-lambda-collector-secrets"
  role = aws_iam_role.lambda_collector.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SecretsManagerRead"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.meta_api.arn,
          aws_secretsmanager_secret.clerk.arn
        ]
      }
    ]
  })
}

# Lambda invoke permission (trigger invokes worker asynchronously)
resource "aws_iam_role_policy" "lambda_collector_invoke" {
  name = "${local.name_prefix}-lambda-collector-invoke"
  role = aws_iam_role.lambda_collector.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "InvokeCollectWorker"
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${local.name_prefix}-collect-worker"
        ]
      }
    ]
  })
}

# SQS DLQ write permission for Collector (collect_worker async failure destination)
resource "aws_iam_role_policy" "lambda_collector_dlq" {
  name = "${local.name_prefix}-lambda-collector-dlq"
  role = aws_iam_role.lambda_collector.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SendMessageToCollectWorkerDLQ"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = [
          aws_sqs_queue.collect_worker_dlq.arn
        ]
      }
    ]
  })
}

# CloudWatch Logs for Collector
resource "aws_iam_role_policy_attachment" "lambda_collector_logs" {
  role       = aws_iam_role.lambda_collector.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# -----------------------------------------------------------------------------
# Lambda Authorizer Role
# Used by: JWT authorizer function
# Permissions: Secrets Manager (Clerk JWKS), CloudWatch Logs
# -----------------------------------------------------------------------------

resource "aws_iam_role" "lambda_authorizer" {
  name = "${local.name_prefix}-lambda-authorizer-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-lambda-authorizer-role"
  }
}

# Authorizer only needs Clerk secret (for JWKS URL)
resource "aws_iam_role_policy" "lambda_authorizer_secrets" {
  name = "${local.name_prefix}-lambda-authorizer-secrets"
  role = aws_iam_role.lambda_authorizer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SecretsManagerRead"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.clerk.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_authorizer_logs" {
  role       = aws_iam_role.lambda_authorizer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# -----------------------------------------------------------------------------
# API Gateway Logging Role
# Used by: API Gateway to write access logs to CloudWatch
# -----------------------------------------------------------------------------

resource "aws_iam_role" "apigateway_logs" {
  name = "${local.name_prefix}-apigateway-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-apigateway-logs-role"
  }
}

resource "aws_iam_role_policy_attachment" "apigateway_logs" {
  role       = aws_iam_role.apigateway_logs.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# -----------------------------------------------------------------------------
# CloudFront Origin Access Control (for S3)
# -----------------------------------------------------------------------------

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.name_prefix}-frontend-oac"
  description                       = "OAC for frontend S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# S3 bucket policy allowing CloudFront OAC access
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAC"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}
