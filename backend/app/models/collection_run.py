"""
CollectionRun model - tracks data collection history.

Records each collection run with statistics and status.
"""
from app import db
from app.utils.ids import generate_uuid, now_iso8601


class CollectionRun(db.Model):
    """
    Tracks data collection history per niche.

    DynamoDB Access Pattern:
        PK: niche_id (partition key)
        SK: "RUN#<timestamp>#<uuid>" (sort key)

    Attributes:
        run_id: UUID primary key
        niche_id: UUID of the niche
        keyword: Keyword used for collection
        status: pending, running, completed, error
        ads_collected: Total ads collected
        ads_new: New ads found
        ads_updated: Existing ads updated
        error_message: Error message if failed
        started_at: When the run started
        completed_at: When the run completed
    """
    __tablename__ = 'collection_runs'

    # Primary key
    run_id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    # Niche association
    niche_id = db.Column(db.String(36), nullable=False, index=True)

    # Collection details
    keyword = db.Column(db.String(200), nullable=True)

    # Status: pending, running, completed, error
    status = db.Column(db.String(20), default='pending')

    # Statistics
    ads_collected = db.Column(db.Integer, default=0)
    ads_new = db.Column(db.Integer, default=0)
    ads_updated = db.Column(db.Integer, default=0)

    # Error handling
    error_message = db.Column(db.Text, nullable=True)

    # Timestamps
    started_at = db.Column(db.String(30), default=now_iso8601)
    completed_at = db.Column(db.String(30), nullable=True)

    # Index for status queries
    __table_args__ = (
        db.Index('ix_niche_status', 'niche_id', 'status'),
    )

    def to_dict(self) -> dict:
        """Convert collection run to dictionary for API responses."""
        return {
            'id': self.run_id,
            'niche_id': self.niche_id,
            'keyword': self.keyword,
            'status': self.status,
            'stats': {
                'ads_collected': self.ads_collected,
                'ads_new': self.ads_new,
                'ads_updated': self.ads_updated
            },
            'error_message': self.error_message,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }

    def mark_running(self):
        """Mark the run as running."""
        self.status = 'running'
        self.started_at = now_iso8601()

    def mark_completed(self, ads_collected: int = 0, ads_new: int = 0, ads_updated: int = 0):
        """Mark the run as completed with statistics."""
        self.status = 'completed'
        self.ads_collected = ads_collected
        self.ads_new = ads_new
        self.ads_updated = ads_updated
        self.completed_at = now_iso8601()

    def mark_error(self, error_message: str):
        """Mark the run as failed with error message."""
        self.status = 'error'
        self.error_message = error_message
        self.completed_at = now_iso8601()

    def __repr__(self):
        return f'<CollectionRun {self.run_id} ({self.status})>'
