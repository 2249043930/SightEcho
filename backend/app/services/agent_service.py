"""
Agent 服务：长任务委派（演示：直接同步执行，生产用 Celery）
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Awaitable, Callable

from loguru import logger

# 任务存储（演示用）
TASKS: dict[str, dict[str, Any]] = {}


async def dispatch(coro_factory: Callable[[str], Awaitable[Any]]) -> str:
    """派发一个后台任务，返回 task_id"""
    task_id = uuid.uuid4().hex
    TASKS[task_id] = {"status": "pending", "created_at": asyncio.get_event_loop().time()}

    async def _run() -> None:
        TASKS[task_id]["status"] = "running"
        try:
            result = await coro_factory(task_id)
            TASKS[task_id].update({"status": "success", "result": result})
        except Exception as e:
            logger.exception(f"任务 {task_id} 失败: {e}")
            TASKS[task_id].update({"status": "failed", "error": str(e)})

    asyncio.create_task(_run())
    return task_id


def get_task(task_id: str) -> dict[str, Any]:
    return TASKS.get(task_id, {"status": "not_found"})
