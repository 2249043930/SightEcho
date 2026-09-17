"""
API 网关：请求 ID 注入 + 访问日志
（鉴权与限流由 Depends/中间件按接口粒度处理）
"""
from __future__ import annotations

import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER = "X-Request-ID"


class GatewayMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # 1) 请求 ID
        rid = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex[:16]
        request.state.request_id = rid

        # 2) 计时
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception(f"[{rid}] {request.method} {request.url.path} 异常: {exc}")
            raise
        cost_ms = int((time.perf_counter() - start) * 1000)

        response.headers[REQUEST_ID_HEADER] = rid
        # 3) 访问日志
        logger.info(
            f"[{rid}] {request.method} {request.url.path} -> {response.status_code} {cost_ms}ms"
        )
        return response
