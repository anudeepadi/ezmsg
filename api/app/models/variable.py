"""Variable model."""

from typing import Optional, List, TYPE_CHECKING
import enum

from sqlalchemy import String, Text, Boolean, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.participant import ParticipantVariableValue


class VariableType(str, enum.Enum):
    """Variable type enumeration."""
    STRING = "STRING"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"


class VariableSourceType(str, enum.Enum):
    """Variable source type enumeration."""
    MANUAL = "MANUAL"
    CALCULATED = "CALCULATED"
    EXTERNAL = "EXTERNAL"
    SYSTEM = "SYSTEM"


class Variable(Base, TimestampMixin):
    """Variable model - project-defined variables."""

    __tablename__ = "variables"

    id: Mapped[int] = mapped_column(primary_key=True)
    uu_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[VariableType] = mapped_column(
        Enum(VariableType, name="variable_type", create_type=False),
        default=VariableType.STRING,
        nullable=False,
    )
    source_type: Mapped[VariableSourceType] = mapped_column(
        Enum(VariableSourceType, name="variable_source_type", create_type=False),
        default=VariableSourceType.MANUAL,
        nullable=False,
    )
    external_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    default_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_automatically_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="variables")
    participant_values: Mapped[List["ParticipantVariableValue"]] = relationship(
        "ParticipantVariableValue",
        back_populates="variable",
    )

    def __repr__(self) -> str:
        return f"<Variable(id={self.id}, name={self.name}, type={self.type})>"
