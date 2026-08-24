from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

MAX_SUMMARY_CHARS = 400


class TriageCategory(str, Enum):
    """What a poll failure most likely is.

    NO_ISSUE and UNKNOWN are deliberate escape hatches. A model with no
    way to say "nothing is wrong" or "I cannot tell" will invent a
    diagnosis for healthy runs, which is worse than silence.
    """

    NO_ISSUE = "no_issue"
    TRANSIENT_UPSTREAM = "transient_upstream"
    UPSTREAM_AUTH = "upstream_auth"
    UPSTREAM_SCHEMA = "upstream_schema"
    NOTIFY_DELIVERY = "notify_delivery"
    DATA_ANOMALY = "data_anomaly"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TriageVerdict:
    """One judgement about the recent history of a club's polls."""

    category: TriageCategory
    needs_human: bool
    confidence: float
    summary: str
    source: str


def unknown_verdict(reason: str, source: str) -> TriageVerdict:
    """The safe answer whenever triage cannot produce a real one."""
    return TriageVerdict(
        category=TriageCategory.UNKNOWN,
        needs_human=True,
        confidence=0.0,
        summary=reason[:MAX_SUMMARY_CHARS],
        source=source,
    )


@runtime_checkable
class TriageAgent(Protocol):
    """Anything that can turn an evidence bundle into a verdict."""

    name: str

    def triage(self, evidence: dict) -> TriageVerdict:
        ...


def safe_triage(agent: TriageAgent, evidence: dict) -> TriageVerdict:
    """Run an agent and turn any escaping exception into UNKNOWN.

    Triage observes the poller; it must never be able to kill it.
    Individual agents handle their own expected failures, and this
    wrapper is the last line for the ones nobody anticipated.
    """
    try:
        return agent.triage(evidence)
    except Exception as error:
        return unknown_verdict(
            f"triage agent crashed ({type(error).__name__})", agent.name
        )