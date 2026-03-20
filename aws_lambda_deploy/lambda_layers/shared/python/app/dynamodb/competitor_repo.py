"""
Competitor repository — CRUD for tracked competitor advertiser pages.

Access patterns:
    list_for_user(user_id)       PK=USER#<id>  SK begins_with("COMPETITOR#")
    get(user_id, page_id)        GetItem PK=USER#<id>  SK=COMPETITOR#<page_id>
    create(competitor)           PutItem
    delete(user_id, page_id)     DeleteItem
"""

from __future__ import annotations

from typing import List, Optional

from boto3.dynamodb.conditions import Key

from app.dynamodb.client import get_table
from app.dynamodb.models import Competitor, CompetitorScrapeCache
from app.utils.ids import now_iso8601


class CompetitorRepo:

    @staticmethod
    def list_for_user(user_id: str) -> List[Competitor]:
        """Return all competitor pages tracked by this user."""
        table = get_table()
        resp = table.query(
            KeyConditionExpression=(
                Key("PK").eq(Competitor.pk(user_id)) &
                Key("SK").begins_with("COMPETITOR#")
            ),
        )
        return [Competitor.from_item(i) for i in resp.get("Items", [])]

    @staticmethod
    def get(user_id: str, page_id: str) -> Optional[Competitor]:
        """Fetch a single competitor by page_id."""
        table = get_table()
        resp = table.get_item(
            Key={
                "PK": Competitor.pk(user_id),
                "SK": Competitor.sk(page_id),
            }
        )
        item = resp.get("Item")
        return Competitor.from_item(item) if item else None

    @staticmethod
    def create(competitor: Competitor) -> Competitor:
        """Insert a new competitor record."""
        table = get_table()
        if not competitor.added_at:
            competitor.added_at = now_iso8601()
        table.put_item(Item=competitor.to_item())
        return competitor

    @staticmethod
    def update_notes(user_id: str, page_id: str, notes: str) -> bool:
        """Update the notes field for a competitor."""
        table = get_table()
        table.update_item(
            Key={
                "PK": Competitor.pk(user_id),
                "SK": Competitor.sk(page_id),
            },
            UpdateExpression="SET #notes = :notes",
            ExpressionAttributeNames={"#notes": "notes"},
            ExpressionAttributeValues={":notes": notes},
        )
        return True

    @staticmethod
    def update_profile(
        user_id: str,
        page_id: str,
        *,
        fan_count: int | None = None,
        category: str = "",
        about: str = "",
    ) -> bool:
        """Update page-profile metadata (fan_count, category, about)."""
        table = get_table()
        table.update_item(
            Key={
                "PK": Competitor.pk(user_id),
                "SK": Competitor.sk(page_id),
            },
            UpdateExpression="SET category = :cat, about = :about"
            + (", fan_count = :fc" if fan_count is not None else ""),
            ExpressionAttributeValues={
                ":cat": category,
                ":about": about,
                **({":fc": fan_count} if fan_count is not None else {}),
            },
        )
        return True

    @staticmethod
    def delete(user_id: str, page_id: str) -> bool:
        """Hard-delete a competitor record."""
        table = get_table()
        table.delete_item(
            Key={
                "PK": Competitor.pk(user_id),
                "SK": Competitor.sk(page_id),
            }
        )
        return True


class ScrapeCacheRepo:
    """
    Read/write Playwright scrape cache records.

    Cache items are global (not user-scoped): the same page_id always maps
    to the same public Ad Library data regardless of which user requested it.
    DynamoDB TTL on `ttl` attribute expires items automatically after 4 hours.
    """

    @staticmethod
    def get(page_id: str) -> Optional[CompetitorScrapeCache]:
        """Return the cached scrape result for page_id, or None if missing/expired."""
        table = get_table()
        resp = table.get_item(
            Key={
                "PK": CompetitorScrapeCache.pk(page_id),
                "SK": CompetitorScrapeCache.sk(),
            }
        )
        item = resp.get("Item")
        return CompetitorScrapeCache.from_item(item) if item else None

    @staticmethod
    def put(cache: CompetitorScrapeCache) -> None:
        """Write (or overwrite) a scrape cache record."""
        table = get_table()
        table.put_item(Item=cache.to_item())

    @staticmethod
    def delete(page_id: str) -> None:
        """Remove a scrape cache record (e.g. on competitor deletion)."""
        table = get_table()
        table.delete_item(
            Key={
                "PK": CompetitorScrapeCache.pk(page_id),
                "SK": CompetitorScrapeCache.sk(),
            }
        )
