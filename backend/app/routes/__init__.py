"""
API Routes for MetAds Backend
"""
from app.routes.auth import auth_bp
from app.routes.niches import niches_bp
from app.routes.ads import ads_bp
from app.routes.saved import saved_bp

__all__ = ['auth_bp', 'niches_bp', 'ads_bp', 'saved_bp']
