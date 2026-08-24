from __future__ import annotations


class ConsoleNotifier:
    """Prints instead of sending, and keeps what it sent for tests."""

    name = "console"

    def __init__(self, echo: bool = True) -> None:
        self.echo = echo
        self.sent: list[str] = []

    def send(self, text: str) -> None:
        self.sent.append(text)
        if self.echo:
            print(text)