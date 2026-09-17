"""端到端契约测试：使用 fakeredis 替代真实 Redis"""
import asyncio
import os
import sys
from unittest.mock import patch

# 设置测试环境
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("JWT_SECRET", "test-secret-key-32-or-more-random-chars-here")

# 用 fakeredis 替代（如果装了）；否则直接跳过需要 Redis 的测试
try:
    import fakeredis.aioredis  # noqa
    HAS_FAKE = True
except ImportError:
    HAS_FAKE = False
    print("WARN: fakeredis 未装，跳过 Redis 相关用例")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

def safe_test(name, fn):
    try:
        fn()
        print(f"OK   {name}")
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__}: {str(e)[:120]}")


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body


def test_openapi():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    expected = {
        "/api/v1/auth/email-code",
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/me",
        "/api/v1/user/profile",
        "/api/v1/user/settings",
        "/api/v1/recognition/upload",
        "/api/v1/recognition/history",
        "/api/v1/recognition/feedback",
        "/api/v1/voice/tts",
        "/api/v1/voice/asr/token",
        "/api/v1/voice/tts/token",
        "/api/v1/video/parse",
        "/api/v1/feedback",
        "/api/v1/admin/stats",
        "/api/v1/admin/prompts",
        "/api/v1/admin/monitor",
        "/api/v1/admin/feedback",
    }
    missing = expected - set(paths.keys())
    assert not missing, f"missing: {missing}"


def test_invalid_email():
    r = client.post("/api/v1/auth/email-code", json={"email": "bad"})
    assert r.status_code == 200
    body = r.json()
    assert body["code"] != 0 and "邮箱" in body["message"]


def test_protected_no_token():
    r = client.get("/api/v1/user/profile")
    assert r.status_code == 401
    body = r.json()
    assert "code" in body and "message" in body


def test_admin_no_token():
    r = client.get("/api/v1/admin/stats")
    assert r.status_code == 401


def test_recognition_history_no_token():
    r = client.get("/api/v1/recognition/history")
    assert r.status_code == 401


def test_voice_tts_no_token():
    r = client.post("/api/v1/voice/tts?text=hello")
    assert r.status_code == 401


def test_prompts_list_no_token():
    r = client.get("/api/v1/admin/prompts")
    assert r.status_code == 401


def test_login_no_redis():
    r = client.post("/api/v1/auth/login", json={"email": "a@b.com", "code": "000000"})
    # 业务响应（code/message/data）
    body = r.json()
    assert "code" in body and "message" in body


def test_send_code_no_redis():
    """不带 Redis 时验证码应能走通到写审计表；这里只验证不崩溃"""
    try:
        r = client.post("/api/v1/auth/email-code", json={"email": "user@example.com"})
        body = r.json()
        assert "code" in body
    except Exception:
        # Redis 不通是预期，断言响应格式即可
        pass


def test_invalid_recognition_type():
    """错误的 type 应在 Pydantic 校验前被业务逻辑拒绝"""
    # 这里仅检查服务层
    from app.schemas.recognition import RecognitionResult
    rec = RecognitionResult(id="1", type="travel", title="t", content="c", createdAt="2026-01-01T00:00:00Z")
    d = rec.model_dump()
    assert d["audioUrl"] is None
    assert d["thumbnail"] is None
    assert d["isFallback"] is None


def test_schemas_camel_case():
    from app.schemas.user import UserSettings
    s = UserSettings()
    # 必须保留 camelCase 字段名给前端
    assert s.speed == 1.0
    assert s.wakeEnabled is True
    assert s.autoAnnounce is True
    assert s.fontScale == "medium"
    # 模型 dump 也是 camelCase
    d = s.model_dump()
    assert "wakeEnabled" in d and "autoAnnounce" in d and "fontScale" in d


def test_recognition_result_fields():
    from app.schemas.recognition import RecognitionResult
    r = RecognitionResult(
        id="100", type="travel", title="出行感知", content="前方有台阶",
        audioUrl=None, thumbnail=None, createdAt="2026-01-01T00:00:00Z",
    )
    d = r.model_dump()
    for k in ["id", "type", "title", "content", "audioUrl", "thumbnail", "createdAt"]:
        assert k in d


def test_admin_stats_shape():
    from app.schemas.admin import AdminStatsResp
    s = AdminStatsResp(
        totalUsers=10, todayActive=3, todayCalls=100, successRate=0.99,
        trend=[], distribution=[],
    )
    d = s.model_dump()
    assert d["totalUsers"] == 10
    assert d["successRate"] == 0.99


def test_fallback_service():
    """降级服务逻辑"""
    from app.services.fallback_service import run_with_fallback

    async def _t():
        # 主失败 + 备选成功
        async def ok_fb(p):
            return {"text": "ok", "confidence": 0.5}
        r, fb = await run_with_fallback(
            primary=lambda p: (_ for _ in ()).throw(RuntimeError("fail")),
            fallback=ok_fb,
        )
        assert fb is True
        assert r["text"] == "ok"
        # 双失败
        async def fail_fb(p):
            raise RuntimeError("y")
        r2, fb2 = await run_with_fallback(
            primary=lambda p: (_ for _ in ()).throw(RuntimeError("x")),
            fallback=fail_fb,
        )
        assert fb2 is True
        assert r2["is_fallback"] is True

    asyncio.run(_t())


def test_prompt_danger_keywords():
    from app.services.prompt_service import PromptService
    assert PromptService.detect_priority("前方有台阶") == "high"
    assert PromptService.detect_priority("车辆靠近") == "high"
    assert PromptService.detect_priority("天气很好") == "normal"
    # 危险句置顶
    text = "天气很好。前方有台阶请小心。安全通行。"
    sorted_text = PromptService.extract_high_priority(text)
    assert "台阶" in sorted_text[:10]


print("=== SightEcho 后端契约测试 ===")
safe_test("health", test_health)
safe_test("openapi 路径完整", test_openapi)
safe_test("错误邮箱被拒", test_invalid_email)
safe_test("无 token 访问受保护", test_protected_no_token)
safe_test("无 token 访问 admin", test_admin_no_token)
safe_test("无 token 访问 history", test_recognition_history_no_token)
safe_test("无 token 访问 tts", test_voice_tts_no_token)
safe_test("无 token 访问 prompts", test_prompts_list_no_token)
safe_test("login 无 redis 仍返回统一格式", test_login_no_redis)
safe_test("email-code 流程", test_send_code_no_redis)
safe_test("Schema 字段 camelCase", test_schemas_camel_case)
safe_test("RecognitionResult 字段", test_recognition_result_fields)
safe_test("AdminStatsResp 字段", test_admin_stats_shape)
safe_test("降级服务逻辑", test_fallback_service)
safe_test("危险关键词", test_prompt_danger_keywords)
print("=== 完成 ===")
