"""
Niche repository — replaces app/services/niche_service.py + app/models/niche.py.

Access patterns covered:
    list_for_user(user_id)      PK=USER#<id>  SK begins_with("NICHE#")
    get(niche_id)               GSI1: GSI1PK=NICHE#<id>  GSI1SK=METADATA
    get_by_slug(user_id, slug)  GSI2: GSI2PK=USER_SLUG#<uid>#<slug>
    create(niche)               PutItem (slug uniqueness via condition)
    update(niche_id, **kwargs)  UpdateItem
    delete(user_id, niche_id)   DeleteItem
    get_stats(niche_id)         aggregates counts from Ads + CollectionRuns
"""

from __future__ import annotations

from typing import List, Optional

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from app.dynamodb.client import get_table, GSI1, GSI2
from app.dynamodb.models import Niche
from app.utils.ids import now_iso8601


class NicheRepo:

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def list_for_user(user_id: str) -> List[Niche]:
        """Return all niches belonging to user_id (base table query)."""
        table = get_table()
        resp = table.query(
            KeyConditionExpression=(
                Key("PK").eq(Niche.pk(user_id)) &
                Key("SK").begins_with("NICHE#")
            ),
        )
        return [Niche.from_item(i) for i in resp.get("Items", [])
                if i.get("is_active", True)]

    @staticmethod
    def get(niche_id: str) -> Optional[Niche]:
        """Look up a niche by its UUID via GSI1."""
        table = get_table()
        resp = table.query(
            IndexName=GSI1,
            KeyConditionExpression=(
                Key("GSI1PK").eq(f"NICHE#{niche_id}") &
                Key("GSI1SK").eq("METADATA")
            ),
            Limit=1,
        )
        items = resp.get("Items", [])
        return Niche.from_item(items[0]) if items else None

    @staticmethod
    def get_by_slug(user_id: str, slug: str) -> Optional[Niche]:
        """Look up a niche by (user_id, slug) — enforces uniqueness per user."""
        table = get_table()
        resp = table.query(
            IndexName=GSI2,
            KeyConditionExpression=(
                Key("GSI2PK").eq(f"USER_SLUG#{user_id}#{slug}") &
                Key("GSI2SK").eq("METADATA")
            ),
            Limit=1,
        )
        items = resp.get("Items", [])
        return Niche.from_item(items[0]) if items else None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def create(niche: Niche) -> Niche:
        """
        Insert a new Niche.

        Raises ValueError if the (user_id, slug) combination already exists
        (checked via GSI2 before write — eventual consistency is acceptable
        here because slug collisions are rare and caught on the second write).
        """
        table = get_table()
        now = now_iso8601()
        niche.created_at = niche.created_at or now
        niche.updated_at = now

        # Proactively check slug uniqueness
        if NicheRepo.get_by_slug(niche.user_id, niche.slug):
            raise ValueError(
                f"A niche with slug '{niche.slug}' already exists for this user"
            )

        try:
            table.put_item(
                Item=niche.to_item(),
                ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ValueError(f"Niche {niche.id} already exists") from exc
            raise

        return niche

    @staticmethod
    def update(niche_id: str, user_id: str, **kwargs) -> Optional[Niche]:
        """
        Update specific fields.  Accepted kwargs:
            name, description, keywords, countries, platforms, is_active
        Note: slug is intentionally NOT updatable (would break bookmarks).
        """
        table = get_table()

        niche = NicheRepo.get(niche_id)
        if not niche or niche.user_id != user_id:
            return None

        allowed = {"name", "description", "keywords", "countries", "platforms", "is_active",
                   "auto_collect_enabled", "auto_collect_interval_hours"}
        import json
        updates: dict = {}
        for k, v in kwargs.items():
            if k not in allowed:
                continue
            # Serialise list fields to JSON string
            updates[k] = json.dumps(v) if isinstance(v, list) else v

        if not updates:
            return niche

        updates["updated_at"] = now_iso8601()

        expr_parts = [f"#{k} = :{k}" for k in updates]
        update_expr = "SET " + ", ".join(expr_parts)
        expr_names = {f"#{k}": k for k in updates}
        expr_values = {f":{k}": v for k, v in updates.items()}

        table.update_item(
            Key={"PK": Niche.pk(user_id), "SK": Niche.sk(niche_id)},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

        return NicheRepo.get(niche_id)

    @staticmethod
    def delete(user_id: str, niche_id: str) -> bool:
        """
        Soft-delete a niche (is_active=False).
        Returns True if found and deleted, False if not found.
        """
        niche = NicheRepo.get(niche_id)
        if not niche or niche.user_id != user_id:
            return False

        NicheRepo.update(niche_id, user_id, is_active=False)
        return True

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @staticmethod
    def get_stats(niche_id: str) -> dict:
        """
        Compute lightweight stats for a niche dashboard card.

        Queries:
          - AD items  (PK=NICHE#<id>, SK begins_with "AD#")
          - PAGE items (PK=NICHE#<id>, SK begins_with "PAGE#")
          - RUN items  (PK=NICHE#<id>, SK begins_with "RUN#")
        """
        table = get_table()
        pk = f"NICHE#{niche_id}"

        def _query(sk_prefix: str, projection: str) -> list:
            items = []
            kwargs = dict(
                KeyConditionExpression=(
                    Key("PK").eq(pk) & Key("SK").begins_with(sk_prefix)
                ),
                ProjectionExpression=projection,
            )
            while True:
                resp = table.query(**kwargs)
                items.extend(resp.get("Items", []))
                last_key = resp.get("LastEvaluatedKey")
                if not last_key:
                    break
                kwargs["ExclusiveStartKey"] = last_key
            return items

        ads = _query("AD#", "is_active, is_saved, days_active")
        pages = _query("PAGE#", "page_id")

        # Need ExpressionAttributeNames for reserved word 'status'
        resp_runs = table.query(
            KeyConditionExpression=(
                Key("PK").eq(pk) & Key("SK").begins_with("RUN#")
            ),
            ProjectionExpression="#s, completed_at, ads_found",
            ExpressionAttributeNames={"#s": "status"},
            ScanIndexForward=False,  # Most recent first
            Limit=10,
        )
        runs = resp_runs.get("Items", [])

        total_ads = len(ads)
        active_ads = sum(1 for a in ads if a.get("is_active"))
        saved_ads = sum(1 for a in ads if a.get("is_saved"))
        avg_days = (
            sum(a.get("days_active") or 0 for a in ads) / total_ads
            if total_ads else 0
        )

        last_run = runs[0] if runs else None

        return {
            "total_ads": total_ads,
            "active_ads": active_ads,
            "saved_ads": saved_ads,
            "unique_pages": len(pages),
            "avg_days_active": round(avg_days, 1),
            "last_collection": {
                "status": last_run.get("status") if last_run else None,
                "completed_at": last_run.get("completed_at") if last_run else None,
                "ads_found": last_run.get("ads_found", 0) if last_run else 0,
            },
        }
