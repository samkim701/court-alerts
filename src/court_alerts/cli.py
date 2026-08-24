from __future__ import annotations

import argparse
from datetime import date, timedelta

from court_alerts.config import CLUB_NAME
from court_alerts.core.subscription import Subscription
from court_alerts.db.session import SessionLocal, create_all
from court_alerts.notify.factory import build_notifier
from court_alerts.poller import run_poll
from court_alerts.providers.mock import MockProvider, make_day, open_slot

DEMO_CLUB_ID = "centreville"
DEMO_COURTS = ["Court 1", "Court 2", "Court 3", "Court 4"]


def build_demo_subscriptions() -> list[Subscription]:
    """Hard-coded for now; the API will store these per user."""
    return [
        Subscription(
            label="Weeknight prime time",
            weekdays=frozenset({0, 1, 2, 3, 4}),
            earliest_hour=17,
            latest_hour=21,
        )
    ]


def next_weekday(start: date) -> date:
    """First Mon-Fri date on or after `start`."""
    candidate = start
    while candidate.weekday() > 4:
        candidate = candidate + timedelta(days=1)
    return candidate


def run_demo() -> None:
    """Two cycles: a fully booked day, then a cancellation."""
    create_all()

    on_date = next_weekday(date.today())
    notifier = build_notifier()
    subscriptions = build_demo_subscriptions()

    booked = make_day(on_date, DEMO_COURTS)
    after_cancellation = open_slot(booked, "Court 1", 19)
    after_cancellation = open_slot(after_cancellation, "Court 3", 18)

    provider = MockProvider([booked, after_cancellation])

    print(f"Club: {CLUB_NAME}  Date: {on_date}  Notifier: {notifier.name}")

    for cycle in (1, 2):
        session = SessionLocal()
        try:
            result = run_poll(
                session=session,
                provider=provider,
                notifier=notifier,
                subscriptions=subscriptions,
                club_id=DEMO_CLUB_ID,
                on_date=on_date,
                club_name=CLUB_NAME,
            )
        finally:
            session.close()

        print(
            f"cycle {cycle}: status={result.status.value} "
            f"slots={result.slot_count} "
            f"opened={result.opened_count} "
            f"alerts={result.alerts_sent}"
        )
        if result.error is not None:
            print(f"  error: {result.error}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="court-alerts")
    parser.add_argument(
        "command",
        choices=["demo"],
        help="demo: run two poll cycles against the mock provider",
    )
    args = parser.parse_args()

    if args.command == "demo":
        run_demo()


if __name__ == "__main__":
    main()