"""
Prompt 模板表 tpl_prompt
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, BigInteger, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class PromptTemplate(BaseModel):
    __tablename__ = "tpl_prompt"
    __table_args__ = (
        Index("idx_scene_active", "scene", "is_active", "version"),
        {"comment": "Prompt 模板表"},
    )

    scene: Mapped[str] = mapped_column(String(32), nullable=False, comment="场景")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="模板名称")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="模板内容")
    variables: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="变量定义")
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="版本号")
    is_active: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="0 停用 1 启用")
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="创建人")
