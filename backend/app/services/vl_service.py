"""
多模态视觉大模型（VL）适配器
支持 Qwen-VL / GPT-4V / JoyAI-VL-Interaction 三种实现，未配置 Key 时使用 Demo 数据
"""
from __future__ import annotations

import base64
import json
import time
from typing import Any, Optional

import httpx
from loguru import logger

from app.core.config import settings
from app.services.base import AIServiceAdapter

DEMO_RESULTS: dict[str, list[str]] = {
    "travel": [
        "前方 3 米有台阶，请小心通过。",
        "左侧约 2 米有一辆静止的白色轿车，无通行风险。",
        "前方 5 米有红色交通信号灯，当前为红灯。",
        "当前路径畅通，地面平整，可继续直行。",
        "前方 2 米有施工围挡，建议绕行。",
    ],
    "ocr": [
        "《用户协议》\n\n一、服务说明\n本服务为视障人士提供图像识别与语音辅助。\n\n二、隐私保护\n我们严格保护用户隐私，识别图像不会用于模型训练。\n\n三、联系我们\n邮箱：support@sightecho.cn",
        "今日菜单\n早餐：豆浆、油条、茶叶蛋\n午餐：宫保鸡丁盖饭、番茄牛腩面\n晚餐：清炒时蔬、米饭、玉米排骨汤",
    ],
    "currency": [
        "面额：100 元（人民币）；置信度：高；备注：红色主色调，纸币正面有毛泽东头像。",
        "面额：20 美元（USD）；置信度：高；备注：绿色背景，正面为杰克逊肖像。",
        "面额：50 元（人民币）；置信度：中；备注：绿色主色调，建议核对冠字号码。",
    ],
    "product": [
        "名称：农夫山泉 550ml 矿泉水；类别：饮料；特征：红色瓶身，透明液体。",
        "名称：可口可乐 330ml 罐装；类别：饮料；特征：红色铝罐，白色飘带 logo。",
        "名称：三只松鼠每日坚果；类别：零食；特征：黄色牛皮纸包装，750g 装。",
    ],
    "face": [
        "性别：男；年龄段：约 30 岁；表情：微笑；配饰：黑框眼镜；场景：办公室。",
        "性别：女；年龄段：约 25 岁；表情：平静；配饰：长发，无明显饰品；场景：户外公园。",
        "性别：男；年龄段：约 50 岁；表情：严肃；配饰：白色衬衫；场景：会议室。",
    ],
}


class QwenVLAdapter(AIServiceAdapter):
    name = "qwen-vl"

    async def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not settings.QWEN_API_KEY:
            raise RuntimeError("QWEN_API_KEY 未配置")
        image_b64 = payload.get("image_base64")
        prompt = payload.get("prompt", "")
        if not image_b64:
            raise ValueError("缺少 image_base64")
        url = f"{settings.QWEN_API_BASE}/services/aigc/multimodal-generation/generation"
        headers = {
            "Authorization": f"Bearer {settings.QWEN_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": settings.QWEN_VL_MODEL,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": f"data:image/jpeg;base64,{image_b64}"},
                            {"text": prompt},
                        ],
                    }
                ]
            },
            "parameters": {"result_format": "message"},
        }
        async with httpx.AsyncClient(timeout=settings.FALLBACK_TIMEOUT_SEC) as client:
            r = await client.post(url, json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
            text = (
                data.get("output", {})
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", [{}])[0]
                .get("text", "")
            )
            return {"text": text, "confidence": 0.9}

    async def health_check(self) -> bool:
        return bool(settings.QWEN_API_KEY)


class GPT4VAdapter(AIServiceAdapter):
    name = "gpt-4v"

    async def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY 未配置")
        image_b64 = payload.get("image_base64")
        prompt = payload.get("prompt", "")
        if not image_b64:
            raise ValueError("缺少 image_base64")
        url = f"{settings.OPENAI_API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }
        async with httpx.AsyncClient(timeout=settings.FALLBACK_TIMEOUT_SEC) as client:
            r = await client.post(url, json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"]
            return {"text": text, "confidence": 0.9}

    async def health_check(self) -> bool:
        return bool(settings.OPENAI_API_KEY)


class JoyAIVLAdapter(AIServiceAdapter):
    """
    京东 JoyAI-VL-Interaction 多模态模型适配器
    - 基于 OpenAI 兼容协议（/v1/chat/completions）
    - 支持两种模式：image（单图）和 video（视频流抽帧）
    - 模型专为「实时视频理解」设计，对出行/监控/直播场景优化
    """

    name = "joyai-vl"

    async def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not settings.JOYAI_API_KEY:
            raise RuntimeError("JOYAI_API_KEY 未配置")

        # 兼容两种入参格式：单图 / 多帧（视频）
        images_b64: list[str] = payload.get("images_base64") or []
        single_b64: str = payload.get("image_base64") or ""
        if not images_b64 and single_b64:
            images_b64 = [single_b64]
        if not images_b64:
            raise ValueError("缺少 image_base64 / images_base64")

        prompt: str = payload.get("prompt", "")
        # 允许调用方在 payload 中临时覆盖运行模式（默认仍走 settings.JOYAI_VL_MODE）
        # - "image": 单图理解（仅取第一帧）
        # - "video": 视频流理解（多帧时序建模，适合实时出行/人脸）
        mode_override: Optional[str] = payload.get("mode")
        mode: str = (mode_override or settings.JOYAI_VL_MODE).lower()
        if mode not in ("image", "video"):
            mode = "image"

        # 构造 OpenAI 兼容的 messages.content（图文混排）
        content: list[dict[str, Any]] = []
        if mode == "video":
            # 视频模式：先放所有帧，再放 prompt
            for i, img_b64 in enumerate(images_b64[: settings.JOYAI_VIDEO_MAX_FRAMES]):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                })
            # 视频模式补帧序号提示
            video_hint = f"（共 {len(images_b64[:settings.JOYAI_VIDEO_MAX_FRAMES])} 帧采样，每秒 {settings.JOYAI_VIDEO_FPS} 帧，按时间顺序）\n\n"
            content.append({"type": "text", "text": video_hint + prompt})
        else:
            # 图片模式：单图 + prompt
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{images_b64[0]}"},
            })
            content.append({"type": "text", "text": prompt})

        url = f"{settings.JOYAI_API_BASE.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.JOYAI_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": settings.JOYAI_VL_MODEL,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.3,        # 低温度 → 更确定的结果（适合视障场景）
            "max_tokens": 500,
            "top_p": 0.9,
        }
        timeout = max(settings.FALLBACK_TIMEOUT_SEC, 10.0)  # 视频模式至少 10s
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(url, json=body, headers=headers)
                r.raise_for_status()
                data = r.json()
                # OpenAI 兼容响应：choices[0].message.content
                text = data["choices"][0]["message"]["content"]
                return {
                    "text": text.strip() if isinstance(text, str) else str(text),
                    "confidence": 0.9,
                    "provider": "joyai",
                    "mode": mode,
                    "frames_used": len(images_b64[: settings.JOYAI_VIDEO_MAX_FRAMES]),
                }
        except httpx.HTTPStatusError as e:
            err_body = e.response.text[:300] if e.response else str(e)
            logger.error(f"JoyAI-VL 调用失败 [{e.response.status_code}]: {err_body}")
            raise
        except Exception as e:
            logger.error(f"JoyAI-VL 调用异常: {type(e).__name__}: {e}")
            raise

    async def health_check(self) -> bool:
        return bool(settings.JOYAI_API_KEY)


def get_vl_adapter() -> AIServiceAdapter:
    """根据 AI_PROVIDER 选择 VL 适配器"""
    provider = (settings.AI_PROVIDER or "qwen").lower()
    if provider == "openai":
        return GPT4VAdapter()
    if provider == "joyai":
        return JoyAIVLAdapter()
    return QwenVLAdapter()


def get_vl_demo(scene: str) -> dict[str, Any]:
    """无 API Key 时返回演示结果"""
    import random

    texts = DEMO_RESULTS.get(scene, DEMO_RESULTS["travel"])
    return {
        "text": random.choice(texts),
        "confidence": 0.85,
        "is_demo": True,
    }
