from court_alerts.core.diff import find_opened_slots


def test_detects_newly_opened_slot():
    before = [
        {"court": "c1", "start": "18:00", "available": False},
        {"court": "c1", "start": "19:00", "available": False},
    ]
    after = [
        {"court": "c1", "start": "18:00", "available": True},
        {"court": "c1", "start": "19:00", "available": False},
    ]

    opened = find_opened_slots(before, after)

    assert len(opened) == 1
    assert opened[0]["start"] == "18:00"


def test_ignores_already_open_slot():
    before = [{"court": "c1", "start": "18:00", "available": True}]
    after = [{"court": "c1", "start": "18:00", "available": True}]

    assert find_opened_slots(before, after) == []
