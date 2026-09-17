"""
邮箱验证码表 cfg_verification
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class VerificationCode(BaseModel):
    __tablename__ = "cfg_verification"
    __table_args__ = (
        Index("idx_email_purpose", "email", "purpose", "used"),
        Index("idx_expires", "expires_at"),
        {"comment": "邮箱验证码表"},
    )

    email: Mapped[str] = mapped_column(String(128), nullable=False, comment="邮箱")
    code: Mapped[str] = mapped_column(String(8), nullable=False, comment="验证码")
    purpose: Mapped[str] = mapped_column(String(32), default="login", nullable=False, comment="用途")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")
    used: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="是否已用")
    ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, comment="发送 IP")
