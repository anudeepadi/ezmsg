"""Timing element model."""

from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.variable import Variable


class TimingElement(Base, TimestampMixin):
    """Timing element model - scheduling offsets."""

    __tablename__ = "timing_elements"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    offset_direction: Mapped[str] = mapped_column(String(10), default="AFTER", nullable=False)
    offset_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offset_hours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offset_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offset_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overwrite_time: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overwritten_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    overwritten_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_variable_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("variables.id"),
        nullable=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="timing_elements")
    time_variable: Mapped[Optional["Variable"]] = relationship("Variable")

    def __repr__(self) -> str:
        return f"<TimingElement(id={self.id}, name={self.name})>"
