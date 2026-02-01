"""
Tests for ads endpoints.
"""
import json


def test_search_ads_empty(client, sample_niche):
    """Test searching ads when none exist."""
    response = client.get('/api/niches/test-niche/ads/search')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data'] == []
    assert data['pagination']['total'] == 0


def test_search_ads_with_results(client, sample_ad, app):
    """Test searching ads returns results."""
    with app.app_context():
        response = client.get('/api/niches/test-niche/ads/search')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['meta_ad_id'] == '123456789'


def test_search_ads_with_query(client, sample_ad, app):
    """Test searching ads with query parameter."""
    with app.app_context():
        response = client.get('/api/niches/test-niche/ads/search?q=test')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


def test_get_ad_detail(client, sample_ad, app):
    """Test getting ad details."""
    with app.app_context():
        from app.models import Ad
        ad = Ad.query.first()

        response = client.get(f'/api/niches/test-niche/ads/{ad.id}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['meta_ad_id'] == '123456789'


def test_get_ad_not_found(client, sample_niche):
    """Test getting non-existent ad."""
    response = client.get('/api/niches/test-niche/ads/nonexistent-id')

    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False


def test_get_related_ads(client, sample_ad, app):
    """Test getting related ads."""
    with app.app_context():
        from app.models import Ad
        ad = Ad.query.first()

        response = client.get(f'/api/niches/test-niche/ads/{ad.id}/related')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'original' in data['data']
        assert 'related' in data['data']
        assert 'insights' in data['data']
