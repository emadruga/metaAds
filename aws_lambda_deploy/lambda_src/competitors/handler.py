"""
Competitors Lambda handler — CRUD for tracked competitor advertiser pages.

Routes (HTTP API v2 payload format 2.0):
    POST   /api/competitors/resolve        resolve_competitor  (search, no save)
    GET    /api/competitors                list_competitors
    POST   /api/competitors                add_competitor
    PATCH  /api/competitors/{page_id}      update_competitor
    DELETE /api/competitors/{page_id}      remove_competitor
    GET    /api/competitors/{page_id}/ads  get_competitor_ads

Environment variables:
    DYNAMODB_TABLE         — DynamoDB table name
    META_API_SECRETS_NAME  — e.g. metaads/dev/meta-api
    AWS_REGION             — injected by Lambda runtime
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import List

import boto3
import requests

from app.dynamodb.competitor_repo import CompetitorRepo
from app.dynamodb.models import Competitor
from app.utils.ids import now_iso8601

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


# ---------------------------------------------------------------------------
# Meta API credentials (cached per cold start)
# ---------------------------------------------------------------------------

_meta_token: str | None = None


def _get_meta_token() -> str:
    global _meta_token
    if _meta_token:
        return _meta_token

    secret_name = os.environ.get("META_API_SECRETS_NAME", "metaads/dev/meta-api")
    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("secretsmanager", region_name=region)
    resp = client.get_secret_value(SecretId=secret_name)
    _meta_token = json.loads(resp["SecretString"])["access_token"]
    return _meta_token


# ---------------------------------------------------------------------------
# Meta API helpers
# ---------------------------------------------------------------------------

_META_BASE = "https://graph.facebook.com/v24.0"

# Broadened country list used as fallback when stored country yields 0 ads.
# Covers the main markets where Brazilian / Lusophone advertisers tend to run.
_MAJOR_MARKETS = ["BR", "PT", "MX", "AR", "US", "ES", "CO", "CL", "PE", "CA", "FR", "DE", "GB", "AU", "JP"]

# Country list used for competitor discovery (page_id resolution).
# Ordered to maximise hit rate: English-speaking markets first, then PT/ES/global.
_DISCOVERY_MARKETS = ["US", "GB", "AU", "CA", "BR", "PT", "MX", "DE", "FR", "IT", "ES", "JP", "AR", "CO", "CL"]

_AD_FIELDS = [
    "id",
    "ad_creation_time",
    "ad_creative_bodies",
    "ad_creative_link_captions",
    "ad_creative_link_titles",
    "ad_creative_link_descriptions",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_snapshot_url",
    "page_name",
    "page_id",
    "platforms",
    "publisher_platforms",
    "media_type",
    "spend",
    "impressions",
]


def _get_page_profile(page_id: str) -> dict:
    """
    Fetch public page metadata (fan_count, category, about) from the Graph API.
    Returns an empty dict on any error — this is best-effort enrichment.
    """
    try:
        token = _get_meta_token()
        resp = requests.get(
            f"{_META_BASE}/{page_id}",
            params={
                "access_token": token,
                "fields": "name,fan_count,category,about",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        logger.warning(f"Could not fetch page profile for {page_id}: {exc}")
    return {}


def _normalize_media_type(raw: str | None) -> str:
    """Map Meta API media_type values to a consistent frontend enum."""
    if not raw:
        return "OTHER"
    t = raw.upper()
    if t == "PHOTO":
        return "IMAGE"
    if t in ("CAROUSEL_CONTAINER", "CAROUSEL_AD"):
        return "CAROUSEL"
    if t in ("VIDEO", "IMAGE", "CAROUSEL", "OTHER"):
        return t
    return "OTHER"


def _variant_key(page_name: str, headline: str, is_active: bool) -> str:
    """Stable 12-char hash of page_name|headline|active (lowercase).
    Active and inactive ads with the same headline form separate groups."""
    active_flag = "1" if is_active else "0"
    raw = f"{(page_name or '').strip().lower()}|{(headline or '').strip().lower()}|{active_flag}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _group_by_variant(ads: List[dict]) -> List[dict]:
    """
    Group pre-sorted ads by (page_name, headline, is_active).
    Active and inactive ads are kept in separate groups.
    The group's start_date is the oldest (minimum) start_date across all variants.
    The group's days_active is the maximum across all variants.
    """
    groups: dict[str, dict] = {}
    order: List[str] = []

    for ad in ads:
        is_active = ad.get("is_active", False)
        key = _variant_key(ad.get("page_name", ""), ad.get("headline", ""), is_active)
        if key not in groups:
            groups[key] = {
                "variant_key": key,
                "page_name": ad.get("page_name", ""),
                "headline": ad.get("headline", ""),
                "body": ad.get("body", ""),
                "description": ad.get("description", ""),
                "link_caption": ad.get("link_caption", ""),
                "media_type": ad.get("media_type"),
                "start_date": ad.get("start_date"),
                "days_active": ad.get("days_active") or 0,
                "is_active": is_active,
                "snapshot_url": ad.get("snapshot_url"),
                "platforms": ad.get("platforms", []),
                "count": 0,
                "ads": [],
            }
            order.append(key)

        g = groups[key]
        g["ads"].append(ad)
        g["count"] += 1
        if (ad.get("days_active") or 0) > g["days_active"]:
            g["days_active"] = ad["days_active"]
        # Keep the oldest (minimum) start_date across the group
        new_start = ad.get("start_date")
        if new_start and (not g["start_date"] or new_start < g["start_date"]):
            g["start_date"] = new_start

    for g in groups.values():
        g["ads"].sort(key=lambda a: a.get("start_date") or "")

    return [groups[k] for k in order]


def _search_by_page_name(page_name: str, hint_country: str = "") -> List[dict]:
    """
    Search the Ad Library for ads matching page_name.

    Cascades across country lists to maximise discovery:
      1. User-hinted country (if provided and not empty)
      2. Broad _DISCOVERY_MARKETS list (comma-joined, single API call)

    Uses ad_active_status=ALL so paused / historical ads are also matched —
    we only need one ad to extract page_id, so restricting to ACTIVE is too narrow.

    Returns (ads, resolved_countries) where resolved_countries is the
    country string that produced a hit — useful for storing on the Competitor
    so subsequent ad fetches target the right market.
    """
    token = _get_meta_token()

    # Build ordered list of country strings to attempt
    country_passes: List[str] = []
    hint = (hint_country or "").strip().upper()
    if hint:
        country_passes.append(hint)
    broad = ",".join(_DISCOVERY_MARKETS)
    if broad not in country_passes:
        country_passes.append(broad)

    for country_str in country_passes:
        params = {
            "access_token": token,
            "search_terms": page_name,
            "ad_reached_countries": country_str,
            "ad_active_status": "ALL",
            "fields": ",".join(_AD_FIELDS),
            "limit": 25,
        }
        resp = requests.get(f"{_META_BASE}/ads_archive", params=params, timeout=20)
        resp.raise_for_status()
        results = resp.json().get("data", [])
        if results:
            logger.info(
                f"_search_by_page_name: found {len(results)} ads for "
                f"'{page_name}' with countries={country_str}"
            )
            return results, country_str

    return [], ""


def _fetch_ads_for_page(
    page_id: str,
    countries: List[str],
    ad_active_status: str,
    limit: int,
) -> List[dict]:
    """
    Fetch ads from the Ad Library filtered by page_id.
    Uses the search_page_ids parameter for precise targeting.
    """
    token = _get_meta_token()
    params = {
        "access_token": token,
        "search_page_ids": page_id,
        "ad_reached_countries": ",".join(countries),
        "ad_active_status": ad_active_status,
        "fields": ",".join(_AD_FIELDS),
        "limit": min(limit, 100),
    }

    all_ads: List[dict] = []
    url = f"{_META_BASE}/ads_archive"

    while len(all_ads) < limit:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        all_ads.extend(data.get("data", []))

        if "paging" in data and "next" in data["paging"]:
            url = data["paging"]["next"]
            params = {}
        else:
            break

    return all_ads[:limit]


def _format_ad(raw: dict) -> dict:
    """Convert a raw Meta API ad object to a clean frontend-friendly dict."""
    start_str = raw.get("ad_delivery_start_time")
    stop_str = raw.get("ad_delivery_stop_time")

    days_active: int | None = None
    if start_str:
        try:
            start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if stop_str:
                end = datetime.fromisoformat(stop_str.replace("Z", "+00:00"))
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
            else:
                end = datetime.now(tz=timezone.utc)
            days_active = max(0, (end - start).days)
        except Exception:
            pass

    bodies = raw.get("ad_creative_bodies") or []
    titles = raw.get("ad_creative_link_titles") or []
    descriptions = raw.get("ad_creative_link_descriptions") or []
    captions = raw.get("ad_creative_link_captions") or []
    platforms = raw.get("platforms") or raw.get("publisher_platforms") or []

    spend_raw = raw.get("spend") or {}
    impressions_raw = raw.get("impressions") or {}

    return {
        "meta_ad_id": raw.get("id"),
        "page_id": raw.get("page_id"),
        "page_name": raw.get("page_name"),
        "body": bodies[0] if bodies else "",
        "headline": titles[0] if titles else "",
        "description": descriptions[0] if descriptions else "",
        "link_caption": captions[0] if captions else "",
        "creation_time": raw.get("ad_creation_time"),
        "start_date": start_str,
        "end_date": stop_str,
        "is_active": stop_str is None,
        "days_active": days_active,
        "snapshot_url": raw.get("ad_snapshot_url"),
        "platforms": platforms,
        "media_type": _normalize_media_type(raw.get("media_type")),
        "spend": {
            "lower_bound": spend_raw.get("lower_bound"),
            "upper_bound": spend_raw.get("upper_bound"),
        } if spend_raw else None,
        "impressions": {
            "lower_bound": impressions_raw.get("lower_bound"),
            "upper_bound": impressions_raw.get("upper_bound"),
        } if impressions_raw else None,
    }


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

def _resolve_competitor(event: dict) -> dict:
    """
    POST /api/competitors/resolve

    Searches Meta Ad Library for the given page_name and returns up to 5
    distinct candidate pages with basic profile metadata.
    Does NOT save anything — purely a preview/confirmation step used by the
    frontend before calling POST /api/competitors to actually save.

    Request body:
        { "page_name": "Marcella NYC", "countries": "US" }   # countries optional hint

    Response:
        { "success": true, "candidates": [
            { "page_id": "...", "page_name": "...", "fan_count": 88500,
              "category": "Clothing (Brand)", "about": "..." },
            ...
          ]
        }
    """
    data = _body(event)
    page_name = (data.get("page_name") or "").strip()
    hint_country = (data.get("countries") or "").strip()

    if not page_name:
        return _response(400, {"success": False, "error": "page_name is required"})

    try:
        ads, resolved_countries = _search_by_page_name(page_name, hint_country=hint_country)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 0
        if status == 400:
            return _response(422, {
                "success": False,
                "error": "Meta API rejected the search. Check that your access token is valid.",
            })
        logger.warning(f"Meta API error during resolve: {exc}")
        return _response(502, {"success": False, "error": "Meta API error during search."})
    except Exception as exc:
        logger.warning(f"resolve search failed: {exc}")
        return _response(502, {"success": False, "error": "Search failed. Please try again."})

    if not ads:
        return _response(404, {
            "success": False,
            "error": (
                f"No pages found matching '{page_name}'. "
                "Try the exact advertiser name shown in Meta Ad Library, "
                "or provide the page_id directly."
            ),
        })

    # Deduplicate by page_id, keep up to 5 candidates
    seen_pids: set = set()
    candidates: List[dict] = []
    for ad in ads:
        pid   = ad.get("page_id", "")
        pname = ad.get("page_name", "")
        if pid and pid not in seen_pids:
            seen_pids.add(pid)
            candidates.append({"page_id": pid, "page_name": pname})
        if len(candidates) >= 5:
            break

    # Enrich only the top candidate with profile metadata (best-effort, 1 extra call)
    if candidates:
        profile = _get_page_profile(candidates[0]["page_id"])
        candidates[0].update({
            "fan_count": profile.get("fan_count"),
            "category":  profile.get("category", ""),
            "about":     profile.get("about", ""),
        })

    logger.info(
        f"resolve '{page_name}' → {len(candidates)} candidates: "
        f"{[c['page_id'] for c in candidates]} (resolved via countries={resolved_countries})"
    )
    return _response(200, {
        "success": True,
        "candidates": candidates,
        "resolved_countries": resolved_countries,
    })


def _list_competitors(event: dict) -> dict:
    user_id = _get_user_id(event)
    competitors = CompetitorRepo.list_for_user(user_id)
    return _response(200, {
        "success": True,
        "data": [c.to_dict() for c in competitors],
        "count": len(competitors),
    })


def _add_competitor(event: dict) -> dict:
    user_id = _get_user_id(event)
    data = _body(event)

    page_name = (data.get("page_name") or "").strip()
    page_id = (data.get("page_id") or "").strip()
    # countries stores which market to use for ongoing ad collection.
    # Default to "US,BR" so the cascade in _fetch_ads_for_page covers both.
    countries = (data.get("countries") or "US,BR").strip()

    if not page_name:
        return _response(400, {"success": False, "error": "page_name is required"})

    # If page_id not provided, search Meta API to resolve it
    if not page_id:
        try:
            # Pass the first country in the list as a hint (user-selected market).
            hint = countries.split(",")[0].strip()
            ads, resolved_countries = _search_by_page_name(page_name, hint_country=hint)
            # Prefer exact case-insensitive match on page_name
            matched = [a for a in ads if a.get("page_name", "").lower() == page_name.lower()]
            if not matched:
                matched = ads  # fallback: use first result
            if matched:
                page_id = matched[0].get("page_id", "")
                page_name = matched[0].get("page_name", page_name)  # use canonical casing
                if resolved_countries:
                    countries = resolved_countries  # use the market that actually found the page
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            if status == 400:
                return _response(422, {
                    "success": False,
                    "error": "Meta API rejected the search. Check that your access token is valid.",
                })
            logger.warning(f"Meta API search failed with status {status}: {exc}")
        except Exception as exc:
            logger.warning(f"Meta API search failed: {exc}")

    if not page_id:
        return _response(422, {
            "success": False,
            "error": (
                f"Could not find a page_id for '{page_name}'. "
                "Use the exact advertiser name shown in Meta Ad Library, "
                "or provide the page_id directly."
            ),
        })

    # Idempotent check
    existing = CompetitorRepo.get(user_id, page_id)
    if existing:
        return _response(409, {
            "success": False,
            "error": f"'{existing.page_name}' is already in your competitors list.",
        })

    # Enrich with page profile metadata from Graph API (best-effort)
    profile = _get_page_profile(page_id)
    fan_count = profile.get("fan_count")
    if fan_count is not None:
        try:
            fan_count = int(fan_count)
        except (TypeError, ValueError):
            fan_count = None

    competitor = Competitor(
        user_id=user_id,
        page_id=page_id,
        page_name=page_name,
        notes=data.get("notes", ""),
        added_at=now_iso8601(),
        countries=countries,
        fan_count=fan_count,
        category=profile.get("category", ""),
        about=profile.get("about", ""),
    )
    CompetitorRepo.create(competitor)
    logger.info(f"User {user_id} added competitor: {page_name} (page_id={page_id})")

    return _response(201, {"success": True, "data": competitor.to_dict()})


def _update_competitor(event: dict) -> dict:
    user_id = _get_user_id(event)
    page_id = _path_params(event).get("page_id", "")
    data = _body(event)

    existing = CompetitorRepo.get(user_id, page_id)
    if not existing:
        return _response(404, {"success": False, "error": "Competitor not found"})

    if "notes" in data:
        CompetitorRepo.update_notes(user_id, page_id, data["notes"])

    updated = CompetitorRepo.get(user_id, page_id)
    return _response(200, {"success": True, "data": updated.to_dict()})


def _remove_competitor(event: dict) -> dict:
    user_id = _get_user_id(event)
    page_id = _path_params(event).get("page_id", "")

    existing = CompetitorRepo.get(user_id, page_id)
    if not existing:
        return _response(404, {"success": False, "error": "Competitor not found"})

    CompetitorRepo.delete(user_id, page_id)
    logger.info(f"User {user_id} removed competitor page_id={page_id}")
    return _response(200, {"success": True, "message": "Competitor removed"})


def _get_competitor_ads(event: dict) -> dict:
    """
    Fetch active ads for a competitor from the Meta Ad Library (live).
    Query params:
        limit    — max ads to return (default 100, max 200)
        status   — ACTIVE | INACTIVE | ALL (default ACTIVE)
        countries — comma-separated ISO codes (default US,BR)
    """
    user_id = _get_user_id(event)
    page_id = _path_params(event).get("page_id", "")
    params = _query_params(event)

    competitor = CompetitorRepo.get(user_id, page_id)
    if not competitor:
        return _response(404, {"success": False, "error": "Competitor not found"})

    limit = min(int(params.get("limit", 100)), 200)
    # Default to ALL so we surface both active and historical ads (like the ANDROMEDA doc recommends)
    ad_active_status = params.get("status", "ALL").upper()
    countries_raw = params.get("countries") or competitor.countries or "BR"
    countries = [c.strip() for c in countries_raw.split(",") if c.strip()]

    try:
        raw_ads = _fetch_ads_for_page(page_id, countries, ad_active_status, limit)

        # Cascade retry: if stored country returns 0, widen to major markets
        if not raw_ads:
            broad = list(dict.fromkeys(countries + _MAJOR_MARKETS))
            logger.info(
                f"0 ads for page {page_id} with countries={countries}, "
                f"retrying with {len(broad)} markets"
            )
            raw_ads = _fetch_ads_for_page(page_id, broad, ad_active_status, limit)

        # Final fallback: broad markets + ALL statuses
        if not raw_ads and ad_active_status != "ALL":
            broad = list(dict.fromkeys(countries + _MAJOR_MARKETS))
            logger.info(f"Still 0 ads, retrying with ALL statuses + broad markets")
            raw_ads = _fetch_ads_for_page(page_id, broad, "ALL", limit)

    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 0
        logger.error(f"Meta API HTTP {status} fetching ads for page {page_id}: {exc}")
        body = {}
        try:
            body = exc.response.json()
        except Exception:
            pass
        err_msg = body.get("error", {}).get("message", f"Meta API error {status}")
        return _response(502, {"success": False, "error": err_msg})
    except Exception as exc:
        logger.error(f"Error fetching ads for page {page_id}: {exc}", exc_info=True)
        return _response(502, {"success": False, "error": str(exc)})

    ads = [_format_ad(a) for a in raw_ads]
    # Sort by days_active descending so longest-running ads appear first
    ads.sort(key=lambda a: a.get("days_active") or 0, reverse=True)

    # ----------------------------------------------------------------
    # Compute aggregate intelligence from the fetched ad set
    # ----------------------------------------------------------------
    from datetime import timedelta

    now = datetime.now(tz=timezone.utc)
    cutoff_30d = now - timedelta(days=30)

    total_spend_min = 0
    total_spend_max = 0
    spend_30d_min = 0
    spend_30d_max = 0
    total_impressions_min = 0
    total_impressions_max = 0
    media_counts: dict = {}
    platform_counts: dict = {}
    new_last_30d = 0
    kill_days: list = []

    for ad in ads:
        # Spend
        sp = ad.get("spend") or {}
        lo = int(sp.get("lower_bound") or 0)
        hi = int(sp.get("upper_bound") or lo)
        total_spend_min += lo
        total_spend_max += hi

        # Impressions
        imp = ad.get("impressions") or {}
        total_impressions_min += int(imp.get("lower_bound") or 0)
        total_impressions_max += int(imp.get("upper_bound") or 0)

        # New in last 30 days
        start_str = ad.get("start_date")
        if start_str:
            try:
                start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                if start >= cutoff_30d:
                    new_last_30d += 1
                    spend_30d_min += lo
                    spend_30d_max += hi
            except Exception:
                pass

        # Media type distribution
        mt = (ad.get("media_type") or "OTHER").upper()
        media_counts[mt] = media_counts.get(mt, 0) + 1

        # Platform distribution
        for p in (ad.get("platforms") or []):
            platform_counts[p] = platform_counts.get(p, 0) + 1

        # Kill threshold: collect days_active for finished ads
        if not ad.get("is_active") and ad.get("days_active") is not None:
            kill_days.append(ad["days_active"])

    total = len(ads)

    media_pct = (
        {k: round(v / total * 100) for k, v in media_counts.items()}
        if total > 0 else {}
    )
    platform_pct = (
        {k: round(v / total * 100) for k, v in platform_counts.items()}
        if total > 0 else {}
    )

    kill_threshold: int | None = None
    if kill_days:
        kill_days_sorted = sorted(kill_days)
        kill_threshold = kill_days_sorted[len(kill_days_sorted) // 2]

    aggregates = {
        "total_ads_found": total,
        "new_ads_last_30d": new_last_30d,
        "spend_all_time": {"min": total_spend_min, "max": total_spend_max},
        "spend_30d": {"min": spend_30d_min, "max": spend_30d_max},
        "impressions_all_time": {"min": total_impressions_min, "max": total_impressions_max},
        "media_type_pct": media_pct,
        "platform_pct": platform_pct,
        "kill_threshold_days": kill_threshold,
    }

    return _response(200, {
        "success": True,
        "data": _group_by_variant(ads),
        "count": len(ads),
        "page_id": page_id,
        "page_name": competitor.page_name,
        "aggregates": aggregates,
    })


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

_ROUTES: dict[tuple[str, str], callable] = {
    ("POST",   "/api/competitors/resolve"):       _resolve_competitor,
    ("GET",    "/api/competitors"):               _list_competitors,
    ("POST",   "/api/competitors"):               _add_competitor,
    ("PATCH",  "/api/competitors/{page_id}"):     _update_competitor,
    ("DELETE", "/api/competitors/{page_id}"):     _remove_competitor,
    ("GET",    "/api/competitors/{page_id}/ads"): _get_competitor_ads,
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
