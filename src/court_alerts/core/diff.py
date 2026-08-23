from __future__ import annotations

from court_alerts.core.models import Slot


def find_opened_slots(before: list[Slot], after: list[Slot]) -> list[Slot]:
    """Return slots that were unavailable in `before` but are open in `after`.

    This is what a cancellation looks like: someone released a court and it
    became bookable between two polls.
    """
    # Step 1: collect (court, start) pairs that were already open before.
    was_open = set()
    for slot in before:
        if slot.is_available:
            was_open.add(slot.key)

    # Step 2: report slots that are open now but were not open before.
    opened = []
    for slot in after:
        if slot.is_available and slot.key not in was_open:
            opened.append(slot)

    return opened