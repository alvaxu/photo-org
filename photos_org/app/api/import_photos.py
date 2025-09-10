"""
照片导入API

提供照片文件导入、文件夹扫描、元数据提取等功能的API接口

作者：AI助手
创建日期：2025年9月9日
"""

import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import get_db
from app.models.photo import Photo
from app.services.import_service import ImportService
from app.services.photo_service import PhotoService

router = APIRouter()


@router.post("/scan-folder")
async def scan_folder(
    folder_path: str,
    recursive: bool = True,
    background_tasks: BackgroundTasks = None,
    db: get_db = None
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
        if len(photo_files) > 10:
            background_tasks.add_task(process_photos_batch, photo_files, db)

            return JSONResponse(
                status_code=202,
                content={
                    "success": True,
                    "message": f"发现{len(photo_files)}个照片文件，已提交后台处理",
                    "data": {
                        "scanned_files": len(photo_files),
                        "status": "processing"
                    }
                }
            )

        # 小批量直接处理
        imported_count = await process_photos_batch(photo_files, db)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"成功导入{imported_count}张照片",
                "data": {
                    "scanned_files": len(photo_files),
                    "imported_photos": imported_count
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件夹扫描失败: {str(e)}")


@router.post("/upload")
async def upload_photos(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: get_db = None
):
    """
    上传照片文件

    :param files: 上传的文件列表
    :param background_tasks: 后台任务
    :param db: 数据库会话
    """
    if not files:
        raise HTTPException(status_code=400, detail="未选择文件")

    if len(files) > 50:  # 限制单次上传数量
        raise HTTPException(status_code=400, detail="单次最多上传50个文件")

    try:
        import_service = ImportService()
        photo_service = PhotoService(db)
        imported_count = 0

        for file in files:
            # 验证文件类型
            if not file.content_type or not file.content_type.startswith('image/'):
                continue

            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_path = temp_file.name

            try:
                # 处理照片
                success, message, photo_data = import_service.process_single_photo(temp_path)

                if success and photo_data:
                    # 保存到数据库
                    photo = photo_service.create_photo(photo_data)
                    imported_count += 1
                else:
                    print(f"文件 {file.filename} 处理失败: {message}")

            finally:
                # 清理临时文件
                Path(temp_path).unlink(missing_ok=True)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"成功导入{imported_count}/{len(files)}个文件",
                "data": {
                    "total_files": len(files),
                    "imported_photos": imported_count
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/process-single")
async def process_single_file(
    file_path: str,
    db: get_db = None
):
    """
    处理单个照片文件

    :param file_path: 文件路径
    :param db: 数据库会话
    """
    try:
        import_service = ImportService()
        photo_service = PhotoService(db)

        # 处理照片
        success, message, photo_data = import_service.process_single_photo(file_path)

        if success and photo_data:
            # 保存到数据库
            photo = photo_service.create_photo(photo_data)

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
        else:
            raise HTTPException(status_code=400, detail=message)

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


async def process_photos_batch(photo_files: List[str], db) -> int:
    """
    批量处理照片文件

    :param photo_files: 照片文件路径列表
    :param db: 数据库会话
    :return: 成功导入的数量
    """
    import_service = ImportService()
    photo_service = PhotoService(db)
    imported_count = 0

    for file_path in photo_files:
        try:
            # 处理单个照片
            success, message, photo_data = import_service.process_single_photo(file_path)

            if success and photo_data:
                # 保存到数据库
                photo = photo_service.create_photo(photo_data)
                imported_count += 1
                print(f"成功导入: {file_path}")
            else:
                print(f"导入失败 {file_path}: {message}")

        except Exception as e:
            print(f"处理文件 {file_path} 时发生错误: {str(e)}")
            continue

    return imported_count
