"""Unit tests for the AccountScanner."""

from unittest.mock import AsyncMock, patch

import pytest

from guard.core.scanner import AccountScanner
from guard.models.risk import AccountRiskReport


@pytest.mark.asyncio
async def test_run_scan_success():
    """Tests the full scan orchestration successfully."""
    mock_user = {
        "id": "1", "username": "test", "discriminator": "0001", 
        "mfa_enabled": True, "flags": 0
    }
    mock_apps = [
        {
            "application": {"id": "app1", "name": "Test App", "description": "desc"},
            "scopes": ["identify"]
        }
    ]
    mock_sessions = {"sessions": [{"session_id": "sess1", "client_info": {"os": "win"}}], "note": None}

    with patch("guard.core.scanner.DiscordClient") as MockClient:
        instance = MockClient.return_value
        instance.get_me = AsyncMock(return_value=mock_user)
        instance.get_authorized_apps = AsyncMock(return_value=mock_apps)
        instance.get_sessions = AsyncMock(return_value=mock_sessions)

        scanner = AccountScanner("token")
        report = await scanner.run_scan()

        assert isinstance(report, AccountRiskReport)
        assert report.user_id == "1"
        assert len(report.authorized_apps) == 1
        assert len(report.active_sessions) == 1
        assert report.overall_score == 0
        assert report.sessions_note is None
