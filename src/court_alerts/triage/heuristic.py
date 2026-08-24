from __future__ import annotations

from court_alerts.triage.base import (
    TriageCategory,
    TriageVerdict,
    unknown_verdict,
)

CONSECUTIVE_FAILURES_FOR_HUMAN = 3


class HeuristicTriageAgent:
    """Deterministic rules. Runs without a key, and acts as the
    baseline the LLM has to beat in the eval set."""

    name = "heuristic"

    def triage(self, evidence: dict) -> TriageVerdict:
        runs = evidence.get("runs", [])
        if not runs:
            return unknown_verdict("no runs to inspect", self.name)

        latest = runs[0]
        status = latest.get("status", "")

        if status == "notify_failed":
            return TriageVerdict(
                category=TriageCategory.NOTIFY_DELIVERY,
                needs_human=True,
                confidence=0.8,
                summary="The poll succeeded but the alert could not be delivered.",
                source=self.name,
            )

        if status == "provider_failed":
            failures = 0
            for run in runs:
                if run.get("status") != "provider_failed":
                    break
                failures = failures + 1

            persistent = failures >= CONSECUTIVE_FAILURES_FOR_HUMAN
            return TriageVerdict(
                category=TriageCategory.TRANSIENT_UPSTREAM,
                needs_human=persistent,
                confidence=0.6,
                summary=f"The provider failed on the last {failures} run(s).",
                source=self.name,
            )

        if latest.get("slot_count", 0) == 0:
            return TriageVerdict(
                category=TriageCategory.DATA_ANOMALY,
                needs_human=True,
                confidence=0.7,
                summary="The poll reported success but returned no slots at all.",
                source=self.name,
            )

        return TriageVerdict(
            category=TriageCategory.NO_ISSUE,
            needs_human=False,
            confidence=0.9,
            summary="The most recent poll completed normally.",
            source=self.name,
        )