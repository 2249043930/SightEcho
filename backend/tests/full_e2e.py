"""
完整端到端流程测试 v4：用纯内存 dict 替代 Redis（避免 event loop 问题）
"""
import asyncio
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=True)


# ============= 纯内存 Redis 替代 =============
class FakeRedisSync:
    """同步 dict 实现的 Redis 替身，兼容 redis.asyncio 协议"""
    def __init__(self):
        self.data = {}
        self.expiry = {}
        self.pipe = None

    async def get(self, k):
        return self.data.get(k)

    async def set(self, k, v, ex=None):
        self.data[k] = v
        if ex:
            self.expiry[k] = ex
        return True

    async def delete(self, k):
        self.data.pop(k, None)
        self.expiry.pop(k, None)
        return 1

    async def exists(self, k):
        return 1 if k in self.data else 0

    async def incr(self, k):
        v = int(self.data.get(k, 0)) + 1
        self.data[k] = v
        return v

    async def expire(self, k, t):
        self.expiry[k] = t
        return True

    async def aclose(self):
        pass

    async def ping(self):
        return True

    def pipeline(self):
        self.pipe = _Pipe(self)
        return self.pipe


class _Pipe:
    def __init__(self, parent):
        self.parent = parent
        self.results = []

    def zremrangebyscore(self, *a): return self
    def zadd(self, *a): return self
    def zcard(self, *a): return self

    async def execute(self):
        # 模拟：返回 [0, 0, 1, 1]
        return [0, 0, 1, 1]


_fake = FakeRedisSync()


async def _fake_get_redis():
    return _fake


# 替换 rate_limit
import app.utils.rate_limit as rlm
rlm.get_redis = _fake_get_redis
rlm.close_redis = lambda: asyncio.sleep(0)

# 替换 main 中的 close_redis
import app.main
app.main.close_redis = lambda: asyncio.sleep(0)

from fastapi.testclient import TestClient
from app.main import app

# 禁用 lifespan 避免 TestClient 事件循环问题
app.router.lifespan_context = None
c = TestClient(app, raise_server_exceptions=True)


def safe(label, fn):
    print(f"\n=== {label} ===")
    try:
        r = fn()
        print(f"HTTP {r.status_code}")
        try:
            b = r.json()
            print(b)
            return b
        except Exception:
            print(r.text[:200])
            return {}
    except Exception as e:
        print(f"EXCEPTION: {type(e).__name__}: {e}")
        return {}


# 1
safe("1. /health", lambda: c.get("/health"))

# 2. send code
r2 = safe("2. send-email-code", lambda: c.post(
    "/api/v1/auth/email-code", json={"email": "demo@sightecho.cn"}
))

# 关键：auth.py 中 r = await get_redis(); await r.set(key, code, ex=300)
# 但 v.set 是同步的，没有 await 问题。
# 直接读 _fake.data
code = _fake.data.get("verify:login:demo@sightecho.cn")
print(f"\n>>> 验证码: {code}")
if not code:
    print("!! 没有验证码")
    sys.exit(1)

# 3. login
r3 = safe("3. login", lambda: c.post(
    "/api/v1/auth/login", json={"email": "demo@sightecho.cn", "code": code}
))
token = r3.get("data", {}).get("token")
print(f">>> token 长度: {len(token) if token else 0}")
auth = {"Authorization": f"Bearer {token}"} if token else {}

# 4
safe("4. profile", lambda: c.get("/api/v1/user/profile", headers=auth))

# 5
safe("5. update settings", lambda: c.put(
    "/api/v1/user/settings",
    json={"speed": 1.5, "volume": 90, "wakeEnabled": True, "autoAnnounce": False, "fontScale": "large"},
    headers=auth,
))

# 6
safe("6. get settings", lambda: c.get("/api/v1/user/settings", headers=auth))

# 7
safe("7. tts", lambda: c.post("/api/v1/voice/tts?text=你好世界", headers=auth))

# 8
import base64
png = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAfbLI3wAAAABJRU5ErkJggg=="
)
r8 = safe("8. travel", lambda: c.post(
    "/api/v1/recognition/travel",
    files={"image": ("t.png", png, "image/png")},
    data={"extra": "{}"},
    headers=auth,
))
rec_id = r8.get("data", {}).get("id") if isinstance(r8, dict) else None
print(f">>> recognition id: {rec_id}")

# 9
safe("9. history", lambda: c.get("/api/v1/recognition/history?page=1&pageSize=10", headers=auth))

# 10
if rec_id:
    safe("10. detail", lambda: c.get(f"/api/v1/recognition/history/{rec_id}", headers=auth))

# 11
if rec_id:
    safe("11. feedback", lambda: c.post(
        "/api/v1/recognition/feedback",
        json={"id": rec_id, "rating": 5, "comment": "识别准确"},
        headers=auth,
    ))

# 12
safe("12. logout", lambda: c.post("/api/v1/auth/logout", headers=auth))

# 13
safe("13. me (登出后)", lambda: c.get("/api/v1/auth/me", headers=auth))

# 14
safe("14. 重复用验证码", lambda: c.post(
    "/api/v1/auth/login", json={"email": "demo@sightecho.cn", "code": code}
))

# 15
safe("15. 普通用户访问 admin", lambda: c.get("/api/v1/admin/stats", headers=auth))

# 16. 无 token
safe("16. 无 token 访问 admin", lambda: c.get("/api/v1/admin/stats"))

# 17. 登录另一用户做权限测试
r17 = safe("17. 给 admin 角色创建用户（直接改库）", lambda: None)
import aiomysql
from app.core.config import settings

async def make_admin():
    conn = await aiomysql.connect(
        host=settings.MYSQL_HOST, port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD,
        db=settings.MYSQL_DB, charset='utf8mb4',
    )
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT IGNORE INTO sys_user (email, nickname, role, status, created_at, updated_at, is_deleted) "
            "VALUES (%s, %s, 'admin', 1, NOW(), NOW(), 0)",
            ("admin@sightecho.cn", "admin"),
        )
        await conn.commit()
    conn.close()
asyncio.run(make_admin())

# 18. 给 admin 发送验证码
r18 = safe("18. admin email-code", lambda: c.post(
    "/api/v1/auth/email-code", json={"email": "admin@sightecho.cn"}
))
admin_code = _fake.data.get("verify:login:admin@sightecho.cn")
print(f">>> admin 验证码: {admin_code}")

if admin_code:
    r19 = safe("19. admin login", lambda: c.post(
        "/api/v1/auth/login", json={"email": "admin@sightecho.cn", "code": admin_code}
    ))
    admin_token = r19.get("data", {}).get("token")
    admin_auth = {"Authorization": f"Bearer {admin_token}"}
    # 20. admin stats
    safe("20. admin stats", lambda: c.get("/api/v1/admin/stats", headers=admin_auth))
    # 21. admin prompts
    safe("21. admin prompts", lambda: c.get("/api/v1/admin/prompts", headers=admin_auth))
    # 22. admin monitor
    safe("22. admin monitor", lambda: c.get("/api/v1/admin/monitor", headers=admin_auth))
    # 23. admin feedback
    safe("23. admin feedback", lambda: c.get("/api/v1/admin/feedback", headers=admin_auth))
    # 24. admin 创建一个 prompt
    safe("24. admin create prompt", lambda: c.post(
        "/api/v1/admin/prompts",
        json={"type": "travel", "name": "测试模板", "content": "你是一个出行助手", "enabled": True},
        headers=admin_auth,
    ))

print("\n=== 全部完成 ===")
