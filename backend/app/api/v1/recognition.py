"""
识别业务接口
- POST /recognition/{type}        上传图片执行识别
- GET  /recognition/history       历史列表
- GET  /recognition/history/{id}  记录详情
- DELETE /recognition/history/{id}
- POST /recognition/feedback      提交反馈
- POST /recognition/upload        通用上传（与 {type} 等价）
"""
from __future__ import annotations

import base64
import json
import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from loguru import logger
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.recognition import RecognitionRecord
from app.models.user import User
from app.schemas.recognition import FeedbackSubmitReq, HistoryListResp, LiveRecognitionReq, RecognitionResult
from app.services.fallback_service import run_with_fallback
from app.services.ocr_service import get_ocr_adapter
from app.services.prompt_service import PromptService
from app.services.vl_service import get_vl_adapter, get_vl_demo
from app.utils.exception_handler import BizException
from app.utils.oss_util import upload_file
from app.utils.response import ok

router = APIRouter(prefix="/recognition", tags=["识别"])

VALID_TYPES = {"travel", "ocr", "currency", "product", "face"}


def _to_camel(record: RecognitionRecord) -> dict:
    return {
        "id": str(record.id),
        "type": record.type,
        "title": record.title or _default_title(record.type),
        "content": record.result_text or "",
        "audioUrl": record.audio_url,
        "thumbnail": record.thumbnail,
        "createdAt": record.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resultJson": record.result_json,
        "confidence": float(record.confidence) if record.confidence is not None else None,
        "isFallback": bool(record.is_fallback),
    }


def _default_title(type_: str) -> str:
    return {
        "travel": "出行感知",
        "ocr": "文档阅读",
        "currency": "货币识别",
        "product": "商品识别",
        "face": "人脸描述",
    }.get(type_, "识别")


async def _recognize_image(
    type_: str,
    image_bytes: bytes,
    extra: Optional[dict] = None,
) -> tuple[str, dict, bool]:
    """执行识别核心逻辑，返回 (text, structured, is_fallback)"""
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    prompt = PromptService.get_active(type_)
    if extra:
        prompt = PromptService.render(prompt, extra)

    is_demo = settings.DEMO_MODE or not settings.QWEN_API_KEY
    is_fallback = False

    if type_ == "ocr":
        adapter = get_ocr_adapter()
        primary = lambda p: adapter.call({"image_base64": p["image_base64"], "prompt": prompt})  # noqa
    else:
        adapter = get_vl_adapter()
        primary = lambda p: adapter.call({"image_base64": p["image_base64"], "prompt": prompt})  # noqa

    if is_demo:
        result = get_vl_demo(type_)
    else:
        result, is_fallback = await run_with_fallback(
            primary=primary,
            fallback=(lambda p: get_vl_demo(type_)),
            payload={"image_base64": image_b64},
        )
    text = result.get("text", "")
    structured = {
        "objects": [],
        "is_fallback": bool(result.get("is_fallback") or is_fallback),
        "is_demo": bool(result.get("is_demo", False)),
        "confidence": result.get("confidence", 0.0),
    }
    priority = PromptService.detect_priority(text)
    if priority == "high":
        structured["priority"] = "high"
        text = PromptService.extract_high_priority(text)
    return text, structured, structured["is_fallback"]


def _strip_data_url(b64: str) -> str:
    """
    去除 base64 字符串中可能存在的前缀：
        "data:image/jpeg;base64,XXXXX"
        "data:image/png;base64,XXXXX"
    只保留真正的 base64 主体，避免重复加前缀。
    """
    s = b64.strip()
    if s.startswith("data:") and "," in s:
        return s.split(",", 1)[1]
    return s


async def _recognize_live_frames(
    scene: str,
    images_b64: list[str],
    extra: Optional[dict] = None,
) -> tuple[str, dict, bool]:
    """
    WebRTC 实时帧识别核心逻辑

    与 _recognize_image 的差异：
    - 接收 1+ 张 base64 图片（WebRTC 浏览器抓帧批量上传）
    - 始终用 "video" 模式调用 JoyAI-VL，强制走多帧时序建模
    - 仍然继承 run_with_fallback 的 5s 超时 + Demo 兜底
    """
    cleaned = [_strip_data_url(b) for b in images_b64 if b]
    if not cleaned:
        raise BizException("images 不能为空")

    prompt = PromptService.get_active(scene)
    if extra:
        prompt = PromptService.render(prompt, extra)

    is_fallback = False
    is_demo = settings.DEMO_MODE or not (
        settings.JOYAI_API_KEY
        or settings.QWEN_API_KEY
        or settings.OPENAI_API_KEY
    )

    if is_demo:
        # Demo 模式：从 demo 字典里取一条对应的预制文本，保证前端能看到效果
        result = get_vl_demo(scene)
        # 多帧 demo 场景做点轻微差异化：附上 N 帧提示
        sample_text = result.get("text", "")
        if len(cleaned) >= 2:
            sample_text = f"（已采样 {len(cleaned)} 帧，实时模式）{sample_text}"
        result = {**result, "text": sample_text, "frames_used": len(cleaned), "mode": "video"}
    else:
        # 真实调用：根据 AI_PROVIDER 选 adapter
        if scene == "ocr":
            # OCR 服务暂不支持多帧拼成单文档，降到第一帧 + prompt 提示
            adapter = get_ocr_adapter()
            primary = lambda p: adapter.call({  # noqa
                "image_base64": p["images_base64"][0],
                "prompt": p["prompt"],
            })
        else:
            adapter = get_vl_adapter()
            primary = lambda p: adapter.call({  # noqa
                "images_base64": p["images_base64"],
                "prompt": p["prompt"],
                "mode": "video",   # 强制覆盖：实时帧必须用视频流模式
            })
        result, is_fallback = await run_with_fallback(
            primary=primary,
            fallback=(lambda p: get_vl_demo(scene)),
            payload={"images_base64": cleaned, "prompt": prompt},
        )

    text = result.get("text", "")
    structured = {
        "objects": [],
        "is_fallback": bool(result.get("is_fallback") or is_fallback),
        "is_demo": bool(result.get("is_demo", False)),
        "confidence": result.get("confidence", 0.0),
        "frames_used": result.get("frames_used", len(cleaned)),
        "mode": result.get("mode", "video"),
    }
    priority = PromptService.detect_priority(text)
    if priority == "high":
        structured["priority"] = "high"
        text = PromptService.extract_high_priority(text)
    return text, structured, structured["is_fallback"]


@router.post("/live", summary="WebRTC 实时视频流识别（多帧 batch）")
async def recognize_live(
    payload: LiveRecognitionReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    给前端 WebRTC 摄像头实时抓帧调用：
    1. 接收 1~8 张 base64 帧图（按批批量上传）；
    2. 多帧"一次性"喂给 JoyAI-VL-Interaction（视频流模式）；
    3. 危险关键词自动置顶优先级；
    4. 默认保存到 rec_record，可在请求体中传 saveRecord=false 关闭。
    """
    t0 = time.perf_counter()
    text, structured, is_fallback = await _recognize_live_frames(
        payload.scene, payload.images, payload.extra
    )
    cost_ms = int((time.perf_counter() - t0) * 1000)

    record_id: Optional[str] = None
    if payload.saveRecord:
        try:
            # 把这一批的第一帧当作缩略图（base64 太长时仅保存元信息）
            first_frame = _strip_data_url(payload.images[0])
            thumb = None
            # 仅当帧够小时（避免数据库塞大 payload）写一笔标记
            if len(first_frame) <= 4096:
                thumb = f"data:image/jpeg;base64,{first_frame[:4000]}"
            record = RecognitionRecord(
                user_id=user.id,
                type=payload.scene,
                input_url=None,
                input_type="video_frame",
                result_text=text,
                result_json=structured,
                confidence=structured.get("confidence", 0.0),
                cost_ms=cost_ms,
                is_fallback=1 if is_fallback else 0,
                title=_default_title(payload.scene),
                thumbnail=thumb,
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)
            record_id = str(record.id)
        except Exception as e:
            logger.warning(f"保存 live 记录失败，不影响主流程: {e}")

    return ok({
        "id": record_id,
        "type": payload.scene,
        "title": _default_title(payload.scene),
        "content": text,
        "audioUrl": None,
        "thumbnail": None,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "resultJson": structured,
        "confidence": structured.get("confidence", 0.0),
        "isFallback": bool(is_fallback),
        "priority": structured.get("priority", "normal"),
        "framesUsed": structured.get("frames_used", len(payload.images)),
        "latencyMs": cost_ms,
    })


@router.post("/feedback", summary="提交反馈")
async def feedback(
    payload: FeedbackSubmitReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.feedback import Feedback

    rec = (
        await db.execute(
            select(RecognitionRecord).where(
                RecognitionRecord.id == int(payload.id),
                RecognitionRecord.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    fb = Feedback(
        user_id=user.id,
        record_id=int(payload.id) if payload.id.isdigit() else None,
        content=payload.comment or "",
        rating=payload.rating,
        status=0,
        extra={"recognition_id": payload.id},
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return ok({"id": str(fb.id)})


@router.post("/{type_}", summary="通用识别（图片上传）")
async def recognize(
    type_: str,
    request: Request,
    image: UploadFile = File(...),
    extra: Optional[str] = Form(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if type_ not in VALID_TYPES:
        raise BizException(f"不支持的识别类型: {type_}")
    if image.content_type and image.content_type not in settings.upload_allowed_mime_list:
        raise BizException("仅支持 jpg/png/webp 图片")
    data = await image.read()
    if len(data) > settings.UPLOAD_MAX_MB * 1024 * 1024:
        raise BizException(f"图片大小不能超过 {settings.UPLOAD_MAX_MB}MB")

    extra_dict: dict[str, Any] = {}
    if extra:
        try:
            extra_dict = json.loads(extra)
        except Exception:
            extra_dict = {}

    t0 = time.perf_counter()
    text, structured, is_fallback = await _recognize_image(type_, data, extra_dict)
    cost_ms = int((time.perf_counter() - t0) * 1000)

    # 上传原图到 OSS（可选）
    try:
        image.filename = image.filename or f"upload_{int(time.time())}.jpg"
        image_url = await upload_file(image)
    except Exception:
        image_url = None

    record = RecognitionRecord(
        user_id=user.id,
        type=type_,
        input_url=image_url,
        input_type="image",
        result_text=text,
        result_json=structured,
        confidence=structured.get("confidence", 0.0),
        cost_ms=cost_ms,
        is_fallback=1 if is_fallback else 0,
        title=_default_title(type_),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return ok(_to_camel(record))


@router.post("/upload", summary="通用上传（返回 URL）")
async def upload(
    image: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    if image.content_type and image.content_type not in settings.upload_allowed_mime_list:
        raise BizException("仅支持 jpg/png/webp 图片")
    data = await image.read()
    if len(data) > settings.UPLOAD_MAX_MB * 1024 * 1024:
        raise BizException("文件过大")
    url = await upload_file(image)
    return ok({"url": url})


@router.get("/history", summary="历史记录")
async def history(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    type: Optional[str] = Query(default=None, alias="type"),
    keyword: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if type and type not in VALID_TYPES:
        raise BizException("类型参数错误")
    stmt = select(RecognitionRecord).where(
        RecognitionRecord.user_id == user.id,
        RecognitionRecord.is_deleted == 0,
    )
    count_stmt = select(func.count(RecognitionRecord.id)).where(
        RecognitionRecord.user_id == user.id,
        RecognitionRecord.is_deleted == 0,
    )
    if type:
        stmt = stmt.where(RecognitionRecord.type == type)
        count_stmt = count_stmt.where(RecognitionRecord.type == type)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(RecognitionRecord.result_text.like(like))
        count_stmt = count_stmt.where(RecognitionRecord.result_text.like(like))

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(desc(RecognitionRecord.id)).offset((page - 1) * pageSize).limit(pageSize)
    rows = (await db.execute(stmt)).scalars().all()
    return ok(
        {
            "list": [_to_camel(r) for r in rows],
            "total": int(total or 0),
            "page": page,
            "pageSize": pageSize,
        }
    )


@router.get("/history/{rec_id}", summary="记录详情")
async def history_detail(
    rec_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (
        await db.execute(
            select(RecognitionRecord).where(
                RecognitionRecord.id == rec_id,
                RecognitionRecord.user_id == user.id,
                RecognitionRecord.is_deleted == 0,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise BizException("记录不存在")
    return ok(_to_camel(row))


@router.delete("/history/{rec_id}", summary="删除记录")
async def history_delete(
    rec_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (
        await db.execute(
            select(RecognitionRecord).where(
                RecognitionRecord.id == rec_id,
                RecognitionRecord.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise BizException("记录不存在")
    await db.execute(
        update(RecognitionRecord)
        .where(RecognitionRecord.id == rec_id)
        .values(is_deleted=1)
    )
    await db.commit()
    return ok(message="已删除")
