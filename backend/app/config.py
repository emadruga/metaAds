"""
Configuration settings for MetAds Backend
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///../data/ads_intelligence.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173')

    # Clerk Authentication
    CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY', '')
    CLERK_PUBLISHABLE_KEY = os.getenv('CLERK_PUBLISHABLE_KEY', '')
    CLERK_WEBHOOK_SECRET = os.getenv('CLERK_WEBHOOK_SECRET', '')

    # Dev Mode - bypass auth for local testing (NEVER enable in production!)
    DEV_AUTH_BYPASS = os.getenv('DEV_AUTH_BYPASS', 'false').lower() == 'true'
    DEV_USER_ID = os.getenv('DEV_USER_ID', 'dev_user_001')

    # Meta API
    FB_ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN', '')
    FB_API_VERSION = os.getenv('FB_API_VERSION', 'v18.0')
    FB_BASE_URL = f'https://graph.facebook.com/{FB_API_VERSION}'

    # Rate Limiting
    API_RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', '200'))
    API_RETRY_ATTEMPTS = int(os.getenv('API_RETRY_ATTEMPTS', '3'))
    API_RETRY_DELAY = int(os.getenv('API_RETRY_DELAY', '5'))

    # Analysis
    MIN_AD_DAYS_ACTIVE = int(os.getenv('MIN_AD_DAYS_ACTIVE', '30'))
    TOP_N_KEYWORDS = int(os.getenv('TOP_N_KEYWORDS', '50'))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
