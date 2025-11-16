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

# 任务状态存储（生产环境建议使用Redis）
task_status = {}




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
        
        # 限制并发数量，避免资源耗尽
        semaphore = asyncio.Semaphore(3)  # 最多同时处理3个文件
        
        async def process_single_file_with_semaphore(file: UploadFile, file_index: int):
            """使用信号量控制并发处理单个文件"""
            async with semaphore:
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
                            "message": "不支持的文件类型"
                        }

                    # 🔥 异步执行：保存临时文件（避免阻塞事件循环）
                    def save_temp_file():
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                            shutil.copyfileobj(file.file, temp_file)
                            return temp_file.name
                    
                    temp_path = await asyncio.to_thread(save_temp_file)

                    # 🔥 使用上下文管理器管理数据库会话（Python 最佳实践）
                    from app.db.session import get_db_context
                    with get_db_context() as task_db:
                        # 🔥 异步执行：处理单个照片（文件IO和图像处理都是阻塞操作）
                        # 传递清理后的文件名（只包含文件名，不包含路径），用于保存到数据库
                        success, message, photo_data, duplicate_info = await asyncio.to_thread(
                            import_service.process_single_photo,
                            temp_path, False, task_db, clean_filename  # move_file=False, db_session=task_db, original_filename=clean_filename
                        )

                        if success and photo_data:
                            # 阶段一：从返回值中提取质量分析和标签信息
                            quality_result = None
                            exif_tags = []
                            time_tags = []
                            
                            # duplicate_info可能是重复信息，也可能是additional_data（包含质量分析和标签）
                            if duplicate_info and isinstance(duplicate_info, dict):
                                # 检查是否是additional_data（包含质量分析和标签信息）
                                if 'quality_result' in duplicate_info or 'exif_tags' in duplicate_info or 'time_tags' in duplicate_info:
                                    quality_result = duplicate_info.get('quality_result')
                                    exif_tags = duplicate_info.get('exif_tags', [])
                                    time_tags = duplicate_info.get('time_tags', [])
                            
                            # 🔥 异步执行：保存到数据库（包括质量分析和标签）
                            # 简化逻辑：直接调用 create_photo，它内部已经处理了并发检查
                            def create_photo_record():
                                return photo_service.create_photo(
                                    task_db, 
                                    photo_data,
                                    quality_result=quality_result,
                                    exif_tags=exif_tags,
                                    time_tags=time_tags
                                )
                            
                            photo, is_new = await asyncio.to_thread(create_photo_record)
                            
                            # 注意：上下文管理器会在退出时自动 commit，这里不需要手动 commit
                            
                            if photo:
                                if is_new:
                                    # 新创建的文件
                                    print(f"成功导入: {clean_filename}")
                                    return {
                                        "file_index": file_index,
                                        "filename": clean_filename,
                                        "status": "imported",
                                        "message": "导入成功"
                                    }
                                else:
                                    # 已存在的文件（并发情况）
                                    return {
                                        "file_index": file_index,
                                        "filename": clean_filename,
                                        "status": "skipped",
                                        "message": "文件已存在，跳过导入"
                                    }
                            else:
                                return {
                                    "file_index": file_index,
                                    "filename": clean_filename,
                                    "status": "failed",
                                    "message": "数据库保存失败"
                                }
                        elif duplicate_info:
                            # 处理重复文件 - 使用完整的重复检测逻辑
                            duplicate_type = duplicate_info.get('duplicate_type', 'unknown')
                            message = duplicate_info.get('message', '文件重复')
                            
                            # 根据重复类型生成更详细的提示
                            if duplicate_type == 'full_duplicate':
                                status_text = f"文件已存在，跳过导入"
                                return {
                                    "file_index": file_index,
                                    "filename": clean_filename,
                                    "status": "skipped",
                                    "message": status_text
                                }
                            elif duplicate_type == 'physical_only':
                                status_text = f"文件已存在（物理重复）"
                                return {
                                    "file_index": file_index,
                                    "filename": clean_filename,
                                    "status": "imported",
                                    "message": status_text
                                }
                            elif duplicate_type == 'orphan_cleaned':
                                status_text = f"孤儿记录已清理，继续处理"
                                return {
                                    "file_index": file_index,
                                    "filename": clean_filename,
                                    "status": "imported",
                                    "message": status_text
                                }
                            else:
                                return {
                                    "file_index": file_index,
                                    "filename": clean_filename,
                                    "status": "failed",
                                    "message": message
                                }
                        else:
                            return {
                                "file_index": file_index,
                                "filename": clean_filename,
                                "status": "failed",
                                "message": message
                            }
                    
                    # 清理临时文件
                    if 'temp_path' in locals() and os.path.exists(temp_path):
                        os.unlink(temp_path)

                except Exception as e:
                    # 如果发生异常，尝试获取清理后的文件名，如果失败则使用原始文件名
                    clean_filename = Path(file.filename).name if hasattr(file, 'filename') and file.filename else "unknown"
                    return {
                        "file_index": file_index,
                        "filename": clean_filename,
                        "status": "failed",
                        "message": f"处理异常 - {str(e)}"
                    }
        
        # 并发执行所有文件处理任务
        try:
            tasks = [process_single_file_with_semaphore(file, i) for i, file in enumerate(files)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            imported_count = 0
            skipped_count = 0
            failed_count = 0
            failed_files = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_count += 1
                    failed_files.append(f"处理异常: {str(result)}")
                    continue
                    
                if result["status"] == "imported":
                    imported_count += 1
                elif result["status"] == "skipped":
                    skipped_count += 1
                elif result["status"] == "failed":
                    failed_count += 1
                    failed_files.append(f"{result['filename']}: {result['message']}")
            
            # 🔥 注意：每个任务已经使用独立的数据库会话并提交，这里不需要再次提交
            
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
            
            print(f"并发处理完成: 导入{imported_count}个，跳过{skipped_count}个，失败{failed_count}个")

        except Exception as e:
            # 🔥 注意：每个任务已经使用独立的数据库会话，不需要共享会话的回滚
            task_status[task_id].update({
                "status": "failed",
                "end_time": datetime.now().isoformat(),
                "error": str(e)
            })
            print(f"并发处理失败: {str(e)}")

    except Exception as e:
        # 处理整个函数级别的异常
        task_status[task_id] = {
            "status": "failed",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        }
        print(f"任务初始化失败: {str(e)}")
