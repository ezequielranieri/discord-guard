"""Integration tests for the discord-guard CLI."""

from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from guard.cli import app
from guard.models.account import AuthorizedApp
from guard.models.risk import AccountRiskReport, RiskLevel

runner = CliRunner()


@pytest.fixture
def mock_report():
    return AccountRiskReport(
        user_id="12345",
        username="testuser#0001",
        overall_score=70,
        overall_level=RiskLevel.CRITICAL,
        risks=[],
        authorized_apps=[],
        active_sessions=[],
        two_fa_enabled=False
    )


def test_help_command():
    """Tests that the help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Discord security scanner and protector" in result.stdout


def test_scan_command_no_token():
    """Tests that scan command fails without a token."""
    # Note: Typer might prompt for token if missing in some configurations, 
    # but with --token as required Option, it should show error if not provided 
    # and not interactive.
    result = runner.invoke(app, ["scan"])
    assert result.exit_code != 0


@patch("guard.cli.AccountScanner")
def test_scan_command_success(MockScanner, mock_report):
    """Tests scan command with a valid token (mocked)."""
    mock_scanner_instance = MockScanner.return_value
    mock_scanner_instance.run_scan = AsyncMock(return_value=mock_report)

    # We need to mock asyncio.run because CliRunner is synchronous 
    # and we are calling asyncio.run inside the command.
    # Actually, CliRunner handles it fine if we mock the internal async call.

    result = runner.invoke(app, ["scan", "--token", "valid_token"])
    
    assert result.exit_code == 0
    assert "discord-guard" in result.stdout
    assert "SECURITY REPORT" in result.stdout
    assert "CRITICAL" in result.stdout


@patch("guard.cli.AccountScanner")
def test_scan_command_invalid_token(MockScanner):
    """Tests scan command with an invalid token."""
    from guard.api.discord import InvalidTokenError
    
    mock_scanner_instance = MockScanner.return_value
    mock_scanner_instance.run_scan = AsyncMock(side_effect=InvalidTokenError("Invalid token"))

    result = runner.invoke(app, ["scan", "--token", "invalid_token"])
    
    assert result.exit_code == 0 # We handle the exception and print error
    assert "Error: The provided token is invalid" in result.stdout


@patch("guard.cli.AccountScanner")
@patch("guard.cli.DiscordClient")
def test_scan_command_with_revoke(MockClient, MockScanner, mock_report):
    """Tests scan command with interactive revocation flow."""
    # Add a suspicious app to the report
    mock_report.authorized_apps = [
        AuthorizedApp(id="app123", name="Suspicious App", scopes=["bot"])
    ]
    
    mock_scanner_instance = MockScanner.return_value
    mock_scanner_instance.run_scan = AsyncMock(return_value=mock_report)
    
    mock_client_instance = MockClient.return_value
    mock_client_instance.revoke_app = AsyncMock()

    # Provide 'y' twice: once for the overall flow, once for the specific app
    result = runner.invoke(app, ["scan", "--token", "token"], input="y\ny\n")
    
    assert result.exit_code == 0
    assert "Suspicious Authorized Apps Found" in result.stdout
    assert "Successfully revoked access for Suspicious App" in result.stdout
