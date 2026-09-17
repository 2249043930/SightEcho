"""
管理员接口
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from loguru import logger
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_db
from app.models.feedback import Feedback
from app.models.prompt_template import PromptTemplate
from app.models.recognition import RecognitionRecord
from app.models.user import User
from app.schemas.admin import (
    AdminFeedbackItem,
    AdminFeedbackListResp,
    AdminStatsResp,
    MonitorEndpoint,
    MonitorResp,
    PromptCreate,
    PromptItem,
    PromptUpdate,
)
from app.services.prompt_service import PromptService
from app.services.stats_service import (
    distribution_by_type,
    overview_stats,
    realtime_monitor,
    trend_calls,
)
from app.utils.exception_handler import BizException
from app.utils.response import ok

router = APIRouter(prefix="/admin", tags=["管理端"])


# ---------------- Stats ----------------
@router.get("/stats", summary="概览统计（前端契约）")
async def get_stats(_: User = Depends(get_current_admin)):
    ov = await overview_stats()
    trend = await trend_calls(days=7)
    distribution = await distribution_by_type(days=7)
    return ok(
        AdminStatsResp(
            totalUsers=ov["totalUsers"],
            todayActive=ov["todayActive"],
            todayCalls=ov["todayCalls"],
            successRate=ov["successRate"],
            trend=trend,
            distribution=distribution,
        ).model_dump()
    )


# 兼容后端 prompt 文档命名
@router.get("/stats/overview", summary="概览统计（后端契约别名）")
async def stats_overview(_: User = Depends(get_current_admin)):
    return await get_stats(_)


@router.get("/stats/calls", summary="调用量按日")
async def stats_calls(days: int = 7, _: User = Depends(get_current_admin)):
    return ok({"items": await trend_calls(days=days)})


@router.get("/stats/users", summary="用户增长")
async def stats_users(days: int = 7, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    from datetime import timedelta
    start = datetime.utcnow() - timedelta(days=days)
    rows = (
        await db.execute(
            select(func.date(User.created_at), func.count(User.id))
            .where(User.created_at >= start)
            .group_by(func.date(User.created_at))
        )
    ).all()
    return ok({"items": [{"date": str(r[0]), "value": int(r[1])} for r in rows]})


# ---------------- Users ----------------
@router.get("/users", summary="用户列表")
async def list_users(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    base = select(User).where(User.is_deleted == 0)
    cnt = select(func.count(User.id)).where(User.is_deleted == 0)
    if keyword:
        like = f"%{keyword}%"
        base = base.where(User.email.like(like))
        cnt = cnt.where(User.email.like(like))
    total = (await db.execute(cnt)).scalar_one()
    rows = (
        await db.execute(base.order_by(desc(User.id)).offset((page - 1) * pageSize).limit(pageSize))
    ).scalars().all()
    return ok(
        {
            "list": [
                {
                    "id": str(u.id),
                    "email": u.email,
                    "nickname": u.nickname,
                    "role": u.role,
                    "status": u.status,
                    "createdAt": u.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "lastLoginAt": u.last_login_at.strftime("%Y-%m-%dT%H:%M:%SZ") if u.last_login_at else None,
                }
                for u in rows
            ],
            "total": int(total or 0),
            "page": page,
            "pageSize": pageSize,
        }
    )


@router.put("/users/{user_id}/status", summary="启/禁用户")
async def toggle_user_status(
    user_id: int,
    status: int = Query(..., ge=0, le=1),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    await db.execute(update(User).where(User.id == user_id).values(status=status))
    await db.commit()
    return ok(message="已更新")


# ---------------- Prompts ----------------
def _to_prompt_item(p: PromptTemplate) -> dict:
    return {
        "id": str(p.id),
        "type": p.scene,
        "scene": p.scene,
        "name": p.name,
        "content": p.content,
        "version": p.version,
        "enabled": bool(p.is_active),
        "variables": p.variables,
        "updatedAt": p.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if p.updated_at else "",
    }


@router.get("/prompts", summary="Prompt 列表")
async def list_prompts(
    scene: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    stmt = select(PromptTemplate).where(PromptTemplate.is_deleted == 0)
    if scene:
        stmt = stmt.where(PromptTemplate.scene == scene)
    rows = (await db.execute(stmt.order_by(desc(PromptTemplate.id)))).scalars().all()
    return ok([_to_prompt_item(p) for p in rows])


@router.post("/prompts", summary="创建 Prompt")
async def create_prompt(
    payload: PromptCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    p = PromptTemplate(
        scene=payload.type,
        name=payload.name,
        content=payload.content,
        variables=payload.variables,
        version=1,
        is_active=1 if payload.enabled else 0,
        created_by=admin.id,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    await PromptService.load_all()
    return ok(_to_prompt_item(p))


@router.put("/prompts/{pid}", summary="更新 Prompt")
async def update_prompt(
    pid: int,
    payload: PromptUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    p = (
        await db.execute(
            select(PromptTemplate).where(
                PromptTemplate.id == pid, PromptTemplate.is_deleted == 0
            )
        )
    ).scalar_one_or_none()
    if not p:
        raise BizException("Prompt 不存在")
    values = payload.model_dump(exclude_unset=True)
    if "content" in values and values["content"]:
        p.version = (p.version or 1) + 1
    for k, v in values.items():
        if k == "enabled":
            p.is_active = 1 if v else 0
        elif k == "type":
            p.scene = v
        elif v is not None:
            setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    await PromptService.load_all()
    return ok(_to_prompt_item(p))


@router.delete("/prompts/{pid}", summary="删除 Prompt")
async def delete_prompt(
    pid: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    await db.execute(
        update(PromptTemplate)
        .where(PromptTemplate.id == pid)
        .values(is_deleted=1, is_active=0)
    )
    await db.commit()
    await PromptService.load_all()
    return ok(message="已删除")


@router.post("/prompts/{pid}/activate", summary="启用指定版本")
async def activate_prompt(
    pid: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    p = (
        await db.execute(
            select(PromptTemplate).where(
                PromptTemplate.id == pid, PromptTemplate.is_deleted == 0
            )
        )
    ).scalar_one_or_none()
    if not p:
        raise BizException("Prompt 不存在")
    # 同场景其他全部停用
    await db.execute(
        update(PromptTemplate)
        .where(PromptTemplate.scene == p.scene)
        .values(is_active=0)
    )
    p.is_active = 1
    await db.commit()
    await PromptService.load_all()
    return ok(message="已启用")


# ---------------- Monitor ----------------
@router.get("/monitor", summary="实时监控（前端契约）")
async def monitor(_: User = Depends(get_current_admin)):
    data = await realtime_monitor(window_min=5)
    return ok(
        MonitorResp(
            qps=data["qps"],
            successRate=data["successRate"],
            avgLatency=data["avgLatency"],
            endpoints=[MonitorEndpoint(**e) for e in data["endpoints"]],
        ).model_dump()
    )


@router.get("/monitor/realtime", summary="实时监控（别名）")
async def monitor_realtime(_: User = Depends(get_current_admin)):
    return await monitor(_)


@router.get("/monitor/logs", summary="调用日志")
async def monitor_logs(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    from app.models.api_log import ApiCallLog

    total = (await db.execute(select(func.count(ApiCallLog.id)))).scalar_one()
    rows = (
        await db.execute(
            select(ApiCallLog).order_by(desc(ApiCallLog.id)).offset((page - 1) * pageSize).limit(pageSize)
        )
    ).scalars().all()
    return ok(
        {
            "list": [
                {
                    "id": r.id,
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "statusCode": r.status_code,
                    "costMs": r.cost_ms,
                    "isFallback": bool(r.is_fallback),
                    "errorMsg": r.error_msg,
                    "createdAt": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for r in rows
            ],
            "total": int(total or 0),
            "page": page,
            "pageSize": pageSize,
        }
    )


# ---------------- Admin Feedback ----------------
def _to_admin_fb(f: Feedback) -> dict:
    return {
        "id": str(f.id),
        "userId": str(f.user_id) if f.user_id else None,
        "recognitionId": (f.extra or {}).get("recognitionId") if f.extra else None,
        "rating": f.rating,
        "comment": f.content,
        "content": f.content,
        "contact": f.contact,
        "status": "resolved" if f.status == 1 else "pending",
        "createdAt": f.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@router.get("/feedback", summary="反馈列表")
async def admin_feedback(
    status: Optional[str] = Query(default=None, description="pending/resolved"),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    base = select(Feedback).where(Feedback.is_deleted == 0)
    cnt = select(func.count(Feedback.id)).where(Feedback.is_deleted == 0)
    if status == "pending":
        base = base.where(Feedback.status == 0)
        cnt = cnt.where(Feedback.status == 0)
    elif status == "resolved":
        base = base.where(Feedback.status == 1)
        cnt = cnt.where(Feedback.status == 1)
    total = (await db.execute(cnt)).scalar_one()
    rows = (
        await db.execute(base.order_by(desc(Feedback.id)).offset((page - 1) * pageSize).limit(pageSize))
    ).scalars().all()
    return ok({"list": [_to_admin_fb(r) for r in rows], "total": int(total or 0)})


@router.put("/feedback/{fid}", summary="回复反馈")
async def reply_feedback(
    fid: int,
    reply: str = Query(..., min_length=1, max_length=2000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    f = (
        await db.execute(
            select(Feedback).where(Feedback.id == fid, Feedback.is_deleted == 0)
        )
    ).scalar_one_or_none()
    if not f:
        raise BizException("反馈不存在")
    f.reply = reply
    f.status = 1
    f.replied_at = datetime.utcnow()
    await db.commit()
    return ok(message="已回复")


@router.put("/feedback/{fid}/resolve", summary="标记反馈为已处理（前端契约）")
async def resolve_feedback(
    fid: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    f = (
        await db.execute(
            select(Feedback).where(Feedback.id == fid, Feedback.is_deleted == 0)
        )
    ).scalar_one_or_none()
    if not f:
        raise BizException("反馈不存在")
    f.status = 1
    f.replied_at = datetime.utcnow()
    await db.commit()
    return ok(message="已处理")
