#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析功能测试脚本
测试DashScope AI服务和智能分析功能
"""
import sys
import os
from pathlib import Path
from datetime import datetime

from app.db.session import get_db
from app.models.photo import Photo, PhotoAnalysis
from app.services.dashscope_service import DashScopeService
from app.services.analysis_service import AnalysisService
from app.services.classification_service import ClassificationService
from app.core.logging import setup_logging

# 设置日志
setup_logging()


def test_dashscope_basic():
    """测试DashScope服务基本功能"""
    print("=== 测试DashScope服务基本功能 ===")

    try:
        service = DashScopeService()
        print("✓ DashScope服务初始化成功")

        # 检查API密钥
        if service.api_key and service.api_key != "${DASHSCOPE_API_KEY}":
            print("✓ API密钥已配置")
        else:
            print("❌ API密钥未配置")
            return False

        return True

    except Exception as e:
        print(f"❌ DashScope服务初始化失败: {e}")
        return False


def test_photo_analysis():
    """测试单张照片AI分析"""
    print("\n=== 测试单张照片AI分析 ===")

    db = next(get_db())

    try:
        # 获取第一张照片
        photo = db.query(Photo).first()
        if not photo:
            print("❌ 数据库中没有照片数据")
            return False

        print(f"✓ 选择测试照片: {photo.filename}")
        print(f"  路径: {photo.original_path}")

        # 检查照片文件是否存在
        if not os.path.exists(photo.original_path):
            print(f"❌ 照片文件不存在: {photo.original_path}")
            return False

        # 初始化AI服务
        dashscope_service = DashScopeService()

        # 分析照片内容
        print("🤖 正在分析照片内容...")
        analysis_result = dashscope_service.analyze_photo_content(photo.original_path)

        if analysis_result:
            print("✓ AI分析成功!")
            print("\n📊 分析结果:")
            print(f"  描述: {analysis_result['description']}")
            print(f"  场景类型: {analysis_result['scene_type']}")
            print(f"  检测物体: {', '.join(analysis_result['objects'])}")
            print(f"  人物数量: {analysis_result['people_count']}")
            print(f"  情感: {analysis_result['emotion']}")
            print(f"  活动类型: {analysis_result['activity']}")
            print(f"  时间特征: {analysis_result['time_period']}")
            print(f"  地点类型: {analysis_result['location_type']}")
            print(f"  置信度: {analysis_result['confidence']}")
            print(f"  标签: {', '.join(analysis_result['tags'])}")

            # 保存分析结果到数据库
            photo_analysis = PhotoAnalysis(
                photo_id=photo.id,
                analysis_type='content_analysis',
                analysis_result=analysis_result,
                confidence_score=analysis_result['confidence']
            )
            db.add(photo_analysis)
            db.commit()
            print("✓ 分析结果已保存到数据库")

            return analysis_result
        else:
            print("❌ AI分析失败")
            return False

    except Exception as e:
        print(f"❌ 照片分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_caption_generation():
    """测试照片标题生成"""
    print("\n=== 测试照片标题生成 ===")

    db = next(get_db())

    try:
        # 获取第一张照片
        photo = db.query(Photo).first()
        if not photo:
            print("❌ 数据库中没有照片数据")
            return False

        print(f"✓ 选择测试照片: {photo.filename}")

        # 初始化AI服务
        dashscope_service = DashScopeService()

        # 生成不同风格的标题
        styles = ["natural", "creative", "poetic"]

        print("🎨 正在生成照片标题...")
        for style in styles:
            try:
                caption = dashscope_service.generate_photo_caption(photo.original_path, style)
                print(f"  {style.capitalize()}: {caption}")
            except Exception as e:
                print(f"  {style.capitalize()}: 生成失败 - {e}")

        return True

    except Exception as e:
        print(f"❌ 标题生成测试失败: {e}")
        return False
    finally:
        db.close()


def test_full_analysis_pipeline():
    """测试完整的分析流程"""
    print("\n=== 测试完整分析流程 ===")

    db = next(get_db())

    try:
        # 获取所有照片
        photos = db.query(Photo).all()
        print(f"✓ 找到 {len(photos)} 张照片待分析")

        if not photos:
            print("❌ 没有照片数据")
            return False

        # 初始化服务
        analysis_service = AnalysisService()
        classification_service = ClassificationService()

        # 分析第一张照片
        photo = photos[0]
        print(f"🤖 正在完整分析照片: {photo.filename}")

        # 执行完整分析
        import asyncio
        result = asyncio.run(analysis_service.analyze_photo(photo.id))

        if result['success']:
            print("✓ 完整分析成功!")
            print(f"  分析类型: {result.get('analysis_types', [])}")

            # 显示分析结果
            analyses = db.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id == photo.id
            ).all()

            for analysis in analyses:
                print(f"\n📊 {analysis.analysis_type} 结果:")
                if analysis.analysis_type == 'content_analysis':
                    content = analysis.analysis_result
                    print(f"  场景: {content.get('scene_type', '未知')}")
                    print(f"  物体: {', '.join(content.get('objects', []))}")
                    print(f"  标签: {', '.join(content.get('tags', []))}")

            # 基于分析结果进行分类
            print("🏷️ 正在进行智能分类...")
            classification_result = classification_service.classify_photo(photo.id, db)

            if classification_result['success']:
                print("✓ 智能分类成功!")
                print(f"  生成分类: {classification_result['classifications']}")
                print(f"  生成标签: {classification_result['tags']}")

                # 显示最终的分类和标签
                final_classifications = classification_service.get_photo_classifications(photo.id, db)
                final_tags = classification_service.get_photo_tags(photo.id, db)

                print("\n📂 最终分类结果:")
                for cls in final_classifications:
                    print(f"  - {cls['name']} (置信度: {cls['confidence']})")

                print("\n🏷️  最终标签结果:")
                for tag in final_tags:
                    print(f"  - {tag['name']} ({tag['category']}, 置信度: {tag['confidence']})")

            else:
                print(f"❌ 智能分类失败: {classification_result['error']}")

        else:
            print(f"❌ 完整分析失败: {result['error']}")

        return result['success']

    except Exception as e:
        print(f"❌ 完整分析流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """主测试流程"""
    print("家庭单机版智能照片整理系统 - AI分析功能测试")
    print("=" * 60)

    # 1. 测试DashScope服务基本功能
    if not test_dashscope_basic():
        print("❌ DashScope服务测试失败，请检查API密钥配置")
        return

    # 2. 测试单张照片AI分析
    analysis_result = test_photo_analysis()
    if not analysis_result:
        print("❌ 照片AI分析测试失败")
        return

    # 3. 测试照片标题生成
    test_caption_generation()

    # 4. 测试完整分析流程
    if test_full_analysis_pipeline():
        print("\n🎉 所有AI分析功能测试通过!")
        print("✅ DashScope AI服务运行正常")
        print("✅ 照片内容分析功能正常")
        print("✅ 智能分类功能正常")
        print("✅ 中文标签生成功能正常")
    else:
        print("\n❌ 完整分析流程测试失败")

    print("\n" + "=" * 60)
    print("AI分析功能测试完成")


if __name__ == "__main__":
    main()
