from __future__ import annotations

from dataclasses import dataclass

from court_alerts.core.models import Slot


@dataclass(frozen=True)
class Subscription:
    """A standing request to be told when a court opens.

    `courts=None` means any court. Hours refer to the slot's start,
    with `latest_hour` exclusive: 18-21 matches slots starting at
    18, 19 and 20.
    """

    label: str
    weekdays: frozenset[int]
    earliest_hour: int
    latest_hour: int
    courts: frozenset[str] | None = None

    def __post_init__(self) -> None:
        if self.earliest_hour >= self.latest_hour:
            raise ValueError(
                f"{self.label}: earliest_hour must come before latest_hour"
            )
        for day in self.weekdays:
            if day < 0 or day > 6:
                raise ValueError(f"{self.label}: weekday {day} is out of range")


def matches_criteria(subscription: Subscription, slot: Slot) -> bool:
    """True when court, weekday and hour all fit the subscription.

    Availability is deliberately not checked here — the diff layer
    already decided which slots just opened. The name says `criteria`
    so nobody mistakes this for a full "should we alert?" answer.
    """
    if subscription.courts is not None:
        if slot.court not in subscription.courts:
            return False

    if slot.start.weekday() not in subscription.weekdays:
        return False

    if slot.start.hour < subscription.earliest_hour:
        return False

    if slot.start.hour >= subscription.latest_hour:
        return False

    return True


def filter_slots(subscription: Subscription, slots: list[Slot]) -> list[Slot]:
    """Every slot in the list that this subscription cares about."""
    matched = []
    for slot in slots:
        if matches_criteria(subscription, slot):
            matched.append(slot)
    return matched


def route(
    subscriptions: list[Subscription],
    opened: list[Slot],
) -> list[tuple[Subscription, list[Slot]]]:
    """Pair each subscription with its matching slots.

    Subscriptions with no matches are dropped, so a caller can never
    accidentally send an empty alert.
    """
    routed = []
    for subscription in subscriptions:
        matched = filter_slots(subscription, opened)
        if matched:
            routed.append((subscription, matched))
    return routed