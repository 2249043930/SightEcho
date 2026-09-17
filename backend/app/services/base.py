"""
Adapter 抽象基类
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional


class AIServiceAdapter(ABC):
    """所有 AI 服务适配器必须实现的统一接口"""

    name: str = "base"

    @abstractmethod
    async def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        """同步调用"""

    async def stream(self, payload: dict[str, Any]) -> AsyncIterator[Any]:
        """流式调用（默认走 call）"""
        yield await self.call(payload)

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
