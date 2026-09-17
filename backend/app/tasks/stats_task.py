"""
每日统计聚合（写入 log_api_call 的快照或外部 BI）
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import func, select

from app.db.session import async_session_factory
from app.models.api_log import ApiCallLog
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.stats_task.run_daily_stats")
def run_daily_stats() -> dict:
    async def _do() -> dict:
        start = datetime.utcnow() - timedelta(days=1)
        async with async_session_factory() as session:
            total = (
                await session.execute(
                    select(func.count(ApiCallLog.id)).where(
                        ApiCallLog.created_at >= start
                    )
                )
            ).scalar_one()
            success = (
                await session.execute(
                    select(func.count(ApiCallLog.id)).where(
                        ApiCallLog.created_at >= start,
                        ApiCallLog.status_code < 400,
                    )
                )
            ).scalar_one()
        return {"total": int(total or 0), "success": int(success or 0)}

    data = asyncio.run(_do())
    logger.info(f"daily stats: {data}")
    return data
