# =============================================================================
# Lambda Functions - Placeholder Stubs (Phase 1)
# =============================================================================
#
# These are placeholder functions (return 501) deployed in Phase 1 so that
# all infrastructure wiring (IAM, API Gateway, CloudWatch) can be validated.
# Real handlers are swapped in during Phase 3.
#
# Stub zips live in: ../lambda_stubs/*.zip
# Real handlers will live in: ../lambda_src/
#
# =============================================================================

locals {
  stubs_path = "${path.module}/../lambda_stubs"
  layers_path = "${path.module}/../lambda_layers"

  # Common environment variables injected into every Lambda.
  # Handler code reads:
  #   SECRETS_NAME      — logical name used for boto3 GetSecretValue calls (Clerk secret)
  #   DYNAMODB_TABLE    — table name for DynamoDB client
  #   LOG_LEVEL         — Python logging level
  common_env = {
    ENVIRONMENT  = var.environment
    DYNAMODB_TABLE = aws_dynamodb_table.main.name
    SECRETS_NAME = aws_secretsmanager_secret.clerk.name   # "metaads/dev/clerk"
    LOG_LEVEL    = var.environment == "dev" ? "DEBUG" : "INFO"
  }
}

# -----------------------------------------------------------------------------
# Shared Lambda Layer
# Contains all Python dependencies (PyJWT, boto3, requests, svix, etc.)
# -----------------------------------------------------------------------------

resource "aws_lambda_layer_version" "shared" {
  layer_name          = "${local.name_prefix}-shared-layer"
  description         = "Shared Python dependencies for all Lambda functions"
  filename            = "${local.stubs_path}/shared_layer.zip"
  source_code_hash    = filebase64sha256("${local.stubs_path}/shared_layer.zip")
  compatible_runtimes = [var.lambda_runtime]

  lifecycle {
    create_before_destroy = true
  }
}

# -----------------------------------------------------------------------------
# JWT Authorizer Lambda
# Validates Clerk JWT tokens for all protected routes
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "authorizer" {
  function_name = "${local.name_prefix}-authorizer"
  description   = "Clerk JWT authorizer for API Gateway"
  role          = aws_iam_role.lambda_authorizer.arn
  runtime       = var.lambda_runtime
  handler       = "handler.handler"
  timeout       = 10
  memory_size   = 128 # Authorizer needs minimal memory

  filename         = "${local.stubs_path}/authorizer.zip"
  source_code_hash = filebase64sha256("${local.stubs_path}/authorizer.zip")

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = merge(local.common_env, {
      ADMIN_USER_IDS = var.admin_user_ids
    })
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_authorizer,
    aws_iam_role_policy_attachment.lambda_authorizer_logs
  ]

  tags = {
    Name = "${local.name_prefix}-authorizer"
  }
}

# -----------------------------------------------------------------------------
# Auth Handler Lambda
# Routes: POST /api/auth/webhook, GET /api/auth/me
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "auth" {
  function_name = "${local.name_prefix}-auth"
  description   = "Clerk webhook handler + /auth/me endpoint"
  role          = aws_iam_role.lambda_api.arn
  runtime       = var.lambda_runtime
  handler       = "handler.handler"
  timeout       = var.lambda_timeout_api
  memory_size   = var.lambda_memory_mb

  filename         = "${local.stubs_path}/auth.zip"
  source_code_hash = filebase64sha256("${local.stubs_path}/auth.zip")

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = local.common_env
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_auth,
    aws_iam_role_policy_attachment.lambda_api_logs
  ]

  tags = {
    Name = "${local.name_prefix}-auth"
  }
}

# -----------------------------------------------------------------------------
# Niches Handler Lambda
# Routes: GET/POST/PATCH/DELETE /api/niches/*
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "niches" {
  function_name = "${local.name_prefix}-niches"
  description   = "Niches CRUD handler"
  role          = aws_iam_role.lambda_api.arn
  runtime       = var.lambda_runtime
  handler       = "handler.handler"
  timeout       = var.lambda_timeout_api
  memory_size   = var.lambda_memory_mb

  filename         = "${local.stubs_path}/niches.zip"
  source_code_hash = filebase64sha256("${local.stubs_path}/niches.zip")

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = local.common_env
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_niches,
    aws_iam_role_policy_attachment.lambda_api_logs
  ]

  tags = {
    Name = "${local.name_prefix}-niches"
  }
}

# -----------------------------------------------------------------------------
# Ads Handler Lambda
# Routes: GET /api/niches/{slug}/ads/*, POST /api/niches/{slug}/ads/clear
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "ads" {
  function_name = "${local.name_prefix}-ads"
  description   = "Ads search, detail, variants, related, clear handler"
  role          = aws_iam_role.lambda_api.arn
  runtime       = var.lambda_runtime
  handler       = "handler.handler"
  timeout       = var.lambda_timeout_api
  memory_size   = var.lambda_memory_mb

  filename         = "${local.stubs_path}/ads.zip"
  source_code_hash = filebase64sha256("${local.stubs_path}/ads.zip")

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = merge(local.common_env, {
      META_API_SECRETS_NAME = aws_secretsmanager_secret.meta_api.name
    })
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_ads,
    aws_iam_role_policy_attachment.lambda_api_logs
  ]

  tags = {
    Name = "${local.name_prefix}-ads"
  }
}

# -----------------------------------------------------------------------------
# Saved Handler Lambda
# Routes: GET/POST/PATCH/DELETE /api/niches/{slug}/saved + /ads/{id}/save
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "saved" {
  function_name = "${local.name_prefix}-saved"
  description   = "Saved ads handler"
  role          = aws_iam_role.lambda_api.arn
  runtime       = var.lambda_runtime
  handler       = "handler.handler"
  timeout       = var.lambda_timeout_api
  memory_size   = var.lambda_memory_mb

  filename         = "${local.stubs_path}/saved.zip"
  source_code_hash = filebase64sha256("${local.stubs_path}/saved.zip")

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = local.common_env
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_saved,
    aws_iam_role_policy_attachment.lambda_api_logs
  ]

  tags = {
    Name = "${local.name_prefix}-saved"
  }
}

# -----------------------------------------------------------------------------
# Collection Trigger Lambda
# Route: POST /api/niches/{slug}/collect
# Creates CollectionRun record, async-invokes worker, returns 202 immediately
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "collect_trigger" {
  function_name = "${local.name_prefix}-collect-trigger"
  description   = "Collection trigger: creates run, async-invokes worker, returns 202"
  role          = aws_iam_role.lambda_collector.arn
  runtime       = var.lambda_runtime
  handler       = "handler.handler"
  timeout       = var.lambda_timeout_api
  memory_size   = var.lambda_memory_mb

  filename         = "${local.stubs_path}/collect_trigger.zip"
  source_code_hash = filebase64sha256("${local.stubs_path}/collect_trigger.zip")

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = merge(local.common_env, {
      # Full ARN required: handler calls boto3 lambda.invoke(FunctionName=worker_arn)
      COLLECT_WORKER_ARN = aws_lambda_function.collect_worker.arn
    })
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_collect_trigger,
    aws_iam_role_policy_attachment.lambda_collector_logs
  ]

  tags = {
    Name = "${local.name_prefix}-collect-trigger"
  }
}

# -----------------------------------------------------------------------------
# Collection Worker Lambda
# Invoked async by trigger. Runs Meta API collection, up to 15 minutes.
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "collect_worker" {
  function_name = "${local.name_prefix}-collect-worker"
  description   = "Collection worker: calls Meta API, parses ads, writes to DynamoDB"
  role          = aws_iam_role.lambda_collector.arn
  runtime       = var.lambda_runtime
  handler       = "handler.handler"
  timeout       = var.lambda_timeout_collector # 900 seconds (15 min)
  memory_size   = 512                          # More memory for parsing large ad batches

  filename         = "${local.stubs_path}/collect_worker.zip"
  source_code_hash = filebase64sha256("${local.stubs_path}/collect_worker.zip")

  layers = [aws_lambda_layer_version.shared.arn]

  # Reserved concurrency: max 5 parallel collection jobs (protects Meta API rate limits)
  reserved_concurrent_executions = var.lambda_collector_concurrency

  environment {
    variables = merge(local.common_env, {
      # Override SECRETS_NAME for the worker: it needs the Meta API secret, not Clerk.
      # collect_worker/handler.py reads os.environ["SECRETS_NAME"] for boto3 GetSecretValue.
      SECRETS_NAME = aws_secretsmanager_secret.meta_api.name
    })
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_collect_worker,
    aws_iam_role_policy_attachment.lambda_collector_logs
  ]

  tags = {
    Name = "${local.name_prefix}-collect-worker"
  }
}

# -----------------------------------------------------------------------------
# Collection Scheduler Lambda
# Triggered by EventBridge Scheduler (cron every 3 hours).
# Lists opt-in niches, checks timing, fan-outs one collect_worker per keyword.
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "collect_scheduler" {
  function_name = "${local.name_prefix}-collect-scheduler"
  description   = "Periodic scheduler: scans opt-in niches, fans out collect_worker per keyword"
  role          = aws_iam_role.lambda_collector.arn
  runtime       = var.lambda_runtime
  handler       = "handler.handler"
  timeout       = 60   # Bounded: scan + N async invocations; well under 1 min
  memory_size   = 256

  filename         = "${local.stubs_path}/collect_scheduler.zip"
  source_code_hash = filebase64sha256("${local.stubs_path}/collect_scheduler.zip")

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = merge(local.common_env, {
      COLLECT_WORKER_ARN = aws_lambda_function.collect_worker.arn
    })
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_collect_scheduler,
    aws_iam_role_policy_attachment.lambda_collector_logs
  ]

  tags = {
    Name = "${local.name_prefix}-collect-scheduler"
  }
}

# -----------------------------------------------------------------------------
# Competitors Handler Lambda
# Routes: GET/POST/PATCH/DELETE /api/competitors + /api/competitors/{page_id}/ads
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "competitors" {
  function_name = "${local.name_prefix}-competitors"
  description   = "Competitors CRUD + live Meta Ad Library ad fetching"
  role          = aws_iam_role.lambda_api.arn
  runtime       = var.lambda_runtime
  handler       = "handler.handler"
  timeout       = 30   # Live Meta API calls can take up to ~20s
  memory_size   = var.lambda_memory_mb

  filename         = "${local.stubs_path}/competitors.zip"
  source_code_hash = filebase64sha256("${local.stubs_path}/competitors.zip")

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = merge(local.common_env, {
      META_API_SECRETS_NAME = aws_secretsmanager_secret.meta_api.name
    })
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_competitors,
    aws_iam_role_policy_attachment.lambda_api_logs
  ]

  tags = {
    Name = "${local.name_prefix}-competitors"
  }
}

# -----------------------------------------------------------------------------
# Step 5.4: Dead Letter Queue for collect_worker failed async invocations
#
# When collect_trigger invokes collect_worker with InvocationType="Event",
# Lambda retries the invocation twice on failure.  If all retries fail the
# event payload is sent to this SQS queue so nothing is silently lost.
#
# Architecture:
#   collect_trigger ─(async)─> collect_worker
#                                    │ (all retries exhausted)
#                                    └─(on_failure destination)─> SQS DLQ
#
# Visibility timeout = 6× Lambda timeout (AWS best practice for SQS DLQs).
# Max receive count = 1 (already failed 3× inside Lambda; one more chance
# in the queue then sent to the DLQ's own DLQ if needed, but for simplicity
# we just alert and let an operator replay manually).
# -----------------------------------------------------------------------------

resource "aws_sqs_queue" "collect_worker_dlq" {
  name                       = "${local.name_prefix}-collect-worker-dlq"
  message_retention_seconds  = 1209600  # 14 days
  visibility_timeout_seconds = 60       # Short – messages here are dead; just for inspection

  tags = {
    Name = "${local.name_prefix}-collect-worker-dlq"
  }
}

# Allow Lambda service to send messages to the DLQ (resource-based policy)
resource "aws_sqs_queue_policy" "collect_worker_dlq" {
  queue_url = aws_sqs_queue.collect_worker_dlq.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowLambdaServiceSendMessage"
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.collect_worker_dlq.arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" = aws_lambda_function.collect_worker.arn
          }
        }
      }
    ]
  })
}

# Async invocation config: route failed events to the SQS DLQ
# Lambda retries async invocations twice (maximum_retry_attempts = 2) before
# sending to the on_failure destination.
resource "aws_lambda_function_event_invoke_config" "collect_worker" {
  function_name                = aws_lambda_function.collect_worker.function_name
  maximum_retry_attempts       = 2    # default; explicit for clarity
  maximum_event_age_in_seconds = 3600 # discard stale events after 1 hour

  destination_config {
    on_failure {
      destination = aws_sqs_queue.collect_worker_dlq.arn
    }
  }
}
