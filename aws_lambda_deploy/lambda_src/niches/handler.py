"""
Niches Lambda handler — CRUD + stats + collection trigger (async).

Routes (HTTP API v2 payload format 2.0):
    GET    /api/niches                    list_niches
    POST   /api/niches                    create_niche
    GET    /api/niches/{slug}             get_niche
    PATCH  /api/niches/{slug}             update_niche
    DELETE /api/niches/{slug}             delete_niche
    GET    /api/niches/{slug}/stats       get_niche_stats
    POST   /api/niches/{slug}/collect     trigger_collection  → returns 202, async-invokes worker
    GET    /api/niches/{slug}/collection-runs/{run_id}   get_collection_run

Environment variables:
    DYNAMODB_TABLE        — DynamoDB table name
    COLLECT_WORKER_ARN    — ARN of the collect_worker Lambda
    AWS_REGION            — injected by Lambda runtime
"""

from __future__ import annotations

import json
import logging
import os
import re

import boto3

from app.dynamodb.niche_repo import NicheRepo
from app.dynamodb.collection_repo import CollectionRepo
from app.dynamodb.models import Niche, CollectionRun
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


def _path_params(event: dict) -> dict:
    return event.get("pathParameters") or {}


def _query_params(event: dict) -> dict:
    return event.get("queryStringParameters") or {}


def _body(event: dict) -> dict:
    raw = event.get("body") or "{}"
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = re.sub(r"^-+|-+$", "", slug)
    return slug


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

def _list_niches(event: dict) -> dict:
    user_id = _get_user_id(event)
    niches = NicheRepo.list_for_user(user_id)

    niches_data = []
    for niche in niches:
        nd = niche.to_dict()
        nd["stats"] = NicheRepo.get_stats(niche.id)
        niches_data.append(nd)

    return _response(200, {"success": True, "data": niches_data, "count": len(niches_data)})


def _create_niche(event: dict) -> dict:
    user_id = _get_user_id(event)
    data = _body(event)

    if not data.get("name"):
        return _response(400, {"success": False, "error": "Name is required"})

    slug = data.get("slug") or _slugify(data["name"])

    existing = NicheRepo.get_by_slug(user_id, slug)
    if existing:
        return _response(409, {"success": False, "error": f"Niche with slug '{slug}' already exists"})

    niche = Niche(
        id=generate_uuid(),
        user_id=user_id,
        name=data["name"],
        slug=slug,
        description=data.get("description") or "",
        keywords=data.get("keywords") or [],
        countries=data.get("countries") or ["US"],
        platforms=data.get("platforms") or ["instagram"],
        is_active=True,
        created_at=now_iso8601(),
        updated_at=now_iso8601(),
    )
    NicheRepo.create(niche)
    return _response(201, {"success": True, "data": niche.to_dict()})


def _get_niche(event: dict) -> dict:
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")

    niche = NicheRepo.get_by_slug(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    nd = niche.to_dict()
    nd["stats"] = NicheRepo.get_stats(niche.id)
    return _response(200, {"success": True, "data": nd})


def _update_niche(event: dict) -> dict:
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    data = _body(event)

    niche = NicheRepo.get_by_slug(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    updates = {}
    for field in ("name", "description", "keywords", "countries", "platforms"):
        if field in data:
            updates[field] = data[field]

    if updates:
        NicheRepo.update(niche.id, user_id, **updates)
        niche = NicheRepo.get(niche.id)

    return _response(200, {"success": True, "data": niche.to_dict()})


def _delete_niche(event: dict) -> dict:
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")

    niche = NicheRepo.get_by_slug(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    NicheRepo.delete(user_id, niche.id)
    return _response(200, {"success": True, "message": f"Niche '{niche.name}' deleted"})


def _get_niche_stats(event: dict) -> dict:
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")

    niche = NicheRepo.get_by_slug(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    stats = NicheRepo.get_stats(niche.id)
    return _response(200, {
        "success": True,
        "data": {
            "niche_id": niche.id,
            "slug": niche.slug,
            "name": niche.name,
            "stats": stats,
        },
    })


def _trigger_collection(event: dict) -> dict:
    """
    Create a CollectionRun (status=pending) and async-invoke collect_worker.
    Returns 202 immediately — no blocking API Gateway timeout.
    """
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    data = _body(event)

    niche = NicheRepo.get_by_slug(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    # Determine keyword
    keyword = data.get("keyword")
    if not keyword and niche.keywords:
        keyword = niche.keywords[0]

    if not keyword:
        return _response(400, {"success": False, "error": "No keyword specified and niche has no keywords"})

    # Create run record
    run_id = generate_uuid()
    run = CollectionRun(
        id=run_id,
        niche_id=niche.id,
        status="pending",
        keywords_used=[keyword],
        ads_found=0,
        ads_new=0,
        ads_updated=0,
        error_message=None,
        started_at=now_iso8601(),
        completed_at=None,
    )
    CollectionRepo.create(run)
    logger.info(f"Created collection run {run_id} for niche {niche.id}")

    # Async invoke collect_worker
    worker_arn = os.environ.get("COLLECT_WORKER_ARN")
    if not worker_arn:
        logger.error("COLLECT_WORKER_ARN not set")
        return _response(500, {"success": False, "error": "Worker Lambda not configured"})

    payload = {
        "niche_id": niche.id,
        "run_id": run_id,
        "started_at": run.started_at,
        "keyword": keyword,
        "limit": data.get("limit", 50),
        "countries": niche.countries or ["US"],
        "platforms": niche.platforms or ["instagram"],
    }

    try:
        lambda_client = boto3.client("lambda", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        lambda_client.invoke(
            FunctionName=worker_arn,
            InvocationType="Event",          # async — no waiting
            Payload=json.dumps(payload).encode(),
        )
        logger.info(f"Async invoked collect_worker for run {run_id}")
    except Exception as exc:
        logger.error(f"Failed to invoke collect_worker: {exc}", exc_info=True)
        CollectionRepo.mark_error(niche.id, run_id, run.started_at, f"Failed to invoke worker: {exc}")
        return _response(500, {"success": False, "error": "Failed to start collection"})

    return _response(202, {
        "success": True,
        "data": {
            "run_id": run_id,
            "status": "pending",
            "keyword": keyword,
            "message": f"Collection started for keyword '{keyword}'",
        },
    })


def _get_collection_run(event: dict) -> dict:
    """Poll endpoint — returns current status of a collection run."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    run_id = _path_params(event).get("run_id", "")

    niche = NicheRepo.get_by_slug(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    run = CollectionRepo.get(niche.id, run_id)
    if not run:
        return _response(404, {"success": False, "error": "Collection run not found"})

    return _response(200, {"success": True, "data": {
        "run_id": run.id,
        "niche_id": run.niche_id,
        "status": run.status,
        "keywords_used": run.keywords_used,
        "ads_found": run.ads_found,
        "ads_new": run.ads_new,
        "ads_updated": run.ads_updated,
        "error_message": run.error_message,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }})


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

_ROUTES: dict[tuple[str, str], callable] = {
    ("GET",    "/api/niches"):                                              _list_niches,
    ("POST",   "/api/niches"):                                              _create_niche,
    ("GET",    "/api/niches/{slug}"):                                       _get_niche,
    ("PATCH",  "/api/niches/{slug}"):                                       _update_niche,
    ("DELETE", "/api/niches/{slug}"):                                       _delete_niche,
    ("GET",    "/api/niches/{slug}/stats"):                                 _get_niche_stats,
    ("POST",   "/api/niches/{slug}/collect"):                               _trigger_collection,
    ("GET",    "/api/niches/{slug}/collection-runs/{run_id}"):              _get_collection_run,
}


def handler(event: dict, context) -> dict:
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    route_key = event.get("routeKey", "")  # e.g. "GET /api/niches/{slug}"

    # Normalise: "GET /api/niches/{slug}" → ("GET", "/api/niches/{slug}")
    parts = route_key.split(" ", 1)
    if len(parts) == 2:
        key = (parts[0], parts[1])
        fn = _ROUTES.get(key)
        if fn:
            return fn(event)

    return _response(404, {"error": "Not found"})
