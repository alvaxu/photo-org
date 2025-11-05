"""
图像特征向量相似度搜索测试 - 第二步
从数据库读取测试照片
"""
import sys
import sqlite3
import os
from pathlib import Path

print("=" * 60)
print("步骤2: 从数据库读取测试照片")
print("=" * 60)
print()

# 1. 连接数据库
print("[2.1] 连接数据库...")
db_path = Path("photo_db/photos.db")
if not db_path.exists():
    print(f"  ❌ 数据库文件不存在: {db_path}")
    sys.exit(1)

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    print(f"  ✅ 成功连接到数据库: {db_path}")
except Exception as e:
    print(f"  ❌ 数据库连接失败: {e}")
    sys.exit(1)

# 2. 查询测试照片
print()
print("[2.2] 查询测试照片...")
test_photo_ids = [21, 22, 26, 27, 28, 29]

try:
    placeholders = ','.join(['?'] * len(test_photo_ids))
    cursor.execute(f'''
        SELECT id, filename, original_path, perceptual_hash, taken_at
        FROM photos 
        WHERE id IN ({placeholders})
        ORDER BY id
    ''', test_photo_ids)
    
    photos = cursor.fetchall()
    print(f"  ✅ 找到 {len(photos)} 张测试照片")
    
    if len(photos) != len(test_photo_ids):
        found_ids = [p[0] for p in photos]
        missing_ids = [pid for pid in test_photo_ids if pid not in found_ids]
        print(f"  ⚠️  缺少照片ID: {missing_ids}")
    
except Exception as e:
    print(f"  ❌ 查询失败: {e}")
    conn.close()
    sys.exit(1)

# 3. 检查文件路径
print()
print("[2.3] 检查照片文件路径...")
storage_base = Path("storage")
test_photos_data = []

for photo_id, filename, original_path, perceptual_hash, taken_at in photos:
    # 构建完整路径
    if original_path:
        # 如果路径已经是绝对路径，直接使用；否则拼接storage路径
        if os.path.isabs(original_path):
            full_path = Path(original_path)
        else:
            full_path = storage_base / original_path
    else:
        print(f"  ⚠️  ID {photo_id} ({filename}): 无文件路径")
        continue
    
    # 检查文件是否存在
    exists = full_path.exists()
    status = "✅" if exists else "❌"
    
    if exists:
        file_size_mb = full_path.stat().st_size / 1024 / 1024
        print(f"  {status} ID {photo_id:2d}: {filename}")
        print(f"      路径: {full_path}")
        print(f"      大小: {file_size_mb:.2f} MB")
        print(f"      Hash: {perceptual_hash}")
        print(f"      时间: {taken_at}")
        
        test_photos_data.append({
            'id': photo_id,
            'filename': filename,
            'path': full_path,
            'perceptual_hash': perceptual_hash,
            'taken_at': taken_at
        })
    else:
        print(f"  {status} ID {photo_id:2d}: {filename}")
        print(f"      ❌ 文件不存在: {full_path}")

print()

# 4. 验证测试数据
print("[2.4] 验证测试数据...")
if len(test_photos_data) == len(test_photo_ids):
    print(f"  ✅ 所有 {len(test_photos_data)} 张测试照片文件都存在")
else:
    print(f"  ⚠️  只有 {len(test_photos_data)}/{len(test_photo_ids)} 张照片可用")

if len(test_photos_data) < 2:
    print("  ❌ 测试照片数量不足，至少需要2张")
    conn.close()
    sys.exit(1)

conn.close()

print()
print("=" * 60)
print("✅ 步骤2完成: 测试照片数据准备完成")
print("=" * 60)
print()
print(f"准备测试的照片列表:")
for photo in test_photos_data:
    print(f"  - ID {photo['id']:2d}: {photo['filename']}")
print()
print("下一步: 图像预处理和特征提取")
print("  请运行: python test_image_features_step3.py")

