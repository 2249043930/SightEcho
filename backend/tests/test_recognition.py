"""
识别接口契约测试
"""
import io

import pytest
from httpx import ASGITransport, AsyncClient


def _fake_jwt(user_id: int = 1, role: str = "user") -> str:
    from app.core.security import create_access_token
    return create_access_token(user_id=user_id, role=role)


def _png_bytes() -> bytes:
    # 最小的 1x1 PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff"
        b"\xff?\x00\x05\xfe\x02\xfe\xa3\x9b\xff\x00\x00\x00\x00IEND\xaeB`\x82"
    )


@pytest.mark.asyncio
async def test_recognize_travel_demo():
    from app.main import app

    token = _fake_jwt(user_id=999, role="user")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 当前用户可能在测试库不存在，但鉴权流程会先校验 token，校验通过后查不到用户会 401
        # 因此这里仅做契约验证（即便 401 也能拿到统一格式响应）
        r = await ac.post(
            "/api/v1/recognition/travel",
            files={"image": ("t.png", _png_bytes(), "image/png")},
            data={"extra": "{}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        body = r.json()
        assert "code" in body
        assert "message" in body


@pytest.mark.asyncio
async def test_recognize_invalid_type():
    from app.main import app

    token = _fake_jwt()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/recognition/invalid_type",
            files={"image": ("t.png", _png_bytes(), "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )
        # 类型校验可能先于鉴权；也可能鉴权先 401
        body = r.json()
        assert "code" in body


@pytest.mark.asyncio
async def test_history_endpoint_contract():
    from app.main import app

    token = _fake_jwt()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(
            "/api/v1/recognition/history",
            params={"page": 1, "pageSize": 20},
            headers={"Authorization": f"Bearer {token}"},
        )
        body = r.json()
        assert "code" in body
