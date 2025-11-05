"""
图像特征向量相似度搜索测试 - 第四步
计算相似度矩阵并对比分析
"""
import sys
import os
import sqlite3
import time
from pathlib import Path
import torch
import torchvision
from torchvision import models, transforms
from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import imagehash

# 导入HEIC支持
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORT = True
except ImportError:
    HEIC_SUPPORT = False

print("=" * 60)
print("步骤4: 计算相似度矩阵并对比分析")
print("=" * 60)
print()

# 1. 加载模型（复用步骤3的逻辑）
print("[4.1] 加载ResNet50模型...")
model_dir = Path("models/resnet50")
model_path = model_dir / "resnet50-0676ba61.pth"

model = models.resnet50(weights=None)
state_dict = torch.load(model_path, map_location='cpu')
model.load_state_dict(state_dict)
model = torch.nn.Sequential(*list(model.children())[:-2])
model = torch.nn.Sequential(
    model,
    torch.nn.AdaptiveAvgPool2d((1, 1)),
    torch.nn.Flatten()
)
model.eval()
print("  ✅ 模型加载成功")

# 2. 定义预处理
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 3. 从数据库读取测试照片
print()
print("[4.2] 从数据库读取测试照片...")
db_path = Path("photo_db/photos.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 测试照片ID：南京2023027-2032 (6张) + 南京2023038-2042 (5张)
test_photo_ids = [21, 22, 26, 27, 28, 29, 40, 41, 42, 8, 15]
placeholders = ','.join(['?'] * len(test_photo_ids))
cursor.execute(f'''
    SELECT id, filename, original_path, perceptual_hash
    FROM photos 
    WHERE id IN ({placeholders})
    ORDER BY id
''', test_photo_ids)

photos = cursor.fetchall()
storage_base = Path("storage")

test_photos_data = []
for photo_id, filename, original_path, perceptual_hash in photos:
    if original_path:
        if os.path.isabs(original_path):
            full_path = Path(original_path)
        else:
            full_path = storage_base / original_path
        
        if full_path.exists():
            test_photos_data.append({
                'id': photo_id,
                'filename': filename,
                'path': full_path,
                'perceptual_hash': perceptual_hash
            })

conn.close()
print(f"  ✅ 读取到 {len(test_photos_data)} 张测试照片")

# 4. 提取特征向量
print()
print("[4.3] 提取特征向量...")
features_dict = {}

for photo in test_photos_data:
    photo_id = photo['id']
    filename = photo['filename']
    file_path = photo['path']
    
    try:
        img = Image.open(file_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img_tensor = preprocess(img).unsqueeze(0)
        
        with torch.no_grad():
            features = model(img_tensor)
            features = features.squeeze(0).numpy()
        
        features_dict[photo_id] = {
            'filename': filename,
            'features': features,
            'perceptual_hash': photo['perceptual_hash']
        }
        
    except Exception as e:
        print(f"  ❌ ID {photo_id} 提取失败: {e}")

print(f"  ✅ 成功提取 {len(features_dict)} 张照片的特征向量")

# 5. 计算特征向量相似度矩阵
print()
print("[4.4] 计算特征向量相似度矩阵（余弦相似度）...")
photo_ids = sorted(features_dict.keys())
n = len(photo_ids)

# 构建特征矩阵
features_matrix = np.array([features_dict[pid]['features'] for pid in photo_ids])

# 计算余弦相似度矩阵
similarity_matrix = cosine_similarity(features_matrix)

print("  特征向量相似度矩阵:")
print("      ", end="")
for pid in photo_ids:
    # 显示照片名（去掉扩展名，只显示前15个字符）
    name = Path(features_dict[pid]['filename']).stem
    display_name = name[:15] if len(name) > 15 else name
    print(f"{display_name:15s} ", end="")
print()

for i, pid1 in enumerate(photo_ids):
    name1 = Path(features_dict[pid1]['filename']).stem
    display_name1 = name1[:15] if len(name1) > 15 else name1
    print(f"  {display_name1:15s} ", end="")
    for j, pid2 in enumerate(photo_ids):
        sim = similarity_matrix[i][j]
        print(f"{sim:5.2f} ", end="")
    print()

# 6. 计算Hash相似度矩阵（对比）
print()
print("[4.5] 计算Hash相似度矩阵（汉明距离转换）...")
max_distance = 64  # 16字符hash = 64位

hash_similarity_matrix = np.zeros((n, n))
for i, pid1 in enumerate(photo_ids):
    for j, pid2 in enumerate(photo_ids):
        if i == j:
            hash_similarity_matrix[i][j] = 1.0
        else:
            hash1 = features_dict[pid1]['perceptual_hash']
            hash2 = features_dict[pid2]['perceptual_hash']
            
            if hash1 and hash2 and len(hash1) == len(hash2):
                try:
                    h1 = imagehash.hex_to_hash(hash1)
                    h2 = imagehash.hex_to_hash(hash2)
                    distance = h1 - h2
                    similarity = (max_distance - distance) / max_distance
                    hash_similarity_matrix[i][j] = similarity
                except:
                    hash_similarity_matrix[i][j] = 0.0

print("  Hash相似度矩阵:")
print("      ", end="")
for pid in photo_ids:
    # 显示照片名（去掉扩展名，只显示前15个字符）
    name = Path(features_dict[pid]['filename']).stem
    display_name = name[:15] if len(name) > 15 else name
    print(f"{display_name:15s} ", end="")
print()

for i, pid1 in enumerate(photo_ids):
    name1 = Path(features_dict[pid1]['filename']).stem
    display_name1 = name1[:15] if len(name1) > 15 else name1
    print(f"  {display_name1:15s} ", end="")
    for j, pid2 in enumerate(photo_ids):
        sim = hash_similarity_matrix[i][j]
        print(f"{sim:5.2f} ", end="")
    print()

# 7. 详细对比分析
print()
print("[4.6] 详细对比分析...")
print()

# 分析第一组照片（南京2023027-2032）
group1_ids = [21, 22, 26, 27, 28, 29]
group2_ids = [40, 41, 42, 8, 15]  # 南京2023038-2042

print("=" * 60)
print("第一组照片分析（南京2023027-2032）")
print("=" * 60)
print()

for ref_id in group1_ids:
    if ref_id not in photo_ids:
        continue
    
    ref_idx = photo_ids.index(ref_id)
    ref_filename = features_dict[ref_id]['filename']
    
    print(f"参考照片: {ref_filename}")
    print()
    
    # 特征向量相似度
    feature_matches = []
    for pid in group1_ids:
        if pid != ref_id and pid in photo_ids:
            idx = photo_ids.index(pid)
            sim = similarity_matrix[ref_idx][idx]
            status = "✅" if sim > 0.8 else "❌"
            filename = features_dict[pid]['filename']
            feature_matches.append((pid, filename, sim, sim > 0.8))
    
    # Hash相似度
    hash_matches = []
    for pid in group1_ids:
        if pid != ref_id and pid in photo_ids:
            idx = photo_ids.index(pid)
            sim = hash_similarity_matrix[ref_idx][idx]
            status = "✅" if sim > 0.5 else "❌"
            filename = features_dict[pid]['filename']
            hash_matches.append((pid, filename, sim, sim > 0.5))
    
    print("  特征向量相似度（阈值>0.8）:")
    for _, filename, sim, _ in sorted(feature_matches, key=lambda x: x[2], reverse=True):
        status = "✅" if sim > 0.8 else "❌"
        print(f"    {status} {filename}: {sim:.4f}")
    
    print("  Hash相似度（阈值>0.5）:")
    for _, filename, sim, _ in sorted(hash_matches, key=lambda x: x[2], reverse=True):
        status = "✅" if sim > 0.5 else "❌"
        print(f"    {status} {filename}: {sim:.4f}")
    
    feature_count = sum(1 for _, _, _, matched in feature_matches if matched)
    hash_count = sum(1 for _, _, _, matched in hash_matches if matched)
    print(f"  对比: 特征向量 {feature_count}/{len(feature_matches)} vs Hash {hash_count}/{len(hash_matches)}")
    print()

print()
print("=" * 60)
print("第二组照片分析（南京2023038-2042）")
print("=" * 60)
print()

for ref_id in group2_ids:
    if ref_id not in photo_ids:
        continue
    
    ref_idx = photo_ids.index(ref_id)
    ref_filename = features_dict[ref_id]['filename']
    
    print(f"参考照片: {ref_filename}")
    print()
    
    # 特征向量相似度（在本组内）
    feature_matches = []
    for pid in group2_ids:
        if pid != ref_id and pid in photo_ids:
            idx = photo_ids.index(pid)
            sim = similarity_matrix[ref_idx][idx]
            status = "✅" if sim > 0.8 else "❌"
            filename = features_dict[pid]['filename']
            feature_matches.append((pid, filename, sim, sim > 0.8))
    
    # Hash相似度（在本组内）
    hash_matches = []
    for pid in group2_ids:
        if pid != ref_id and pid in photo_ids:
            idx = photo_ids.index(pid)
            sim = hash_similarity_matrix[ref_idx][idx]
            status = "✅" if sim > 0.5 else "❌"
            filename = features_dict[pid]['filename']
            hash_matches.append((pid, filename, sim, sim > 0.5))
    
    print("  特征向量相似度（阈值>0.8）:")
    for _, filename, sim, _ in sorted(feature_matches, key=lambda x: x[2], reverse=True):
        status = "✅" if sim > 0.8 else "❌"
        print(f"    {status} {filename}: {sim:.4f}")
    
    print("  Hash相似度（阈值>0.5）:")
    for _, filename, sim, _ in sorted(hash_matches, key=lambda x: x[2], reverse=True):
        status = "✅" if sim > 0.5 else "❌"
        print(f"    {status} {filename}: {sim:.4f}")
    
    feature_count = sum(1 for _, _, _, matched in feature_matches if matched)
    hash_count = sum(1 for _, _, _, matched in hash_matches if matched)
    print(f"  对比: 特征向量 {feature_count}/{len(feature_matches)} vs Hash {hash_count}/{len(hash_matches)}")
    print()

# 总体统计
print()
print("=" * 60)
print("总体统计")
print("=" * 60)
print()

# 计算所有照片对的匹配情况
total_feature_matches = 0
total_hash_matches = 0
total_pairs = 0

for i, pid1 in enumerate(photo_ids):
    for j, pid2 in enumerate(photo_ids):
        if i < j:  # 只计算上三角，避免重复
            total_pairs += 1
            if similarity_matrix[i][j] > 0.8:
                total_feature_matches += 1
            if hash_similarity_matrix[i][j] > 0.5:
                total_hash_matches += 1

print(f"总照片对数: {total_pairs}")
print(f"特征向量方法找到相似照片对: {total_feature_matches}/{total_pairs} ({total_feature_matches/total_pairs*100:.1f}%)")
print(f"Hash方法找到相似照片对: {total_hash_matches}/{total_pairs} ({total_hash_matches/total_pairs*100:.1f}%)")
print(f"差异: 特征向量方法多找到 {total_feature_matches - total_hash_matches} 对相似照片")

print()
print("=" * 60)
print("✅ 步骤4完成: 相似度计算和对比分析完成")
print("=" * 60)

