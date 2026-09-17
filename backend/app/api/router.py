"""
v1 路由聚合
"""
from fastapi import APIRouter

from app.api.v1 import admin, auth, feedback, recognition, user, video, voice

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(recognition.router)
api_router.include_router(voice.router)
api_router.include_router(video.router)
api_router.include_router(feedback.router)
api_router.include_router(admin.router)
