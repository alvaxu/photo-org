#!/usr/bin/env python3
"""
存储清理和修复脚本

清理存储目录和数据库中的不一致数据
"""

import sqlite3
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Set

def calculate_file_hash(file_path: str) -> str:
    """计算文件MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_database_photos(db_path: str) -> Dict[str, Dict]:
    """获取数据库中的所有照片记录"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, filename, original_path, file_hash, status 
        FROM photos 
        ORDER BY id
    ''')
    
    photos = {}
    for row in cursor.fetchall():
        photo_id, filename, original_path, file_hash, status = row
        photos[file_hash] = {
            'id': photo_id,
            'filename': filename,
            'original_path': original_path,
            'file_hash': file_hash,
            'status': status
        }
    
    conn.close()
    return photos

def get_storage_files(storage_path: Path) -> Dict[str, str]:
    """获取存储目录中的所有文件"""
    files = {}
    
    if not storage_path.exists():
        return files
    
    for year_dir in storage_path.iterdir():
        if not year_dir.is_dir():
            continue
            
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
                
            for file_path in month_dir.iterdir():
                if file_path.is_file():
                    try:
                        file_hash = calculate_file_hash(str(file_path))
                        files[file_hash] = str(file_path)
                    except Exception as e:
                        print(f"计算文件哈希失败 {file_path}: {e}")
    
    return files

def find_orphan_files(db_photos: Dict[str, Dict], storage_files: Dict[str, str]) -> List[str]:
    """查找孤立的存储文件（没有对应数据库记录）"""
    orphan_files = []
    
    for file_hash, file_path in storage_files.items():
        if file_hash not in db_photos:
            orphan_files.append(file_path)
    
    return orphan_files

def find_missing_files(db_photos: Dict[str, Dict], storage_files: Dict[str, str]) -> List[Dict]:
    """查找缺失的存储文件（有数据库记录但没有文件）"""
    missing_files = []
    
    for file_hash, photo_info in db_photos.items():
        if file_hash not in storage_files:
            missing_files.append(photo_info)
    
    return missing_files

def find_duplicate_files(storage_files: Dict[str, str]) -> Dict[str, List[str]]:
    """查找重复的文件（相同哈希的多个文件）"""
    hash_to_files = {}
    
    for file_hash, file_path in storage_files.items():
        if file_hash not in hash_to_files:
            hash_to_files[file_hash] = []
        hash_to_files[file_hash].append(file_path)
    
    # 只返回有重复的哈希
    duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
    return duplicates

def cleanup_orphan_files(orphan_files: List[str], dry_run: bool = True):
    """清理孤立的文件"""
    print(f"\n=== 清理孤立文件 ===")
    print(f"发现 {len(orphan_files)} 个孤立文件")
    
    for file_path in orphan_files:
        if dry_run:
            print(f"[DRY RUN] 将删除: {file_path}")
        else:
            try:
                os.remove(file_path)
                print(f"已删除: {file_path}")
            except Exception as e:
                print(f"删除失败 {file_path}: {e}")

def cleanup_duplicate_files(duplicates: Dict[str, List[str]], dry_run: bool = True):
    """清理重复文件（保留第一个，删除其他）"""
    print(f"\n=== 清理重复文件 ===")
    print(f"发现 {len(duplicates)} 组重复文件")
    
    for file_hash, files in duplicates.items():
        print(f"\n哈希 {file_hash[:16]}... 的重复文件:")
        for i, file_path in enumerate(files):
            if i == 0:
                print(f"  保留: {file_path}")
            else:
                if dry_run:
                    print(f"  [DRY RUN] 将删除: {file_path}")
                else:
                    try:
                        os.remove(file_path)
                        print(f"  已删除: {file_path}")
                    except Exception as e:
                        print(f"  删除失败 {file_path}: {e}")

def main():
    print("=== 存储清理和修复工具 ===")
    
    # 配置路径
    db_path = "data/photos.db"
    storage_path = Path("photos_storage/originals")
    
    # 检查文件是否存在
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    if not storage_path.exists():
        print(f"存储目录不存在: {storage_path}")
        return
    
    # 获取数据
    print("正在分析数据库和存储目录...")
    db_photos = get_database_photos(db_path)
    storage_files = get_storage_files(storage_path)
    
    print(f"数据库记录: {len(db_photos)} 张照片")
    print(f"存储文件: {len(storage_files)} 个文件")
    
    # 查找问题
    orphan_files = find_orphan_files(db_photos, storage_files)
    missing_files = find_missing_files(db_photos, storage_files)
    duplicates = find_duplicate_files(storage_files)
    
    print(f"\n=== 问题分析 ===")
    print(f"孤立文件: {len(orphan_files)} 个")
    print(f"缺失文件: {len(missing_files)} 个")
    print(f"重复文件组: {len(duplicates)} 组")
    
    # 显示孤立文件
    if orphan_files:
        print(f"\n孤立文件列表:")
        for file_path in orphan_files[:10]:  # 只显示前10个
            print(f"  {file_path}")
        if len(orphan_files) > 10:
            print(f"  ... 还有 {len(orphan_files) - 10} 个文件")
    
    # 显示缺失文件
    if missing_files:
        print(f"\n缺失文件列表:")
        for photo_info in missing_files[:10]:  # 只显示前10个
            print(f"  ID {photo_info['id']}: {photo_info['filename']} -> {photo_info['original_path']}")
        if len(missing_files) > 10:
            print(f"  ... 还有 {len(missing_files) - 10} 个文件")
    
    # 显示重复文件
    if duplicates:
        print(f"\n重复文件组:")
        for file_hash, files in list(duplicates.items())[:5]:  # 只显示前5组
            print(f"  哈希 {file_hash[:16]}... ({len(files)} 个文件):")
            for file_path in files:
                print(f"    {file_path}")
        if len(duplicates) > 5:
            print(f"  ... 还有 {len(duplicates) - 5} 组重复文件")
    
    # 执行清理（默认为dry run）
    print(f"\n=== 清理操作 ===")
    print("注意：这是 DRY RUN 模式，不会实际删除文件")
    print("要执行实际清理，请运行: python cleanup_storage.py --execute")
    
    cleanup_orphan_files(orphan_files, dry_run=True)
    cleanup_duplicate_files(duplicates, dry_run=True)
    
    print(f"\n=== 清理完成 ===")
    print("建议：")
    print("1. 先备份数据库和存储目录")
    print("2. 运行 python cleanup_storage.py --execute 执行实际清理")
    print("3. 重新导入照片以确保数据一致性")

if __name__ == "__main__":
    import sys
    execute = "--execute" in sys.argv
    
    if execute:
        print("警告：将执行实际的文件删除操作！")
        response = input("确认继续？(y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            sys.exit(0)
        
        # 重新运行清理，这次实际删除
        main()
        cleanup_orphan_files(find_orphan_files(get_database_photos("data/photos.db"), get_storage_files(Path("photos_storage/originals"))), dry_run=False)
        cleanup_duplicate_files(find_duplicate_files(get_storage_files(Path("photos_storage/originals"))), dry_run=False)
    else:
        main()
