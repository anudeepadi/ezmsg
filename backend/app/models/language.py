"""Language model."""

from typing import Optional

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AvailableLanguage(Base, TimestampMixin):
    """Available languages for message localization."""

    __tablename__ = "available_languages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str] = mapped_column(String(10), nullable=False)
    code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<AvailableLanguage(id={self.id}, name={self.name}, code={self.code})>"
