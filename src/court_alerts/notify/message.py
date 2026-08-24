from __future__ import annotations

from operator import attrgetter

from court_alerts.core.models import Slot

DISCORD_CONTENT_LIMIT = 2000
MAX_LINES = 15


def format_slot_line(slot: Slot) -> str:
    day = slot.start.strftime("%a %b %d")
    start = slot.start.strftime("%-I:%M %p")
    end = slot.end.strftime("%-I:%M %p")
    return f"- {day} · {slot.court} · {start}-{end}"


def format_alert(label: str, slots: list[Slot], club_name: str) -> str:
    """One message covering every slot that matched one subscription."""
    ordered = sorted(slots, key=attrgetter("start", "court"))

    shown = ordered[:MAX_LINES]
    hidden = len(ordered) - len(shown)

    lines = [f"**{len(ordered)} opening(s)** — {label} @ {club_name}"]
    for slot in shown:
        lines.append(format_slot_line(slot))
    if hidden > 0:
        lines.append(f"...and {hidden} more")

    text = "\n".join(lines)
    if len(text) > DISCORD_CONTENT_LIMIT:
        text = text[: DISCORD_CONTENT_LIMIT - 1] + "…"
    return text