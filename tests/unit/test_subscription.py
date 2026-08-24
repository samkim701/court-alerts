from datetime import date, datetime, time, timedelta

import pytest

from court_alerts.core.models import CLUB_TZ, Slot
from court_alerts.core.subscription import (
    Subscription,
    filter_slots,
    matches_criteria,
    route,
)

MONDAY = date(2026, 8, 24)


def slot(court: str, hour: int, on_date: date = MONDAY) -> Slot:
    start = datetime.combine(on_date, time(hour=hour), tzinfo=CLUB_TZ)
    return Slot(
        court=court,
        start=start,
        end=start + timedelta(hours=1),
        is_available=True,
    )


def evening(courts=None) -> Subscription:
    return Subscription(
        label="Monday evening",
        weekdays=frozenset({0}),
        earliest_hour=18,
        latest_hour=21,
        courts=courts,
    )


def test_slot_inside_the_window_matches():
    assert matches_criteria(evening(), slot("Court 1", 19)) is True


def test_latest_hour_is_exclusive():
    assert matches_criteria(evening(), slot("Court 1", 21)) is False


def test_earliest_hour_is_inclusive():
    assert matches_criteria(evening(), slot("Court 1", 18)) is True


def test_wrong_weekday_does_not_match():
    tuesday = date(2026, 8, 25)
    assert matches_criteria(evening(), slot("Court 1", 19, tuesday)) is False


def test_none_courts_means_any_court():
    assert matches_criteria(evening(), slot("Court 7", 19)) is True


def test_named_courts_exclude_the_others():
    subscription = evening(courts=frozenset({"Court 1"}))

    assert matches_criteria(subscription, slot("Court 1", 19)) is True
    assert matches_criteria(subscription, slot("Court 2", 19)) is False


def test_filter_keeps_only_matching_slots():
    slots = [
        slot("Court 1", 7),
        slot("Court 1", 19),
        slot("Court 2", 20),
    ]

    matched = filter_slots(evening(), slots)

    assert len(matched) == 2


def test_route_drops_subscriptions_with_no_matches():
    morning = Subscription(
        label="Monday morning",
        weekdays=frozenset({0}),
        earliest_hour=6,
        latest_hour=9,
    )

    routed = route([evening(), morning], [slot("Court 1", 19)])

    assert len(routed) == 1
    assert routed[0][0].label == "Monday evening"


def test_backwards_window_is_rejected_at_construction():
    with pytest.raises(ValueError):
        Subscription(
            label="broken",
            weekdays=frozenset({0}),
            earliest_hour=21,
            latest_hour=18,
        )