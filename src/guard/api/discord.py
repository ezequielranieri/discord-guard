"""Discord API client for discord-guard."""

from typing import Any

import httpx
import structlog

from guard.config import settings

logger = structlog.get_logger(__name__)


class DiscordAPIError(Exception):
    """Base exception for Discord API errors."""
    pass


class InvalidTokenError(DiscordAPIError):
    """Raised when the provided token is invalid or expired."""
    pass


class RateLimitError(DiscordAPIError):
    """Raised when the API rate limit is exceeded."""
    pass


class DiscordClient:
    """Async client for interacting with the Discord API."""

    def __init__(self, token: str):
        """Initializes the Discord client.

        Args:
            token: The Discord user token.
        """
        self.token = token
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": f"discord-guard ({settings.version})",
        }
        self._masked_token = (
            f"{self.token[:8]}...{self.token[-4:]}"
            if len(self.token) > 12
            else "***"
        )

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Sends an async request to the Discord API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.).
            endpoint: API endpoint (e.g., "/users/@me").
            params: Optional query parameters.
            json: Optional JSON body.

        Returns:
            The JSON response from the API.

        Raises:
            InvalidTokenError: If the API returns a 401.
            RateLimitError: If the API returns a 429.
            DiscordAPIError: For other non-2xx responses.
        """
        url = f"{settings.discord_api_base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method, url, headers=self.headers, params=params, json=json
                )

                if response.status_code == 401:
                    logger.error("invalid_token", token=self._masked_token)
                    raise InvalidTokenError("The provided Discord token is invalid.")

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "unknown")
                    logger.warning("rate_limit_exceeded", retry_after=retry_after)
                    raise RateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after}s."
                    )

                response.raise_for_status()
                return response.json() if response.content else None

            except httpx.HTTPStatusError as e:
                logger.error(
                    "api_request_failed",
                    status_code=e.response.status_code,
                    url=url,
                )
                raise DiscordAPIError(
                    f"API request failed with status {e.response.status_code}: {e}"
                )
            except httpx.RequestError as e:
                logger.error("api_connection_error", error=str(e), url=url)
                raise DiscordAPIError(f"Failed to connect to Discord API: {e}")

    async def get_me(self) -> dict[str, Any]:
        """Fetches the current user's account info.

        Returns:
            Dictionary with user information.
        """
        return await self._request("GET", "/users/@me")

    async def get_relationships(self) -> list[dict[str, Any]]:
        """Fetches the user's relationships (friends).

        Returns:
            List of relationships.
        """
        return await self._request("GET", "/users/@me/relationships")

    async def get_guilds(self) -> list[dict[str, Any]]:
        """Fetches the guilds the user is a member of.

        Returns:
            List of guilds.
        """
        return await self._request("GET", "/users/@me/guilds")

    async def get_authorized_apps(self) -> list[dict[str, Any]]:
        """Fetches authorized OAuth2 applications.

        Returns:
            List of authorized applications.
        """
        return await self._request("GET", "/oauth2/tokens")

    async def get_sessions(self) -> dict[str, Any]:
        """Fetches active account sessions.

        Returns:
            Dictionary with 'sessions' (list) and 'note' (optional string).
        """
        # Note: This endpoint might require specific headers or might not be 
        # officially documented for user tokens, but it's used by the web client.
        try:
            sessions = await self._request("GET", "/auth/sessions")
            return {"sessions": sessions, "note": None}
        except DiscordAPIError:
            note = (
                "Discord limits active session visibility for third-party tools. "
                "Check 'User Settings -> Devices' in your Discord app for full details."
            )
            logger.warning("sessions_endpoint_restricted", message=note)
            return {"sessions": [], "note": note}

    async def revoke_app(self, app_id: str) -> None:
        """Revokes an authorized application.

        Args:
            app_id: The ID of the application to revoke.
        """
        await self._request("DELETE", f"/oauth2/tokens/{app_id}")
        logger.info("app_revoked", app_id=app_id)
