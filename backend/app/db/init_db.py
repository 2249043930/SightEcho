"""
init_db: 启动时自动创建所有表（开发用），生产建议用 alembic
"""
from __future__ import annotations

from loguru import logger

from app.db.session import Base, engine


async def init_db() -> None:
    """导入全部模型后建表"""
    # 触发模型注册
    from app.models import user, recognition, feedback, prompt_template, api_log, verification  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表已就绪")
