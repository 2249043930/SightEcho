"""
日志：基于 loguru
"""
import logging
import sys
from pathlib import Path

from loguru import logger as _logger

from app.core.config import settings


def _mask_email(text: str) -> str:
    """邮箱脱敏：a***@b.com"""
    if not text or "@" not in text:
        return text
    try:
        local, domain = text.split("@", 1)
        if len(local) <= 1:
            return f"{local}***@{domain}"
        return f"{local[0]}***@{domain}"
    except Exception:
        return text


class MaskingFilter:
    """敏感信息脱敏过滤器"""

    def __call__(self, record):
        # 记录上下文脱敏
        if "email" in record["extra"]:
            record["extra"]["email"] = _mask_email(record["extra"]["email"])
        return True


def setup_logger() -> None:
    """初始化全局日志"""
    _logger.remove()

    log_level = "DEBUG" if settings.DEBUG else "INFO"

    _logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <7}</level> | "
            "<cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
        ),
        level=log_level,
        filter=MaskingFilter(),
        backtrace=False,
        diagnose=False,
    )

    # 文件日志
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    _logger.add(
        log_dir / "app.log",
        rotation="20 MB",
        retention="14 days",
        encoding="utf-8",
        level=log_level,
        enqueue=True,
    )


setup_logger()

# 屏蔽 uvicorn 默认 logger，交由 loguru 统一处理
logging.getLogger("uvicorn").handlers = []
logging.getLogger("uvicorn.access").handlers = []

logger = _logger
