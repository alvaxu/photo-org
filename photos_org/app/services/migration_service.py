'''
程序说明：

## 1. 文件迁移服务
负责在用户更改存储路径时，将照片文件从旧位置迁移到新位置

## 2. 主要功能
- 检测路径变更
- 迁移文件（原图、缩略图、备份等）
- 更新数据库路径记录
- 清理旧目录（可选）

'''

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.photo import Photo
from app.core.config import settings
from app.services.storage_service import StorageService
import logging

logger = logging.getLogger(__name__)


class MigrationService:
    """文件迁移服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.storage_service = StorageService()
    
    def migrate_storage_path(self, old_base_path: str, new_base_path: str) -> Dict[str, Any]:
        """
        迁移存储路径
        
        :param old_base_path: 旧的存储路径
        :param new_base_path: 新的存储路径
        :return: 迁移结果
        """
        try:
            old_path = Path(old_base_path)
            new_path = Path(new_base_path)
            
            # 检查旧路径是否存在
            if not old_path.exists():
                return {
                    'success': False,
                    'message': f'旧路径不存在: {old_base_path}',
                    'migrated_files': 0,
                    'failed_files': 0
                }
            
            # 创建新路径
            new_path.mkdir(parents=True, exist_ok=True)
            
            # 迁移各个子目录
            result = {
                'success': True,
                'message': '迁移完成',
                'migrated_files': 0,
                'failed_files': 0,
                'details': {}
            }
            
            # 需要迁移的子目录
            subdirs = ['originals', 'thumbnails', 'backups', 'temp']
            
            for subdir in subdirs:
                old_subdir = old_path / subdir
                new_subdir = new_path / subdir
                
                if old_subdir.exists():
                    # 创建新子目录
                    new_subdir.mkdir(parents=True, exist_ok=True)
                    
                    # 迁移文件
                    subdir_result = self._migrate_directory(old_subdir, new_subdir)
                    result['migrated_files'] += subdir_result['migrated_files']
                    result['failed_files'] += subdir_result['failed_files']
                    result['details'][subdir] = subdir_result
            
            # 更新数据库中的路径
            self._update_database_paths(old_base_path, new_base_path)
            
            logger.info(f'存储路径迁移完成: {old_base_path} -> {new_base_path}')
            return result
            
        except Exception as e:
            logger.error(f'存储路径迁移失败: {str(e)}')
            return {
                'success': False,
                'message': f'迁移失败: {str(e)}',
                'migrated_files': 0,
                'failed_files': 0
            }
    
    def _migrate_directory(self, old_dir: Path, new_dir: Path) -> Dict[str, Any]:
        """
        迁移单个目录
        
        :param old_dir: 旧目录路径
        :param new_dir: 新目录路径
        :return: 迁移结果
        """
        migrated_files = 0
        failed_files = 0
        
        try:
            # 遍历旧目录中的所有文件
            for file_path in old_dir.rglob('*'):
                if file_path.is_file():
                    # 计算相对路径
                    relative_path = file_path.relative_to(old_dir)
                    new_file_path = new_dir / relative_path
                    
                    # 创建目标目录
                    new_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(file_path, new_file_path)
                    migrated_files += 1
                    
        except Exception as e:
            logger.error(f'迁移目录失败 {old_dir} -> {new_dir}: {str(e)}')
            failed_files += 1
        
        return {
            'migrated_files': migrated_files,
            'failed_files': failed_files
        }
    
    def _update_database_paths(self, old_base_path: str, new_base_path: str):
        """
        更新数据库中的路径记录
        
        :param old_base_path: 旧的存储路径
        :param new_base_path: 新的存储路径
        """
        try:
            # 获取所有照片记录
            photos = self.db.query(Photo).all()
            
            for photo in photos:
                # 更新原图路径
                if photo.original_path and photo.original_path.startswith(old_base_path):
                    new_original_path = photo.original_path.replace(old_base_path, new_base_path)
                    photo.original_path = new_original_path
                
                # 更新缩略图路径
                if photo.thumbnail_path and photo.thumbnail_path.startswith(old_base_path):
                    new_thumbnail_path = photo.thumbnail_path.replace(old_base_path, new_base_path)
                    photo.thumbnail_path = new_thumbnail_path
            
            # 提交更改
            self.db.commit()
            logger.info(f'数据库路径更新完成: {len(photos)} 条记录')
            
        except Exception as e:
            logger.error(f'更新数据库路径失败: {str(e)}')
            self.db.rollback()
            raise
    
    def cleanup_old_directory(self, old_base_path: str, backup: bool = True) -> bool:
        """
        清理旧目录
        
        :param old_base_path: 旧目录路径
        :param backup: 是否先备份
        :return: 是否成功
        """
        try:
            old_path = Path(old_base_path)
            
            if not old_path.exists():
                return True
            
            if backup:
                # 创建备份
                backup_path = old_path.parent / f"{old_path.name}_backup_{int(time.time())}"
                shutil.move(str(old_path), str(backup_path))
                logger.info(f'旧目录已备份到: {backup_path}')
            else:
                # 直接删除
                shutil.rmtree(str(old_path))
                logger.info(f'旧目录已删除: {old_path}')
            
            return True
            
        except Exception as e:
            logger.error(f'清理旧目录失败: {str(e)}')
            return False
