import pytest

from court_alerts.triage.base import (
    TriageCategory,
    TriageVerdict,
    safe_triage,
    unknown_verdict,
)
from court_alerts.triage.heuristic import HeuristicTriageAgent
from court_alerts.triage.prompt import build_prompt, parse_verdict

SOURCE = "test"


def run(status="ok", slot_count=64, error_type="", error_message=""):
    return {
        "started_at": "2026-08-23T22:00:00-04:00",
        "on_date": "2026-08-24",
        "provider": "mock",
        "status": status,
        "slot_count": slot_count,
        "opened_count": 0,
        "alerts_sent": 0,
        "error_type": error_type,
        "error_message": error_message,
    }


def bundle(runs):
    return {"club_id": "centreville", "runs_examined": len(runs), "runs": runs}


class CrashingAgent:
    name = "crashing"

    def triage(self, evidence):
        raise RuntimeError("boom")


def test_unknown_verdict_asks_for_a_human():
    verdict = unknown_verdict("no idea", SOURCE)

    assert verdict.category is TriageCategory.UNKNOWN
    assert verdict.needs_human is True
    assert verdict.confidence == 0.0


def test_safe_triage_converts_a_crash_into_unknown():
    verdict = safe_triage(CrashingAgent(), bundle([run()]))

    assert verdict.category is TriageCategory.UNKNOWN
    assert "RuntimeError" in verdict.summary


def test_valid_json_is_parsed():
    raw = (
        '{"category": "notify_delivery", "needs_human": true, '
        '"confidence": 0.8, "summary": "Discord rejected the post."}'
    )

    verdict = parse_verdict(raw, SOURCE)

    assert verdict.category is TriageCategory.NOTIFY_DELIVERY
    assert verdict.needs_human is True
    assert verdict.confidence == 0.8


def test_fenced_json_is_still_parsed():
    raw = '```json\n{"category": "no_issue", "needs_human": false, "confidence": 1}\n```'

    verdict = parse_verdict(raw, SOURCE)

    assert verdict.category is TriageCategory.NO_ISSUE


def test_prose_instead_of_json_becomes_unknown():
    verdict = parse_verdict("I think the server is down.", SOURCE)

    assert verdict.category is TriageCategory.UNKNOWN


def test_invented_category_is_rejected():
    raw = '{"category": "probably_auth", "needs_human": true, "confidence": 0.9}'

    verdict = parse_verdict(raw, SOURCE)

    assert verdict.category is TriageCategory.UNKNOWN


def test_out_of_range_confidence_is_clamped():
    raw = '{"category": "no_issue", "needs_human": false, "confidence": 7.5}'

    assert parse_verdict(raw, SOURCE).confidence == 1.0


def test_non_numeric_confidence_falls_back_to_zero():
    raw = '{"category": "no_issue", "needs_human": false, "confidence": "high"}'

    assert parse_verdict(raw, SOURCE).confidence == 0.0


def test_missing_needs_human_defaults_to_true():
    raw = '{"category": "no_issue", "confidence": 0.5}'

    assert parse_verdict(raw, SOURCE).needs_human is True


def test_prompt_contains_the_evidence_and_the_escape_hatches():
    prompt = build_prompt(bundle([run()]))

    assert "centreville" in prompt
    assert "unknown" in prompt
    assert "no_issue" in prompt


def test_heuristic_calls_a_healthy_run_no_issue():
    verdict = HeuristicTriageAgent().triage(bundle([run()]))

    assert verdict.category is TriageCategory.NO_ISSUE
    assert verdict.needs_human is False


def test_heuristic_flags_delivery_failure():
    verdict = HeuristicTriageAgent().triage(bundle([run(status="notify_failed")]))

    assert verdict.category is TriageCategory.NOTIFY_DELIVERY


def test_heuristic_escalates_after_repeated_provider_failures():
    runs = []
    for _ in range(3):
        runs.append(run(status="provider_failed", error_type="ProviderError"))

    verdict = HeuristicTriageAgent().triage(bundle(runs))

    assert verdict.needs_human is True


def test_heuristic_flags_a_successful_run_with_no_slots():
    verdict = HeuristicTriageAgent().triage(bundle([run(slot_count=0)]))

    assert verdict.category is TriageCategory.DATA_ANOMALY