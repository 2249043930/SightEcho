"""
真实 HTTP 端到端测试 v2：使用调试端点读取验证码
"""
import asyncio
import base64
import os
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

BASE = "http://127.0.0.1:8000"


def show(label, r):
    print(f"\n=== {label} ===")
    print(f"HTTP {r.status_code}")
    try:
        b = r.json()
        s = str(b)
        print(s[:300] + ("..." if len(s) > 300 else ""))
        return b
    except Exception:
        print(r.text[:200])
        return {}


def main():
    c = httpx.Client(base_url=BASE, timeout=15)

    # 0. 清空之前的测试数据
    print("=== 0. 清理之前的演示用户 ===")
    import aiomysql
    from app.core.config import settings

    async def clean():
        conn = await aiomysql.connect(
            host=settings.MYSQL_HOST, port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD,
            db=settings.MYSQL_DB, charset='utf8mb4',
        )
        async with conn.cursor() as cur:
            await cur.execute('DELETE FROM cfg_verification')
            await cur.execute('DELETE FROM fb_feedback')
            await cur.execute('DELETE FROM rec_record')
            await cur.execute('DELETE FROM sys_user WHERE email IN (%s, %s)',
                              ('live@sightecho.cn', 'admin@sightecho.cn'))
            await conn.commit()
        conn.close()
    asyncio.run(clean())
    print("已清理")

    # 1. 健康
    show("1. /health", c.get("/health"))

    # 2. 发验证码
    r2 = show("2. send-email-code", c.post("/api/v1/auth/email-code", json={"email": "live@sightecho.cn"}))

    # 3. 从调试端点读验证码（真实 Redis）
    r3 = show("3. /_debug/kv (内存)", c.get("/_debug/kv"))
    import redis as _redis
    rcli = _redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
    code = rcli.get("verify:login:live@sightecho.cn")
    print(f">>> 验证码 (从 Redis): {code}")
    if not code:
        print("!! 没有验证码")
        return

    # 4. 登录
    r4 = show("4. login", c.post("/api/v1/auth/login", json={"email": "live@sightecho.cn", "code": code}))
    token = r4.get("data", {}).get("token")
    print(f">>> token 长度: {len(token) if token else 0}")
    auth = {"Authorization": f"Bearer {token}"} if token else {}

    # 5. profile
    show("5. profile", c.get("/api/v1/user/profile", headers=auth))

    # 6. 更新设置
    show("6. update settings", c.put(
        "/api/v1/user/settings",
        json={"speed": 1.5, "volume": 90, "wakeEnabled": True, "autoAnnounce": False, "fontScale": "large"},
        headers=auth,
    ))

    # 7. 读取设置
    show("7. get settings", c.get("/api/v1/user/settings", headers=auth))

    # 8. TTS
    show("8. tts", c.post("/api/v1/voice/tts?text=你好世界", headers=auth))

    # 9. 识别
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAfbLI3wAAAABJRU5ErkJggg=="
    )
    r9 = show("9. travel", c.post(
        "/api/v1/recognition/travel",
        files={"image": ("t.png", png, "image/png")},
        data={"extra": "{}"},
        headers=auth,
    ))
    rec_id = r9.get("data", {}).get("id") if isinstance(r9, dict) else None
    print(f">>> 识别 ID: {rec_id}")

    # 10. 历史
    show("10. history", c.get("/api/v1/recognition/history?page=1&pageSize=10", headers=auth))

    # 11. 详情
    if rec_id:
        show("11. detail", c.get(f"/api/v1/recognition/history/{rec_id}", headers=auth))

    # 12. 反馈
    if rec_id:
        show("12. feedback", c.post(
            "/api/v1/recognition/feedback",
            json={"id": rec_id, "rating": 5, "comment": "识别准确"},
            headers=auth,
        ))

    # 13. 登出
    show("13. logout", c.post("/api/v1/auth/logout", headers=auth))

    # 14. me
    show("14. me", c.get("/api/v1/auth/me", headers=auth))

    # 15. 重复用验证码
    show("15. 重复用验证码", c.post("/api/v1/auth/login", json={"email": "live@sightecho.cn", "code": code}))

    # 16. 普通用户访问 admin
    show("16. 普通用户访问 admin", c.get("/api/v1/admin/stats", headers=auth))

    # 17. 创建 admin 用户（手改库）
    async def make_admin():
        conn = await aiomysql.connect(
            host=settings.MYSQL_HOST, port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD,
            db=settings.MYSQL_DB, charset='utf8mb4',
        )
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO sys_user (email, nickname, role, status, created_at, updated_at, is_deleted) "
                "VALUES (%s, 'admin', 'admin', 1, NOW(), NOW(), 0)",
                ("admin@sightecho.cn",),
            )
            await conn.commit()
        conn.close()
    asyncio.run(make_admin())

    # 18. admin 验证码
    show("18. admin email-code", c.post("/api/v1/auth/email-code", json={"email": "admin@sightecho.cn"}))
    admin_code = rcli.get("verify:login:admin@sightecho.cn")
    print(f">>> admin 验证码: {admin_code}")

    if admin_code:
        r19 = show("19. admin login", c.post("/api/v1/auth/login", json={"email": "admin@sightecho.cn", "code": admin_code}))
        admin_token = r19.get("data", {}).get("token")
        admin_auth = {"Authorization": f"Bearer {admin_token}"}

        show("20. admin stats", c.get("/api/v1/admin/stats", headers=admin_auth))
        show("21. admin prompts", c.get("/api/v1/admin/prompts", headers=admin_auth))
        show("22. admin monitor", c.get("/api/v1/admin/monitor", headers=admin_auth))
        show("23. admin feedback", c.get("/api/v1/admin/feedback", headers=admin_auth))
        show("24. admin create prompt", c.post(
            "/api/v1/admin/prompts",
            json={"type": "travel", "name": "测试模板", "content": "你是一个出行助手", "enabled": True},
            headers=admin_auth,
        ))

    print("\n=== 真实 HTTP 端到端测试完成 ===")


if __name__ == "__main__":
    main()
