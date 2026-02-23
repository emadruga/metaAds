"""
Saved Ads Lambda handler — save, unsave, update tags, list saved.

Routes (HTTP API v2 payload format 2.0):
    GET    /api/niches/{slug}/saved              list_saved_ads
    POST   /api/niches/{slug}/ads/{ad_id}/save   save_ad
    DELETE /api/niches/{slug}/ads/{ad_id}/save   unsave_ad
    PATCH  /api/niches/{slug}/ads/{ad_id}/save   update_saved_ad

Environment variables:
    DYNAMODB_TABLE  — DynamoDB table name
"""

from __future__ import annotations

import json
import logging

from app.dynamodb.niche_repo import NicheRepo
from app.dynamodb.ad_repo import AdRepo

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


def _get_niche(user_id: str, slug: str):
    return NicheRepo.get_by_slug(user_id, slug)


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

def _list_saved_ads(event: dict) -> dict:
    """List saved ads for a niche with cursor-based pagination."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    qp = _query_params(event)

    niche = _get_niche(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    try:
        limit = min(int(qp.get("per_page", "20")), 100)
    except ValueError:
        limit = 20

    cursor = qp.get("cursor")

    result = AdRepo.list_saved(niche_id=niche.id, limit=limit, cursor=cursor)

    # Collect unique tags across all saved ads for filter UI
    # (small set — iterate in app)
    all_tags: set[str] = set()
    for ad_dict in result["ads"]:
        for tag in (ad_dict.get("saved_tags") or []):
            all_tags.add(tag)

    # Tag filter applied client-side (or caller can pass tag= and we filter)
    tag_filter = qp.get("tag")
    ads_out = result["ads"]
    if tag_filter:
        ads_out = [a for a in ads_out if tag_filter in (a.get("saved_tags") or [])]

    return _response(200, {
        "success": True,
        "data": ads_out,
        "tags": sorted(all_tags),
        "pagination": {
            "has_next": result["has_next"],
            "next_cursor": result["next_cursor"],
            "limit": limit,
        },
    })


def _save_ad(event: dict) -> dict:
    """Mark an ad as saved and attach optional tags."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    ad_id = _path_params(event).get("ad_id", "")
    data = _body(event)

    niche = _get_niche(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    existing = AdRepo.get(niche.id, ad_id)
    if not existing:
        return _response(404, {"success": False, "error": "Ad not found"})

    if existing.is_saved:
        return _response(400, {"success": False, "error": "Ad is already saved"})

    tags = data.get("tags") or []
    ad = AdRepo.save_ad(niche_id=niche.id, meta_ad_id=ad_id, tags=tags)
    return _response(200, {"success": True, "data": ad.to_dict()})


def _unsave_ad(event: dict) -> dict:
    """Remove saved state from an ad."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    ad_id = _path_params(event).get("ad_id", "")

    niche = _get_niche(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    existing = AdRepo.get(niche.id, ad_id)
    if not existing:
        return _response(404, {"success": False, "error": "Ad not found"})

    if not existing.is_saved:
        return _response(400, {"success": False, "error": "Ad is not saved"})

    AdRepo.unsave_ad(niche_id=niche.id, meta_ad_id=ad_id)
    return _response(200, {"success": True, "message": "Ad unsaved"})


def _update_saved_ad(event: dict) -> dict:
    """Update tags on an already-saved ad."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    ad_id = _path_params(event).get("ad_id", "")
    data = _body(event)

    niche = _get_niche(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    existing = AdRepo.get(niche.id, ad_id)
    if not existing:
        return _response(404, {"success": False, "error": "Ad not found"})

    if not existing.is_saved:
        return _response(400, {"success": False, "error": "Ad is not saved"})

    if "tags" in data:
        ad = AdRepo.update_saved_tags(niche_id=niche.id, meta_ad_id=ad_id, tags=data["tags"])
        return _response(200, {"success": True, "data": ad.to_dict()})

    return _response(200, {"success": True, "data": existing.to_dict()})


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

_ROUTES: dict[tuple[str, str], callable] = {
    ("GET",    "/api/niches/{slug}/saved"):              _list_saved_ads,
    ("POST",   "/api/niches/{slug}/ads/{ad_id}/save"):   _save_ad,
    ("DELETE", "/api/niches/{slug}/ads/{ad_id}/save"):   _unsave_ad,
    ("PATCH",  "/api/niches/{slug}/ads/{ad_id}/save"):   _update_saved_ad,
}


def handler(event: dict, context) -> dict:
    route_key = event.get("routeKey", "")
    parts = route_key.split(" ", 1)
    if len(parts) == 2:
        key = (parts[0], parts[1])
        fn = _ROUTES.get(key)
        if fn:
            return fn(event)

    return _response(404, {"error": "Not found"})
