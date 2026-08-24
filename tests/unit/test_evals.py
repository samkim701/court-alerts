from court_alerts.evals.cases import GOLDEN_CASES
from court_alerts.evals.runner import score_agent
from court_alerts.triage.heuristic import HeuristicTriageAgent

HEURISTIC_CATEGORY_FLOOR = 6


def test_golden_case_names_are_unique():
    names = set()
    for case in GOLDEN_CASES:
        assert case.name not in names
        names.add(case.name)


def test_every_case_carries_a_note():
    for case in GOLDEN_CASES:
        assert case.note


def test_heuristic_baseline_is_stable():
    report = score_agent(HeuristicTriageAgent())

    assert report.total == len(GOLDEN_CASES)
    assert report.category_hits >= HEURISTIC_CATEGORY_FLOOR


def test_scoring_a_crashing_agent_does_not_raise():
    class CrashingAgent:
        name = "crashing"

        def triage(self, evidence):
            raise RuntimeError("boom")

    report = score_agent(CrashingAgent())

    assert report.total == len(GOLDEN_CASES)
    assert report.category_hits <= 2
