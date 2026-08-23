def find_opened_slots(before: list[dict], after: list[dict]) -> list[dict]:
    """Return slots that were unavailable in `before` but are open in `after`.

    This is what a cancellation looks like: someone released a court and it
    became bookable between two polls.
    """
    was_open = {(s["court"], s["start"]) for s in before if s["available"]}
    return [
        s for s in after if s["available"] and (s["court"], s["start"]) not in was_open
    ]
