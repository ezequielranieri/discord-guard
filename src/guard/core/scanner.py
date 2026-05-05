"""Account scanner orchestration for discord-guard."""

import asyncio

import structlog

from guard.api.discord import DiscordClient
from guard.core.analyzer import RiskAnalyzer
from guard.models.account import ActiveSession, AuthorizedApp, DiscordUser
from guard.models.risk import AccountRiskReport

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
        user_data, apps_data, sessions_result = await asyncio.gather(
            self.client.get_me(),
            self.client.get_authorized_apps(),
            self.client.get_sessions()
        )

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

        logger.info(
            "scan_run_completed",
            score=report.overall_score,
            level=report.overall_level,
        )
        return report
