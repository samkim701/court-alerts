from __future__ import annotations

from dataclasses import dataclass

from court_alerts.triage.base import TriageCategory


@dataclass(frozen=True)
class EvalCase:
    """One evidence bundle with the answer we expect."""

    name: str
    evidence: dict
    expected_category: TriageCategory
    expected_needs_human: bool
    note: str


def _run(
    status: str = "ok",
    slot_count: int = 64,
    opened_count: int = 0,
    alerts_sent: int = 0,
    error_type: str = "",
    error_message: str = "",
    hour: int = 20,
) -> dict:
    return {
        "started_at": f"2026-08-23T{hour:02d}:00:00-04:00",
        "on_date": "2026-08-24",
        "provider": "lifetime",
        "status": status,
        "slot_count": slot_count,
        "opened_count": opened_count,
        "alerts_sent": alerts_sent,
        "error_type": error_type,
        "error_message": error_message,
    }


def _bundle(runs: list[dict]) -> dict:
    return {
        "club_id": "centreville",
        "runs_examined": len(runs),
        "runs": runs,
    }


def _healthy(count: int, start_hour: int = 10) -> list[dict]:
    runs = []
    for offset in range(count):
        runs.append(_run(hour=start_hour + offset))
    return runs


GOLDEN_CASES: list[EvalCase] = [
    EvalCase(
        name="steady_state",
        evidence=_bundle(_healthy(5)),
        expected_category=TriageCategory.NO_ISSUE,
        expected_needs_human=False,
        note="Nothing is wrong. The model must not invent a problem.",
    ),
    EvalCase(
        name="single_timeout",
        evidence=_bundle(
            [
                _run(
                    status="provider_failed",
                    slot_count=0,
                    error_type="ProviderError",
                    error_message="read timeout after 10s",
                    hour=20,
                ),
            ]
            + _healthy(4, start_hour=16)
        ),
        expected_category=TriageCategory.TRANSIENT_UPSTREAM,
        expected_needs_human=False,
        note="One timeout among healthy runs. A retry fixes this.",
    ),
    EvalCase(
        name="persistent_timeouts",
        evidence=_bundle(
            [
                _run(
                    status="provider_failed",
                    slot_count=0,
                    error_type="ProviderError",
                    error_message="read timeout after 10s",
                    hour=20 - offset,
                )
                for offset in range(5)
            ]
        ),
        expected_category=TriageCategory.TRANSIENT_UPSTREAM,
        expected_needs_human=True,
        note="Same transient error, but it is not clearing. Escalate.",
    ),
    EvalCase(
        name="expired_session",
        evidence=_bundle(
            [
                _run(
                    status="provider_failed",
                    slot_count=0,
                    error_type="ProviderError",
                    error_message="HTTP 401 Unauthorized: session expired",
                    hour=20,
                ),
                _run(
                    status="provider_failed",
                    slot_count=0,
                    error_type="ProviderError",
                    error_message="HTTP 401 Unauthorized: session expired",
                    hour=19,
                ),
            ]
            + _healthy(3, start_hour=16)
        ),
        expected_category=TriageCategory.UPSTREAM_AUTH,
        expected_needs_human=True,
        note="Retrying will never help. Credentials must be rotated.",
    ),
    EvalCase(
        name="forbidden",
        evidence=_bundle(
            [
                _run(
                    status="provider_failed",
                    slot_count=0,
                    error_type="ProviderError",
                    error_message="HTTP 403 Forbidden: access denied for this club",
                    hour=20,
                ),
            ]
        ),
        expected_category=TriageCategory.UPSTREAM_AUTH,
        expected_needs_human=True,
        note="403 is authorisation, not a transient blip.",
    ),
    EvalCase(
        name="shape_changed",
        evidence=_bundle(
            [
                _run(
                    status="provider_failed",
                    slot_count=0,
                    error_type="ProviderError",
                    error_message="KeyError: 'startTime' missing from slot payload",
                    hour=20,
                ),
            ]
            + _healthy(3, start_hour=17)
        ),
        expected_category=TriageCategory.UPSTREAM_SCHEMA,
        expected_needs_human=True,
        note="The upstream response changed. This needs a code change.",
    ),
    EvalCase(
        name="webhook_deleted",
        evidence=_bundle(
            [
                _run(
                    status="notify_failed",
                    opened_count=3,
                    alerts_sent=0,
                    error_type="NotifierError",
                    error_message="Discord rejected the message",
                    hour=20,
                ),
            ]
            + _healthy(3, start_hour=17)
        ),
        expected_category=TriageCategory.NOTIFY_DELIVERY,
        expected_needs_human=True,
        note="Polling is fine. Delivery is broken, so alerts are silently lost.",
    ),
    EvalCase(
        name="empty_schedule",
        evidence=_bundle([_run(slot_count=0, hour=20)] + _healthy(4, start_hour=16)),
        expected_category=TriageCategory.DATA_ANOMALY,
        expected_needs_human=True,
        note="A 200 OK with zero slots after 64 every time. Silent failure.",
    ),
    EvalCase(
        name="recovered_delivery",
        evidence=_bundle(
            [
                _run(hour=21),
                _run(
                    status="notify_failed",
                    opened_count=1,
                    error_type="NotifierError",
                    error_message="Discord rejected the message",
                    hour=20,
                ),
            ]
            + _healthy(3, start_hour=17)
        ),
        expected_category=TriageCategory.NO_ISSUE,
        expected_needs_human=False,
        note="The failure is in the past and the latest run is clean.",
    ),
    EvalCase(
        name="quiet_but_healthy",
        evidence=_bundle(
            [
                _run(slot_count=58, hour=21),
                _run(slot_count=61, hour=20),
                _run(slot_count=64, hour=19),
            ]
        ),
        expected_category=TriageCategory.NO_ISSUE,
        expected_needs_human=False,
        note="Slot counts drift as the day fills. Not an anomaly.",
    ),
    EvalCase(
        name="no_history",
        evidence=_bundle([]),
        expected_category=TriageCategory.UNKNOWN,
        expected_needs_human=True,
        note="Nothing to reason from. Guessing here would be a failure.",
    ),
    EvalCase(
        name="uninformative_error",
        evidence=_bundle(
            [
                _run(
                    status="provider_failed",
                    slot_count=0,
                    error_type="ProviderError",
                    error_message="request failed",
                    hour=20,
                ),
            ]
        ),
        expected_category=TriageCategory.UNKNOWN,
        expected_needs_human=True,
        note="One vague failure with no history. Honest answer is unknown.",
    ),
]
