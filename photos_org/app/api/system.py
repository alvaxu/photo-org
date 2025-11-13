"""
系统信息API

提供系统相关信息接口，包括版本号等

作者：AI助手
创建日期：2025年11月13日
"""

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/version")
async def get_version():
    """
    获取应用版本号
    
    返回版本号（YYYYMMDD_HH格式，与config.json一致）
    """
    return {
        "version": settings.app_version
    }

