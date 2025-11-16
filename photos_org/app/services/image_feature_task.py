"""
图像特征提取批处理任务模块

参考人脸识别批处理任务的设计

## 功能特点：
1. 参考人脸识别批处理的架构
2. 支持分批处理
3. 实时进度更新
4. 任务状态管理
5. 错误处理和重试

## 与其他版本的不同点：
- 完全参考人脸识别批处理的实现
- 支持图像特征提取特定的处理流程
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from app.core.config import settings
from app.db.session import get_db
from app.models.photo import Photo
from app.services.image_feature_service import image_feature_service
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 任务状态存储（参考人脸识别批处理）
image_feature_task_status = {}


async def start_image_feature_extraction_task(photo_ids: List[int]) -> Dict:
    """
    开始图像特征提取任务
    
    :param photo_ids: 照片ID列表
    :return: 任务信息
    """
    try:
        if not photo_ids:
            return {
                "task_id": None,
                "total_photos": 0,
                "message": "没有需要提取特征的照片"
            }
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 记录任务状态
        image_feature_task_status[task_id] = {
            "status": "processing",
            "total_photos": len(photo_ids),
            "completed_photos": 0,
            "failed_photos": 0,
            "progress_percentage": 0.0,
            "start_time": datetime.now(),
            "current_batch": 0,
            "total_batches": 0,
            "completed_batches": 0,
            "failed_batches": 0,
            "processing_photos": len(photo_ids),
            "error": None,
            "error_details": [],
            "batch_details": []
        }
        
        # 启动后台任务
        asyncio.create_task(process_image_feature_extraction_task(task_id, photo_ids))
        
        return {
            "task_id": task_id,
            "total_photos": len(photo_ids),
            "message": "图像特征提取任务已启动"
        }
        
    except Exception as e:
        logger.error(f"启动图像特征提取失败: {str(e)}")
        raise Exception(f"启动图像特征提取失败: {str(e)}")


async def process_image_feature_extraction_task(task_id: str, photo_ids: List[int]):
    """
    处理图像特征提取任务
    
    :param task_id: 任务ID
    :param photo_ids: 照片ID列表
    """
    logger.info(f"=== 开始处理图像特征提取任务 {task_id} ===")
    logger.info(f"照片数量: {len(photo_ids)}")
    
    try:
        # 初始化图像特征提取服务
        if not image_feature_service.is_initialized:
            await image_feature_service.initialize()
            
        if not image_feature_service.is_initialized:
            raise Exception("图像特征提取服务初始化失败")
        
        # 分批处理（使用最新配置）
        from app.core.config import get_settings
        current_settings = get_settings()
        batch_size = current_settings.image_features.batch_size
        batch_threshold = current_settings.image_features.batch_threshold
        
        # 判断是否需要分批
        if len(photo_ids) > batch_threshold:
            total_batches = (len(photo_ids) + batch_size - 1) // batch_size
            logger.info(f"分批处理: 总批次数 {total_batches}, 每批 {batch_size} 张照片")
            
            # 更新任务状态
            image_feature_task_status[task_id]["total_batches"] = total_batches
            
            # 分批处理照片
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(photo_ids))
                batch_photo_ids = photo_ids[start_idx:end_idx]
                
                logger.info(f"处理批次 {batch_idx + 1}/{total_batches}, 照片数量: {len(batch_photo_ids)}")
                
                # 更新当前批次状态
                image_feature_task_status[task_id]["current_batch"] = batch_idx + 1
                
                # 记录批次详情
                batch_detail = {
                    "batch_index": batch_idx + 1,
                    "total_photos": len(batch_photo_ids),
                    "completed_photos": 0,
                    "failed_photos": 0,
                    "status": "processing",
                    "error": None,
                    "completed_at": None
                }
                image_feature_task_status[task_id]["batch_details"].append(batch_detail)
                
                try:
                    # 处理当前批次
                    await process_image_feature_extraction_batch(task_id, batch_photo_ids, batch_idx)
                    
                    # 更新批次完成状态
                    image_feature_task_status[task_id]["completed_batches"] = batch_idx + 1
                    batch_detail["status"] = "completed"
                    batch_detail["completed_photos"] = len(batch_photo_ids)
                    batch_detail["completed_at"] = datetime.now().isoformat()
                    
                except Exception as e:
                    # 处理批次失败状态
                    image_feature_task_status[task_id]["failed_batches"] += 1
                    batch_detail["status"] = "failed"
                    batch_detail["failed_photos"] = len(batch_photo_ids)
                    batch_detail["error"] = str(e)
                    batch_detail["completed_at"] = datetime.now().isoformat()
                    logger.error(f"批次 {batch_idx + 1} 处理失败: {str(e)}")
                
                # 批次间短暂延迟，避免资源竞争
                if batch_idx < total_batches - 1:
                    await asyncio.sleep(0.1)
        else:
            # 单批处理
            logger.info(f"单批处理: {len(photo_ids)} 张照片")
            image_feature_task_status[task_id]["total_batches"] = 1
            await process_image_feature_extraction_batch(task_id, photo_ids, 0)
        
        # 更新任务状态为完成
        image_feature_task_status[task_id]["status"] = "completed"
        image_feature_task_status[task_id]["progress_percentage"] = 100.0
        image_feature_task_status[task_id]["end_time"] = datetime.now()
        
        logger.info(f"=== 图像特征提取任务 {task_id} 完成 ===")
        
        # 延迟清理任务状态（可选）
        # asyncio.create_task(cleanup_task_status(task_id))
        
    except Exception as e:
        logger.error(f"处理图像特征提取任务失败: {str(e)}")
        image_feature_task_status[task_id]["status"] = "failed"
        image_feature_task_status[task_id]["error"] = str(e)
        import traceback
        traceback.print_exc()


async def process_image_feature_extraction_batch(task_id: str, photo_ids: List[int], batch_idx: int = 0):
    """
    处理图像特征提取批次
    
    :param task_id: 任务ID
    :param photo_ids: 照片ID列表
    :param batch_idx: 批次索引
    """
    all_processed_photos = set()
    all_features_data = []  # 存储待保存的特征数据
    successful_extractions = 0
    failed_extractions = 0
    
    # 🔥 使用上下文管理器管理数据库会话（Python 最佳实践）
    from app.db.session import get_db_context
    with get_db_context() as db:
        # 批量预查询所有照片信息
        logger.info(f"批量预查询 {len(photo_ids)} 张照片信息...")
        def batch_query_photos():
            photos = db.query(Photo).filter(Photo.id.in_(photo_ids)).all()
            return {photo.id: photo for photo in photos}
        
        photo_cache = await asyncio.to_thread(batch_query_photos)
        logger.info(f"成功预查询 {len(photo_cache)} 张照片信息")
        
        # 使用信号量控制单批次内的并发数（使用最新配置）
        from app.core.config import get_settings
        current_settings = get_settings()
        max_concurrent_photos = current_settings.image_features.max_concurrent_photos
        semaphore = asyncio.Semaphore(max_concurrent_photos)
        logger.info(f"单批次内最大并发照片数: {max_concurrent_photos}")
        
        async def process_single_photo_with_semaphore(photo_id: int):
            """使用信号量控制并发处理单张照片（只提取特征，不保存数据库）"""
            try:
                # 从缓存获取照片信息
                photo = photo_cache.get(photo_id)
                
                if not photo:
                    return {"photo_id": photo_id, "status": "skipped", "reason": "photo_not_found"}
                
                # 构建完整路径（使用最新配置）
                from app.core.config import get_settings
                from app.core.path_utils import resolve_resource_path
                current_settings = get_settings()
                storage_base = resolve_resource_path(current_settings.storage.base_path)
                if Path(photo.original_path).is_absolute():
                    full_path = Path(photo.original_path)
                else:
                    full_path = storage_base / photo.original_path
                
                # 异步执行：文件检查
                file_exists = await asyncio.to_thread(full_path.exists)
                
                if not file_exists:
                    logger.warning(f"照片文件不存在: {full_path}")
                    return {"photo_id": photo_id, "status": "skipped", "reason": "file_not_found"}
                
                # 使用信号量控制并发提取特征（CPU密集型任务）
                async with semaphore:
                    # 异步执行特征提取（不涉及数据库操作）
                    features = await asyncio.to_thread(
                        image_feature_service.extract_features,
                        photo.original_path
                    )
                
                if features is None:
                    return {"photo_id": photo_id, "status": "error", "error": "特征提取失败"}
                
                # 返回特征数据（不在这里保存到数据库）
                return {
                    "photo_id": photo_id,
                    "status": "success",
                    "features": features
                }
                    
            except Exception as e:
                logger.error(f"处理照片 {photo_id} 失败: {str(e)}")
                return {"photo_id": photo_id, "status": "error", "error": str(e)}
        
        # 并发处理所有照片特征提取（不涉及数据库）
        logger.info(f"开始并发处理 {len(photo_ids)} 张照片，最大并发数: {max_concurrent_photos}")
        tasks = [process_single_photo_with_semaphore(photo_id) for photo_id in photo_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集提取成功的特征数据
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"任务执行异常: {str(result)}")
                failed_extractions += 1
                continue
            
            photo_id = result["photo_id"]
            all_processed_photos.add(photo_id)
            
            if result["status"] == "success" and "features" in result:
                # 收集特征数据，用于批量保存
                all_features_data.append({
                    "photo_id": photo_id,
                    "features": result["features"]
                })
                successful_extractions += 1
            elif result["status"] == "error":
                failed_extractions += 1
                image_feature_task_status[task_id]["error_details"].append({
                    "photo_id": photo_id,
                    "error": result.get("error", "未知错误")
                })
            elif result["status"] == "skipped":
                # 跳过的照片不计入失败
                pass
        
        # 🔥 批量保存所有特征到数据库（避免并发冲突）
        if all_features_data:
            saved_count = await asyncio.to_thread(
                image_feature_service.batch_save_features_to_db,
                all_features_data,
                db
            )
            logger.info(f"✅ 批量保存 {saved_count}/{len(all_features_data)} 个特征向量到数据库")
        
        # 注意：上下文管理器会在退出时自动 commit，这里不需要手动 commit
    
    # 更新任务状态（在上下文管理器外，不涉及数据库操作）
    image_feature_task_status[task_id]["completed_photos"] += successful_extractions
    image_feature_task_status[task_id]["failed_photos"] += failed_extractions
    image_feature_task_status[task_id]["processing_photos"] = (
        image_feature_task_status[task_id]["total_photos"] - 
        image_feature_task_status[task_id]["completed_photos"] - 
        image_feature_task_status[task_id]["failed_photos"]
    )
    image_feature_task_status[task_id]["progress_percentage"] = round(
        (image_feature_task_status[task_id]["completed_photos"] / 
         image_feature_task_status[task_id]["total_photos"]) * 100, 2
    )
    
    # 更新批次详情
    batch_details = image_feature_task_status[task_id]["batch_details"]
    if batch_idx < len(batch_details):
        batch_details[batch_idx]["completed_photos"] = successful_extractions
        batch_details[batch_idx]["failed_photos"] = failed_extractions
    
    logger.info(f"✅ 批次 {batch_idx + 1} 完成: 成功 {successful_extractions}, 失败 {failed_extractions}")


def get_image_feature_extraction_task_status(task_id: str) -> Dict:
    """
    获取任务状态
    
    :param task_id: 任务ID
    :return: 任务状态信息
    """
    return image_feature_task_status.get(task_id, {
        "status": "not_found",
        "message": "任务不存在"
    })

