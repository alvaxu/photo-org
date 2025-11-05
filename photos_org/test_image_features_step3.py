"""
图像特征向量相似度搜索测试 - 第三步
图像预处理和特征提取
"""
import sys
import sqlite3
import time
from pathlib import Path
import torch
import torchvision
from torchvision import models, transforms
from PIL import Image
import numpy as np

# 导入HEIC支持
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORT = True
except ImportError:
    HEIC_SUPPORT = False

print("=" * 60)
print("步骤3: 图像预处理和特征提取")
print("=" * 60)
print()

# 1. 加载模型（复用步骤1的逻辑）
print("[3.1] 加载ResNet50模型...")
try:
    model_dir = Path("models/resnet50")
    model_path = model_dir / "resnet50-0676ba61.pth"
    
    # 加载完整模型
    model = models.resnet50(weights=None)
    state_dict = torch.load(model_path, map_location='cpu')
    model.load_state_dict(state_dict)
    
    # 移除分类层，只保留特征提取部分
    model = torch.nn.Sequential(*list(model.children())[:-2])  # 移除avgpool和fc
    
    # 添加全局平均池化层，将特征图转换为向量
    model = torch.nn.Sequential(
        model,
        torch.nn.AdaptiveAvgPool2d((1, 1)),  # 全局平均池化：7x7 -> 1x1
        torch.nn.Flatten()  # 展平：1x1x2048 -> 2048
    )
    
    model.eval()
    print("  ✅ 模型加载成功（包含全局平均池化）")
    
    # 验证输出维度
    with torch.no_grad():
        test_input = torch.randn(1, 3, 224, 224)
        test_output = model(test_input)
        print(f"  ✅ 输出维度验证: {test_output.shape} (应该是 [1, 2048])")
        
except Exception as e:
    print(f"  ❌ 模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 定义图像预处理
print()
print("[3.2] 定义图像预处理...")
preprocess = transforms.Compose([
    transforms.Resize(256),           # 调整大小到256
    transforms.CenterCrop(224),        # 中心裁剪到224x224
    transforms.ToTensor(),             # 转换为Tensor (0-1范围)
    transforms.Normalize(              # 归一化（ImageNet标准）
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])
print("  ✅ 预处理定义完成")
print("     - Resize(256)")
print("     - CenterCrop(224)")
print("     - ToTensor + Normalize")

# 3. 从数据库读取测试照片
print()
print("[3.3] 从数据库读取测试照片...")
import os

db_path = Path("photo_db/photos.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

test_photo_ids = [21, 22, 26, 27, 28, 29]
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
print("[3.4] 提取特征向量...")
features_dict = {}
extraction_times = []

for i, photo in enumerate(test_photos_data, 1):
    photo_id = photo['id']
    filename = photo['filename']
    file_path = photo['path']
    
    print(f"  [{i}/{len(test_photos_data)}] 处理: {filename} (ID {photo_id})")
    
    try:
        start_time = time.time()
        
        # 加载图像
        img = Image.open(file_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 预处理
        img_tensor = preprocess(img).unsqueeze(0)  # 添加batch维度
        
        # 提取特征
        with torch.no_grad():
            features = model(img_tensor)
            features = features.squeeze(0)  # 移除batch维度: [1, 2048] -> [2048]
            features_np = features.numpy()  # 转换为numpy数组
        
        elapsed = time.time() - start_time
        extraction_times.append(elapsed)
        
        # 保存特征向量
        features_dict[photo_id] = {
            'filename': filename,
            'features': features_np,
            'time': elapsed
        }
        
        print(f"      ✅ 提取成功 (耗时: {elapsed:.2f}秒)")
        print(f"         特征维度: {features_np.shape}")
        print(f"         特征范围: [{features_np.min():.4f}, {features_np.max():.4f}]")
        
    except Exception as e:
        print(f"      ❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()

print()

# 5. 统计信息
print("[3.5] 特征提取统计...")
if extraction_times:
    avg_time = sum(extraction_times) / len(extraction_times)
    total_time = sum(extraction_times)
    print(f"  ✅ 成功提取 {len(features_dict)} 张照片的特征向量")
    print(f"     总耗时: {total_time:.2f} 秒")
    print(f"     平均耗时: {avg_time:.2f} 秒/张")
    print(f"     最快: {min(extraction_times):.2f} 秒")
    print(f"     最慢: {max(extraction_times):.2f} 秒")
    
    # 特征向量存储大小
    feature_size_kb = len(features_dict) * 2048 * 4 / 1024  # 2048维 * 4字节(float32)
    print(f"     特征向量总大小: {feature_size_kb:.2f} KB")
    print(f"     单张特征大小: {feature_size_kb/len(features_dict):.2f} KB")

print()
print("=" * 60)
print("✅ 步骤3完成: 特征向量提取完成")
print("=" * 60)
print()
print("下一步: 计算相似度矩阵")
print("  请运行: python test_image_features_step4.py")

