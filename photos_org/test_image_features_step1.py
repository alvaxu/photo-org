"""
图像特征向量相似度搜索测试 - 第一步
基础设置和模型加载
"""
import sys
from pathlib import Path

print("=" * 60)
print("步骤1: 基础设置和模型加载")
print("=" * 60)
print()

# 1. 检查依赖
print("[1.1] 检查依赖包...")
try:
    import torch
    import torchvision
    from torchvision import models
    from PIL import Image
    import numpy as np
    print(f"  ✅ torch: {torch.__version__}")
    print(f"  ✅ torchvision: {torchvision.__version__}")
    print(f"  ✅ PIL (Pillow): 已安装")
    print(f"  ✅ numpy: {np.__version__}")
except ImportError as e:
    print(f"  ❌ 缺少依赖包: {e}")
    print("  请先安装: pip install torch torchvision")
    sys.exit(1)

# 2. 检查本地模型文件
print()
print("[1.2] 检查本地模型文件...")
model_dir = Path("models/resnet50")
model_path = model_dir / "resnet50-0676ba61.pth"

if not model_dir.exists():
    print(f"  ❌ 模型目录不存在: {model_dir}")
    print(f"  请创建目录并下载模型文件")
    sys.exit(1)

if not model_path.exists():
    print(f"  ❌ 模型文件不存在: {model_path}")
    print(f"  请下载模型文件到: {model_path}")
    print(f"  下载链接: https://download.pytorch.org/models/resnet50-0676ba61.pth")
    sys.exit(1)

file_size_mb = model_path.stat().st_size / 1024 / 1024
print(f"  ✅ 找到模型文件: {model_path}")
print(f"     文件大小: {file_size_mb:.2f} MB")

# 3. 加载模型
print()
print("[1.3] 加载ResNet50模型...")
try:
    # 先加载完整的ResNet50模型（包含分类层）
    model = models.resnet50(weights=None)
    print("  ✅ 模型结构创建成功")
    
    # 从本地文件加载预训练权重
    state_dict = torch.load(model_path, map_location='cpu')
    model.load_state_dict(state_dict)
    print("  ✅ 成功从本地文件加载模型权重")
    
    # 移除分类层（fc层），只保留特征提取部分
    # 方法：创建一个新的Sequential模型，包含除最后两层（avgpool和fc）之外的所有层
    model = torch.nn.Sequential(*list(model.children())[:-2])  # 移除avgpool和fc
    print("  ✅ 已移除分类层，保留特征提取部分")
    
    # 设置为评估模式
    model.eval()
    print("  ✅ 模型设置为评估模式")
    
    # 检查模型结构
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  ✅ 模型参数总数: {total_params:,}")
    
    # 测试模型输出维度（应该是2048维）
    with torch.no_grad():
        test_input = torch.randn(1, 3, 224, 224)
        test_output = model(test_input)
        output_shape = test_output.shape
        print(f"  ✅ 测试输出维度: {output_shape}")
        print(f"     特征向量维度: {output_shape[1]} (应该是2048)")
    
except Exception as e:
    print(f"  ❌ 模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✅ 步骤1完成: 模型加载成功")
print("=" * 60)
print()
print("下一步: 从数据库读取测试照片")
print("  请运行: python test_image_features_step2.py")

