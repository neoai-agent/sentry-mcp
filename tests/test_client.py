"""Tests for the Sentry client."""
import pytest
from unittest.mock import Mock, patch
from sentry_mcp.client import SentryClient, SentryClientConfig


@pytest.fixture
def sentry_config():
    """Create a test SentryClientConfig."""
    return SentryClientConfig(
        api_token="test-token",
        organization="test-org",
        host="https://sentry.io"
    )


@pytest.fixture
def sentry_client(sentry_config):
    """Create a test SentryClient."""
    return SentryClient(
        config=sentry_config,
        model="openai/gpt-4o-mini",
        openai_api_key="test-openai-key"
    )


def test_sentry_client_config(sentry_config):
    """Test SentryClientConfig creation."""
    assert sentry_config.api_token == "test-token"
    assert sentry_config.organization == "test-org"
    assert sentry_config.host == "https://sentry.io"


def test_sentry_client_initialization(sentry_client):
    """Test SentryClient initialization."""
    assert sentry_client.config.api_token == "test-token"
    assert sentry_client.config.organization == "test-org"
    assert sentry_client.base_url == "https://sentry.io/api/0"


@patch('requests.Session.request')
def test_make_request_success(mock_request, sentry_client):
    """Test successful API request."""
    mock_response = Mock()
    mock_response.json.return_value = {"test": "data"}
    mock_response.raise_for_status.return_value = None
    mock_request.return_value = mock_response

    result = sentry_client._make_request('GET', '/test-endpoint')
    
    assert result == {"test": "data"}
    mock_request.assert_called_once()


@patch('requests.Session.request')
def test_make_request_failure(mock_request, sentry_client):
    """Test failed API request."""
    mock_request.side_effect = Exception("API Error")

    with pytest.raises(Exception):
        sentry_client._make_request('GET', '/test-endpoint')


def test_get_organization_projects(sentry_client):
    """Test get_organization_projects method."""
    with patch.object(sentry_client, '_make_request') as mock_request:
        mock_request.return_value = [{"name": "Test Project", "slug": "test-project"}]
        
        result = sentry_client.get_organization_projects()
        
        assert result == [{"name": "Test Project", "slug": "test-project"}]
        mock_request.assert_called_once_with('GET', '/projects/')


def test_get_project_details(sentry_client):
    """Test get_project_details method."""
    with patch.object(sentry_client, '_make_request') as mock_request:
        mock_request.return_value = {"name": "Test Project", "slug": "test-project"}
        
        result = sentry_client.get_project_details("test-project")
        
        assert result == {"name": "Test Project", "slug": "test-project"}
        mock_request.assert_called_once_with('GET', '/projects/test-org/test-project/')


@pytest.mark.asyncio
async def test_find_matching_project_exact_match(sentry_client):
    """Test find_matching_project with exact match."""
    with patch.object(sentry_client, 'get_all_projects') as mock_get_projects:
        mock_get_projects.return_value = [
            {"name": "Test Project", "slug": "test-project"},
            {"name": "Another Project", "slug": "another-project"}
        ]
        
        result = await sentry_client.find_matching_project("test-project")
        
        assert result == {"project_slug": "test-project", "project_name": "Test Project"}


@pytest.mark.asyncio
async def test_find_matching_project_no_match(sentry_client):
    """Test find_matching_project with no match."""
    with patch.object(sentry_client, 'get_all_projects') as mock_get_projects:
        mock_get_projects.return_value = [
            {"name": "Test Project", "slug": "test-project"},
            {"name": "Another Project", "slug": "another-project"}
        ]
        
        # Mock the AI method to return an error when no good match is found
        with patch.object(sentry_client, '_find_best_match_ai') as mock_ai:
            mock_ai.return_value = {"error": "No project found matching 'non-existent'"}
            
            result = await sentry_client.find_matching_project("non-existent")
            
            assert "error" in result
