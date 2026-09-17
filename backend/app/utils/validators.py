"""
Pydantic 自定义校验器
"""
from __future__ import annotations

import re

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
CODE_REGEX = re.compile(r"^\d{6}$")


def is_valid_email(email: str) -> bool:
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def is_valid_code(code: str) -> bool:
    if not code:
        return False
    return bool(CODE_REGEX.match(code.strip()))
