"""
ICO 转 PNG 图标转换脚本

将 ICO 图标文件转换为 MSIX 打包所需的 PNG 格式图标。

功能：
- 自动读取 ICO 文件
- 生成所需尺寸的 PNG 图标
- 保持透明背景
- 自动保存到 Assets 目录

使用方法：
    python convert_ico_to_png.py

或指定 ICO 文件路径：
    python convert_ico_to_png.py --ico path/to/icon.ico

作者：AI助手
创建日期：2025年1月
"""

import os
import sys
from pathlib import Path
import argparse

try:
    from PIL import Image
except ImportError:
    print("❌ 错误: 未安装 Pillow")
    print("   请运行: pip install Pillow")
    sys.exit(1)


def convert_ico_to_png(ico_path: Path, output_dir: Path = None):
    """
    将 ICO 文件转换为多个尺寸的 PNG 文件
    
    :param ico_path: ICO 文件路径
    :param output_dir: 输出目录（默认：release/Assets）
    """
    # 设置输出目录
    if output_dir is None:
        script_dir = Path(__file__).parent
        output_dir = script_dir / "Assets"
    else:
        output_dir = Path(output_dir)
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查 ICO 文件是否存在
    if not ico_path.exists():
        raise FileNotFoundError(f"ICO 文件不存在: {ico_path}")
    
    print(f"📁 读取 ICO 文件: {ico_path}")
    
    # 打开 ICO 文件
    try:
        ico_image = Image.open(ico_path)
    except Exception as e:
        raise ValueError(f"无法读取 ICO 文件: {e}")
    
    # 获取 ICO 中最大的图标（通常质量最好）
    # ICO 文件可能包含多个尺寸，我们选择最大的
    ico_image = ico_image.copy()
    
    print(f"✅ ICO 文件读取成功")
    print(f"   原始尺寸: {ico_image.size}")
    print(f"   模式: {ico_image.mode}")
    
    # 定义需要生成的图标尺寸
    icon_sizes = {
        "Logo.png": (150, 150),
        "Square150x150Logo.png": (150, 150),
        "Square44x44Logo.png": (44, 44),
        "Wide310x150Logo.png": (310, 150),
        "SplashScreen.png": (620, 300),
    }
    
    print(f"\n🔄 开始转换图标...")
    print(f"   输出目录: {output_dir}")
    print()
    
    # 转换并保存每个尺寸
    for filename, (width, height) in icon_sizes.items():
        try:
            # 调整尺寸（使用高质量重采样）
            resized = ico_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # 确保是 RGBA 模式（支持透明背景）
            if resized.mode != 'RGBA':
                # 如果不是 RGBA，转换为 RGBA
                if resized.mode == 'RGB':
                    # RGB 转 RGBA（添加不透明 alpha 通道）
                    resized = resized.convert('RGBA')
                else:
                    # 其他模式先转 RGB 再转 RGBA
                    resized = resized.convert('RGB').convert('RGBA')
            
            # 保存为 PNG
            output_path = output_dir / filename
            resized.save(output_path, 'PNG', optimize=True)
            
            print(f"   ✅ {filename} ({width}x{height}) - 已保存")
            
        except Exception as e:
            print(f"   ❌ {filename} - 转换失败: {e}")
    
    print(f"\n✅ 所有图标转换完成！")
    print(f"\n📁 输出目录: {output_dir}")
    print(f"\n生成的文件：")
    for filename in icon_sizes.keys():
        file_path = output_dir / filename
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"   - {filename} ({size_kb:.1f} KB)")
        else:
            print(f"   - {filename} (未生成)")
    
    return output_dir


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="将 ICO 图标转换为 MSIX 所需的 PNG 格式"
    )
    parser.add_argument(
        "--ico",
        type=str,
        default=None,
        help="ICO 文件路径（默认：release/xuwh.ico）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出目录（默认：release/Assets）"
    )
    
    args = parser.parse_args()
    
    # 确定 ICO 文件路径
    script_dir = Path(__file__).parent
    if args.ico:
        ico_path = Path(args.ico)
    else:
        # 默认查找 release/xuwh.ico
        ico_path = script_dir / "xuwh.ico"
    
    # 确定输出目录
    output_dir = Path(args.output) if args.output else None
    
    print("=" * 60)
    print("🎨 ICO 转 PNG 图标转换工具")
    print("=" * 60)
    print()
    
    try:
        convert_ico_to_png(ico_path, output_dir)
        print()
        print("=" * 60)
        print("✅ 转换完成！")
        print("=" * 60)
        print()
        print("下一步：")
        print("  1. 检查 Assets 目录中的 PNG 文件")
        print("  2. 运行 build_msix.bat 进行 MSIX 打包")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 转换失败: {e}")
        print("=" * 60)
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()

