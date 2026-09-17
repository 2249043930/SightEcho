"""
用户反馈表 fb_feedback
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Feedback(BaseModel):
    __tablename__ = "fb_feedback"
    __table_args__ = ({"comment": "用户反馈表"},)

    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="用户 ID")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="反馈内容")
    contact: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="联系方式")
    record_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="关联识别记录")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="0 未处理 1 已处理")
    reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="管理员回复")
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="回复时间")
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="评分 1-5")
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="扩展字段")
