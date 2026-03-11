"""
DynamoDB item dataclasses.

Each class mirrors the SQLAlchemy model it replaces but is a plain Python
dataclass with two extra methods:

    to_item()   — serialise to DynamoDB item dict (PK/SK/GSI keys included)
    from_item() — deserialise from DynamoDB item dict back to the dataclass

JSON-serialised list fields (platforms, hashtags, etc.) are stored as
DynamoDB String (S) in JSON form so they survive round-trips without loss.

All timestamps are ISO8601 strings (UTC, ending in 'Z').
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

@dataclass
class User:
    """
    DynamoDB layout:
        PK  = USER#<clerk_id>
        SK  = METADATA
        GSI1PK = USER_EMAIL#<email>
        GSI1SK = METADATA
    """
    id: str                         # Clerk user ID
    email: str
    first_name: str = ""
    last_name: str = ""
    image_url: str = ""
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    # ---- DynamoDB key helpers ----

    @staticmethod
    def pk(clerk_id: str) -> str:
        return f"USER#{clerk_id}"

    @staticmethod
    def sk() -> str:
        return "METADATA"

    # ---- Serialisation ----

    def to_item(self) -> dict:
        return {
            "PK": self.pk(self.id),
            "SK": self.sk(),
            "GSI1PK": f"USER_EMAIL#{self.email}",
            "GSI1SK": "METADATA",
            "entity_type": "USER",
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "User":
        return cls(
            id=item["id"],
            email=item["email"],
            first_name=item.get("first_name", ""),
            last_name=item.get("last_name", ""),
            image_url=item.get("image_url", ""),
            is_active=item.get("is_active", True),
            created_at=item.get("created_at", ""),
            updated_at=item.get("updated_at", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ---------------------------------------------------------------------------
# Niche
# ---------------------------------------------------------------------------

@dataclass
class Niche:
    """
    DynamoDB layout:
        PK     = USER#<user_id>
        SK     = NICHE#<niche_id>
        GSI1PK = NICHE#<niche_id>
        GSI1SK = METADATA
        GSI2PK = USER_SLUG#<user_id>#<slug>
        GSI2SK = METADATA
    """
    id: str
    user_id: str
    name: str
    slug: str
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    countries: List[str] = field(default_factory=lambda: ["US"])
    platforms: List[str] = field(default_factory=lambda: ["instagram"])
    is_active: bool = True
    auto_collect_enabled: bool = False
    auto_collect_interval_hours: int = 3
    created_at: str = ""
    updated_at: str = ""

    # ---- DynamoDB key helpers ----

    @staticmethod
    def pk(user_id: str) -> str:
        return f"USER#{user_id}"

    @staticmethod
    def sk(niche_id: str) -> str:
        return f"NICHE#{niche_id}"

    # ---- Serialisation ----

    def to_item(self) -> dict:
        return {
            "PK": self.pk(self.user_id),
            "SK": self.sk(self.id),
            "GSI1PK": f"NICHE#{self.id}",
            "GSI1SK": "METADATA",
            "GSI2PK": f"USER_SLUG#{self.user_id}#{self.slug}",
            "GSI2SK": "METADATA",
            "entity_type": "NICHE",
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "keywords": json.dumps(self.keywords),
            "countries": json.dumps(self.countries),
            "platforms": json.dumps(self.platforms),
            "is_active": self.is_active,
            "auto_collect_enabled": self.auto_collect_enabled,
            "auto_collect_interval_hours": self.auto_collect_interval_hours,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "Niche":
        return cls(
            id=item["id"],
            user_id=item["user_id"],
            name=item["name"],
            slug=item["slug"],
            description=item.get("description", ""),
            keywords=_loads_list(item.get("keywords", "[]")),
            countries=_loads_list(item.get("countries", '["US"]')),
            platforms=_loads_list(item.get("platforms", '["instagram"]')),
            is_active=item.get("is_active", True),
            auto_collect_enabled=item.get("auto_collect_enabled", False),
            auto_collect_interval_hours=int(item.get("auto_collect_interval_hours", 3)),
            created_at=item.get("created_at", ""),
            updated_at=item.get("updated_at", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "keywords": self.keywords,
            "countries": self.countries,
            "platforms": self.platforms,
            "is_active": self.is_active,
            "auto_collect_enabled": self.auto_collect_enabled,
            "auto_collect_interval_hours": self.auto_collect_interval_hours,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ---------------------------------------------------------------------------
# Ad
# ---------------------------------------------------------------------------

@dataclass
class Ad:
    """
    DynamoDB layout:
        PK     = NICHE#<niche_id>
        SK     = AD#<meta_ad_id>
        GSI1PK = NICHE_PAGE#<niche_id>#<page_id>   (ads by page within niche)
        GSI1SK = AD#<meta_ad_id>
        GSI2PK = NICHE_SAVED#<niche_id>             (only set when is_saved=True)
        GSI2SK = <saved_at>#<meta_ad_id>            (chronological saved order)
    """
    # Identity
    id: str                         # Internal UUID
    niche_id: str
    meta_ad_id: str                 # Ad Library ad ID (SK prefix)
    page_id: Optional[str] = None
    page_name: str = ""

    # Dates
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool = True
    days_active: Optional[int] = None
    collected_at: str = ""
    last_seen_at: str = ""          # Updated on every collection pass

    # Platforms
    platforms: List[str] = field(default_factory=list)
    country_codes: List[str] = field(default_factory=list)
    snapshot_url: str = ""

    # Content
    body: str = ""
    headline: str = ""
    description: str = ""
    link_caption: str = ""
    full_text: str = ""

    # Text metrics
    text_length: int = 0
    has_emoji: bool = False
    has_hashtags: bool = False
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    cta_detected: Optional[str] = None

    # Creative metadata
    creative_type: str = "image"
    creatives: List[dict] = field(default_factory=list)

    # Saved state
    is_saved: bool = False
    saved_at: Optional[str] = None
    saved_tags: List[str] = field(default_factory=list)

    # Search
    search_keyword: str = ""

    # ---- DynamoDB key helpers ----

    @staticmethod
    def pk(niche_id: str) -> str:
        return f"NICHE#{niche_id}"

    @staticmethod
    def sk(meta_ad_id: str) -> str:
        return f"AD#{meta_ad_id}"

    # ---- Serialisation ----

    def to_item(self) -> dict:
        item = {
            "PK": self.pk(self.niche_id),
            "SK": self.sk(self.meta_ad_id),
            # GSI1: ads by page within niche
            "GSI1PK": f"NICHE_PAGE#{self.niche_id}#{self.page_id or 'UNKNOWN'}",
            "GSI1SK": self.sk(self.meta_ad_id),
            "entity_type": "AD",
            "id": self.id,
            "niche_id": self.niche_id,
            "meta_ad_id": self.meta_ad_id,
            "page_id": self.page_id or "",
            "page_name": self.page_name,
            "start_date": self.start_date or "",
            "end_date": self.end_date or "",
            "is_active": self.is_active,
            "days_active": self.days_active,
            "collected_at": self.collected_at,
            "last_seen_at": self.last_seen_at,
            "platforms": json.dumps(self.platforms),
            "country_codes": json.dumps(self.country_codes),
            "snapshot_url": self.snapshot_url,
            "body": self.body,
            "headline": self.headline,
            "description": self.description,
            "link_caption": self.link_caption,
            "full_text": self.full_text,
            "text_length": self.text_length,
            "has_emoji": self.has_emoji,
            "has_hashtags": self.has_hashtags,
            "hashtags": json.dumps(self.hashtags),
            "mentions": json.dumps(self.mentions),
            "cta_detected": self.cta_detected or "",
            "creative_type": self.creative_type,
            "creatives": json.dumps(self.creatives),
            "is_saved": self.is_saved,
            "saved_at": self.saved_at or "",
            "saved_tags": json.dumps(self.saved_tags),
            "search_keyword": self.search_keyword,
        }

        # GSI2: only populated when ad is saved (enables efficient saved-ads query)
        if self.is_saved and self.saved_at:
            item["GSI2PK"] = f"NICHE_SAVED#{self.niche_id}"
            item["GSI2SK"] = f"{self.saved_at}#{self.meta_ad_id}"
        else:
            # Remove GSI2 keys if ad is unsaved (DynamoDB ignores missing GSI keys)
            item.pop("GSI2PK", None)
            item.pop("GSI2SK", None)

        return item

    @classmethod
    def from_item(cls, item: dict) -> "Ad":
        return cls(
            id=item["id"],
            niche_id=item["niche_id"],
            meta_ad_id=item["meta_ad_id"],
            page_id=item.get("page_id") or None,
            page_name=item.get("page_name", ""),
            start_date=item.get("start_date") or None,
            end_date=item.get("end_date") or None,
            is_active=item.get("is_active", True),
            days_active=int(item["days_active"]) if item.get("days_active") is not None else None,
            collected_at=item.get("collected_at", ""),
            last_seen_at=item.get("last_seen_at", ""),
            platforms=_loads_list(item.get("platforms", "[]")),
            country_codes=_loads_list(item.get("country_codes", "[]")),
            snapshot_url=item.get("snapshot_url", ""),
            body=item.get("body", ""),
            headline=item.get("headline", ""),
            description=item.get("description", ""),
            link_caption=item.get("link_caption", ""),
            full_text=item.get("full_text", ""),
            text_length=int(item.get("text_length") or 0),
            has_emoji=item.get("has_emoji", False),
            has_hashtags=item.get("has_hashtags", False),
            hashtags=_loads_list(item.get("hashtags", "[]")),
            mentions=_loads_list(item.get("mentions", "[]")),
            cta_detected=item.get("cta_detected") or None,
            creative_type=item.get("creative_type", "image"),
            creatives=_loads_list(item.get("creatives", "[]")),
            is_saved=item.get("is_saved", False),
            saved_at=item.get("saved_at") or None,
            saved_tags=_loads_list(item.get("saved_tags", "[]")),
            search_keyword=item.get("search_keyword", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "niche_id": self.niche_id,
            "meta_ad_id": self.meta_ad_id,
            "page_id": self.page_id,
            "page_name": self.page_name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_active": self.is_active,
            "days_active": self.days_active,
            "collected_at": self.collected_at,
            "last_seen_at": self.last_seen_at,
            "platforms": self.platforms,
            "country_codes": self.country_codes,
            "snapshot_url": self.snapshot_url,
            "body": self.body,
            "headline": self.headline,
            "description": self.description,
            "link_caption": self.link_caption,
            "full_text": self.full_text,
            "text_length": self.text_length,
            "has_emoji": self.has_emoji,
            "has_hashtags": self.has_hashtags,
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "cta_detected": self.cta_detected,
            "creative_type": self.creative_type,
            "creatives": self.creatives,
            "is_saved": self.is_saved,
            "saved_at": self.saved_at,
            "saved_tags": self.saved_tags,
            "search_keyword": self.search_keyword,
        }

    def to_card_dict(self) -> dict:
        """Lightweight representation for list/search responses."""
        return {
            "id": self.id,
            "meta_ad_id": self.meta_ad_id,
            "page_name": self.page_name,
            "headline": self.headline,
            "body": self.body,
            "cta_detected": self.cta_detected,
            "days_active": self.days_active,
            "is_active": self.is_active,
            "is_saved": self.is_saved,
            "snapshot_url": self.snapshot_url,
            "platforms": self.platforms,
            "creative_type": self.creative_type,
        }


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

@dataclass
class Page:
    """
    Global page registry (advertiser pages seen across all niches).

    DynamoDB layout:
        PK  = PAGE#<page_id>
        SK  = METADATA
    """
    page_id: str
    page_name: str
    first_seen_at: str = ""
    last_seen_at: str = ""

    @staticmethod
    def pk(page_id: str) -> str:
        return f"PAGE#{page_id}"

    @staticmethod
    def sk() -> str:
        return "METADATA"

    def to_item(self) -> dict:
        return {
            "PK": self.pk(self.page_id),
            "SK": self.sk(),
            "entity_type": "PAGE",
            "page_id": self.page_id,
            "page_name": self.page_name,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "Page":
        return cls(
            page_id=item["page_id"],
            page_name=item["page_name"],
            first_seen_at=item.get("first_seen_at", ""),
            last_seen_at=item.get("last_seen_at", ""),
        )

    def to_dict(self) -> dict:
        return {
            "page_id": self.page_id,
            "page_name": self.page_name,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
        }


# ---------------------------------------------------------------------------
# NichePage  (links a Page to a Niche; tracks competitor flag)
# ---------------------------------------------------------------------------

@dataclass
class NichePage:
    """
    DynamoDB layout:
        PK  = NICHE#<niche_id>
        SK  = PAGE#<page_id>
    """
    niche_id: str
    page_id: str
    page_name: str
    is_competitor: bool = False
    ad_count: int = 0
    first_seen_at: str = ""
    last_seen_at: str = ""

    @staticmethod
    def pk(niche_id: str) -> str:
        return f"NICHE#{niche_id}"

    @staticmethod
    def sk(page_id: str) -> str:
        return f"PAGE#{page_id}"

    def to_item(self) -> dict:
        return {
            "PK": self.pk(self.niche_id),
            "SK": self.sk(self.page_id),
            "entity_type": "NICHE_PAGE",
            "niche_id": self.niche_id,
            "page_id": self.page_id,
            "page_name": self.page_name,
            "is_competitor": self.is_competitor,
            "ad_count": self.ad_count,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "NichePage":
        return cls(
            niche_id=item["niche_id"],
            page_id=item["page_id"],
            page_name=item["page_name"],
            is_competitor=item.get("is_competitor", False),
            ad_count=item.get("ad_count", 0),
            first_seen_at=item.get("first_seen_at", ""),
            last_seen_at=item.get("last_seen_at", ""),
        )

    def to_dict(self) -> dict:
        return {
            "niche_id": self.niche_id,
            "page_id": self.page_id,
            "page_name": self.page_name,
            "is_competitor": self.is_competitor,
            "ad_count": self.ad_count,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
        }


# ---------------------------------------------------------------------------
# CollectionRun
# ---------------------------------------------------------------------------

@dataclass
class CollectionRun:
    """
    DynamoDB layout:
        PK  = NICHE#<niche_id>
        SK  = RUN#<started_at>#<run_id>   (chronological via ISO8601 sort)
    """
    id: str
    niche_id: str
    status: str = "pending"          # pending | running | completed | error
    keywords_used: List[str] = field(default_factory=list)
    ads_found: int = 0
    ads_new: int = 0
    ads_updated: int = 0
    total_ads_after: int = 0
    limit_requested: int = 0
    countries: List[str] = field(default_factory=lambda: ["US"])
    error_message: Optional[str] = None
    started_at: str = ""
    completed_at: Optional[str] = None
    # Identity fields — who triggered this run and which niche
    user_id: str = ""
    user_email: str = ""
    niche_name: str = ""
    # API quota tracking
    api_requests_made: int = 0

    VALID_STATUSES = {"pending", "running", "completed", "error"}

    @staticmethod
    def pk(niche_id: str) -> str:
        return f"NICHE#{niche_id}"

    @staticmethod
    def sk(started_at: str, run_id: str) -> str:
        return f"RUN#{started_at}#{run_id}"

    def to_item(self) -> dict:
        return {
            "PK": self.pk(self.niche_id),
            "SK": self.sk(self.started_at, self.id),
            "entity_type": "COLLECTION_RUN",
            "id": self.id,
            "niche_id": self.niche_id,
            "status": self.status,
            "keywords_used": json.dumps(self.keywords_used),
            "ads_found": self.ads_found,
            "ads_new": self.ads_new,
            "ads_updated": self.ads_updated,
            "total_ads_after": self.total_ads_after,
            "limit_requested": self.limit_requested,
            "countries": json.dumps(self.countries),
            "error_message": self.error_message or "",
            "started_at": self.started_at,
            "completed_at": self.completed_at or "",
            "user_id": self.user_id,
            "user_email": self.user_email,
            "niche_name": self.niche_name,
            "api_requests_made": self.api_requests_made,
        }

    @classmethod
    def from_item(cls, item: dict) -> "CollectionRun":
        return cls(
            id=item["id"],
            niche_id=item["niche_id"],
            status=item.get("status", "pending"),
            keywords_used=_loads_list(item.get("keywords_used", "[]")),
            ads_found=int(item.get("ads_found") or 0),
            ads_new=int(item.get("ads_new") or 0),
            ads_updated=int(item.get("ads_updated") or 0),
            total_ads_after=int(item.get("total_ads_after") or 0),
            limit_requested=int(item.get("limit_requested") or 0),
            countries=_loads_list(item.get("countries", '["US"]')),
            error_message=item.get("error_message") or None,
            started_at=item.get("started_at", ""),
            completed_at=item.get("completed_at") or None,
            user_id=item.get("user_id", ""),
            user_email=item.get("user_email", ""),
            niche_name=item.get("niche_name", ""),
            api_requests_made=int(item.get("api_requests_made") or 0),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "niche_id": self.niche_id,
            "status": self.status,
            "keywords_used": self.keywords_used,
            "ads_found": self.ads_found,
            "ads_new": self.ads_new,
            "ads_updated": self.ads_updated,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "niche_name": self.niche_name,
            "api_requests_made": self.api_requests_made,
        }


# ---------------------------------------------------------------------------
# Competitor
# ---------------------------------------------------------------------------

@dataclass
class Competitor:
    """
    A competitor advertiser page tracked by a user (global, not niche-scoped).

    DynamoDB layout:
        PK  = USER#<user_id>
        SK  = COMPETITOR#<page_id>
    """
    user_id: str
    page_id: str
    page_name: str
    notes: str = ""
    added_at: str = ""
    # Page profile metadata (fetched from Graph API at add-time)
    fan_count: Optional[int] = None
    category: str = ""
    about: str = ""

    @staticmethod
    def pk(user_id: str) -> str:
        return f"USER#{user_id}"

    @staticmethod
    def sk(page_id: str) -> str:
        return f"COMPETITOR#{page_id}"

    def to_item(self) -> dict:
        item: dict = {
            "PK": self.pk(self.user_id),
            "SK": self.sk(self.page_id),
            "entity_type": "COMPETITOR",
            "user_id": self.user_id,
            "page_id": self.page_id,
            "page_name": self.page_name,
            "notes": self.notes,
            "added_at": self.added_at,
            "category": self.category,
            "about": self.about,
        }
        if self.fan_count is not None:
            item["fan_count"] = self.fan_count
        return item

    @classmethod
    def from_item(cls, item: dict) -> "Competitor":
        fan_count_raw = item.get("fan_count")
        return cls(
            user_id=item["user_id"],
            page_id=item["page_id"],
            page_name=item["page_name"],
            notes=item.get("notes", ""),
            added_at=item.get("added_at", ""),
            fan_count=int(fan_count_raw) if fan_count_raw is not None else None,
            category=item.get("category", ""),
            about=item.get("about", ""),
        )

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "page_id": self.page_id,
            "page_name": self.page_name,
            "notes": self.notes,
            "added_at": self.added_at,
            "fan_count": self.fan_count,
            "category": self.category,
            "about": self.about,
        }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _loads_list(value) -> list:
    """Safely deserialise a JSON string or pass-through a list."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            result = json.loads(value)
            return result if isinstance(result, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []
