"""
用户表 sys_user
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "sys_user"
    __table_args__ = (
        Index("idx_email", "email"),
        Index("idx_role_status", "role", "status"),
        Index("idx_created_at", "created_at"),
        {"comment": "用户表"},
    )

    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="邮箱")
    nickname: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="昵称")
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="头像 URL")
    role: Mapped[str] = mapped_column(
        Enum("user", "admin", name="user_role"),
        default="user",
        nullable=False,
        comment="角色",
    )
    status: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="1 启用 0 禁用")
    settings_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="设置（语速/音量/唤醒）")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, comment="最后登录 IP")
