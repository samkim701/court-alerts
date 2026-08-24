from __future__ import annotations

from sqlalchemy.orm import Session

from court_alerts.db.repository import load_recent_runs

MAX_ERROR_CHARS = 300


def build_evidence(session: Session, club_id: str, limit: int = 10) -> dict:
    """Flat, JSON-safe history of recent polls.

    Only fields chosen here can ever reach the model. Nothing is copied
    wholesale from an exception or a response body, so there is no path
    for a webhook URL or an API key to leak into a prompt.
    """
    runs = load_recent_runs(session, club_id, limit)

    entries = []
    for run in runs:
        message = run.error_message or ""
        entries.append(
            {
                "started_at": run.started_at.isoformat(),
                "on_date": run.on_date.isoformat(),
                "provider": run.provider,
                "status": run.status,
                "slot_count": run.slot_count,
                "opened_count": run.opened_count,
                "alerts_sent": run.alerts_sent,
                "error_type": run.error_type or "",
                "error_message": message[:MAX_ERROR_CHARS],
            }
        )

    return {
        "club_id": club_id,
        "runs_examined": len(entries),
        "runs": entries,
    }