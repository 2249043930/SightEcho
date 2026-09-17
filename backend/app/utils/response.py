"""
统一响应格式
"""
from __future__ import annotations

import math
from typing import Any, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


def ok(data: Any = None, message: str = "ok") -> dict:
    """成功响应"""
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str, data: Any = None) -> dict:
    """失败响应（业务层用）"""
    return {"code": code, "message": message, "data": data}


class ApiResponse(BaseModel):
    """统一响应模型（用于 OpenAPI 文档展示）"""

    code: int = 0
    message: str = "ok"
    data: Any = None


class PageData(BaseModel):
    """分页数据"""

    items: List[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class PageResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: PageData


def page_ok(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """分页响应"""
    return ok(
        {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


def page_front_ok(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """前端契约：list 而非 items"""
    return ok(
        {
            "list": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        }
    )
