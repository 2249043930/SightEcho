"""
pytest 全局 fixture：使用内存 SQLite + 静态 token 简化测试
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio

# 让 tests 目录可导入 app
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 关键：在导入 app 之前覆盖环境变量
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("JWT_SECRET", "test-secret-key-32+characters-please-here")
os.environ.setdefault(
    "MYSQL_HOST", os.environ.get("MYSQL_HOST", "127.0.0.1")
)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _log_quiet():
    import logging
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
