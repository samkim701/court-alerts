def find_opened_slots(before: list[dict], after: list[dict]) -> list[dict]:
    """Return slots that were unavailable in `before` but are open in `after`.

    This is what a cancellation looks like: someone released a court and it
    became bookable between two polls.
    """
    # Step 1: collect (court, start) pairs that were already open before.
    was_open = set()
    for slot in before:
        if slot["available"]:
            key = (slot["court"], slot["start"])
            was_open.add(key)

    # Step 2: keep slots that are open now but were not open before.
    opened = []
    for slot in after:
        if not slot["available"]:
            continue

        key = (slot["court"], slot["start"])
        if key not in was_open:
            opened.append(slot)

    return opened
