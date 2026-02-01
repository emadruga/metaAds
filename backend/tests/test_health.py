"""
Tests for health check endpoint.
"""


def test_health_check(client):
    """Test health check endpoint returns correct response."""
    response = client.get('/api/health')

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'version' in data


def test_health_check_dev_mode(client, app):
    """Test health check shows dev mode status."""
    response = client.get('/api/health')

    data = response.get_json()
    assert data['dev_mode'] == app.config.get('DEV_AUTH_BYPASS', False)
