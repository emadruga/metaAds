"""
User Service - Business logic for user operations.
"""
from app import db
from app.models.user import User
from app.utils.ids import now_iso8601


class UserService:
    """Service class for user-related operations."""

    @staticmethod
    def get_user_by_id(user_id: str) -> User:
        """Get a user by their Clerk ID."""
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_email(email: str) -> User:
        """Get a user by email address."""
        return User.query.filter_by(email=email, is_active=True).first()

    @staticmethod
    def create_user(
        user_id: str,
        email: str,
        first_name: str = None,
        last_name: str = None,
        image_url: str = None
    ) -> User:
        """
        Create a new user.

        Args:
            user_id: Clerk user ID
            email: User's email address
            first_name: First name
            last_name: Last name
            image_url: Profile image URL

        Returns:
            User: Created user instance
        """
        user = User(
            id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            image_url=image_url,
            created_at=now_iso8601()
        )

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def update_user(
        user_id: str,
        email: str = None,
        first_name: str = None,
        last_name: str = None,
        image_url: str = None
    ) -> User:
        """
        Update an existing user.

        Args:
            user_id: Clerk user ID
            email: New email address
            first_name: New first name
            last_name: New last name
            image_url: New profile image URL

        Returns:
            User: Updated user instance or None if not found
        """
        user = User.query.get(user_id)
        if not user:
            return None

        if email:
            user.email = email
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if image_url is not None:
            user.image_url = image_url

        user.updated_at = now_iso8601()
        db.session.commit()

        return user

    @staticmethod
    def deactivate_user(user_id: str) -> bool:
        """
        Soft delete a user by setting is_active=False.

        Args:
            user_id: Clerk user ID

        Returns:
            bool: True if deactivated, False if not found
        """
        user = User.query.get(user_id)
        if not user:
            return False

        user.is_active = False
        user.updated_at = now_iso8601()
        db.session.commit()

        return True

    @staticmethod
    def record_sign_in(user_id: str) -> User:
        """
        Record a user sign-in.

        Args:
            user_id: Clerk user ID

        Returns:
            User: Updated user instance or None if not found
        """
        user = User.query.get(user_id)
        if not user:
            return None

        user.last_sign_in_at = now_iso8601()
        db.session.commit()

        return user
