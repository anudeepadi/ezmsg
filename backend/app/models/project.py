"""Project models."""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
import enum

from sqlalchemy import String, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.participant import Participant
    from app.models.variable import Variable
    from app.models.message_template import MessageTemplate
    from app.models.messaging_node import MessagingNode
    from app.models.timing_element import TimingElement
    from app.models.conditional_expression import ConditionalExpression
    from app.models.scheduled_message import ScheduledMessage
    from app.models.keyword import SmsKeyword


class ProjectStatus(str, enum.Enum):
    """Project status enumeration."""
    NONE = "NONE"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"
    DELETED = "DELETED"


class Project(Base, TimestampMixin):
    """Project model - container for messaging protocols."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    uu_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", create_type=False),
        default=ProjectStatus.ACTIVE,
        nullable=False,
    )
    initial_triggering_node_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messaging_nodes.id", use_alter=True),
        nullable=True,
    )
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_projects", foreign_keys=[user_id])
    project_users: Mapped[List["ProjectUser"]] = relationship("ProjectUser", back_populates="project")
    participants: Mapped[List["Participant"]] = relationship("Participant", back_populates="project")
    variables: Mapped[List["Variable"]] = relationship("Variable", back_populates="project")
    templates: Mapped[List["MessageTemplate"]] = relationship("MessageTemplate", back_populates="project")
    nodes: Mapped[List["MessagingNode"]] = relationship(
        "MessagingNode",
        back_populates="project",
        foreign_keys="MessagingNode.project_id",
    )
    timing_elements: Mapped[List["TimingElement"]] = relationship("TimingElement", back_populates="project")
    conditional_expressions: Mapped[List["ConditionalExpression"]] = relationship(
        "ConditionalExpression",
        back_populates="project",
    )
    scheduled_messages: Mapped[List["ScheduledMessage"]] = relationship("ScheduledMessage", back_populates="project")
    keywords: Mapped[List["SmsKeyword"]] = relationship("SmsKeyword", back_populates="project")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"


class ProjectUser(Base):
    """Project-User access mapping for role-based access control."""

    __tablename__ = "project_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    access_level: Mapped[str] = mapped_column(String(50), default="read", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="project_users")
    user: Mapped["User"] = relationship("User", back_populates="project_access")

    def __repr__(self) -> str:
        return f"<ProjectUser(project_id={self.project_id}, user_id={self.user_id}, access={self.access_level})>"
