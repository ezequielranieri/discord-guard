"""Risk analysis engine for discord-guard."""


from guard.models.account import ActiveSession, AuthorizedApp, DiscordUser
from guard.models.risk import AccountRiskReport, RiskItem, RiskLevel


class RiskAnalyzer:
    """Analyzes account data to identify security risks."""

    def analyze(
        self,
        user: DiscordUser,
        apps: list[AuthorizedApp],
        sessions: list[ActiveSession]
    ) -> AccountRiskReport:
        """Performs a full risk analysis.

        Args:
            user: The Discord user data.
            apps: List of authorized apps.
            sessions: List of active sessions.

        Returns:
            A comprehensive risk report.
        """
        risks = []
        score = 0

        # 1. Check 2FA Status
        if not user.mfa_enabled:
            risks.append(
                RiskItem(
                    category="Authentication",
                    level=RiskLevel.CRITICAL,
                    description="Two-Factor Authentication (2FA) is not enabled.",
                    recommendation=(
                        "Enable 2FA in User Settings -> My Account -> "
                        "Two-Factor Auth."
                    ),
                    auto_fixable=False,
                )
            )
            score += 40

        # 2. Analyze Authorized Apps
        dangerous_scopes = {"bot", "rpc", "messages.read", "guilds.join"}
        dangerous_apps_count = 0

        for app in apps:
            has_dangerous_scope = any(
                scope in dangerous_scopes for scope in app.scopes
            )
            if has_dangerous_scope:
                dangerous_apps_count += 1
                risks.append(
                    RiskItem(
                        category="Apps",
                        level=RiskLevel.WARNING,
                        description=(
                            f"App '{app.name}' has dangerous permissions: "
                            f"{', '.join(app.scopes)}"
                        ),
                        recommendation=(
                            f"Review and consider revoking '{app.name}' if you "
                            "don't recognize it."
                        ),
                        auto_fixable=True,
                    )
                )

        if dangerous_apps_count > 0:
            score += min(dangerous_apps_count * 10, 30)

        # 3. Analyze Sessions
        if len(sessions) > 1:
            risks.append(
                RiskItem(
                    category="Sessions",
                    level=RiskLevel.WARNING,
                    description=(
                        f"There are {len(sessions)} active sessions on your account."
                    ),
                    recommendation=(
                        "Check the active sessions and log out from any device "
                        "you don't recognize."
                    ),
                    auto_fixable=False,
                )
            )
            score += 15

        # Determine overall level
        overall_level = RiskLevel.SAFE
        if any(r.level == RiskLevel.CRITICAL for r in risks):
            overall_level = RiskLevel.CRITICAL
        elif any(r.level == RiskLevel.WARNING for r in risks):
            overall_level = RiskLevel.WARNING

        return AccountRiskReport(
            user_id=user.id,
            username=f"{user.username}#{user.discriminator}",
            overall_score=min(score, 100),
            overall_level=overall_level,
            risks=risks,
            authorized_apps=apps,
            active_sessions=sessions,
            two_fa_enabled=user.mfa_enabled
        )
