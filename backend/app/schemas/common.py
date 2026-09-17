"""
通用响应/分页/标识
"""
from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiResp(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None


class PageData(BaseModel, Generic[T]):
    items: List[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class PageResp(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: PageData[T]


class FrontPage(BaseModel, Generic[T]):
    """前端契约：list/total/page/pageSize"""

    list: List[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    pageSize: int = 20


class IdResp(BaseModel):
    id: int
