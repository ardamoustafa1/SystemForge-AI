from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base, TimestampMixin


class Design(Base, TimestampMixin):
    __tablename__ = "designs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    project_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    discussion_conversation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    share_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    review_owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_decision_note: Mapped[str] = mapped_column(Text, nullable=False, default="")

    owner = relationship("User", back_populates="designs", foreign_keys=[owner_id])
    workspace = relationship("Workspace", back_populates="designs")
    input = relationship("DesignInput", back_populates="design", uselist=False, cascade="all, delete-orphan")
    output = relationship("DesignOutput", back_populates="design", uselist=False, cascade="all, delete-orphan")
    output_versions = relationship(
        "DesignOutputVersion",
        back_populates="design",
        cascade="all, delete-orphan",
    )
    comments = relationship("DesignComment", back_populates="design", cascade="all, delete-orphan")


class DesignInput(Base, TimestampMixin):
    __tablename__ = "design_inputs"

    id: Mapped[int] = mapped_column(primary_key=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("designs.id", ondelete="CASCADE"), nullable=False, unique=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    design = relationship("Design", back_populates="input")


class DesignOutput(Base, TimestampMixin):
    __tablename__ = "design_outputs"

    id: Mapped[int] = mapped_column(primary_key=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("designs.id", ondelete="CASCADE"), nullable=False, unique=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    markdown_export: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(80), nullable=False)
    generation_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    design = relationship("Design", back_populates="output")


class DesignOutputVersion(Base, TimestampMixin):
    """Historical snapshot before each regeneration (and optional future manual saves)."""

    __tablename__ = "design_output_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("designs.id", ondelete="CASCADE"), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    markdown_export: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(80), nullable=False)
    generation_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scale_stance: Mapped[str] = mapped_column(String(20), nullable=False, default="balanced")

    design = relationship("Design", back_populates="output_versions")


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="system", nullable=False)
    default_mode: Mapped[str] = mapped_column(String(20), default="product", nullable=False)

    user = relationship("User", back_populates="settings")


class DesignComment(Base, TimestampMixin):
    __tablename__ = "design_comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("designs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    design = relationship("Design", back_populates="comments")
    user = relationship("User")
