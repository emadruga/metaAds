# =============================================================================
# EventBridge Scheduler — Periodic Collection
# =============================================================================
#
# Fires the collect_scheduler Lambda every 3 hours.
# The scheduler itself is intentionally simple: it delegates all business
# logic (opt-in check, timing check, fan-out) to the Lambda handler.
#
# Resources in this file:
#   aws_iam_role.eventbridge_scheduler          — role assumed by EventBridge Scheduler
#   aws_iam_role_policy.eventbridge_scheduler_invoke — allows InvokeFunction on scheduler Lambda
#   aws_scheduler_schedule.collect_scheduler    — the schedule itself
#
# EventBridge Scheduler requires a separate IAM role from the Lambda's own
# execution role: the *Scheduler service* assumes this role to call InvokeFunction,
# whereas the Lambda's lambda_collector role is assumed by the Lambda *runtime*.
# =============================================================================

# -----------------------------------------------------------------------------
# IAM Role — EventBridge Scheduler → collect_scheduler Lambda
# -----------------------------------------------------------------------------

resource "aws_iam_role" "eventbridge_scheduler" {
  name = "${local.name_prefix}-eventbridge-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-eventbridge-scheduler-role"
  }
}

resource "aws_iam_role_policy" "eventbridge_scheduler_invoke" {
  name = "${local.name_prefix}-eventbridge-scheduler-invoke"
  role = aws_iam_role.eventbridge_scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "InvokeCollectLambdas"
        Effect = "Allow"
        Action = ["lambda:InvokeFunction"]
        Resource = concat(
          [aws_lambda_function.collect_scheduler.arn],
          var.alarm_email != "" ? [aws_lambda_function.collect_daily_reporter[0].arn] : []
        )
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# EventBridge Scheduler — runs every 3 hours
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# EventBridge Scheduler — daily collection summary report (23:00 UTC = 20:00 BRT)
# Only created when alarm_email is set (same condition as the SNS topic and Lambda).
# -----------------------------------------------------------------------------

resource "aws_scheduler_schedule" "collect_daily_reporter" {
  count       = var.alarm_email != "" ? 1 : 0
  name        = "${local.name_prefix}-collect-daily-reporter"
  description = "Daily collection summary email — fires at 23:00 UTC (20:00 BRT)"
  group_name  = "default"

  # No jitter for the daily report — we want it at exactly 23:00 UTC.
  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(0 23 * * ? *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = aws_lambda_function.collect_daily_reporter[0].arn
    role_arn = aws_iam_role.eventbridge_scheduler.arn

    input = "{}"

    retry_policy {
      maximum_event_age_in_seconds = 300
      maximum_retry_attempts       = 1
    }
  }
}

# -----------------------------------------------------------------------------
# EventBridge Scheduler — runs every 3 hours
# -----------------------------------------------------------------------------

resource "aws_scheduler_schedule" "collect_scheduler" {
  name        = "${local.name_prefix}-collect-scheduler"
  description = "Periodic collection trigger — fires every 3 hours"
  group_name  = "default"

  # Flexible time window: allow up to 15 minutes of jitter so bursts of
  # schedules across accounts don't hammer the Meta API simultaneously.
  flexible_time_window {
    mode                      = "FLEXIBLE"
    maximum_window_in_minutes = 15
  }

  # Every 3 hours, year-round.  Uses EventBridge cron syntax (6-field, no TZ field):
  # cron(minutes hours day-of-month month day-of-week year)
  schedule_expression          = "cron(0 */3 * * ? *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = aws_lambda_function.collect_scheduler.arn
    role_arn = aws_iam_role.eventbridge_scheduler.arn

    # Empty input — scheduler Lambda reads all config from DynamoDB
    input = "{}"

    # Retry policy: if Lambda invocation fails (throttled, etc.), retry once
    # after 60 seconds.  After 2 total attempts, drop the event.
    retry_policy {
      maximum_event_age_in_seconds = 300  # Discard stale invocations after 5 min
      maximum_retry_attempts       = 1
    }
  }
}
