from __future__ import annotations

import httpx

from court_alerts.notify.base import NotifierError

DEFAULT_TIMEOUT_SECONDS = 10.0


class DiscordNotifier:
    """Posts a plain-text message to one Discord channel webhook."""

    name = "discord"

    def __init__(
        self,
        webhook_url: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not webhook_url:
            raise ValueError("DiscordNotifier needs a webhook URL")
        self._webhook_url = webhook_url
        self._timeout = timeout

    def send(self, text: str) -> None:
        try:
            response = httpx.post(
                self._webhook_url,
                json={"content": text},
                timeout=self._timeout,
            )
        except (httpx.RequestError, httpx.InvalidURL) as error:
            # The exception's own message can contain the full URL,
            # so only the class name is carried forward.
            raise NotifierError(
                f"could not reach Discord ({type(error).__name__})",
                notifier=self.name,
            ) from error

        if response.status_code >= 400:
            raise NotifierError(
                "Discord rejected the message",
                notifier=self.name,
                status_code=response.status_code,
            )
