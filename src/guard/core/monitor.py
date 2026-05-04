"""Real-time account monitoring for discord-guard."""

import asyncio
import structlog
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Set
from guard.api.discord import DiscordClient, DiscordAPIError
from guard.models.risk import Alert

logger = structlog.get_logger(__name__)


class AccountMonitor:
    """Monitors Discord account for suspicious activity."""

    def __init__(self, token: str, interval: int = 30):
        """Initializes the monitor.

        Args:
            token: The Discord user token.
            interval: Polling interval in seconds.
        """
        self.client = DiscordClient(token)
        self.interval = interval
        self.is_running = False
        
        # State for comparison
        self._prev_apps: Set[str] = set()
        self._prev_friends: Set[str] = set()
        self._prev_guilds: Set[str] = set()
        self._initialized = False

    async def _fetch_current_state(self) -> Dict[str, Any]:
        """Fetches the current state of apps, friends, and guilds."""
        apps = await self.client.get_authorized_apps()
        friends = await self.client.get_relationships()
        guilds = await self.client.get_guilds()
        
        return {
            "apps": {app["application"]["id"] for app in apps},
            "friends": {rel["id"] for rel in friends},
            "guilds": {g["id"] for g in guilds}
        }

    def _detect_anomalies(self, current: Dict[str, Any]) -> List[Alert]:
        """Compares current state with previous state to find anomalies."""
        alerts = []
        
        if not self._initialized:
            self._prev_apps = current["apps"]
            self._prev_friends = current["friends"]
            self._prev_guilds = current["guilds"]
            self._initialized = True
            return alerts

        # 1. New Authorized Apps
        new_apps = current["apps"] - self._prev_apps
        if new_apps:
            alerts.append(
                Alert(
                    type="New Authorized App",
                    description=f"Detected {len(new_apps)} new authorized application(s).",
                    recommendation="Review your authorized apps immediately and revoke any you don't recognize."
                )
            )

        # 2. Friend List Changes (Mass Unfriend)
        removed_friends = self._prev_friends - current["friends"]
        if len(removed_friends) > 5:  # Threshold for "mass"
            alerts.append(
                Alert(
                    type="Mass Unfriend Detected",
                    description=f"Sudden removal of {len(removed_friends)} friends from your list.",
                    recommendation="This could indicate your account is being compromised. Check your recent activity."
                )
            )

        # 3. Server Join Spikes
        new_guilds = current["guilds"] - self._prev_guilds
        if len(new_guilds) > 3:
            alerts.append(
                Alert(
                    type="Server Join Spike",
                    description=f"Your account joined {len(new_guilds)} new servers recently.",
                    recommendation="If you didn't join these servers, your token might be hijacked."
                )
            )

        # Update state
        self._prev_apps = current["apps"]
        self._prev_friends = current["friends"]
        self._prev_guilds = current["guilds"]
        
        return alerts

    async def start(self, on_alert: Callable[[Alert], None]) -> None:
        """Starts the monitoring loop.

        Args:
            on_alert: Callback function to handle detected alerts.
        """
        self.is_running = True
        logger.info("monitor_started", interval=self.interval)

        try:
            while self.is_running:
                try:
                    state = await self._fetch_current_state()
                    alerts = self._detect_anomalies(state)
                    
                    for alert in alerts:
                        logger.warning("anomaly_detected", type=alert.type)
                        on_alert(alert)
                        
                except DiscordAPIError as e:
                    logger.error("monitor_api_error", error=str(e))
                except Exception as e:
                    logger.exception("monitor_unexpected_error", error=str(e))
                
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            logger.info("monitor_cancelled")
        finally:
            self.is_running = False

    def stop(self) -> None:
        """Stops the monitoring loop."""
        self.is_running = False
        logger.info("monitor_stopping")
