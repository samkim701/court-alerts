from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from court_alerts.core.models import Slot
from court_alerts.db.convert import row_to_slot, slot_to_row
from court_alerts.db.tables import Snapshot


def save_snapshot(
    session: Session,
    club_id: str,
    on_date: date,
    provider: str,
    slots: list[Slot],
) -> Snapshot:
    """Store one poll's worth of slots. Caller commits."""
    snapshot = Snapshot(
        club_id=club_id,
        on_date=on_date,
        provider=provider,
        slot_count=len(slots),
    )
    for slot in slots:
        snapshot.slots.append(slot_to_row(slot))

    session.add(snapshot)
    session.flush()
    return snapshot


def load_latest_slots(
    session: Session,
    club_id: str,
    on_date: date,
) -> list[Slot]:
    """Most recent stored snapshot, or [] on a cold start."""
    statement = (
        select(Snapshot)
        .where(
            Snapshot.club_id == club_id,
            Snapshot.on_date == on_date,
        )
        .order_by(Snapshot.polled_at.desc(), Snapshot.id.desc())
        .limit(1)
    )

    snapshot = session.scalars(statement).first()
    if snapshot is None:
        return []

    slots = []
    for row in snapshot.slots:
        slots.append(row_to_slot(row))
    return slots