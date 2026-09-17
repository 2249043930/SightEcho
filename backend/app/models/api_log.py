"""
接口调用日志表 log_api_call
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ApiCallLog(BaseModel):
    __tablename__ = "log_api_call"
    __table_args__ = (
        Index("idx_endpoint_time", "endpoint", "created_at"),
        Index("idx_user_time", "user_id", "created_at"),
        {"comment": "接口调用日志表"},
    )

    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="用户 ID")
    endpoint: Mapped[str] = mapped_column(String(128), nullable=False, comment="接口路径")
    method: Mapped[str] = mapped_column(String(8), nullable=False, comment="HTTP 方法")
    status_code: Mapped[int] = mapped_column(Integer, default=200, nullable=False, comment="状态码")
    cost_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="耗时 ms")
    ai_provider: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="AI 服务商")
    is_fallback: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="是否降级")
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="请求 ID")
    error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错误信息")
