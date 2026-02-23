"""
Auth Lambda handler — Clerk webhook sync + /me endpoint.

Routes (HTTP API v2 payload format 2.0):
    POST  /api/auth/webhook   — NO authorizer — Clerk user.created/updated/deleted
    GET   /api/auth/me        — authorizer required — return current user

Svix webhook verification replaces the original Flask hmac.new() approach
(which used hmac.new() — a typo for hmac.new; Svix is the correct library
for Clerk webhook signatures).

Environment variables:
    DYNAMODB_TABLE   — DynamoDB table name
    SECRETS_NAME     — Secrets Manager secret for Clerk keys
    AWS_REGION       — injected by Lambda runtime
"""

from __future__ import annotations

import json
import logging
import os

import boto3
from svix.webhooks import Webhook, WebhookVerificationError

from app.dynamodb.user_repo import UserRepo
from app.dynamodb.models import User
from app.utils.ids import now_iso8601, generate_uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Secrets (cached across warm invocations)
# ---------------------------------------------------------------------------

_secrets: dict | None = None


def _get_secrets() -> dict:
    global _secrets
    if _secrets is not None:
        return _secrets
    secret_name = os.environ.get("SECRETS_NAME", "metaads/dev/clerk")
    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("secretsmanager", region_name=region)
    resp = client.get_secret_value(SecretId=secret_name)
    _secrets = json.loads(resp["SecretString"])
    return _secrets


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _get_user_id(event: dict) -> str | None:
    """Extract user_id injected by the Lambda authorizer."""
    ctx = (
        event.get("requestContext", {})
             .get("authorizer", {})
             .get("lambda", {})
    )
    return ctx.get("user_id")


def _get_primary_email(user_data: dict) -> str | None:
    emails = user_data.get("email_addresses", [])
    primary_id = user_data.get("primary_email_address_id")
    for e in emails:
        if e.get("id") == primary_id:
            return e.get("email_address")
    if emails:
        return emails[0].get("email_address")
    return None


# ---------------------------------------------------------------------------
# Webhook event handlers
# ---------------------------------------------------------------------------

def _handle_user_created(user_data: dict) -> None:
    email = _get_primary_email(user_data)
    if not email:
        logger.error("user.created: no email in payload")
        return

    user = User(
        id=user_data["id"],
        email=email,
        first_name=user_data.get("first_name") or "",
        last_name=user_data.get("last_name") or "",
        image_url=user_data.get("image_url") or "",
        is_active=True,
        created_at=now_iso8601(),
        updated_at=now_iso8601(),
    )
    UserRepo.create_or_update(user)
    logger.info(f"user.created: {email}")


def _handle_user_updated(user_data: dict) -> None:
    user_id = user_data["id"]
    existing = UserRepo.get(user_id)
    if not existing:
        _handle_user_created(user_data)
        return

    email = _get_primary_email(user_data)
    UserRepo.update(
        user_id,
        email=email or existing.email,
        first_name=user_data.get("first_name") or existing.first_name,
        last_name=user_data.get("last_name") or existing.last_name,
        image_url=user_data.get("image_url") or existing.image_url,
    )
    logger.info(f"user.updated: {user_id}")


def _handle_user_deleted(user_data: dict) -> None:
    user_id = user_data["id"]
    existing = UserRepo.get(user_id)
    if existing:
        UserRepo.deactivate(user_id)
        logger.info(f"user.deleted: {user_id}")


# ---------------------------------------------------------------------------
# Route: POST /api/auth/webhook
# ---------------------------------------------------------------------------

def _webhook(event: dict) -> dict:
    """Verify Svix signature and process Clerk user lifecycle events."""
    body_raw = event.get("body", "") or ""

    # Svix requires the raw bytes and the original headers
    try:
        secrets = _get_secrets()
        webhook_secret = secrets.get("webhook_secret", "")
    except Exception as exc:
        logger.error(f"Failed to load webhook secret: {exc}")
        return _response(500, {"error": "Server configuration error"})

    if not webhook_secret:
        logger.warning("CLERK_WEBHOOK_SECRET not configured — skipping verification")
    else:
        headers = event.get("headers") or {}
        try:
            wh = Webhook(webhook_secret)
            wh.verify(body_raw.encode() if isinstance(body_raw, str) else body_raw, headers)
        except WebhookVerificationError as exc:
            logger.warning(f"Webhook signature invalid: {exc}")
            return _response(401, {"error": "Invalid signature"})

    try:
        evt = json.loads(body_raw)
        event_type = evt.get("type")
        user_data = evt.get("data", {})
        logger.info(f"Clerk webhook: {event_type}")

        if event_type == "user.created":
            _handle_user_created(user_data)
        elif event_type == "user.updated":
            _handle_user_updated(user_data)
        elif event_type == "user.deleted":
            _handle_user_deleted(user_data)
        else:
            logger.info(f"Unhandled webhook event: {event_type}")

        return _response(200, {"received": True})

    except Exception as exc:
        logger.error(f"Webhook processing error: {exc}", exc_info=True)
        return _response(500, {"error": str(exc)})


# ---------------------------------------------------------------------------
# Route: GET /api/auth/me
# ---------------------------------------------------------------------------

def _me(event: dict) -> dict:
    """Return current authenticated user, creating placeholder if missing."""
    user_id = _get_user_id(event)
    if not user_id:
        return _response(401, {"success": False, "error": "Not authenticated"})

    user = UserRepo.get(user_id)

    if not user:
        # Clerk webhook hasn't fired yet; create placeholder
        logger.info(f"Creating placeholder user: {user_id}")
        placeholder = User(
            id=user_id,
            email=f"{user_id}@placeholder.metads.com",
            first_name="",
            last_name="",
            image_url="",
            is_active=True,
            created_at=now_iso8601(),
            updated_at=now_iso8601(),
        )
        UserRepo.create_or_update(placeholder)
        user = placeholder

    if not user.is_active:
        return _response(403, {"success": False, "error": "User account is deactivated"})

    return _response(200, {"success": True, "data": user.to_dict()})


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

def handler(event: dict, context) -> dict:
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    raw_path = event.get("rawPath", "")

    if raw_path.endswith("/webhook") and method == "POST":
        return _webhook(event)
    elif raw_path.endswith("/me") and method == "GET":
        return _me(event)
    else:
        return _response(404, {"error": "Not found"})
