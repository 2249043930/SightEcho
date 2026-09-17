"""
FastAPI 应用入口
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.router import api_router
from app.core.config import settings
from app.core.logger import setup_logger
from app.db.init_db import init_db
from app.middleware.cors import setup_cors
from app.middleware.gateway import GatewayMiddleware
from app.services.prompt_service import PromptService
from app.utils.exception_handler import register_exception_handlers
from app.utils.rate_limit import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    logger.info(f"SightEcho 启动 env={settings.APP_ENV} port={settings.APP_PORT}")
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"init_db 失败（生产应使用 alembic）: {e}")
    try:
        await PromptService.load_all()
    except Exception as e:
        logger.warning(f"Prompt 模板加载失败: {e}")
    # 预热 Redis
    try:
        r = await get_redis()
        await r.ping()
    except Exception as e:
        logger.warning(f"Redis 连接失败: {e}")
    yield
    try:
        await close_redis()
    except Exception:
        pass
    logger.info("SightEcho 关闭")


app = FastAPI(
    title="SightEcho API",
    description="视障场景智能感知系统后端 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 中间件
setup_cors(app)
app.add_middleware(GatewayMiddleware)

# 异常处理
register_exception_handlers(app)

# 路由
app.include_router(api_router)

# 静态资源（TTS 演示音频等）
import os

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", tags=["基础"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["基础"])
async def health():
    """健康检查：返回 db / redis / minio 状态（带超时）"""
    import asyncio as _aio
    status = {"status": "ok", "db": "unknown", "redis": "unknown", "minio": "unknown"}

    # DB
    try:
        from app.db.session import engine
        async def _db():
            async with engine.connect() as conn:
                from sqlalchemy import text
                await conn.execute(text("SELECT 1"))
        await _aio.wait_for(_db(), timeout=3)
        status["db"] = "ok"
    except Exception as e:
        status["db"] = f"error: {str(e)[:100]}"

    # Redis（用探测缓存避免阻塞）
    try:
        from app.utils.rate_limit import _is_redis_ok
        ok = await _aio.wait_for(_is_redis_ok(), timeout=2)
        status["redis"] = "ok" if ok else "in-memory-fallback"
    except Exception as e:
        status["redis"] = "in-memory-fallback"

    # MinIO
    try:
        def _minio():
            from app.utils.oss_util import _get_client
            client = _get_client()
            return client.bucket_exists(settings.MINIO_BUCKET)
        ok = await _aio.wait_for(_aio.to_thread(_minio), timeout=2)
        status["minio"] = "ok" if ok else "missing"
    except Exception as e:
        status["minio"] = f"error: {str(e)[:80]}"

    if any("error" in str(v) for v in status.values()):
        status["status"] = "degraded"
    return status


@app.get("/_debug/kv", tags=["基础"], include_in_schema=False)
async def debug_kv():
    """仅 DEBUG 模式可见：查看内存 KV 状态（用于本地测试）"""
    from app.utils.rate_limit import kv_peek
    return kv_peek


@app.get("/_debug/smtp", tags=["基础"], include_in_schema=False)
async def debug_smtp():
    """诊断 SMTP 配置（管理员调试用）"""
    from app.utils.email_util import diagnose_smtp
    return await diagnose_smtp()
