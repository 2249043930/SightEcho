"""
通用 OCR 适配器（演示：直接复用 VL 文案）
"""
from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.base import AIServiceAdapter
from app.services.vl_service import get_vl_demo


class BaiduOCRAdapter(AIServiceAdapter):
    name = "baidu-ocr"

    async def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        # 真实实现应调用百度 OCR API，这里直接复用 VL Demo
        if not settings.BAIDU_OCR_API_KEY:
            return get_vl_demo("ocr")
        # TODO: 接入百度 OCR
        return get_vl_demo("ocr")

    async def health_check(self) -> bool:
        return bool(settings.BAIDU_OCR_API_KEY) or True


def get_ocr_adapter() -> AIServiceAdapter:
    return BaiduOCRAdapter()
