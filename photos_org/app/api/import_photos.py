"""
照片导入API

提供照片文件导入、文件夹扫描、元数据提取等功能的API接口

作者：AI助手
创建日期：2025年9月9日
"""

import os
import shutil
import tempfile
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import get_db
from app.models.photo import Photo
from app.services.import_service import ImportService
from app.services.photo_service import PhotoService

router = APIRouter()
logger = logging.getLogger(__name__)

# 任务状态存储（生产环境建议使用Redis）
task_status = {}

# 🔥 全局批次信号量：限制所有批次的总并发数（解决多批次并发导致资源耗尽问题）
# 在模块加载时初始化，使用配置的默认值（会在函数中动态更新）
_global_batch_semaphore: Optional[asyncio.Semaphore] = None
_global_batch_semaphore_initial_value: Optional[int] = None  # 保存信号量的初始值，用于判断是否需要重新创建


def get_global_batch_semaphore() -> asyncio.Semaphore:
    """
    获取全局批次信号量（懒加载，使用最新配置）
    
    每次调用时都会读取最新配置，确保配置更新后能立即生效。
    参考人脸识别的实现方式：使用 get_settings() 获取配置（如果调用了 reload_settings() 会重新加载）。
    
    :return: 全局批次信号量
    """
    global _global_batch_semaphore, _global_batch_semaphore_initial_value
    from app.core.config import get_settings
    # 🔥 每次调用都获取最新配置（如果调用了 reload_settings()，get_settings() 会返回重新加载的配置）
    current_settings = get_settings()
    max_concurrent_batches = current_settings.import_config.max_concurrent_batches
    
    # 🔥 修复：使用保存的初始值来判断，而不是使用 _value（_value 会随着使用而变化）
    # 如果信号量不存在或配置已更改，重新创建
    # 注意：如果用户修改了 config.json 但没有调用 reload_settings()，这里不会检测到更改
    # 但这是预期的行为，因为配置更新需要通过 API 或调用 reload_settings() 才能生效
    if _global_batch_semaphore is None or _global_batch_semaphore_initial_value != max_concurrent_batches:
        _global_batch_semaphore = asyncio.Semaphore(max_concurrent_batches)
        _global_batch_semaphore_initial_value = max_concurrent_batches  # 保存初始值
        logger.info(f"全局批次信号量已初始化/更新: 最多 {max_concurrent_batches} 个批次同时运行")
    
    return _global_batch_semaphore




@router.post("/upload")
async def upload_photos(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    上传照片文件

    :param files: 上传的文件列表
    :param background_tasks: 后台任务
    :param db: 数据库会话
    :return: 上传结果
    """
    if not files:
        raise HTTPException(status_code=400, detail="未选择文件")

    if len(files) > settings.import_config.max_upload_files:  # 限制单次上传数量
        raise HTTPException(status_code=400, detail=f"单次最多上传{settings.import_config.max_upload_files}个文件")

    try:
        # 统一使用后台任务处理
        import uuid
        task_id = str(uuid.uuid4())
        background_tasks.add_task(process_photos_batch_with_status_from_upload, files, db, task_id)

        return JSONResponse(
            status_code=202,
            content={
                "success": True,
                "message": f"已提交{len(files)}个文件进行后台处理",
                "data": {
                    "task_id": task_id,
                    "total_files": len(files),
                    "status": "processing"
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/process-single")
async def process_single_file(
    file_path: str,
    db: Session = Depends(get_db)
):
    """
    处理单个照片文件

    :param file_path: 文件路径
    :param db: 数据库会话
    """
    try:
        import_service = ImportService()
        photo_service = PhotoService()

        # 处理照片
        success, message, photo_data, duplicate_info = import_service.process_single_photo(file_path, db_session=db)

        if success and photo_data:
            # 保存到数据库
            photo, is_new = photo_service.create_photo(db, photo_data)
            
            if photo:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "照片处理成功" if is_new else "照片已存在",
                        "data": {
                            "photo_id": photo.id,
                            "filename": photo.filename,
                            "file_size": photo.file_size,
                            "width": photo.width,
                            "height": photo.height
                        }
                    }
                )
            else:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": False,
                        "message": "数据库保存失败"
                    }
                )
        elif duplicate_info:
            # 处理重复文件 - 改为统一响应格式，不抛出异常
            duplicate_type = duplicate_info.get('duplicate_type', 'unknown')
            message = duplicate_info.get('message', '文件重复')
            
            # 根据重复类型生成更详细的提示
            if duplicate_type == 'full_duplicate':
                status_text = f"文件已存在，跳过导入"
            elif duplicate_type == 'physical_only':
                status_text = f"文件已存在（物理重复）"
            elif duplicate_type == 'orphan_cleaned':
                status_text = f"孤儿记录已清理，继续处理"
            else:
                status_text = message
            
            # 返回统一的响应格式，包含重复信息
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "文件重复",
                    "data": {
                        "duplicate_type": duplicate_type,
                        "duplicate_message": status_text,
                        "filename": Path(file_path).name
                    }
                }
            )
        else:
            # 其他错误情况也改为统一响应格式
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "处理失败",
                    "data": {
                        "error_message": message,
                        "filename": Path(file_path).name
                    }
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"照片处理失败: {str(e)}")


@router.get("/supported-formats")
async def get_supported_formats():
    """
    获取支持的文件格式
    """
    import_service = ImportService()

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "formats": import_service.SUPPORTED_FORMATS,
                "mimetypes": import_service.SUPPORTED_MIMETYPES,
                "max_file_size": settings.system.max_file_size
            }
        }
    )


@router.get("/import-status")
async def get_import_status():
    """
    获取导入状态（预留接口，后续实现）
    """
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": "导入服务正常运行",
            "data": {
                "status": "idle",
                "processed_today": 0,
                "queue_length": 0
            }
        }
    )






@router.get("/scan-status/{task_id}")
async def get_scan_status(task_id: str):
    """
    获取扫描任务状态

    :param task_id: 任务ID
    """
    print(f"查询任务状态: {task_id}")
    # print(f"当前任务状态: {task_status}")

    if task_id not in task_status:
        print(f"任务 {task_id} 不存在")
        raise HTTPException(status_code=404, detail="任务不存在")

    # print(f"任务 {task_id} 状态: {task_status[task_id]}")
    return task_status[task_id]


@router.post("/batch-status")
async def get_batch_status(task_ids: List[str]):
    """
    获取多个批次任务的聚合状态

    :param task_ids: 任务ID列表
    :return: 批次聚合状态
    """
    print(f"查询批次状态，任务数量: {len(task_ids)}")

    if not task_ids:
        raise HTTPException(status_code=400, detail="任务ID列表不能为空")

    batch_results = []
    total_files = 0
    total_processed = 0
    total_imported = 0
    total_skipped = 0
    total_failed = 0
    failed_files = []
    completed_tasks = 0

    for task_id in task_ids:
        if task_id in task_status:
            task_data = task_status[task_id]
            batch_results.append({
                "task_id": task_id,
                "status": task_data.get("status", "unknown"),
                "total_files": task_data.get("total_files", 0),
                "processed_files": task_data.get("processed_files", 0),
                "imported_count": task_data.get("imported_count", 0),
                "skipped_count": task_data.get("skipped_count", 0),
                "failed_count": task_data.get("failed_count", 0),
                "failed_files": task_data.get("failed_files", []),
                "progress_percentage": task_data.get("progress_percentage", 0)
            })

            # 累积统计
            total_files += task_data.get("total_files", 0)
            total_processed += task_data.get("processed_files", 0)
            total_imported += task_data.get("imported_count", 0)
            total_skipped += task_data.get("skipped_count", 0)
            total_failed += task_data.get("failed_count", 0)
            failed_files.extend(task_data.get("failed_files", []))

            if task_data.get("status") == "completed":
                completed_tasks += 1
        else:
            # 任务不存在，视为失败
            batch_results.append({
                "task_id": task_id,
                "status": "not_found",
                "error": "任务不存在"
            })

    # 计算总体状态
    overall_status = "completed" if completed_tasks == len(task_ids) else "processing"
    overall_progress = (completed_tasks / len(task_ids) * 100) if task_ids else 0

    result = {
        "overall_status": overall_status,
        "overall_progress_percentage": round(overall_progress, 1),
        "completed_tasks": completed_tasks,
        "total_tasks": len(task_ids),
        "total_files": total_files,
        "total_processed_files": total_processed,
        "total_imported_count": total_imported,
        "total_skipped_count": total_skipped,
        "total_failed_count": total_failed,
        "failed_files": failed_files,
        "task_details": batch_results
    }

    print(f"批次聚合状态: {completed_tasks}/{len(task_ids)} 完成，总体进度: {overall_progress}%")
    return result


async def process_photos_batch_with_status_from_upload(files: List[UploadFile], db, task_id: str):
    """
    带状态跟踪的处理上传文件 - 使用asyncio并发处理
    
    :param files: 上传的文件列表
    :param db: 数据库会话
    :param task_id: 任务ID
    """
    # 🔥 全局批次信号量：限制所有批次的总并发数
    global_batch_semaphore = get_global_batch_semaphore()
    
    # 获取批次内文件并发数配置和临时文件目录
    from app.core.config import get_settings
    from app.core.path_utils import resolve_resource_path
    current_settings = get_settings()
    max_concurrent_photos = current_settings.import_config.max_concurrent_photos
    
    # 🔥 获取配置的临时文件目录（使用 resolve_resource_path 解析路径）
    storage_base = resolve_resource_path(current_settings.storage.base_path)
    temp_dir = storage_base / current_settings.storage.temp_path / "uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 先获取全局批次信号量，确保不会超过总并发批次限制
    async with global_batch_semaphore:
        logger.info(f"批次 {task_id} 已获取全局批次信号量，开始处理 {len(files)} 个文件")
        
        try:
            # 初始化任务状态
            task_status[task_id] = {
                "status": "processing",
                "total_files": len(files),
                "processed_files": 0,
                "imported_count": 0,
                "skipped_count": 0,
                "failed_count": 0,
                "failed_files": [],
                "progress_percentage": 0,
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "error": None
            }
            
            import_service = ImportService()
            photo_service = PhotoService()
            
            # 🔥 批次内文件信号量：限制单个批次内的文件并发数
            batch_photo_semaphore = asyncio.Semaphore(max_concurrent_photos)
            logger.info(f"批次 {task_id} 内最大并发文件数: {max_concurrent_photos}")
            
            async def process_single_file_with_semaphore(file: UploadFile, file_index: int):
                """
                使用信号量控制并发处理单个文件（不占用数据库连接）
                只处理文件，不涉及数据库操作
                """
                async with batch_photo_semaphore:
                    try:
                        # 清理文件名：移除可能包含的路径前缀（文件夹导入时可能有相对路径）
                        # 例如：file.filename 可能是 "heic_all/南京2023001.heic"，需要提取为 "南京2023001.heic"
                        clean_filename = Path(file.filename).name
                        file_ext = Path(clean_filename).suffix.lower()
                        
                        # 特殊处理HEIC格式
                        if file_ext in ['.heic', '.heif']:
                            # HEIC格式的content_type可能为空，需要特殊处理
                            pass
                        elif not file.content_type or not file.content_type.startswith('image/'):
                            return {
                                "file_index": file_index,
                                "filename": clean_filename,
                                "status": "failed",
                                "message": "不支持的文件类型",
                                "temp_path": None
                            }

                        # 🔥 异步执行：保存临时文件到配置的临时目录（避免阻塞事件循环）
                        def save_temp_file():
                            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, dir=str(temp_dir)) as temp_file:
                                shutil.copyfileobj(file.file, temp_file)
                                return temp_file.name
                        
                        temp_path = await asyncio.to_thread(save_temp_file)

                        # 🔥 关键改进：处理文件时不占用数据库连接（参考人脸识别和特征提取的模式）
                        # 传递 db_session=None，跳过重复检查（在批量阶段统一检查）
                        success, message, photo_data, additional_data = await asyncio.to_thread(
                            import_service.process_single_photo,
                            temp_path, False, None, clean_filename  # move_file=False, db_session=None, original_filename=clean_filename
                        )

                        # 返回处理结果，包含所有需要的信息
                        return {
                            "file_index": file_index,
                            "filename": clean_filename,
                            "temp_path": temp_path,  # 保存临时文件路径，用于后续清理
                            "success": success,
                            "message": message,
                            "photo_data": photo_data,
                            "additional_data": additional_data  # 包含 quality_result, exif_tags, time_tags
                        }

                    except Exception as e:
                        # 如果发生异常，尝试获取清理后的文件名，如果失败则使用原始文件名
                        clean_filename = Path(file.filename).name if hasattr(file, 'filename') and file.filename else "unknown"
                        return {
                            "file_index": file_index,
                            "filename": clean_filename,
                            "temp_path": None,
                            "success": False,
                            "message": f"处理异常 - {str(e)}",
                            "photo_data": None,
                            "additional_data": None
                        }
            
            # 🔥 批次提交模式：参考人脸识别和特征提取的实现
            # 阶段1：并发处理所有文件（不占用数据库连接）
            try:
                logger.info(f"开始并发处理 {len(files)} 个文件，最大并发数: {max_concurrent_photos}")
                tasks = [process_single_file_with_semaphore(file, i) for i, file in enumerate(files)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 阶段2：批量检查重复和批量保存到数据库（需要数据库，但很快）
                from app.db.session import get_db_context
                from app.models.photo import Photo
                
                # 收集所有成功处理的文件数据
                all_photo_data = []  # 存储待保存的照片数据
                all_temp_paths = []  # 存储临时文件路径，用于后续清理
                failed_results = []  # 存储失败的结果
                
                for result in results:
                    if isinstance(result, Exception):
                        failed_results.append({
                            "file_index": -1,
                            "filename": "unknown",
                            "status": "failed",
                            "message": f"处理异常: {str(result)}",
                            "temp_path": None
                        })
                        continue
                    
                    if not result.get("success"):
                        # 处理失败的文件
                        failed_results.append({
                            "file_index": result.get("file_index"),
                            "filename": result.get("filename"),
                            "status": "failed",
                            "message": result.get("message", "处理失败"),
                            "temp_path": result.get("temp_path")
                        })
                        continue
                    
                    photo_data = result.get("photo_data")
                    if not photo_data:
                        failed_results.append({
                            "file_index": result.get("file_index"),
                            "filename": result.get("filename"),
                            "status": "failed",
                            "message": "照片数据为空",
                            "temp_path": result.get("temp_path")
                        })
                        continue
                    
                    # 收集成功处理的文件数据
                    all_photo_data.append({
                        "file_index": result.get("file_index"),
                        "filename": result.get("filename"),
                        "photo_data": photo_data,
                        "additional_data": result.get("additional_data"),
                        "temp_path": result.get("temp_path")
                    })
                
                # 🔥 批量检查重复（需要数据库，但很快）
                logger.info(f"批量检查 {len(all_photo_data)} 个文件的重复情况...")
                with get_db_context() as check_db:
                    # 批量查询所有文件哈希
                    file_hashes = [data["photo_data"].file_hash for data in all_photo_data]
                    existing_photos = check_db.query(Photo).filter(Photo.file_hash.in_(file_hashes)).all()
                    existing_hashes = {photo.file_hash for photo in existing_photos}
                
                # 分离重复和新文件
                duplicate_data = []
                new_photo_data = []
                
                for data in all_photo_data:
                    if data["photo_data"].file_hash in existing_hashes:
                        duplicate_data.append(data)
                    else:
                        new_photo_data.append(data)
                
                logger.info(f"重复文件: {len(duplicate_data)} 个，新文件: {len(new_photo_data)} 个")
                
                # 阶段3：批量保存新文件到数据库（需要数据库，但很快）
                imported_count = 0
                skipped_count = len(duplicate_data)
                failed_count = len(failed_results)
                failed_files = []
                
                if new_photo_data:
                    logger.info(f"批量保存 {len(new_photo_data)} 个新文件到数据库...")
                    with get_db_context() as save_db:
                        for data in new_photo_data:
                            try:
                                # 提取质量分析和标签信息
                                additional_data = data.get("additional_data", {})
                                quality_result = additional_data.get('quality_result') if isinstance(additional_data, dict) else None
                                exif_tags = additional_data.get('exif_tags', []) if isinstance(additional_data, dict) else []
                                time_tags = additional_data.get('time_tags', []) if isinstance(additional_data, dict) else []
                                
                                # 保存到数据库（批次模式，不自动提交）
                                photo, is_new = photo_service.create_photo(
                                    save_db,
                                    data["photo_data"],
                                    quality_result=quality_result,
                                    exif_tags=exif_tags,
                                    time_tags=time_tags,
                                    auto_commit=False  # 批次模式，由上下文管理器统一提交
                                )
                                
                                if photo and is_new:
                                    imported_count += 1
                                    logger.debug(f"成功导入: {data['filename']}")
                                else:
                                    # 并发情况下可能已存在
                                    skipped_count += 1
                                    logger.debug(f"文件已存在（并发情况）: {data['filename']}")
                                    
                            except Exception as e:
                                failed_count += 1
                                error_msg = f"{data['filename']}: {str(e)}"
                                failed_files.append(error_msg)
                                logger.error(f"保存文件失败 {error_msg}")
                        
                        # 注意：上下文管理器会在退出时自动 commit，这里不需要手动 commit
                        logger.info(f"✅ 批量提交成功: 导入 {imported_count} 个，跳过 {skipped_count} 个，失败 {failed_count} 个")
                
                # 处理重复文件（标记为跳过，不是失败）
                for data in duplicate_data:
                    # 重复文件不计入失败，只记录到 failed_files 用于日志
                    failed_files.append(f"{data['filename']}: 文件已存在，跳过导入")
                
                # 处理失败的文件
                for result in failed_results:
                    failed_files.append(f"{result.get('filename', 'unknown')}: {result.get('message', '处理失败')}")
                
                # 清理临时文件
                all_temp_paths = [data.get("temp_path") for data in all_photo_data + failed_results if data.get("temp_path")]
                for temp_path in all_temp_paths:
                    try:
                        if temp_path and os.path.exists(temp_path):
                            os.unlink(temp_path)
                    except Exception as e:
                        logger.warning(f"清理临时文件失败 {temp_path}: {str(e)}")
                
                # 更新最终状态
                task_status[task_id].update({
                    "status": "completed",
                    "end_time": datetime.now().isoformat(),
                    "processed_files": len(files),
                    "imported_count": imported_count,
                    "skipped_count": skipped_count,
                    "failed_count": failed_count,
                    "failed_files": failed_files,
                    "progress_percentage": 100
                })
                
                logger.info(f"批次处理完成: 导入 {imported_count} 个，跳过 {skipped_count} 个，失败 {failed_count} 个")
                
                # 延迟清理任务状态，避免内存泄漏
                async def cleanup_task_status():
                    await asyncio.sleep(8 * 3600)  # 延迟8小时清理
                    if task_id in task_status:
                        del task_status[task_id]
                        logger.info(f"清理已完成的任务状态: {task_id}")
                
                # 启动后台清理任务
                asyncio.create_task(cleanup_task_status())

            except Exception as e:
                # 🔥 批次提交模式：异常会在上下文管理器中自动回滚
                logger.error(f"批次处理失败: {str(e)}", exc_info=True)
                task_status[task_id].update({
                    "status": "failed",
                    "end_time": datetime.now().isoformat(),
                    "error": str(e)
                })

        except Exception as e:
            # 处理整个函数级别的异常（包括获取全局信号量失败等）
            logger.error(f"批次任务初始化失败: {str(e)}", exc_info=True)
            task_status[task_id] = {
                "status": "failed",
                "error": str(e),
                "end_time": datetime.now().isoformat()
            }
