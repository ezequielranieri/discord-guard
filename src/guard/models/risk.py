"""Risk assessment models for discord-guard."""

from datetime import datetime
from enum import Enum
from typing import List
from pydantic import BaseModel, Field
from guard.models.account import AuthorizedApp, ActiveSession


class RiskLevel(str, Enum):
    """Security risk levels."""
    SAFE = "safe"
    WARNING = "warning"
    CRITICAL = "critical"


class RiskItem(BaseModel):
    """Specific risk finding."""
    category: str
    level: RiskLevel
    description: str
    recommendation: str
    auto_fixable: bool = False


class Alert(BaseModel):
    """Real-time security alert."""
    type: str
    description: str
    timestamp: datetime = Field(default_factory=datetime.now)
    recommendation: str


class AccountRiskReport(BaseModel):
    """Comprehensive account security report."""
    user_id: str
    username: str
    scan_timestamp: datetime = datetime.now()
    overall_score: int  # 0-100, higher = more risk
    overall_level: RiskLevel
    risks: List[RiskItem]
    authorized_apps: List[AuthorizedApp]
    active_sessions: List[ActiveSession]
    two_fa_enabled: bool
