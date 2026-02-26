"""
Ad repository — replaces app/services/ad_service.py + app/models/ad.py.

This is the most complex repository because it ports the sophisticated
search, filter, group-by-variant and pagination logic from ads.py.

Access patterns covered:
    create_or_update(ad)            PutItem (idempotent upsert)
    get(niche_id, meta_ad_id)       base table GetItem
    search(niche_id, filters)       Query + FilterExpression + app-side grouping
    get_detail(niche_id, meta_ad_id) full ad dict
    get_related(niche_id, page_id)  GSI1 query by page
    get_variants(niche_id, headline, page_name) FilterExpression
    save_ad(niche_id, meta_ad_id, tags)  UpdateItem + GSI2 keys
    unsave_ad(niche_id, meta_ad_id)      UpdateItem (clears GSI2 keys)
    list_saved(niche_id, limit, cursor)  GSI2 query
    clear_all(niche_id)             batch delete all AD# items
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

from app.dynamodb.client import get_table, GSI1, GSI2
from app.dynamodb.models import Ad
from app.utils.ids import generate_uuid, now_iso8601


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _variant_key(page_name: str, headline: str) -> str:
    """Stable hash used to group ad variants (same advertiser + copy)."""
    raw = f"{page_name.strip().lower()}|{headline.strip().lower()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _apply_filters(items: List[dict], filters: dict) -> List[dict]:
    """
    Application-side filter pass after the DynamoDB Query.

    DynamoDB FilterExpression can only hold a limited number of conditions
    before hitting the 1 MB response limit; additionally, boolean/list fields
    stored as JSON strings need Python-level filtering.

    Supported filter keys:
        is_active (bool)
        cta_detected (str)
        has_emoji (bool)
        has_hashtags (bool)
        min_days (int)
        max_days (int)
        page_name (str, partial match, case-insensitive)
        search (str, searches full_text + headline + body, case-insensitive)
        platforms (list[str], intersection check)
    """
    is_active   = filters.get("is_active")
    cta         = filters.get("cta_detected")
    has_emoji   = filters.get("has_emoji")
    has_hashtags = filters.get("has_hashtags")
    min_days    = filters.get("min_days")
    max_days    = filters.get("max_days")
    page_name   = filters.get("page_name", "").lower()
    search      = filters.get("search", "").lower()
    platforms   = filters.get("platforms")  # list or None

    result = []
    for item in items:
        if is_active is not None and item.get("is_active") != is_active:
            continue
        if cta and item.get("cta_detected") != cta:
            continue
        if has_emoji is not None and item.get("has_emoji") != has_emoji:
            continue
        if has_hashtags is not None and item.get("has_hashtags") != has_hashtags:
            continue
        days = item.get("days_active") or 0
        if min_days is not None and days < min_days:
            continue
        if max_days is not None and days > max_days:
            continue
        if page_name and page_name not in (item.get("page_name") or "").lower():
            continue
        if search:
            haystack = " ".join([
                item.get("full_text") or "",
                item.get("headline") or "",
                item.get("body") or "",
            ]).lower()
            if search not in haystack:
                continue
        if platforms:
            ad_platforms = json.loads(item.get("platforms") or "[]") if isinstance(item.get("platforms"), str) else (item.get("platforms") or [])
            if not any(p in ad_platforms for p in platforms):
                continue
        result.append(item)
    return result


def _group_by_variant(ads: List[Ad], sort: str = "variants", order: str = "desc") -> List[Dict[str, Any]]:
    """
    Group ads by (page_name, headline) — mirrors the original ads.py:130-198 logic.

    Returns a list of variant groups, each containing:
        variant_key, page_name, headline, count, days_active (max), ads (list)

    Args:
        ads: List of Ad objects to group
        sort: Sort field - 'variants', 'days_active', 'start_date', or 'collected_at'
        order: Sort order - 'asc' or 'desc'
    """
    groups: Dict[str, List[Ad]] = defaultdict(list)
    for ad in ads:
        key = _variant_key(ad.page_name, ad.headline)
        groups[key].append(ad)

    result = []
    for key, group_ads in groups.items():
        max_days = max((a.days_active or 0) for a in group_ads)
        representative = group_ads[0]
        result.append({
            "variant_key": key,
            "page_name": representative.page_name,
            "headline": representative.headline,
            "count": len(group_ads),
            "days_active": max_days,
            "start_date": representative.start_date,
            "collected_at": representative.collected_at,
            "ads": [a.to_card_dict() for a in group_ads],
        })

    # Sort based on the specified field
    reverse = (order == "desc")

    if sort == "variants":
        # Sort by number of variants (count)
        result.sort(key=lambda g: g["count"], reverse=reverse)
    elif sort == "days_active":
        # Sort by days_active
        result.sort(key=lambda g: g["days_active"], reverse=reverse)
    elif sort == "start_date":
        # Sort by start_date
        result.sort(key=lambda g: g["start_date"] or "", reverse=reverse)
    elif sort == "collected_at":
        # Sort by collected_at
        result.sort(key=lambda g: g["collected_at"] or "", reverse=reverse)
    else:
        # Default: sort by variants
        result.sort(key=lambda g: g["count"], reverse=reverse)

    return result


# ---------------------------------------------------------------------------
# AdRepo
# ---------------------------------------------------------------------------

class AdRepo:

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def get(niche_id: str, meta_ad_id: str) -> Optional[Ad]:
        """Fetch a single ad by primary key."""
        table = get_table()
        resp = table.get_item(
            Key={"PK": Ad.pk(niche_id), "SK": Ad.sk(meta_ad_id)}
        )
        item = resp.get("Item")
        return Ad.from_item(item) if item else None

    @staticmethod
    def search(
        niche_id: str,
        filters: Optional[dict] = None,
        group_by_variant: bool = True,
        sort: str = "variants",
        order: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """
        Main search endpoint — mirrors routes/ads.py GET /ads.

        1. Query all AD# items for the niche (single partition scan).
        2. Apply application-side filters.
        3. Optionally group by variant and paginate.

        Args:
            niche_id: Niche ID to search within
            filters: Filter dict for _apply_filters
            group_by_variant: Whether to group by (page_name, headline)
            sort: Sort field - 'variants', 'days_active', 'start_date', or 'collected_at'
            order: Sort order - 'asc' or 'desc'
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            {
                "ads": [...],           # list of card dicts or variant groups
                "total": int,           # total after filtering
                "page": int,
                "per_page": int,
                "has_next": bool,
            }
        """
        table = get_table()
        filters = filters or {}

        # 1. Fetch all ads for this niche partition
        items: list = []
        query_kwargs = dict(
            KeyConditionExpression=(
                Key("PK").eq(Ad.pk(niche_id)) &
                Key("SK").begins_with("AD#")
            ),
        )

        while True:
            resp = table.query(**query_kwargs)
            items.extend(resp.get("Items", []))
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break
            query_kwargs["ExclusiveStartKey"] = last_key

        # 2. Application-side filter
        filtered = _apply_filters(items, filters)

        # 3. Convert to Ad objects
        ads = [Ad.from_item(i) for i in filtered]

        # 4. Group or flat list
        total_ads = len(ads)

        if group_by_variant:
            groups = _group_by_variant(ads, sort=sort, order=order)
            total = len(groups)
            start = (page - 1) * per_page
            end   = start + per_page
            page_items = groups[start:end]
            return {
                "ads": page_items,
                "total": total,
                "total_ads": total_ads,
                "page": page,
                "per_page": per_page,
                "has_next": end < total,
            }
        else:
            # Flat list - apply sorting
            reverse = (order == "desc")
            if sort == "days_active":
                ads.sort(key=lambda a: a.days_active or 0, reverse=reverse)
            elif sort == "start_date":
                ads.sort(key=lambda a: a.start_date or "", reverse=reverse)
            elif sort == "collected_at":
                ads.sort(key=lambda a: a.collected_at or "", reverse=reverse)
            else:
                # Default to days_active for flat list
                ads.sort(key=lambda a: a.days_active or 0, reverse=reverse)

            total = total_ads
            start = (page - 1) * per_page
            end   = start + per_page
            return {
                "ads": [a.to_card_dict() for a in ads[start:end]],
                "total": total,
                "total_ads": total_ads,
                "page": page,
                "per_page": per_page,
                "has_next": end < total,
            }

    @staticmethod
    def get_related(
        niche_id: str,
        page_id: str,
        exclude_meta_ad_id: str = "",
        limit: int = 6,
        page_name: str = None
    ) -> List[dict]:
        """
        Other ads from the same page within the niche (GSI1 query).
        Falls back to page_name matching if page_id is empty/None.
        """
        table = get_table()

        # If page_id is empty or None, fall back to page_name filtering
        if not page_id and page_name:
            # Query all ads in niche and filter by page_name
            items: list = []
            query_kwargs = dict(
                KeyConditionExpression=(
                    Key("PK").eq(Ad.pk(niche_id)) &
                    Key("SK").begins_with("AD#")
                ),
            )
            while True:
                resp = table.query(**query_kwargs)
                for item in resp.get("Items", []):
                    if (item.get("page_name") == page_name and
                        item.get("meta_ad_id") != exclude_meta_ad_id):
                        items.append(item)
                        if len(items) >= limit:
                            break
                if len(items) >= limit or not resp.get("LastEvaluatedKey"):
                    break
                query_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

            ads = [Ad.from_item(i).to_card_dict() for i in items]
            return ads[:limit]

        # Original GSI1 query path (when page_id exists)
        resp = table.query(
            IndexName=GSI1,
            KeyConditionExpression=(
                Key("GSI1PK").eq(f"NICHE_PAGE#{niche_id}#{page_id}") &
                Key("GSI1SK").begins_with("AD#")
            ),
            Limit=limit + 1,  # fetch one extra so we can exclude self
        )
        ads = [
            Ad.from_item(i).to_card_dict()
            for i in resp.get("Items", [])
            if i.get("meta_ad_id") != exclude_meta_ad_id
        ]
        return ads[:limit]

    @staticmethod
    def get_variants(niche_id: str, page_name: str, headline: str) -> List[dict]:
        """
        All ads from the same page with the same headline (variant group).
        Application-side filter after base-table query.
        """
        table = get_table()
        items: list = []
        key = _variant_key(page_name, headline)

        query_kwargs = dict(
            KeyConditionExpression=(
                Key("PK").eq(Ad.pk(niche_id)) &
                Key("SK").begins_with("AD#")
            ),
        )
        while True:
            resp = table.query(**query_kwargs)
            for item in resp.get("Items", []):
                if _variant_key(
                    item.get("page_name", ""),
                    item.get("headline", ""),
                ) == key:
                    items.append(item)
            if not resp.get("LastEvaluatedKey"):
                break
            query_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

        ads = [Ad.from_item(i) for i in items]
        ads.sort(key=lambda a: a.days_active or 0, reverse=True)
        return [a.to_dict() for a in ads]

    # ------------------------------------------------------------------
    # Saved ads
    # ------------------------------------------------------------------

    @staticmethod
    def list_saved(
        niche_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Saved ads for a niche, newest save first (GSI2 descending).

        cursor: opaque pagination token (LastEvaluatedKey JSON-encoded)
        """
        table = get_table()
        query_kwargs = dict(
            IndexName=GSI2,
            KeyConditionExpression=Key("GSI2PK").eq(f"NICHE_SAVED#{niche_id}"),
            ScanIndexForward=False,
            Limit=limit + 1,
        )
        if cursor:
            query_kwargs["ExclusiveStartKey"] = json.loads(cursor)

        resp = table.query(**query_kwargs)
        items = resp.get("Items", [])

        has_next = len(items) > limit
        if has_next:
            items = items[:limit]

        next_cursor = None
        if has_next and resp.get("LastEvaluatedKey"):
            next_cursor = json.dumps(resp["LastEvaluatedKey"])

        return {
            "ads": [Ad.from_item(i).to_dict() for i in items],
            "has_next": has_next,
            "next_cursor": next_cursor,
        }

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def create_or_update(ad: Ad) -> Tuple[Ad, bool]:
        """
        Upsert an ad.  Returns (ad, is_new).

        Mirrors ad_service.create_or_update_ad() but without SQLAlchemy:
        - PutItem is used for new ads
        - UpdateItem for existing ads (preserves is_saved / saved_tags)

        Side effects (called by caller / collect_worker):
            PageRepo.upsert_page()
            PageRepo.upsert_niche_page()
        """
        table = get_table()
        now = now_iso8601()

        existing = AdRepo.get(ad.niche_id, ad.meta_ad_id)
        is_new = existing is None

        if is_new:
            ad.id = ad.id or generate_uuid()
            ad.collected_at = now
            table.put_item(Item=ad.to_item())
        else:
            # Preserve saved state from existing record
            ad.id = existing.id
            ad.is_saved = existing.is_saved
            ad.saved_at = existing.saved_at
            ad.saved_tags = existing.saved_tags
            ad.collected_at = existing.collected_at
            table.put_item(Item=ad.to_item())

        return ad, is_new

    @staticmethod
    def save_ad(niche_id: str, meta_ad_id: str, tags: Optional[List[str]] = None) -> Optional[Ad]:
        """
        Mark an ad as saved, set saved_at, populate GSI2 keys.
        """
        table = get_table()
        now = now_iso8601()
        tags = tags or []

        ad = AdRepo.get(niche_id, meta_ad_id)
        if not ad:
            return None

        ad.is_saved = True
        ad.saved_at = now
        ad.saved_tags = tags

        table.update_item(
            Key={"PK": Ad.pk(niche_id), "SK": Ad.sk(meta_ad_id)},
            UpdateExpression=(
                "SET is_saved = :true, saved_at = :now, saved_tags = :tags, "
                "GSI2PK = :gsi2pk, GSI2SK = :gsi2sk"
            ),
            ExpressionAttributeValues={
                ":true": True,
                ":now": now,
                ":tags": json.dumps(tags),
                ":gsi2pk": f"NICHE_SAVED#{niche_id}",
                ":gsi2sk": f"{now}#{meta_ad_id}",
            },
        )
        return ad

    @staticmethod
    def unsave_ad(niche_id: str, meta_ad_id: str) -> Optional[Ad]:
        """
        Remove saved state.  Removes GSI2 keys so ad disappears from saved index.
        """
        table = get_table()

        ad = AdRepo.get(niche_id, meta_ad_id)
        if not ad:
            return None

        table.update_item(
            Key={"PK": Ad.pk(niche_id), "SK": Ad.sk(meta_ad_id)},
            UpdateExpression=(
                "SET is_saved = :false, saved_at = :empty, saved_tags = :empty_list "
                "REMOVE GSI2PK, GSI2SK"
            ),
            ExpressionAttributeValues={
                ":false": False,
                ":empty": "",
                ":empty_list": json.dumps([]),
            },
        )
        ad.is_saved = False
        ad.saved_at = None
        ad.saved_tags = []
        return ad

    @staticmethod
    def update_saved_tags(niche_id: str, meta_ad_id: str, tags: List[str]) -> Optional[Ad]:
        """Update tags on an already-saved ad."""
        table = get_table()

        ad = AdRepo.get(niche_id, meta_ad_id)
        if not ad or not ad.is_saved:
            return None

        table.update_item(
            Key={"PK": Ad.pk(niche_id), "SK": Ad.sk(meta_ad_id)},
            UpdateExpression="SET saved_tags = :tags",
            ExpressionAttributeValues={":tags": json.dumps(tags)},
        )
        ad.saved_tags = tags
        return ad

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    @staticmethod
    def clear_all(niche_id: str, include_saved: bool = False) -> int:
        """
        Delete AD# items for a niche.

        When include_saved=False (default), saved ads are preserved.
        When include_saved=True, all ads including saved ones are deleted.

        Returns number of deleted items.
        """
        table = get_table()

        # 1. Collect all AD# keys
        items: list = []
        query_kwargs = dict(
            KeyConditionExpression=(
                Key("PK").eq(Ad.pk(niche_id)) &
                Key("SK").begins_with("AD#")
            ),
            ProjectionExpression="PK, SK, is_saved",
        )
        while True:
            resp = table.query(**query_kwargs)
            items.extend(resp.get("Items", []))
            if not resp.get("LastEvaluatedKey"):
                break
            query_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

        # 2. Delete in batches of 25 (DynamoDB batch_write_item limit)
        to_delete = items if include_saved else [i for i in items if not i.get("is_saved")]
        deleted = 0

        for i in range(0, len(to_delete), 25):
            batch = to_delete[i:i + 25]
            with table.batch_writer() as bw:
                for item in batch:
                    bw.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
            deleted += len(batch)

        return deleted
