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
    GET    /api/admin/collection/health   get_collection_health  (all users)
    GET    /api/admin/global-history      get_global_history     (admin only)
    GET    /api/admin/rate-limit/history  get_rate_limit_history (admin only)

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
from app.dynamodb.ad_repo import AdRepo
from app.dynamodb.rate_limit_repo import RateLimitRepo
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


def _get_role(event: dict) -> str:
    """Return the caller's role from the authorizer context (default: 'user')."""
    return (
        event.get("requestContext", {})
             .get("authorizer", {})
             .get("lambda", {})
             .get("role", "user")
    ) or "user"


def _get_user_email(event: dict) -> str:
    """Return the caller's email from the authorizer context."""
    return (
        event.get("requestContext", {})
             .get("authorizer", {})
             .get("lambda", {})
             .get("user_email", "")
    ) or ""


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

    keywords = data.get("keywords") or []
    if len(keywords) > 5:
        return _response(400, {"success": False, "error": "A niche can have at most 5 keywords"})

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
        keywords=keywords,
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

    if "keywords" in data and len(data["keywords"]) > 5:
        return _response(400, {"success": False, "error": "A niche can have at most 5 keywords"})

    if "auto_collect_interval_hours" in data and data["auto_collect_interval_hours"] not in [2, 3, 6, 12]:
        return _response(400, {"success": False, "error": "Invalid interval: must be 2, 3, 6, or 12"})

    updates = {}
    for field in ("name", "description", "keywords", "countries", "platforms",
                  "auto_collect_enabled", "auto_collect_interval_hours"):
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
    user_id    = _get_user_id(event)
    user_email = _get_user_email(event)
    slug       = _path_params(event).get("slug", "")
    data       = _body(event)

    niche = NicheRepo.get_by_slug(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    # Determine keyword
    keyword = data.get("keyword")
    if not keyword and niche.keywords:
        keyword = niche.keywords[0]

    if not keyword:
        return _response(400, {"success": False, "error": "No keyword specified and niche has no keywords"})

    # Create run record — store who triggered it and the niche name
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
        user_id=user_id or "",
        user_email=user_email,
        niche_name=niche.name,
    )
    CollectionRepo.create(run)
    logger.info(f"Created collection run {run_id} for niche {niche.id} by {user_email or user_id}")

    # Async invoke collect_worker
    worker_arn = os.environ.get("COLLECT_WORKER_ARN")
    if not worker_arn:
        logger.error("COLLECT_WORKER_ARN not set")
        return _response(500, {"success": False, "error": "Worker Lambda not configured"})

    payload = {
        "niche_id":   niche.id,
        "run_id":     run_id,
        "started_at": run.started_at,
        "keyword":    keyword,
        "limit":      data.get("limit", 50),
        "countries":  niche.countries or ["US"],
        "platforms":  niche.platforms or ["instagram"],
        "user_email": user_email,
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


def _list_collection_runs(event: dict) -> dict:
    """Return the most recent collection runs for a niche (newest first)."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    limit = min(int(_query_params(event).get("limit", 50)), 100)

    niche = NicheRepo.get_by_slug(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    runs = CollectionRepo.list_for_niche(niche.id, limit=limit)
    return _response(200, {
        "success": True,
        "data": [
            {
                "run_id": r.id,
                "status": r.status,
                "keyword": r.keywords_used[0] if r.keywords_used else None,
                "limit_requested": r.limit_requested,
                "countries": r.countries,
                "ads_found": r.ads_found,
                "ads_new": r.ads_new,
                "ads_updated": r.ads_updated,
                "total_ads_after": r.total_ads_after,
                "error_message": r.error_message,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "api_requests_made": r.api_requests_made,
            }
            for r in runs
        ],
        "count": len(runs),
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
        "api_requests_made": run.api_requests_made,
    }})


def _get_collection_health(event: dict) -> dict:
    """
    Return per-user collection health stats across all niches.
    Accessible to all authenticated users (shows their own data).

    For each niche owned by the caller, reports:
      - runs in the last 24 h and their success rate
      - hours elapsed since the most recent run
      - number of active ads that haven't been seen in the last 24 h (stale)
    """
    from datetime import datetime, timezone, timedelta

    user_id = _get_user_id(event)
    niches = NicheRepo.list_for_user(user_id)
    cutoff_24h = (
        datetime.now(tz=timezone.utc) - timedelta(hours=24)
    ).isoformat()

    summary_runs_24h = 0
    summary_successful_24h = 0
    niches_data = []

    for niche in niches:
        # Recent runs — fetch up to 50 so we cover a busy 24-h window
        recent_runs = CollectionRepo.list_for_niche(niche.id, limit=50)
        runs_24h = [r for r in recent_runs if (r.started_at or "") >= cutoff_24h]
        successful_24h = sum(1 for r in runs_24h if r.status == "completed")
        runs_24h_count = len(runs_24h)
        success_rate = (
            round(successful_24h / runs_24h_count * 100, 1)
            if runs_24h_count else None
        )

        # Hours since the most recent run completed (or started if in-flight)
        latest = recent_runs[0] if recent_runs else None
        hours_since_last: float | None = None
        if latest:
            ref_time = latest.completed_at or latest.started_at
            if ref_time:
                try:
                    ref_dt = datetime.fromisoformat(ref_time)
                    if ref_dt.tzinfo is None:
                        ref_dt = ref_dt.replace(tzinfo=timezone.utc)
                    hours_since_last = round(
                        (datetime.now(tz=timezone.utc) - ref_dt).total_seconds() / 3600,
                        1,
                    )
                except ValueError:
                    pass

        # Ads not seen in the last 24 h
        stale_ads_count = len(AdRepo.get_stale_ads(niche.id, hours_threshold=24))

        summary_runs_24h += runs_24h_count
        summary_successful_24h += successful_24h

        niches_data.append({
            "niche_id": niche.id,
            "slug": niche.slug,
            "name": niche.name,
            "auto_collect_enabled": niche.auto_collect_enabled,
            "auto_collect_interval_hours": niche.auto_collect_interval_hours,
            "hours_since_last_run": hours_since_last,
            "runs_24h": runs_24h_count,
            "successful_24h": successful_24h,
            "success_rate": success_rate,
            "stale_ads_count": stale_ads_count,
            "last_run_status": latest.status if latest else None,
        })

    total_niches = len(niches)
    niches_with_auto_collect = sum(1 for n in niches if n.auto_collect_enabled)

    return _response(200, {
        "success": True,
        "data": {
            "summary": {
                "total_niches": total_niches,
                "niches_with_auto_collect": niches_with_auto_collect,
                "total_runs_24h": summary_runs_24h,
                "total_successful_24h": summary_successful_24h,
            },
            "niches": niches_data,
        },
    })


def _get_global_history(event: dict) -> dict:
    """
    Admin-only: return all collection runs across all users and niches.
    Supports time-range filtering and pagination via cursor.

    Query params:
        hours  — look-back window in hours (default 24, max 168=7d)
        limit  — max results per page (default 50, max 200)
        cursor — opaque pagination token (base64 of LastEvaluatedKey JSON)
    """
    import base64

    if _get_role(event) != "admin":
        return _response(403, {"success": False, "error": "Admin access required"})

    from datetime import datetime, timezone, timedelta

    params = _query_params(event)
    hours  = min(int(params.get("hours", 24)), 168)
    limit  = min(int(params.get("limit", 50)), 200)
    cursor = params.get("cursor")

    cutoff = (
        datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    ).strftime("%Y-%m-%dT%H:%M:%S")

    # Decode pagination cursor
    exclusive_start_key = None
    if cursor:
        try:
            exclusive_start_key = json.loads(
                base64.b64decode(cursor.encode()).decode()
            )
        except Exception:
            exclusive_start_key = None

    runs, last_key = CollectionRepo.list_all_runs(
        cutoff_iso=cutoff,
        limit=limit,
        exclusive_start_key=exclusive_start_key,
    )

    # Encode next-page cursor
    next_cursor = None
    if last_key:
        next_cursor = base64.b64encode(
            json.dumps(last_key, default=str).encode()
        ).decode()

    return _response(200, {
        "success": True,
        "data": [
            {
                "run_id":            r.id,
                "niche_id":          r.niche_id,
                "niche_name":        r.niche_name,
                "user_email":        r.user_email,
                "status":            r.status,
                "keyword":           r.keywords_used[0] if r.keywords_used else None,
                "limit_requested":   r.limit_requested,
                "countries":         r.countries,
                "ads_found":         r.ads_found,
                "ads_new":           r.ads_new,
                "ads_updated":       r.ads_updated,
                "total_ads_after":   r.total_ads_after,
                "api_requests_made": r.api_requests_made,
                "error_message":     r.error_message,
                "started_at":        r.started_at,
                "completed_at":      r.completed_at,
            }
            for r in runs
        ],
        "count":       len(runs),
        "next_cursor": next_cursor,
        "hours":       hours,
    })


def _get_rate_limit_history(event: dict) -> dict:
    """
    Admin-only: return hourly Meta API request counts for the last N hours.

    Query params:
        hours — look-back window (default 48, max 168)
    """
    if _get_role(event) != "admin":
        return _response(403, {"success": False, "error": "Admin access required"})

    from datetime import datetime, timezone

    params = _query_params(event)
    hours  = min(int(params.get("hours", 48)), 168)

    buckets = RateLimitRepo.list_recent(hours=hours)

    # Current-hour bucket for the alert banner
    current_hour = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H")
    current_total = 0
    for b in buckets:
        if b["hour"] == current_hour:
            current_total = b["total_requests"]
            break

    return _response(200, {
        "success": True,
        "data": buckets,
        "current_hour": current_hour,
        "current_total": current_total,
        "alert_threshold": 160,
        "hard_limit": 200,
    })


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
    ("GET",    "/api/niches/{slug}/collection-runs"):                       _list_collection_runs,
    ("GET",    "/api/niches/{slug}/collection-runs/{run_id}"):              _get_collection_run,
    ("GET",    "/api/admin/collection/health"):                             _get_collection_health,
    ("GET",    "/api/admin/global-history"):                                _get_global_history,
    ("GET",    "/api/admin/rate-limit/history"):                            _get_rate_limit_history,
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
