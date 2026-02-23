"""
Page repository — merges app/models/page.py + app/models/niche_page.py.

Access patterns covered:
    get_page(page_id)                   PK=PAGE#<id>  SK=METADATA
    upsert_page(page)                   PutItem (idempotent)
    get_niche_page(niche_id, page_id)   PK=NICHE#<niche_id>  SK=PAGE#<page_id>
    upsert_niche_page(np)               UpdateItem (increments ad_count)
    list_pages_for_niche(niche_id)      PK=NICHE#<id>  SK begins_with "PAGE#"
"""

from __future__ import annotations

from typing import List, Optional

from boto3.dynamodb.conditions import Key

from app.dynamodb.client import get_table
from app.dynamodb.models import Page, NichePage
from app.utils.ids import now_iso8601


class PageRepo:

    # ------------------------------------------------------------------
    # Global page registry
    # ------------------------------------------------------------------

    @staticmethod
    def get_page(page_id: str) -> Optional[Page]:
        table = get_table()
        resp = table.get_item(
            Key={"PK": Page.pk(page_id), "SK": Page.sk()}
        )
        item = resp.get("Item")
        return Page.from_item(item) if item else None

    @staticmethod
    def upsert_page(page: Page) -> None:
        """
        Insert or update the global page registry entry.
        Preserves first_seen_at on subsequent calls.
        """
        table = get_table()
        now = now_iso8601()

        existing = PageRepo.get_page(page.page_id)
        page.first_seen_at = existing.first_seen_at if existing else now
        page.last_seen_at = now

        table.put_item(Item=page.to_item())

    # ------------------------------------------------------------------
    # Niche ↔ Page relationship
    # ------------------------------------------------------------------

    @staticmethod
    def get_niche_page(niche_id: str, page_id: str) -> Optional[NichePage]:
        table = get_table()
        resp = table.get_item(
            Key={
                "PK": NichePage.pk(niche_id),
                "SK": NichePage.sk(page_id),
            }
        )
        item = resp.get("Item")
        return NichePage.from_item(item) if item else None

    @staticmethod
    def upsert_niche_page(niche_id: str, page_id: str, page_name: str) -> NichePage:
        """
        Atomically increment the ad_count for a (niche, page) pair,
        creating the record if it does not yet exist.
        """
        table = get_table()
        now = now_iso8601()

        table.update_item(
            Key={
                "PK": NichePage.pk(niche_id),
                "SK": NichePage.sk(page_id),
            },
            UpdateExpression=(
                "SET entity_type = if_not_exists(entity_type, :etype), "
                "niche_id = if_not_exists(niche_id, :niche_id), "
                "page_id = if_not_exists(page_id, :page_id), "
                "page_name = :page_name, "
                "is_competitor = if_not_exists(is_competitor, :false), "
                "first_seen_at = if_not_exists(first_seen_at, :now), "
                "last_seen_at = :now "
                "ADD ad_count :one"
            ),
            ExpressionAttributeValues={
                ":etype": "NICHE_PAGE",
                ":niche_id": niche_id,
                ":page_id": page_id,
                ":page_name": page_name,
                ":false": False,
                ":now": now,
                ":one": 1,
            },
        )

        return PageRepo.get_niche_page(niche_id, page_id)

    @staticmethod
    def list_pages_for_niche(niche_id: str) -> List[NichePage]:
        """Return all pages that have appeared in a niche's ad collection."""
        table = get_table()
        resp = table.query(
            KeyConditionExpression=(
                Key("PK").eq(NichePage.pk(niche_id)) &
                Key("SK").begins_with("PAGE#")
            ),
        )
        return [NichePage.from_item(i) for i in resp.get("Items", [])]

    @staticmethod
    def set_competitor(niche_id: str, page_id: str, is_competitor: bool) -> None:
        """Toggle the competitor flag for a page within a niche."""
        table = get_table()
        table.update_item(
            Key={
                "PK": NichePage.pk(niche_id),
                "SK": NichePage.sk(page_id),
            },
            UpdateExpression="SET is_competitor = :val",
            ExpressionAttributeValues={":val": is_competitor},
        )
