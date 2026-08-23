from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared metadata for every table in the project."""


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