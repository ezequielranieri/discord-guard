"""Unit tests for the RiskAnalyzer."""

import pytest

from guard.core.analyzer import RiskAnalyzer
from guard.models.account import ActiveSession, AuthorizedApp, DiscordUser
from guard.models.risk import RiskLevel


@pytest.fixture
def analyzer():
    return RiskAnalyzer()


@pytest.fixture
def safe_user():
    return DiscordUser(id="1", username="test", discriminator="0001", mfa_enabled=True)


def test_analyze_safe_account(analyzer, safe_user):
    """Tests analysis of a safe account."""
    report = analyzer.analyze(safe_user, [], [])
    
    assert report.overall_score == 0
    assert report.overall_level == RiskLevel.SAFE
    assert len(report.risks) == 0


def test_analyze_no_2fa(analyzer, safe_user):
    """Tests analysis when 2FA is disabled."""
    safe_user.mfa_enabled = False
    report = analyzer.analyze(safe_user, [], [])
    
    assert report.overall_score == 40
    assert report.overall_level == RiskLevel.CRITICAL
    assert any(r.category == "Authentication" for r in report.risks)


def test_analyze_dangerous_apps(analyzer, safe_user):
    """Tests analysis with dangerous authorized apps."""
    apps = [
        AuthorizedApp(id="app1", name="Evil App", scopes=["bot", "messages.read"]),
        AuthorizedApp(id="app2", name="Safe App", scopes=["identify"])
    ]
    report = analyzer.analyze(safe_user, apps, [])
    
    assert report.overall_score == 10
    assert report.overall_level == RiskLevel.WARNING
    assert len([r for r in report.risks if r.category == "Apps"]) == 1


def test_analyze_multiple_sessions(analyzer, safe_user):
    """Tests analysis with multiple active sessions."""
    sessions = [
        ActiveSession(session_id="s1", client_info={"os": "win"}),
        ActiveSession(session_id="s2", client_info={"os": "linux"})
    ]
    report = analyzer.analyze(safe_user, [], sessions)
    
    assert report.overall_score == 15
    assert report.overall_level == RiskLevel.WARNING
    assert any(r.category == "Sessions" for r in report.risks)
