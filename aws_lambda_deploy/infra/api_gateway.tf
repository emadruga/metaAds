# =============================================================================
# API Gateway HTTP API v2
# =============================================================================
#
# HTTP API (v2) is ~70% cheaper than REST API:
#   REST API: $3.50/million requests
#   HTTP API: $1.00/million requests
#
# Route structure:
#   POST   /api/auth/webhook              -> auth Lambda (no authorizer)
#   GET    /api/auth/me                   -> auth Lambda (authorizer)
#   GET    /api/niches                    -> niches Lambda
#   POST   /api/niches                    -> niches Lambda
#   GET    /api/niches/{slug}             -> niches Lambda
#   PATCH  /api/niches/{slug}             -> niches Lambda
#   DELETE /api/niches/{slug}             -> niches Lambda
#   GET    /api/niches/{slug}/stats       -> niches Lambda
#   POST   /api/niches/{slug}/collect     -> collect_trigger Lambda
#   GET    /api/niches/{slug}/collection-runs/{run_id} -> niches Lambda
#   GET    /api/niches/{slug}/ads         -> ads Lambda
#   GET    /api/niches/{slug}/ads/{id}    -> ads Lambda
#   GET    /api/niches/{slug}/ads/{id}/related -> ads Lambda
#   GET    /api/niches/{slug}/ads/{id}/variants -> ads Lambda
#   POST   /api/niches/{slug}/ads/clear   -> ads Lambda
#   PATCH  /api/niches/{slug}/ads/{id}/save -> saved Lambda
#   GET    /api/niches/{slug}/saved       -> saved Lambda
#   GET    /api/health                    -> inline response (no Lambda)
#
# =============================================================================

# -----------------------------------------------------------------------------
# HTTP API
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_api" "main" {
  name          = "${local.name_prefix}-api"
  protocol_type = "HTTP"
  description   = "MetaAds serverless API"

  cors_configuration {
    allow_headers = [
      "Content-Type",
      "Authorization",
      "X-Amz-Date",
      "X-Api-Key",
      "svix-id",
      "svix-signature",
      "svix-timestamp"
    ]
    allow_methods = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    # Locked to the CloudFront origin so browsers block cross-origin requests
    # from any other domain.  Set via tfvars:
    #   dev.tfvars:  cors_allow_origins = ["https://<dist>.cloudfront.net"]
    #   prod.tfvars: cors_allow_origins = ["https://yourdomain.com"]
    # Populated after first terraform apply (outputs cloudfront_domain_name).
    allow_origins = var.cors_allow_origins
    max_age       = 300
  }

  tags = {
    Name = "${local.name_prefix}-api"
  }
}

# -----------------------------------------------------------------------------
# Default Stage (auto-deploy on changes)
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  # Throttling: prevents runaway costs from abuse
  default_route_settings {
    throttling_burst_limit = var.api_throttle_burst
    throttling_rate_limit  = var.api_throttle_rate
  }

  # Access logging to CloudWatch
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      sourceIp       = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      errorMessage   = "$context.error.message"
      userAgent      = "$context.identity.userAgent"
    })
  }

  tags = {
    Name = "${local.name_prefix}-api-stage"
  }
}

# -----------------------------------------------------------------------------
# Lambda Authorizer (Clerk JWT)
# Caches auth decisions for 5 minutes to reduce invocations
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "REQUEST"
  name             = "${local.name_prefix}-jwt-authorizer"
  authorizer_uri   = aws_lambda_function.authorizer.invoke_arn
  identity_sources = ["$request.header.Authorization"]

  # Cache authorizer results for 5 minutes (reduces Lambda invocations)
  authorizer_payload_format_version = "2.0"
  enable_simple_responses           = true
  authorizer_result_ttl_in_seconds  = 300
}

# Permission for API Gateway to invoke the authorizer Lambda
resource "aws_lambda_permission" "authorizer" {
  statement_id  = "AllowAPIGatewayInvokeAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*"
}

# -----------------------------------------------------------------------------
# Lambda Integrations (payload format 2.0 for HTTP API)
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_integration" "auth" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.auth.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "niches" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.niches.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "ads" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.ads.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "saved" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.saved.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "collect_trigger" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.collect_trigger.invoke_arn
  payload_format_version = "2.0"
}

# -----------------------------------------------------------------------------
# Lambda invoke permissions for API Gateway
# -----------------------------------------------------------------------------

resource "aws_lambda_permission" "auth" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*"
}

resource "aws_lambda_permission" "niches" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.niches.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*"
}

resource "aws_lambda_permission" "ads" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ads.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*"
}

resource "aws_lambda_permission" "saved" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.saved.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*"
}

resource "aws_lambda_permission" "collect_trigger" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.collect_trigger.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*"
}

# -----------------------------------------------------------------------------
# Routes: Auth
# -----------------------------------------------------------------------------

# Clerk webhook - NO authorizer (Svix signature verified inside handler)
resource "aws_apigatewayv2_route" "auth_webhook" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/auth/webhook"
  target    = "integrations/${aws_apigatewayv2_integration.auth.id}"
}

# Auth/me - requires JWT
resource "aws_apigatewayv2_route" "auth_me" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/auth/me"
  target             = "integrations/${aws_apigatewayv2_integration.auth.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

# -----------------------------------------------------------------------------
# Routes: Niches
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_route" "niches_list" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "niches_create" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "POST /api/niches"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "niches_get" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches/{slug}"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "niches_update" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "PATCH /api/niches/{slug}"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "niches_delete" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "DELETE /api/niches/{slug}"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "niches_stats" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches/{slug}/stats"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "niches_collection_runs_list" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches/{slug}/collection-runs"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "niches_collection_run_status" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches/{slug}/collection-runs/{run_id}"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

# -----------------------------------------------------------------------------
# Routes: Admin endpoints (collection health, global history, rate limits)
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_route" "collection_health" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/admin/collection/health"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "admin_global_history" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/admin/global-history"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "admin_rate_limit_history" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/admin/rate-limit/history"
  target             = "integrations/${aws_apigatewayv2_integration.niches.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

# -----------------------------------------------------------------------------
# Routes: Collection
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_route" "collect" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "POST /api/niches/{slug}/collect"
  target             = "integrations/${aws_apigatewayv2_integration.collect_trigger.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

# -----------------------------------------------------------------------------
# Routes: Ads
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_route" "ads_search" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches/{slug}/ads/search"
  target             = "integrations/${aws_apigatewayv2_integration.ads.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "ads_detail" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches/{slug}/ads/{ad_id}"
  target             = "integrations/${aws_apigatewayv2_integration.ads.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "ads_related" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches/{slug}/ads/{ad_id}/related"
  target             = "integrations/${aws_apigatewayv2_integration.ads.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "ads_variants" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches/{slug}/ads/{ad_id}/variants/analysis"
  target             = "integrations/${aws_apigatewayv2_integration.ads.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "ads_pages" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches/{slug}/pages"
  target             = "integrations/${aws_apigatewayv2_integration.ads.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "ads_clear" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "DELETE /api/niches/{slug}/ads/clear"
  target             = "integrations/${aws_apigatewayv2_integration.ads.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

# -----------------------------------------------------------------------------
# Routes: Saved
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_route" "saved_list" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /api/niches/{slug}/saved"
  target             = "integrations/${aws_apigatewayv2_integration.saved.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "saved_save" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "POST /api/niches/{slug}/ads/{ad_id}/save"
  target             = "integrations/${aws_apigatewayv2_integration.saved.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "saved_unsave" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "DELETE /api/niches/{slug}/ads/{ad_id}/save"
  target             = "integrations/${aws_apigatewayv2_integration.saved.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_route" "saved_update" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "PATCH /api/niches/{slug}/ads/{ad_id}/save"
  target             = "integrations/${aws_apigatewayv2_integration.saved.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

# -----------------------------------------------------------------------------
# Outputs specific to API Gateway (also in outputs.tf)
# -----------------------------------------------------------------------------

output "api_gateway_url" {
  description = "API Gateway HTTP API endpoint URL"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.main.id
}
