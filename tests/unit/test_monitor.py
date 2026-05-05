"""Unit tests for the AccountMonitor."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from guard.core.monitor import AccountMonitor


@pytest.fixture
def monitor():
    return AccountMonitor("token", interval=1)


@pytest.mark.asyncio
async def test_monitor_initialization(monitor):
    """Tests that the monitor initializes its state correctly."""
    mock_state = {
        "apps": {"app1"},
        "friends": {"user1", "user2"},
        "guilds": {"guild1"}
    }
    
    alerts = monitor._detect_anomalies(mock_state)
    
    assert alerts == []
    assert monitor._initialized is True
    assert monitor._prev_apps == {"app1"}


def test_detect_new_app(monitor):
    """Tests detection of a new authorized app."""
    # Initialize
    monitor._detect_anomalies({"apps": {"app1"}, "friends": set(), "guilds": set()})
    
    # New state
    new_state = {"apps": {"app1", "app2"}, "friends": set(), "guilds": set()}
    alerts = monitor._detect_anomalies(new_state)
    
    assert len(alerts) == 1
    assert alerts[0].type == "New Authorized App"


def test_detect_mass_unfriend(monitor):
    """Tests detection of mass unfriending."""
    # Initialize with 10 friends
    friends = {f"u{i}" for i in range(10)}
    monitor._detect_anomalies({"apps": set(), "friends": friends, "guilds": set()})
    
    # Remove 6 friends
    new_friends = {f"u{i}" for i in range(4)}
    alerts = monitor._detect_anomalies({"apps": set(), "friends": new_friends, "guilds": set()})
    
    assert len(alerts) == 1
    assert alerts[0].type == "Mass Unfriend Detected"


def test_detect_server_spike(monitor):
    """Tests detection of sudden server joins."""
    # Initialize
    monitor._detect_anomalies({"apps": set(), "friends": set(), "guilds": {"g1"}})
    
    # Join 4 servers
    new_guilds = {"g1", "g2", "g3", "g4", "g5"}
    alerts = monitor._detect_anomalies({"apps": set(), "friends": set(), "guilds": new_guilds})
    
    assert len(alerts) == 1
    assert alerts[0].type == "Server Join Spike"


@pytest.mark.asyncio
async def test_monitor_loop_alert_callback(monitor):
    """Tests that the monitor loop calls the alert callback."""
    # Mock current state fetching
    initial_state = {"apps": {"app1"}, "relationships": [], "guilds": []}
    new_state = {"apps": {"app1", "app2"}, "relationships": [], "guilds": []}
    
    monitor.client.get_authorized_apps = AsyncMock(side_effect=[[{"application": {"id": "app1"}}], [{"application": {"id": "app1"}}, {"application": {"id": "app2"}}]])
    monitor.client.get_relationships = AsyncMock(return_value=[])
    monitor.client.get_guilds = AsyncMock(return_value=[])
    
    on_alert = MagicMock()
    
    # Run loop briefly
    task = asyncio.create_task(monitor.start(on_alert=on_alert))
    await asyncio.sleep(1.5) # Wait for two polls (interval=1)
    monitor.stop()
    await task
    
    assert on_alert.called
    assert on_alert.call_args[0][0].type == "New Authorized App"
