"""Unit tests for the Discord API client."""

import pytest
from pytest_httpx import HTTPXMock
from guard.api.discord import DiscordClient, InvalidTokenError, RateLimitError, DiscordAPIError


@pytest.mark.asyncio
async def test_get_me_success(httpx_mock: HTTPXMock):
    """Tests fetching current user info successfully."""
    mock_response = {"id": "123456789", "username": "testuser", "discriminator": "0001"}
    httpx_mock.add_response(
        method="GET",
        url="https://discord.com/api/v10/users/@me",
        json=mock_response,
        status_code=200,
    )

    client = DiscordClient("valid_token")
    user_info = await client.get_me()

    assert user_info["id"] == "123456789"
    assert user_info["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_me_invalid_token(httpx_mock: HTTPXMock):
    """Tests fetching current user info with an invalid token."""
    httpx_mock.add_response(
        method="GET",
        url="https://discord.com/api/v10/users/@me",
        status_code=401,
    )

    client = DiscordClient("invalid_token")
    with pytest.raises(InvalidTokenError):
        await client.get_me()


@pytest.mark.asyncio
async def test_get_me_rate_limit(httpx_mock: HTTPXMock):
    """Tests fetching current user info when rate limited."""
    httpx_mock.add_response(
        method="GET",
        url="https://discord.com/api/v10/users/@me",
        status_code=429,
        headers={"Retry-After": "5"},
    )

    client = DiscordClient("valid_token")
    with pytest.raises(RateLimitError) as excinfo:
        await client.get_me()
    
    assert "Retry after 5s" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_authorized_apps_success(httpx_mock: HTTPXMock):
    """Tests fetching authorized apps successfully."""
    mock_response = [{"id": "app1", "application": {"name": "Test App"}}]
    httpx_mock.add_response(
        method="GET",
        url="https://discord.com/api/v10/oauth2/tokens",
        json=mock_response,
        status_code=200,
    )

    client = DiscordClient("valid_token")
    apps = await client.get_authorized_apps()

    assert len(apps) == 1
    assert apps[0]["application"]["name"] == "Test App"


@pytest.mark.asyncio
async def test_get_sessions_success(httpx_mock: HTTPXMock):
    """Tests fetching active sessions successfully."""
    mock_response = [{"session_id": "sess1", "client_info": {"os": "windows"}}]
    httpx_mock.add_response(
        method="GET",
        url="https://discord.com/api/v10/auth/sessions",
        json=mock_response,
        status_code=200,
    )

    client = DiscordClient("valid_token")
    result = await client.get_sessions()

    assert len(result["sessions"]) == 1
    assert result["sessions"][0]["client_info"]["os"] == "windows"
    assert result["note"] is None


@pytest.mark.asyncio
async def test_get_sessions_error_fallback(httpx_mock: HTTPXMock):
    """Tests fetching active sessions when the endpoint fails (returns explanatory note)."""
    httpx_mock.add_response(
        method="GET",
        url="https://discord.com/api/v10/auth/sessions",
        status_code=404,  # Hypothetical failure
    )

    client = DiscordClient("valid_token")
    result = await client.get_sessions()

    assert result["sessions"] == []
    assert "Discord limits active session visibility" in result["note"]


@pytest.mark.asyncio
async def test_revoke_app_success(httpx_mock: HTTPXMock):
    """Tests revoking an app successfully."""
    httpx_mock.add_response(
        method="DELETE",
        url="https://discord.com/api/v10/oauth2/tokens/123",
        status_code=204,
    )

    client = DiscordClient("valid_token")
    await client.revoke_app("123")
    # If no exception, it's considered successful
