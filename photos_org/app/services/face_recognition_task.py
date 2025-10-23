"""
人脸识别批处理任务模块

## 功能特点：
1. 参考基础分析的批处理架构
2. 支持并发处理
3. 实时进度更新
4. 任务状态管理
5. 错误处理和重试

## 与其他版本的不同点：
- 完全参考基础分析的实现
- 支持人脸识别特定的处理流程
- 集成聚类功能
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from app.core.config import settings
from app.db.session import get_db
from app.models.face import FaceDetection, FaceCluster, FaceClusterMember, Person
from app.models.photo import Photo
from app.services.face_recognition_service import face_service
from app.services.face_cluster_service import cluster_service
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 任务状态存储（参考基础分析）
face_recognition_task_status = {}

async def start_face_recognition_task(photo_ids: List[int]) -> Dict:
    """
    开始人脸识别任务（参考基础分析的start_analysis）
    :param photo_ids: 照片ID列表
    :return: 任务信息
    """
    try:
        if not photo_ids:
            return {
                "task_id": None,
                "total_photos": 0,
                "message": "没有需要人脸识别的照片"
            }
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 记录任务状态
        face_recognition_task_status[task_id] = {
            "status": "processing",
            "total_photos": len(photo_ids),
            "completed_photos": 0,
            "failed_photos": 0,
            "progress_percentage": 0,
            "start_time": datetime.now(),
            "current_batch": 0,
            "total_batches": 0,
            "error": None
        }
        
        # 启动后台任务
        asyncio.create_task(process_face_recognition_task(task_id, photo_ids))
        
        return {
            "task_id": task_id,
            "total_photos": len(photo_ids),
            "message": "人脸识别任务已启动"
        }
        
    except Exception as e:
        logger.error(f"启动人脸识别失败: {str(e)}")
        raise Exception(f"启动人脸识别失败: {str(e)}")

async def process_face_recognition_task(task_id: str, photo_ids: List[int]):
    """
    处理人脸识别任务（参考基础分析的process_analysis_task）
    :param task_id: 任务ID
    :param photo_ids: 照片ID列表
    """
    logger.info(f"=== 开始处理人脸识别任务 {task_id} ===")
    logger.info(f"照片数量: {len(photo_ids)}")
    
    try:
        # 初始化人脸识别服务
        if not face_service.is_initialized:
            await face_service.initialize()
            
        if not face_service.is_initialized:
            raise Exception("人脸识别服务初始化失败")
        
        # 分批处理
        batch_size = settings.face_recognition.batch_size
        max_concurrent_batches = settings.face_recognition.max_concurrent_batches
        
        total_batches = (len(photo_ids) + batch_size - 1) // batch_size
        
        # 更新任务状态
        face_recognition_task_status[task_id]["total_batches"] = total_batches
        
        # 处理单批次照片（前端负责分批和并发控制）
        logger.info(f"处理照片批次, 照片数量: {len(photo_ids)}")
        
        # 更新任务状态
        face_recognition_task_status[task_id]["current_batch"] = 1
        face_recognition_task_status[task_id]["total_batches"] = 1
        
        # 处理当前批次
        await process_face_recognition_batch(task_id, photo_ids)
        
        # 完成后执行聚类
        logger.info("开始执行人脸聚类...")
        await perform_face_clustering(task_id)
        
        # 更新任务状态为完成
        face_recognition_task_status[task_id]["status"] = "completed"
        face_recognition_task_status[task_id]["progress_percentage"] = 100
        face_recognition_task_status[task_id]["end_time"] = datetime.now()
        
        logger.info(f"=== 人脸识别任务 {task_id} 完成 ===")
        
        # 延迟清理任务状态
        asyncio.create_task(cleanup_task_status(task_id))
        
    except Exception as e:
        logger.error(f"处理人脸识别任务失败: {str(e)}")
        face_recognition_task_status[task_id]["status"] = "failed"
        face_recognition_task_status[task_id]["error"] = str(e)

async def process_face_recognition_batch(task_id: str, photo_ids: List[int]):
    """
    处理人脸识别批次（参考基础分析的process_analysis_batch）
    :param task_id: 任务ID
    :param photo_ids: 照片ID列表
    """
    try:
        # 使用信号量控制单批次内的并发数
        max_concurrent_photos = settings.face_recognition.max_concurrent_photos
        semaphore = asyncio.Semaphore(max_concurrent_photos)
        logger.info(f"单批次内最大并发照片数: {max_concurrent_photos}")
        
        async def process_single_photo(photo_id: int):
            async with semaphore:
                try:
                    # 获取照片信息
                    db = next(get_db())
                    photo = db.query(Photo).filter(Photo.id == photo_id).first()
                    
                    if not photo:
                        return
                    
                    # 构建完整路径
                    storage_base = Path(settings.storage.base_path)
                    full_path = storage_base / photo.original_path
                    
                    if not full_path.exists():
                        logger.warning(f"照片文件不存在: {full_path}")
                        return
                    
                    # 检测人脸
                    detections = await face_service.detect_faces_in_photo(str(full_path), photo_id)
                    
                    # 保存人脸检测结果
                    if detections:
                        await face_service.save_face_detections(detections, db)
                    
                    # 🔥 新增：为没有检测到人脸的照片创建处理记录
                    await face_service.mark_photos_as_processed({photo_id}, db)
                    
                    # 更新任务状态
                    face_recognition_task_status[task_id]["completed_photos"] += 1
                    face_recognition_task_status[task_id]["progress_percentage"] = int(
                        (face_recognition_task_status[task_id]["completed_photos"] / 
                         face_recognition_task_status[task_id]["total_photos"]) * 100
                    )
                    
                except Exception as e:
                    logger.error(f"处理照片 {photo_id} 失败: {str(e)}")
                    face_recognition_task_status[task_id]["failed_photos"] += 1
                finally:
                    db.close()
        
        # 并发处理照片
        await asyncio.gather(*[process_single_photo(photo_id) for photo_id in photo_ids])
        
    except Exception as e:
        logger.error(f"处理人脸识别批次失败: {str(e)}")
        raise

async def perform_face_clustering(task_id: str):
    """
    执行人脸聚类（参考基础分析的perform_clustering）
    :param task_id: 任务ID
    """
    try:
        # 获取数据库会话
        db = next(get_db())
        
        # 执行聚类
        await cluster_service.cluster_faces(db)
        
        logger.info(f"人脸聚类完成")
        
    except Exception as e:
        logger.error(f"人脸聚类失败: {str(e)}")
        raise
    finally:
        db.close()

async def cleanup_task_status(task_id: str):
    """
    清理任务状态（参考基础分析的cleanup_task_status）
    :param task_id: 任务ID
    """
    try:
        # 延迟5分钟后清理任务状态
        await asyncio.sleep(300)  # 5分钟
        
        if task_id in face_recognition_task_status:
            del face_recognition_task_status[task_id]
            logger.info(f"任务状态已清理: {task_id}")
            
    except Exception as e:
        logger.error(f"清理任务状态失败: {str(e)}")

def get_face_recognition_task_status(task_id: str) -> Dict:
    """
    获取人脸识别任务状态（参考基础分析的get_analysis_task_status）
    :param task_id: 任务ID
    :return: 任务状态
    """
    try:
        # 优先从内存获取
        if task_id in face_recognition_task_status:
            status = face_recognition_task_status[task_id].copy()
            # 转换datetime对象为字符串
            if "start_time" in status and status["start_time"]:
                status["start_time"] = status["start_time"].isoformat()
            if "end_time" in status and status["end_time"]:
                status["end_time"] = status["end_time"].isoformat()
            return status
        
        # 如果内存中没有，返回默认状态
        return {
            "status": "not_found",
            "message": "任务不存在或已过期"
        }
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
