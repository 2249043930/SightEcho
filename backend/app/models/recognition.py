"""
识别记录表 rec_record
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, BigInteger, DECIMAL, Enum, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RecognitionRecord(BaseModel):
    __tablename__ = "rec_record"
    __table_args__ = (
        Index("idx_user_type_time", "user_id", "type", "created_at"),
        Index("idx_type_time", "type", "created_at"),
        {"comment": "识别记录表"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="用户 ID")
    type: Mapped[str] = mapped_column(
        Enum("travel", "ocr", "currency", "product", "face", name="rec_type"),
        nullable=False,
        comment="业务类型",
    )
    input_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="输入 URL")
    input_type: Mapped[Optional[str]] = mapped_column(
        Enum("image", "video_frame", "video", name="rec_input_type"),
        default="image",
        nullable=True,
        comment="输入类型",
    )
    result_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="识别结果文本")
    result_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="结构化结果")
    confidence: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 4), nullable=True, comment="置信度 0-1")
    cost_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="耗时（毫秒）")
    is_fallback: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="是否降级")
    audio_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="TTS 音频 URL（可选）")
    thumbnail: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="缩略图 URL（可选）")
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="结果标题")
