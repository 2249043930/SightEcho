"""
认证相关请求/响应
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SendCodeReq(BaseModel):
    email: str = Field(..., description="邮箱")


class SendCodeResp(BaseModel):
    expire: int = Field(..., description="验证码有效期（秒）")


class LoginReq(BaseModel):
    email: str = Field(..., description="邮箱")
    code: str = Field(..., min_length=6, max_length=6, description="6 位验证码")


class LoginResp(BaseModel):
    token: str
    expiresIn: int
    refreshToken: Optional[str] = None
