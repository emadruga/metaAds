"""
Tests for niche CRUD endpoints.
"""
import json


def test_list_niches_empty(client, db_session):
    """Test listing niches when none exist."""
    response = client.get('/api/niches')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data'] == []
    assert data['count'] == 0


def test_create_niche(client, db_session):
    """Test creating a new niche."""
    response = client.post(
        '/api/niches',
        data=json.dumps({
            'name': 'Video Editing Apps',
            'keywords': ['video editor', 'AI video'],
            'countries': ['US', 'BR']
        }),
        content_type='application/json'
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['name'] == 'Video Editing Apps'
    assert data['data']['slug'] == 'video-editing-apps'
    assert data['data']['keywords'] == ['video editor', 'AI video']


def test_create_niche_requires_name(client, db_session):
    """Test that creating a niche requires a name."""
    response = client.post(
        '/api/niches',
        data=json.dumps({'keywords': ['test']}),
        content_type='application/json'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'error' in data


def test_create_duplicate_niche(client, db_session):
    """Test that duplicate slugs are rejected."""
    # Create first niche
    client.post(
        '/api/niches',
        data=json.dumps({'name': 'Test Niche'}),
        content_type='application/json'
    )

    # Try to create duplicate
    response = client.post(
        '/api/niches',
        data=json.dumps({'name': 'Test Niche'}),
        content_type='application/json'
    )

    assert response.status_code == 409
    data = response.get_json()
    assert data['success'] is False


def test_get_niche(client, sample_niche):
    """Test getting a niche by slug."""
    response = client.get('/api/niches/test-niche')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['name'] == 'Test Niche'
    assert 'stats' in data['data']


def test_get_niche_not_found(client, db_session):
    """Test getting a non-existent niche."""
    response = client.get('/api/niches/nonexistent')

    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False


def test_update_niche(client, sample_niche):
    """Test updating a niche."""
    response = client.patch(
        '/api/niches/test-niche',
        data=json.dumps({
            'description': 'Updated description',
            'color': '#FF0000'
        }),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['description'] == 'Updated description'
    assert data['data']['color'] == '#FF0000'


def test_delete_niche(client, sample_niche):
    """Test soft-deleting a niche."""
    response = client.delete('/api/niches/test-niche')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

    # Verify niche is no longer returned in list
    list_response = client.get('/api/niches')
    assert list_response.get_json()['count'] == 0


def test_niche_stats(client, sample_niche):
    """Test getting niche statistics."""
    response = client.get('/api/niches/test-niche/stats')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'stats' in data['data']
    assert 'total_ads' in data['data']['stats']
