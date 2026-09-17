"""
降级容错：主接口超时/失败时切换备选；最终返回固定文本
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional

from loguru import logger

from app.core.config import settings


FallbackHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


async def run_with_fallback(
    primary: FallbackHandler,
    fallback: Optional[FallbackHandler] = None,
    timeout: Optional[float] = None,
    payload: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Any], bool]:
    """
    执行主调用，失败或超时则降级。
    返回: (结果, 是否降级)
    """
    payload = payload or {}
    timeout = timeout or settings.FALLBACK_TIMEOUT_SEC
    is_fallback = False

    try:
        result = await asyncio.wait_for(primary(payload), timeout=timeout)
        return result, False
    except Exception as primary_err:
        logger.warning(f"主接口失败: {primary_err}，尝试降级")
        if fallback is not None:
            try:
                result = await asyncio.wait_for(fallback(payload), timeout=timeout)
                is_fallback = True
                return result, True
            except Exception as fb_err:
                logger.error(f"降级接口也失败: {fb_err}")

    # 最终兜底：固定文本
    return {
        "text": "当前服务繁忙，请稍后重试",
        "confidence": 0.0,
        "is_fallback": True,
        "is_demo": settings.DEMO_MODE,
    }, True
