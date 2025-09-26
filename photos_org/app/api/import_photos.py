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


@router.post("/scan-folder")
async def scan_folder(
    folder_path: str,
    recursive: bool = True,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    扫描文件夹导入照片

    :param folder_path: 文件夹路径
    :param recursive: 是否递归扫描子文件夹
    :param background_tasks: 后台任务
    :param db: 数据库会话
    """
    try:
        import_service = ImportService()

        # 扫描文件夹
        photo_files = import_service.scan_folder(folder_path, recursive)

        if not photo_files:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "未找到支持的照片文件",
                    "data": {
                        "scanned_files": 0,
                        "imported_photos": 0
                    }
                }
            )

        # 如果文件数量较大，放到后台处理
        if len(photo_files) > settings.import_config.max_upload_files:
            # 创建后台任务ID，用于状态跟踪
            import uuid
            task_id = str(uuid.uuid4())
            background_tasks.add_task(process_photos_batch_with_status, photo_files, db, task_id)

            return JSONResponse(
                status_code=202,
                content={
                    "success": True,
                    "message": f"发现{len(photo_files)}个照片文件，已提交后台处理",
                    "data": {
                        "scanned_files": len(photo_files),
                        "status": "processing",
                        "task_id": task_id
                    }
                }
            )

        # 小批量直接处理
        imported_count, skipped_count, failed_count, failed_files = await process_photos_batch(photo_files, db)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"成功导入{imported_count}张照片",
                "data": {
                    "total_files": len(photo_files),
                    "imported_photos": imported_count,
                    "skipped_photos": skipped_count,
                    "failed_photos": failed_count,
                    "failed_files": failed_files
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件夹扫描失败: {str(e)}")


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
            photo = photo_service.create_photo(db, photo_data)

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "照片处理成功",
                    "data": {
                        "photo_id": photo.id,
                        "filename": photo.filename,
                        "file_size": photo.file_size,
                        "width": photo.width,
                        "height": photo.height
                    }
                }
            )
        elif duplicate_info:
            # 处理重复文件 - 改为统一响应格式，不抛出异常
            duplicate_type = duplicate_info.get('duplicate_type', 'unknown')
            message = duplicate_info.get('message', '文件重复')
            
            # 根据重复类型生成更详细的提示
            if duplicate_type == 'full_duplicate_completed':
                status_text = f"文件已存在且已完成智能处理"
            elif duplicate_type == 'full_duplicate_incomplete':
                status_text = f"文件已存在但未完成智能处理 - 将重新处理"
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


async def process_photos_batch(photo_files: List[str], db) -> Tuple[int, int, int, List[str]]:
    """
    智能处理照片文件

    :param photo_files: 照片文件路径列表
    :param db: 数据库会话
    :return: (成功导入的数量, 无需导入的数量, 失败的数量, 失败文件列表)
    """
    import_service = ImportService()
    photo_service = PhotoService()
    imported_count = 0
    skipped_count = 0
    failed_count = 0
    failed_files = []

    for file_path in photo_files:
        try:
            # 处理单个照片（文件夹扫描时复制文件，不移动）
            success, message, photo_data, duplicate_info = import_service.process_single_photo(file_path, move_file=False, db_session=db)

            if success and photo_data:
                # 保存到数据库
                photo = photo_service.create_photo(db, photo_data)
                if photo:
                    imported_count += 1
                    print(f"成功导入: {file_path}")
                else:
                    failed_files.append(f"{file_path}: 数据库保存失败")
                    print(f"数据库保存失败: {file_path}")
            elif duplicate_info:
                # 处理重复文件 - 按照重复图片处理逻辑.md的完整逻辑
                duplicate_type = duplicate_info.get('duplicate_type', 'unknown')
                message = duplicate_info.get('message', '文件重复')
                
                if duplicate_type == 'full_duplicate_completed':
                    # 情况1.1：完全重复且已完成智能处理 - 无需导入
                    status_text = f"文件已存在且已完成智能处理"
                    skipped_count += 1
                    print(f"跳过重复文件: {file_path} - {status_text}")
                    
                elif duplicate_type == 'full_duplicate_incomplete':
                    # 情况1.2：完全重复但未完成智能处理 - 继续智能处理
                    status_text = f"文件已存在但未完成智能处理 - 将重新处理"
                    print(f"继续处理重复文件: {file_path} - {status_text}")
                    # 注意：这里不需要创建新的数据库记录，因为记录已存在
                    # 只需要确保状态正确，让后续的智能处理来处理
                    skipped_count += 1  # 重复文件，计入跳过
                    
                elif duplicate_type == 'orphan_cleaned':
                    # 情况2：孤儿记录 - 清理后继续正常处理
                    status_text = f"孤儿记录已清理，继续处理"
                    print(f"孤儿记录已清理: {file_path} - {status_text}")
                    # 孤儿记录清理后，应该继续正常处理流程
                    try:
                        success, message, photo_data, _ = import_service.process_single_photo(
                            file_path, move_file=False, db_session=db
                        )
                        if success and photo_data:
                            photo = photo_service.create_photo(db, photo_data)
                            if photo:
                                imported_count += 1
                                print(f"孤儿记录清理后成功导入: {file_path}")
                            else:
                                failed_files.append(f"{file_path}: 孤儿记录清理后数据库保存失败")
                                failed_count += 1
                        else:
                            failed_files.append(f"{file_path}: 孤儿记录清理后处理失败 - {message}")
                            failed_count += 1
                    except Exception as e:
                        failed_files.append(f"{file_path}: 孤儿记录清理后处理异常 - {str(e)}")
                        failed_count += 1
                        
                elif duplicate_type == 'physical_only':
                    # 情况3：物理重复 - 使用现有文件，继续处理
                    status_text = f"文件已存在（物理重复）"
                    print(f"物理重复文件: {file_path} - {status_text}")
                    # 物理重复时，process_single_photo应该已经处理了数据库记录
                    if success and photo_data:
                        photo = photo_service.create_photo(db, photo_data)
                        if photo:
                            imported_count += 1
                            print(f"物理重复文件成功处理: {file_path}")
                        else:
                            failed_files.append(f"{file_path}: 物理重复文件数据库保存失败")
                            failed_count += 1
                    else:
                        failed_files.append(f"{file_path}: 物理重复文件处理失败 - {message}")
                        failed_count += 1
                        
                else:
                    # 未知重复类型
                    status_text = message
                    failed_files.append(f"{file_path}: {status_text}")
                    failed_count += 1
                    print(f"未知重复类型: {file_path} - {status_text}")
            else:
                failed_files.append(f"{file_path}: {message}")
                failed_count += 1
                print(f"导入失败 {file_path}: {message}")

        except Exception as e:
            error_msg = f"处理文件 {file_path} 时发生错误: {str(e)}"
            failed_files.append(error_msg)
            failed_count += 1
            print(error_msg)
            continue

    # 如果有失败的文件，打印详细信息
    if failed_files:
        print(f"\n导入失败的文件详情:")
        for failed in failed_files:
            print(f"  - {failed}")
    
    print(f"\n导入完成: 成功 {imported_count}/{len(photo_files)} 张照片，跳过 {skipped_count} 张，失败 {failed_count} 张")
    
    # 导入完成，通知用户手动点击智能处理
    if imported_count > 0:
        print(f"导入完成: {imported_count} 张照片已导入，请手动点击智能处理按钮进行智能分析")
    
    return imported_count, skipped_count, failed_count, failed_files


async def process_photos_batch_with_status(photo_files: List[str], db, task_id: str):
    """
    带状态跟踪的智能处理照片文件
    
    :param photo_files: 照片文件路径列表
    :param db: 数据库会话
    :param task_id: 任务ID
    """
    try:
        # 初始化任务状态
        task_status[task_id] = {
            "status": "processing",
            "total_files": len(photo_files),
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
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        failed_files = []
        
        # 使用数据库事务确保数据一致性
        try:
            for i, file_path in enumerate(photo_files):
                try:
                    # 处理单个照片（文件夹扫描时复制文件，不移动）
                    success, message, photo_data, duplicate_info = import_service.process_single_photo(
                        file_path, move_file=False, db_session=db
                    )

                    if success and photo_data:
                        # 保存到数据库
                        photo = photo_service.create_photo(db, photo_data)
                        if photo:
                            imported_count += 1
                            print(f"成功导入: {file_path}")
                        else:
                            failed_files.append(f"{file_path}: 数据库保存失败")
                            print(f"数据库保存失败: {file_path}")
                    elif duplicate_info:
                        # 处理重复文件 - 按照重复图片处理逻辑.md的完整逻辑
                        duplicate_type = duplicate_info.get('duplicate_type', 'unknown')
                        message = duplicate_info.get('message', '文件重复')
                        
                        if duplicate_type == 'full_duplicate_completed':
                            # 情况1.1：完全重复且已完成智能处理 - 无需导入
                            status_text = f"文件已存在且已完成智能处理"
                            skipped_count += 1
                            print(f"跳过重复文件: {file_path} - {status_text}")
                            
                        elif duplicate_type == 'full_duplicate_incomplete':
                            # 情况1.2：完全重复但未完成智能处理 - 继续智能处理
                            status_text = f"文件已存在但未完成智能处理 - 将重新处理"
                            print(f"继续处理重复文件: {file_path} - {status_text}")
                            # 注意：这里不需要创建新的数据库记录，因为记录已存在
                            # 只需要确保状态正确，让后续的智能处理来处理
                            skipped_count += 1  # 重复文件，计入跳过
                            
                        elif duplicate_type == 'orphan_cleaned':
                            # 情况2：孤儿记录 - 清理后继续正常处理
                            status_text = f"孤儿记录已清理，继续处理"
                            print(f"孤儿记录已清理: {file_path} - {status_text}")
                            # 孤儿记录清理后，应该继续正常处理流程
                            # 这里需要重新调用处理逻辑
                            try:
                                success, message, photo_data, _ = import_service.process_single_photo(
                                    file_path, move_file=False, db_session=db
                                )
                                if success and photo_data:
                                    photo = photo_service.create_photo(db, photo_data)
                                    if photo:
                                        imported_count += 1
                                        print(f"孤儿记录清理后成功导入: {file_path}")
                                    else:
                                        failed_files.append(f"{file_path}: 孤儿记录清理后数据库保存失败")
                                        failed_count += 1
                                else:
                                    failed_files.append(f"{file_path}: 孤儿记录清理后处理失败 - {message}")
                                    failed_count += 1
                            except Exception as e:
                                failed_files.append(f"{file_path}: 孤儿记录清理后处理异常 - {str(e)}")
                                failed_count += 1
                                
                        elif duplicate_type == 'physical_only':
                            # 情况3：物理重复 - 使用现有文件，继续处理
                            status_text = f"文件已存在（物理重复）"
                            print(f"物理重复文件: {file_path} - {status_text}")
                            # 物理重复时，process_single_photo应该已经处理了数据库记录
                            # 这里需要检查是否成功创建了记录
                            if success and photo_data:
                                photo = photo_service.create_photo(db, photo_data)
                                if photo:
                                    imported_count += 1
                                    print(f"物理重复文件成功处理: {file_path}")
                                else:
                                    failed_files.append(f"{file_path}: 物理重复文件数据库保存失败")
                                    failed_count += 1
                            else:
                                failed_files.append(f"{file_path}: 物理重复文件处理失败 - {message}")
                                failed_count += 1
                                
                        else:
                            # 未知重复类型
                            status_text = message
                            failed_files.append(f"{file_path}: {status_text}")
                            failed_count += 1
                            print(f"未知重复类型: {file_path} - {status_text}")
                    else:
                        failed_files.append(f"{file_path}: {message}")
                        failed_count += 1
                        print(f"导入失败 {file_path}: {message}")
                        
                except Exception as e:
                    error_msg = f"{file_path}: 处理异常 - {str(e)}"
                    failed_files.append(error_msg)
                    failed_count += 1
                    print(error_msg)
                
                # 更新任务状态
                processed_count = i + 1
                progress = (processed_count / len(photo_files)) * 100
                
                task_status[task_id].update({
                    "processed_files": processed_count,
                    "imported_count": imported_count,
                    "skipped_count": skipped_count,
                    "failed_count": failed_count,
                    "failed_files": failed_files,
                    "progress_percentage": round(progress, 2)
                })
            
            # 提交事务
            db.commit()
            
            # 更新最终状态
            task_status[task_id].update({
                "status": "completed",
                "end_time": datetime.now().isoformat(),
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "failed_count": failed_count,
                "failed_files": failed_files
            })
            
            print(f"\n后台导入完成: 成功 {imported_count}/{len(photo_files)} 张照片")
            
        except Exception as e:
            # 回滚事务
            db.rollback()
            task_status[task_id].update({
                "status": "failed",
                "end_time": datetime.now().isoformat(),
                "error": str(e)
            })
            print(f"后台导入失败: {str(e)}")
    except Exception as e:
        # 处理整个函数级别的异常
        task_status[task_id] = {
            "status": "failed",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        }
        print(f"智能处理函数异常: {str(e)}")


@router.get("/scan-status/{task_id}")
async def get_scan_status(task_id: str):
    """
    获取扫描任务状态

    :param task_id: 任务ID
    """
    print(f"查询任务状态: {task_id}")
    print(f"当前任务状态: {task_status}")

    if task_id not in task_status:
        print(f"任务 {task_id} 不存在")
        raise HTTPException(status_code=404, detail="任务不存在")

    print(f"任务 {task_id} 状态: {task_status[task_id]}")
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
    带状态跟踪的处理上传文件
    
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
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        failed_files = []
        
        # 使用数据库事务确保数据一致性
        try:
            for i, file in enumerate(files):
                try:
                    # 验证文件类型
                    file_ext = Path(file.filename).suffix.lower()
                    
                    # 特殊处理HEIC格式
                    if file_ext in ['.heic', '.heif']:
                        # HEIC格式的content_type可能为空，需要特殊处理
                        pass
                    elif not file.content_type or not file.content_type.startswith('image/'):
                        failed_files.append(f"{file.filename}: 不支持的文件类型")
                        failed_count += 1
                        continue

                    # 保存临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                        shutil.copyfileobj(file.file, temp_file)
                        temp_path = temp_file.name

                    try:
                        # 处理单个照片
                        success, message, photo_data, duplicate_info = import_service.process_single_photo(
                            temp_path, move_file=False, db_session=db
                        )

                        if success and photo_data:
                            # 保存到数据库
                            photo = photo_service.create_photo(db, photo_data)
                            if photo:
                                imported_count += 1
                                print(f"成功导入: {file.filename}")
                            else:
                                failed_files.append(f"{file.filename}: 数据库保存失败")
                                failed_count += 1
                        elif duplicate_info:
                            # 处理重复文件 - 使用完整的重复检测逻辑
                            duplicate_type = duplicate_info.get('duplicate_type', 'unknown')
                            message = duplicate_info.get('message', '文件重复')
                            
                            # 根据重复类型生成更详细的提示
                            if duplicate_type == 'full_duplicate_completed':
                                status_text = f"文件已存在且已完成智能处理"
                                skipped_count += 1
                            elif duplicate_type == 'full_duplicate_incomplete':
                                status_text = f"文件已存在但未完成智能处理 - 将重新处理"
                                skipped_count += 1  # 重复文件，计入跳过
                            elif duplicate_type == 'physical_only':
                                status_text = f"文件已存在（物理重复）"
                                imported_count += 1  # 物理重复，计入成功
                            elif duplicate_type == 'orphan_cleaned':
                                status_text = f"孤儿记录已清理，继续处理"
                                imported_count += 1  # 清理后继续处理，计入成功
                            else:
                                status_text = message
                                failed_files.append(f"{file.filename}: {status_text}")
                                failed_count += 1
                                continue
                        else:
                            failed_files.append(f"{file.filename}: {message}")
                            failed_count += 1

                    finally:
                        # 清理临时文件
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)

                except Exception as e:
                    failed_files.append(f"{file.filename}: 处理异常 - {str(e)}")
                    failed_count += 1
                
                # 更新进度（每处理一个文件就+1，不管结果）
                task_status[task_id]["processed_files"] = i + 1
                task_status[task_id]["progress_percentage"] = int((i + 1) / len(files) * 100)
                task_status[task_id]["imported_count"] = imported_count
                task_status[task_id]["skipped_count"] = skipped_count
                task_status[task_id]["failed_count"] = failed_count
                task_status[task_id]["failed_files"] = failed_files

                print(f"进度更新: {i + 1}/{len(files)} ({int((i + 1) / len(files) * 100)}%) - 导入:{imported_count}, 跳过:{skipped_count}, 失败:{failed_count}")

                # 动态延迟：根据文件数量调整，让前端能看到进度变化
                # 小批量文件(<10)：500ms，大批量文件：减少延迟以提高性能
                total_files = len(files)
                if total_files <= 10:
                    delay = 0.5  # 500ms for small batches
                elif total_files <= 50:
                    delay = 0.2  # 200ms for medium batches
                else:
                    delay = 0.05  # 50ms for large batches, minimal impact on performance

                await asyncio.sleep(delay)

        except Exception as e:
            task_status[task_id]["status"] = "failed"
            task_status[task_id]["error"] = str(e)
            task_status[task_id]["end_time"] = datetime.now().isoformat()
            print(f"处理过程中发生错误: {str(e)}")
            return

        # 标记完成
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["end_time"] = datetime.now().isoformat()
        task_status[task_id]["imported_count"] = imported_count
        task_status[task_id]["skipped_count"] = skipped_count
        task_status[task_id]["failed_count"] = failed_count
        task_status[task_id]["failed_files"] = failed_files
        task_status[task_id]["progress_percentage"] = 100
        print(f"处理完成: 导入{imported_count}个，跳过{skipped_count}个，失败{failed_count}个")

    except Exception as e:
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["end_time"] = datetime.now().isoformat()
        print(f"任务初始化失败: {str(e)}")
