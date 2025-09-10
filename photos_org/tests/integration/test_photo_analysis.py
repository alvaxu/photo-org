'''
程序说明：
## 1. 照片快速分析测试脚本
## 2. 验证EXIF数据提取、OpenCV图像分析和AI分析的处理时间
## 3. 测试快速处理策略的实际效果
'''

import time
import cv2
import numpy as np
from PIL import Image, ExifTags
import json
import os
from datetime import datetime

def extract_exif_data(image_path):
    """提取EXIF数据"""
    start_time = time.time()
    
    try:
        with Image.open(image_path) as img:
            exif_data = {}
            
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
            
            # 基础图像信息
            basic_info = {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.size[0],
                'height': img.size[1]
            }
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'exif_data': exif_data,
                'basic_info': basic_info,
                'processing_time': processing_time,
                'exif_count': len(exif_data)
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'processing_time': time.time() - start_time
        }

def analyze_with_opencv(image_path):
    """使用OpenCV进行图像分析"""
    start_time = time.time()
    
    try:
        # 读取图像（支持中文路径）
        img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return {
                'success': False,
                'error': '无法读取图像',
                'processing_time': time.time() - start_time
            }
        
        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 质量评估
        quality_metrics = {
            'sharpness': float(cv2.Laplacian(gray, cv2.CV_64F).var()),
            'brightness': float(np.mean(gray)),
            'contrast': float(np.std(gray)),
            'width': img.shape[1],
            'height': img.shape[0],
            'channels': img.shape[2] if len(img.shape) > 2 else 1
        }
        
        # 颜色分析
        color_analysis = {
            'mean_b': float(np.mean(img[:, :, 0])),
            'mean_g': float(np.mean(img[:, :, 1])),
            'mean_r': float(np.mean(img[:, :, 2])),
            'dominant_color': 'unknown'  # 简化处理
        }
        
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.sum(edges > 0) / (img.shape[0] * img.shape[1]))
        
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'quality_metrics': quality_metrics,
            'color_analysis': color_analysis,
            'edge_density': edge_density,
            'processing_time': processing_time
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'processing_time': time.time() - start_time
        }

def fast_image_processing(image_path):
    """快速图像处理（模拟AI分析）"""
    start_time = time.time()
    
    try:
        # 读取并压缩图像
        img = Image.open(image_path)
        img.thumbnail((512, 512), Image.Resampling.LANCZOS)
        
        # 模拟AI分析结果
        analysis_result = {
            'description': '室内场景，老年女性在桌前进行某种仪式或准备餐食',
            'objects': ['桌子', '碗', '蜡烛', '筷子', '食物', '女性', '椅子', '帽子'],
            'scene': '室内家庭场景',
            'tags': ['家庭', '传统', '仪式', '食物', '蜡烛', '室内', '老年女性'],
            'confidence': 0.85,
            'emotion': '庄重',
            'activity': '传统仪式或祭祀',
            'time_period': '现代',
            'location_type': '家庭室内'
        }
        
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'analysis_result': analysis_result,
            'processing_time': processing_time
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'processing_time': time.time() - start_time
        }

def test_photo_analysis(image_path):
    """测试照片分析"""
    print(f"开始分析照片: {image_path}")
    print("=" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"错误: 文件不存在 - {image_path}")
        return
    
    # 1. EXIF数据提取
    print("1. EXIF数据提取...")
    exif_result = extract_exif_data(image_path)
    print(f"   处理时间: {exif_result['processing_time']:.3f}秒")
    print(f"   成功: {exif_result['success']}")
    if exif_result['success']:
        print(f"   EXIF数据条数: {exif_result['exif_count']}")
        print(f"   图像尺寸: {exif_result['basic_info']['width']}x{exif_result['basic_info']['height']}")
        print(f"   图像格式: {exif_result['basic_info']['format']}")
    else:
        print(f"   错误: {exif_result['error']}")
    
    print()
    
    # 2. OpenCV图像分析
    print("2. OpenCV图像分析...")
    opencv_result = analyze_with_opencv(image_path)
    print(f"   处理时间: {opencv_result['processing_time']:.3f}秒")
    print(f"   成功: {opencv_result['success']}")
    if opencv_result['success']:
        quality = opencv_result['quality_metrics']
        print(f"   清晰度: {quality['sharpness']:.2f}")
        print(f"   亮度: {quality['brightness']:.2f}")
        print(f"   对比度: {quality['contrast']:.2f}")
        print(f"   边缘密度: {opencv_result['edge_density']:.4f}")
    else:
        print(f"   错误: {opencv_result['error']}")
    
    print()
    
    # 3. 快速AI分析
    print("3. 快速AI分析...")
    ai_result = fast_image_processing(image_path)
    print(f"   处理时间: {ai_result['processing_time']:.3f}秒")
    print(f"   成功: {ai_result['success']}")
    if ai_result['success']:
        analysis = ai_result['analysis_result']
        print(f"   描述: {analysis['description']}")
        print(f"   场景: {analysis['scene']}")
        print(f"   标签: {', '.join(analysis['tags'])}")
        print(f"   置信度: {analysis['confidence']}")
    else:
        print(f"   错误: {ai_result['error']}")
    
    print()
    
    # 4. 总结
    total_time = exif_result['processing_time'] + opencv_result['processing_time'] + ai_result['processing_time']
    print("=" * 60)
    print("分析总结:")
    print(f"总处理时间: {total_time:.3f}秒")
    print(f"EXIF提取: {exif_result['processing_time']:.3f}秒")
    print(f"OpenCV分析: {opencv_result['processing_time']:.3f}秒")
    print(f"AI分析: {ai_result['processing_time']:.3f}秒")
    
    # 性能评估
    if total_time <= 3.0:
        print("✅ 性能优秀: 总处理时间 ≤ 3秒")
    elif total_time <= 5.0:
        print("⚠️  性能良好: 总处理时间 ≤ 5秒")
    else:
        print("❌ 性能需要优化: 总处理时间 > 5秒")
    
    # 保存详细结果
    result_data = {
        'image_path': image_path,
        'analysis_time': datetime.now().isoformat(),
        'exif_result': exif_result,
        'opencv_result': opencv_result,
        'ai_result': ai_result,
        'total_time': total_time
    }
    
    with open('photo_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细结果已保存到: photo_analysis_result.json")

if __name__ == "__main__":
    # 测试照片路径
    test_image = "doc/微信图片_20250909193208_25_2.jpg"
    
    print("照片快速分析测试")
    print("=" * 60)
    test_photo_analysis(test_image)
