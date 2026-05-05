"""Account data models for discord-guard."""


from pydantic import BaseModel, ConfigDict, Field


class DiscordUser(BaseModel):
    """Discord user account information."""

    id: str
    username: str
    discriminator: str
    mfa_enabled: bool
    email: str | None = None
    phone: str | None = None
    flags: int = 0


class AuthorizedApp(BaseModel):
    """Authorized OAuth2 application information."""

    id: str
    name: str
    description: str | None = ""
    icon: str | None = None
    scopes: list[str]
    last_used_at: str | None = None


class ActiveSession(BaseModel):
    """Active account session information."""

    id: str = Field(alias="session_id")
    client_info: dict
    location: str | None = "Unknown"
    last_used_at: str | None = None

    model_config = ConfigDict(populate_by_name=True)
