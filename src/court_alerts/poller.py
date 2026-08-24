from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from court_alerts.core.diff import find_opened_slots
from court_alerts.core.subscription import Subscription, route
from court_alerts.db.repository import (
    load_latest_slots,
    save_snapshot,
    start_poll_run,
)
from court_alerts.db.tables import PollStatus
from court_alerts.notify.base import Notifier, NotifierError
from court_alerts.notify.message import format_alert
from court_alerts.providers.base import ProviderError, ScheduleProvider


@dataclass(frozen=True)
class PollResult:
    """What one cycle did, for the CLI and for tests."""

    status: PollStatus
    slot_count: int
    opened_count: int
    alerts_sent: int
    error: dict[str, str] | None = None


def run_poll(
    *,
    session: Session,
    provider: ScheduleProvider,
    notifier: Notifier,
    subscriptions: list[Subscription],
    club_id: str,
    on_date: date,
    club_name: str,
) -> PollResult:
    """Fetch, diff, persist, then notify — in that order.

    Persisting before notifying is deliberate. If delivery fails after
    the snapshot is committed, the worst case is one repeated alert next
    cycle. If the snapshot were lost instead, the next cycle would be a
    cold start and every open court would alert at once.
    """
    run = start_poll_run(session, club_id, on_date, provider.name)

    # --- fetch -------------------------------------------------------
    try:
        current = provider.fetch_slots(club_id, on_date)
    except ProviderError as error:
        evidence = error.as_evidence()
        run.status = PollStatus.PROVIDER_FAILED.value
        run.error_type = evidence["error_type"]
        run.error_message = evidence["message"]
        session.commit()
        return PollResult(
            status=PollStatus.PROVIDER_FAILED,
            slot_count=0,
            opened_count=0,
            alerts_sent=0,
            error=evidence,
        )

    # --- diff --------------------------------------------------------
    previous = load_latest_slots(session, club_id, on_date)
    opened = find_opened_slots(previous, current)

    # --- persist (committed before any delivery is attempted) --------
    snapshot = save_snapshot(session, club_id, on_date, provider.name, current)
    run.slot_count = len(current)
    run.opened_count = len(opened)
    run.snapshot_id = snapshot.id
    session.commit()

    if not opened:
        return PollResult(
            status=PollStatus.OK,
            slot_count=len(current),
            opened_count=0,
            alerts_sent=0,
        )

    # --- notify ------------------------------------------------------
    sent = 0
    failure = None

    for subscription, matched in route(subscriptions, opened):
        text = format_alert(subscription.label, matched, club_name)
        try:
            notifier.send(text)
        except NotifierError as error:
            failure = error.as_evidence()
            break
        sent += 1

    run.alerts_sent = sent
    if failure is not None:
        run.status = PollStatus.NOTIFY_FAILED.value
        run.error_type = failure["error_type"]
        run.error_message = failure["message"]
    session.commit()

    status = PollStatus.OK
    if failure is not None:
        status = PollStatus.NOTIFY_FAILED

    return PollResult(
        status=status,
        slot_count=len(current),
        opened_count=len(opened),
        alerts_sent=sent,
        error=failure,
    )   