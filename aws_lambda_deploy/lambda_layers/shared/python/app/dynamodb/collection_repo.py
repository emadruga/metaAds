"""
CollectionRun repository — replaces app/models/collection_run.py.

Access patterns covered:
    create(run)                     PutItem
    get(niche_id, run_id)           base table scan by SK prefix (RUN#<ts>#<id>)
    list_for_niche(niche_id)        PK=NICHE#<id>  SK begins_with "RUN#"
    mark_running(niche_id, run_id)  UpdateItem status → running
    mark_completed(...)             UpdateItem status → completed + stats
    mark_error(...)                 UpdateItem status → error + message
"""

from __future__ import annotations

from typing import List, Optional

from boto3.dynamodb.conditions import Attr, Key

from app.dynamodb.client import get_table
from app.dynamodb.models import CollectionRun
from app.utils.ids import now_iso8601


def _cutoff_iso(hours: int) -> str:
    """Return ISO8601 timestamp *hours* ago (UTC)."""
    from datetime import datetime, timezone, timedelta
    return (datetime.now(tz=timezone.utc) - timedelta(hours=hours)).isoformat()


class CollectionRepo:

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def get(niche_id: str, run_id: str) -> Optional[CollectionRun]:
        """
        Find a CollectionRun by niche_id + run_id.

        Because the SK is RUN#<started_at>#<run_id> we query with a
        FilterExpression on the id attribute rather than doing a full Scan.
        """
        table = get_table()
        resp = table.query(
            KeyConditionExpression=(
                Key("PK").eq(CollectionRun.pk(niche_id)) &
                Key("SK").begins_with("RUN#")
            ),
            FilterExpression=Attr("id").eq(run_id),
        )
        items = resp.get("Items", [])
        return CollectionRun.from_item(items[0]) if items else None

    @staticmethod
    def list_for_niche(niche_id: str, limit: int = 20) -> List[CollectionRun]:
        """Return the most recent collection runs for a niche (newest first)."""
        table = get_table()
        resp = table.query(
            KeyConditionExpression=(
                Key("PK").eq(CollectionRun.pk(niche_id)) &
                Key("SK").begins_with("RUN#")
            ),
            ScanIndexForward=False,   # Descending — ISO8601 SK sorts chronologically
            Limit=limit,
        )
        return [CollectionRun.from_item(i) for i in resp.get("Items", [])]

    @staticmethod
    def get_latest_for_niche(niche_id: str) -> Optional[CollectionRun]:
        """Return the single most recent CollectionRun for a niche, or None."""
        runs = CollectionRepo.list_for_niche(niche_id, limit=1)
        return runs[0] if runs else None

    @staticmethod
    def list_recent_global(hours: int = 24, limit: int = 100) -> List[CollectionRun]:
        """
        Return the most recent CollectionRuns across ALL niches/users.
        Uses a DynamoDB Scan with FilterExpression — intended for admin use only.
        Results are sorted newest-first by started_at.
        """
        table = get_table()
        cutoff = _cutoff_iso(hours)

        filter_expr = (
            Attr("entity_type").eq("COLLECTION_RUN") &
            Attr("started_at").gte(cutoff)
        )

        runs: List[CollectionRun] = []
        scan_kwargs = {
            "FilterExpression": filter_expr,
            "Limit": 1000,   # DynamoDB page size; we filter client-side down to *limit*
        }

        while True:
            resp = table.scan(**scan_kwargs)
            for item in resp.get("Items", []):
                try:
                    runs.append(CollectionRun.from_item(item))
                except Exception:
                    pass

            if "LastEvaluatedKey" not in resp or len(runs) >= limit * 5:
                break
            scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

        # Sort newest-first and cap
        runs.sort(key=lambda r: r.started_at or "", reverse=True)
        return runs[:limit]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def create(run: CollectionRun) -> CollectionRun:
        """Insert a new CollectionRun with status=pending."""
        table = get_table()
        run.started_at = run.started_at or now_iso8601()
        run.status = "pending"
        table.put_item(Item=run.to_item())
        return run

    @staticmethod
    def _update_status(
        niche_id: str,
        run_id: str,
        started_at: str,
        status: str,
        extra_updates: Optional[dict] = None,
    ) -> None:
        """Internal helper: UpdateItem on the known PK + SK."""
        table = get_table()
        updates = {"#s": status, **(extra_updates or {})}

        set_parts = ["#status = :status"]
        expr_names = {"#status": "status"}
        expr_values = {":status": status}

        if extra_updates:
            for k, v in extra_updates.items():
                set_parts.append(f"#{k} = :{k}")
                expr_names[f"#{k}"] = k
                expr_values[f":{k}"] = v

        table.update_item(
            Key={
                "PK": CollectionRun.pk(niche_id),
                "SK": CollectionRun.sk(started_at, run_id),
            },
            UpdateExpression="SET " + ", ".join(set_parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

    @staticmethod
    def mark_running(niche_id: str, run_id: str, started_at: str) -> None:
        CollectionRepo._update_status(niche_id, run_id, started_at, "running")

    @staticmethod
    def mark_completed(
        niche_id: str,
        run_id: str,
        started_at: str,
        ads_found: int,
        ads_new: int,
        ads_updated: int,
        total_ads_after: int = 0,
        api_requests_made: int = 0,
    ) -> None:
        CollectionRepo._update_status(
            niche_id,
            run_id,
            started_at,
            "completed",
            extra_updates={
                "ads_found": ads_found,
                "ads_new": ads_new,
                "ads_updated": ads_updated,
                "total_ads_after": total_ads_after,
                "api_requests_made": api_requests_made,
                "completed_at": now_iso8601(),
            },
        )

    @staticmethod
    def mark_error(
        niche_id: str,
        run_id: str,
        started_at: str,
        error_message: str,
    ) -> None:
        CollectionRepo._update_status(
            niche_id,
            run_id,
            started_at,
            "error",
            extra_updates={
                "error_message": error_message,
                "completed_at": now_iso8601(),
            },
        )
