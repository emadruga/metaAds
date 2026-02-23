"""
Lambda Authorizer — Clerk JWT RS256 verification via JWKS.

This is a security upgrade over the original Flask middleware which decoded
JWTs WITHOUT signature verification (verify_signature: False).

Flow:
  1. Extract Bearer token from Authorization header
  2. Decode header to get `kid` (key ID)
  3. Fetch JWKS from Clerk (cached per Lambda warm invocation)
  4. Verify RS256 signature against matching public key
  5. Validate expiry + issuer
  6. Return IAM policy ALLOW with user_id in context

API Gateway HTTP API uses "simple responses" (enable_simple_responses=true),
so we return {"isAuthorized": bool, "context": {...}} instead of IAM policy docs.

Environment variables:
    CLERK_JWKS_URL   — e.g. https://clerk.your-app.dev/.well-known/jwks.json
                      (also stored in Secrets Manager; fetched at cold start)
    CLERK_ISSUER     — optional issuer check, e.g. https://clerk.your-app.dev
    SECRETS_NAME     — e.g. metaads/dev/clerk
    AWS_REGION       — injected automatically by Lambda runtime
"""

from __future__ import annotations

import json
import logging
import os
import time
from functools import lru_cache
from typing import Optional

import boto3
import jwt
from jwt import PyJWKClient, ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# JWKS client — module-level singleton, cached across warm invocations
# ---------------------------------------------------------------------------

_jwks_client: Optional[PyJWKClient] = None
_clerk_secrets: Optional[dict] = None


def _get_clerk_secrets() -> dict:
    """Fetch Clerk config from Secrets Manager (cached per cold start)."""
    global _clerk_secrets
    if _clerk_secrets is not None:
        return _clerk_secrets

    secret_name = os.environ.get("SECRETS_NAME", "metaads/dev/clerk")
    region = os.environ.get("AWS_REGION", "us-east-1")

    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    _clerk_secrets = json.loads(response["SecretString"])
    return _clerk_secrets


def _get_jwks_client() -> PyJWKClient:
    """Return (or create) the JWKS client singleton."""
    global _jwks_client
    if _jwks_client is not None:
        return _jwks_client

    # Try env var first (cheaper), fall back to Secrets Manager
    jwks_url = os.environ.get("CLERK_JWKS_URL")
    if not jwks_url:
        secrets = _get_clerk_secrets()
        jwks_url = secrets.get("jwks_url", "")

    if not jwks_url:
        raise RuntimeError("CLERK_JWKS_URL not configured")

    # cache_keys=True caches the JWKS response; lifespan controls key rotation
    _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    logger.info(f"JWKS client initialised for {jwks_url}")
    return _jwks_client


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

def _verify_jwt(token: str) -> Optional[dict]:
    """
    Verify a Clerk JWT using RS256 + JWKS.

    Returns the decoded payload dict on success, None on failure.
    Raises ExpiredSignatureError / InvalidTokenError on verifiable failures.
    """
    client = _get_jwks_client()
    signing_key = client.get_signing_key_from_jwt(token)

    # Optionally enforce issuer
    issuer = os.environ.get("CLERK_ISSUER")
    options = {"require": ["exp", "sub"]}
    decode_kwargs: dict = {
        "algorithms": ["RS256"],
        "options": options,
    }
    if issuer:
        decode_kwargs["issuer"] = issuer

    payload = jwt.decode(
        token,
        signing_key.key,
        **decode_kwargs,
    )
    return payload


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

def handler(event: dict, context) -> dict:
    """
    Lambda Authorizer handler (HTTP API simple response format).

    API Gateway passes the full request event; we read the Authorization header.

    Returns:
        {"isAuthorized": True/False, "context": {"user_id": "..."}}
    """
    logger.debug("Authorizer invoked")

    # Extract token from Authorization: Bearer <token>
    headers = event.get("headers") or {}
    auth_header = headers.get("authorization") or headers.get("Authorization", "")

    if not auth_header.lower().startswith("bearer "):
        logger.info("Missing or malformed Authorization header")
        return _deny()

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return _deny()

    try:
        payload = _verify_jwt(token)
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("JWT missing 'sub' claim")
            return _deny()

        logger.info(f"Authorizer ALLOW for user={user_id}")
        return {
            "isAuthorized": True,
            "context": {
                "user_id": user_id,
                "session_id": payload.get("sid", ""),
            },
        }

    except ExpiredSignatureError:
        logger.info("JWT expired")
        return _deny()
    except InvalidTokenError as exc:
        logger.warning(f"JWT invalid: {exc}")
        return _deny()
    except Exception as exc:
        logger.error(f"Authorizer error: {exc}", exc_info=True)
        return _deny()


def _deny() -> dict:
    return {"isAuthorized": False, "context": {}}
