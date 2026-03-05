"""
RateLimitRepo — per-hour Meta API request counter.

DynamoDB item schema:
    PK            = SYSTEM
    SK            = RATE#<YYYY-MM-DDTHH>   (UTC hour, e.g. RATE#2026-03-05T14)
    entity_type   = RATE_WINDOW
    total_requests = N                      (atomic counter)
    alert_sent    = BOOL                    (flag: SNS alert already fired)
    ttl           = N                       (Unix timestamp 7 days out; auto-expire)

Access patterns:
    increment(hour_str, n)         ADD total_requests atomically, return new total
    get(hour_str)                  GetItem → dict or None
    list_recent(hours)             Query PK=SYSTEM SK begins_with RATE# descending
    mark_alert_sent(hour_str)      SET alert_sent = True
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from boto3.dynamodb.conditions import Key

from app.dynamodb.client import get_table

_SYSTEM_PK = "SYSTEM"
_SK_PREFIX = "RATE#"
_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def _sk(hour_str: str) -> str:
    return f"{_SK_PREFIX}{hour_str}"


class RateLimitRepo:

    @staticmethod
    def increment(hour_str: str, n: int) -> int:
        """
        Atomically add *n* to total_requests for the given UTC hour.
        Creates the item if it does not exist (ADD is idempotent on missing items).
        Returns the new total_requests value.
        """
        table = get_table()
        ttl = int(time.time()) + _TTL_SECONDS

        resp = table.update_item(
            Key={"PK": _SYSTEM_PK, "SK": _sk(hour_str)},
            UpdateExpression=(
                "SET entity_type = if_not_exists(entity_type, :et), "
                "    alert_sent  = if_not_exists(alert_sent,  :f), "
                "    #ttl        = if_not_exists(#ttl,        :ttl) "
                "ADD total_requests :n"
            ),
            ExpressionAttributeNames={"#ttl": "ttl"},
            ExpressionAttributeValues={
                ":et":  "RATE_WINDOW",
                ":f":   False,
                ":ttl": ttl,
                ":n":   n,
            },
            ReturnValues="UPDATED_NEW",
        )
        return int(resp["Attributes"].get("total_requests", n))

    @staticmethod
    def get(hour_str: str) -> Optional[Dict]:
        """Return the raw item dict for the given hour, or None."""
        table = get_table()
        resp = table.get_item(Key={"PK": _SYSTEM_PK, "SK": _sk(hour_str)})
        item = resp.get("Item")
        if not item:
            return None
        return {
            "hour":            hour_str,
            "total_requests":  int(item.get("total_requests", 0)),
            "alert_sent":      bool(item.get("alert_sent", False)),
        }

    @staticmethod
    def list_recent(hours: int = 48) -> List[Dict]:
        """
        Return up to *hours* most-recent hourly windows (newest first).
        Uses a Query on PK=SYSTEM SK begins_with RATE# descending.
        """
        table = get_table()
        resp = table.query(
            KeyConditionExpression=(
                Key("PK").eq(_SYSTEM_PK) &
                Key("SK").begins_with(_SK_PREFIX)
            ),
            ScanIndexForward=False,
            Limit=hours,
        )
        result = []
        for item in resp.get("Items", []):
            sk = item.get("SK", "")
            hour_str = sk.removeprefix(_SK_PREFIX)
            result.append({
                "hour":           hour_str,
                "total_requests": int(item.get("total_requests", 0)),
                "alert_sent":     bool(item.get("alert_sent", False)),
            })
        return result

    @staticmethod
    def mark_alert_sent(hour_str: str) -> None:
        """Set alert_sent = True for the given hour (idempotent)."""
        table = get_table()
        table.update_item(
            Key={"PK": _SYSTEM_PK, "SK": _sk(hour_str)},
            UpdateExpression="SET alert_sent = :t",
            ExpressionAttributeValues={":t": True},
        )
