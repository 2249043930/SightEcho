"""
视频抽帧 + 推理（Celery 版）
生产环境启动 Celery worker:
    celery -A app.tasks.celery_app worker -l info -c 4
"""
from __future__ import annotations

import base64

from loguru import logger

from app.services.prompt_service import PromptService
from app.services.vl_service import get_vl_adapter, get_vl_demo
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.video_task.parse", bind=True, max_retries=3)
def parse_video_task(self, task_id: str, src: str, scene: str = "travel", fps: int = 1):
    """Celery 版视频抽帧推理（保留 import 点；具体抽帧建议用 ffmpeg-python）"""
    logger.info(f"video parse start: task_id={task_id} src={src[:60]}")
    import cv2

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        return {"status": "failed", "error": "无法打开视频流"}
    frames = []
    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1
            if frame_idx % max(1, fps) != 0:
                continue
            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            b64 = base64.b64encode(buf.tobytes()).decode("ascii")
            try:
                res = get_vl_demo(scene)  # 生产用 adapter
            except Exception as e:
                logger.warning(f"VL 失败: {e}")
                res = get_vl_demo(scene)
            frames.append({"idx": frame_idx, "text": res.get("text", "")})
    finally:
        cap.release()
    return {"status": "completed", "task_id": task_id, "frames": frames}
