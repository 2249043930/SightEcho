"""
用户接口
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserProfile, UserProfileUpdate, UserSettings, UserSettingsUpdate
from app.utils.response import ok
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

router = APIRouter(prefix="/user", tags=["用户"])

DEFAULT_SETTINGS = {
    "speed": 1.0,
    "volume": 80,
    "voice_wake_enabled": True,
    "auto_announce": True,
    "tts_voice": "default",
    "font_scale": "medium",
}


def _to_profile(user: User) -> dict:
    return UserProfile(
        id=str(user.id),
        email=user.email,
        nickname=user.nickname,
        avatar=user.avatar,
        role=user.role,
        createdAt=user.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if user.created_at else None,
    ).model_dump()


def _to_settings_camel(data: dict | None) -> dict:
    s = {**DEFAULT_SETTINGS, **(data or {})}
    return UserSettings(
        speed=float(s.get("speed", 1.0)),
        volume=int(s.get("volume", 80)),
        wakeEnabled=bool(s.get("voice_wake_enabled", True)),
        autoAnnounce=bool(s.get("auto_announce", True)),
        fontScale=s.get("font_scale", "medium"),
    ).model_dump()


@router.get("/profile", summary="获取用户信息")
async def get_profile(user: User = Depends(get_current_user)):
    return ok(_to_profile(user))


@router.put("/profile", summary="修改昵称/头像")
async def update_profile(
    payload: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    values = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if values:
        await db.execute(update(User).where(User.id == user.id).values(**values))
        await db.commit()
        await db.refresh(user)
    return ok(_to_profile(user))


@router.get("/settings", summary="获取用户设置")
async def get_settings(user: User = Depends(get_current_user)):
    return ok(_to_settings_camel(user.settings_json))


@router.put("/settings", summary="更新用户设置")
async def update_settings(
    payload: UserSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cur = {**(user.settings_json or {}), **DEFAULT_SETTINGS}
    update_data = payload.model_dump(exclude_unset=True)
    mapping = {
        "speed": "speed",
        "volume": "volume",
        "wakeEnabled": "voice_wake_enabled",
        "autoAnnounce": "auto_announce",
        "fontScale": "font_scale",
    }
    for k, v in update_data.items():
        if v is None:
            continue
        key = mapping.get(k, k)
        cur[key] = v
    await db.execute(update(User).where(User.id == user.id).values(settings_json=cur))
    await db.commit()
    await db.refresh(user)
    return ok(_to_settings_camel(user.settings_json))
