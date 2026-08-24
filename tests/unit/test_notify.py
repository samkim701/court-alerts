from datetime import date, datetime, time, timedelta

import pytest

from court_alerts.core.models import CLUB_TZ, Slot
from court_alerts.notify.base import Notifier, NotifierError
from court_alerts.notify.console import ConsoleNotifier
from court_alerts.notify.discord import DiscordNotifier
from court_alerts.notify.message import DISCORD_CONTENT_LIMIT, format_alert

MONDAY = date(2026, 8, 24)
CLUB = "Life Time Centreville"


def slot(court: str, hour: int) -> Slot:
    start = datetime.combine(MONDAY, time(hour=hour), tzinfo=CLUB_TZ)
    return Slot(
        court=court,
        start=start,
        end=start + timedelta(hours=1),
        is_available=True,
    )


def test_console_notifier_satisfies_the_protocol():
    assert isinstance(ConsoleNotifier(echo=False), Notifier)


def test_console_notifier_records_what_it_sent():
    notifier = ConsoleNotifier(echo=False)

    notifier.send("hello")

    assert notifier.sent == ["hello"]


def test_alert_lists_every_slot_in_one_message():
    text = format_alert(
        "Monday evening", [slot("Court 2", 20), slot("Court 1", 19)], CLUB
    )

    assert "2 opening(s)" in text
    assert "Court 1" in text
    assert "Court 2" in text
    # Earliest slot is listed first.
    assert text.index("Court 1") < text.index("Court 2")


def test_long_alert_stays_under_the_discord_limit():
    many = []
    for hour in range(6, 22):
        many.append(slot("Court with a deliberately long name", hour))

    text = format_alert("everything", many, CLUB)

    assert len(text) <= DISCORD_CONTENT_LIMIT
    assert "more" in text


def test_discord_notifier_needs_a_url():
    with pytest.raises(ValueError):
        DiscordNotifier("")


def test_factory_falls_back_to_console_without_a_webhook(monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

    from court_alerts.notify.factory import build_notifier

    assert build_notifier().name == "console"


def test_malformed_webhook_becomes_a_notifier_error():
    """A bad URL must be recorded as a delivery failure, not crash the poller."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/1/token\r")

    with pytest.raises(NotifierError):
        notifier.send("hello")
