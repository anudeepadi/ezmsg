"""Participant models."""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
import enum

from sqlalchemy import String, Text, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.language import AvailableLanguage
    from app.models.variable import Variable
    from app.models.scheduled_message import ScheduledMessage
    from app.models.incoming_message import IncomingMessage


class ParticipantStatus(str, enum.Enum):
    """Participant status enumeration."""
    NONE = "NONE"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"
    COMPLETED = "COMPLETED"
    BLOCKED_SYSTEM = "BLOCKED_SYSTEM"


class MessagingChannelType(str, enum.Enum):
    """Messaging channel type enumeration."""
    NONE = "NONE"
    TWILIO = "TWILIO"
    FACEBOOK = "FACEBOOK"
    MOBILE_APP = "MOBILE_APP"
    EMAIL = "EMAIL"


class Participant(Base, TimestampMixin):
    """Participant model - enrolled recipients in a project."""

    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    uu_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    channel_type: Mapped[MessagingChannelType] = mapped_column(
        Enum(MessagingChannelType, name="messaging_channel_type", create_type=False),
        default=MessagingChannelType.MOBILE_APP,
        nullable=False,
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        Enum(ParticipantStatus, name="participant_status", create_type=False),
        default=ParticipantStatus.ACTIVE,
        nullable=False,
    )
    current_language_id: Mapped[int] = mapped_column(
        ForeignKey("available_languages.id"),
        default=1,
        nullable=False,
    )
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone_number_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_test_participant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    participant_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fcm_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    enrolled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_data: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="participants")
    current_language: Mapped["AvailableLanguage"] = relationship("AvailableLanguage")
    variable_values: Mapped[List["ParticipantVariableValue"]] = relationship(
        "ParticipantVariableValue",
        back_populates="participant",
        cascade="all, delete-orphan",
    )
    scheduled_messages: Mapped[List["ScheduledMessage"]] = relationship(
        "ScheduledMessage",
        back_populates="participant",
    )
    incoming_messages: Mapped[List["IncomingMessage"]] = relationship(
        "IncomingMessage",
        back_populates="participant",
    )

    def __repr__(self) -> str:
        return f"<Participant(id={self.id}, project_id={self.project_id}, status={self.status})>"


class ParticipantVariableValue(Base, TimestampMixin):
    """Per-participant variable values."""

    __tablename__ = "participant_variable_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
    )
    variable_id: Mapped[int] = mapped_column(
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
    )
    variable_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    participant: Mapped["Participant"] = relationship(
        "Participant",
        back_populates="variable_values",
    )
    variable: Mapped["Variable"] = relationship("Variable", back_populates="participant_values")

    def __repr__(self) -> str:
        return f"<ParticipantVariableValue(participant_id={self.participant_id}, variable_id={self.variable_id})>"
