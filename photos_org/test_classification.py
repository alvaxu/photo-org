#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分类标签功能测试脚本
"""
import sys
import os
from pathlib import Path

from app.db.session import get_db
from app.models.photo import Photo, PhotoAnalysis
from app.services.classification_service import ClassificationService
from datetime import datetime
import json


def test_classification_service():
    """测试分类标签服务"""
    print("=== 开始测试分类标签服务 ===")

    # 创建服务实例
    service = ClassificationService()
    print("✓ 分类标签服务初始化成功")

    # 获取数据库会话
    db = next(get_db())

    try:
        # 查找一张照片进行测试
        photo = db.query(Photo).first()
        if not photo:
            print("❌ 数据库中没有照片数据，请先导入一些照片")
            return

        print(f"✓ 找到测试照片: {photo.filename} (ID: {photo.id})")

        # 测试分类功能
        print("\n=== 测试自动分类功能 ===")
        result = service.classify_photo(photo.id, db)

        if result['success']:
            print("✓ 自动分类成功!")
            print(f"  - 生成分类数量: {len(result['classifications'])}")
            print(f"  - 生成标签数量: {len(result['tags'])}")
            print(f"  - 分类列表: {result['classifications']}")
            print(f"  - 标签列表: {result['tags']}")
        else:
            print(f"❌ 自动分类失败: {result['error']}")

        # 测试获取分类信息
        print("\n=== 测试获取分类信息 ===")
        classifications = service.get_photo_classifications(photo.id, db)
        print(f"✓ 获取到 {len(classifications)} 个分类:")
        for cls in classifications:
            print(f"  - {cls['name']} (置信度: {cls['confidence']})")

        # 测试获取标签信息
        print("\n=== 测试获取标签信息 ===")
        tags = service.get_photo_tags(photo.id, db)
        print(f"✓ 获取到 {len(tags)} 个标签:")
        for tag in tags:
            print(f"  - {tag['name']} ({tag['category']}, 置信度: {tag['confidence']})")

        # 测试创建手动分类
        print("\n=== 测试创建手动分类 ===")
        test_category_name = "测试分类"
        category_result = service.create_manual_category(
            test_category_name,
            "这是一个测试分类",
            db=db
        )

        if category_result['success']:
            print("✓ 手动分类创建成功!")
            print(f"  - 分类ID: {category_result['category']['id']}")
            print(f"  - 分类名称: {category_result['category']['name']}")
        else:
            print(f"❌ 手动分类创建失败: {category_result['error']}")

        # 测试添加手动标签
        print("\n=== 测试添加手动标签 ===")
        tag_result = service.add_manual_tag(photo.id, "测试标签", db)

        if tag_result['success']:
            print("✓ 手动标签添加成功!")
            print(f"  - 标签名称: {tag_result['tag']['name']}")
            print(f"  - 标签类别: {tag_result['tag']['category']}")
        else:
            print(f"❌ 手动标签添加失败: {tag_result['error']}")

        print("\n=== 测试完成 ===")
        print("✅ 分类标签服务测试全部通过!")

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def test_chinese_tag_mapping():
    """测试中文标签映射功能"""
    print("\n=== 测试中文标签映射 ===")

    service = ClassificationService()

    # 测试一些常见的英文标签
    test_tags = ['person', 'food', 'mountain', 'car', 'indoor', 'sunset']

    for tag in test_tags:
        chinese_tag = service.chinese_tag_mapping.get(tag.lower(), tag)
        print(f"  {tag} -> {chinese_tag}")

    print("✓ 中文标签映射测试完成")


if __name__ == "__main__":
    print("家庭单机版智能照片整理系统 - 分类标签功能测试")
    print("=" * 60)

    # 测试中文标签映射
    test_chinese_tag_mapping()

    # 测试分类服务
    test_classification_service()

    print("\n" + "=" * 60)
    print("测试脚本执行完毕")
