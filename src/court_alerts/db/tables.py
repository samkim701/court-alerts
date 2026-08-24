from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared metadata for every table in the project."""


class PollStatus(str, Enum):
    """How one poll attempt ended."""

    OK = "ok"
    PROVIDER_FAILED = "provider_failed"
    NOTIFY_FAILED = "notify_failed"


class Snapshot(Base):
    """One successful poll of one club's schedule for one day."""

    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[str] = mapped_column(String(64))
    on_date: Mapped[date] = mapped_column(Date)
    provider: Mapped[str] = mapped_column(String(32))
    polled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    slot_count: Mapped[int] = mapped_column(Integer)

    slots: Mapped[list["SnapshotSlot"]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
        order_by="SnapshotSlot.start",
    )

    __table_args__ = (
        Index(
            "ix_snapshots_club_date_polled",
            "club_id",
            "on_date",
            "polled_at",
        ),
    )


class SnapshotSlot(Base):
    """One court/time block inside a snapshot."""

    __tablename__ = "snapshot_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("snapshots.id", ondelete="CASCADE")
    )
    court: Mapped[str] = mapped_column(String(64))
    start: Mapped[datetime] = mapped_column("start_at", DateTime(timezone=True))
    end: Mapped[datetime] = mapped_column("end_at", DateTime(timezone=True))
    is_available: Mapped[bool]

    snapshot: Mapped[Snapshot] = relationship(back_populates="slots")

    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "court",
            "start_at",
            name="uq_snapshot_slot",
        ),
    )


class PollRun(Base):
    """One poll attempt — successful or not.

    This is the raw material the triage agent reads. Every field here
    exists because it helps answer "what went wrong, and does it matter?"
    """

    __tablename__ = "poll_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[str] = mapped_column(String(64))
    on_date: Mapped[date] = mapped_column(Date)
    provider: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    status: Mapped[str] = mapped_column(String(32))
    slot_count: Mapped[int] = mapped_column(Integer, default=0)
    opened_count: Mapped[int] = mapped_column(Integer, default=0)
    alerts_sent: Mapped[int] = mapped_column(Integer, default=0)

    error_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("snapshots.id", ondelete="SET NULL"), nullable=True
    )
    triage_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    triage_needs_human: Mapped[bool | None] = mapped_column(nullable=True)
    triage_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    triage_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    triage_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    triaged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "ix_poll_runs_club_date_started",
            "club_id",
            "on_date",
            "started_at",
        ),
    )
