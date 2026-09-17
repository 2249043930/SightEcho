"""
统计数据聚合
"""
from __future__ import annotations

from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import func, select

from app.db.session import async_session_factory
from app.models.api_log import ApiCallLog
from app.models.recognition import RecognitionRecord
from app.models.user import User


async def overview_stats() -> dict:
    """管理端概览统计"""
    async with async_session_factory() as session:
        try:
            total_users = (
                await session.execute(
                    select(func.count(User.id)).where(User.is_deleted == 0)
                )
            ).scalar_one()
        except Exception:
            total_users = 0
        try:
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_active = (
                await session.execute(
                    select(func.count(func.distinct(ApiCallLog.user_id))).where(
                        ApiCallLog.created_at >= today_start,
                        ApiCallLog.user_id.isnot(None),
                    )
                )
            ).scalar_one()
        except Exception:
            today_active = 0
        try:
            today_calls = (
                await session.execute(
                    select(func.count(ApiCallLog.id)).where(
                        ApiCallLog.created_at >= today_start
                    )
                )
            ).scalar_one()
        except Exception:
            today_calls = 0
        try:
            success_calls = (
                await session.execute(
                    select(func.count(ApiCallLog.id)).where(
                        ApiCallLog.created_at >= today_start,
                        ApiCallLog.status_code < 400,
                    )
                )
            ).scalar_one()
            success_rate = round(success_calls / today_calls, 4) if today_calls else 1.0
        except Exception:
            success_rate = 1.0
    return {
        "totalUsers": int(total_users or 0),
        "todayActive": int(today_active or 0),
        "todayCalls": int(today_calls or 0),
        "successRate": float(success_rate),
    }


async def trend_calls(days: int = 7) -> list[dict]:
    """近 N 日调用量"""
    async with async_session_factory() as session:
        try:
            start = datetime.now() - timedelta(days=days)
            rows = (
                await session.execute(
                    select(
                        func.date(ApiCallLog.created_at).label("d"),
                        func.count(ApiCallLog.id).label("c"),
                    )
                    .where(ApiCallLog.created_at >= start)
                    .group_by("d")
                    .order_by("d")
                )
            ).all()
            return [{"date": str(r.d), "calls": int(r.c)} for r in rows]
        except Exception as e:
            logger.warning(f"trend_calls 查询失败: {e}")
            return []


async def distribution_by_type(days: int = 7) -> list[dict]:
    """业务类型分布"""
    async with async_session_factory() as session:
        try:
            start = datetime.now() - timedelta(days=days)
            rows = (
                await session.execute(
                    select(
                        RecognitionRecord.type,
                        func.count(RecognitionRecord.id),
                    )
                    .where(RecognitionRecord.created_at >= start)
                    .group_by(RecognitionRecord.type)
                )
            ).all()
            return [{"type": r[0], "value": int(r[1])} for r in rows]
        except Exception as e:
            logger.warning(f"distribution_by_type 失败: {e}")
            return []


async def realtime_monitor(window_min: int = 5) -> dict:
    """实时接口监控：QPS/成功率/平均耗时"""
    async with async_session_factory() as session:
        try:
            start = datetime.now() - timedelta(minutes=window_min)
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
            avg_latency = (
                await session.execute(
                    select(func.avg(ApiCallLog.cost_ms)).where(
                        ApiCallLog.created_at >= start
                    )
                )
            ).scalar_one() or 0
            endpoints_rows = (
                await session.execute(
                    select(
                        ApiCallLog.endpoint,
                        func.count(ApiCallLog.id).label("c"),
                        func.sum(
                            func.if_(ApiCallLog.status_code < 400, 1, 0)
                        ).label("s"),
                    )
                    .where(ApiCallLog.created_at >= start)
                    .group_by(ApiCallLog.endpoint)
                )
            ).all()
            qps = round(total / max(1, window_min * 60), 4)
            success_rate = round(success / total, 4) if total else 1.0
            endpoints = [
                {
                    "path": r.endpoint,
                    "qps": round(int(r.c or 0) / max(1, window_min * 60), 4),
                    "success": int(r.s or 0),
                    "fail": int((r.c or 0) - (r.s or 0)),
                }
                for r in endpoints_rows
            ]
            return {
                "qps": qps,
                "successRate": success_rate,
                "avgLatency": round(float(avg_latency), 1),
                "endpoints": endpoints,
            }
        except Exception as e:
            logger.warning(f"realtime_monitor 失败: {e}")
            return {"qps": 0, "successRate": 1.0, "avgLatency": 0, "endpoints": []}
