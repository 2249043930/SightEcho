"""
ASR 语音识别适配器（WebSocket 流式）
- 演示模式：直接返回固定结果
- 真实模式：可对接阿里 Qwen3-ASR / OpenAI Whisper
"""
from __future__ import annotations

import asyncio
import base64
import json
from typing import Any, AsyncIterator, Optional

import httpx
from loguru import logger

from app.core.config import settings
from app.services.base import AIServiceAdapter

DEMO_ASR_RESULTS = [
    "你好",
    "今天天气不错",
    "请帮我识别前方的物体",
    "打开设置",
    "拨打 120",
]


class QwenASRAdapter(AIServiceAdapter):
    name = "qwen-asr"

    async def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        audio_b64 = payload.get("audio_base64")
        if not audio_b64:
            return {"text": "", "is_final": True}
        if not settings.QWEN_API_KEY:
            return {"text": self._demo(), "is_final": True}
        # 真实实现：调用 DashScope 录音识别 API
        try:
            url = f"{settings.QWEN_API_BASE}/services/audio/asr/transcription"
            headers = {
                "Authorization": f"Bearer {settings.QWEN_API_KEY}",
                "Content-Type": "application/json",
            }
            body = {
                "model": settings.QWEN_ASR_MODEL,
                "input": {"file_urls": [f"data:audio/pcm;base64,{audio_b64}"]},
            }
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(url, json=body, headers=headers)
                r.raise_for_status()
                data = r.json()
                text = (
                    data.get("output", {})
                    .get("transcripts", [{}])[0]
                    .get("text", "")
                )
                return {"text": text, "is_final": True}
        except Exception as e:
            logger.warning(f"Qwen ASR 调用失败: {e}")
            return {"text": self._demo(), "is_final": True}

    async def stream(self, payload: dict[str, Any]) -> AsyncIterator[Any]:
        """流式：每个分片返回中间结果"""
        async for partial in _stream_simulate(payload.get("audio_base64", "")):
            yield partial
        # 最终结果
        yield {"type": "final", "text": self._demo()}

    async def health_check(self) -> bool:
        return True

    def _demo(self) -> str:
        import random

        return random.choice(DEMO_ASR_RESULTS)


async def _stream_simulate(audio_b64: str) -> AsyncIterator[dict]:
    """简单的流式模拟：每 200ms 返回 partial"""
    if not audio_b64:
        return
    try:
        raw = base64.b64decode(audio_b64)
    except Exception:
        return
    # 按 16kHz 16bit 单声道 1 秒 = 32KB 切分
    chunk = 32000
    partial = ""
    sample = DEMO_ASR_RESULTS[0]
    for i in range(0, min(len(raw), chunk * 3), chunk):
        partial = sample[: max(1, (i // chunk + 1) * 2)]
        yield {"type": "partial", "text": partial}
        await asyncio.sleep(0.05)


def get_asr_adapter() -> AIServiceAdapter:
    return QwenASRAdapter()
