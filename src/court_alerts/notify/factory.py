from __future__ import annotations

from court_alerts.config import get_discord_webhook_url
from court_alerts.notify.base import Notifier
from court_alerts.notify.console import ConsoleNotifier
from court_alerts.notify.discord import DiscordNotifier


def build_notifier() -> Notifier:
    """Discord when a webhook is configured, console otherwise."""
    webhook_url = get_discord_webhook_url()
    if webhook_url:
        return DiscordNotifier(webhook_url)
    return ConsoleNotifier()