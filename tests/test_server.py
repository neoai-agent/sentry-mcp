"""Tests for the Sentry MCP server."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from sentry_mcp.server import SentryMCPServer
from sentry_mcp.client import SentryClientConfig


@pytest.fixture
def sentry_config():
    """Create a test SentryClientConfig."""
    return SentryClientConfig(
        api_token="test-token",
        organization="test-org",
        host="https://sentry.io"
    )


@pytest.fixture
def sentry_server(sentry_config):
    """Create a test SentryMCPServer."""
    return SentryMCPServer(
        model="openai/gpt-4o-mini",
        openai_api_key="test-openai-key",
        sentry_config=sentry_config
    )


def test_sentry_server_initialization(sentry_server):
    """Test SentryMCPServer initialization."""
    assert sentry_server is not None
    assert hasattr(sentry_server, 'client')
    assert hasattr(sentry_server, 'mcp')
    assert hasattr(sentry_server, 'get_project_health')
    assert hasattr(sentry_server, 'get_recent_issues')
    assert hasattr(sentry_server, 'get_issue_analysis')
    assert hasattr(sentry_server, 'get_issue_trends')


@pytest.mark.asyncio
async def test_get_project_health_success(sentry_server):
    """Test get_project_health with successful response."""
    with patch.object(sentry_server.client, 'find_matching_project') as mock_find:
        mock_find.return_value = {
            "project_slug": "test-project",
            "project_name": "Test Project"
        }
        
        with patch.object(sentry_server.client, 'get_project_details') as mock_details:
            mock_details.return_value = {
                "status": "active",
                "platform": "python",
                "dateCreated": "2024-01-01",
                "latestRelease": "1.0.0"
            }
            
            result = await sentry_server.get_project_health("test-project")
            
            assert result["project_name"] == "Test Project"
            assert result["project_slug"] == "test-project"
            assert result["health_status"] == "active"
            assert result["platform"] == "python"
            assert "recent_issues_count" in result
            assert "latestRelease" in result



@pytest.mark.asyncio
async def test_get_recent_issues_success(sentry_server):
    """Test get_recent_issues with successful response."""
    with patch.object(sentry_server.client, 'find_matching_project') as mock_find:
        mock_find.return_value = {
            "project_slug": "test-project",
            "project_name": "Test Project"
        }
        
        with patch.object(sentry_server.client, 'get_project_issues') as mock_issues:
            mock_issues.return_value = {"data": [{"id": 1}, {"id": 2}]}
            
            result = await sentry_server.get_recent_issues("test-project", time_range_minutes=60)
            
            assert result["project_name"] == "Test Project"
            assert result["project_slug"] == "test-project"
            assert result["time_range_minutes"] == 60
            assert "issues" in result


@pytest.mark.asyncio
async def test_get_issue_analysis_success(sentry_server):
    """Test get_issue_analysis with successful response."""
    with patch.object(sentry_server.client, 'get_issue_details') as mock_details:
        mock_details.return_value = {
            "id": "123",
            "title": "Test Issue",
            "status": "unresolved",
            "level": "error"
        }
        
        with patch.object(sentry_server.client, 'get_issue_events') as mock_events:
            mock_events.return_value = {"data": [{"id": 1}, {"id": 2}]}
            
            with patch.object(sentry_server.client, 'get_issue_latest_event') as mock_latest:
                mock_latest.return_value = {"id": "latest-event"}
                
                result = await sentry_server.get_issue_analysis("123")
                
                assert result["issue_id"] == "123"
                assert result["title"] == "Test Issue"
                assert result["status"] == "unresolved"
                assert result["level"] == "error"
                assert "events_count" in result


@pytest.mark.asyncio
async def test_get_issue_trends_success(sentry_server):
    """Test get_issue_trends with successful response."""
    with patch.object(sentry_server.client, 'get_issue_details') as mock_details:
        mock_details.return_value = {
            "id": "123",
            "title": "Test Issue",
            "stats": {
                "24h": [[1640995200, 10], [1640998800, 15]],
                "30d": [[1640995200, 100], [1641081600, 150]]
            }
        }
        
        result = await sentry_server.get_issue_trends("123")
        
        assert result["issue_id"] == "123"
        assert result["title"] == "Test Issue"
        assert "24h_summary" in result
        assert "30d_summary" in result
