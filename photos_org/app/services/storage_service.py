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


class StorageService:
    """
    存储管理服务类
    负责文件存储、备份、清理等存储相关功能
    """

    def __init__(self):
        """初始化存储服务"""
        self.logger = get_logger(__name__)
        self.base_path = Path(settings.storage.base_path)
        self.originals_path = self.base_path / settings.storage.originals_path
        self.thumbnails_path = self.base_path / settings.storage.thumbnails_path
        self.temp_path = self.base_path / settings.storage.temp_path
        self.backups_path = self.base_path / settings.storage.backups_path

        # 确保目录存在
        self._ensure_directories()

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
                db_path = Path(settings.database.path)
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
                "version": "1.0.0"
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
                                db_path = Path(settings.database.path)
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
