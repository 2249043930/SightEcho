"""
邮件发送：QQ/网易/通用 SMTP
- 邮件 HTML 模板位于前端：frontend/src/assets/email/verification.html
- 与前端新拟物派风格完全一致（颜色、阴影、字体）
- 失败时返回 False 并打印详细错误，不抛异常
- QQ 邮箱需在 设置→账户→SMTP 服务 开启 + 生成 16 位授权码
"""
from __future__ import annotations

import asyncio
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, Tuple

from loguru import logger

from app.core.config import settings

# 邮件模板路径（前端 assets 目录）
_TEMPLATE_PATHS = [
    # 当前工作目录向上找（app/utils/ → app/ → backend/ → project/ → frontend/...）
    Path(__file__).resolve().parents[3] / "frontend" / "src" / "assets" / "email" / "verification.html",
    # 兼容 Docker 部署：/app/frontend/src/...
    Path("/app/frontend/src/assets/email/verification.html"),
    # 兜底：使用后端自带模板（如果前端模板不存在）
    Path(__file__).resolve().parent / "email_templates" / "verification.html",
]


def _load_template() -> Optional[str]:
    """从文件系统加载邮件 HTML 模板"""
    for p in _TEMPLATE_PATHS:
        if p.exists():
            try:
                return p.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"读取邮件模板失败: {p}: {e}")
    return None


def _fallback_html(code: str, expire_sec: int) -> str:
    """内置兜底模板（前端模板加载失败时使用）"""
    return f"""
    <div style="font-family: -apple-system, 'PingFang SC', sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; background: #e0e5ec; border-radius: 12px;">
        <h2 style="color: #2c2c34;">SightEcho 昭视智伴</h2>
        <p style="color: #5b6470;">您的验证码：<strong style="font-size: 24px; color: #6d5dfc;">{code}</strong></p>
        <p style="color: #5b6470; font-size: 14px;">{expire_sec // 60} 分钟内有效</p>
    </div>
    """


def _try_login(host: str, port: int, user: str, pwd: str, use_ssl: bool) -> Tuple[bool, str]:
    """尝试一种 SMTP 登录方式"""
    try:
        if use_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            s = smtplib.SMTP_SSL(host, port, timeout=15, context=ctx)
        else:
            s = smtplib.SMTP(host, port, timeout=15)
            if port == 587:
                s.starttls()
        s.ehlo("localhost")
        s.login(user, pwd)
        s.quit()
        return True, "OK"
    except smtplib.SMTPAuthenticationError as e:
        err = e.smtp_error.decode(errors="ignore") if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        return False, f"认证失败 {e.smtp_code}: {err}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


async def diagnose_smtp() -> dict:
    """诊断 SMTP 配置；返回每种尝试的结果"""
    user = settings.EMAIL_USER
    pwd = settings.EMAIL_PASSWORD
    host = settings.EMAIL_SMTP_HOST

    if not user or not pwd:
        return {"configured": False, "message": "EMAIL_USER / EMAIL_PASSWORD 未配置"}

    results = []
    attempts = [
        (host, 465, True, "SMTP_SSL :465"),
        (host, 587, False, "STARTTLS :587"),
        (host, 25, False, "明文 :25"),
    ]
    for h, p, ssl_, desc in attempts:
        ok, msg = await asyncio.to_thread(_try_login, h, p, user, pwd, ssl_)
        results.append({"method": desc, "host": h, "port": p, "ok": ok, "msg": msg})
        if ok:
            break

    return {
        "configured": True,
        "user": user,
        "host": host,
        "attempts": results,
    }


async def send_code_email(to_email: str, code: str, expire_sec: int = 300) -> bool:
    """发送验证码邮件，失败返回 False"""
    # DEBUG 模式：无论成功失败都打印验证码到日志
    from app.core.config import settings as _s
    if _s.DEBUG:
        logger.info(f"[DEV-CODE] {to_email} -> {code} (expire={expire_sec}s)")

    if not settings.EMAIL_USER or not settings.EMAIL_PASSWORD:
        logger.warning(
            f"[DEV-MAIL] -> {to_email}: 验证码 {code}（{expire_sec}s 内有效）"
        )
        return True

    # 加载模板（来自前端 assets 目录）
    template = _load_template()
    if not template:
        logger.warning("未找到前端邮件模板，使用内置兜底")
        html_body = _fallback_html(code, expire_sec)
    else:
        from datetime import datetime
        html_body = (
            template
            .replace("{{CODE}}", code)
            .replace("{{EXPIRE_MIN}}", str(expire_sec // 60))
            .replace("{{YEAR}}", str(datetime.now().year))
        )

    subject = "【SightEcho 昭视智伴】邮箱验证码"

    def _do_send() -> bool:
        from email.header import Header

        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8").encode()
        # From 头：QQ Mail 严格校验，必须只写邮箱（不带名称）
        msg["From"] = settings.EMAIL_USER
        # 名称用 Sender 或 Reply-To 头
        msg["Reply-To"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_USER}>"
        msg["To"] = to_email
        # 优先 HTML 客户端；附加纯文本备选
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(MIMEText(
            f"您的 SightEcho 验证码：{code}（{expire_sec // 60} 分钟内有效）",
            "plain",
            "utf-8",
        ))

        port = settings.EMAIL_SMTP_PORT
        if settings.EMAIL_USE_SSL or port == 465:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with smtplib.SMTP_SSL(settings.EMAIL_SMTP_HOST, port, timeout=15, context=ctx) as server:
                server.ehlo("localhost")
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.sendmail(settings.EMAIL_USER, to_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.EMAIL_SMTP_HOST, port, timeout=15) as server:
                server.ehlo("localhost")
                if port == 587:
                    server.starttls()
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.sendmail(settings.EMAIL_USER, to_email, msg.as_string())
        return True

    try:
        return await asyncio.to_thread(_do_send)
    except smtplib.SMTPAuthenticationError as e:
        err = e.smtp_error.decode(errors="ignore") if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        logger.error(
            f"邮件发送失败：SMTP 认证错误（{e.smtp_code} {err}）。"
            f"\n排查："
            f"\n1. 确认 EMAIL_USER 与授权码对应的 QQ 号一致（注意 9/10 位区别）"
            f"\n2. 登录 https://mail.qq.com → 设置 → 账户 → 开启 IMAP/SMTP 服务"
            f"\n3. 重新生成 16 位授权码，更新 backend/.env"
        )
        return False
    except Exception as e:
        logger.error(f"邮件发送失败: {type(e).__name__}: {e}")
        return False
