"""Incoming message model."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import String, Text, Boolean, DateTime, Numeric, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.participant import MessagingChannelType

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.participant import Participant
    from app.models.scheduled_message import ScheduledMessage
    from app.models.message_template import MessageTemplate


class IncomingMessage(Base, TimestampMixin):
    """Incoming message model - inbound webhooks and replies."""

    __tablename__ = "incoming_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    participant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("participants.id"), nullable=True)
    scheduled_message_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("scheduled_messages.id"),
        nullable=True,
    )
    template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("message_templates.id"),
        nullable=True,
    )
    channel_type: Mapped[MessagingChannelType] = mapped_column(
        Enum(MessagingChannelType, name="messaging_channel_type", create_type=False),
        nullable=False,
    )
    from_address: Mapped[str] = mapped_column(String(100), nullable=False)
    to_address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quick_reply_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_data: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project")
    participant: Mapped[Optional["Participant"]] = relationship(
        "Participant",
        back_populates="incoming_messages",
    )
    replied_to_message: Mapped[Optional["ScheduledMessage"]] = relationship("ScheduledMessage")
    template: Mapped[Optional["MessageTemplate"]] = relationship("MessageTemplate")

    def __repr__(self) -> str:
        return f"<IncomingMessage(id={self.id}, from={self.from_address})>"
