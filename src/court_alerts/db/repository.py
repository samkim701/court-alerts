from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from court_alerts.core.models import Slot
from court_alerts.db.convert import row_to_slot, slot_to_row
from court_alerts.db.tables import Snapshot
from court_alerts.db.tables import PollRun, PollStatus


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


def start_poll_run(
    session: Session,
    club_id: str,
    on_date: date,
    provider: str,
) -> PollRun:
    """Open a run row up front, so even a crash leaves a trace."""
    run = PollRun(
        club_id=club_id,
        on_date=on_date,
        provider=provider,
        status=PollStatus.OK.value,
        slot_count=0,
        opened_count=0,
        alerts_sent=0,
    )
    session.add(run)
    session.flush()
    return run


def load_recent_runs(
    session: Session,
    club_id: str,
    limit: int = 20,
) -> list[PollRun]:
    """Newest runs first — the triage agent's window into history."""
    statement = (
        select(PollRun)
        .where(PollRun.club_id == club_id)
        .order_by(PollRun.started_at.desc(), PollRun.id.desc())
        .limit(limit)
    )

    runs = []
    for run in session.scalars(statement):
        runs.append(run)
    return runs


def load_untriaged_runs(
    session: Session,
    club_id: str,
    limit: int = 5,
) -> list[PollRun]:
    """Failed runs that have not been classified yet, newest first.

    Successful runs are skipped on purpose: sending them to a model
    costs money and produces nothing but `no_issue`.
    """
    statement = (
        select(PollRun)
        .where(
            PollRun.club_id == club_id,
            PollRun.status != PollStatus.OK.value,
            PollRun.triage_category.is_(None),
        )
        .order_by(PollRun.started_at.desc(), PollRun.id.desc())
        .limit(limit)
    )

    runs = []
    for run in session.scalars(statement):
        runs.append(run)
    return runs


def save_verdict(session: Session, run: PollRun, verdict) -> None:
    """Attach a triage verdict to one run. Caller commits.

    `verdict` is a TriageVerdict, but it is not imported here — the db
    layer stays unaware of the triage layer so the dependency arrow
    keeps pointing inward.
    """
    run.triage_category = verdict.category.value
    run.triage_needs_human = verdict.needs_human
    run.triage_confidence = verdict.confidence
    run.triage_summary = verdict.summary
    run.triage_source = verdict.source
    run.triaged_at = datetime.now(timezone.utc)
    session.flush()
