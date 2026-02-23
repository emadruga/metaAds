# =============================================================================
# CloudFront Distribution
# =============================================================================
#
# Serves the Vue 3 SPA from S3 via HTTPS.
# - OAC (Origin Access Control) for secure S3 access
# - SPA routing: 403/404 errors redirect to /index.html
# - Cache: immutable hashed assets cached 1 year, index.html cached 5 min
# - TLS 1.2+ enforced
# - PriceClass_100: US + Canada + Europe only (cheapest)
#
# =============================================================================

# Response headers policy for security headers
resource "aws_cloudfront_response_headers_policy" "security_headers" {
  name = "${local.name_prefix}-security-headers"

  security_headers_config {
    # Prevent clickjacking
    frame_options {
      frame_option = "DENY"
      override     = true
    }

    # Prevent MIME type sniffing
    content_type_options {
      override = true
    }

    # Enable XSS protection
    xss_protection {
      mode_block = true
      protection = true
      override   = true
    }

    # Strict Transport Security (HSTS)
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    # Referrer policy
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
  }
}

# Cache policy for static assets (hashed filenames)
resource "aws_cloudfront_cache_policy" "static_assets" {
  name        = "${local.name_prefix}-static-assets"
  min_ttl     = 0
  default_ttl = 86400    # 1 day
  max_ttl     = 31536000 # 1 year

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }

    enable_accept_encoding_gzip   = true
    enable_accept_encoding_brotli = true
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = var.cloudfront_price_class
  comment             = "${local.name_prefix} frontend distribution"

  # S3 Origin with OAC
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # Default cache behavior (index.html and non-hashed files)
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "s3-frontend"

    # Short cache for index.html (allows quick updates)
    min_ttl     = 0
    default_ttl = 300  # 5 minutes
    max_ttl     = 300  # 5 minutes

    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    compress                   = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Cache behavior for hashed assets (/assets/*)
  ordered_cache_behavior {
    path_pattern     = "/assets/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "s3-frontend"

    cache_policy_id            = aws_cloudfront_cache_policy.static_assets.id
    viewer_protocol_policy     = "redirect-to-https"
    compress                   = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # SPA routing: serve index.html for all 403/404 errors
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  # Geo restriction: none (serve globally within price class)
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL/TLS: Use CloudFront default cert (*.cloudfront.net)
  # Custom domain + ACM cert can be added later
  viewer_certificate {
    cloudfront_default_certificate = var.custom_domain == "" ? true : false
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  tags = {
    Name = "${local.name_prefix}-frontend-cdn"
  }
}
