#!/usr/bin/env python3
"""
缩略图清理工具

删除与originals目录中文件名不匹配的缩略图文件
用于清理孤立的缩略图，保持存储一致性

使用方法:
    python tools/cleanup_thumbnails.py          # 预览模式（不实际删除）
    python tools/cleanup_thumbnails.py --execute # 执行实际删除
"""

import os
import sys
from pathlib import Path
from typing import Set, List

def get_original_filenames(originals_path: Path) -> Set[str]:
    """
    获取originals目录中的所有文件名（不含扩展名）
    
    :param originals_path: originals目录路径
    :return: 原始文件名集合
    """
    original_names = set()
    
    if not originals_path.exists():
        return original_names
    
    for year_dir in originals_path.iterdir():
        if not year_dir.is_dir():
            continue
            
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
                
            for file_path in month_dir.iterdir():
                if file_path.is_file():
                    # 获取文件名（不含扩展名）
                    name_without_ext = file_path.stem
                    original_names.add(name_without_ext)
    
    return original_names

def get_thumbnail_files(thumbnails_path: Path) -> List[Path]:
    """
    获取thumbnails目录中的所有缩略图文件
    
    :param thumbnails_path: thumbnails目录路径
    :return: 缩略图文件路径列表
    """
    thumbnail_files = []
    
    if not thumbnails_path.exists():
        return thumbnail_files
    
    # 直接扫描thumbnails目录下的所有文件
    for file_path in thumbnails_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            thumbnail_files.append(file_path)
    
    return thumbnail_files

def extract_original_name_from_thumbnail(thumbnail_path: Path) -> str:
    """
    从缩略图文件名中提取原始文件名
    
    :param thumbnail_path: 缩略图文件路径
    :return: 提取的原始文件名
    """
    filename = thumbnail_path.name
    
    # 处理不同的缩略图命名格式
    if '_thumb' in filename:
        # 格式: originalname_thumb.jpg 或 photo_id_originalname_thumb.jpg
        parts = filename.split('_thumb')
        if len(parts) > 0:
            name_part = parts[0]
            # 如果包含下划线，可能是photo_id_originalname格式
            if '_' in name_part:
                # 尝试提取原始文件名（去掉可能的photo_id）
                # 对于tmp开头的文件，直接使用整个name_part
                if name_part.startswith('tmp'):
                    return name_part
                else:
                    # 对于其他格式，去掉第一个下划线前的部分
                    return '_'.join(name_part.split('_')[1:])
            else:
                return name_part
    elif filename.startswith('tmp'):
        # 临时文件，直接返回文件名
        return filename
    
    # 默认情况，去掉扩展名
    return thumbnail_path.stem

def cleanup_thumbnails(originals_path: Path, thumbnails_path: Path, dry_run: bool = True):
    """
    清理缩略图
    
    :param originals_path: originals目录路径
    :param thumbnails_path: thumbnails目录路径
    :param dry_run: 是否为预览模式
    """
    print("=== 缩略图清理工具 ===")
    
    # 获取原始文件名
    print("正在扫描originals目录...")
    original_names = get_original_filenames(originals_path)
    print(f"找到 {len(original_names)} 个原始文件")
    
    # 获取缩略图文件
    print("正在扫描thumbnails目录...")
    thumbnail_files = get_thumbnail_files(thumbnails_path)
    print(f"找到 {len(thumbnail_files)} 个缩略图文件")
    
    # 找出需要删除的缩略图
    files_to_delete = []
    files_to_keep = []
    
    for thumbnail_path in thumbnail_files:
        original_name = extract_original_name_from_thumbnail(thumbnail_path)
        
        if original_name in original_names:
            files_to_keep.append(thumbnail_path)
        else:
            files_to_delete.append(thumbnail_path)
    
    print(f"\n=== 清理结果 ===")
    print(f"保留的缩略图: {len(files_to_keep)} 个")
    print(f"需要删除的缩略图: {len(files_to_delete)} 个")
    
    if files_to_keep:
        print(f"\n保留的文件:")
        for file_path in files_to_keep:
            print(f"  ✅ {file_path.name}")
    
    if files_to_delete:
        print(f"\n需要删除的文件:")
        for file_path in files_to_delete:
            print(f"  ❌ {file_path.name}")
    
    # 执行删除
    if files_to_delete:
        if dry_run:
            print(f"\n[预览模式] 将删除 {len(files_to_delete)} 个缩略图文件")
            print("要执行实际删除，请运行: python tools/cleanup_thumbnails.py --execute")
        else:
            print(f"\n正在删除 {len(files_to_delete)} 个缩略图文件...")
            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    print(f"已删除: {file_path.name}")
                except Exception as e:
                    print(f"删除失败 {file_path.name}: {e}")
            
            print(f"\n删除完成: 成功删除 {deleted_count}/{len(files_to_delete)} 个文件")
    else:
        print("\n没有需要删除的缩略图文件")

def main():
    """主函数"""
    # 确保在项目根目录运行
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    originals_path = Path("photos_storage/originals")
    thumbnails_path = Path("photos_storage/thumbnails")
    
    # 检查目录是否存在
    if not originals_path.exists():
        print(f"错误: originals目录不存在: {originals_path}")
        print("请确保在项目根目录运行此脚本")
        return
    
    if not thumbnails_path.exists():
        print(f"错误: thumbnails目录不存在: {thumbnails_path}")
        print("请确保在项目根目录运行此脚本")
        return
    
    # 执行清理（默认为预览模式）
    cleanup_thumbnails(originals_path, thumbnails_path, dry_run=True)

if __name__ == "__main__":
    execute = "--execute" in sys.argv
    
    if execute:
        print("⚠️  警告：将执行实际的缩略图删除操作！")
        response = input("确认继续？(y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            sys.exit(0)
        
        # 执行实际删除
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        os.chdir(project_root)
        
        originals_path = Path("photos_storage/originals")
        thumbnails_path = Path("photos_storage/thumbnails")
        cleanup_thumbnails(originals_path, thumbnails_path, dry_run=False)
    else:
        main()
