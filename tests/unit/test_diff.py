from court_alerts.core.diff import find_opened_slots


def test_detects_newly_opened_slot():
    # Arrange: 18:00 was booked, then someone cancelled.
    before = [
        {"court": "c1", "start": "18:00", "available": False},
        {"court": "c1", "start": "19:00", "available": False},
    ]
    after = [
        {"court": "c1", "start": "18:00", "available": True},
        {"court": "c1", "start": "19:00", "available": False},
    ]

    # Act
    opened = find_opened_slots(before, after)

    # Assert
    assert len(opened) == 1
    assert opened[0]["start"] == "18:00"


def test_ignores_already_open_slot():
    """A slot open in both snapshots must not alert twice."""
    before = [{"court": "c1", "start": "18:00", "available": True}]
    after = [{"court": "c1", "start": "18:00", "available": True}]

    assert find_opened_slots(before, after) == []


def test_same_time_on_different_courts_are_distinct():
    """Court 2 opening must not be masked by court 1 being open."""
    before = [
        {"court": "c1", "start": "18:00", "available": True},
        {"court": "c2", "start": "18:00", "available": False},
    ]
    after = [
        {"court": "c1", "start": "18:00", "available": True},
        {"court": "c2", "start": "18:00", "available": True},
    ]

    opened = find_opened_slots(before, after)

    assert len(opened) == 1
    assert opened[0]["court"] == "c2"


def test_slot_that_closed_is_not_reported():
    """Bookings disappearing is normal, not an opening."""
    before = [{"court": "c1", "start": "18:00", "available": True}]
    after = [{"court": "c1", "start": "18:00", "available": False}]

    assert find_opened_slots(before, after) == []


def test_empty_before_reports_all_open_slots():
    """First run has no previous snapshot to compare against."""
    after = [
        {"court": "c1", "start": "18:00", "available": True},
        {"court": "c1", "start": "19:00", "available": False},
    ]

    opened = find_opened_slots([], after)

    assert len(opened) == 1
    assert opened[0]["start"] == "18:00"
