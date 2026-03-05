"""
Collect Worker Lambda handler — runs up to 15 minutes.

Invoked asynchronously by collect_trigger (InvocationType="Event").
NOT exposed through API Gateway.

Responsibilities:
    1. Mark run as "running"
    2. Fetch Meta API token from Secrets Manager
    3. Call MetaAdLibraryAPI.search_ads()
    4. Parse each raw ad with AdParser
    5. Upsert each ad + page/niche_page via DynamoDB repos
    6. Mark run as "completed" (or "error" on failure)

Environment variables:
    DYNAMODB_TABLE   — DynamoDB table name
    SECRETS_NAME     — e.g. metaads/dev/meta-api
    AWS_REGION       — injected by Lambda runtime

Input event (JSON payload from collect_trigger):
    {
        "niche_id":   str,
        "run_id":     str,
        "started_at": str (ISO8601),
        "keyword":    str,
        "limit":      int,
        "countries":  list[str],
        "platforms":  list[str],
    }
"""

from __future__ import annotations

import json
import logging
import os
import time

import boto3
from datetime import datetime, timezone

from app.dynamodb.ad_repo import AdRepo
from app.dynamodb.collection_repo import CollectionRepo
from app.dynamodb.page_repo import PageRepo
from app.dynamodb.rate_limit_repo import RateLimitRepo
from app.dynamodb.models import Ad, Page
from app.utils.ids import generate_uuid, now_iso8601

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Meta API credentials (cached per cold start)
# ---------------------------------------------------------------------------

_meta_secrets: dict | None = None


def _get_meta_token() -> str:
    """Fetch Meta API access_token from Secrets Manager (cached)."""
    global _meta_secrets
    if _meta_secrets is not None:
        return _meta_secrets["access_token"]

    secret_name = os.environ.get("SECRETS_NAME", "metaads/dev/meta-api")
    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("secretsmanager", region_name=region)
    resp = client.get_secret_value(SecretId=secret_name)
    _meta_secrets = json.loads(resp["SecretString"])
    return _meta_secrets["access_token"]


# ---------------------------------------------------------------------------
# Lazy import collector + parser from Lambda layer
# ---------------------------------------------------------------------------

def _get_collector(access_token: str):
    """Import MetaAdLibraryAPI from the shared layer and initialise."""
    from meta_api_collector import MetaAdLibraryAPI
    return MetaAdLibraryAPI(access_token=access_token)


def _get_parser():
    from ad_parser import AdParser
    return AdParser()


# ---------------------------------------------------------------------------
# Rate-limit alert helper
# ---------------------------------------------------------------------------

_RATE_LIMIT_ALERT_THRESHOLD = 160   # 80% of 200 req/hour
_RATE_LIMIT_MAX = 200

def _send_rate_limit_alert(new_total: int, hour_str: str) -> None:
    """Publish a rate-limit warning to SNS (best-effort)."""
    topic_arn = os.environ.get("SNS_ALARM_TOPIC_ARN")
    if not topic_arn:
        logger.warning("SNS_ALARM_TOPIC_ARN not set; skipping rate-limit alert")
        return
    try:
        region = os.environ.get("AWS_REGION", "us-east-1")
        sns = boto3.client("sns", region_name=region)
        message = (
            f"MetaAds Rate Limit Warning\n\n"
            f"Hour: {hour_str} UTC\n"
            f"Requests used: {new_total} / {_RATE_LIMIT_MAX} (80% threshold reached)\n\n"
            f"Remaining capacity: {_RATE_LIMIT_MAX - new_total} requests\n"
            f"If this pace continues you may hit the hard limit before the hour resets."
        )
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"[MetaAds] Rate limit at {new_total}/{_RATE_LIMIT_MAX} — hour {hour_str}",
            Message=message,
        )
        logger.info(f"Rate-limit alert published to SNS: {new_total}/{_RATE_LIMIT_MAX} for hour {hour_str}")
    except Exception as exc:
        logger.error(f"Failed to publish SNS rate-limit alert: {exc}")


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

def handler(event: dict, context) -> None:
    """
    Collection worker — no HTTP response needed (async invocation).
    Logs progress; updates CollectionRun status in DynamoDB.
    """
    niche_id   = event.get("niche_id", "")
    run_id     = event.get("run_id", "")
    started_at = event.get("started_at", now_iso8601())
    keyword    = event.get("keyword", "")
    limit      = int(event.get("limit", 50))
    countries  = event.get("countries") or ["US"]
    platforms  = event.get("platforms") or ["instagram"]

    logger.info(
        f"collect_worker started: niche={niche_id} run={run_id} "
        f"keyword={keyword!r} limit={limit}"
    )

    # Mark run as running
    try:
        CollectionRepo.mark_running(niche_id, run_id, started_at)
    except Exception as exc:
        logger.error(f"Failed to mark run as running: {exc}")
        return

    ads_found        = 0
    ads_new          = 0
    ads_updated      = 0
    api_requests_made = 0

    try:
        # Fetch Meta API token
        access_token = _get_meta_token()
        api = _get_collector(access_token)
        parser = _get_parser()

        logger.info(f"Calling Meta API: search_terms={keyword!r} countries={countries} platforms={platforms}")
        raw_ads, api_requests_made = api.search_ads(
            search_terms=keyword,
            countries=countries,
            platforms=platforms,
            limit=limit,
        )
        ads_found = len(raw_ads)
        logger.info(f"Meta API returned {ads_found} ads (requests_made={api_requests_made})")

        # Process each raw ad
        for raw in raw_ads:
            try:
                parsed = parser.parse_ad(raw)

                # Map parsed dict → Ad dataclass
                ad = Ad(
                    id=generate_uuid(),
                    niche_id=niche_id,
                    meta_ad_id=parsed.get("ad_id") or raw.get("id", ""),
                    page_id=parsed.get("page_id") or None,
                    page_name=parsed.get("page_name") or "",
                    start_date=_dt_str(parsed.get("start_date")),
                    end_date=_dt_str(parsed.get("end_date")),
                    is_active=parsed.get("is_active", True),
                    days_active=parsed.get("days_active"),
                    collected_at=now_iso8601(),
                    platforms=_ensure_list(parsed.get("platforms")),
                    country_codes=countries,
                    snapshot_url=parsed.get("snapshot_url") or "",
                    body=parsed.get("body") or "",
                    headline=parsed.get("headline") or "",
                    description=parsed.get("description") or "",
                    link_caption=parsed.get("link_caption") or "",
                    full_text=parsed.get("full_text") or "",
                    text_length=parsed.get("text_length") or 0,
                    has_emoji=parsed.get("has_emoji") or False,
                    has_hashtags=parsed.get("has_hashtags") or False,
                    hashtags=parsed.get("hashtags") or [],
                    mentions=parsed.get("mentions") or [],
                    cta_detected=parsed.get("cta_detected") or None,
                    creative_type="image",
                    creatives=[],
                    is_saved=False,
                    saved_at=None,
                    saved_tags=[],
                    search_keyword=keyword,
                )

                _, is_new = AdRepo.create_or_update(ad)

                if is_new:
                    ads_new += 1
                    # Upsert page registry + niche-page link
                    if ad.page_id:
                        page = Page(
                            page_id=ad.page_id,
                            page_name=ad.page_name,
                            first_seen_at=now_iso8601(),
                            last_seen_at=now_iso8601(),
                        )
                        PageRepo.upsert_page(page)
                        PageRepo.upsert_niche_page(
                            niche_id=niche_id,
                            page_id=ad.page_id,
                            page_name=ad.page_name,
                        )
                else:
                    ads_updated += 1

            except Exception as exc:
                logger.warning(f"Failed to process ad {raw.get('id', '?')}: {exc}", exc_info=True)
                # Continue with remaining ads

        # Count total ads in the niche after this run
        total_ads_after = AdRepo.count_for_niche(niche_id)

        # Mark run completed
        CollectionRepo.mark_completed(
            niche_id=niche_id,
            run_id=run_id,
            started_at=started_at,
            ads_found=ads_found,
            ads_new=ads_new,
            ads_updated=ads_updated,
            total_ads_after=total_ads_after,
            api_requests_made=api_requests_made,
        )
        logger.info(
            f"collect_worker completed: run={run_id} "
            f"found={ads_found} new={ads_new} updated={ads_updated} "
            f"api_requests={api_requests_made}"
        )

        # Update hourly rate-limit counter and fire alert if threshold reached
        if api_requests_made > 0:
            try:
                hour_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
                new_total = RateLimitRepo.increment(hour_str, api_requests_made)
                logger.info(f"Rate-limit counter: {new_total}/{_RATE_LIMIT_MAX} for hour {hour_str}")

                if new_total >= _RATE_LIMIT_ALERT_THRESHOLD:
                    window = RateLimitRepo.get(hour_str)
                    if window and not window.get("alert_sent"):
                        RateLimitRepo.mark_alert_sent(hour_str)
                        _send_rate_limit_alert(new_total, hour_str)
            except Exception as exc:
                logger.error(f"Failed to update rate-limit counter: {exc}")

    except Exception as exc:
        logger.error(f"collect_worker fatal error: {exc}", exc_info=True)
        try:
            CollectionRepo.mark_error(niche_id, run_id, started_at, str(exc))
        except Exception as inner:
            logger.error(f"Failed to mark run as error: {inner}")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _dt_str(dt) -> str | None:
    """Convert datetime → ISO8601 string, or pass through if already a string."""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt if dt.endswith("Z") else dt + "Z"
    # datetime object
    return dt.isoformat() + "Z"


def _ensure_list(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [value]
        except (json.JSONDecodeError, ValueError):
            return [value] if value else []
    return []
