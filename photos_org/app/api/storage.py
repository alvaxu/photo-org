"""
家庭单机版智能照片整理系统 - 存储管理API
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.services.storage_service import StorageService

logger = get_logger(__name__)

router = APIRouter()


# 请求/响应模型
class BackupRequest(BaseModel):
    """备份请求"""
    backup_type: str = Field("manual", description="备份类型", pattern="^(manual|daily|weekly|monthly)$")


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


@router.post("/backup", response_model=BackupResponse)
async def create_backup(request: BackupRequest, background_tasks: BackgroundTasks):
    """
    创建数据备份

    - **backup_type**: 备份类型 (manual, daily, weekly, monthly)
    """
    try:
        storage_service = StorageService()

        # 添加后台任务
        background_tasks.add_task(perform_backup, request.backup_type)

        # 立即返回响应
        return BackupResponse(
            backup_path="",
            backup_size=0,
            total_files=0,
            backup_time=datetime.now().isoformat(),
            message=f"已开始{request.backup_type}备份，请稍后查看结果"
        )

    except Exception as e:
        logger.error(f"启动备份失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动备份失败: {str(e)}")


@router.get("/backups")
async def get_backup_list():
    """
    获取备份文件列表
    """
    try:
        storage_service = StorageService()
        backups = storage_service.get_backup_list()
        return backups

    except Exception as e:
        logger.error(f"获取备份列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")


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


# 后台任务函数
async def perform_backup(backup_type: str):
    """
    执行备份任务

    Args:
        backup_type: 备份类型
    """
    try:
        logger.info(f"开始执行{backup_type}备份")
        storage_service = StorageService()
        backup_path, backup_info = storage_service.create_backup(backup_type)

        logger.info(f"{backup_type}备份完成: {backup_path}")

    except Exception as e:
        logger.error(f"{backup_type}备份失败: {str(e)}")


# 导入datetime用于类型注解
from datetime import datetime
