"""
识别业务相关
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

RecognitionType = Literal["travel", "ocr", "currency", "product", "face"]


class RecognitionResult(BaseModel):
    """前端契约：识别结果（camelCase）"""

    id: str
    type: RecognitionType
    title: str
    content: str
    audioUrl: Optional[str] = None
    thumbnail: Optional[str] = None
    createdAt: str
    # 扩展字段（与前端 useRecognition 兼容）
    resultJson: Optional[dict] = None
    confidence: Optional[float] = None
    isFallback: Optional[bool] = None


class HistoryListResp(BaseModel):
    """前端契约：list/total/page/pageSize"""

    list: List[RecognitionResult]
    total: int
    page: int
    pageSize: int


class HistoryQuery(BaseModel):
    page: int = 1
    pageSize: int = 20
    type: Optional[RecognitionType] = None
    keyword: Optional[str] = None


class FeedbackSubmitReq(BaseModel):
    """识别结果反馈"""

    id: str = Field(..., description="识别记录 ID")
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    comment: Optional[str] = Field(default=None, max_length=500)


class LiveRecognitionReq(BaseModel):
    """
    WebRTC 实时帧识别请求

    前端通过 getUserMedia 拿到视频流后，定期截帧转 base64，
    按"批"调用本接口（推荐 4 帧/批，对应 4 秒 1 帧）。
    后端会把多帧一次性喂给 JoyAI-VL-Interaction（视频流模式），
    返回结构化场景描述 + 危险关键词优先级。
    """

    scene: RecognitionType = Field(default="travel", description="业务场景")
    # 1~8 张 base64 编码的 jpeg 图片（不含 "data:image/jpeg;base64," 前缀也可）
    images: List[str] = Field(..., min_length=1, max_length=8, description="base64 帧图列表")
    extra: Optional[dict[str, Any]] = Field(default=None, description="Prompt 模板变量")
    # 是否把这一批结果落库为一条识别记录（默认 true，便于历史回放）
    saveRecord: Optional[bool] = Field(default=True, description="是否保存到 rec_record")

