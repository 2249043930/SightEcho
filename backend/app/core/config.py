"""
应用配置：基于 pydantic-settings 从环境变量加载
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基础
    APP_NAME: str = "SightEcho"
    APP_ENV: str = "dev"
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    DEBUG: bool = True
    TIMEZONE: str = "Asia/Shanghai"

    # MySQL
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "sightecho"
    MYSQL_PASSWORD: str = "sightecho"
    MYSQL_DB: str = "sightecho"
    MYSQL_CHARSET: str = "utf8mb4"

    # Redis
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # MinIO / OSS
    MINIO_ENDPOINT: str = "127.0.0.1:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "sightecho"
    MINIO_PUBLIC_BASE: str = "http://127.0.0.1:9000"

    # JWT
    JWT_SECRET: str = "sightecho-super-secret-key-change-me-in-prod-32+chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # AI 服务商
    AI_PROVIDER: str = "joyai"  # qwen / openai / joyai
    QWEN_API_KEY: str = ""
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/api/v1"
    QWEN_ASR_MODEL: str = "qwen3-asr-flash"
    QWEN_TTS_MODEL: str = "qwen3-tts-flash"
    QWEN_VL_MODEL: str = "qwen-vl-max"
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    # JoyAI-VL-Interaction（京东云 JoyBuilder MaaS 平台，Chat 兼容协议）
    # 文档：https://docs.jdcloud.com/cn/jdcloud-maas/model-api
    # 注意：只支持 Chat API，视频流场景需要业务侧抽帧后循环喂图
    JOYAI_API_KEY: str = ""
    JOYAI_API_BASE: str = "https://modelservicep.jdcloud.com/v1"
    JOYAI_VL_MODEL: str = "joyai-vl-interaction"
    # 调用模式：image = 单图理解；video = 视频流理解（更适合出行/监控）
    JOYAI_VL_MODE: str = "image"  # image | video
    JOYAI_VIDEO_MAX_FRAMES: int = 8  # 视频模式下采样帧数
    JOYAI_VIDEO_FPS: float = 1.0   # 视频模式下采样帧率

    OCR_PROVIDER: str = "baidu"  # baidu / tencent
    BAIDU_OCR_API_KEY: str = ""
    BAIDU_OCR_SECRET_KEY: str = ""

    # 邮件
    EMAIL_SMTP_HOST: str = "smtp.qq.com"
    EMAIL_SMTP_PORT: int = 465
    EMAIL_USE_SSL: bool = True
    EMAIL_USER: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM_NAME: str = "SightEcho 昭视智伴"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 限流
    RATE_LIMIT_PER_MIN: int = 60
    EMAIL_CODE_DAILY_IP_LIMIT: int = 10
    EMAIL_CODE_INTERVAL_SEC: int = 60

    # 上传
    UPLOAD_MAX_MB: int = 10
    UPLOAD_ALLOWED_MIME: str = "image/jpeg,image/png,image/webp"

    # 降级
    FALLBACK_TIMEOUT_SEC: float = 5.0

    # 演示模式：未配置 AI Key 时返回固定演示结果，便于本地体验
    DEMO_MODE: bool = True

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset={self.MYSQL_CHARSET}"
        )

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def upload_allowed_mime_list(self) -> List[str]:
        return [m.strip() for m in self.UPLOAD_ALLOWED_MIME.split(",") if m.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
