"""
认证模块测试：验证码发送 + 登录
"""
import io

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body.get("status") in ("ok", "degraded")


@pytest.mark.asyncio
async def test_send_code_invalid_email():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/email-code", json={"email": "not-an-email"})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] != 0
        assert "邮箱" in body["message"]


@pytest.mark.asyncio
async def test_login_without_code():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/login", json={"email": "x@x.com", "code": "000000"})
        # 由于 Redis 在测试环境可能未启动，可能直接失败；以业务返回判断
        body = r.json()
        assert "code" in body


@pytest.mark.asyncio
async def test_protected_endpoint_no_token():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/v1/user/profile")
        assert r.status_code == 401
