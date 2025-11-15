"""
家庭版智能照片系统 - 存储管理服务
"""
import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import hashlib
import json

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.photo import Photo
from sqlalchemy import func


class StorageService:
    """
    存储管理服务类
    负责文件存储、备份、清理等存储相关功能
    """
    # 缓存相关
    _stats_cache: Optional[Dict[str, Any]] = None
    _stats_cache_time: Optional[datetime] = None
    _cache_ttl: timedelta = timedelta(minutes=5)  # 缓存有效期5分钟

    def __init__(self):
        """初始化存储服务"""
        self.logger = get_logger(__name__)
        # 注意：不再在 __init__ 中固定路径，改为动态读取
        # 确保目录存在（使用动态路径）
        self._ensure_directories()
    
    @property
    def base_path(self) -> Path:
        """动态获取存储基础路径（每次使用时读取最新配置）"""
        from app.core.config import get_settings
        from app.core.path_utils import resolve_resource_path
        return resolve_resource_path(get_settings().storage.base_path)
    
    @property
    def originals_path(self) -> Path:
        """动态获取原图路径"""
        from app.core.config import get_settings
        current_settings = get_settings()
        return self.base_path / current_settings.storage.originals_path
    
    @property
    def thumbnails_path(self) -> Path:
        """动态获取缩略图路径"""
        from app.core.config import get_settings
        current_settings = get_settings()
        return self.base_path / current_settings.storage.thumbnails_path
    
    @property
    def temp_path(self) -> Path:
        """动态获取临时文件路径"""
        from app.core.config import get_settings
        current_settings = get_settings()
        return self.base_path / current_settings.storage.temp_path
    
    @property
    def backups_path(self) -> Path:
        """动态获取备份路径"""
        from app.core.config import get_settings
        current_settings = get_settings()
        return self.base_path / current_settings.storage.backups_path

    def _ensure_directories(self):
        """确保所有必要的目录都存在"""
        directories = [
            self.base_path,
            self.originals_path,
            self.thumbnails_path,
            self.temp_path,
            self.backups_path,
            self.backups_path / "daily",
            self.backups_path / "weekly",
            self.backups_path / "monthly",
            self.temp_path / "processing",
            self.temp_path / "uploads",
            self.temp_path / "cache"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_storage_info(self) -> Dict[str, Any]:
        """
        获取存储信息

        Returns:
            存储信息字典
        """
        try:
            # 获取磁盘使用情况（跨平台兼容）
            if hasattr(os, 'statvfs'):  # Unix-like systems
                stat = os.statvfs(str(self.base_path))
                total_space = stat.f_bsize * stat.f_blocks
                free_space = stat.f_bsize * stat.f_bavail
            else:  # Windows
                import shutil
                usage = shutil.disk_usage(str(self.base_path))
                total_space = usage.total
                free_space = usage.free
                used_space = usage.used

            used_space = total_space - free_space

            # 计算照片存储使用情况
            originals_size = self._calculate_directory_size(self.originals_path)
            thumbnails_size = self._calculate_directory_size(self.thumbnails_path)
            temp_size = self._calculate_directory_size(self.temp_path)
            backups_size = self._calculate_directory_size(self.backups_path)

            return {
                "total_space": total_space,
                "used_space": used_space,
                "free_space": free_space,
                "usage_percent": (used_space / total_space) * 100 if total_space > 0 else 0,
                "originals_size": originals_size,
                "thumbnails_size": thumbnails_size,
                "temp_size": temp_size,
                "backups_size": backups_size,
                "total_photos_size": originals_size + thumbnails_size,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"获取存储信息失败: {str(e)}")
            return {
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }

    def _calculate_directory_size(self, path: Path) -> int:
        """
        计算目录大小

        Args:
            path: 目录路径

        Returns:
            目录大小（字节）
        """
        try:
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception as e:
            self.logger.error(f"计算目录大小失败 {path}: {str(e)}")
            return 0
    
    def _count_files_in_directory(self, path: Path) -> int:
        """
        统计目录中的文件数量

        Args:
            path: 目录路径

        Returns:
            文件数量
        """
        try:
            count = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    count += 1
            return count
        except Exception as e:
            self.logger.error(f"统计文件数量失败 {path}: {str(e)}")
            return 0
    
    def _count_and_size_directory(self, path: Path) -> Tuple[int, int]:
        """
        一次遍历同时统计目录中的文件数量和大小（优化性能）

        Args:
            path: 目录路径

        Returns:
            (文件数量, 总大小字节数)
        """
        try:
            count = 0
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    count += 1
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        # 忽略无法访问的文件
                        pass
            return count, total_size
        except Exception as e:
            self.logger.error(f"统计目录文件数量和大小失败 {path}: {str(e)}")
            return 0, 0
    
    def get_storage_stats(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取系统存储统计信息（用于备份预览）
        
        返回数据库大小、原图数量/大小、缩略图数量/大小
        
        优化说明：
        - 原图统计：从数据库读取（快速，Photo表已有file_size字段）
        - 缩略图统计：基于数据库查询数量 + 估算大小（快速，300x300像素质量50的JPEG平均约20KB）
        - 缓存机制：结果缓存5分钟，避免重复计算

        Args:
            use_cache: 是否使用缓存（默认True）

        Returns:
            存储统计信息字典
        """
        try:
            # 检查缓存
            if use_cache and self._stats_cache is not None and self._stats_cache_time is not None:
                if datetime.now() - self._stats_cache_time < self._cache_ttl:
                    self.logger.debug("使用缓存的存储统计信息")
                    return self._stats_cache.copy()
            
            from app.core.config import get_settings
            from app.db.session import get_db
            from app.core.path_utils import resolve_resource_path
            
            # 1. 获取数据库信息（快速）
            db_path = resolve_resource_path(get_settings().database.path)
            db_size = db_path.stat().st_size if db_path.exists() else 0
            
            # 2. 获取原图文件信息（从数据库读取，快速）
            db = next(get_db())
            try:
                originals_count = db.query(Photo).count()
                originals_size = db.query(func.sum(Photo.file_size)).scalar() or 0
                
                # 3. 获取缩略图文件信息（基于数据库查询 + 估算，快速）
                # 查询有缩略图的照片数量
                thumbnails_count = db.query(Photo).filter(
                    Photo.thumbnail_path.isnot(None)
                ).count()
                
                # 估算总大小：300x300像素，质量50的JPEG，平均约20KB
                AVERAGE_THUMBNAIL_SIZE = 20 * 1024  # 20KB
                thumbnails_size = thumbnails_count * AVERAGE_THUMBNAIL_SIZE
                
            except Exception as e:
                self.logger.warning(f"从数据库读取统计失败，回退到文件系统遍历: {str(e)}")
                # 回退方案：如果数据库查询失败，使用文件系统遍历
                originals_count = self._count_files_in_directory(self.originals_path)
                originals_size = self._calculate_directory_size(self.originals_path)
                thumbnails_count, thumbnails_size = self._count_and_size_directory(self.thumbnails_path)
            finally:
                db.close()
            
            result = {
                "database": {
                    "size": db_size,
                    "path": str(db_path)
                },
                "originals": {
                    "count": originals_count,
                    "total_size": originals_size
                },
                "thumbnails": {
                    "count": thumbnails_count,
                    "total_size": thumbnails_size
                }
            }
            
            # 更新缓存
            self._stats_cache = result.copy()
            self._stats_cache_time = datetime.now()
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取存储统计失败: {str(e)}")
            return {
                "database": {
                    "size": 0,
                    "path": ""
                },
                "originals": {
                    "count": 0,
                    "total_size": 0
                },
                "thumbnails": {
                    "count": 0,
                    "total_size": 0
                },
                "error": str(e)
            }
    
    def clear_storage_stats_cache(self):
        """
        清除存储统计缓存（在文件系统发生变化时调用）
        """
        self._stats_cache = None
        self._stats_cache_time = None
        self.logger.debug("已清除存储统计缓存")

    def generate_photo_path(self, taken_at: datetime, filename: str) -> Tuple[Path, str]:
        """
        生成照片存储路径

        Args:
            taken_at: 拍摄时间
            filename: 原始文件名

        Returns:
            (完整路径, 新文件名)
        """
        try:
            # 生成目录路径：originals/YYYY/MM/DD/
            year = taken_at.strftime('%Y')
            month = taken_at.strftime('%m')
            day = taken_at.strftime('%d')

            dir_path = self.originals_path / year / month / day
            dir_path.mkdir(parents=True, exist_ok=True)

            # 生成新文件名：YYYYMMDD_HHMMSS_original_filename
            timestamp = taken_at.strftime('%Y%m%d_%H%M%S')
            name_without_ext = Path(filename).stem
            ext = Path(filename).suffix.lower()
            new_filename = f"{timestamp}_{name_without_ext}{ext}"

            return dir_path / new_filename, new_filename

        except Exception as e:
            self.logger.error(f"生成照片路径失败: {str(e)}")
            raise Exception(f"生成照片路径失败: {str(e)}")

    def generate_thumbnail_path(self, photo_id: int, original_filename: str) -> Path:
        """
        生成缩略图存储路径

        Args:
            photo_id: 照片ID
            original_filename: 原始文件名

        Returns:
            缩略图完整路径
        """
        try:
            # 生成目录路径：thumbnails/XXXXXX/
            # 使用photo_id的前6位作为目录名，避免单个目录文件过多
            dir_name = f"{photo_id:06d}"[:6]
            dir_path = self.thumbnails_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

            # 生成缩略图文件名
            name_without_ext = Path(original_filename).stem
            thumbnail_filename = f"{photo_id}_{name_without_ext}_thumb.jpg"

            return dir_path / thumbnail_filename

        except Exception as e:
            self.logger.error(f"生成缩略图路径失败: {str(e)}")
            raise Exception(f"生成缩略图路径失败: {str(e)}")

    def save_photo_file(self, source_path: str, taken_at: datetime, filename: str) -> Tuple[Path, str]:
        """
        保存照片文件到存储目录

        Args:
            source_path: 源文件路径
            taken_at: 拍摄时间
            filename: 原始文件名

        Returns:
            (保存后的路径, 新文件名)
        """
        try:
            # 生成目标路径
            target_path, new_filename = self.generate_photo_path(taken_at, filename)

            # 复制文件
            shutil.copy2(source_path, target_path)

            self.logger.info(f"照片文件保存成功: {target_path}")
            return target_path, new_filename

        except Exception as e:
            self.logger.error(f"保存照片文件失败: {str(e)}")
            raise Exception(f"保存照片文件失败: {str(e)}")

    def save_thumbnail_file(self, thumbnail_data: bytes, photo_id: int, original_filename: str) -> Path:
        """
        保存缩略图文件

        Args:
            thumbnail_data: 缩略图二进制数据
            photo_id: 照片ID
            original_filename: 原始文件名

        Returns:
            保存后的路径
        """
        try:
            # 生成目标路径
            target_path = self.generate_thumbnail_path(photo_id, original_filename)

            # 保存缩略图
            with open(target_path, 'wb') as f:
                f.write(thumbnail_data)

            self.logger.info(f"缩略图保存成功: {target_path}")
            return target_path

        except Exception as e:
            self.logger.error(f"保存缩略图失败: {str(e)}")
            raise Exception(f"保存缩略图失败: {str(e)}")

    def delete_photo_file(self, file_path: str, thumbnail_path: Optional[str] = None) -> bool:
        """
        删除照片文件

        Args:
            file_path: 照片文件路径
            thumbnail_path: 缩略图路径

        Returns:
            删除是否成功
        """
        try:
            # 删除原图
            if file_path and Path(file_path).exists():
                Path(file_path).unlink()
                self.logger.info(f"原图删除成功: {file_path}")

            # 删除缩略图
            if thumbnail_path and Path(thumbnail_path).exists():
                Path(thumbnail_path).unlink()
                self.logger.info(f"缩略图删除成功: {thumbnail_path}")

            return True

        except Exception as e:
            self.logger.error(f"删除照片文件失败: {str(e)}")
            return False

    def move_photo_file(self, source_path: str, taken_at: datetime, filename: str) -> Tuple[Path, str]:
        """
        移动照片文件到正确的存储位置

        Args:
            source_path: 源文件路径
            taken_at: 拍摄时间
            filename: 原始文件名

        Returns:
            (新路径, 新文件名)
        """
        try:
            # 生成目标路径
            target_path, new_filename = self.generate_photo_path(taken_at, filename)

            # 移动文件
            shutil.move(source_path, target_path)

            self.logger.info(f"照片文件移动成功: {source_path} -> {target_path}")
            return target_path, new_filename

        except Exception as e:
            self.logger.error(f"移动照片文件失败: {str(e)}")
            raise Exception(f"移动照片文件失败: {str(e)}")

    def create_backup(self, backup_type: str = "manual") -> Tuple[Path, Dict[str, Any]]:
        """
        创建数据备份

        Args:
            backup_type: 备份类型 (manual, daily, weekly, monthly)

        Returns:
            (备份文件路径, 备份信息)
        """
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"photos_backup_{backup_type}_{timestamp}.zip"
            backup_path = self.backups_path / backup_type / backup_filename

            # 确保备份目录存在
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # 获取备份信息
            backup_info = self._get_backup_info()

            # 创建ZIP备份
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加照片存储目录
                self._add_directory_to_zip(zipf, self.originals_path, "originals")
                self._add_directory_to_zip(zipf, self.thumbnails_path, "thumbnails")

                # 添加数据库文件
                from app.core.config import settings
                from app.core.path_utils import resolve_resource_path
                db_path = resolve_resource_path(settings.database.path)
                if db_path.exists():
                    zipf.write(db_path, "photos.db")

                # 添加备份信息
                info_json = json.dumps(backup_info, indent=2, ensure_ascii=False)
                zipf.writestr("backup_info.json", info_json)

            self.logger.info(f"备份创建成功: {backup_path}")
            return backup_path, backup_info

        except Exception as e:
            self.logger.error(f"创建备份失败: {str(e)}")
            raise Exception(f"创建备份失败: {str(e)}")

    def _get_backup_info(self) -> Dict[str, Any]:
        """
        获取备份信息

        Returns:
            备份信息字典
        """
        try:
            db = next(get_db())

            # 获取照片统计
            total_photos = db.query(Photo).count()
            total_size = db.query(Photo).with_entities(
                db.func.sum(Photo.file_size)
            ).scalar() or 0

            backup_info = {
                "backup_time": datetime.now().isoformat(),
                "total_photos": total_photos,
                "total_size": total_size,
                "storage_info": self.get_storage_info(),
                "version": "2.1.4"
            }

            db.close()
            return backup_info

        except Exception as e:
            self.logger.error(f"获取备份信息失败: {str(e)}")
            return {
                "backup_time": datetime.now().isoformat(),
                "error": str(e)
            }

    def _add_directory_to_zip(self, zipf: zipfile.ZipFile, source_dir: Path, arcname_prefix: str):
        """
        将目录添加到ZIP文件中

        Args:
            zipf: ZIP文件对象
            source_dir: 源目录
            arcname_prefix: ZIP中的路径前缀
        """
        try:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    # 计算相对路径
                    relative_path = file_path.relative_to(source_dir)
                    arcname = f"{arcname_prefix}/{relative_path}"
                    zipf.write(file_path, arcname)
        except Exception as e:
            self.logger.error(f"添加目录到ZIP失败 {source_dir}: {str(e)}")

    def restore_backup(self, backup_path: str, restore_type: str = "full") -> Dict[str, Any]:
        """
        从备份恢复数据

        Args:
            backup_path: 备份文件路径
            restore_type: 恢复类型 (full, photos, database)

        Returns:
            恢复结果信息
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise Exception("备份文件不存在")

            restore_info = {
                "restore_time": datetime.now().isoformat(),
                "backup_file": str(backup_file),
                "restore_type": restore_type,
                "files_restored": 0,
                "errors": []
            }

            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # 提取文件列表
                file_list = zipf.namelist()

                for file_name in file_list:
                    try:
                        if restore_type == "full" or restore_type == "photos":
                            if file_name.startswith("originals/") or file_name.startswith("thumbnails/"):
                                zipf.extract(file_name, self.base_path)
                                restore_info["files_restored"] += 1

                        if restore_type == "full" or restore_type == "database":
                            if file_name == "photos.db":
                                from app.core.config import settings
                                from app.core.path_utils import resolve_resource_path
                                db_path = resolve_resource_path(settings.database.path)
                                zipf.extract(file_name, db_path.parent)
                                # 如果配置的路径不是默认路径，需要重命名文件
                                if db_path.name != "photos.db":
                                    temp_db_path = db_path.parent / "photos.db"
                                    if temp_db_path.exists():
                                        temp_db_path.rename(db_path)
                                restore_info["database_restored"] = True

                    except Exception as e:
                        restore_info["errors"].append(f"恢复文件失败 {file_name}: {str(e)}")

            self.logger.info(f"数据恢复完成: {restore_info}")
            return restore_info

        except Exception as e:
            self.logger.error(f"数据恢复失败: {str(e)}")
            raise Exception(f"数据恢复失败: {str(e)}")

    def cleanup_temp_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        清理临时文件

        Args:
            max_age_hours: 文件最大保留时间（小时）

        Returns:
            清理结果信息
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            cleanup_info = {
                "cleanup_time": datetime.now().isoformat(),
                "max_age_hours": max_age_hours,
                "files_removed": 0,
                "space_freed": 0,
                "errors": []
            }

            # 清理临时目录
            temp_dirs = [
                self.temp_path / "processing",
                self.temp_path / "uploads",
                self.temp_path / "cache"
            ]

            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    for file_path in temp_dir.rglob('*'):
                        if file_path.is_file():
                            try:
                                # 检查文件修改时间
                                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                                if file_mtime < cutoff_time:
                                    file_size = file_path.stat().st_size
                                    file_path.unlink()
                                    cleanup_info["files_removed"] += 1
                                    cleanup_info["space_freed"] += file_size
                            except Exception as e:
                                cleanup_info["errors"].append(f"清理文件失败 {file_path}: {str(e)}")

            self.logger.info(f"临时文件清理完成: {cleanup_info}")
            return cleanup_info

        except Exception as e:
            self.logger.error(f"临时文件清理失败: {str(e)}")
            raise Exception(f"临时文件清理失败: {str(e)}")

    def check_backup_space(self, backup_path: Path) -> Dict[str, Any]:
        """
        检查备份目标路径的可用空间
        
        Args:
            backup_path: 备份目标路径
        
        Returns:
            空间检查结果
        """
        try:
            import shutil
            
            # 获取系统存储统计
            stats = self.get_storage_stats()
            
            # 计算需要的空间（数据库 + 原图 + 缩略图）
            required_size = (
                stats['database']['size'] +
                stats['originals']['total_size'] +
                stats['thumbnails']['total_size']
            )
            
            # 获取目标路径的磁盘使用情况
            try:
                usage = shutil.disk_usage(str(backup_path))
                free_space = usage.free
            except Exception:
                # 如果路径不存在，尝试使用父目录
                parent_path = backup_path.parent if backup_path.parent != backup_path else Path('C:\\')
                usage = shutil.disk_usage(str(parent_path))
                free_space = usage.free
            
            # 计算可用空间百分比
            available = free_space >= required_size
            free_space_percent = (free_space / usage.total * 100) if usage.total > 0 else 0
            
            return {
                "available": available,
                "free_space": free_space,
                "required_space": required_size,
                "free_space_percent": free_space_percent,
                "message": f"可用空间: {self._format_size(free_space)}, 需要空间: {self._format_size(required_size)}"
            }
            
        except Exception as e:
            self.logger.error(f"检查备份空间失败: {str(e)}")
            return {
                "available": False,
                "free_space": 0,
                "required_space": 0,
                "free_space_percent": 0,
                "message": f"检查空间失败: {str(e)}",
                "error": str(e)
            }
    
    def _format_size(self, bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            bytes: 字节数
        
        Returns:
            格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def _run_robocopy_sync(
        self,
        cmd: list,
        encoding: str = None,
        errors: str = 'replace',
        env: dict = None
    ) -> tuple:
        """
        同步执行 robocopy 命令（在线程池中调用）
        
        Args:
            cmd: robocopy 命令列表
            encoding: 编码格式（None表示使用系统默认）
            errors: 错误处理方式
            env: 环境变量字典（None表示使用系统默认环境变量）
        
        Returns:
            (output, error, exit_code)
        """
        import subprocess
        import os
        
        # 如果提供了环境变量，合并到当前环境变量中
        if env is not None:
            # 复制当前环境变量
            process_env = os.environ.copy()
            # 更新为新提供的环境变量
            process_env.update(env)
        else:
            process_env = None
        
        if encoding:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                encoding=encoding,
                errors=errors,
                env=process_env
            )
        else:
            # 使用系统默认编码
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                errors=errors,
                env=process_env
            )
        return result.stdout, result.stderr, result.returncode
    
    async def backup_files_with_robocopy(
        self,
        source_path: Path,
        dest_path: Path,
        backup_mode: str = "incremental"
    ) -> Dict[str, Any]:
        """
        使用 robocopy 备份文件（Windows系统，异步版本）
        
        Args:
            source_path: 源目录（如 originals）
            dest_path: 目标目录（备份目录下的 originals）
            backup_mode: 备份方式 "full"（覆盖）或 "incremental"（跳过同名）
        
        Returns:
            备份结果信息
        """
        import asyncio
        import platform
        
        if platform.system() != "Windows":
            raise ValueError("此功能仅支持 Windows 系统")
        
        # 确保目标目录存在
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # 构建 robocopy 命令
        # 注意：移除 /NJS 参数，以便获取统计信息
        cmd = [
            "robocopy",
            str(source_path),
            str(dest_path),
            "/E",           # 复制所有子目录和文件
            "/MT:16",       # 多线程（16线程）
            "/R:3",         # 重试3次
            "/W:1",         # 等待1秒
            "/NP",          # 不显示进度百分比
            "/NDL",         # 不记录目录列表
            "/NFL",         # 不记录文件列表
            "/NJH",         # 不显示作业标题
            # 注意：不添加 /NJS，以便获取统计信息
        ]
        
        # 备份方式处理
        if backup_mode == "full":
            # 全量备份（覆盖已存在的文件）
            cmd.extend(["/IS", "/IT"])
        elif backup_mode == "incremental":
            # 增量备份（跳过已存在的文件，只复制较新的或新文件）
            cmd.append("/XO")
        else:
            raise ValueError(f"不支持的备份方式: {backup_mode}")
        
        try:
            import re
            
            # 执行 robocopy（尝试多种编码以处理中文Windows系统）
            # 使用 asyncio.to_thread() 在线程池中执行，避免阻塞事件循环
            output = ""
            error = ""
            exit_code = -1
            
            # 方案1：尝试强制 robocopy 使用英文输出
            # 设置环境变量强制使用英文（Windows可能不支持，但尝试一下）
            import os
            env_english = os.environ.copy()
            # 尝试设置多个可能的环境变量（Windows可能不支持这些，但尝试一下）
            env_english['LANG'] = 'en_US.UTF-8'
            env_english['LC_ALL'] = 'en_US.UTF-8'
            env_english['LC_MESSAGES'] = 'en_US.UTF-8'
            
            # 先尝试GBK编码（Windows中文系统默认）+ 强制英文环境变量
            # 注意：使用 errors='replace' 可以避免编码错误，所以直接尝试即可
            output, error, exit_code = await asyncio.to_thread(
                self._run_robocopy_sync,
                cmd,
                'gbk',
                'replace',
                env_english
            )
            
            # 如果输出为空或异常，尝试其他编码（虽然 errors='replace' 应该能处理）
            if not output and exit_code >= 8:
                # 如果GBK失败，尝试UTF-8（仍然使用英文环境变量）
                try:
                    output, error, exit_code = await asyncio.to_thread(
                        self._run_robocopy_sync,
                        cmd,
                        'utf-8',
                        'replace',
                        env_english
                    )
                except Exception:
                    # 最后尝试使用系统默认编码（仍然使用英文环境变量）
                    output, error, exit_code = await asyncio.to_thread(
                        self._run_robocopy_sync,
                        cmd,
                        None,  # 使用系统默认编码
                        'replace',
                        env_english
                    )
            
            # robocopy 返回码说明：
            # 0-7: 成功（有文件复制）
            # 8+: 错误
            if exit_code >= 8:
                raise Exception(f"robocopy 执行失败，返回码: {exit_code}, 错误: {error}")
            
            # 解析输出获取统计信息
            bytes_copied = None
            files_total = None
            files_copied = None
            dirs_total = None
            dirs_copied = None
            elapsed_time = None
            elapsed_seconds = None
            speed = None
            speed_bytes_per_sec = None
            
            # 解析 Bytes（支持 k、M、G、T 等单位）
            # robocopy 输出格式: Bytes :    10.0 k    10.0 k         0         0         0         0
            # 中文格式: 字节:    10.0 k    10.0 k         0         0         0         0
            # 列含义: Total, Copied, Skipped, Mismatch, FAILED, Extras
            # 我们需要 Total（第一个值）和 Copied（第二个值）
            # 方案3：多语言解析（作为回退方案，同时支持中英文）
            bytes_patterns = [
                r'(?:Bytes|字节)\s*:\s*([\d,]+\.?\d*)\s*([kmgt]?)\s+([\d,]+\.?\d*)\s*([kmgt]?)',  # 格式: Bytes/字节 : 10.0 k    10.0 k (Total Copied)
                r'(?:Bytes|字节)\s*:\s*([\d,]+\.?\d*)\s*([kmgt]?)',  # 简化格式（只有Total）
            ]
            
            bytes_total = None
            bytes_copied = None
            
            for pattern in bytes_patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    # 解析 Total（第一个值）
                    total_value_str = match.group(1).replace(',', '')
                    total_unit = match.group(2).lower() if len(match.groups()) > 1 and match.group(2) else ''
                    try:
                        total_value = float(total_value_str)
                        total_multiplier = 1
                        if total_unit == 'k':
                            total_multiplier = 1024
                        elif total_unit == 'm':
                            total_multiplier = 1024 * 1024
                        elif total_unit == 'g':
                            total_multiplier = 1024 * 1024 * 1024
                        elif total_unit == 't':
                            total_multiplier = 1024 * 1024 * 1024 * 1024
                        bytes_total = int(total_value * total_multiplier)
                        
                        # 如果有第二个值（Copied），解析它
                        if len(match.groups()) >= 4 and match.group(3):
                            copied_value_str = match.group(3).replace(',', '')
                            copied_unit = match.group(4).lower() if match.group(4) else ''
                            try:
                                copied_value = float(copied_value_str)
                                copied_multiplier = 1
                                if copied_unit == 'k':
                                    copied_multiplier = 1024
                                elif copied_unit == 'm':
                                    copied_multiplier = 1024 * 1024
                                elif copied_unit == 'g':
                                    copied_multiplier = 1024 * 1024 * 1024
                                elif copied_unit == 't':
                                    copied_multiplier = 1024 * 1024 * 1024 * 1024
                                bytes_copied = int(copied_value * copied_multiplier)
                            except ValueError:
                                pass
                        else:
                            # 如果没有第二个值，Copied = Total
                            bytes_copied = bytes_total
                        break
                    except ValueError:
                        continue
            
            # 解析 Files（Total 和 Copied）
            # 方案3：多语言解析（同时支持中英文）
            # 英文格式: Files : 11 11
            # 中文格式: 文件: 11 11
            files_pattern = r'(?:Files|文件)\s*:\s*(\d+)\s+(\d+)'
            match = re.search(files_pattern, output, re.IGNORECASE)
            if match:
                files_total = int(match.group(1))
                files_copied = int(match.group(2))
            
            # 解析 Dirs（Total 和 Copied）
            # 方案3：多语言解析（同时支持中英文）
            # 英文格式: Dirs : 3 3
            # 中文格式: 目录: 3 3
            dirs_pattern = r'(?:Dirs|目录)\s*:\s*(\d+)\s+(\d+)'
            match = re.search(dirs_pattern, output, re.IGNORECASE)
            if match:
                dirs_total = int(match.group(1))
                dirs_copied = int(match.group(2))
            
            # 解析 Times（时长）
            # robocopy Times 格式: Times :   Total    Copied   Skipped  Mismatch    FAILED    Extras
            # 中文格式: 时间:   Total    Copied   Skipped  Mismatch    FAILED    Extras
            # 在多线程模式下，Total是所有线程的时间总和，Copied才是实际运行时间
            # 我们需要解析第二列（Copied time），而不是第一列（Total time）
            # 方案3：多语言解析（同时支持中英文）
            times_pattern = r'(?:Times|时间)\s*:\s*(\d+):(\d+):(\d+)\s+(\d+):(\d+):(\d+)'  # 匹配两列时间
            match = re.search(times_pattern, output, re.IGNORECASE)
            if match:
                # 第一列是Total time（所有线程时间总和，多线程模式下不准确）
                # 第二列是Copied time（实际复制时间，这是实际运行时间）
                # 我们使用第二列（Copied time）
                hours = int(match.group(4))  # 第二列的小时
                minutes = int(match.group(5))  # 第二列的分钟
                seconds = int(match.group(6))  # 第二列的秒
                elapsed_seconds = hours * 3600 + minutes * 60 + seconds
                elapsed_time = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                # 回退：如果无法匹配两列，尝试匹配单列（向后兼容）
                times_patterns = [
                    r'(?:Times|时间)\s*:\s*(\d+):(\d+):(\d+)',  # 标准格式: Times/时间 : 0:00:01
                    r'(\d+):(\d+):(\d+)\s+elapsed',    # elapsed格式
                ]
                for pattern in times_patterns:
                    match = re.search(pattern, output, re.IGNORECASE)
                    if match:
                        hours = int(match.group(1))
                        minutes = int(match.group(2))
                        seconds = int(match.group(3))
                        elapsed_seconds = hours * 3600 + minutes * 60 + seconds
                        elapsed_time = f"{hours}:{minutes:02d}:{seconds:02d}"
                        break
            
            # 解析 Speed（优先使用 Bytes/sec）
            # 方案3：多语言解析（同时支持中英文）
            # 英文格式: Speed : 845,026,348 Bytes/sec
            # 中文格式: 速度: 845,026,348 字节/秒
            speed_pattern = r'(?:Speed|速度)\s*:\s*([\d,]+\.?\d*)\s*([KMGT]?Bytes?/sec|字节/秒)'
            match = re.search(speed_pattern, output, re.IGNORECASE)
            if match:
                speed_value = match.group(1).replace(',', '')
                speed_unit = match.group(2)
                speed = f"{speed_value} {speed_unit}"
                # 转换为字节/秒
                try:
                    value = float(speed_value)
                    multiplier = 1
                    # 处理英文单位
                    if speed_unit.upper().startswith('K'):
                        multiplier = 1024
                    elif speed_unit.upper().startswith('M'):
                        multiplier = 1024 * 1024
                    elif speed_unit.upper().startswith('G'):
                        multiplier = 1024 * 1024 * 1024
                    # 处理中文单位（字节/秒，已经是字节单位，multiplier=1）
                    elif '字节' in speed_unit or 'Bytes' in speed_unit:
                        multiplier = 1
                    speed_bytes_per_sec = int(value * multiplier)
                except:
                    pass
            
            return {
                "success": True,
                "exit_code": exit_code,
                "output": output,
                "source": str(source_path),
                "dest": str(dest_path),
                "mode": backup_mode,
                # 解析的统计信息
                "bytes_total": bytes_total,      # 总字节数（所有文件）
                "bytes_copied": bytes_copied,     # 实际复制的字节数
                "files_total": files_total,
                "files_copied": files_copied,
                "dirs_total": dirs_total,
                "dirs_copied": dirs_copied,
                "elapsed_time": elapsed_time,
                "elapsed_seconds": elapsed_seconds,
                "speed": speed,
                "speed_bytes_per_sec": speed_bytes_per_sec
            }
            
        except Exception as e:
            self.logger.error(f"执行 robocopy 失败: {str(e)}")
            raise Exception(f"执行备份失败: {str(e)}")
    
    def get_backup_list(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取备份文件列表

        Returns:
            备份文件列表
        """
        try:
            backup_types = ["manual", "daily", "weekly", "monthly"]
            result = {}

            for backup_type in backup_types:
                backup_dir = self.backups_path / backup_type
                if backup_dir.exists():
                    backups = []
                    for backup_file in backup_dir.glob("*.zip"):
                        backup_info = {
                            "filename": backup_file.name,
                            "path": str(backup_file),
                            "size": backup_file.stat().st_size,
                            "created_time": datetime.fromtimestamp(backup_file.stat().st_ctime).isoformat(),
                            "modified_time": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
                        }
                        backups.append(backup_info)

                    # 按创建时间排序
                    backups.sort(key=lambda x: x["created_time"], reverse=True)
                    result[backup_type] = backups
                else:
                    result[backup_type] = []

            return result

        except Exception as e:
            self.logger.error(f"获取备份列表失败: {str(e)}")
            return {"error": str(e)}

    def validate_file_integrity(self, file_path: str, expected_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        验证文件完整性

        Args:
            file_path: 文件路径
            expected_hash: 期望的哈希值

        Returns:
            验证结果信息
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {"valid": False, "error": "文件不存在"}

            # 计算文件哈希
            sha256_hash = hashlib.sha256()
            with open(file_path_obj, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            actual_hash = sha256_hash.hexdigest()

            result = {
                "file_path": str(file_path_obj),
                "file_size": file_path_obj.stat().st_size,
                "actual_hash": actual_hash,
                "valid": True
            }

            # 如果提供了期望哈希，进行比较
            if expected_hash:
                result["expected_hash"] = expected_hash
                result["hash_match"] = actual_hash == expected_hash
                if not result["hash_match"]:
                    result["valid"] = False
                    result["error"] = "文件哈希不匹配"

            return result

        except Exception as e:
            self.logger.error(f"文件完整性验证失败 {file_path}: {str(e)}")
            return {
                "file_path": str(file_path),
                "valid": False,
                "error": str(e)
            }
