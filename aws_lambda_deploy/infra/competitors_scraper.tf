# =============================================================================
# Competitors Scraper — Playwright Lambda (Container Image)
#
# Playwright + Chromium exceed the 250 MB ZIP Lambda limit, so this function
# runs as a container image stored in ECR.
#
# Invocation: async (InvocationType=Event) from the competitors Lambda
#             whenever Graph API returns < 5 results or all-inactive ads.
# Result:     written directly to DynamoDB (SCRAPE_CACHE#<page_id> / DATA)
#             with a 4-hour TTL.
#
# Deploy flow:
#   1. `bash scripts/build_scraper_image.sh`  — builds & pushes to ECR
#   2. `terraform apply`                       — updates image_uri if changed
# =============================================================================

# ---------------------------------------------------------------------------
# ECR Repository
# ---------------------------------------------------------------------------

resource "aws_ecr_repository" "competitors_scraper" {
  name                 = "${local.name_prefix}-competitors-scraper"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = {
    Name = "${local.name_prefix}-competitors-scraper"
  }
}

resource "aws_ecr_lifecycle_policy" "competitors_scraper" {
  repository = aws_ecr_repository.competitors_scraper.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = { type = "expire" }
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# Dead-Letter Queue for failed async invocations
# ---------------------------------------------------------------------------

resource "aws_sqs_queue" "scraper_dlq" {
  name                      = "${local.name_prefix}-scraper-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Name = "${local.name_prefix}-scraper-dlq"
  }
}

# ---------------------------------------------------------------------------
# IAM Role for the scraper Lambda
# Needs: DynamoDB write (to store cache) + CloudWatch Logs
# ---------------------------------------------------------------------------

resource "aws_iam_role" "lambda_scraper" {
  name = "${local.name_prefix}-lambda-scraper-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-lambda-scraper-role"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_scraper_logs" {
  role       = aws_iam_role.lambda_scraper.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_scraper_dynamodb" {
  name = "${local.name_prefix}-lambda-scraper-dynamodb"
  role = aws_iam_role.lambda_scraper.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBCacheWrite"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
        ]
        Resource = [
          aws_dynamodb_table.main.arn,
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_scraper_sqs_dlq" {
  name = "${local.name_prefix}-lambda-scraper-sqs-dlq"
  role = aws_iam_role.lambda_scraper.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = [aws_sqs_queue.scraper_dlq.arn]
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# CloudWatch Log Group
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "lambda_scraper" {
  name              = "/aws/lambda/${local.name_prefix}-competitors-scraper"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-competitors-scraper-logs"
  }
}

# ---------------------------------------------------------------------------
# Lambda Function (container image)
#
# image_uri references ECR. On first `terraform apply` the ECR repo is empty
# so Terraform will fail — run build_scraper_image.sh first.
# Use `lifecycle { ignore_changes = [image_uri] }` so the function isn't
# force-replaced every time image_uri changes; the build script handles
# updating the image, and you can trigger a new deployment with:
#   aws lambda update-function-code --image-uri <new-uri> ...
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "competitors_scraper" {
  function_name = "${local.name_prefix}-competitors-scraper"
  description   = "Playwright fallback scraper for competitor ads (container image)"
  role          = aws_iam_role.lambda_scraper.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.competitors_scraper.repository_url}:latest"

  # Chromium needs generous memory and time
  timeout     = 300  # 5 minutes — Playwright + full scroll can take 2-3 min
  memory_size = 2048 # 2 GB — Chromium needs ~1.5 GB minimum

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.main.name
      LOG_LEVEL      = var.environment == "dev" ? "DEBUG" : "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_scraper,
    aws_iam_role_policy_attachment.lambda_scraper_logs,
  ]

  lifecycle {
    # image_uri is managed outside Terraform (build_scraper_image.sh).
    # Terraform only creates / recreates the function; image updates are
    # applied via `aws lambda update-function-code`.
    ignore_changes = [image_uri]
  }

  tags = {
    Name = "${local.name_prefix}-competitors-scraper"
  }
}

# Async invocation config: no retries (scraper is idempotent; caller retries
# on next cache miss), failed invocations go to SQS DLQ for inspection.
resource "aws_lambda_function_event_invoke_config" "competitors_scraper" {
  function_name          = aws_lambda_function.competitors_scraper.function_name
  maximum_retry_attempts = 0

  destination_config {
    on_failure {
      destination = aws_sqs_queue.scraper_dlq.arn
    }
  }
}

# ---------------------------------------------------------------------------
# Allow the competitors API Lambda to invoke the scraper asynchronously
# ---------------------------------------------------------------------------

resource "aws_iam_role_policy" "lambda_api_invoke_scraper" {
  name = "${local.name_prefix}-lambda-api-invoke-scraper"
  role = aws_iam_role.lambda_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "InvokeScraperLambda"
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = [aws_lambda_function.competitors_scraper.arn]
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "scraper_ecr_repository_url" {
  description = "ECR repo URL for the competitors scraper image"
  value       = aws_ecr_repository.competitors_scraper.repository_url
}

output "scraper_lambda_arn" {
  description = "ARN of the competitors scraper Lambda"
  value       = aws_lambda_function.competitors_scraper.arn
}

output "scraper_dlq_url" {
  description = "SQS DLQ URL for failed scraper invocations"
  value       = aws_sqs_queue.scraper_dlq.url
}
