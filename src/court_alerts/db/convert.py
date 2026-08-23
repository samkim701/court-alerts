from __future__ import annotations

from court_alerts.core.models import CLUB_TZ, Slot
from court_alerts.db.tables import SnapshotSlot


def slot_to_row(slot: Slot) -> SnapshotSlot:
    """Domain object to ORM row (not yet attached to a session)."""
    return SnapshotSlot(
        court=slot.court,
        start=slot.start,
        end=slot.end,
        is_available=slot.is_available,
    )


def row_to_slot(row: SnapshotSlot) -> Slot:
    """ORM row back to a domain object, in club-local time.

    Postgres hands timestamptz back in UTC, so the wall-clock hour
    would read wrong without converting home first.
    """
    return Slot(
        court=row.court,
        start=row.start.astimezone(CLUB_TZ),
        end=row.end.astimezone(CLUB_TZ),
        is_available=row.is_available,
    )