"""Messaging node models."""

from typing import Optional, List, TYPE_CHECKING
import enum

from sqlalchemy import String, Text, Integer, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.message_template import MessageTemplate
    from app.models.timing_element import TimingElement
    from app.models.conditional_expression import ConditionalExpression
    from app.models.variable import Variable
    from app.models.scheduled_message import ScheduledMessage


class NodeTimingObjectType(str, enum.Enum):
    """Node timing object type enumeration."""
    TIMING_VARIABLE = "TIMING_VARIABLE"
    MESSAGING_NODE = "MESSAGING_NODE"
    MESSAGE_TEMPLATE = "MESSAGE_TEMPLATE"
    KEYWORD = "KEYWORD"


class MessagingNode(Base, TimestampMixin):
    """Messaging node model - workflow step."""

    __tablename__ = "messaging_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_terminal_node: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_entry_node: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exec_commands: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conditional_expression_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("conditional_expressions.id"),
        nullable=True,
    )
    template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("message_templates.id"),
        nullable=True,
    )
    timing_element_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("timing_elements.id"),
        nullable=True,
    )
    node_timing_object_type: Mapped[NodeTimingObjectType] = mapped_column(
        Enum(NodeTimingObjectType, name="node_timing_object_type", create_type=False),
        default=NodeTimingObjectType.MESSAGING_NODE,
        nullable=False,
    )
    timing_variable_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("variables.id"),
        nullable=True,
    )
    answered_template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("message_templates.id"),
        nullable=True,
    )
    node_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extra_data: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="nodes",
        foreign_keys=[project_id],
    )
    template: Mapped[Optional["MessageTemplate"]] = relationship(
        "MessageTemplate",
        foreign_keys=[template_id],
    )
    answered_template: Mapped[Optional["MessageTemplate"]] = relationship(
        "MessageTemplate",
        foreign_keys=[answered_template_id],
    )
    timing_element: Mapped[Optional["TimingElement"]] = relationship("TimingElement")
    conditional_expression: Mapped[Optional["ConditionalExpression"]] = relationship("ConditionalExpression")
    timing_variable: Mapped[Optional["Variable"]] = relationship("Variable")

    # Graph edges
    outgoing_edges: Mapped[List["MessagingNodeEdge"]] = relationship(
        "MessagingNodeEdge",
        back_populates="parent_node",
        foreign_keys="MessagingNodeEdge.parent_node_id",
        cascade="all, delete-orphan",
    )
    incoming_edges: Mapped[List["MessagingNodeEdge"]] = relationship(
        "MessagingNodeEdge",
        back_populates="child_node",
        foreign_keys="MessagingNodeEdge.child_node_id",
    )
    scheduled_messages: Mapped[List["ScheduledMessage"]] = relationship(
        "ScheduledMessage",
        back_populates="messaging_node",
    )

    def __repr__(self) -> str:
        return f"<MessagingNode(id={self.id}, name={self.name})>"


class MessagingNodeEdge(Base, TimestampMixin):
    """Edge connecting two messaging nodes in the workflow graph."""

    __tablename__ = "messaging_node_edges"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_node_id: Mapped[int] = mapped_column(
        ForeignKey("messaging_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    child_node_id: Mapped[int] = mapped_column(
        ForeignKey("messaging_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    condition_expression_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("conditional_expressions.id"),
        nullable=True,
    )
    edge_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    edge_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    parent_node: Mapped["MessagingNode"] = relationship(
        "MessagingNode",
        back_populates="outgoing_edges",
        foreign_keys=[parent_node_id],
    )
    child_node: Mapped["MessagingNode"] = relationship(
        "MessagingNode",
        back_populates="incoming_edges",
        foreign_keys=[child_node_id],
    )
    condition: Mapped[Optional["ConditionalExpression"]] = relationship("ConditionalExpression")

    def __repr__(self) -> str:
        return f"<MessagingNodeEdge(parent={self.parent_node_id}, child={self.child_node_id})>"
