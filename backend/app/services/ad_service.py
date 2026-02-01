"""
Ad Service - Business logic for ad operations.
"""
from typing import List, Optional
from app import db
from app.models.ad import Ad
from app.models.niche import Niche
from app.models.page import Page
from app.models.niche_page import NichePage
from app.utils.ids import generate_uuid, now_iso8601


class AdService:
    """Service class for ad-related operations."""

    @staticmethod
    def get_ads_by_niche(
        niche_id: str,
        filters: dict = None,
        sort_by: str = 'days_active',
        sort_order: str = 'desc',
        page: int = 1,
        per_page: int = 20
    ) -> tuple:
        """
        Get ads for a niche with filters and pagination.

        Args:
            niche_id: UUID of the niche
            filters: Dictionary of filter criteria
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            page: Page number
            per_page: Results per page

        Returns:
            tuple: (list of ads, total count, has_more)
        """
        query = Ad.query.filter_by(niche_id=niche_id)

        if filters:
            # Apply filters
            if 'q' in filters and filters['q']:
                query = query.filter(Ad.full_text.ilike(f"%{filters['q']}%"))

            if 'is_active' in filters:
                query = query.filter_by(is_active=filters['is_active'])

            if 'min_days' in filters:
                query = query.filter(Ad.days_active >= filters['min_days'])

            if 'max_days' in filters:
                query = query.filter(Ad.days_active <= filters['max_days'])

            if 'cta' in filters and filters['cta']:
                query = query.filter_by(cta_detected=filters['cta'])

            if 'page_id' in filters and filters['page_id']:
                query = query.filter_by(page_id=filters['page_id'])

        # Sorting
        sort_column = getattr(Ad, sort_by, Ad.days_active)
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return pagination.items, pagination.total, pagination.has_next

    @staticmethod
    def get_ad_by_id(niche_id: str, ad_id: str) -> Optional[Ad]:
        """Get an ad by ID within a niche."""
        return Ad.query.filter_by(
            niche_id=niche_id,
            id=ad_id
        ).first()

    @staticmethod
    def get_related_ads(niche_id: str, ad: Ad, limit: int = 20) -> List[Ad]:
        """
        Get related ads (variants) for an ad.

        Related ads are from the same page.
        """
        return Ad.query.filter(
            Ad.niche_id == niche_id,
            Ad.page_id == ad.page_id,
            Ad.id != ad.id
        ).order_by(Ad.start_date.desc()).limit(limit).all()

    @staticmethod
    def save_ad(ad: Ad, notes: str = None, tags: list = None) -> Ad:
        """
        Save an ad to the user's saved collection.

        Args:
            ad: Ad instance to save
            notes: Optional notes
            tags: Optional list of tags

        Returns:
            Ad: Updated ad instance
        """
        ad.is_saved = True
        ad.saved_at = now_iso8601()
        ad.saved_notes = notes
        if tags:
            ad.saved_tags = tags

        db.session.commit()
        return ad

    @staticmethod
    def unsave_ad(ad: Ad) -> Ad:
        """
        Remove an ad from the user's saved collection.

        Args:
            ad: Ad instance to unsave

        Returns:
            Ad: Updated ad instance
        """
        ad.is_saved = False
        ad.saved_at = None
        ad.saved_notes = None
        ad.saved_tags = None

        db.session.commit()
        return ad

    @staticmethod
    def create_or_update_ad(niche_id: str, ad_data: dict) -> tuple:
        """
        Create a new ad or update existing one.

        Args:
            niche_id: UUID of the niche
            ad_data: Dictionary of ad fields from parser

        Returns:
            tuple: (Ad instance, is_new: bool)
        """
        # Check if ad already exists
        existing = Ad.query.filter_by(
            niche_id=niche_id,
            meta_ad_id=ad_data['ad_id']
        ).first()

        if existing:
            # Update existing ad
            existing.is_active = ad_data.get('is_active', existing.is_active)
            existing.end_date = ad_data.get('end_date', existing.end_date)
            existing.days_active = ad_data.get('days_active', existing.days_active)
            existing.updated_at = now_iso8601()
            db.session.commit()
            return existing, False

        # Create new ad
        ad = Ad(
            id=generate_uuid(),
            niche_id=niche_id,
            meta_ad_id=ad_data['ad_id'],
            page_id=ad_data.get('page_id'),
            page_name=ad_data.get('page_name'),
            start_date=ad_data.get('start_date'),
            end_date=ad_data.get('end_date'),
            is_active=ad_data.get('is_active', True),
            days_active=ad_data.get('days_active', 0),
            snapshot_url=ad_data.get('snapshot_url'),
            body=ad_data.get('body'),
            headline=ad_data.get('headline'),
            description=ad_data.get('description'),
            link_caption=ad_data.get('link_caption'),
            full_text=ad_data.get('full_text'),
            cta_detected=ad_data.get('cta_detected'),
            text_length=ad_data.get('text_length', 0),
            has_emoji=ad_data.get('has_emoji', False),
            has_hashtags=ad_data.get('has_hashtags', False),
            search_keyword=ad_data.get('search_keyword'),
            created_at=now_iso8601()
        )

        # Set list properties
        if 'platforms' in ad_data:
            ad.platforms = ad_data['platforms']
        if 'hashtags' in ad_data:
            ad.hashtags = ad_data['hashtags']
        if 'mentions' in ad_data:
            ad.mentions = ad_data['mentions']
        if 'country_codes' in ad_data:
            ad.country_codes = ad_data['country_codes']

        db.session.add(ad)

        # Update or create page entry
        AdService._update_page(ad_data, niche_id)

        db.session.commit()
        return ad, True

    @staticmethod
    def _update_page(ad_data: dict, niche_id: str):
        """Update or create page and niche_page entries."""
        page_id = ad_data.get('page_id')
        if not page_id:
            return

        # Update global page registry
        page = Page.query.get(page_id)
        if not page:
            page = Page(
                page_id=page_id,
                page_name=ad_data.get('page_name', 'Unknown'),
                first_seen=now_iso8601(),
                last_seen=now_iso8601()
            )
            db.session.add(page)
        else:
            page.last_seen = now_iso8601()

        # Update niche_page entry
        niche_page = NichePage.query.filter_by(
            niche_id=niche_id,
            page_id=page_id
        ).first()

        if not niche_page:
            niche_page = NichePage(
                id=generate_uuid(),
                niche_id=niche_id,
                page_id=page_id,
                page_name=ad_data.get('page_name', 'Unknown'),
                total_ads_in_niche=1,
                added_at=now_iso8601()
            )
            db.session.add(niche_page)
        else:
            niche_page.total_ads_in_niche += 1
