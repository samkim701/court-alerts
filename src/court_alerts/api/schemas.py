from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class OpeningOut(BaseModel):
    """One slot that is currently bookable."""

    court: str
    start: datetime
    end: datetime


class TriageOut(BaseModel):
    """A verdict attached to a failed run."""

    category: str
    needs_human: bool
    confidence: float
    summary: str
    source: str
    triaged_at: datetime


class RunOut(BaseModel):
    """One poll attempt, with its verdict when it has one."""

    id: int
    started_at: datetime
    status: str
    slot_count: int
    opened_count: int
    alerts_sent: int
    error_type: str | None
    error_message: str | None
    triage: TriageOut | None


class SubscriptionOut(BaseModel):
    """Read-only view of a standing subscription."""

    label: str
    weekdays: list[int]
    earliest_hour: int
    latest_hour: int
    courts: list[str] | None
