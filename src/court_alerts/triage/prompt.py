from __future__ import annotations

import json

from court_alerts.triage.base import (
    MAX_SUMMARY_CHARS,
    TriageCategory,
    TriageVerdict,
    unknown_verdict,
)

INSTRUCTIONS = """You are triaging a court-availability monitor.

Every few minutes the monitor polls one club's schedule, compares it to
the previous snapshot, and sends an alert when a booked court opens up.
You are given the recent run history as JSON.

Decide which single category best explains the most recent run:

- no_issue: the latest run succeeded and the history looks normal.
- transient_upstream: the provider failed in a way a retry would fix
  (timeout, 5xx, connection reset), and it is not persistent.
- upstream_auth: the provider is rejecting us (401/403, expired session).
- upstream_schema: the provider responded, but the shape of the data
  changed, so parsing broke.
- notify_delivery: polling worked; sending the alert failed.
- data_anomaly: the poll "succeeded" but the numbers are implausible,
  such as slot_count dropping to zero when earlier runs saw many.
- unknown: the evidence does not support any of the above.

Rules:
- Use unknown whenever you are not confident. Guessing is worse than
  admitting uncertainty.
- Use no_issue when nothing is wrong. Do not invent a problem.
- Base every claim on the JSON you were given. Do not assume facts
  that are not present.
- needs_human should be true when a person must act (code change,
  credential rotation, repeated failures), false for self-healing
  situations.

Reply with JSON only, in exactly this shape:
{"category": "...", "needs_human": true, "confidence": 0.0,
 "summary": "one or two sentences"}
"""


def build_prompt(evidence: dict) -> str:
    return f"{INSTRUCTIONS}\n\nEvidence:\n{json.dumps(evidence, indent=2)}"


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        kept = []
        for line in lines:
            if line.strip().startswith("```"):
                continue
            kept.append(line)
        cleaned = "\n".join(kept).strip()
    return cleaned


def parse_verdict(raw_text: str, source: str) -> TriageVerdict:
    """Turn model output into a verdict, never trusting any of it."""
    cleaned = _strip_fences(raw_text)

    try:
        payload = json.loads(cleaned)
    except (ValueError, TypeError):
        return unknown_verdict("model did not return JSON", source)

    if not isinstance(payload, dict):
        return unknown_verdict("model returned JSON that is not an object", source)

    raw_category = payload.get("category")
    try:
        category = TriageCategory(raw_category)
    except ValueError:
        return unknown_verdict(
            f"model returned an unrecognised category: {raw_category!r}", source
        )

    raw_confidence = payload.get("confidence", 0.0)
    try:
        confidence = float(raw_confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence < 0.0:
        confidence = 0.0
    if confidence > 1.0:
        confidence = 1.0

    summary = str(payload.get("summary", ""))[:MAX_SUMMARY_CHARS]

    return TriageVerdict(
        category=category,
        needs_human=bool(payload.get("needs_human", True)),
        confidence=confidence,
        summary=summary,
        source=source,
    )