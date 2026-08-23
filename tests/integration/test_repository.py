from datetime import date, datetime

from court_alerts.core.diff import find_opened_slots
from court_alerts.core.models import CLUB_TZ
from court_alerts.db.repository import load_latest_slots, save_snapshot
from court_alerts.providers.mock import make_day, open_slot

TODAY = date(2026, 8, 24)
COURTS = ["Court 1", "Court 2"]
CLUB = "centreville"


def test_cold_start_returns_no_slots(session):
    assert load_latest_slots(session, CLUB, TODAY) == []


def test_slots_survive_a_round_trip_in_club_local_time(session):
    original = make_day(TODAY, COURTS)
    save_snapshot(session, CLUB, TODAY, "mock", original)

    restored = load_latest_slots(session, CLUB, TODAY)

    assert len(restored) == len(original)
    assert restored[0].start.tzinfo is CLUB_TZ
    assert restored[0].start == datetime(2026, 8, 24, 6, tzinfo=CLUB_TZ)


def test_latest_snapshot_wins_and_feeds_the_diff(session):
    full = make_day(TODAY, COURTS)
    after_cancellation = open_slot(full, "Court 1", 19)

    save_snapshot(session, CLUB, TODAY, "mock", full)
    before = load_latest_slots(session, CLUB, TODAY)

    save_snapshot(session, CLUB, TODAY, "mock", after_cancellation)
    after = load_latest_slots(session, CLUB, TODAY)

    opened = find_opened_slots(before, after)

    assert len(opened) == 1
    assert opened[0].court == "Court 1"
    assert opened[0].start.hour == 19