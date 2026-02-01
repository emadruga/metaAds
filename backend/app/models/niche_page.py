"""
NichePage model - tracks pages per niche and competitor status.

Links pages to niches and allows marking pages as competitors.
"""
from app import db
from app.utils.ids import generate_uuid, now_iso8601


class NichePage(db.Model):
    """
    Tracks pages within a niche and their competitor status.

    DynamoDB Access Pattern:
        PK: niche_id (partition key)
        SK: "PAGE#<page_id>" (sort key)

    Attributes:
        id: Internal UUID
        niche_id: UUID of the containing niche
        page_id: Meta page ID
        page_name: Denormalized page name
        is_competitor: Whether marked as competitor
        notes: Optional notes about the page
        total_ads_in_niche: Denormalized count of ads
        added_at: When the page was added to this niche
    """
    __tablename__ = 'niche_pages'

    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    # Associations
    niche_id = db.Column(db.String(36), nullable=False, index=True)
    page_id = db.Column(db.String(100), nullable=False, index=True)

    # Denormalized data
    page_name = db.Column(db.String(200))

    # Competitor tracking
    is_competitor = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)

    # Stats (denormalized for quick access)
    total_ads_in_niche = db.Column(db.Integer, default=0)

    # Timestamps
    added_at = db.Column(db.String(30), default=now_iso8601)

    # Unique constraint: page can only be in a niche once
    __table_args__ = (
        db.UniqueConstraint('niche_id', 'page_id', name='uq_niche_page'),
        db.Index('ix_page_niche', 'page_id', 'niche_id'),
    )

    def to_dict(self) -> dict:
        """Convert niche page to dictionary for API responses."""
        return {
            'id': self.id,
            'page_id': self.page_id,
            'page_name': self.page_name,
            'is_competitor': self.is_competitor,
            'notes': self.notes,
            'total_ads': self.total_ads_in_niche,
            'added_at': self.added_at
        }

    def __repr__(self):
        return f'<NichePage {self.page_name} in niche {self.niche_id}>'
