"""
管理员后台相关
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------- Prompt ----------------
class PromptItem(BaseModel):
    id: str
    type: str
    name: str
    content: str
    version: int
    enabled: bool
    updatedAt: str
    variables: Optional[dict] = None
    scene: Optional[str] = None


class PromptCreate(BaseModel):
    type: str
    name: str
    content: str
    variables: Optional[dict] = None
    enabled: Optional[bool] = False


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[dict] = None
    enabled: Optional[bool] = None


# ---------------- Stats ----------------
class AdminStatsResp(BaseModel):
    totalUsers: int
    todayActive: int
    todayCalls: int
    successRate: float
    trend: List[dict]  # [{date, calls}]
    distribution: List[dict]  # [{type, value}]


# ---------------- Monitor ----------------
class MonitorEndpoint(BaseModel):
    path: str
    qps: float
    success: int
    fail: int


class MonitorResp(BaseModel):
    qps: float
    successRate: float
    avgLatency: float
    endpoints: List[MonitorEndpoint]


# ---------------- Feedback ----------------
class AdminFeedbackItem(BaseModel):
    id: str
    userId: Optional[str] = None
    recognitionId: Optional[str] = None
    rating: Optional[int] = None
    comment: Optional[str] = None
    status: Literal["pending", "resolved"]
    createdAt: str
    content: Optional[str] = None
    contact: Optional[str] = None


class AdminFeedbackListResp(BaseModel):
    list: List[AdminFeedbackItem]
    total: int


# ---------------- Admin User ----------------
class AdminUserItem(BaseModel):
    id: str
    email: str
    nickname: Optional[str] = None
    role: str
    status: int
    createdAt: str
    lastLoginAt: Optional[str] = None
