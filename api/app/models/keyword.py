"""SMS keyword model."""

from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.language import AvailableLanguage
    from app.models.messaging_node import MessagingNode
    from app.models.variable import Variable
    from app.models.message_template import MessageTemplate


class SmsKeyword(Base, TimestampMixin):
    """SMS keyword model - trigger actions on keyword match."""

    __tablename__ = "sms_keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    language_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("available_languages.id"),
        nullable=True,
    )
    keyword_action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    keyword_name: Mapped[str] = mapped_column(String(100), nullable=False)
    keyword_text: Mapped[str] = mapped_column(String(255), nullable=False)
    messaging_node_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messaging_nodes.id"),
        nullable=True,
    )
    variable_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("variables.id"),
        nullable=True,
    )
    variable_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("message_templates.id"),
        nullable=True,
    )
    message_pool: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="keywords")
    language: Mapped[Optional["AvailableLanguage"]] = relationship("AvailableLanguage")
    messaging_node: Mapped[Optional["MessagingNode"]] = relationship("MessagingNode")
    variable: Mapped[Optional["Variable"]] = relationship("Variable")
    response_template: Mapped[Optional["MessageTemplate"]] = relationship("MessageTemplate")

    def __repr__(self) -> str:
        return f"<SmsKeyword(id={self.id}, keyword={self.keyword_text})>"
