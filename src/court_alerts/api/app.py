from __future__ import annotations

from datetime import date

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from court_alerts.api.schemas import (
    OpeningOut,
    RunOut,
    SubscriptionOut,
    TriageOut,
)
from court_alerts.cli import DEMO_CLUB_ID, build_demo_subscriptions
from court_alerts.config import CLUB_NAME
from court_alerts.db.repository import load_latest_slots, load_recent_runs
from court_alerts.db.session import SessionLocal

app = FastAPI(title="court-alerts", version="0.1.0")


@app.get("/")
def root() -> dict[str, str]:
    """Point a curious browser at the docs."""
    return {"service": "court-alerts", "docs": "/docs"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_session():
    """One session per request, always closed."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "club": CLUB_NAME}


@app.get("/api/openings", response_model=list[OpeningOut])
def list_openings(
    on_date: date | None = None,
    session: Session = Depends(get_session),
) -> list[OpeningOut]:
    """Bookable slots in the most recent stored snapshot."""
    target = on_date or date.today()
    slots = load_latest_slots(session, DEMO_CLUB_ID, target)

    openings = []
    for slot in slots:
        if slot.is_available:
            openings.append(
                OpeningOut(court=slot.court, start=slot.start, end=slot.end)
            )
    return openings


@app.get("/api/runs", response_model=list[RunOut])
def list_runs(
    limit: int = 20,
    session: Session = Depends(get_session),
) -> list[RunOut]:
    """Recent poll attempts, newest first, with triage verdicts."""
    runs = load_recent_runs(session, DEMO_CLUB_ID, limit)

    out = []
    for run in runs:
        triage = None
        if run.triage_category is not None:
            triage = TriageOut(
                category=run.triage_category,
                needs_human=bool(run.triage_needs_human),
                confidence=float(run.triage_confidence or 0.0),
                summary=run.triage_summary or "",
                source=run.triage_source or "",
                triaged_at=run.triaged_at,
            )

        out.append(
            RunOut(
                id=run.id,
                started_at=run.started_at,
                status=run.status,
                slot_count=run.slot_count,
                opened_count=run.opened_count,
                alerts_sent=run.alerts_sent,
                error_type=run.error_type or None,
                error_message=run.error_message or None,
                triage=triage,
            )
        )
    return out


@app.get("/api/subscriptions", response_model=list[SubscriptionOut])
def list_subscriptions() -> list[SubscriptionOut]:
    """Read-only view of the hard-coded subscriptions."""
    out = []
    for subscription in build_demo_subscriptions():
        courts = None
        if subscription.courts is not None:
            courts = sorted(subscription.courts)

        out.append(
            SubscriptionOut(
                label=subscription.label,
                weekdays=sorted(subscription.weekdays),
                earliest_hour=subscription.earliest_hour,
                latest_hour=subscription.latest_hour,
                courts=courts,
            )
        )
    return out
