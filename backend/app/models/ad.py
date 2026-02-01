"""
Ad model - includes denormalized saved_ads data and page info.

Each ad belongs to a niche and contains all relevant data
including save status, notes, and tags.
"""
import json
from app import db
from app.utils.ids import generate_uuid, now_iso8601


class Ad(db.Model):
    """
    Ad model with denormalized data for efficient queries.

    DynamoDB Access Pattern:
        PK: niche_id (partition key)
        SK: "AD#<meta_ad_id>" (sort key)

    Attributes:
        id: Internal UUID (primary key)
        niche_id: UUID of the containing niche
        meta_ad_id: Original Meta Ad Library ID
        page_id: Meta page ID
        page_name: Denormalized page name
        page_verified: Whether the page is verified
        is_competitor_page: Whether marked as competitor
        start_date: When the ad started running
        end_date: When the ad stopped (null if active)
        is_active: Whether the ad is currently running
        days_active: Calculated days the ad has been active
        platforms: JSON list of platforms
        snapshot_url: URL to ad snapshot
        thumbnail_url: URL to thumbnail
        body: Ad body text
        headline: Ad headline
        description: Ad description
        link_caption: Link caption text
        full_text: Combined text for search
        cta_detected: Detected call-to-action
        landing_url: Landing page URL
        text_length: Length of full_text
        has_emoji: Whether text contains emoji
        has_hashtags: Whether text contains hashtags
        hashtags: JSON list of hashtags
        mentions: JSON list of mentions
        country_codes: JSON list of country codes
        search_keyword: Keyword used to find this ad
        collected_at: When the ad was collected
        is_saved: Whether the ad is saved
        saved_at: When the ad was saved
        saved_notes: User notes for saved ad
        saved_tags: JSON list of tags for saved ad
    """
    __tablename__ = 'ads'

    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    # Niche association
    niche_id = db.Column(db.String(36), nullable=False, index=True)

    # Meta Ad Library ID
    meta_ad_id = db.Column(db.String(100), nullable=False)

    # Page info (denormalized)
    page_id = db.Column(db.String(100), index=True)
    page_name = db.Column(db.String(200))
    page_verified = db.Column(db.Boolean, default=False)
    is_competitor_page = db.Column(db.Boolean, default=False)

    # Ad timing
    start_date = db.Column(db.String(30), index=True)
    end_date = db.Column(db.String(30), nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    days_active = db.Column(db.Integer, default=0)

    # Platforms (stored as JSON)
    _platforms = db.Column('platforms', db.Text, default='[]')

    # URLs
    snapshot_url = db.Column(db.Text, nullable=True)
    thumbnail_url = db.Column(db.Text, nullable=True)
    landing_url = db.Column(db.Text, nullable=True)

    # Multiple creatives (JSON array of {url, type: 'image'|'video'})
    _creatives = db.Column('creatives', db.Text, default='[]')

    # Ad content
    body = db.Column(db.Text, nullable=True)
    headline = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    link_caption = db.Column(db.String(500), nullable=True)
    full_text = db.Column(db.Text, nullable=True)
    cta_detected = db.Column(db.String(50), index=True)

    # Text analysis
    text_length = db.Column(db.Integer, default=0)
    has_emoji = db.Column(db.Boolean, default=False)
    has_hashtags = db.Column(db.Boolean, default=False)
    _hashtags = db.Column('hashtags', db.Text, default='[]')
    _mentions = db.Column('mentions', db.Text, default='[]')

    # Collection metadata
    _country_codes = db.Column('country_codes', db.Text, default='[]')
    search_keyword = db.Column(db.String(200), index=True)
    collected_at = db.Column(db.String(30), default=now_iso8601)

    # Saved ads (denormalized - no separate table)
    is_saved = db.Column(db.Boolean, default=False, index=True)
    saved_at = db.Column(db.String(30), nullable=True)
    saved_notes = db.Column(db.Text, nullable=True)
    _saved_tags = db.Column('saved_tags', db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.String(30), default=now_iso8601)
    updated_at = db.Column(db.String(30), default=now_iso8601, onupdate=now_iso8601)

    # Unique constraint: meta_ad_id must be unique per niche
    __table_args__ = (
        db.UniqueConstraint('niche_id', 'meta_ad_id', name='uq_niche_meta_ad'),
        db.Index('ix_niche_days', 'niche_id', 'days_active'),
        db.Index('ix_niche_page', 'niche_id', 'page_id'),
        db.Index('ix_niche_saved', 'niche_id', 'is_saved'),
        db.Index('ix_niche_cta', 'niche_id', 'cta_detected'),
    )

    @property
    def platforms(self) -> list:
        """Get platforms as a list."""
        try:
            return json.loads(self._platforms) if self._platforms else []
        except json.JSONDecodeError:
            return []

    @platforms.setter
    def platforms(self, value: list):
        """Set platforms from a list."""
        self._platforms = json.dumps(value) if value else '[]'

    @property
    def hashtags(self) -> list:
        """Get hashtags as a list."""
        try:
            return json.loads(self._hashtags) if self._hashtags else []
        except json.JSONDecodeError:
            return []

    @hashtags.setter
    def hashtags(self, value: list):
        """Set hashtags from a list."""
        self._hashtags = json.dumps(value) if value else '[]'

    @property
    def mentions(self) -> list:
        """Get mentions as a list."""
        try:
            return json.loads(self._mentions) if self._mentions else []
        except json.JSONDecodeError:
            return []

    @mentions.setter
    def mentions(self, value: list):
        """Set mentions from a list."""
        self._mentions = json.dumps(value) if value else '[]'

    @property
    def country_codes(self) -> list:
        """Get country codes as a list."""
        try:
            return json.loads(self._country_codes) if self._country_codes else []
        except json.JSONDecodeError:
            return []

    @country_codes.setter
    def country_codes(self, value: list):
        """Set country codes from a list."""
        self._country_codes = json.dumps(value) if value else '[]'

    @property
    def saved_tags(self) -> list:
        """Get saved tags as a list."""
        try:
            return json.loads(self._saved_tags) if self._saved_tags else []
        except json.JSONDecodeError:
            return []

    @saved_tags.setter
    def saved_tags(self, value: list):
        """Set saved tags from a list."""
        self._saved_tags = json.dumps(value) if value else None

    @property
    def creatives(self) -> list:
        """Get creatives as a list of {url, type} objects."""
        try:
            return json.loads(self._creatives) if self._creatives else []
        except json.JSONDecodeError:
            return []

    @creatives.setter
    def creatives(self, value: list):
        """Set creatives from a list."""
        self._creatives = json.dumps(value) if value else '[]'

    def to_dict(self, include_saved: bool = True) -> dict:
        """
        Convert ad to dictionary for API responses.

        Args:
            include_saved: Whether to include saved status and notes
        """
        result = {
            'id': self.id,
            'meta_ad_id': self.meta_ad_id,
            'niche_id': self.niche_id,
            'page': {
                'id': self.page_id,
                'name': self.page_name,
                'verified': self.page_verified,
                'is_competitor': self.is_competitor_page
            },
            'timing': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'is_active': self.is_active,
                'days_active': self.days_active
            },
            'platforms': self.platforms,
            'content': {
                'body': self.body,
                'headline': self.headline,
                'description': self.description,
                'link_caption': self.link_caption,
                'full_text': self.full_text,
                'cta': self.cta_detected,
                'landing_url': self.landing_url
            },
            'media': {
                'snapshot_url': self.snapshot_url,
                'thumbnail_url': self.thumbnail_url,
                'creatives': self.creatives
            },
            'analysis': {
                'text_length': self.text_length,
                'has_emoji': self.has_emoji,
                'has_hashtags': self.has_hashtags,
                'hashtags': self.hashtags,
                'mentions': self.mentions
            },
            'metadata': {
                'country_codes': self.country_codes,
                'search_keyword': self.search_keyword,
                'collected_at': self.collected_at
            },
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        if include_saved:
            result['saved'] = {
                'is_saved': self.is_saved,
                'saved_at': self.saved_at,
                'notes': self.saved_notes,
                'tags': self.saved_tags
            }

        return result

    def to_card_dict(self) -> dict:
        """
        Convert ad to minimal dictionary for list/card views.
        """
        return {
            'id': self.id,
            'meta_ad_id': self.meta_ad_id,
            'page_name': self.page_name,
            'headline': self.headline,
            'body': self.body[:150] + '...' if self.body and len(self.body) > 150 else self.body,
            'thumbnail_url': self.thumbnail_url,
            'creatives': self.creatives,
            'days_active': self.days_active,
            'is_active': self.is_active,
            'is_saved': self.is_saved,
            'platforms': self.platforms,
            'cta': self.cta_detected
        }

    def __repr__(self):
        return f'<Ad {self.meta_ad_id} ({self.page_name})>'
