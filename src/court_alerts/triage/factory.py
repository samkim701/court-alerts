from __future__ import annotations

from court_alerts.config import get_gemini_api_key
from court_alerts.triage.base import TriageAgent
from court_alerts.triage.gemini import GeminiTriageAgent
from court_alerts.triage.heuristic import HeuristicTriageAgent


def build_triage_agent() -> TriageAgent:
    """Gemini when a key is configured, rules otherwise."""
    api_key = get_gemini_api_key()
    if api_key:
        return GeminiTriageAgent(api_key)
    return HeuristicTriageAgent()