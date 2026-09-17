"""
基于 Redis 的滑动窗口限流
支持内存降级：未配置/不可用时自动使用本地字典
"""
from __future__ import annotations

import time
from typing import Optional

import redis.asyncio as redis_async

from app.core.config import settings

_redis_client: Optional[redis_async.Redis] = None
_redis_available: Optional[bool] = None  # None=未知, True=可用, False=不可用

# 内存降级存储
_inmem: dict[str, tuple[float, ...]] = {}  # key -> 时间戳列表（滑动窗口）


async def get_redis() -> redis_async.Redis:
    """全局异步 Redis 客户端（带自动探测）"""
    global _redis_client, _redis_available
    if _redis_client is None:
        _redis_client = redis_async.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
    return _redis_client


async def _is_redis_ok() -> bool:
    """探测 Redis 是否可用；首次会真实 ping，之后使用缓存结果"""
    global _redis_available
    if _redis_available is not None:
        return _redis_available
    try:
        r = await get_redis()
        await r.ping()
        _redis_available = True
    except Exception:
        _redis_available = False
    return _redis_available


async def close_redis() -> None:
    global _redis_client, _redis_available
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
    _redis_available = None


async def rate_limit_check(
    key: str,
    limit: int,
    window: int = 60,
) -> tuple[bool, int]:
    """
    滑动窗口限流（Redis 不可用时降级到内存）
    返回: (是否允许, 剩余次数)
    """
    if not await _is_redis_ok():
        return _inmem_sliding_window(key, limit, window)

    r = await get_redis()
    now = int(time.time() * 1000)
    window_ms = window * 1000
    member = f"{now}-{now}"

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_ms)
    pipe.zadd(key, {member: now})
    pipe.zcard(key)
    pipe.expire(key, window + 5)
    results = await pipe.execute()
    count = results[2]
    allowed = count <= limit
    remaining = max(0, limit - count)
    return allowed, remaining


async def rate_limit_ip_daily(key: str, limit: int) -> tuple[bool, int]:
    """按 IP+日维度计数（自然日）；Redis 不可用时降级到内存"""
    if not await _is_redis_ok():
        day = time.strftime("%Y%m%d")
        full_key = f"mem:{key}:{day}"
        items = _inmem.get(full_key, ())
        new = items + (time.time(),)
        _inmem[full_key] = new
        count = len(new)
        allowed = count <= limit
        return allowed, max(0, limit - count)

    r = await get_redis()
    day = time.strftime("%Y%m%d")
    full_key = f"{key}:{day}"
    count = await r.incr(full_key)
    if count == 1:
        await r.expire(full_key, 60 * 60 * 26)
    allowed = count <= limit
    remaining = max(0, limit - count)
    return allowed, remaining


async def rate_limit_interval(key: str, interval_sec: int) -> bool:
    """简单时间间隔限流；Redis 不可用时降级到内存"""
    if not await _is_redis_ok():
        items = _inmem.get(key, ())
        if items and (time.time() - items[-1]) < interval_sec:
            return False
        _inmem[key] = items + (time.time(),)
        return True
    r = await get_redis()
    exists = await r.exists(key)
    if exists:
        return False
    await r.set(key, "1", ex=interval_sec)
    return True


# ---------- 内存降级实现 ----------
def _inmem_sliding_window(key: str, limit: int, window: int) -> tuple[bool, int]:
    now = time.time()
    items = _inmem.get(key, ())
    items = tuple(t for t in items if now - t < window) + (now,)
    _inmem[key] = items
    count = len(items)
    return count <= limit, max(0, limit - count)


# ---------- 验证码 KV 存储（带内存降级）----------
_kv_store: dict[str, tuple[str, float]] = {}  # key -> (value, expire_at_ts)


async def kv_set(key: str, value: str, ex: int = 300) -> None:
    """设置 KV（验证码等），优先 Redis，失败降级到内存"""
    if await _is_redis_ok():
        try:
            r = await get_redis()
            await r.set(key, value, ex=ex)
            return
        except Exception:
            pass
    _kv_store[key] = (value, time.time() + ex)


async def kv_get(key: str) -> Optional[str]:
    """获取 KV"""
    if await _is_redis_ok():
        try:
            r = await get_redis()
            v = await r.get(key)
            if v is not None:
                return v
        except Exception:
            pass
    item = _kv_store.get(key)
    if not item:
        return None
    value, expire_at = item
    if time.time() > expire_at:
        _kv_store.pop(key, None)
        return None
    return value


async def kv_delete(key: str) -> int:
    """删除 KV"""
    deleted = 0
    if await _is_redis_ok():
        try:
            r = await get_redis()
            deleted = await r.delete(key)
            if deleted:
                return deleted
        except Exception:
            pass
    if _kv_store.pop(key, None) is not None:
        deleted += 1
    return deleted


def kv_reset_for_test() -> None:
    """测试用：清空所有内存 KV"""
    _kv_store.clear()
    _inmem.clear()


def kv_peek() -> dict[str, str]:
    """仅测试/调试用：导出当前内存 KV 视图（不含 Redis）"""
    return {k: v for k, (v, exp) in _kv_store.items()}
