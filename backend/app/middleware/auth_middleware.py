"""
鉴权中间件：占位（鉴权逻辑由 Depends(get_current_user) 处理）
这里保留扩展位（如 IP 黑名单、设备指纹等）
"""
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # 透传；具体鉴权由 Depends(get_current_user) 控制
        return await call_next(request)
