"""
Niche Service - Business logic for niche operations.
"""
import re
from app import db
from app.models.niche import Niche
from app.models.ad import Ad
from app.models.collection_run import CollectionRun
from app.middleware.auth import get_current_user_id
from app.utils.ids import generate_uuid, now_iso8601


class NicheService:
    """Service class for niche-related operations."""

    @staticmethod
    def get_user_niches() -> list:
        """Get all niches for the current user."""
        user_id = get_current_user_id()
        return Niche.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(Niche.created_at.desc()).all()

    @staticmethod
    def get_niche_by_slug(slug: str) -> Niche:
        """Get a niche by slug for the current user."""
        user_id = get_current_user_id()
        return Niche.query.filter_by(
            user_id=user_id,
            slug=slug,
            is_active=True
        ).first()

    @staticmethod
    def get_niche_by_id(niche_id: str) -> Niche:
        """Get a niche by ID for the current user."""
        user_id = get_current_user_id()
        return Niche.query.filter_by(
            user_id=user_id,
            niche_id=niche_id,
            is_active=True
        ).first()

    @staticmethod
    def create_niche(data: dict) -> Niche:
        """
        Create a new niche for the current user.

        Args:
            data: Dictionary containing niche fields

        Returns:
            Niche: Created niche instance

        Raises:
            ValueError: If slug already exists
        """
        user_id = get_current_user_id()

        # Generate slug if not provided
        slug = data.get('slug') or NicheService.slugify(data['name'])

        # Check if slug already exists for this user
        existing = Niche.query.filter_by(
            user_id=user_id,
            slug=slug
        ).first()

        if existing:
            raise ValueError(f"Niche with slug '{slug}' already exists")

        niche = Niche(
            niche_id=generate_uuid(),
            user_id=user_id,
            slug=slug,
            name=data['name'],
            description=data.get('description'),
            color=data.get('color', '#8B5CF6'),
            icon=data.get('icon', '📊'),
            created_at=now_iso8601()
        )

        # Set list properties
        if 'keywords' in data:
            niche.keywords = data['keywords']
        if 'countries' in data:
            niche.countries = data['countries']
        if 'platforms' in data:
            niche.platforms = data['platforms']

        db.session.add(niche)
        db.session.commit()

        return niche

    @staticmethod
    def update_niche(slug: str, data: dict) -> Niche:
        """
        Update a niche for the current user.

        Args:
            slug: Niche slug
            data: Dictionary of fields to update

        Returns:
            Niche: Updated niche instance or None if not found
        """
        niche = NicheService.get_niche_by_slug(slug)
        if not niche:
            return None

        if 'name' in data:
            niche.name = data['name']
        if 'description' in data:
            niche.description = data['description']
        if 'color' in data:
            niche.color = data['color']
        if 'icon' in data:
            niche.icon = data['icon']
        if 'keywords' in data:
            niche.keywords = data['keywords']
        if 'countries' in data:
            niche.countries = data['countries']
        if 'platforms' in data:
            niche.platforms = data['platforms']

        niche.updated_at = now_iso8601()
        db.session.commit()

        return niche

    @staticmethod
    def delete_niche(slug: str) -> bool:
        """
        Soft delete a niche.

        Args:
            slug: Niche slug

        Returns:
            bool: True if deleted, False if not found
        """
        niche = NicheService.get_niche_by_slug(slug)
        if not niche:
            return False

        niche.is_active = False
        niche.updated_at = now_iso8601()
        db.session.commit()

        return True

    @staticmethod
    def get_niche_stats(niche_id: str) -> dict:
        """
        Get statistics for a niche.

        Args:
            niche_id: UUID of the niche

        Returns:
            dict: Statistics including total_ads, active_ads, etc.
        """
        total_ads = Ad.query.filter_by(niche_id=niche_id).count()
        active_ads = Ad.query.filter_by(niche_id=niche_id, is_active=True).count()
        saved_ads = Ad.query.filter_by(niche_id=niche_id, is_saved=True).count()
        unique_pages = db.session.query(Ad.page_id).filter_by(
            niche_id=niche_id
        ).distinct().count()

        # Get last collection run
        last_run = CollectionRun.query.filter_by(
            niche_id=niche_id,
            status='completed'
        ).order_by(CollectionRun.completed_at.desc()).first()

        return {
            'total_ads': total_ads,
            'active_ads': active_ads,
            'saved_ads': saved_ads,
            'unique_pages': unique_pages,
            'last_collection': last_run.completed_at if last_run else None
        }

    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to URL-friendly slug."""
        slug = text.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        slug = re.sub(r'^-+|-+$', '', slug)
        return slug
