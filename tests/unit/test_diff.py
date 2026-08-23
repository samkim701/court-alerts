from datetime import date, datetime, time, timedelta

from court_alerts.core.diff import find_opened_slots
from court_alerts.core.models import CLUB_TZ, Slot

TODAY = date(2026, 8, 24)


def slot(court: str, hour: int, available: bool) -> Slot:
    """Build one test slot without repeating datetime plumbing."""
    start = datetime.combine(TODAY, time(hour=hour), tzinfo=CLUB_TZ)
    end = start + timedelta(hours=1)
    return Slot(court=court, start=start, end=end, is_available=available)


def test_detects_newly_opened_slot():
    # Arrange: 18:00 was booked, then someone cancelled.
    before = [
        slot("c1", 18, False),
        slot("c1", 19, False),
    ]
    after = [
        slot("c1", 18, True),
        slot("c1", 19, False),
    ]

    # Act
    opened = find_opened_slots(before, after)

    # Assert
    assert len(opened) == 1
    assert opened[0].court == "c1"
    assert opened[0].start.hour == 18


def test_ignores_already_open_slot():
    """A slot open in both snapshots must not alert twice."""
    before = [slot("c1", 18, True)]
    after = [slot("c1", 18, True)]

    assert find_opened_slots(before, after) == []


def test_same_time_on_different_courts_are_distinct():
    """Court 2 opening must not be masked by court 1 being open."""
    before = [
        slot("c1", 18, True),
        slot("c2", 18, False),
    ]
    after = [
        slot("c1", 18, True),
        slot("c2", 18, True),
    ]

    opened = find_opened_slots(before, after)

    assert len(opened) == 1
    assert opened[0].court == "c2"


def test_slot_that_closed_is_not_reported():
    """Bookings disappearing is normal, not an opening."""
    before = [slot("c1", 18, True)]
    after = [slot("c1", 18, False)]

    assert find_opened_slots(before, after) == []


def test_empty_before_reports_all_open_slots():
    """First run has no previous snapshot to compare against."""
    after = [
        slot("c1", 18, True),
        slot("c1", 19, False),
    ]

    opened = find_opened_slots([], after)

    assert len(opened) == 1
    assert opened[0].start.hour == 18