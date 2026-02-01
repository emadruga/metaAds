"""
Niche model - analysis projects scoped to users.

Each user can have multiple niches, each containing its own
collection of ads, saved items, and search history.
"""
import json
from app import db
from app.utils.ids import generate_uuid, now_iso8601


class Niche(db.Model):
    """
    Niche model for organizing ad research.

    DynamoDB Access Pattern:
        PK: user_id (partition key)
        SK: niche_id (sort key)

    Attributes:
        niche_id: UUID primary key
        user_id: Clerk user ID (for multi-tenancy)
        slug: URL-friendly identifier (unique per user)
        name: Display name
        description: Optional description
        color: Hex color for UI theming
        icon: Emoji or icon name
        keywords: JSON list of search keywords
        countries: JSON list of country codes
        platforms: JSON list of platforms
        is_active: Whether the niche is active
    """
    __tablename__ = 'niches'

    # Primary key
    niche_id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    # User scoping
    user_id = db.Column(db.String(100), nullable=False, index=True)

    # Identifiers
    slug = db.Column(db.String(200), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # UI customization
    color = db.Column(db.String(7), default='#8B5CF6')  # Hex color
    icon = db.Column(db.String(50), default='📊')  # Emoji or icon name

    # Configuration (stored as JSON strings)
    _keywords = db.Column('keywords', db.Text, default='[]')
    _countries = db.Column('countries', db.Text, default='["US"]')
    _platforms = db.Column('platforms', db.Text, default='["instagram", "facebook"]')

    # Status
    is_active = db.Column(db.Boolean, default=True)

    # Timestamps
    created_at = db.Column(db.String(30), default=now_iso8601)
    updated_at = db.Column(db.String(30), default=now_iso8601, onupdate=now_iso8601)

    # Unique constraint: slug must be unique per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'slug', name='uq_user_slug'),
    )

    @property
    def keywords(self) -> list:
        """Get keywords as a list."""
        try:
            return json.loads(self._keywords) if self._keywords else []
        except json.JSONDecodeError:
            return []

    @keywords.setter
    def keywords(self, value: list):
        """Set keywords from a list."""
        self._keywords = json.dumps(value) if value else '[]'

    @property
    def countries(self) -> list:
        """Get countries as a list."""
        try:
            return json.loads(self._countries) if self._countries else ['US']
        except json.JSONDecodeError:
            return ['US']

    @countries.setter
    def countries(self, value: list):
        """Set countries from a list."""
        self._countries = json.dumps(value) if value else '["US"]'

    @property
    def platforms(self) -> list:
        """Get platforms as a list."""
        try:
            return json.loads(self._platforms) if self._platforms else ['instagram', 'facebook']
        except json.JSONDecodeError:
            return ['instagram', 'facebook']

    @platforms.setter
    def platforms(self, value: list):
        """Set platforms from a list."""
        self._platforms = json.dumps(value) if value else '["instagram", "facebook"]'

    def to_dict(self, include_stats: bool = False) -> dict:
        """
        Convert niche to dictionary for API responses.

        Args:
            include_stats: Whether to include statistics (requires additional queries)
        """
        result = {
            'id': self.niche_id,
            'slug': self.slug,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'keywords': self.keywords,
            'countries': self.countries,
            'platforms': self.platforms,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        if include_stats:
            # Stats would be computed by the service layer
            result['stats'] = {
                'total_ads': 0,
                'active_ads': 0,
                'saved_ads': 0,
                'unique_pages': 0,
                'last_collection': None
            }

        return result

    def __repr__(self):
        return f'<Niche {self.name} ({self.slug})>'
