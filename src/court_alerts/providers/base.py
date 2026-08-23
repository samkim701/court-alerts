from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

from court_alerts.core.models import Slot


class ProviderError(Exception):
    """A provider could not produce a usable snapshot."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        club_id: str,
        on_date: date,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.club_id = club_id
        self.on_date = on_date

    def as_evidence(self) -> dict[str, str]:
        """Flat, log-safe facts for the triage agent's evidence bundle."""
        return {
            "error_type": type(self).__name__,
            "message": self.message,
            "provider": self.provider,
            "club_id": self.club_id,
            "on_date": self.on_date.isoformat(),
        }


@runtime_checkable
class ScheduleProvider(Protocol):
    """Anything that can hand back one day's court schedule."""

    name: str

    def fetch_slots(self, club_id: str, on_date: date) -> list[Slot]:
        """Return every slot for that club/day, available or not.

        Raises ProviderError if a usable snapshot cannot be produced.
        """
        ...