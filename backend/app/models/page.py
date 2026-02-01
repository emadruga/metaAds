"""
Page model - global page registry.

Stores information about Facebook/Instagram pages
that have been encountered during ad collection.
"""
from app import db
from app.utils.ids import now_iso8601


class Page(db.Model):
    """
    Global page registry.

    DynamoDB Access Pattern:
        PK: page_id (partition key)
        SK: "METADATA" (sort key - constant)

    Attributes:
        page_id: Meta page ID (primary key)
        page_name: Display name of the page
        is_verified: Whether the page is verified
        first_seen: When the page was first encountered
        last_seen: When the page was last seen
    """
    __tablename__ = 'pages'

    # Primary key (Meta page ID)
    page_id = db.Column(db.String(100), primary_key=True)

    # Page info
    page_name = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

    # Tracking
    first_seen = db.Column(db.String(30), default=now_iso8601)
    last_seen = db.Column(db.String(30), default=now_iso8601)

    # Timestamps
    created_at = db.Column(db.String(30), default=now_iso8601)
    updated_at = db.Column(db.String(30), default=now_iso8601, onupdate=now_iso8601)

    def to_dict(self) -> dict:
        """Convert page to dictionary for API responses."""
        return {
            'id': self.page_id,
            'name': self.page_name,
            'is_verified': self.is_verified,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen
        }

    def __repr__(self):
        return f'<Page {self.page_name} ({self.page_id})>'
