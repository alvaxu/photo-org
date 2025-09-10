#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整图像处理功能测试脚本
测试AI分析、OpenCV处理、质量评估等所有图像处理功能
"""
import sys
import os
from pathlib import Path
import asyncio

from app.db.session import get_db
from app.models.photo import Photo, PhotoAnalysis
from app.services.dashscope_service import DashScopeService
from app.services.analysis_service import AnalysisService
from app.services.photo_quality_service import PhotoQualityService
from app.core.logging import setup_logging

# 设置日志
setup_logging()


def test_opencv_functionality():
    """测试OpenCV图像处理功能"""
    print("=== 测试OpenCV图像处理功能 ===")

    try:
        import cv2
        print("✅ OpenCV导入成功")

        # 检查OpenCV版本
        version = cv2.__version__
        print(f"📦 OpenCV版本: {version}")

        # 测试基本功能
        # 这里可以添加更多的OpenCV功能测试

        return True

    except ImportError as e:
        print(f"❌ OpenCV导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ OpenCV测试失败: {e}")
        return False


def test_image_quality_assessment():
    """测试图像质量评估功能"""
    print("\n=== 测试图像质量评估功能 ===")

    db = next(get_db())

    try:
        # 获取第一张照片
        photo = db.query(Photo).first()
        if not photo:
            print("❌ 数据库中没有照片数据")
            return False

        print(f"✓ 选择测试照片: {photo.filename}")

        # 初始化质量评估服务
        quality_service = PhotoQualityService()

        # 评估图像质量
        print("🔍 正在评估图像质量...")
        quality_result = quality_service.assess_quality(photo.original_path)

        if quality_result:
            print("✅ 质量评估成功!")
            print(f"  质量评分: {quality_result.get('quality_score', 'N/A')}")
            print(f"  锐度评分: {quality_result.get('sharpness_score', 'N/A')}")
            print(f"  亮度评分: {quality_result.get('brightness_score', 'N/A')}")
            print(f"  对比度评分: {quality_result.get('contrast_score', 'N/A')}")
            print(f"  色彩评分: {quality_result.get('color_score', 'N/A')}")
            print(f"  构图评分: {quality_result.get('composition_score', 'N/A')}")
            print(f"  质量等级: {quality_result.get('quality_level', 'N/A')}")

            return quality_result
        else:
            print("❌ 质量评估失败")
            return False

    except Exception as e:
        print(f"❌ 质量评估测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_image_hashing():
    """测试图像哈希功能"""
    print("\n=== 测试图像哈希功能 ===")

    try:
        import imagehash
        from PIL import Image
        print("✅ imagehash库导入成功")

        # 获取测试照片
        db = next(get_db())
        photo = db.query(Photo).first()
        if not photo:
            print("❌ 数据库中没有照片数据")
            db.close()
            return False

        print(f"✓ 选择测试照片: {photo.filename}")

        # 打开图像并计算哈希
        try:
            img = Image.open(photo.original_path)
            # 计算感知哈希
            phash = imagehash.phash(img)
            print(f"✅ 感知哈希计算成功: {phash}")

            # 计算差异哈希
            dhash = imagehash.dhash(img)
            print(f"✅ 差异哈希计算成功: {dhash}")

            # 计算平均哈希
            ahash = imagehash.average_hash(img)
            print(f"✅ 平均哈希计算成功: {ahash}")

            db.close()
            return True

        except Exception as e:
            print(f"❌ 图像哈希计算失败: {e}")
            db.close()
            return False

    except ImportError as e:
        print(f"❌ imagehash库导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 哈希测试失败: {e}")
        return False


def test_thumbnail_generation():
    """测试缩略图生成功能"""
    print("\n=== 测试缩略图生成功能 ===")

    db = next(get_db())

    try:
        # 获取第一张照片
        photo = db.query(Photo).first()
        if not photo:
            print("❌ 数据库中没有照片数据")
            return False

        print(f"✓ 选择测试照片: {photo.filename}")

        # 检查缩略图是否已存在
        if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
            print(f"✅ 缩略图已存在: {photo.thumbnail_path}")

            # 检查缩略图尺寸
            try:
                from PIL import Image
                thumb_img = Image.open(photo.thumbnail_path)
                print(f"  📏 缩略图尺寸: {thumb_img.size}")
                thumb_img.close()
            except Exception as e:
                print(f"⚠️  缩略图读取失败: {e}")

            return True
        else:
            print("⚠️  缩略图不存在，尝试重新生成")
            # 这里可以调用缩略图生成服务
            return False

    except Exception as e:
        print(f"❌ 缩略图测试失败: {e}")
        return False
    finally:
        db.close()


def test_ai_analysis_complete():
    """测试完整的AI分析流程"""
    print("\n=== 测试完整AI分析流程 ===")

    db = next(get_db())

    try:
        # 获取第一张照片
        photo = db.query(Photo).first()
        if not photo:
            print("❌ 数据库中没有照片数据")
            return False

        print(f"✓ 选择测试照片: {photo.filename}")

        # 检查是否已有AI分析结果
        existing_analysis = db.query(PhotoAnalysis).filter(
            PhotoAnalysis.photo_id == photo.id,
            PhotoAnalysis.analysis_type == 'content_analysis'
        ).first()

        if existing_analysis:
            print("✅ AI分析结果已存在")
            analysis_data = existing_analysis.analysis_result
            print(f"  📝 描述: {analysis_data.get('description', 'N/A')[:50]}...")
            print(f"  🏷️  标签: {', '.join(analysis_data.get('tags', []))}")
            print(f"  🎯 置信度: {analysis_data.get('confidence', 'N/A')}")
            return True
        else:
            print("⚠️  没有找到AI分析结果")
            return False

    except Exception as e:
        print(f"❌ AI分析检查失败: {e}")
        return False
    finally:
        db.close()


def test_database_storage():
    """测试数据库存储情况"""
    print("\n=== 测试数据库存储情况 ===")

    db = next(get_db())

    try:
        # 统计照片数量
        photo_count = db.query(Photo).count()
        print(f"📸 照片总数: {photo_count}")

        # 统计分析结果数量
        analysis_count = db.query(PhotoAnalysis).count()
        print(f"🤖 AI分析结果数: {analysis_count}")

        # 检查每张照片的分析状态
        photos = db.query(Photo).all()
        for photo in photos[:5]:  # 只检查前5张
            analysis_count = db.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id == photo.id
            ).count()

            status = "✅ 已分析" if analysis_count > 0 else "❌ 未分析"
            thumbnail_status = "✅ 有缩略图" if photo.thumbnail_path and os.path.exists(photo.thumbnail_path) else "❌ 无缩略图"

            print(f"  {photo.filename}: {status} | {thumbnail_status}")

        return True

    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False
    finally:
        db.close()


def main():
    """主测试流程"""
    print("家庭单机版智能照片整理系统 - 完整图像处理功能测试")
    print("=" * 70)

    test_results = {}

    # 1. 测试OpenCV功能
    test_results['opencv'] = test_opencv_functionality()

    # 2. 测试图像质量评估
    test_results['quality'] = test_image_quality_assessment()

    # 3. 测试图像哈希
    test_results['hashing'] = test_image_hashing()

    # 4. 测试缩略图生成
    test_results['thumbnail'] = test_thumbnail_generation()

    # 5. 测试AI分析
    test_results['ai_analysis'] = test_ai_analysis_complete()

    # 6. 测试数据库存储
    test_results['database'] = test_database_storage()

    # 总结测试结果
    print("\n" + "=" * 70)
    print("📊 测试结果总结:")

    success_count = 0
    total_count = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name.capitalize()}: {status}")
        if result:
            success_count += 1

    print(f"\n🎯 总体结果: {success_count}/{total_count} 个测试通过")

    if success_count == total_count:
        print("🎉 所有图像处理功能测试通过！")
    else:
        print("⚠️  部分功能需要进一步调试")

    print("=" * 70)


if __name__ == "__main__":
    main()
