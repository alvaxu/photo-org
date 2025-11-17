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
from app.models.face import FaceDetection, FaceCluster, FaceClusterMember, Person
from app.models.photo import Photo
from app.services.face_recognition_service import face_service
from app.services.face_cluster_service import cluster_service

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
            "skipped_photos": 0,  # 🔥 新增：跳过的照片（如GIF格式）
            "progress_percentage": 0.0,
            "start_time": datetime.now(),
            "current_batch": 0,
            "total_batches": 0,
            "completed_batches": 0,
            "failed_batches": 0,
            "processing_photos": len(photo_ids),
            "error": None,
            "error_details": [],  # 新增：记录具体错误信息
            "batch_details": []   # 新增：批次详情信息
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
        
        # 🔥 关键改进：真正的分批处理
        batch_size = settings.face_recognition.batch_size
        max_concurrent_batches = settings.face_recognition.max_concurrent_batches
        
        total_batches = (len(photo_ids) + batch_size - 1) // batch_size
        
        # 更新任务状态
        face_recognition_task_status[task_id]["total_batches"] = total_batches
        
        logger.info(f"分批处理: 总批次数 {total_batches}, 每批 {batch_size} 张照片")
        
        # 分批处理照片
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(photo_ids))
            batch_photo_ids = photo_ids[start_idx:end_idx]
            
            logger.info(f"处理批次 {batch_idx + 1}/{total_batches}, 照片数量: {len(batch_photo_ids)}")
            
            # 更新当前批次状态
            face_recognition_task_status[task_id]["current_batch"] = batch_idx + 1
            
            # 🔥 新增：记录批次详情
            batch_detail = {
                "batch_index": batch_idx + 1,
                "total_photos": len(batch_photo_ids),
                "completed_photos": 0,
                "failed_photos": 0,
                "skipped_photos": 0,  # 🔥 新增：跳过的照片（如GIF格式）
                "faces_detected": 0,
                "status": "processing",
                "error": None,
                "completed_at": None
            }
            face_recognition_task_status[task_id]["batch_details"].append(batch_detail)
            
            try:
                # 处理当前批次
                await process_face_recognition_batch(task_id, batch_photo_ids, batch_idx)
                
                # 🔥 新增：更新批次完成状态
                face_recognition_task_status[task_id]["completed_batches"] = batch_idx + 1
                batch_detail["status"] = "completed"
                batch_detail["completed_photos"] = len(batch_photo_ids)
                batch_detail["completed_at"] = datetime.now().isoformat()
                
            except Exception as e:
                # 🔥 新增：处理批次失败状态
                face_recognition_task_status[task_id]["failed_batches"] += 1
                batch_detail["status"] = "failed"
                batch_detail["failed_photos"] = len(batch_photo_ids)
                batch_detail["error"] = str(e)
                batch_detail["completed_at"] = datetime.now().isoformat()
                raise
            
            # 批次间短暂延迟，避免资源竞争
            if batch_idx < total_batches - 1:
                await asyncio.sleep(0.1)
        
        # 🔥 移除自动聚类逻辑，改为由用户手动触发
        # 完成后不再自动执行聚类
        # logger.info("开始执行人脸聚类...")
        # await perform_face_clustering(task_id)
        
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

async def process_face_recognition_batch(task_id: str, photo_ids: List[int], batch_idx: int = 0):
    """
    处理人脸识别批次（优化版：批量数据库操作）
    :param task_id: 任务ID
    :param photo_ids: 照片ID列表
    :param batch_idx: 批次索引
    """
    # 🔥 修复：在try外初始化变量，避免作用域问题
    all_detection_results = []  # 包含检测结果和人数信息
    all_processed_photos = set()
    results = []
    total_faces_detected = 0
    
    # 🔥 使用上下文管理器管理数据库会话（Python 最佳实践）
    from app.db.session import get_db_context
    with get_db_context() as db:
        # 🔥 性能优化：批量预查询所有照片信息（避免并发时创建过多数据库会话）
        logger.info(f"批量预查询 {len(photo_ids)} 张照片信息...")
        def batch_query_photos():
            photos = db.query(Photo).filter(Photo.id.in_(photo_ids)).all()
            return {photo.id: photo for photo in photos}
        
        photo_cache = await asyncio.to_thread(batch_query_photos)
        logger.info(f"成功预查询 {len(photo_cache)} 张照片信息")
        
        # 使用信号量控制单批次内的并发数
        max_concurrent_photos = settings.face_recognition.max_concurrent_photos
        semaphore = asyncio.Semaphore(max_concurrent_photos)
        logger.info(f"单批次内最大并发照片数: {max_concurrent_photos}")
        
        async def process_single_photo_with_semaphore(photo_id: int):
            """使用信号量控制并发处理单张照片（只控制人脸检测部分）"""
            try:
                # 🔥 从缓存获取照片信息（不再为每个任务创建数据库会话）
                photo = photo_cache.get(photo_id)
                
                if not photo:
                    return {"photo_id": photo_id, "status": "skipped", "reason": "photo_not_found"}
                
                # 构建完整路径（使用最新配置）
                from app.core.config import get_settings
                from app.core.path_utils import resolve_resource_path
                current_settings = get_settings()
                storage_base = resolve_resource_path(current_settings.storage.base_path)
                full_path = storage_base / photo.original_path
                
                # 🔥 异步执行：文件检查（避免阻塞事件循环）
                file_exists = await asyncio.to_thread(full_path.exists)
                
                if not file_exists:
                    logger.warning(f"照片文件不存在: {full_path}")
                    return {"photo_id": photo_id, "status": "skipped", "reason": "file_not_found"}
                
                # 🔥 关键：只有人脸检测部分使用信号量控制并发
                async with semaphore:
                    detection_result = await face_service.detect_faces_in_photo(str(full_path), photo_id)
                
                # 🔥 检查是否因为格式问题跳过（如GIF格式）
                if detection_result.get('skipped', False):
                    skip_reason = detection_result.get('skip_reason', 'unknown')
                    return {
                        "photo_id": photo_id,
                        "status": "skipped",
                        "reason": skip_reason,
                        "detections": detection_result.get('detections', []),
                        "real_face_count": detection_result.get('real_face_count', 0)
                    }
                
                return {
                    "photo_id": photo_id, 
                    "status": "success", 
                    "detections": detection_result['detections'],
                    "real_face_count": detection_result['real_face_count']
                }
                
            except Exception as e:
                logger.error(f"处理照片 {photo_id} 失败: {str(e)}")
                return {"photo_id": photo_id, "status": "error", "error": str(e)}
        
        # 🔥 关键改进：并发执行所有人脸识别任务（不涉及数据库）
        logger.info(f"开始并发处理 {len(photo_ids)} 张照片，最大并发数: {max_concurrent_photos}")
        tasks = [process_single_photo_with_semaphore(photo_id) for photo_id in photo_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 🔥 新增：批量数据库操作（变量已在函数开头初始化）
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"任务执行异常: {str(result)}")
                continue
                
            photo_id = result["photo_id"]
            all_processed_photos.add(photo_id)  # 所有照片都标记为已处理
            
            if result["status"] == "success" and "detections" in result:
                # 构建包含人数信息的检测结果
                detection_result = {
                    'photo_id': photo_id,
                    'detections': result["detections"],
                    'real_face_count': result["real_face_count"]
                }
                all_detection_results.append(detection_result)
        
        # 🔥 批量保存到数据库（包含人数信息）
        if all_detection_results:
            await face_service.batch_save_face_detections(all_detection_results, db)
        
        if all_processed_photos:
            await face_service.batch_mark_photos_as_processed(all_processed_photos, db)
        
        # 注意：上下文管理器会在退出时自动 commit，这里不需要手动 commit
        
        # 统计人脸数量（已在函数开头初始化total_faces_detected）
        if all_detection_results:
            total_faces_detected = sum(result['real_face_count'] for result in all_detection_results)
            total_faces_processed = sum(len(result['detections']) for result in all_detection_results)
            logger.info(f"✅ 批次 {batch_idx + 1} 批量提交成功: 检测到 {total_faces_detected} 个人脸，处理了 {total_faces_processed} 个，{len(all_processed_photos)} 张照片")
        
        # 处理结果和更新状态
        successful_analyses = 0
        failed_analyses = 0
        skipped_analyses = 0  # 🔥 新增：统计跳过的照片（如GIF格式）
        
        for result in results:
            if isinstance(result, Exception):
                failed_analyses += 1
                logger.error(f"任务执行异常: {str(result)}")
                # 记录错误详情
                face_recognition_task_status[task_id]["error_details"].append({
                    "error": str(result),
                    "error_type": "task_exception",
                    "timestamp": datetime.now().isoformat()
                })
                continue
                
            if result["status"] == "success":
                successful_analyses += 1
            elif result["status"] == "error":
                failed_analyses += 1
                # 记录错误详情
                face_recognition_task_status[task_id]["error_details"].append({
                    "photo_id": result["photo_id"],
                    "error": result["error"],
                    "error_type": "face_detection_error",
                    "timestamp": datetime.now().isoformat()
                })
            elif result["status"] == "skipped":
                # 🔥 新增：GIF格式等跳过的文件，不被算作成功
                skipped_analyses += 1
                skip_reason = result.get("reason", "unknown")
                logger.info(f"跳过照片 {result.get('photo_id')}: {skip_reason}")
        
        # 🔥 优化：更新任务状态（包含人脸检测数量）
        face_recognition_task_status[task_id]["completed_photos"] += successful_analyses
        face_recognition_task_status[task_id]["failed_photos"] += failed_analyses
        face_recognition_task_status[task_id]["skipped_photos"] += skipped_analyses  # 🔥 新增：统计跳过的照片
        face_recognition_task_status[task_id]["processing_photos"] = (
            face_recognition_task_status[task_id]["total_photos"] - 
            face_recognition_task_status[task_id]["completed_photos"] - 
            face_recognition_task_status[task_id]["failed_photos"] -
            face_recognition_task_status[task_id]["skipped_photos"]  # 🔥 新增：跳过的照片也不计入处理中
        )
        face_recognition_task_status[task_id]["progress_percentage"] = round(
            (face_recognition_task_status[task_id]["completed_photos"] / 
             face_recognition_task_status[task_id]["total_photos"]) * 100, 2
        )
        
        # 🔥 修复：更新批次详情的人脸检测数量
        # 找到对应的批次详情并更新人脸检测数量
        batch_details = face_recognition_task_status[task_id]["batch_details"]
        if batch_idx < len(batch_details):
            # total_faces_detected已在try块内更新
            batch_details[batch_idx]["faces_detected"] = total_faces_detected
            batch_details[batch_idx]["completed_photos"] = successful_analyses
            batch_details[batch_idx]["failed_photos"] = failed_analyses
            batch_details[batch_idx]["skipped_photos"] = skipped_analyses  # 🔥 新增：批次的跳过统计
        
        logger.info(f"✅ 批次 {batch_idx + 1} 完成: 成功 {successful_analyses}, 失败 {failed_analyses}, 跳过 {skipped_analyses}, 检测到 {total_faces_detected} 个人脸")

async def perform_face_clustering(task_id: str):
    """
    执行人脸聚类（参考基础分析的perform_clustering）
    :param task_id: 任务ID（用于增量聚类识别新人脸）
    """
    # 🔥 使用上下文管理器管理数据库会话（Python 最佳实践）
    from app.db.session import get_db_context
    with get_db_context() as db:
        # 执行聚类（传入task_id以支持增量聚类）
        await cluster_service.cluster_faces(db, task_id=task_id)
        
        logger.info(f"人脸聚类完成")

async def cleanup_task_status(task_id: str):
    """
    清理任务状态（参考基础分析的cleanup_task_status）
    :param task_id: 任务ID
    """
    try:
        # 延迟8小时后清理任务状态
        await asyncio.sleep(8 * 3600)  # 8小时
        
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
            
            # 确保processing_photos字段存在（需要减去已完成的、失败的、跳过的）
            if "processing_photos" not in status:
                skipped = status.get("skipped_photos", 0)
                status["processing_photos"] = (
                    status["total_photos"] - 
                    status["completed_photos"] - 
                    status["failed_photos"] -
                    skipped
                )
            # 确保skipped_photos字段存在（向后兼容）
            if "skipped_photos" not in status:
                status["skipped_photos"] = 0
            
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
