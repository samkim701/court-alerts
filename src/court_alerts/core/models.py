from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

CLUB_TZ = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class Slot:
    """One bookable block on one court."""

    court: str
    start: datetime
    end: datetime
    is_available: bool

    @property
    def key(self) -> tuple[str, datetime]:
        """Identity of this slot across polls."""
        return (self.court, self.start)