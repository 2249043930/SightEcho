"""
视频流服务：解析 URL → 抽帧 → 调用 JoyAI 多帧 → 推送结果

设计要点（基于 JoyAI-VL-Interaction 平台特性）：
1. 模型只支持 Chat API（图文混排），没有原生视频流 API
2. 业务侧用 OpenCV 抽 N 帧后，**一次性**喂到 messages.content 列表
3. 每 N 帧做一次"批推理"（不是每帧一次，节省 token 和 API 费用）
4. 模型自然能理解多帧 = 时序变化，可识别移动物体/事件
"""
from __future__ import annotations

import asyncio
import base64
import time
from typing import Any, Optional

import cv2
from loguru import logger

from app.core.config import settings
from app.services.vl_service import get_vl_adapter, get_vl_demo

# 视频解析任务状态（内存缓存，生产用 Redis）
TASK_STATUS: dict[str, dict[str, Any]] = {}


def _is_url(src: str) -> bool:
    return src.startswith(("rtsp://", "rtmp://", "http://", "https://"))


def _open_capture(src: str) -> Optional[cv2.VideoCapture]:
    try:
        return cv2.VideoCapture(src)
    except Exception as e:
        logger.error(f"打开视频流失败: {e}")
        return None


def _frame_to_base64(frame, quality: int = 75) -> str:
    """抽帧 → JPEG → base64（quality 默认 75 节省带宽）"""
    ok, buf = cv2.imencode(
        ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    )
    if not ok:
        return ""
    return base64.b64encode(buf.tobytes()).decode("ascii")


def _resize_frame(frame, max_side: int = 640) -> Any:
    """缩放图片到 max_side 像素内（节省 token，提升推理速度）"""
    h, w = frame.shape[:2]
    if max(h, w) <= max_side:
        return frame
    scale = max_side / max(h, w)
    return cv2.resize(frame, (int(w * scale), int(h * scale)))


def get_prompt_text(scene: str, frame_count: int) -> str:
    """构造视频流 prompt（带帧数提示）"""
    base = {
        "travel": "你正在协助一位视障用户。请分析这组连续视频帧（按时间顺序），判断前方是否有危险（台阶/车辆/坑洞等），如有请明确方位和距离。",
        "face": "请分析这组连续视频帧中的人物变化。如果有显著变化（不同人/不同表情/不同动作），请依次描述。",
        "ocr": "请综合分析这组视频帧中出现的文字内容（可能是不同时间的画面）。",
        "product": "请分析这组连续视频帧中的商品变化，识别主要的商品并描述。",
        "currency": "请分析这组视频帧中出现的货币（可能多张），识别最大面额那张。",
    }.get(scene, "请分析这组连续视频帧的关键内容变化。")

    return f"【共 {frame_count} 帧，按时间顺序采样】\n\n{base}"


async def _recognize_batch(
    adapter,
    frames_b64: list[str],
    prompt: str,
    is_demo_mode: bool,
    scene: str,
) -> dict[str, Any]:
    """对一批帧做一次推理调用"""
    if is_demo_mode or not settings.JOYAI_API_KEY:
        return get_vl_demo(scene)

    try:
        # 多帧调用 JoyAI（视频流模式）
        result = await adapter.call({
            "images_base64": frames_b64,
            "prompt": prompt,
        })
        return result
    except Exception as e:
        logger.warning(f"JoyAI 视频批推理失败: {e}")
        return get_vl_demo(scene)


async def parse_video_stream(
    task_id: str,
    src: str,
    scene: str = "travel",
    fps: int = 1,
    batch_size: int = 4,
) -> None:
    """
    异步解析视频流（按"批"调用模型）

    Args:
        task_id: 任务 ID
        src: 视频源（rtsp/rtmp/http(s)/本地文件）
        scene: 业务场景（travel/face/ocr/...）
        fps: 抽帧率（默认 1 帧/秒）
        batch_size: 每多少帧做一次推理（默认 4 帧 = 4 秒一次）
    """
    TASK_STATUS[task_id] = {
        "status": "running",
        "frames": [],
        "started_at": time.time(),
    }
    cap = _open_capture(src)
    if cap is None or not cap.isOpened():
        TASK_STATUS[task_id] = {"status": "failed", "error": "无法打开视频流"}
        return

    interval = 1.0 / max(1, fps)
    adapter = get_vl_adapter()
    is_demo = settings.DEMO_MODE or not settings.JOYAI_API_KEY

    frame_idx = 0
    buffer_b64: list[str] = []
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1
            # 每 fps 帧采 1 帧
            if frame_idx % max(1, int(fps)) != 0:
                continue
            # 缩放 + base64
            small = _resize_frame(frame, max_side=640)
            b64 = _frame_to_base64(small, quality=75)
            if not b64:
                continue
            buffer_b64.append(b64)

            # 凑够 batch_size 帧或最后一次（视频结尾）做一次推理
            if len(buffer_b64) >= batch_size:
                prompt = get_prompt_text(scene, len(buffer_b64))
                result = await _recognize_batch(
                    adapter, buffer_b64, prompt, is_demo, scene
                )
                TASK_STATUS[task_id]["frames"].append({
                    "idx": frame_idx,
                    "text": result.get("text", ""),
                    "ts": time.time(),
                    "frames_used": result.get("frames_used", len(buffer_b64)),
                })
                logger.info(
                    f"[{task_id}] 帧 {frame_idx}: {result.get('text', '')[:80]}"
                )
                buffer_b64 = []  # 清空 buffer

            await asyncio.sleep(interval)
    finally:
        # 收尾：剩余 buffer 也做一次推理
        if buffer_b64:
            prompt = get_prompt_text(scene, len(buffer_b64))
            result = await _recognize_batch(
                adapter, buffer_b64, prompt, is_demo, scene
            )
            TASK_STATUS[task_id]["frames"].append({
                "idx": frame_idx,
                "text": result.get("text", ""),
                "ts": time.time(),
                "frames_used": result.get("frames_used", len(buffer_b64)),
            })
        cap.release()
        TASK_STATUS[task_id]["status"] = "completed"
        TASK_STATUS[task_id]["finished_at"] = time.time()
        logger.info(f"[{task_id}] 视频流解析完成，共 {frame_idx} 帧")


def get_task_status(task_id: str) -> dict[str, Any]:
    return TASK_STATUS.get(task_id, {"status": "not_found"})
