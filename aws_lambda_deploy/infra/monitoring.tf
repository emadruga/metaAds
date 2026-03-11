# =============================================================================
# CloudWatch Monitoring & Alarms
# =============================================================================
#
# Log groups for all Lambda functions + API Gateway.
# Alarms for errors, throttling, and collection failures.
# Optional SNS topic for email alerts.
#
# =============================================================================

# -----------------------------------------------------------------------------
# Log Groups (created upfront so Lambda doesn't auto-create with infinite retention)
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "lambda_auth" {
  name              = "/aws/lambda/${local.name_prefix}-auth"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-auth-logs"
  }
}

resource "aws_cloudwatch_log_group" "lambda_niches" {
  name              = "/aws/lambda/${local.name_prefix}-niches"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-niches-logs"
  }
}

resource "aws_cloudwatch_log_group" "lambda_ads" {
  name              = "/aws/lambda/${local.name_prefix}-ads"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-ads-logs"
  }
}

resource "aws_cloudwatch_log_group" "lambda_saved" {
  name              = "/aws/lambda/${local.name_prefix}-saved"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-saved-logs"
  }
}

resource "aws_cloudwatch_log_group" "lambda_collect_trigger" {
  name              = "/aws/lambda/${local.name_prefix}-collect-trigger"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-collect-trigger-logs"
  }
}

resource "aws_cloudwatch_log_group" "lambda_collect_worker" {
  name              = "/aws/lambda/${local.name_prefix}-collect-worker"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-collect-worker-logs"
  }
}

resource "aws_cloudwatch_log_group" "lambda_collect_scheduler" {
  name              = "/aws/lambda/${local.name_prefix}-collect-scheduler"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-collect-scheduler-logs"
  }
}

resource "aws_cloudwatch_log_group" "lambda_competitors" {
  name              = "/aws/lambda/${local.name_prefix}-competitors"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-competitors-logs"
  }
}

resource "aws_cloudwatch_log_group" "lambda_authorizer" {
  name              = "/aws/lambda/${local.name_prefix}-authorizer"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-authorizer-logs"
  }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${local.name_prefix}-api"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${local.name_prefix}-apigateway-logs"
  }
}

# -----------------------------------------------------------------------------
# SNS Topic for Alarm Notifications (optional)
# -----------------------------------------------------------------------------

resource "aws_sns_topic" "alarms" {
  count = var.alarm_email != "" ? 1 : 0
  name  = "${local.name_prefix}-alarms"

  tags = {
    Name = "${local.name_prefix}-alarms"
  }
}

resource "aws_sns_topic_subscription" "alarm_email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms[0].arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms
# -----------------------------------------------------------------------------

# Alarm: DynamoDB read throttling (should never happen with on-demand)
resource "aws_cloudwatch_metric_alarm" "dynamodb_read_throttle" {
  alarm_name          = "${local.name_prefix}-dynamodb-read-throttle"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ReadThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "DynamoDB read throttling detected - should not happen with on-demand billing"

  dimensions = {
    TableName = aws_dynamodb_table.main.name
  }

  alarm_actions = var.alarm_email != "" ? [aws_sns_topic.alarms[0].arn] : []

  tags = {
    Name = "${local.name_prefix}-dynamodb-read-throttle-alarm"
  }
}

# -----------------------------------------------------------------------------
# Step 5.4: Alarms for collect_worker failures (async invocation)
# -----------------------------------------------------------------------------

# Alarm: collect_worker Lambda errors (handler threw unhandled exception)
# Fires as soon as a single error is recorded in a 5-minute window.
resource "aws_cloudwatch_metric_alarm" "collect_worker_errors" {
  alarm_name          = "${local.name_prefix}-collect-worker-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "collect_worker Lambda threw an unhandled exception"

  dimensions = {
    FunctionName = aws_lambda_function.collect_worker.function_name
  }

  alarm_actions = var.alarm_email != "" ? [aws_sns_topic.alarms[0].arn] : []

  tags = {
    Name = "${local.name_prefix}-collect-worker-errors-alarm"
  }
}

# Alarm: messages arriving in the collect_worker DLQ.
# Any message in the DLQ means all Lambda retries were exhausted — operator
# attention required (check CloudWatch Logs, replay or discard the message).
resource "aws_cloudwatch_metric_alarm" "collect_worker_dlq_depth" {
  alarm_name          = "${local.name_prefix}-collect-worker-dlq-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "collect_worker DLQ has messages — all Lambda retries exhausted for at least one collection job"

  dimensions = {
    QueueName = aws_sqs_queue.collect_worker_dlq.name
  }

  alarm_actions = var.alarm_email != "" ? [aws_sns_topic.alarms[0].arn] : []

  tags = {
    Name = "${local.name_prefix}-collect-worker-dlq-alarm"
  }
}

# Alarm: DynamoDB write throttling
resource "aws_cloudwatch_metric_alarm" "dynamodb_write_throttle" {
  alarm_name          = "${local.name_prefix}-dynamodb-write-throttle"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "WriteThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "DynamoDB write throttling detected"

  dimensions = {
    TableName = aws_dynamodb_table.main.name
  }

  alarm_actions = var.alarm_email != "" ? [aws_sns_topic.alarms[0].arn] : []

  tags = {
    Name = "${local.name_prefix}-dynamodb-write-throttle-alarm"
  }
}
