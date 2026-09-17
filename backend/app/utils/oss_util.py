"""
MinIO 对象存储：上传图片、生成可访问 URL
"""
from __future__ import annotations

import asyncio
import io
import uuid
from datetime import datetime
from typing import Optional

from loguru import logger
from minio import Minio
from minio.error import S3Error

from app.core.config import settings

# 上传超时（秒）
UPLOAD_TIMEOUT = 3.0


_client: Optional[Minio] = None


def _get_client() -> Minio:
    global _client
    if _client is None:
        secure = settings.MINIO_ENDPOINT.startswith("https://") or settings.MINIO_PUBLIC_BASE.startswith("https://")
        endpoint = settings.MINIO_ENDPOINT.replace("https://", "").replace("http://", "")
        _client = Minio(
            endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=secure,
        )
        # 确保 bucket 存在
        try:
            if not _client.bucket_exists(settings.MINIO_BUCKET):
                _client.make_bucket(settings.MINIO_BUCKET)
        except S3Error as e:
            logger.warning(f"MinIO bucket 检查失败: {e}")
    return _client


async def upload_bytes(
    data: bytes,
    suffix: str,
    content_type: str = "image/jpeg",
) -> Optional[str]:
    """
    上传二进制到 MinIO，返回可访问的 URL
    开发环境若 MinIO 不可用，则返回 None，由调用方降级到本地 /static
    """
    def _do() -> Optional[str]:
        try:
            client = _get_client()
            date = datetime.utcnow().strftime("%Y/%m/%d")
            name = f"{date}/{uuid.uuid4().hex}{suffix}"
            client.put_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return f"{settings.MINIO_PUBLIC_BASE}/{settings.MINIO_BUCKET}/{name}"
        except Exception as e:
            logger.warning(f"MinIO 上传失败: {e}")
            return None

    try:
        return await asyncio.wait_for(asyncio.to_thread(_do), timeout=UPLOAD_TIMEOUT)
    except asyncio.TimeoutError:
        logger.warning(f"MinIO 上传超时（{UPLOAD_TIMEOUT}s）")
        return None
    except Exception as e:
        logger.warning(f"MinIO 上传失败: {e}")
        return None


async def upload_file(file) -> Optional[str]:
    """上传 UploadFile"""
    try:
        data = await file.read()
    except Exception:
        return None
    suffix = "." + file.filename.split(".")[-1] if "." in (file.filename or "") else ".jpg"
    return await upload_bytes(data, suffix=suffix, content_type=file.content_type or "image/jpeg")
