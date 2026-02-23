# =============================================================================
# DynamoDB - Single Table Design
# =============================================================================
#
# One table for all entities (User, Niche, Ad, Page, NichePage, CollectionRun).
# PK/SK + 2 GSIs cover all access patterns.
#
# Entity          | PK                      | SK
# ----------------+-------------------------+----------------------------
# User            | USER#<clerk_id>         | METADATA
# Niche           | USER#<user_id>          | NICHE#<niche_id>
# Ad              | NICHE#<niche_id>        | AD#<meta_ad_id>
# Page            | PAGE#<page_id>          | METADATA
# NichePage       | NICHE#<niche_id>        | PAGE#<page_id>
# CollectionRun   | NICHE#<niche_id>        | RUN#<timestamp>#<run_id>
#
# =============================================================================

resource "aws_dynamodb_table" "main" {
  name         = "${local.name_prefix}-table"
  billing_mode = "PAY_PER_REQUEST" # On-demand: $0 at low traffic, scales automatically
  hash_key     = "PK"
  range_key    = "SK"

  # Primary key attributes
  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # GSI1 attributes
  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  # GSI2 attributes
  attribute {
    name = "GSI2PK"
    type = "S"
  }

  attribute {
    name = "GSI2SK"
    type = "S"
  }

  # GSI1: Cross-entity lookups
  # - User by email:        GSI1PK=USER_EMAIL#<email>          GSI1SK=METADATA
  # - Niche by ID:          GSI1PK=NICHE#<niche_id>            GSI1SK=METADATA
  # - Ads by page in niche: GSI1PK=NICHE_PAGE#<niche_id>#<page_id>  GSI1SK=AD#<id>
  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  # GSI2: Slug lookups + Saved ads
  # - Niche by slug:  GSI2PK=USER_SLUG#<user_id>#<slug>  GSI2SK=METADATA
  # - Saved ads:      GSI2PK=NICHE_SAVED#<niche_id>      GSI2SK=<saved_at>#<ad_id>
  global_secondary_index {
    name            = "GSI2"
    hash_key        = "GSI2PK"
    range_key       = "GSI2SK"
    projection_type = "ALL"
  }

  # Point-in-time recovery (backup protection)
  point_in_time_recovery {
    enabled = var.dynamodb_pitr_enabled
  }

  # Server-side encryption (AWS-managed KMS key, free)
  server_side_encryption {
    enabled = true
  }

  # TTL attribute (optional, for future auto-cleanup of old collection runs)
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "${local.name_prefix}-table"
  }
}
