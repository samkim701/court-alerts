from datetime import date

from court_alerts.core.subscription import Subscription
from court_alerts.db.tables import PollStatus
from court_alerts.notify.base import NotifierError
from court_alerts.notify.console import ConsoleNotifier
from court_alerts.poller import run_poll
from court_alerts.providers.base import ProviderError
from court_alerts.providers.mock import MockProvider, make_day, open_slot

MONDAY = date(2026, 8, 24)
COURTS = ["Court 1", "Court 2"]
CLUB = "centreville"
CLUB_NAME = "Life Time Centreville"


class BrokenNotifier:
    """Always fails, to prove the snapshot survives a delivery failure."""

    name = "broken"

    def send(self, text: str) -> None:
        raise NotifierError("channel is gone", notifier=self.name, status_code=404)


def evening() -> list[Subscription]:
    return [
        Subscription(
            label="Monday evening",
            weekdays=frozenset({0}),
            earliest_hour=17,
            latest_hour=21,
        )
    ]


def poll(session, provider, notifier):
    return run_poll(
        session=session,
        provider=provider,
        notifier=notifier,
        subscriptions=evening(),
        club_id=CLUB,
        on_date=MONDAY,
        club_name=CLUB_NAME,
    )


def test_cold_start_on_a_booked_day_sends_nothing(session):
    provider = MockProvider([make_day(MONDAY, COURTS)])
    notifier = ConsoleNotifier(echo=False)

    result = poll(session, provider, notifier)

    assert result.status is PollStatus.OK
    assert result.opened_count == 0
    assert notifier.sent == []


def test_cancellation_on_the_second_cycle_sends_one_alert(session):
    booked = make_day(MONDAY, COURTS)
    provider = MockProvider([booked, open_slot(booked, "Court 1", 19)])
    notifier = ConsoleNotifier(echo=False)

    poll(session, provider, notifier)
    result = poll(session, provider, notifier)

    assert result.opened_count == 1
    assert result.alerts_sent == 1
    assert len(notifier.sent) == 1
    assert "Court 1" in notifier.sent[0]


def test_opening_outside_the_window_is_not_alerted(session):
    booked = make_day(MONDAY, COURTS)
    provider = MockProvider([booked, open_slot(booked, "Court 1", 7)])
    notifier = ConsoleNotifier(echo=False)

    poll(session, provider, notifier)
    result = poll(session, provider, notifier)

    assert result.opened_count == 1
    assert result.alerts_sent == 0
    assert notifier.sent == []


def test_provider_failure_is_recorded_and_stops_the_cycle(session):
    error = ProviderError(
        "upstream 503", provider="mock", club_id=CLUB, on_date=MONDAY
    )
    provider = MockProvider([error])
    notifier = ConsoleNotifier(echo=False)

    result = poll(session, provider, notifier)

    assert result.status is PollStatus.PROVIDER_FAILED
    assert result.error["error_type"] == "ProviderError"
    assert notifier.sent == []


def test_snapshot_survives_a_delivery_failure(session):
    booked = make_day(MONDAY, COURTS)
    provider = MockProvider([booked, open_slot(booked, "Court 1", 19)])

    poll(session, provider, ConsoleNotifier(echo=False))
    result = poll(session, provider, BrokenNotifier())

    assert result.status is PollStatus.NOTIFY_FAILED
    assert result.alerts_sent == 0

    # The third cycle repeats the last snapshot, so nothing looks "new"
    # any more — the opening was persisted despite the failed send.
    third = poll(session, provider, ConsoleNotifier(echo=False))
    assert third.opened_count == 0