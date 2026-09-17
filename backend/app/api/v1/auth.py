"""
认证接口：邮箱验证码 + 登录
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from loguru import logger
from sqlalchemy import select, update

from app.core.config import settings
from app.core.deps import get_client_ip, get_current_user
from app.core.security import create_access_token
from app.models.user import User
from app.models.verification import VerificationCode
from app.schemas.auth import LoginReq, LoginResp, SendCodeReq
from app.utils.email_util import send_code_email
from app.utils.exception_handler import BizException
from app.utils.rate_limit import (
    kv_delete,
    kv_get,
    kv_set,
    rate_limit_interval,
    rate_limit_ip_daily,
)
from app.utils.response import ok
from app.utils.validators import is_valid_code, is_valid_email

router = APIRouter(prefix="/auth", tags=["认证"])

CODE_TTL_SEC = 300  # 5 分钟


@router.post("/email-code", summary="发送邮箱验证码")
async def send_email_code(req: SendCodeReq, request: Request):
    email = (req.email or "").strip().lower()
    if not is_valid_email(email):
        raise BizException("邮箱格式不正确")

    ip = get_client_ip(request)
    # 限流：单邮箱 60s 一次
    ok_interval = await rate_limit_interval(
        f"verify:interval:{email}", settings.EMAIL_CODE_INTERVAL_SEC
    )
    if not ok_interval:
        raise BizException(f"发送过于频繁，请 {settings.EMAIL_CODE_INTERVAL_SEC} 秒后重试")

    # 限流：单 IP 单日 10 次
    allowed, _ = await rate_limit_ip_daily(
        "verify:ip", settings.EMAIL_CODE_DAILY_IP_LIMIT
    )
    if not allowed:
        raise BizException("今日验证码发送次数已达上限")

    code = f"{random.randint(0, 999999):06d}"
    await kv_set(f"verify:login:{email}", code, ex=CODE_TTL_SEC)

    # 发送邮件
    sent = await send_code_email(email, code, expire_sec=CODE_TTL_SEC)
    if not sent:
        # DEBUG 模式：邮件发送失败时仍然在响应里返回验证码（仅 dev 方便联调）
        from app.core.config import settings as _s
        if _s.DEBUG:
            logger.warning(
                f"[DEV-FALLBACK] 邮件发送失败，但验证码已返回前端: {code}"
            )
            return ok({
                "expire": CODE_TTL_SEC,
                "code": code,
                "devOnly": True,  # 标记为 dev-only 字段
                "message": "邮件发送失败（dev 模式直接返回验证码）",
            })
        raise BizException("验证码发送失败，请稍后重试")

    # 写入审计表
    from app.db.session import async_session_factory as _factory

    async with _factory() as session:
        vc = VerificationCode(
            email=email,
            code=code,
            purpose="login",
            expires_at=datetime.utcnow() + timedelta(seconds=CODE_TTL_SEC),
            used=0,
            ip=ip,
        )
        session.add(vc)
        await session.commit()

    logger.info(f"验证码已发送 email={email[:3]}*** ip={ip}")
    return ok({"expire": CODE_TTL_SEC})


@router.post("/login", summary="邮箱+验证码登录")
async def login_by_code(req: LoginReq, request: Request):
    email = (req.email or "").strip().lower()
    if not is_valid_email(email):
        raise BizException("邮箱格式不正确")
    if not is_valid_code(req.code):
        raise BizException("验证码格式不正确")

    key = f"verify:login:{email}"
    cached = await kv_get(key)
    if not cached:
        raise BizException("验证码已过期或不存在")
    if cached != req.code:
        raise BizException("验证码错误")
    # 立即消费
    await kv_delete(key)

    # 用户不存在则自动注册
    from app.db.session import async_session_factory as _factory

    ip = get_client_ip(request)
    async with _factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email=email,
                nickname=email.split("@")[0][:32],
                role="user",
                status=1,
                last_login_at=datetime.utcnow(),
                last_login_ip=ip,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # 更新最后登录
            await session.execute(
                update(User)
                .where(User.id == user.id)
                .values(last_login_at=datetime.utcnow(), last_login_ip=ip)
            )
            await session.commit()

        token = create_access_token(user_id=user.id, role=user.role)
        # 标记验证码已用
        await session.execute(
            update(VerificationCode)
            .where(
                VerificationCode.email == email,
                VerificationCode.purpose == "login",
                VerificationCode.used == 0,
            )
            .values(used=1)
        )
        await session.commit()

    expires_in = settings.JWT_EXPIRE_DAYS * 24 * 3600
    return ok(
        LoginResp(
            token=token,
            expiresIn=expires_in,
            refreshToken=None,
        ).model_dump()
    )


@router.post("/logout", summary="登出")
async def logout(user: User = Depends(get_current_user)):
    # 演示：JWT 无黑名单，前端清除本地 token 即可
    return ok(message="已登出")


@router.get("/me", summary="获取当前用户")
async def get_me(user: User = Depends(get_current_user)):
    return ok(
        {
            "id": str(user.id),
            "email": user.email,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "role": user.role,
            "createdAt": user.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if user.created_at else None,
        }
    )
