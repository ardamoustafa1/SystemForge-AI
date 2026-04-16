import enum
from sqlalchemy import String, ForeignKey, Enum as SQLEnum, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

class RoleEnum(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    viewer = "viewer"

class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    monthly_token_budget: Mapped[int] = mapped_column(Integer, nullable=False, default=200000)
    budget_alert_threshold_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    designs = relationship("Design", back_populates="workspace", cascade="all, delete-orphan")

class WorkspaceMember(Base, TimestampMixin):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[RoleEnum] = mapped_column(SQLEnum(RoleEnum, name="role_enum", native_enum=False), nullable=False, default=RoleEnum.viewer)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspaces")
