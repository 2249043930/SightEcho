"""
管理端接口契约测试
"""
import pytest
from httpx import ASGITransport, AsyncClient


def _admin_token() -> str:
    from app.core.security import create_access_token
    return create_access_token(user_id=1, role="admin")


def _user_token() -> str:
    from app.core.security import create_access_token
    return create_access_token(user_id=2, role="user")


@pytest.mark.asyncio
async def test_admin_stats_requires_admin():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {_user_token()}"},
        )
        # user 角色访问 admin 应 403
        assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_admin_prompts_list_contract():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(
            "/api/v1/admin/prompts",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        body = r.json()
        assert "code" in body


@pytest.mark.asyncio
async def test_admin_monitor_contract():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(
            "/api/v1/admin/monitor",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        body = r.json()
        assert "code" in body
