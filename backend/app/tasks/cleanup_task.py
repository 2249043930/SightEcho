"""
临时资源清理：删除过期的软删除记录 / 临时图片
"""
from __future__ import annotations

from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import delete, select

from app.db.session import async_session_factory
from app.models.recognition import RecognitionRecord
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.cleanup_task.run_cleanup")
def run_cleanup(days: int = 30) -> dict:
    """清理 30 天前已软删除的识别记录"""
    import asyncio

    async def _do():
        cutoff = datetime.utcnow() - timedelta(days=days)
        async with async_session_factory() as session:
            stmt = select(RecognitionRecord.id).where(
                RecognitionRecord.is_deleted == 1,
                RecognitionRecord.updated_at < cutoff,
            )
            ids = (await session.execute(stmt)).scalars().all()
            if not ids:
                return 0
            await session.execute(
                delete(RecognitionRecord).where(RecognitionRecord.id.in_(ids))
            )
            await session.commit()
            return len(ids)

    deleted = asyncio.run(_do())
    logger.info(f"cleanup 清理 {deleted} 条历史识别记录")
    return {"deleted": deleted}
