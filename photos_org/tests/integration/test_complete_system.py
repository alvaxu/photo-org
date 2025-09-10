#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的系统功能验证脚本
清空数据库后重新导入照片，并测试所有核心功能
"""
import sys
import os
from pathlib import Path
import asyncio

from app.db.session import get_db
from app.models.photo import Photo, PhotoAnalysis
from app.services.import_service import ImportService
from app.services.analysis_service import AnalysisService
from app.services.photo_quality_service import PhotoQualityService
from app.services.classification_service import ClassificationService
from app.core.logging import setup_logging

# 设置日志
setup_logging()


def clear_database():
    """清空数据库"""
    print("🗑️  清空数据库...")

    db = next(get_db())

    try:
        # 删除分析结果
        photo_analysis_count = db.query(PhotoAnalysis).delete()
        print(f"  删除分析结果: {photo_analysis_count}")

        # 删除照片
        photos_count = db.query(Photo).delete()
        print(f"  删除照片: {photos_count}")

        db.commit()
        print("✅ 数据库已清空")

    except Exception as e:
        print(f"❌ 清空数据库失败: {e}")
        db.rollback()
    finally:
        db.close()


async def import_photos():
    """导入照片"""
    print("\n=== 导入照片 ===")

    import_service = ImportService()
    db = next(get_db())

    try:
        # 扫描照片
        photo_folder = "1.prepare/photo"
        photo_files = import_service.scan_folder(photo_folder, recursive=True)
        print(f"✓ 发现 {len(photo_files)} 个照片文件")

        imported_count = 0
        for photo_file_path in photo_files:
            try:
                file_name = os.path.basename(photo_file_path)
                print(f"  正在导入: {file_name}")

                # 处理照片
                success, message, photo_data = import_service.process_single_photo(photo_file_path)
                if success and photo_data:
                    # 保存到数据库
                    photo = Photo(**photo_data.dict())
                    db.add(photo)
                    db.commit()
                    db.refresh(photo)
                    imported_count += 1
                    print(f"  ✓ 成功导入: {photo.filename}")
                else:
                    print(f"  ❌ 处理失败: {file_name} - {message}")

            except Exception as e:
                print(f"  ❌ 导入异常: {file_name} - {e}")
                db.rollback()

        print(f"\n✅ 导入完成: {imported_count}/{len(photo_files)} 张照片")

        return imported_count > 0

    except Exception as e:
        print(f"❌ 导入过程异常: {e}")
        return False
    finally:
        db.close()


async def test_quality_assessment():
    """测试质量评估"""
    print("\n=== 测试质量评估功能 ===")

    db = next(get_db())

    try:
        # 获取第一张照片
        photos = db.query(Photo).limit(1).all()
        if not photos:
            print("❌ 数据库中没有照片数据")
            return False

        photo = photos[0]
        print(f"✓ 选择测试照片: {photo.filename}")

        # 初始化质量评估服务
        quality_service = PhotoQualityService()

        # 评估图像质量
        print("🔍 正在评估图像质量...")
        quality_result = quality_service.assess_quality(photo.original_path)

        if quality_result:
            print("✅ 质量评估成功!")
            print(f"  质量评分: {quality_result.get('quality_score', 'N/A')}")
            print(f"  质量等级: {quality_result.get('quality_level', 'N/A')}")
            return True
        else:
            print("❌ 质量评估失败")
            return False

    except Exception as e:
        print(f"❌ 质量评估测试失败: {e}")
        return False
    finally:
        db.close()


async def test_ai_analysis():
    """测试AI分析"""
    print("\n=== 测试AI分析功能 ===")

    db = next(get_db())

    try:
        # 获取第一张照片
        photos = db.query(Photo).limit(1).all()
        if not photos:
            print("❌ 数据库中没有照片数据")
            return False

        photo = photos[0]
        print(f"✓ 选择测试照片: {photo.filename}")

        # 初始化分析服务
        analysis_service = AnalysisService()

        # 分析照片
        print("🤖 正在进行AI分析...")
        result = await analysis_service.analyze_photo(photo.id)

        # 检查分析结果
        if result and result.get('photo_id'):
            print("✅ AI分析成功!")
            print(f"  照片ID: {result.get('photo_id')}")
            print(f"  内容分析: {'✅' if result.get('content_analysis') else '❌'}")
            print(f"  质量分析: {'✅' if result.get('quality_analysis') else '❌'}")
            print(f"  感知哈希: {'✅' if result.get('perceptual_hash') else '❌'}")
            return True
        else:
            print("❌ AI分析失败: 分析结果为空或无效")
            return False

    except Exception as e:
        print(f"❌ AI分析测试失败: {e}")
        return False
    finally:
        db.close()


async def test_classification():
    """测试分类功能"""
    print("\n=== 测试分类功能 ===")

    db = next(get_db())

    try:
        # 获取第一张照片
        photos = db.query(Photo).limit(1).all()
        if not photos:
            print("❌ 数据库中没有照片数据")
            return False

        photo = photos[0]
        print(f"✓ 选择测试照片: {photo.filename}")

        # 初始化分类服务
        classification_service = ClassificationService()

        # 分类照片
        print("📂 正在分类照片...")
        result = classification_service.classify_photo(photo.id, db)

        if result.get('success'):
            print("✅ 分类成功!")
            print(f"  分类结果: {result.get('classifications', [])}")
            print(f"  标签结果: {result.get('tags', [])}")
            return True
        else:
            print(f"❌ 分类失败: {result.get('error', '未知错误')}")
            return False

    except Exception as e:
        print(f"❌ 分类测试失败: {e}")
        return False
    finally:
        db.close()


def show_final_status():
    """显示最终状态"""
    print("\n=== 最终系统状态 ===")

    db = next(get_db())

    try:
        # 统计信息
        photo_count = db.query(Photo).count()
        analysis_count = db.query(PhotoAnalysis).count()

        print(f"📸 总照片数: {photo_count}")
        print(f"🤖 AI分析结果数: {analysis_count}")

        # 显示一些照片
        photos = db.query(Photo).limit(3).all()
        if photos:
            print("\n📸 照片示例:")
            for photo in photos:
                print(f"  - {photo.filename} (ID: {photo.id})")

    except Exception as e:
        print(f"❌ 获取状态失败: {e}")
    finally:
        db.close()


async def main():
    """主测试流程"""
    print("家庭单机版智能照片整理系统 - 完整系统验证")
    print("=" * 60)

    # 1. 清空数据库
    clear_database()

    # 2. 导入照片
    import_success = await import_photos()
    if not import_success:
        print("❌ 照片导入失败，终止测试")
        return

    # 3. 测试质量评估
    quality_success = await test_quality_assessment()

    # 4. 测试AI分析
    ai_success = await test_ai_analysis()

    # 5. 测试分类
    classification_success = await test_classification()

    # 6. 显示最终状态
    show_final_status()

    print("\n" + "=" * 60)
    print("🎯 测试结果汇总:")
    print(f"  照片导入: {'✅' if import_success else '❌'}")
    print(f"  质量评估: {'✅' if quality_success else '❌'}")
    print(f"  AI分析: {'✅' if ai_success else '❌'}")
    print(f"  分类功能: {'✅' if classification_success else '❌'}")

    successful_tests = sum([import_success, quality_success, ai_success, classification_success])
    print(f"\n🎉 总体结果: {successful_tests}/4 个测试通过")

    if successful_tests == 4:
        print("🎉 所有核心功能测试通过！系统运行正常。")
    else:
        print("⚠️  部分功能需要进一步调试。")


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())
