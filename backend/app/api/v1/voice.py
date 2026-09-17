"""
语音接口：TTS HTTP + ASR/TTS WebSocket
"""
from __future__ import annotations

import asyncio
import base64
import json
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, decode_token
from app.models.user import User
from app.services.asr_service import get_asr_adapter
from app.services.tts_service import get_tts_adapter
from app.utils.exception_handler import BizException
from app.utils.response import ok

router = APIRouter(prefix="/voice", tags=["语音"])


@router.post("/tts", summary="一次性 TTS 合成")
async def tts_once(
    text: str,
    voice: Optional[str] = "default",
    speed: Optional[float] = 1.0,
    volume: Optional[int] = 80,
    user: User = Depends(get_current_user),
):
    if not text or not text.strip():
        raise BizException("文本不能为空")
    if len(text) > 2000:
        raise BizException("文本过长")
    adapter = get_tts_adapter()
    result = await adapter.call(
        {
            "text": text,
            "voice": voice or "default",
            "rate": speed or 1.0,
            "volume": volume or 80,
        }
    )
    return ok(
        {
            "audioUrl": result.get("audio_url", ""),
            "duration": result.get("duration", 0),
        }
    )


# ---------- WebSocket 鉴权：前端先用 HTTP 申请短时 token，再连 WS ----------

@router.post("/asr/token", summary="申请 ASR 临时 token")
async def get_asr_token(user: User = Depends(get_current_user)):
    from datetime import timedelta

    token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=10),
        extra={"purpose": "asr"},
    )
    ws_base = settings.APP_HOST if settings.APP_HOST.startswith("ws") else "ws://localhost:8000"
    return ok({"token": token, "url": f"{ws_base}/api/v1/voice/asr"})


@router.post("/tts/token", summary="申请 TTS 临时 token")
async def get_tts_token(user: User = Depends(get_current_user)):
    from datetime import timedelta

    token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=10),
        extra={"purpose": "tts"},
    )
    ws_base = settings.APP_HOST if settings.APP_HOST.startswith("ws") else "ws://localhost:8000"
    return ok({"token": token, "url": f"{ws_base}/api/v1/voice/tts"})


# ---------- WebSocket 端点 ----------

async def _ws_auth(websocket: WebSocket) -> Optional[User]:
    """从 query.token / Authorization 头解析用户"""
    token = websocket.query_params.get("token")
    if not token:
        # 兼容 Sec-WebSocket-Protocol 头
        token = websocket.headers.get("authorization", "").replace("Bearer ", "")
    if not token:
        await websocket.close(code=4401)
        return None
    try:
        payload = decode_token(token)
    except Exception:
        await websocket.close(code=4401)
        return None
    from sqlalchemy import select
    from app.db.session import async_session_factory
    from app.models.user import User as UserModel

    async with async_session_factory() as session:
        row = (
            await session.execute(
                select(UserModel).where(
                    UserModel.id == int(payload.get("user_id", 0)),
                    UserModel.is_deleted == 0,
                )
            )
        ).scalar_one_or_none()
        if not row or row.status == 0:
            await websocket.close(code=4403)
            return None
        # detach
        from sqlalchemy.orm import Session
        session.expunge(row)
        return row


@router.websocket("/asr")
async def asr_ws(websocket: WebSocket):
    """ASR 流式识别：客户端发二进制音频，服务端返回 JSON 识别结果"""
    user = await _ws_auth(websocket)
    if not user:
        return
    await websocket.accept()
    adapter = get_asr_adapter()
    try:
        buf = b""
        while True:
            msg = await websocket.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            data = msg.get("bytes") or msg.get("text", "").encode()
            if not data:
                continue
            # 文本控制消息
            if isinstance(data, bytes) and data[:1] == b"\x00":
                cmd = data[1:].decode("utf-8", errors="ignore")
                if cmd == "end":
                    # 触发最终识别
                    res = await adapter.call(
                        {"audio_base64": base64.b64encode(buf).decode("ascii")}
                    )
                    await websocket.send_json(
                        {"type": "final", "text": res.get("text", "")}
                    )
                    buf = b""
                continue
            buf += data
            # 每 200ms 返回 partial
            if len(buf) >= 16000 * 2 * 1:  # 1s
                res = await adapter.call(
                    {"audio_base64": base64.b64encode(buf).decode("ascii")}
                )
                await websocket.send_json(
                    {"type": "partial", "text": res.get("text", "")}
                )
                buf = b""
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception(f"ASR WS 异常: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


@router.websocket("/tts")
async def tts_ws(websocket: WebSocket):
    """TTS 流式合成：客户端发 JSON {text,voice,rate,volume}，服务端返回音频分片"""
    user = await _ws_auth(websocket)
    if not user:
        return
    await websocket.accept()
    adapter = get_tts_adapter()
    try:
        while True:
            msg = await websocket.receive_json()
            text = (msg or {}).get("text", "")
            if not text:
                await websocket.send_json({"type": "error", "message": "empty text"})
                continue
            result = await adapter.call(
                {
                    "text": text,
                    "voice": msg.get("voice", "default"),
                    "rate": msg.get("rate", msg.get("speed", 1.0)),
                    "volume": msg.get("volume", 80),
                }
            )
            await websocket.send_json(
                {
                    "type": "audio",
                    "audioUrl": result.get("audio_url", ""),
                    "duration": result.get("duration", 0),
                }
            )
            await websocket.send_json({"type": "end"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception(f"TTS WS 异常: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
