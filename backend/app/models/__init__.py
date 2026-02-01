"""
SQLAlchemy Models for MetAds

All models use UUIDs for primary keys and ISO8601 strings for dates
to ensure compatibility with DynamoDB for future cloud migration.
"""
from app.models.user import User
from app.models.niche import Niche
from app.models.ad import Ad
from app.models.page import Page
from app.models.niche_page import NichePage
from app.models.collection_run import CollectionRun

__all__ = [
    'User',
    'Niche',
    'Ad',
    'Page',
    'NichePage',
    'CollectionRun'
]
