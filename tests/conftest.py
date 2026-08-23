import pytest
from src.app import create_app
import responses

@pytest.fixture
def app():
    """Create app with test configuration"""
    app = create_app({
        'TESTING': True,
        'RAGNAR_BASE_URL': 'https://ragnar.test.local',
    })
    yield app

@pytest.fixture
def client(app):
    """Test client for sending requests to app"""
    return app.test_client()

@pytest.fixture
def mock_ragnar_api():
    """Imitate Ragnar API calls using responses library"""
    with responses.RequestsMock() as resp:
        yield resp
