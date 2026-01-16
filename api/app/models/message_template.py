"""Message template models."""

from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.language import AvailableLanguage
    from app.models.variable import Variable


class MessageTemplate(Base, TimestampMixin):
    """Message template model."""

    __tablename__ = "message_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(50), default="STANDARD", nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="templates")
    texts: Mapped[List["MessageTemplateText"]] = relationship(
        "MessageTemplateText",
        back_populates="template",
        cascade="all, delete-orphan",
    )
    template_variables: Mapped[List["MessageTemplateVariable"]] = relationship(
        "MessageTemplateVariable",
        back_populates="template",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<MessageTemplate(id={self.id}, name={self.name})>"


class MessageTemplateText(Base, TimestampMixin):
    """Localized message template content."""

    __tablename__ = "message_template_texts"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("message_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    language_id: Mapped[int] = mapped_column(
        ForeignKey("available_languages.id"),
        nullable=False,
    )
    message_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    quick_replies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    template: Mapped["MessageTemplate"] = relationship("MessageTemplate", back_populates="texts")
    language: Mapped["AvailableLanguage"] = relationship("AvailableLanguage")

    def __repr__(self) -> str:
        return f"<MessageTemplateText(template_id={self.template_id}, language_id={self.language_id})>"


class MessageTemplateVariable(Base, TimestampMixin):
    """Join table for template-variable relationships."""

    __tablename__ = "message_template_variables"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("message_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    variable_id: Mapped[int] = mapped_column(
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    template: Mapped["MessageTemplate"] = relationship(
        "MessageTemplate",
        back_populates="template_variables",
    )
    variable: Mapped["Variable"] = relationship("Variable")

    def __repr__(self) -> str:
        return f"<MessageTemplateVariable(template_id={self.template_id}, variable_id={self.variable_id})>"
