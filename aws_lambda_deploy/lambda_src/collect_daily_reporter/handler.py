"""
Daily Collection Reporter Lambda.

Triggered daily at 23:00 UTC (= 20:00 BRT) by EventBridge Scheduler.
Aggregates the last 24 hours of collection activity and rate-limit usage,
then publishes a formatted plain-text email report to the SNS alarms topic.

Environment variables:
    DYNAMODB_TABLE      — DynamoDB table name
    SNS_ALARM_TOPIC_ARN — SNS topic ARN for email alerts
    AWS_REGION          — injected by Lambda runtime
"""

from __future__ import annotations

import logging
import os
from collections import Counter
from datetime import datetime, timezone, timedelta

import boto3

from app.dynamodb.collection_repo import CollectionRepo
from app.dynamodb.rate_limit_repo import RateLimitRepo

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

def handler(event: dict, context) -> dict:
    """EventBridge Scheduler entry point — no HTTP response needed."""
    topic_arn = os.environ.get("SNS_ALARM_TOPIC_ARN")
    if not topic_arn:
        logger.warning("SNS_ALARM_TOPIC_ARN not set; daily report skipped")
        return {"status": "skipped", "reason": "no SNS topic"}

    report = _build_report()
    _publish(topic_arn, report)

    logger.info("Daily report published successfully")
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _build_report() -> str:
    today_utc = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    lines: list[str] = []

    lines.append(f"MetaAds Daily Report — {today_utc}")
    lines.append("=" * 50)
    lines.append("")

    # ---- Rate-limit section ----
    windows = RateLimitRepo.list_recent(hours=24)
    if windows:
        total_requests = sum(w["total_requests"] for w in windows)
        peak_window = max(windows, key=lambda w: w["total_requests"])
        alerts_fired = sum(1 for w in windows if w.get("alert_sent"))
        quota = 200 * 24  # 200/hr × 24h

        lines.append("RATE LIMIT USAGE (last 24h)")
        lines.append(f"  Peak hour: {peak_window['hour']} UTC — {peak_window['total_requests']} requests")
        lines.append(f"  Total requests: {total_requests} / {quota} quota")
        lines.append(f"  Alert threshold crossings: {alerts_fired}")
    else:
        lines.append("RATE LIMIT USAGE (last 24h)")
        lines.append("  No data recorded.")
    lines.append("")

    # ---- Collection summary section ----
    runs = CollectionRepo.list_recent_global(hours=24, limit=500)

    total_runs = len(runs)
    completed   = [r for r in runs if r.status == "completed"]
    failed      = [r for r in runs if r.status in ("error", "failed")]
    running     = [r for r in runs if r.status == "running"]

    ads_found   = sum(r.ads_found   or 0 for r in completed)
    ads_new     = sum(r.ads_new     or 0 for r in completed)
    ads_updated = sum(r.ads_updated or 0 for r in completed)

    lines.append("COLLECTION SUMMARY")
    lines.append(f"  Total runs:    {total_runs}  "
                 f"({len(completed)} completed, {len(failed)} failed, {len(running)} running)")
    lines.append(f"  Ads found:     {ads_found:,}")
    lines.append(f"  New ads:       {ads_new:,}")
    lines.append(f"  Updated ads:   {ads_updated:,}")
    lines.append("")

    # ---- Top keywords ----
    kw_counter: Counter = Counter()
    kw_ads: Counter = Counter()
    for r in completed:
        kw = r.keywords_used[0] if r.keywords_used else "(unknown)"
        kw_counter[kw] += 1
        kw_ads[kw] += r.ads_found or 0

    if kw_counter:
        lines.append("TOP KEYWORDS (by runs)")
        for kw, count in kw_counter.most_common(5):
            lines.append(f"  \"{kw}\" — {count} runs, {kw_ads[kw]:,} ads found")
    lines.append("")

    # ---- Errors ----
    if failed:
        lines.append(f"ERRORS (last 24h) — {len(failed)} run(s) failed")
        for r in failed[:10]:
            ts = (r.started_at or "?")[:16].replace("T", " ")
            kw = r.keywords_used[0] if r.keywords_used else "?"
            msg = (r.error_message or "no message")[:120]
            lines.append(f"  {ts} UTC — keyword={kw!r} — {msg}")
        if len(failed) > 10:
            lines.append(f"  ...and {len(failed) - 10} more")
    else:
        lines.append("ERRORS (last 24h)")
        lines.append("  None")
    lines.append("")

    lines.append("=" * 50)
    return "\n".join(lines)


def _publish(topic_arn: str, message: str) -> None:
    today_utc = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    region = os.environ.get("AWS_REGION", "us-east-1")
    sns = boto3.client("sns", region_name=region)
    sns.publish(
        TopicArn=topic_arn,
        Subject=f"[MetaAds] Daily Report — {today_utc}",
        Message=message,
    )
    logger.info(f"Published daily report to {topic_arn}")
