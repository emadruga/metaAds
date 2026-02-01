"""
Pytest configuration and fixtures for MetAds Backend tests.
"""
import pytest
from app import create_app, db
from app.models import User, Niche, Ad, Page


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'DEV_AUTH_BYPASS': True,
        'DEV_USER_ID': 'test_user_001'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a fresh database session for each test."""
    with app.app_context():
        # Clear all tables
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

        yield db.session

        db.session.rollback()


@pytest.fixture
def sample_user(app, db_session):
    """Create a sample user."""
    from app.utils.ids import generate_uuid, now_iso8601

    with app.app_context():
        user = User(
            id='test_user_001',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            created_at=now_iso8601()
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_niche(app, db_session, sample_user):
    """Create a sample niche."""
    from app.utils.ids import generate_uuid, now_iso8601

    with app.app_context():
        niche = Niche(
            niche_id=generate_uuid(),
            user_id='test_user_001',
            slug='test-niche',
            name='Test Niche',
            description='A test niche',
            created_at=now_iso8601()
        )
        niche.keywords = ['test', 'keyword']
        niche.countries = ['US']
        db.session.add(niche)
        db.session.commit()
        return niche


@pytest.fixture
def sample_ad(app, db_session, sample_niche):
    """Create a sample ad."""
    from app.utils.ids import generate_uuid, now_iso8601

    with app.app_context():
        # Refresh niche to get attached instance
        niche = Niche.query.filter_by(slug='test-niche').first()

        ad = Ad(
            id=generate_uuid(),
            meta_ad_id='123456789',
            niche_id=niche.niche_id,
            page_id='page_001',
            page_name='Test Page',
            body='This is a test ad body',
            start_date='2025-01-01',
            is_active=True,
            created_at=now_iso8601()
        )
        db.session.add(ad)
        db.session.commit()
        return ad
