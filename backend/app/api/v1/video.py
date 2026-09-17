"""
视频流解析接口
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from loguru import logger

from app.core.deps import get_current_user
from app.models.user import User
from app.services.agent_service import dispatch
from app.services.video_service import TASK_STATUS, get_task_status, parse_video_stream
from app.utils.exception_handler import BizException
from app.utils.response import ok

router = APIRouter(prefix="/video", tags=["视频流"])


@router.post("/parse", summary="提交视频流解析")
async def parse_video(
    src: str = Query(..., description="视频流地址 (rtsp/rtmp/https)"),
    scene: str = Query(default="travel", description="识别场景"),
    fps: int = Query(default=1, ge=1, le=10, description="每秒抽帧数"),
    user: User = Depends(get_current_user),
):
    if not src:
        raise BizException("src 不能为空")

    async def _runner(task_id: str) -> dict:
        await parse_video_stream(task_id=task_id, src=src, scene=scene, fps=fps)
        return TASK_STATUS.get(task_id, {})

    task_id = await dispatch(_runner)
    return ok({"taskId": task_id, "status": "pending"})


@router.get("/tasks/{task_id}", summary="查询任务状态")
async def task_status(task_id: str, user: User = Depends(get_current_user)):
    status = get_task_status(task_id)
    return ok(status)


@router.get("/stream/{task_id}", summary="SSE 实时获取结果")
async def stream_result(task_id: str, user: User = Depends(get_current_user)):
    from fastapi.responses import StreamingResponse

    async def event_gen():
        last = 0
        while True:
            data = get_task_status(task_id)
            frames = data.get("frames", [])
            for f in frames[last:]:
                yield f"data: {__import__('json').dumps(f, ensure_ascii=False)}\n\n"
                last += 1
            if data.get("status") in ("completed", "failed"):
                yield f"data: {__import__('json').dumps({'status': data['status']}, ensure_ascii=False)}\n\n"
                break
            import asyncio

            await asyncio.sleep(1)

    return StreamingResponse(event_gen(), media_type="text/event-stream")
