"""Scheduled message model - the scheduler work queue."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
import enum

from sqlalchemy import String, Text, Integer, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.participant import MessagingChannelType

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.participant import Participant
    from app.models.messaging_node import MessagingNode
    from app.models.message_template import MessageTemplate


class ScheduledMessageStatus(str, enum.Enum):
    """Scheduled message status enumeration."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SENT = "SENT"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class SmsMessageDirection(str, enum.Enum):
    """Message direction enumeration."""
    OUTGOING = "OUTGOING"
    INCOMING = "INCOMING"


class ScheduledMessage(Base, TimestampMixin):
    """Scheduled message model - the scheduler work queue.

    This is the CRITICAL table for message scheduling and delivery.
    Uses partial indexes for efficient claiming by the worker.
    """

    __tablename__ = "scheduled_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), nullable=False)
    messaging_node_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messaging_nodes.id"),
        nullable=True,
    )
    template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("message_templates.id"),
        nullable=True,
    )
    status: Mapped[ScheduledMessageStatus] = mapped_column(
        Enum(ScheduledMessageStatus, name="scheduled_message_status", create_type=False),
        default=ScheduledMessageStatus.PENDING,
        nullable=False,
        index=True,
    )
    message_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    quick_replies: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    send_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    direction: Mapped[SmsMessageDirection] = mapped_column(
        Enum(SmsMessageDirection, name="sms_message_direction", create_type=False),
        default=SmsMessageDirection.OUTGOING,
        nullable=False,
    )
    channel_type: Mapped[MessagingChannelType] = mapped_column(
        Enum(MessagingChannelType, name="messaging_channel_type", create_type=False),
        default=MessagingChannelType.MOBILE_APP,
        nullable=False,
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Retry management
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Idempotency and locking
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lock_token: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    extra_data: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="scheduled_messages")
    participant: Mapped["Participant"] = relationship("Participant", back_populates="scheduled_messages")
    messaging_node: Mapped[Optional["MessagingNode"]] = relationship(
        "MessagingNode",
        back_populates="scheduled_messages",
    )
    template: Mapped[Optional["MessageTemplate"]] = relationship("MessageTemplate")

    def __repr__(self) -> str:
        return f"<ScheduledMessage(id={self.id}, status={self.status}, send_at={self.send_at})>"
