"""
家庭版智能照片系统 - 存储管理API
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import json
import shutil
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.services.storage_service import StorageService
import asyncio
import uuid

logger = get_logger(__name__)

router = APIRouter()

# 全局备份任务状态跟踪
backup_task_status = {}

# 任务状态清理配置
BACKUP_TASK_STATUS_CLEANUP_HOURS = 1  # 任务完成后1小时清理状态


# 请求/响应模型
class BackupRequest(BaseModel):
    """备份请求"""
    backup_path: str = Field(..., description="备份目标路径")
    backup_mode: str = Field("incremental", description="备份方式", pattern="^(full|incremental)$")
    backup_type: str = Field("manual", description="备份类型", pattern="^(manual|daily|weekly|monthly)$")


class BackupStartResponse(BaseModel):
    """备份启动响应"""
    task_id: str = Field(..., description="任务ID")
    success: bool = Field(..., description="是否成功启动")


class BackupResponse(BaseModel):
    """备份响应"""
    backup_path: str = Field(..., description="备份文件路径")
    backup_size: int = Field(..., description="备份文件大小")
    total_files: int = Field(..., description="备份的文件数量")
    backup_time: str = Field(..., description="备份时间")
    message: str = Field(..., description="备份结果信息")


class RestoreRequest(BaseModel):
    """恢复请求"""
    backup_path: str = Field(..., description="备份文件路径")
    restore_type: str = Field("full", description="恢复类型", pattern="^(full|photos|database)$")


class RestoreResponse(BaseModel):
    """恢复响应"""
    files_restored: int = Field(..., description="恢复的文件数量")
    database_restored: bool = Field(False, description="数据库是否恢复")
    restore_time: str = Field(..., description="恢复时间")
    errors: List[str] = Field(default_factory=list, description="恢复过程中的错误")


class CleanupRequest(BaseModel):
    """清理请求"""
    max_age_hours: int = Field(24, description="文件最大保留时间（小时）", ge=1, le=168)


class CleanupResponse(BaseModel):
    """清理响应"""
    files_removed: int = Field(..., description="删除的文件数量")
    space_freed: int = Field(..., description="释放的空间（字节）")
    space_freed_mb: float = Field(..., description="释放的空间（MB）")
    cleanup_time: str = Field(..., description="清理时间")
    errors: List[str] = Field(default_factory=list, description="清理过程中的错误")


class StorageInfo(BaseModel):
    """存储信息"""
    total_space: int = Field(..., description="总空间（字节）")
    used_space: int = Field(..., description="已用空间（字节）")
    free_space: int = Field(..., description="可用空间（字节）")
    usage_percent: float = Field(..., description="使用率百分比")
    originals_size: int = Field(..., description="原始照片大小")
    thumbnails_size: int = Field(..., description="缩略图大小")
    temp_size: int = Field(..., description="临时文件大小")
    backups_size: int = Field(..., description="备份文件大小")
    total_photos_size: int = Field(..., description="照片总大小")
    last_updated: str = Field(..., description="最后更新时间")


class FileIntegrityCheck(BaseModel):
    """文件完整性检查"""
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., description="文件大小")
    actual_hash: str = Field(..., description="实际哈希值")
    expected_hash: Optional[str] = Field(None, description="期望哈希值")
    hash_match: Optional[bool] = Field(None, description="哈希是否匹配")
    valid: bool = Field(..., description="文件是否有效")


class StorageStatsResponse(BaseModel):
    """系统存储统计响应"""
    database: Dict[str, Any] = Field(..., description="数据库信息")
    originals: Dict[str, Any] = Field(..., description="原图文件信息")
    thumbnails: Dict[str, Any] = Field(..., description="缩略图文件信息")


@router.get("/info", response_model=StorageInfo)
async def get_storage_info():
    """
    获取存储信息
    """
    try:
        storage_service = StorageService()
        info = storage_service.get_storage_info()
        return StorageInfo(**info)

    except Exception as e:
        logger.error(f"获取存储信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取存储信息失败: {str(e)}")


@router.get("/stats", response_model=StorageStatsResponse)
async def get_storage_stats():
    """
    获取系统存储统计信息（用于备份预览）

    返回数据库大小、原图数量/大小、缩略图数量/大小
    """
    try:
        storage_service = StorageService()
        stats = storage_service.get_storage_stats()
        return StorageStatsResponse(**stats)
    except Exception as e:
        logger.error(f"获取存储统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取存储统计失败: {str(e)}")


@router.post("/backup/select-path")
async def select_backup_path(request: Request):
    """
    选择备份路径（使用Windows文件夹选择对话框）
    
    - **initial_dir**: 初始目录路径（可选，默认使用上次备份路径或C盘）
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # 获取初始目录
        initial_dir = "C:\\"
        try:
            body = await request.json()
            if body and "initial_dir" in body:
                initial_dir = body["initial_dir"]
        except:
            pass
        
        # 如果没有提供，尝试从备份历史中获取最近一次备份路径
        if initial_dir == "C:\\":
            try:
                storage_service = StorageService()
                history_file = storage_service.backups_path / "backup_history.json"
                if history_file.exists():
                    with open(history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                        if history and len(history) > 0:
                            # 获取最近一次备份的路径的父目录
                            last_backup_path = history[-1].get('backup_path', '')
                            if last_backup_path:
                                backup_path_obj = Path(last_backup_path)
                                if backup_path_obj.exists():
                                    initial_dir = str(backup_path_obj.parent)
            except Exception as e:
                logger.debug(f"获取上次备份路径失败: {str(e)}")
        
        # 创建根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 设置窗口属性
        root.attributes('-topmost', True)  # 置顶显示
        root.state('withdrawn')  # 完全隐藏主窗口
        
        # 选择目录
        directory = filedialog.askdirectory(
            title="选择备份目录",
            initialdir=initial_dir
        )
        
        root.destroy()  # 销毁窗口
        
        if directory:
            return {
                "success": True,
                "path": directory
            }
        else:
            return {
                "success": False,
                "message": "用户取消选择"
            }
            
    except Exception as e:
        logger.error(f"选择备份路径失败: {str(e)}")
        return {
            "success": False,
            "message": f"选择备份路径失败: {str(e)}"
        }


@router.post("/backup", response_model=BackupStartResponse)
async def create_backup(request: BackupRequest):
    """
    启动数据备份任务（异步执行）
    
    - **backup_path**: 备份目标路径
    - **backup_mode**: 备份方式 (full/incremental)
    - **backup_type**: 备份类型 (manual, daily, weekly, monthly)
    
    返回 task_id，前端可通过 GET /api/v1/storage/backup/status/{task_id} 查询进度
    """
    try:
        # 生成任务ID
        task_id = f"backup_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        # 启动后台任务
        asyncio.create_task(process_backup_task(task_id, request))
        
        logger.info(f"备份任务已启动: {task_id}, 路径: {request.backup_path}, 方式: {request.backup_mode}")
        
        return BackupStartResponse(
            task_id=task_id,
            success=True
        )

    except Exception as e:
        logger.error(f"启动备份任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动备份任务失败: {str(e)}")


async def process_backup_task(task_id: str, request: BackupRequest):
    """
    处理备份任务（后台任务）
    
    :param task_id: 任务ID
    :param request: 备份请求
    """
    storage_service = StorageService()
    backup_path = Path(request.backup_path)
    backup_start_time = datetime.now()
    
    try:
        # 初始化任务状态
        backup_task_status[task_id] = {
            "status": "processing",
            "current_stage": "initializing",
            "progress_percentage": 0.0,
            "message": "正在初始化备份..."
        }
        
        # 1. 初始化（0% → 5%）
        backup_task_status[task_id].update({
            "current_stage": "initializing",
            "progress_percentage": 0.0,
            "message": "正在初始化备份..."
        })
        
        # 确保备份目录存在
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 记录备份开始时间到 backup_info.json
        backup_info = {
            "backup_start_time": backup_start_time.isoformat(),
            "backup_type": request.backup_type,
            "backup_mode": request.backup_mode,
            "backup_path": str(backup_path)
        }
        
        info_path = backup_path / "backup_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[{task_id}] 备份初始化完成，开始时间: {backup_start_time.isoformat()}")
        
        backup_task_status[task_id].update({
            "progress_percentage": 5.0,
            "message": "初始化完成，开始备份数据库..."
        })
        
        # 2. 备份数据库（5% → 15%）
        backup_task_status[task_id].update({
            "current_stage": "backing_up_db",
            "progress_percentage": 5.0,
            "message": "正在备份数据库..."
        })
        
        from app.core.path_utils import resolve_resource_path
        db_path = resolve_resource_path(settings.database.path)
        backup_db_path = backup_path / "photos.db"
        if db_path.exists():
            try:
                import sqlite3
                
                # 使用SQLite备份API进行安全备份（即使系统正在运行也能完整备份）
                source_conn = sqlite3.connect(str(db_path), timeout=30.0)
                backup_conn = sqlite3.connect(str(backup_db_path), timeout=30.0)
                
                try:
                    # 执行备份（这会确保WAL文件中的数据也被包含）
                    # pages=-1 表示一次性备份所有页面（更快）
                    source_conn.backup(backup_conn, pages=-1, progress=None)
                    logger.info(f"[{task_id}] 数据库备份完成（使用SQLite备份API）: {backup_db_path}")
                finally:
                    backup_conn.close()
                    source_conn.close()
            except Exception as e:
                logger.error(f"[{task_id}] 使用SQLite备份API失败，回退到文件复制: {str(e)}")
                # 回退方案：如果备份API失败，使用文件复制
                try:
                    shutil.copy2(db_path, backup_db_path)
                    logger.warning(f"[{task_id}] 数据库备份完成（使用文件复制，可能不完整）: {backup_db_path}")
                except Exception as copy_error:
                    logger.error(f"[{task_id}] 数据库备份失败: {str(copy_error)}")
                    raise Exception(f"数据库备份失败: {str(copy_error)}")
        
        backup_task_status[task_id].update({
            "progress_percentage": 15.0,
            "message": "数据库备份完成，开始备份原图文件..."
        })
        
        # 3. 备份原图目录（15% → 60%）
        backup_task_status[task_id].update({
            "current_stage": "backing_up_originals",
            "progress_percentage": 15.0,
            "message": "正在备份原图文件..."
        })
        
        originals_source = storage_service.originals_path
        originals_dest = backup_path / "originals"
        
        result_originals = await storage_service.backup_files_with_robocopy(
            originals_source,
            originals_dest,
            request.backup_mode
        )
        logger.info(f"[{task_id}] 原图备份完成: {result_originals}")
        
        backup_task_status[task_id].update({
            "progress_percentage": 60.0,
            "message": "原图备份完成，开始备份缩略图..."
        })
        
        # 4. 备份缩略图目录（60% → 95%）
        backup_task_status[task_id].update({
            "current_stage": "backing_up_thumbnails",
            "progress_percentage": 60.0,
            "message": "正在备份缩略图..."
        })
        
        thumbnails_source = storage_service.thumbnails_path
        thumbnails_dest = backup_path / "thumbnails"
        
        result_thumbnails = await storage_service.backup_files_with_robocopy(
            thumbnails_source,
            thumbnails_dest,
            request.backup_mode
        )
        logger.info(f"[{task_id}] 缩略图备份完成: {result_thumbnails}")
        
        backup_task_status[task_id].update({
            "progress_percentage": 95.0,
            "message": "缩略图备份完成，正在计算统计信息..."
        })
        
        # 5. 计算备份大小和统计信息（95% → 98%）
        backup_task_status[task_id].update({
            "current_stage": "calculating_stats",
            "progress_percentage": 95.0,
            "message": "正在计算统计信息..."
        })
        
        backup_size = 0
        if backup_db_path.exists():
            backup_size += backup_db_path.stat().st_size
        
        # 使用 robocopy 返回的字节数（原图 + 缩略图）
        # 备份大小使用实际复制的字节数（Copied）
        originals_bytes_copied = result_originals.get('bytes_copied', 0) or 0
        thumbnails_bytes_copied = result_thumbnails.get('bytes_copied', 0) or 0
        backup_size += originals_bytes_copied + thumbnails_bytes_copied
        
        # 获取原图统计信息（Total 和 Copied）
        originals_files_total = result_originals.get('files_total', 0) or 0
        originals_files_copied = result_originals.get('files_copied', 0) or 0
        originals_bytes_total = result_originals.get('bytes_total', 0) or 0
        
        # 获取缩略图统计信息（Total 和 Copied）
        thumbnails_files_total = result_thumbnails.get('files_total', 0) or 0
        thumbnails_files_copied = result_thumbnails.get('files_copied', 0) or 0
        thumbnails_bytes_total = result_thumbnails.get('bytes_total', 0) or 0
        
        # 获取原图和缩略图的 robocopy 时长（用于统计，但不作为总时长）
        originals_elapsed = result_originals.get('elapsed_seconds', 0) or 0
        thumbnails_elapsed = result_thumbnails.get('elapsed_seconds', 0) or 0
        robocopy_elapsed_seconds = originals_elapsed + thumbnails_elapsed
        
        backup_task_status[task_id].update({
            "progress_percentage": 98.0,
            "message": "统计信息计算完成，正在保存元信息..."
        })
        
        # 6. 保存备份元信息和历史（98% → 100%）
        backup_task_status[task_id].update({
            "current_stage": "saving_metadata",
            "progress_percentage": 98.0,
            "message": "正在保存元信息..."
        })
        
        backup_end_time = datetime.now()
        backup_duration_seconds = int((backup_end_time - backup_start_time).total_seconds())
        
        # 格式化总备份时长（包含所有步骤：数据库+原图+缩略图+统计+保存）
        if backup_duration_seconds is not None:
            hours = backup_duration_seconds // 3600
            minutes = (backup_duration_seconds % 3600) // 60
            seconds = backup_duration_seconds % 60
            total_elapsed_time = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            total_elapsed_time = None
        
        # 更新 backup_info.json（包含开始时间、结束时间、时长等）
        backup_info = {
            "backup_start_time": backup_start_time.isoformat(),
            "backup_time": backup_end_time.isoformat(),
            "backup_type": request.backup_type,
            "backup_mode": request.backup_mode,
            "backup_path": str(backup_path),
            "backup_duration_seconds": backup_duration_seconds
        }
        
        info_path = backup_path / "backup_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        # 记录备份历史（保存到backups目录，包含备份大小、文件数、时长等信息）
        history_file = storage_service.backups_path / "backup_history.json"
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []
        
        # 添加新备份记录（包含完整的统计信息，分原图和缩略图）
        history.append({
            "backup_path": str(backup_path),
            "backup_time": backup_info["backup_time"],
            "backup_type": request.backup_type,
            "backup_mode": request.backup_mode,
            "size": backup_size,  # 总备份大小（数据库+原图实际+缩略图实际，字节）
            "elapsed_time": total_elapsed_time,  # 备份时长（格式化字符串，包含所有步骤）
            "elapsed_seconds": backup_duration_seconds,  # 备份时长（秒数，包含所有步骤）
            # 原图统计信息
            "originals": {
                "total_files": originals_files_total,      # 总文件数
                "copied_files": originals_files_copied,    # 实际备份文件数
                "total_size": originals_bytes_total,       # 总大小（所有文件，字节）
                "copied_size": originals_bytes_copied      # 实际备份大小（字节）
            },
            # 缩略图统计信息
            "thumbnails": {
                "total_files": thumbnails_files_total,
                "copied_files": thumbnails_files_copied,
                "total_size": thumbnails_bytes_total,
                "copied_size": thumbnails_bytes_copied
            }
        })
        
        # 保存历史（最多保留100条）
        history = history[-100:]
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        # 更新任务状态为完成
        backup_task_status[task_id].update({
            "status": "completed",
            "current_stage": "completed",
            "progress_percentage": 100.0,
            "message": f"备份完成（{request.backup_mode}模式）"
        })
        
        logger.info(f"[{task_id}] 备份任务完成，耗时: {backup_duration_seconds}秒")
        
        # 延迟清理任务状态，避免内存泄漏
        async def cleanup_task_status():
            await asyncio.sleep(BACKUP_TASK_STATUS_CLEANUP_HOURS * 3600)  # 延迟清理
            if task_id in backup_task_status:
                del backup_task_status[task_id]
                logger.info(f"清理已完成的备份任务状态: {task_id}")
        
        # 启动后台清理任务
        asyncio.create_task(cleanup_task_status())
        
    except Exception as e:
        logger.error(f"[{task_id}] 备份任务失败: {str(e)}")
        import traceback
        logger.error(f"[{task_id}] 详细错误信息: {traceback.format_exc()}")
        
        # 标记任务失败
        backup_task_status[task_id].update({
            "status": "failed",
            "message": f"备份失败: {str(e)}"
        })
        
        # 失败状态也保留1小时，然后清理
        async def cleanup_failed_task_status():
            await asyncio.sleep(BACKUP_TASK_STATUS_CLEANUP_HOURS * 3600)
            if task_id in backup_task_status:
                del backup_task_status[task_id]
                logger.info(f"清理失败的备份任务状态: {task_id}")
        
        asyncio.create_task(cleanup_failed_task_status())


@router.get("/backup/status/{task_id}")
async def get_backup_task_status(task_id: str):
    """
    获取备份任务状态
    
    :param task_id: 任务ID
    :return: 任务状态
    """
    try:
        task_status = backup_task_status.get(task_id)
        
        if not task_status:
            return {
                "status": "not_found",
                "message": "任务不存在或已过期"
            }
        
        return {
            "status": task_status.get("status", "unknown"),
            "current_stage": task_status.get("current_stage", "unknown"),
            "progress_percentage": task_status.get("progress_percentage", 0.0),
            "message": task_status.get("message", "")
        }
        
    except Exception as e:
        logger.error(f"获取备份任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取备份任务状态失败: {str(e)}")


@router.get("/backups")
async def get_backup_list():
    """
    获取备份文件列表（旧版，保留兼容性）
    """
    try:
        storage_service = StorageService()
        backups = storage_service.get_backup_list()
        return backups

    except Exception as e:
        logger.error(f"获取备份列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")


@router.get("/backups/history")
async def get_backup_history():
    """
    获取备份历史（从backups目录的backup_history.json读取）
    
    返回所有备份记录，按时间倒序排列
    """
    try:
        storage_service = StorageService()
        history_file = storage_service.backups_path / "backup_history.json"
        
        backups = []
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    
                    # 为每个备份记录添加大小信息
                    for backup in history:
                        backup_path = Path(backup.get('backup_path', ''))
                        
                        # 优先使用JSON中保存的大小（性能优化）
                        if 'size' in backup:
                            # JSON中已有大小，直接使用
                            size = backup.get('size', 0)
                        else:
                            # 向后兼容：如果JSON中没有size字段，则计算（旧数据）
                            if backup_path.exists():
                                size = 0
                                if (backup_path / "photos.db").exists():
                                    size += (backup_path / "photos.db").stat().st_size
                                if (backup_path / "originals").exists():
                                    size += storage_service._calculate_directory_size(backup_path / "originals")
                                if (backup_path / "thumbnails").exists():
                                    size += storage_service._calculate_directory_size(backup_path / "thumbnails")
                            else:
                                # 备份目录不存在，无法计算，使用0
                                size = 0
                        
                        backup['size'] = size
                        backups.append(backup)
            except Exception as e:
                logger.error(f"读取备份历史失败: {str(e)}")
        
        # 按时间倒序排列
        backups.sort(key=lambda x: x.get('backup_time', ''), reverse=True)
        
        return {
            "backups": backups,
            "total": len(backups)
        }
        
    except Exception as e:
        logger.error(f"获取备份历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取备份历史失败: {str(e)}")


@router.post("/restore", response_model=RestoreResponse)
async def restore_backup(request: RestoreRequest):
    """
    从备份恢复数据

    - **backup_path**: 备份文件路径
    - **restore_type**: 恢复类型 (full, photos, database)
    """
    try:
        storage_service = StorageService()
        result = storage_service.restore_backup(request.backup_path, request.restore_type)

        return RestoreResponse(
            files_restored=result.get("files_restored", 0),
            database_restored=result.get("database_restored", False),
            restore_time=result.get("restore_time", datetime.now().isoformat()),
            errors=result.get("errors", [])
        )

    except Exception as e:
        logger.error(f"数据恢复失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据恢复失败: {str(e)}")


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_temp_files(request: CleanupRequest):
    """
    清理临时文件

    - **max_age_hours**: 文件最大保留时间（小时）
    """
    try:
        storage_service = StorageService()
        result = storage_service.cleanup_temp_files(request.max_age_hours)

        return CleanupResponse(
            files_removed=result.get("files_removed", 0),
            space_freed=result.get("space_freed", 0),
            space_freed_mb=round(result.get("space_freed", 0) / (1024 * 1024), 2),
            cleanup_time=result.get("cleanup_time", datetime.now().isoformat()),
            errors=result.get("errors", [])
        )

    except Exception as e:
        logger.error(f"清理临时文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理临时文件失败: {str(e)}")


@router.get("/integrity/{file_path:path}")
async def check_file_integrity(file_path: str, expected_hash: Optional[str] = None):
    """
    检查文件完整性

    - **file_path**: 文件路径
    - **expected_hash**: 期望的哈希值（可选）
    """
    try:
        storage_service = StorageService()
        result = storage_service.validate_file_integrity(file_path, expected_hash)
        return result

    except Exception as e:
        logger.error(f"文件完整性检查失败 {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件完整性检查失败: {str(e)}")


@router.get("/structure")
async def get_storage_structure():
    """
    获取存储目录结构
    """
    try:
        storage_service = StorageService()

        def get_directory_structure(path: Path, max_depth: int = 3) -> Dict[str, Any]:
            """
            递归获取目录结构

            Args:
                path: 目录路径
                max_depth: 最大递归深度

            Returns:
                目录结构字典
            """
            if max_depth <= 0 or not path.exists():
                return {}

            structure = {
                "name": path.name,
                "path": str(path),
                "type": "directory",
                "children": []
            }

            try:
                for item in sorted(path.iterdir()):
                    if item.is_file():
                        structure["children"].append({
                            "name": item.name,
                            "path": str(item),
                            "type": "file",
                            "size": item.stat().st_size,
                            "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                        })
                    elif item.is_dir() and max_depth > 1:
                        structure["children"].append(get_directory_structure(item, max_depth - 1))
            except PermissionError:
                structure["error"] = "权限不足"

            return structure

        # 获取存储根目录结构
        structure = get_directory_structure(storage_service.base_path, max_depth=4)

        return {
            "storage_root": str(storage_service.base_path),
            "structure": structure,
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取存储结构失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取存储结构失败: {str(e)}")


@router.get("/maintenance")
async def get_maintenance_info():
    """
    获取存储维护信息
    """
    try:
        storage_service = StorageService()

        # 获取存储信息
        storage_info = storage_service.get_storage_info()

        # 计算维护建议
        maintenance_info = {
            "storage_info": storage_info,
            "maintenance_tasks": []
        }

        # 检查存储空间使用率
        usage_percent = storage_info.get("usage_percent", 0)
        if usage_percent > 90:
            maintenance_info["maintenance_tasks"].append({
                "type": "storage_warning",
                "level": "critical",
                "message": f"存储空间使用率过高: {usage_percent:.1f}%",
                "suggestion": "清理不需要的文件或扩展存储空间"
            })
        elif usage_percent > 80:
            maintenance_info["maintenance_tasks"].append({
                "type": "storage_warning",
                "level": "warning",
                "message": f"存储空间使用率较高: {usage_percent:.1f}%",
                "suggestion": "考虑清理临时文件或创建备份"
            })

        # 检查临时文件大小
        temp_size_mb = storage_info.get("temp_size", 0) / (1024 * 1024)
        if temp_size_mb > 100:  # 超过100MB
            maintenance_info["maintenance_tasks"].append({
                "type": "temp_cleanup",
                "level": "info",
                "message": f"临时文件较大: {temp_size_mb:.1f}MB",
                "suggestion": "运行临时文件清理"
            })

        # 检查备份文件
        backups = storage_service.get_backup_list()
        total_backups = sum(len(backup_list) for backup_list in backups.values())
        if total_backups == 0:
            maintenance_info["maintenance_tasks"].append({
                "type": "backup_missing",
                "level": "warning",
                "message": "没有找到备份文件",
                "suggestion": "创建数据备份以确保数据安全"
            })

        maintenance_info["last_updated"] = datetime.now().isoformat()

        return maintenance_info

    except Exception as e:
        logger.error(f"获取维护信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取维护信息失败: {str(e)}")


