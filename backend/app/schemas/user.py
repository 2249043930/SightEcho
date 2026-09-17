"""
用户相关
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    role: Literal["user", "admin"] = "user"
    createdAt: Optional[str] = None


class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = Field(default=None, max_length=64)
    avatar: Optional[str] = Field(default=None, max_length=255)


class UserSettings(BaseModel):
    """前端契约字段名（camelCase）"""

    speed: float = 1.0
    volume: int = 80
    wakeEnabled: bool = True
    autoAnnounce: bool = True
    fontScale: Literal["small", "medium", "large"] = "medium"


class UserSettingsUpdate(BaseModel):
    speed: Optional[float] = None
    volume: Optional[int] = None
    wakeEnabled: Optional[bool] = None
    autoAnnounce: Optional[bool] = None
    fontScale: Optional[Literal["small", "medium", "large"]] = None
