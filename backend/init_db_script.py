"""初始化数据库 + 建表（首次启动用）"""
import asyncio
import aiomysql
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

from app.core.config import settings


async def ensure_database():
    """创建库（如不存在）"""
    conn = await aiomysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        charset="utf8mb4",
    )
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "CREATE DATABASE IF NOT EXISTS sightecho "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print(f"OK database 'sightecho' ensured on {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
            await cur.execute("SHOW DATABASES LIKE 'sightecho'")
            rows = await cur.fetchall()
            print(f"   验证：{rows}")
    finally:
        conn.close()


async def create_tables():
    """用 SQLAlchemy 建表"""
    from app.db.session import Base, engine
    # 触发模型注册
    from app.models import (  # noqa
        api_log, feedback, prompt_template, recognition, user, verification,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"OK tables created ({len(Base.metadata.tables)} 张)")
    for name in Base.metadata.tables:
        print(f"   - {name}")


async def main():
    print(f"=== SightEcho 数据库初始化 ===")
    print(f"  MySQL: {settings.MYSQL_USER}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    print()
    await ensure_database()
    print()
    await create_tables()
    print()
    print("=== 完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
