from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from court_alerts.core.models import CLUB_TZ, Slot
from court_alerts.providers.base import ProviderError

Step = list[Slot] | Exception


def make_day(
    on_date: date,
    courts: list[str],
    *,
    first_hour: int = 6,
    last_hour: int = 22,
    available: bool = False,
    tz: ZoneInfo = CLUB_TZ,
) -> list[Slot]:
    """Build a full grid of one-hour slots for the given courts."""
    slots: list[Slot] = []
    for court in courts:
        for hour in range(first_hour, last_hour):
            start = datetime.combine(on_date, time(hour=hour), tzinfo=tz)
            end = start + timedelta(hours=1)
            slots.append(
                Slot(court=court, start=start, end=end, is_available=available)
            )
    return slots


def open_slot(snapshot: list[Slot], court: str, hour: int) -> list[Slot]:
    """Copy the snapshot with one slot flipped to available (a cancellation)."""
    updated: list[Slot] = []
    for slot in snapshot:
        if slot.court == court and slot.start.hour == hour:
            updated.append(replace(slot, is_available=True))
        else:
            updated.append(slot)
    return updated


class MockProvider:
    """Replays a scripted sequence of snapshots, one per fetch_slots call.

    Each step is either a snapshot to return or an exception to raise.
    Once the script runs out, the final step repeats forever, so a poll
    loop can keep running against a steady state.
    """

    name = "mock"

    def __init__(self, script: list[Step]) -> None:
        if not script:
            raise ValueError("MockProvider needs at least one step")
        self._script = list(script)
        self.calls = 0

    def fetch_slots(self, club_id: str, on_date: date) -> list[Slot]:
        index = self.calls
        if index >= len(self._script):
            index = len(self._script) - 1
        step = self._script[index]
        self.calls += 1

        if isinstance(step, Exception):
            raise step
        return list(step)


def failing_provider(message: str, club_id: str, on_date: date) -> MockProvider:
    """A provider whose every call blows up — feedstock for triage tests."""
    error = ProviderError(
        message, provider="mock", club_id=club_id, on_date=on_date
    )
    return MockProvider([error])