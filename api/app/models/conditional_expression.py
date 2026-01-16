"""Conditional expression models."""

from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.variable import Variable


class ConditionalExpression(Base, TimestampMixin):
    """Conditional expression model - boolean logic for node execution."""

    __tablename__ = "conditional_expressions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    condition_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="conditional_expressions")
    expression_variables: Mapped[List["ConditionalExpressionVariable"]] = relationship(
        "ConditionalExpressionVariable",
        back_populates="expression",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ConditionalExpression(id={self.id}, name={self.name})>"


class ConditionalExpressionVariable(Base, TimestampMixin):
    """Join table for expression-variable relationships."""

    __tablename__ = "conditional_expression_variables"

    id: Mapped[int] = mapped_column(primary_key=True)
    conditional_expression_id: Mapped[int] = mapped_column(
        ForeignKey("conditional_expressions.id", ondelete="CASCADE"),
        nullable=False,
    )
    variable_id: Mapped[int] = mapped_column(
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    expression: Mapped["ConditionalExpression"] = relationship(
        "ConditionalExpression",
        back_populates="expression_variables",
    )
    variable: Mapped["Variable"] = relationship("Variable")

    def __repr__(self) -> str:
        return f"<ConditionalExpressionVariable(expression_id={self.conditional_expression_id})>"
