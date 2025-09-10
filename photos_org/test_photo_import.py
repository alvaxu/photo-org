#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照片导入和分析测试脚本
使用准备的照片数据测试完整功能流程
"""
import sys
import os
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.db.session import get_db
from app.models.photo import Photo, PhotoAnalysis
from app.services.import_service import ImportService
from app.services.analysis_service import AnalysisService
from app.services.classification_service import ClassificationService
from app.core.logging import setup_logging

# 设置日志
setup_logging()


async def import_photos_from_folder(folder_path: str):
    """从文件夹导入照片"""
    print("=== 开始导入照片 ===")

    import_service = ImportService()
    db = next(get_db())

    try:
        # 扫描文件夹
        photo_files = import_service.scan_folder(folder_path, recursive=True)
        print(f"✓ 发现 {len(photo_files)} 个照片文件")

        imported_count = 0
        for photo_file_path in photo_files:
            try:
                file_name = os.path.basename(photo_file_path)
                print(f"正在导入: {file_name}")

                # 处理照片
                success, message, photo_data = import_service.process_single_photo(photo_file_path)
                if success and photo_data:
                    try:
                        # 保存到数据库
                        from app.models.photo import Photo
                        photo = Photo(**photo_data.dict())
                        db.add(photo)
                        db.commit()
                        db.refresh(photo)
                        imported_count += 1
                        print(f"✓ 导入成功: {photo.filename}")
                    except Exception as save_error:
                        print(f"❌ 保存失败: {file_name} - {save_error}")
                        db.rollback()
                else:
                    print(f"❌ 处理失败: {file_name} - {message}")

            except Exception as e:
                print(f"❌ 导入异常: {file_name} - {e}")

        print(f"\n=== 导入完成 ===")
        print(f"成功导入: {imported_count}/{len(photo_files)} 张照片")

        return imported_count > 0

    except Exception as e:
        print(f"❌ 导入过程异常: {e}")
        return False
    finally:
        db.close()


async def analyze_all_photos():
    """分析所有照片"""
    print("\n=== 开始分析照片 ===")

    analysis_service = AnalysisService()
    db = next(get_db())

    try:
        # 获取所有照片
        photos = db.query(Photo).all()
        print(f"✓ 找到 {len(photos)} 张照片待分析")

        analyzed_count = 0
        for photo in photos:
            try:
                print(f"正在分析: {photo.filename}")

                # 分析照片
                result = analysis_service.analyze_photo(photo.id)
                if result['success']:
                    analyzed_count += 1
                    print(f"✓ 分析成功: {photo.filename}")
                    print(f"  - 分析结果: {result.get('analysis_types', [])}")
                else:
                    print(f"❌ 分析失败: {photo.filename} - {result['error']}")

            except Exception as e:
                print(f"❌ 分析异常: {photo.filename} - {e}")

        print(f"\n=== 分析完成 ===")
        print(f"成功分析: {analyzed_count}/{len(photos)} 张照片")

        return analyzed_count > 0

    except Exception as e:
        print(f"❌ 分析过程异常: {e}")
        return False
    finally:
        db.close()


async def classify_all_photos():
    """对所有照片进行分类"""
    print("\n=== 开始分类照片 ===")

    classification_service = ClassificationService()
    db = next(get_db())

    try:
        # 获取所有照片
        photos = db.query(Photo).all()
        print(f"✓ 找到 {len(photos)} 张照片待分类")

        classified_count = 0
        for photo in photos:
            try:
                print(f"正在分类: {photo.filename}")

                # 分类照片
                result = classification_service.classify_photo(photo.id, db)
                if result['success']:
                    classified_count += 1
                    print("✓ 分类成功:")
                    print(f"  - 分类: {result['classifications']}")
                    print(f"  - 标签: {result['tags']}")
                else:
                    print(f"❌ 分类失败: {photo.filename} - {result['error']}")

            except Exception as e:
                print(f"❌ 分类异常: {photo.filename} - {e}")

        print(f"\n=== 分类完成 ===")
        print(f"成功分类: {classified_count}/{len(photos)} 张照片")

        return classified_count > 0

    except Exception as e:
        print(f"❌ 分类过程异常: {e}")
        return False
    finally:
        db.close()


async def show_statistics():
    """显示统计信息"""
    print("\n=== 系统统计信息 ===")

    db = next(get_db())

    try:
        # 照片统计
        total_photos = db.query(Photo).count()
        print(f"📸 总照片数: {total_photos}")

        # 分类统计
        from app.models.photo import Category, PhotoCategory
        total_categories = db.query(Category).count()
        print(f"📂 总分类数: {total_categories}")

        # 标签统计
        from app.models.photo import Tag
        total_tags = db.query(Tag).count()
        print(f"🏷️  总标签数: {total_tags}")

        # 显示前5个分类
        categories = db.query(Category).limit(5).all()
        if categories:
            print("\n📂 分类示例:")
            for category in categories:
                photo_count = db.query(PhotoCategory).filter(
                    PhotoCategory.category_id == category.id
                ).count()
                print(f"  - {category.name}: {photo_count}张照片")

        # 显示前5个标签
        tags = db.query(Tag).order_by(Tag.usage_count.desc()).limit(5).all()
        if tags:
            print("\n🏷️  标签示例:")
            for tag in tags:
                print(f"  - {tag.name} ({tag.category}): 使用{tag.usage_count}次")

        # 显示一些照片详情
        photos = db.query(Photo).limit(3).all()
        if photos:
            print("\n📸 照片示例:")
            for photo in photos:
                print(f"  - {photo.filename}")
                print(f"    📏 尺寸: {photo.width}x{photo.height}")
                print(f"    📅 时间: {photo.taken_at}")
                print(f"    📷 设备: {photo.camera_model or '未知'}")

                # 显示该照片的分类
                photo_categories = db.query(PhotoCategory).filter(
                    PhotoCategory.photo_id == photo.id
                ).join(Category).all()

                if photo_categories:
                    category_names = [pc.category.name for pc in photo_categories]
                    print(f"    📂 分类: {', '.join(category_names)}")

    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
    finally:
        db.close()


async def main():
    """主测试流程"""
    print("家庭单机版智能照片整理系统 - 完整功能测试")
    print("=" * 60)

    # 照片文件夹路径
    photo_folder = "1.prepare/photo"

    if not os.path.exists(photo_folder):
        print(f"❌ 照片文件夹不存在: {photo_folder}")
        return

    print(f"📁 照片文件夹: {photo_folder}")

    # 1. 导入照片
    import_success = await import_photos_from_folder(photo_folder)
    if not import_success:
        print("❌ 照片导入失败，终止测试")
        return

    # 2. 分析照片
    analysis_success = await analyze_all_photos()
    if not analysis_success:
        print("⚠️  照片分析部分失败，继续其他测试")

    # 3. 分类照片
    classification_success = await classify_all_photos()
    if not classification_success:
        print("⚠️  照片分类部分失败，继续统计")

    # 4. 显示统计信息
    await show_statistics()

    print("\n" + "=" * 60)
    print("🎉 完整功能测试完成！")
    print("您现在可以使用系统来管理这些照片了。")


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())
