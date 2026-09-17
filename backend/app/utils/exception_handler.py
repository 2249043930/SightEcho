"""
全局异常处理：所有错误统一返回 {code, message, data}
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.utils.response import fail


class BizException(Exception):
    """业务异常：抛出即可在响应层转换为统一格式"""

    def __init__(self, message: str = "操作失败", code: int = 1, data: Any = None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)


def _error_payload(code: int, message: str, data: Any = None) -> dict:
    return fail(code=code, message=message, data=data)


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""

    @app.exception_handler(BizException)
    async def biz_exception_handler(_: Request, exc: BizException):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_error_payload(exc.code, exc.message, exc.data),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        # 401/403/404/422/429/500 等统一成业务响应
        code_map = {
            400: 4000,
            401: 4001,
            403: 4003,
            404: 4004,
            405: 4005,
            409: 4009,
            422: 4022,
            429: 4029,
        }
        biz_code = code_map.get(exc.status_code, 5000)
        msg = exc.detail if isinstance(exc.detail, str) else "请求失败"
        # 401 在这里要保留 HTTP 状态码以便前端拦截器识别
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers or {},
            content=_error_payload(biz_code, msg),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        # Pydantic 校验错误：取首条 message 给用户
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(x) for x in first.get("loc", []))
        msg = first.get("msg", "参数错误")
        message = f"{loc}: {msg}" if loc else msg
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_payload(4022, message, data=exc.errors()),
        )

    @app.exception_handler(Exception)
    async def all_exception_handler(request: Request, exc: Exception):
        logger.exception(f"未捕获异常: {exc} | path={request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload(5000, "服务异常，请稍后重试"),
        )
