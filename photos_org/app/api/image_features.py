"""
图像特征提取API接口

参考人脸识别API的设计

## 功能特点：
1. 图像特征提取API
2. 批处理任务管理API
3. 任务状态查询API
4. 统计信息API

## 与其他版本的不同点：
- 完全参考人脸识别API的实现
- 支持批量特征提取
- 提供任务状态查询功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging

from app.db.session import get_db
from app.services.image_feature_service import image_feature_service
from app.services.image_feature_task import (
    start_image_feature_extraction_task,
    get_image_feature_extraction_task_status as get_task_status
)
from app.models.photo import Photo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image-features", tags=["image_features"])


@router.get("/pending-photos")
async def get_pending_image_feature_extraction_photos(db: Session = Depends(get_db)):
    """
    获取待提取特征的照片列表
    
    :param db: 数据库会话
    :return: 待处理照片列表
    """
    try:
        # 查询未提取特征的照片
        photos_to_process = db.query(Photo).filter(
            Photo.image_features_extracted == False  # 或 image_features_extracted IS NULL
        ).all()
        
        return {
            "success": True,
            "total": len(photos_to_process),
            "photos": [
                {
                    "id": photo.id,
                    "filename": photo.filename,
                    "original_path": photo.original_path,
                    "taken_at": photo.taken_at.isoformat() if photo.taken_at else None
                }
                for photo in photos_to_process
            ]
        }
        
    except Exception as e:
        logger.error(f"获取待处理照片列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-extraction")
async def start_image_feature_extraction(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    开始图像特征提取处理（支持分批处理）
    
    :param request: 请求数据，可包含photo_ids字段
    :param db: 数据库会话
    :return: 任务信息
    """
    try:
        # 初始化图像特征提取服务
        if not image_feature_service.is_initialized:
            await image_feature_service.initialize()
            
        if not image_feature_service.is_initialized:
            return {
                "success": False,
                "task_id": None,
                "total_photos": 0,
                "message": "图像特征提取服务初始化失败"
            }
        
        # 获取要处理的照片ID列表
        photo_ids = request.get("photo_ids", [])
        
        if not photo_ids:
            # 如果没有提供照片ID，获取所有需要提取特征的照片
            photos_to_process = db.query(Photo).filter(
                Photo.image_features_extracted == False  # 或 image_features_extracted IS NULL
            ).all()
            photo_ids = [photo.id for photo in photos_to_process]
        
        if not photo_ids:
            return {
                "success": True,
                "task_id": None,
                "total_photos": 0,
                "message": "没有需要提取特征的照片"
            }
        
        # 启动特征提取任务
        task_result = await start_image_feature_extraction_task(photo_ids)
        
        return {
            "success": True,
            "task_id": task_result["task_id"],
            "total_photos": task_result["total_photos"],
            "message": task_result["message"]
        }
        
    except Exception as e:
        logger.error(f"启动图像特征提取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-status/{task_id}")
async def get_image_feature_extraction_task_status(task_id: str):
    """
    获取图像特征提取任务状态
    
    :param task_id: 任务ID
    :return: 任务状态信息
    """
    try:
        status = get_task_status(task_id)
        
        # 如果任务不存在，返回友好的错误信息
        if status.get("status") == "not_found":
            return {
                "success": False,
                "task_id": task_id,
                "status": "not_found",
                "message": "任务不存在或已过期"
            }
        
        # 直接返回状态数据（与基础分析和人脸识别保持一致）
        return status
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_image_feature_extraction_stats(db: Session = Depends(get_db)):
    """
    获取图像特征提取统计信息
    
    :param db: 数据库会话
    :return: 统计信息
    """
    try:
        total_photos = db.query(Photo).count()
        extracted_photos = db.query(Photo).filter(
            Photo.image_features_extracted == True
        ).count()
        pending_photos = total_photos - extracted_photos
        
        return {
            "success": True,
            "total_photos": total_photos,
            "extracted_photos": extracted_photos,
            "pending_photos": pending_photos,
            "extraction_rate": round((extracted_photos / total_photos * 100) if total_photos > 0 else 0, 2)
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

