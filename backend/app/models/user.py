"""
User model - synced from Clerk via webhooks.

Stores minimal user data for query efficiency.
Primary key matches Clerk user ID for easy lookup.
"""
from app import db
from app.utils.ids import now_iso8601


class User(db.Model):
    """
    User model synced from Clerk.

    Attributes:
        id: Clerk user ID (primary key)
        email: User's email address (unique)
        first_name: User's first name
        last_name: User's last name
        image_url: Profile image URL from Clerk
        is_active: Whether the user account is active
        created_at: When the user was created (ISO8601)
        updated_at: Last update timestamp (ISO8601)
        last_sign_in_at: Last sign in timestamp (ISO8601)
    """
    __tablename__ = 'users'

    # Primary key matches Clerk user ID
    id = db.Column(db.String(100), primary_key=True)

    # Basic info (synced from Clerk)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.Text, nullable=True)

    # Account status
    is_active = db.Column(db.Boolean, default=True)

    # Timestamps (ISO8601 strings)
    created_at = db.Column(db.String(30), default=now_iso8601)
    updated_at = db.Column(db.String(30), default=now_iso8601, onupdate=now_iso8601)
    last_sign_in_at = db.Column(db.String(30), nullable=True)

    def to_dict(self) -> dict:
        """Convert user to dictionary for API responses."""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'created_at': self.created_at
        }

    def __repr__(self):
        return f'<User {self.email}>'
