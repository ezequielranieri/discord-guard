"""Account data models for discord-guard."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class DiscordUser(BaseModel):
    """Discord user account information."""

    id: str
    username: str
    discriminator: str
    mfa_enabled: bool
    email: Optional[str] = None
    phone: Optional[str] = None
    flags: int = 0


class AuthorizedApp(BaseModel):
    """Authorized OAuth2 application information."""

    id: str
    name: str
    description: Optional[str] = ""
    icon: Optional[str] = None
    scopes: List[str]
    last_used_at: Optional[str] = None


class ActiveSession(BaseModel):
    """Active account session information."""

    id: str = Field(alias="session_id")
    client_info: dict
    location: Optional[str] = "Unknown"
    last_used_at: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)
