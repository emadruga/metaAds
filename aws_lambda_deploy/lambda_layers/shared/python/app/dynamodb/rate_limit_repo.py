"""
RateLimitRepo — hourly Meta API request-count tracking.

DynamoDB layout (single-table):
    PK  = SYSTEM
    SK  = RATE#<YYYY-MM-DDTHH>   (one item per UTC hour)
    entity_type = RATE_WINDOW
    total_requests = N           (atomic ADD counter)
    alert_sent     = bool        (True once the 80% threshold alert fired)
    ttl            = <unix_ts>   (7 days; DynamoDB auto-deletes expired items)

Methods:
    increment(hour_str, n)       → new total (int)
    get(hour_str)                → dict | None
    list_recent(hours)           → List[dict] newest-first
    mark_alert_sent(hour_str)    → None
"""

from __future__ import annotations

import time
from typing import List, Optional

from boto3.dynamodb.conditions import Key

from app.dynamodb.client import get_table

_SYSTEM_PK = "SYSTEM"
_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def _sk(hour_str: str) -> str:
    return f"RATE#{hour_str}"


class RateLimitRepo:

    @staticmethod
    def increment(hour_str: str, n: int = 1) -> int:
        """
        Atomically add *n* to the total_requests counter for the given hour.
        Creates the item if it doesn't exist yet.
        Returns the new total_requests value.
        """
        table = get_table()
        ttl = int(time.time()) + _TTL_SECONDS

        resp = table.update_item(
            Key={
                "PK": _SYSTEM_PK,
                "SK": _sk(hour_str),
            },
            UpdateExpression=(
                "SET entity_type = if_not_exists(entity_type, :et), "
                "    #ttl        = if_not_exists(#ttl, :ttl), "
                "    alert_sent  = if_not_exists(alert_sent, :false) "
                "ADD total_requests :n"
            ),
            ExpressionAttributeNames={
                "#ttl": "ttl",
            },
            ExpressionAttributeValues={
                ":et":    "RATE_WINDOW",
                ":ttl":   ttl,
                ":false": False,
                ":n":     n,
            },
            ReturnValues="UPDATED_NEW",
        )
        return int(resp["Attributes"].get("total_requests", n))

    @staticmethod
    def get(hour_str: str) -> Optional[dict]:
        """Return the RATE_WINDOW item for a specific hour, or None."""
        table = get_table()
        resp = table.get_item(
            Key={
                "PK": _SYSTEM_PK,
                "SK": _sk(hour_str),
            }
        )
        item = resp.get("Item")
        if not item:
            return None
        return {
            "hour": hour_str,
            "total_requests": int(item.get("total_requests", 0)),
            "alert_sent": bool(item.get("alert_sent", False)),
        }

    @staticmethod
    def list_recent(hours: int = 48) -> List[dict]:
        """
        Return the last *hours* RATE_WINDOW items, newest-first.
        Uses a Query on PK=SYSTEM + SK begins_with "RATE#".
        """
        table = get_table()
        resp = table.query(
            KeyConditionExpression=(
                Key("PK").eq(_SYSTEM_PK) &
                Key("SK").begins_with("RATE#")
            ),
            ScanIndexForward=False,   # Descending — ISO8601 SK sorts chronologically
            Limit=hours,
        )
        result = []
        for item in resp.get("Items", []):
            hour_str = item["SK"].replace("RATE#", "", 1)
            result.append({
                "hour": hour_str,
                "total_requests": int(item.get("total_requests", 0)),
                "alert_sent": bool(item.get("alert_sent", False)),
            })
        return result

    @staticmethod
    def mark_alert_sent(hour_str: str) -> None:
        """Set alert_sent = True for the given hour (idempotent)."""
        table = get_table()
        table.update_item(
            Key={
                "PK": _SYSTEM_PK,
                "SK": _sk(hour_str),
            },
            UpdateExpression="SET alert_sent = :true",
            ExpressionAttributeValues={":true": True},
        )
