from __future__ import annotations

from typing import Protocol, runtime_checkable


class NotifierError(Exception):
    """A notifier could not deliver a message."""

    def __init__(
        self,
        message: str,
        *,
        notifier: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.notifier = notifier
        self.status_code = status_code

    def as_evidence(self) -> dict[str, str]:
        """Flat, log-safe facts for the triage agent's evidence bundle."""
        return {
            "error_type": type(self).__name__,
            "message": self.message,
            "notifier": self.notifier,
            "status_code": str(self.status_code),
        }


@runtime_checkable
class Notifier(Protocol):
    """Anything that can deliver one alert message."""

    name: str

    def send(self, text: str) -> None:
        """Deliver the message. Raises NotifierError on failure."""
        ...