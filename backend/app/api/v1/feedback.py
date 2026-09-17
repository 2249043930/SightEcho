"""
用户反馈接口
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.feedback import Feedback
from app.models.user import User
from app.utils.exception_handler import BizException
from app.utils.response import ok

router = APIRouter(prefix="/feedback", tags=["反馈"])


@router.post("", summary="提交反馈")
async def submit_feedback(
    content: str = Query(..., min_length=1, max_length=2000),
    contact: str | None = None,
    record_id: int | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fb = Feedback(
        user_id=user.id,
        content=content,
        contact=contact,
        record_id=record_id,
        status=0,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return ok({"id": str(fb.id)})


@router.get("/my", summary="我的反馈")
async def my_feedback(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base_q = select(Feedback).where(
        Feedback.user_id == user.id, Feedback.is_deleted == 0
    )
    cnt = (
        await db.execute(
            select(func.count(Feedback.id)).where(
                Feedback.user_id == user.id, Feedback.is_deleted == 0
            )
        )
    ).scalar_one()
    rows = (
        await db.execute(
            base_q.order_by(desc(Feedback.id)).offset((page - 1) * pageSize).limit(pageSize)
        )
    ).scalars().all()
    return ok(
        {
            "list": [
                {
                    "id": str(r.id),
                    "content": r.content,
                    "status": r.status,
                    "reply": r.reply,
                    "createdAt": r.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                for r in rows
            ],
            "total": int(cnt or 0),
            "page": page,
            "pageSize": pageSize,
        }
    )
