"""
TTS 语音合成服务
- 演示模式：返回占位音频 URL
- 真实模式：调用 Qwen3-TTS / Edge TTS
"""
from __future__ import annotations

import base64
import hashlib
import time
from typing import Any, AsyncIterator, Optional

import httpx
from loguru import logger

from app.core.config import settings
from app.services.base import AIServiceAdapter
from app.utils.oss_util import upload_bytes


class QwenTTSAdapter(AIServiceAdapter):
    name = "qwen-tts"

    async def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = payload.get("text", "")
        if not text:
            return {"audio_url": "", "duration": 0}
        if not settings.QWEN_API_KEY:
            return await self._demo(text)
        try:
            url = f"{settings.QWEN_API_BASE}/services/audio/tts/synthesis"
            headers = {
                "Authorization": f"Bearer {settings.QWEN_API_KEY}",
                "Content-Type": "application/json",
            }
            body = {
                "model": settings.QWEN_TTS_MODEL,
                "input": {"text": text},
                "parameters": {
                    "voice": payload.get("voice", "default"),
                    "speech_rate": payload.get("rate", 1.0),
                    "volume": payload.get("volume", 80),
                },
            }
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(url, json=body, headers=headers)
                r.raise_for_status()
                data = r.json()
                audio_b64 = (
                    data.get("output", {}).get("audio", {}).get("data", "")
                )
                if audio_b64:
                    raw = base64.b64decode(audio_b64)
                    url = await upload_bytes(raw, ".mp3", "audio/mpeg")
                    return {"audio_url": url or "", "duration": len(text) * 0.15}
        except Exception as e:
            logger.warning(f"Qwen TTS 调用失败: {e}")
        return await self._demo(text)

    async def stream(self, payload: dict[str, Any]) -> AsyncIterator[Any]:
        text = payload.get("text", "")
        # 简单切分：每 20 字一个分片
        step = 20
        for i in range(0, len(text), step):
            chunk = text[i : i + step]
            yield {"type": "audio", "text": chunk}
            await asyncio_sleep(0.05)  # noqa
        yield {"type": "end"}

    async def health_check(self) -> bool:
        return True

    async def _demo(self, text: str) -> dict[str, Any]:
        # 没有真音频：生成一个 base64 占位字符串，前端可识别
        h = hashlib.md5(text.encode("utf-8")).hexdigest()[:16]
        fake_url = f"/static/tts/demo/{int(time.time())}-{h}.mp3"
        return {"audio_url": fake_url, "duration": max(1, len(text) * 0.15)}


async def asyncio_sleep(_: float) -> None:
    import asyncio

    await asyncio.sleep(_)


def get_tts_adapter() -> AIServiceAdapter:
    return QwenTTSAdapter()
