# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Meta API
    FB_ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN')
    FB_API_VERSION = 'v20.0'  # Updated to latest stable version
    FB_BASE_URL = f'https://graph.facebook.com/{FB_API_VERSION}'

    # Rate Limiting
    API_RATE_LIMIT = 200  # requests per hour
    API_RETRY_ATTEMPTS = 3
    API_RETRY_DELAY = 5  # seconds

    # Database
    DB_PATH = 'data/ads_intelligence.db'

    # Scraping
    HEADLESS = True
    USER_AGENT = 'Mozilla/5.0...'

    # Analysis
    MIN_AD_DAYS_ACTIVE = 30  # considerar top performer
    TOP_N_KEYWORDS = 50
