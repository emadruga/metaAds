"""
Ads Lambda handler — search, detail, variants/analysis, related, pages, clear.

Routes (HTTP API v2 payload format 2.0):
    GET    /api/niches/{slug}/ads/search              search_ads
    GET    /api/niches/{slug}/ads/{ad_id}             get_ad
    GET    /api/niches/{slug}/ads/{ad_id}/related     get_related_ads
    GET    /api/niches/{slug}/ads/{ad_id}/variants/analysis  analyze_ad_variants
    GET    /api/niches/{slug}/pages                   list_pages
    DELETE /api/niches/{slug}/ads/clear               clear_all_ads

Environment variables:
    DYNAMODB_TABLE  — DynamoDB table name
"""

from __future__ import annotations

import json
import logging

from app.dynamodb.niche_repo import NicheRepo
from app.dynamodb.ad_repo import AdRepo
from app.dynamodb.page_repo import PageRepo

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


def _get_niche(user_id: str, slug: str):
    """Return Niche or None."""
    return NicheRepo.get_by_slug(user_id, slug)


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

def _search_ads(event: dict) -> dict:
    """
    Search ads within a niche.

    Query params: q, platform, is_active, status, min_days, max_days, cta,
                  page_name, page, per_page, group_by_variant
    """
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    qp = _query_params(event)

    niche = _get_niche(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    # Build filters dict matching AdRepo._apply_filters expectations
    filters: dict = {}

    # Text search
    if qp.get("q"):
        filters["search"] = qp["q"]

    # is_active / status
    is_active_raw = qp.get("is_active")
    status_raw = qp.get("status", "all")
    if is_active_raw is not None and is_active_raw != "":
        filters["is_active"] = is_active_raw.lower() == "true"
    elif status_raw == "active":
        filters["is_active"] = True
    elif status_raw == "inactive":
        filters["is_active"] = False

    # Numeric filters
    if qp.get("min_days"):
        try:
            filters["min_days"] = int(qp["min_days"])
        except ValueError:
            pass
    if qp.get("max_days"):
        try:
            filters["max_days"] = int(qp["max_days"])
        except ValueError:
            pass

    if qp.get("cta"):
        filters["cta_detected"] = qp["cta"]

    if qp.get("page_name"):
        filters["page_name"] = qp["page_name"]

    # Platform filter
    if qp.get("platform"):
        filters["platforms"] = [p.strip() for p in qp["platform"].split(",")]

    # Pagination
    try:
        page_num = int(qp.get("page", "1"))
    except ValueError:
        page_num = 1
    try:
        per_page = min(int(qp.get("per_page", "20")), 100)
    except ValueError:
        per_page = 20

    group_by_variant = qp.get("group_by_variant", "true").lower() != "false"

    result = AdRepo.search(
        niche_id=niche.id,
        filters=filters,
        group_by_variant=group_by_variant,
        page=page_num,
        per_page=per_page,
    )

    import math
    total = result["total"]
    total_ads = result["total_ads"]
    per_page_val = result["per_page"]
    page_val = result["page"]
    pages = math.ceil(total / per_page_val) if per_page_val else 1

    return _response(200, {
        "success": True,
        "data": result["ads"],
        "pagination": {
            "page": page_val,
            "per_page": per_page_val,
            "total": total,
            "total_ads": total_ads,
            "pages": pages,
            "has_next": result["has_next"],
            "has_prev": page_val > 1,
        },
    })


def _get_ad(event: dict) -> dict:
    """Get ad detail by meta_ad_id."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    ad_id = _path_params(event).get("ad_id", "")

    niche = _get_niche(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    ad = AdRepo.get(niche.id, ad_id)
    if not ad:
        return _response(404, {"success": False, "error": "Ad not found"})

    ad_data = ad.to_dict()

    # Count same-variant ads
    variants = AdRepo.get_variants(niche.id, ad.page_name, ad.headline)
    ad_data["variant_count"] = len(variants)

    return _response(200, {"success": True, "data": ad_data})


def _get_related_ads(event: dict) -> dict:
    """Other ads from the same page within the niche."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    ad_id = _path_params(event).get("ad_id", "")
    qp = _query_params(event)

    niche = _get_niche(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    ad = AdRepo.get(niche.id, ad_id)
    if not ad:
        return _response(404, {"success": False, "error": "Ad not found"})

    try:
        limit = min(int(qp.get("limit", "6")), 20)
    except ValueError:
        limit = 6

    related = AdRepo.get_related(
        niche_id=niche.id,
        page_id=ad.page_id or "",
        exclude_meta_ad_id=ad_id,
        limit=limit,
    )

    total_variants = len(related) + 1
    insights = {
        "total_variants": total_variants,
        "longest_running": None,
        "newest": None,
    }

    if related:
        all_ads = [ad.to_card_dict()] + related
        longest = max(all_ads, key=lambda x: x.get("days_active") or 0)
        newest = max(all_ads, key=lambda x: x.get("start_date") or "")
        insights["longest_running"] = {
            "id": longest.get("meta_ad_id"),
            "days_active": longest.get("days_active"),
        }
        insights["newest"] = {
            "id": newest.get("meta_ad_id"),
            "start_date": newest.get("start_date"),
        }

    return _response(200, {
        "success": True,
        "data": {
            "original": ad.to_card_dict(),
            "related": related,
            "insights": insights,
        },
    })


def _analyze_ad_variants(event: dict) -> dict:
    """Analyze differences between ad variants (same page_name + headline)."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    ad_id = _path_params(event).get("ad_id", "")

    niche = _get_niche(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    ad = AdRepo.get(niche.id, ad_id)
    if not ad:
        return _response(404, {"success": False, "error": "Ad not found"})

    variants = AdRepo.get_variants(niche.id, ad.page_name, ad.headline)

    if len(variants) <= 1:
        return _response(200, {
            "success": True,
            "data": {
                "total_variants": 1,
                "differences": [],
                "variants": variants,
            },
        })

    differences = _analyze_variant_differences(variants)
    return _response(200, {
        "success": True,
        "data": {
            "total_variants": len(variants),
            "differences": differences,
            "variants": variants,
        },
    })


def _analyze_variant_differences(variants: list) -> list:
    """Return list of field-level difference summaries across variants."""
    fields_map = {
        "body": "Body Text",
        "description": "Description",
        "link_caption": "Link Caption",
        "cta_detected": "Call-to-Action",
    }
    analysis = []

    for field, label in fields_map.items():
        unique_vals = {v.get(field) for v in variants if v.get(field)}
        if len(unique_vals) > 1:
            analysis.append({
                "field": field,
                "variations_count": len(unique_vals),
                "label": label,
                "description": f"{len(unique_vals)} different {label.lower()} versions",
                "values": list(unique_vals)[:5],
            })

    # Body length variations
    body_lengths = [len(v.get("body") or "") for v in variants]
    if len(set(body_lengths)) > 1:
        analysis.append({
            "field": "body_length",
            "variations_count": len(set(body_lengths)),
            "label": "Body Text Length",
            "description": f"Text length varies from {min(body_lengths)} to {max(body_lengths)} characters",
            "values": [f"{l} chars" for l in sorted(set(body_lengths))],
        })

    if not analysis:
        analysis.append({
            "field": "media",
            "variations_count": len(variants),
            "label": "Creative Media",
            "description": f"{len(variants)} variants — likely image/video variations with identical text",
            "values": [],
        })

    return analysis


def _list_pages(event: dict) -> dict:
    """List pages that have appeared in a niche's ad collection."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")

    niche = _get_niche(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    pages = PageRepo.list_pages_for_niche(niche.id)
    return _response(200, {
        "success": True,
        "data": [p.to_dict() for p in pages],
        "count": len(pages),
    })


def _clear_all_ads(event: dict) -> dict:
    """Delete ads for a niche. Pass include_saved=true to also delete saved ads."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    qp = _query_params(event)

    niche = _get_niche(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    include_saved = qp.get("include_saved", "false").lower() == "true"
    deleted = AdRepo.clear_all(niche.id, include_saved=include_saved)
    return _response(200, {
        "success": True,
        "message": f"Cleared {deleted} ads from niche",
        "ads_deleted": deleted,
    })


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

_ROUTES: dict[tuple[str, str], callable] = {
    ("GET",    "/api/niches/{slug}/ads/search"):                     _search_ads,
    ("GET",    "/api/niches/{slug}/ads/{ad_id}"):                    _get_ad,
    ("GET",    "/api/niches/{slug}/ads/{ad_id}/related"):            _get_related_ads,
    ("GET",    "/api/niches/{slug}/ads/{ad_id}/variants/analysis"):  _analyze_ad_variants,
    ("GET",    "/api/niches/{slug}/pages"):                          _list_pages,
    ("DELETE", "/api/niches/{slug}/ads/clear"):                      _clear_all_ads,
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
