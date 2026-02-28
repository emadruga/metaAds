"""
Collect Trigger Lambda handler.

This handler is intentionally thin — it only validates the request,
creates a CollectionRun record, and async-invokes the collect_worker.

It is kept separate from niches_handler so it can have its own IAM role
(needs Lambda:InvokeFunction permission that api handlers do not need).

Route (HTTP API v2):
    POST /api/niches/{slug}/collect

NOTE: The niches_handler also registers this route key and delegates here
via the same route in API Gateway; both Lambdas share the same route key.
In practice, API Gateway is configured to point this route to THIS function.

Environment variables:
    DYNAMODB_TABLE       — DynamoDB table name
    COLLECT_WORKER_ARN   — ARN of the collect_worker Lambda
    AWS_REGION           — injected by Lambda runtime
"""

from __future__ import annotations

import json
import logging
import os

import boto3

from app.dynamodb.niche_repo import NicheRepo
from app.dynamodb.collection_repo import CollectionRepo
from app.dynamodb.models import CollectionRun
from app.utils.ids import generate_uuid, now_iso8601

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }


def _get_user_id(event: dict) -> str | None:
    return (
        event.get("requestContext", {})
             .get("authorizer", {})
             .get("lambda", {})
             .get("user_id")
    )


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

def handler(event: dict, context) -> dict:
    """
    1. Validate request
    2. Create CollectionRun (status=pending)
    3. Async-invoke collect_worker
    4. Return 202 immediately
    """
    user_id = _get_user_id(event)
    path_params = event.get("pathParameters") or {}
    slug = path_params.get("slug", "")

    body_raw = event.get("body") or "{}"
    try:
        data = json.loads(body_raw)
    except (json.JSONDecodeError, TypeError):
        data = {}

    # Verify niche ownership
    niche = NicheRepo.get_by_slug(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    # Determine keyword
    keyword = data.get("keyword")
    if not keyword and niche.keywords:
        keyword = niche.keywords[0]

    if not keyword:
        return _response(400, {"success": False, "error": "No keyword specified and niche has no keywords"})

    # Create pending run record
    run_id = generate_uuid()
    started_at = now_iso8601()
    limit = int(data.get("limit", 50))
    run = CollectionRun(
        id=run_id,
        niche_id=niche.id,
        status="pending",
        keywords_used=[keyword],
        ads_found=0,
        ads_new=0,
        ads_updated=0,
        limit_requested=limit,
        countries=niche.countries or ["US"],
        error_message=None,
        started_at=started_at,
        completed_at=None,
    )
    CollectionRepo.create(run)
    logger.info(f"CollectionRun created: run_id={run_id} niche={niche.id} keyword={keyword!r}")

    # Async invoke worker
    worker_arn = os.environ.get("COLLECT_WORKER_ARN")
    if not worker_arn:
        logger.error("COLLECT_WORKER_ARN environment variable not set")
        CollectionRepo.mark_error(niche.id, run_id, started_at, "Worker Lambda ARN not configured")
        return _response(500, {"success": False, "error": "Collection worker not configured"})

    payload = {
        "niche_id": niche.id,
        "run_id": run_id,
        "started_at": started_at,
        "keyword": keyword,
        "limit": limit,
        "countries": niche.countries or ["US"],
        "platforms": niche.platforms or ["instagram"],
    }

    try:
        region = os.environ.get("AWS_REGION", "us-east-1")
        lambda_client = boto3.client("lambda", region_name=region)
        lambda_client.invoke(
            FunctionName=worker_arn,
            InvocationType="Event",   # fire-and-forget (async)
            Payload=json.dumps(payload).encode(),
        )
        logger.info(f"collect_worker invoked asynchronously for run {run_id}")
    except Exception as exc:
        logger.error(f"Failed to invoke collect_worker: {exc}", exc_info=True)
        CollectionRepo.mark_error(niche.id, run_id, started_at, f"Invoke failed: {exc}")
        return _response(500, {"success": False, "error": "Failed to start collection"})

    return _response(202, {
        "success": True,
        "data": {
            "run_id": run_id,
            "status": "pending",
            "keyword": keyword,
            "message": f"Collection started for keyword '{keyword}'. Poll /collection-runs/{run_id} for status.",
        },
    })
