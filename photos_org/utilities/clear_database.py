#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库清空脚本
清空所有照片和分析数据，用于重新测试
"""
import sys
from pathlib import Path

from app.db.session import get_db
from app.models.photo import Photo, PhotoAnalysis, PhotoQuality, Category, Tag, PhotoCategory, PhotoTag, DuplicateGroup, DuplicateGroupPhoto
from app.core.logging import setup_logging

# 设置日志
setup_logging()


def clear_database():
    """清空数据库中的所有数据"""
    print("=== 清空数据库 ===")
    print("⚠️  警告：此操作将删除所有照片和分析数据！")

    # 确认操作
    confirm = input("是否确认清空数据库？(输入 'yes' 确认): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return False

    db = next(get_db())

    try:
        # 删除顺序：先删除关联表，再删除主表
        print("🗑️  正在删除数据...")

        # 删除重复组照片关联
        duplicate_group_photos_count = db.query(DuplicateGroupPhoto).delete()
        print(f"  删除重复组照片关联: {duplicate_group_photos_count} 条")

        # 删除重复组
        duplicate_groups_count = db.query(DuplicateGroup).delete()
        print(f"  删除重复组: {duplicate_groups_count} 条")

        # 删除照片标签关联
        photo_tags_count = db.query(PhotoTag).delete()
        print(f"  删除照片标签关联: {photo_tags_count} 条")

        # 删除照片分类关联
        photo_categories_count = db.query(PhotoCategory).delete()
        print(f"  删除照片分类关联: {photo_categories_count} 条")

        # 删除照片质量评估
        photo_quality_count = db.query(PhotoQuality).delete()
        print(f"  删除照片质量评估: {photo_quality_count} 条")

        # 删除照片分析结果
        photo_analysis_count = db.query(PhotoAnalysis).delete()
        print(f"  删除照片分析结果: {photo_analysis_count} 条")

        # 删除标签
        tags_count = db.query(Tag).delete()
        print(f"  删除标签: {tags_count} 条")

        # 删除分类
        categories_count = db.query(Category).delete()
        print(f"  删除分类: {categories_count} 条")

        # 删除照片
        photos_count = db.query(Photo).delete()
        print(f"  删除照片: {photos_count} 条")

        # 提交事务
        db.commit()

        print("✅ 数据库清空完成!")
        print("📊 删除统计:")
        print(f"  📸 照片: {photos_count}")
        print(f"  🤖 分析结果: {photo_analysis_count}")
        print(f"  🏷️  标签: {tags_count}")
        print(f"  📂 分类: {categories_count}")

        return True

    except Exception as e:
        print(f"❌ 清空数据库失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def show_current_status():
    """显示当前数据库状态"""
    print("\n=== 当前数据库状态 ===")

    db = next(get_db())

    try:
        photo_count = db.query(Photo).count()
        analysis_count = db.query(PhotoAnalysis).count()
        category_count = db.query(Category).count()
        tag_count = db.query(Tag).count()

        print(f"📸 照片数量: {photo_count}")
        print(f"🤖 分析结果: {analysis_count}")
        print(f"📂 分类数量: {category_count}")
        print(f"🏷️  标签数量: {tag_count}")

    except Exception as e:
        print(f"❌ 获取状态失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("家庭版智能照片系统 - 数据库清空工具")
    print("=" * 50)

    # 显示当前状态
    show_current_status()

    # 执行清空操作
    if clear_database():
        print("\n" + "=" * 50)
        print("✅ 数据库已清空，可以重新开始测试")
        print("💡 提示: 运行测试脚本时会重新导入照片")
    else:
        print("\n" + "=" * 50)
        print("❌ 数据库清空失败或已取消")

    print("=" * 50)
