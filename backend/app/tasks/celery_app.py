"""
Celery 应用配置
"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "sightecho",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    include=["app.tasks.video_task", "app.tasks.cleanup_task", "app.tasks.stats_task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.TIMEZONE,
    enable_utc=False,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=4,
    broker_connection_retry_on_startup=True,
)

# 定时任务
celery_app.conf.beat_schedule = {
    # 每天凌晨清理 30 天前软删除的临时文件
    "cleanup-everyday": {
        "task": "app.tasks.cleanup_task.run_cleanup",
        "schedule": crontab(hour=3, minute=0),
    },
    # 每天 0 点聚合统计
    "stats-everyday": {
        "task": "app.tasks.stats_task.run_daily_stats",
        "schedule": crontab(hour=0, minute=5),
    },
}
