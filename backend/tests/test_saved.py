"""
Tests for saved ads endpoints.
"""
import json


def test_list_saved_empty(client, sample_niche):
    """Test listing saved ads when none exist."""
    response = client.get('/api/niches/test-niche/saved')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data'] == []
    assert data['tags'] == []


def test_save_ad(client, sample_ad, app):
    """Test saving an ad."""
    # Get ad_id outside the request context
    with app.app_context():
        from app.models import Ad
        ad = Ad.query.first()
        ad_id = ad.id

    response = client.post(
        f'/api/niches/test-niche/ads/{ad_id}/save',
        data=json.dumps({
            'notes': 'Great creative!',
            'tags': ['inspiration', 'video']
        }),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # to_dict() returns 'saved' object
    assert data['data']['saved']['is_saved'] is True
    assert data['data']['saved']['notes'] == 'Great creative!'


def test_unsave_not_saved_ad(client, sample_ad, app):
    """Test unsaving an ad that's not saved returns 400."""
    with app.app_context():
        from app.models import Ad
        ad = Ad.query.first()
        ad_id = ad.id

    response = client.delete(f'/api/niches/test-niche/ads/{ad_id}/save')

    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_list_saved_with_ads(client, sample_ad, app):
    """Test listing saved ads after saving one."""
    with app.app_context():
        from app.models import Ad
        ad = Ad.query.first()
        ad_id = ad.id

    # Save an ad
    client.post(
        f'/api/niches/test-niche/ads/{ad_id}/save',
        data=json.dumps({'tags': ['test-tag']}),
        content_type='application/json'
    )

    # List saved
    response = client.get('/api/niches/test-niche/saved')

    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']) == 1
    assert 'test-tag' in data['tags']


def test_save_unsave_update_workflow(client, sample_ad, app):
    """Test the full save/unsave/update workflow in a single test."""
    with app.app_context():
        from app.models import Ad
        ad = Ad.query.first()
        ad_id = ad.id

    # 1. Save the ad
    response = client.post(
        f'/api/niches/test-niche/ads/{ad_id}/save',
        data=json.dumps({'notes': 'Initial notes'}),
        content_type='application/json'
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['data']['saved']['is_saved'] is True

    # 2. Try to save again - should get 400
    response = client.post(
        f'/api/niches/test-niche/ads/{ad_id}/save',
        content_type='application/json'
    )
    assert response.status_code == 400

    # 3. Update the saved ad
    response = client.patch(
        f'/api/niches/test-niche/ads/{ad_id}/save',
        data=json.dumps({
            'notes': 'Updated notes',
            'tags': ['updated']
        }),
        content_type='application/json'
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['data']['saved']['notes'] == 'Updated notes'

    # 4. Unsave the ad
    response = client.delete(f'/api/niches/test-niche/ads/{ad_id}/save')
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Ad unsaved'

    # 5. Verify it's unsaved - update should fail
    response = client.patch(
        f'/api/niches/test-niche/ads/{ad_id}/save',
        data=json.dumps({'notes': 'Should fail'}),
        content_type='application/json'
    )
    assert response.status_code == 400
