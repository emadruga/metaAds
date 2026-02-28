"""
Collect Scheduler Lambda handler.

Triggered by EventBridge Scheduler on a cron(0 */3 * * ? *) schedule
(every 3 hours).  For each niche that has auto_collect_enabled=True:

  1. Check the most recent CollectionRun's completed_at timestamp.
  2. Skip if the run completed less than auto_collect_interval_hours ago.
  3. For every keyword in the niche, create one CollectionRun (status=pending)
     and async-invoke collect_worker (fan-out, one invocation per keyword).

Design decisions:
  - Bypasses collect_trigger (HTTP handler) — creates CollectionRun directly.
  - One collect_worker per keyword (Issue #3 Option A) for independent retries.
  - No loading spinner / loading state — silent background operation.

Environment variables:
    DYNAMODB_TABLE       — DynamoDB table name
    COLLECT_WORKER_ARN   — ARN of the collect_worker Lambda
    AWS_REGION           — injected by Lambda runtime
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone, timedelta

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

def _should_collect(niche, latest_run) -> bool:
    """
    Return True if the niche is due for a new collection.

    Rules:
    - No previous run → always collect.
    - Latest run has no completed_at (still running / errored without ts) → skip
      to avoid overlapping runs.
    - Latest run completed_at is older than interval_hours → collect.
    """
    if latest_run is None:
        return True

    completed_at = latest_run.completed_at
    if not completed_at:
        # Run never finished — don't start another one yet
        logger.info(
            f"Niche {niche.id} has an in-flight or incomplete run "
            f"(run_id={latest_run.id}), skipping."
        )
        return False

    # Use started_at (not completed_at) for the interval calculation.
    # The worker completes 1-2 min after the EventBridge fire, so
    # completed_at + interval pushes due_at just past the next fire,
    # causing every other 3h tick to be skipped (effective 6h cadence).
    # started_at is set at fire time, so due_at aligns exactly with
    # the next EventBridge tick.
    ref_ts_str = latest_run.started_at or completed_at
    try:
        last_ts = datetime.fromisoformat(ref_ts_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        logger.warning(
            f"Could not parse started_at={ref_ts_str!r} for niche {niche.id}; "
            "scheduling collection anyway."
        )
        return True

    interval = timedelta(hours=niche.auto_collect_interval_hours)
    due_at = last_ts + interval
    now = datetime.now(tz=timezone.utc)

    if now >= due_at:
        return True

    logger.info(
        f"Niche {niche.id} is not yet due (next at {due_at.isoformat()})."
    )
    return False


def _invoke_worker(lambda_client, worker_arn: str, payload: dict) -> None:
    """Fire-and-forget async invocation of collect_worker."""
    lambda_client.invoke(
        FunctionName=worker_arn,
        InvocationType="Event",
        Payload=json.dumps(payload).encode(),
    )


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

def handler(event: dict, context) -> dict:
    """
    EventBridge Scheduler entry point.

    Returns a summary dict (not used by EventBridge but useful for logs).
    """
    worker_arn = os.environ.get("COLLECT_WORKER_ARN")
    if not worker_arn:
        logger.error("COLLECT_WORKER_ARN environment variable not set")
        raise RuntimeError("COLLECT_WORKER_ARN not configured")

    region = os.environ.get("AWS_REGION", "us-east-1")
    lambda_client = boto3.client("lambda", region_name=region)

    niches = NicheRepo.list_all_with_auto_collect()
    logger.info(f"Found {len(niches)} niche(s) with auto_collect_enabled=True")

    total_invocations = 0
    total_skipped = 0

    for niche in niches:
        if not niche.keywords:
            logger.info(f"Niche {niche.id} has no keywords, skipping.")
            total_skipped += 1
            continue

        latest_run = CollectionRepo.get_latest_for_niche(niche.id)

        if not _should_collect(niche, latest_run):
            total_skipped += 1
            continue

        logger.info(
            f"Scheduling collection for niche {niche.id} "
            f"({len(niche.keywords)} keyword(s))."
        )

        for keyword in niche.keywords:
            run_id = generate_uuid()
            started_at = now_iso8601()

            run = CollectionRun(
                id=run_id,
                niche_id=niche.id,
                status="pending",
                keywords_used=[keyword],
                ads_found=0,
                ads_new=0,
                ads_updated=0,
                limit_requested=50,
                countries=niche.countries or ["US"],
                error_message=None,
                started_at=started_at,
                completed_at=None,
            )
            CollectionRepo.create(run)
            logger.info(
                f"Created CollectionRun run_id={run_id} "
                f"niche={niche.id} keyword={keyword!r}"
            )

            payload = {
                "niche_id": niche.id,
                "run_id": run_id,
                "started_at": started_at,
                "keyword": keyword,
                "limit": 50,
                "countries": niche.countries or ["US"],
                "platforms": niche.platforms or ["instagram"],
            }

            try:
                _invoke_worker(lambda_client, worker_arn, payload)
                logger.info(f"Invoked collect_worker for run {run_id}")
                total_invocations += 1
            except Exception as exc:
                logger.error(
                    f"Failed to invoke collect_worker for run {run_id}: {exc}",
                    exc_info=True,
                )
                CollectionRepo.mark_error(
                    niche.id, run_id, started_at, f"Invoke failed: {exc}"
                )

    summary = {
        "niches_found": len(niches),
        "invocations": total_invocations,
        "skipped": total_skipped,
    }
    logger.info(f"Scheduler complete: {summary}")
    return summary
