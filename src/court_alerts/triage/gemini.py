from __future__ import annotations

import httpx

from court_alerts.config import GEMINI_MODEL
from court_alerts.triage.base import TriageVerdict, unknown_verdict
from court_alerts.triage.prompt import build_prompt, parse_verdict

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_TIMEOUT_SECONDS = 20.0


class GeminiTriageAgent:
    """Asks Gemini to classify a run history. Never raises."""

    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = GEMINI_MODEL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not api_key:
            raise ValueError("GeminiTriageAgent needs an API key")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def triage(self, evidence: dict) -> TriageVerdict:
        url = ENDPOINT.format(model=self._model)
        body = {
            "contents": [
                {"parts": [{"text": build_prompt(evidence)}]},
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0,
            },
        }

        try:
            response = httpx.post(
                url,
                headers={"x-goog-api-key": self._api_key},
                json=body,
                timeout=self._timeout,
            )
        except httpx.RequestError as error:
            return unknown_verdict(
                f"could not reach Gemini ({type(error).__name__})", self.name
            )

        if response.status_code >= 400:
            return unknown_verdict(
                f"Gemini returned HTTP {response.status_code}", self.name
            )

        try:
            payload = response.json()
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            return unknown_verdict(
                f"unexpected Gemini response shape ({type(error).__name__})",
                self.name,
            )

        return parse_verdict(text, self.name)