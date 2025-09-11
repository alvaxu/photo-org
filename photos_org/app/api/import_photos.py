"""
照片导入API

提供照片文件导入、文件夹扫描、元数据提取等功能的API接口

作者：AI助手
创建日期：2025年9月9日
"""

import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
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
        imported_count, failed_files = await process_photos_batch(photo_files, db)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"成功导入{imported_count}张照片",
                "data": {
                    "scanned_files": len(photo_files),
                    "imported_photos": imported_count,
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
    """
    if not files:
        raise HTTPException(status_code=400, detail="未选择文件")

    if len(files) > 50:  # 限制单次上传数量
        raise HTTPException(status_code=400, detail="单次最多上传50个文件")

    try:
        import_service = ImportService()
        photo_service = PhotoService()
        imported_count = 0
        failed_files = []

        for file in files:
            # 验证文件类型
            if not file.content_type or not file.content_type.startswith('image/'):
                failed_files.append(f"{file.filename}: 不支持的文件类型")
                continue

            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_path = temp_file.name

            try:
                # 处理照片
                success, message, photo_data, duplicate_info = import_service.process_single_photo(temp_path, db_session=db)

                if success and photo_data:
                    # 保存到数据库
                    photo = photo_service.create_photo(db, photo_data)
                    if photo:
                        imported_count += 1
                    else:
                        failed_files.append(f"{file.filename}: 数据库保存失败")
                elif duplicate_info:
                    # 处理重复文件 - 使用完整的重复检测逻辑
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
                    
                    failed_files.append(f"{file.filename}: {status_text}")
                else:
                    failed_files.append(f"{file.filename}: {message}")

            except Exception as e:
                failed_files.append(f"{file.filename}: 处理异常 - {str(e)}")
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
                    "imported_photos": imported_count,
                    "failed_files": failed_files
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


async def process_photos_batch(photo_files: List[str], db) -> Tuple[int, List[str]]:
    """
    批量处理照片文件

    :param photo_files: 照片文件路径列表
    :param db: 数据库会话
    :return: (成功导入的数量, 失败文件列表)
    """
    import_service = ImportService()
    photo_service = PhotoService()
    imported_count = 0
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
                # 处理重复文件
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
                
                failed_files.append(f"{file_path}: {status_text}")
                print(f"跳过重复文件: {file_path} - {status_text}")
            else:
                failed_files.append(f"{file_path}: {message}")
                print(f"导入失败 {file_path}: {message}")

        except Exception as e:
            error_msg = f"处理文件 {file_path} 时发生错误: {str(e)}"
            failed_files.append(error_msg)
            print(error_msg)
            continue

    # 如果有失败的文件，打印详细信息
    if failed_files:
        print(f"\n导入失败的文件详情:")
        for failed in failed_files:
            print(f"  - {failed}")
    
    print(f"\n导入完成: 成功 {imported_count}/{len(photo_files)} 张照片")
    
    # 导入完成，通知用户手动点击批量处理
    if imported_count > 0:
        print(f"导入完成: {imported_count} 张照片已导入，请手动点击批量处理按钮进行智能分析")
    
    return imported_count, failed_files
