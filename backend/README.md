# SightEcho 昭视智伴 — 后端

> 视障场景智能感知系统后端。**严格对齐前端契约**（`frontend/src/api/*.ts`），统一返回 `{code, message, data}`。

## 一、技术栈

| 组件 | 版本 | 用途 |
|---|---|---|
| Python | 3.11+ | 运行时 |
| FastAPI | 0.110+ | Web 框架 |
| SQLAlchemy | 2.0+ | 异步 ORM |
| aiomysql | 0.2.0+ | MySQL 异步驱动 |
| Alembic | 1.13+ | 数据库迁移 |
| Pydantic | 2.6+ | 数据校验 |
| Redis | 5.0+ | 缓存 / 限流 / 验证码 |
| Celery | 5.3+ | 异步任务 |
| MinIO | - | 对象存储 |
| OpenCV | 4.9+ | 视频处理 |
| websockets | 12+ | ASR/TTS 流式 |
| loguru | 0.7+ | 日志 |

## 二、架构

```
API 层 (api/)         → 只做参数解析、调用 service、返回统一格式
Service 层 (services/)→ 业务编排、Adapter 模式、事务控制、降级策略
Model 层 (models/)    → ORM 映射
Schema 层 (schemas/)  → Pydantic 数据校验
DB 层 (db/)           → 数据库连接、会话工厂
```

外部 AI 接口（Qwen3-ASR / TTS / VL / OCR）通过 **Adapter 模式** 统一封装，支持 **降级容错**（5s 超时）。

## 三、本地启动

### 1. 准备依赖

- Python 3.11+
- MySQL 8.0+
- Redis 7+
- MinIO（可选，未配置时降级到本地占位）

### 2. 安装

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入真实配置（数据库/Redis/AI Key）
```

### 3. 数据库迁移

```bash
alembic upgrade head
```

如果只是开发体验，亦可启动时自动建表（已内置 `init_db`，无需 alembic）。

### 4. 启动

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动 Celery（可选）：

```bash
celery -A app.tasks.celery_app worker -l info -c 4
celery -A app.tasks.celery_app beat -l info
```

## 四、Docker 部署

```bash
cp .env.example .env
docker compose up -d
```

包含服务：MySQL、Redis、MinIO、Backend、Celery Worker、Celery Beat。

## 五、API 文档

启动后访问：

- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health

## 六、前端契约（严格对齐）

> 详见 `frontend/src/api/*.ts`

| 前端方法 | 后端路径 | 鉴权 |
|---|---|---|
| `sendEmailCode({email})` | `POST /api/v1/auth/email-code` | 否 |
| `loginByCode({email,code})` | `POST /api/v1/auth/login` | 否 |
| `logout()` | `POST /api/v1/auth/logout` | 是 |
| `getProfile()` | `GET /api/v1/user/profile` | 是 |
| `updateProfile(p)` | `PUT /api/v1/user/profile` | 是 |
| `getUserSettings()` | `GET /api/v1/user/settings` | 是 |
| `updateUserSettings(p)` | `PUT /api/v1/user/settings` | 是 |
| `recognize({type,image,extra})` | `POST /api/v1/recognition/{type}` | 是 |
| `getHistory(p)` | `GET /api/v1/recognition/history` | 是 |
| `getHistoryDetail(id)` | `GET /api/v1/recognition/history/{id}` | 是 |
| `deleteHistory(id)` | `DELETE /api/v1/recognition/history/{id}` | 是 |
| `submitFeedback({id,rating,comment})` | `POST /api/v1/recognition/feedback` | 是 |
| `ttsOnce({text,...})` | `POST /api/v1/voice/tts` | 是 |
| `getAsrToken()` | `POST /api/v1/voice/asr/token` | 是 |
| `getTtsToken()` | `POST /api/v1/voice/tts/token` | 是 |
| `getAdminStats()` | `GET /api/v1/admin/stats` | admin |
| `listPrompts()` | `GET /api/v1/admin/prompts` | admin |
| `createPrompt(p)` | `POST /api/v1/admin/prompts` | admin |
| `updatePrompt(id,p)` | `PUT /api/v1/admin/prompts/{id}` | admin |
| `deletePrompt(id)` | `DELETE /api/v1/admin/prompts/{id}` | admin |
| `getMonitor()` | `GET /api/v1/admin/monitor` | admin |
| `listFeedback(p)` | `GET /api/v1/admin/feedback` | admin |
| `resolveFeedback(id)` | `PUT /api/v1/admin/feedback/{id}/resolve` | admin |

WebSocket：
- `ws://host/api/v1/voice/asr?token=...`：ASR 流式（音频分片 → JSON 识别结果）
- `ws://host/api/v1/voice/tts?token=...`：TTS 流式（JSON 文本 → 音频 URL）

## 七、调用示例

### 登录流程

```bash
# 1) 发送验证码
curl -X POST http://127.0.0.1:8000/api/v1/auth/email-code \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# 2) 验证码在控制台日志里（DEMO_MODE）或邮件中
# 3) 登录
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'

# 4) 调用受保护接口
TOKEN="eyJ..."
curl http://127.0.0.1:8000/api/v1/user/profile \
  -H "Authorization: Bearer $TOKEN"
```

### 识别

```bash
curl -X POST http://127.0.0.1:8000/api/v1/recognition/travel \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@./test.jpg" \
  -F "extra={}"
```

### WebSocket ASR（使用 websocat）

```bash
websocat "ws://127.0.0.1:8000/api/v1/voice/asr?token=$TOKEN"
# 然后从 stdin 输入 PCM 16kHz 16bit 单声道二进制，输出 JSON
```

## 八、安全

- JWT 7 天过期；HS256；secret 至少 32 位。
- 邮箱验证码：Redis 5 分钟过期，单次有效；单 IP 单日 10 次上限；单邮箱 60s 间隔。
- 文件上传：白名单 MIME（image/jpeg,image/png,image/webp），最大 10MB。
- 隐私：人脸描述接口禁止返回身份信息。
- 日志：邮箱自动脱敏（`a***@b.com`）。

## 九、目录结构

```
backend/
├── app/
│   ├── main.py
│   ├── core/         # config / security / deps / logger
│   ├── api/v1/       # auth / user / recognition / voice / video / feedback / admin
│   ├── services/     # 业务编排 + AI Adapter
│   ├── models/       # SQLAlchemy 2.0 ORM（6 张表）
│   ├── schemas/      # Pydantic v2
│   ├── db/           # 异步会话
│   ├── tasks/        # Celery
│   ├── utils/        # 通用工具
│   └── middleware/   # CORS / Gateway
├── alembic/          # 数据库迁移
├── tests/            # pytest + httpx
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

## 十、降级容错

所有外部 AI 接口统一 5s 超时降级；返回结果含 `isFallback` 字段；前端可据此提示「当前服务繁忙」。

## 十一、扩展点

- Adapter 模式：增加新 AI 服务商只需实现 `AIServiceAdapter` 并在 `config.AI_PROVIDER` 切换。
- Prompt 模板：数据库 `tpl_prompt` 表 + 内存缓存 + 热更新（增删改后 `PromptService.load_all()` 自动重载）。
- 管理员后台：通过 `User.role == 'admin'` 控制访问。

## 十二、测试

```bash
pytest -v
```

## 十三、License

MIT
