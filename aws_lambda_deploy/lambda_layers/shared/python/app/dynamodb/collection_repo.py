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
