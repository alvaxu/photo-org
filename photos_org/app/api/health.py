"""
健康检查API

提供系统健康状态检查接口

作者：AI助手
创建日期：2025年9月9日
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """
    健康检查接口

    检查系统各组件的运行状态
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }

    try:
        # 检查数据库连接
        db = next(get_db())
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)

    # 检查配置文件
    try:
        if settings.dashscope.api_key:
            health_status["checks"]["configuration"] = "healthy"
        else:
            health_status["checks"]["configuration"] = "warning"
    except Exception as e:
        health_status["checks"]["configuration"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # 检查存储目录
    from pathlib import Path
    storage_path = Path(settings.storage.base_path)
    if storage_path.exists():
        health_status["checks"]["storage"] = "healthy"
    else:
        health_status["checks"]["storage"] = "unhealthy"
        health_status["status"] = "unhealthy"

    if health_status["status"] != "healthy":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status
