from __future__ import annotations

from dataclasses import dataclass

from court_alerts.evals.cases import GOLDEN_CASES, EvalCase
from court_alerts.triage.base import TriageAgent, TriageVerdict, safe_triage


@dataclass(frozen=True)
class CaseResult:
    case: EvalCase
    verdict: TriageVerdict
    category_ok: bool
    needs_human_ok: bool


@dataclass(frozen=True)
class EvalReport:
    agent: str
    results: list[CaseResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def category_hits(self) -> int:
        hits = 0
        for result in self.results:
            if result.category_ok:
                hits = hits + 1
        return hits

    @property
    def needs_human_hits(self) -> int:
        hits = 0
        for result in self.results:
            if result.needs_human_ok:
                hits = hits + 1
        return hits


def score_agent(agent: TriageAgent, cases: list[EvalCase] | None = None) -> EvalReport:
    """Run every case through one agent and grade the answers.

    safe_triage is used so a crashing agent scores zero instead of
    aborting the run — the eval measures behaviour, not luck.
    """
    if cases is None:
        cases = GOLDEN_CASES

    results = []
    for case in cases:
        verdict = safe_triage(agent, case.evidence)
        results.append(
            CaseResult(
                case=case,
                verdict=verdict,
                category_ok=verdict.category is case.expected_category,
                needs_human_ok=verdict.needs_human == case.expected_needs_human,
            )
        )

    return EvalReport(agent=agent.name, results=results)


def format_report(report: EvalReport) -> str:
    lines = [f"agent: {report.agent}"]

    for result in report.results:
        mark = "PASS" if result.category_ok else "FAIL"
        lines.append(
            f"  [{mark}] {result.case.name}: "
            f"expected {result.case.expected_category.value}, "
            f"got {result.verdict.category.value}"
        )

    lines.append(f"  category:    {report.category_hits}/{report.total}")
    lines.append(f"  needs_human: {report.needs_human_hits}/{report.total}")
    return "\n".join(lines)
