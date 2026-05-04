"""Account scanner orchestration for discord-guard."""

import structlog
from typing import List
from guard.api.discord import DiscordClient
from guard.models.account import DiscordUser, AuthorizedApp, ActiveSession
from guard.models.risk import AccountRiskReport
from guard.core.analyzer import RiskAnalyzer

logger = structlog.get_logger(__name__)


class AccountScanner:
    """Orchestrates the account scanning process."""

    def __init__(self, token: str):
        """Initializes the scanner.

        Args:
            token: The Discord user token.
        """
        self.client = DiscordClient(token)
        self.analyzer = RiskAnalyzer()

    async def run_scan(self) -> AccountRiskReport:
        """Fetches data and performs analysis.

        Returns:
            The generated risk report.
        """
        logger.info("scan_run_started")

        # 1. Fetch data in parallel
        # Note: In a real scenario, we might use asyncio.gather
        user_data = await self.client.get_me()
        apps_data = await self.client.get_authorized_apps()
        sessions_result = await self.client.get_sessions()

        # 2. Parse into models
        user = DiscordUser(**user_data)
        
        apps = [
            AuthorizedApp(
                id=app["application"]["id"],
                name=app["application"]["name"],
                description=app["application"].get("description", ""),
                scopes=app["scopes"]
            )
            for app in apps_data
        ]
        
        sessions = [ActiveSession(**s) for s in sessions_result["sessions"]]

        # 3. Analyze
        report = self.analyzer.analyze(user, apps, sessions)
        report.sessions_note = sessions_result["note"]
        
        logger.info("scan_run_completed", score=report.overall_score, level=report.overall_level)
        return report
