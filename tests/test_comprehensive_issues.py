"""Tests for the comprehensive issue analysis functionality."""
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


def test_sentry_client_comprehensive_issue_methods(sentry_server):
    """Test that the server has the expected comprehensive issue methods."""
    # This test verifies that the server has the methods we expect
    assert hasattr(sentry_server, 'get_project_health')
    assert hasattr(sentry_server, 'get_recent_issues')
    assert hasattr(sentry_server, 'get_issue_analysis')
    assert hasattr(sentry_server, 'get_issue_trends')
    
    # Verify these are async methods
    import inspect
    assert inspect.iscoroutinefunction(sentry_server.get_project_health)
    assert inspect.iscoroutinefunction(sentry_server.get_recent_issues)
    assert inspect.iscoroutinefunction(sentry_server.get_issue_analysis)
    assert inspect.iscoroutinefunction(sentry_server.get_issue_trends)
