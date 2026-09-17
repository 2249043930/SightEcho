"""
SQLAlchemy 2.0 异步 ORM 声明基类
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

# 复用 db.session 中的 Base，保证 metadata 一致
from app.db.session import Base  # noqa: F401


class BaseModel(Base):
    """含主键/时间/逻辑删除的公共基类"""

    __abstract__ = True

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )
    is_deleted: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="逻辑删除 0 否 1 是"
    )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for col in self.__table__.columns:
            v = getattr(self, col.name)
            if isinstance(v, datetime):
                v = v.strftime("%Y-%m-%d %H:%M:%S")
            out[col.name] = v
        return out
