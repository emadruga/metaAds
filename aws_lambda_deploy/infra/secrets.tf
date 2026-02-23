# =============================================================================
# Secrets Manager
# =============================================================================
#
# Stores sensitive configuration that Lambda functions retrieve at runtime.
# Cost: $0.40/secret/month = $0.80 total for 2 secrets.
#
# Secrets are created with placeholder values. Actual values must be set
# manually via AWS Console or CLI after terraform apply:
#
#   aws secretsmanager put-secret-value \
#     --secret-id metaads/dev/meta-api \
#     --secret-string '{"access_token":"YOUR_TOKEN"}' \
#     --profile metads
#
# =============================================================================

# Meta API credentials (Facebook access token)
resource "aws_secretsmanager_secret" "meta_api" {
  name                    = "${var.project_name}/${var.environment}/meta-api"
  description             = "Meta Ad Library API credentials"
  recovery_window_in_days = var.environment == "dev" ? 0 : 30

  tags = {
    Name = "${local.name_prefix}-meta-api-secret"
  }
}

# Placeholder value - must be updated manually
resource "aws_secretsmanager_secret_version" "meta_api" {
  secret_id = aws_secretsmanager_secret.meta_api.id
  secret_string = jsonencode({
    access_token = "PLACEHOLDER_UPDATE_VIA_CLI"
  })

  lifecycle {
    ignore_changes = [secret_string] # Don't overwrite after manual update
  }
}

# Clerk authentication keys
resource "aws_secretsmanager_secret" "clerk" {
  name                    = "${var.project_name}/${var.environment}/clerk"
  description             = "Clerk authentication keys and webhook secret"
  recovery_window_in_days = var.environment == "dev" ? 0 : 30

  tags = {
    Name = "${local.name_prefix}-clerk-secret"
  }
}

# Placeholder value - must be updated manually
resource "aws_secretsmanager_secret_version" "clerk" {
  secret_id = aws_secretsmanager_secret.clerk.id
  secret_string = jsonencode({
    publishable_key = "PLACEHOLDER_UPDATE_VIA_CLI"
    secret_key      = "PLACEHOLDER_UPDATE_VIA_CLI"
    webhook_secret  = "PLACEHOLDER_UPDATE_VIA_CLI"
    jwks_url        = "PLACEHOLDER_UPDATE_VIA_CLI"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
