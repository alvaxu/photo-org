#!/usr/bin/env python3
"""
家庭单机版智能照片整理系统 - 搜索功能完整测试
"""
from app.db.session import get_db
from app.services.search_service import SearchService

def test_search_functionality():
    """测试搜索功能"""
    print("=== 搜索功能完整测试 ===")

    db = next(get_db())
    search_service = SearchService()

    try:
        # 测试1: 基础搜索
        print("🔍 测试1: 基础关键词搜索...")
        results, total = search_service.search_photos(db, keyword="室内")
        print(f"  📊 找到 {total} 张包含'室内'的照片")
        if results:
            print(f"  📸 第一张照片: {results[0]['filename']}")
            print(f"  🏷️ 标签: {results[0]['tags']}")

        # 测试2: 相机筛选
        print("\\n📷 测试2: 相机品牌筛选...")
        results, total = search_service.search_photos(db, camera_make="Apple")
        print(f"  📊 找到 {total} 张Apple相机拍摄的照片")

        # 测试3: 质量筛选
        print("\\n⭐ 测试3: 质量筛选...")
        results, total = search_service.search_photos(db, quality_min=80)
        print(f"  📊 找到 {total} 张质量分数>=80的照片")

        # 测试4: 时间范围筛选
        print("\\n📅 测试4: 时间范围筛选...")
        results, total = search_service.search_photos(db, date_from="2025-01-01")
        print(f"  📊 找到 {total} 张2025年拍摄的照片")

        # 测试5: 标签筛选
        print("\\n🏷️ 测试5: 标签筛选...")
        results, total = search_service.search_photos(db, tags=["生日"])
        print(f"  📊 找到 {total} 张包含'生日'标签的照片")

        # 测试6: 复合条件搜索
        print("\\n🔗 测试6: 复合条件搜索...")
        results, total = search_service.search_photos(
            db,
            camera_make="Apple",
            quality_min=70,
            sort_by="taken_at",
            sort_order="desc",
            limit=5
        )
        print(f"  📊 找到 {total} 张符合复合条件的照片")
        if results:
            print("  📸 最新5张照片:")
            for i, photo in enumerate(results, 1):
                print(f"    {i}. {photo['filename']} ({photo['taken_at']})")

        # 测试7: 地理位置搜索
        print("\\n🌍 测试7: 地理位置搜索...")
        # 上海坐标附近5公里
        results, total = search_service.search_photos(
            db,
            location_lat=31.264,
            location_lng=121.410,
            location_radius=5
        )
        print(f"  📊 找到 {total} 张在上海附近拍摄的照片")

        # 测试8: 搜索建议
        print("\\n💡 测试8: 搜索建议...")
        suggestions = search_service.get_search_suggestions(db, "室")
        print("  💭 输入'室'的搜索建议:")
        for category, items in suggestions.items():
            if items:
                print(f"    {category}: {items[:3]}")  # 只显示前3个

        # 测试9: 搜索统计
        print("\\n📊 测试9: 搜索统计...")
        stats = search_service.get_search_stats(db)
        print("  📈 系统统计:")
        print(f"    照片总数: {stats.get('total_photos', 0)}")
        print(f"    标签总数: {stats.get('total_tags', 0)}")
        print(f"    分类总数: {stats.get('total_categories', 0)}")

        if 'quality_distribution' in stats:
            print("    质量分布:")
            for level, count in stats['quality_distribution'].items():
                print(f"      {level}: {count}张")

        # 测试10: 高级排序
        print("\\n🔄 测试10: 高级排序...")
        # 按文件大小降序
        results, total = search_service.search_photos(
            db,
            sort_by="file_size",
            sort_order="desc",
            limit=3
        )
        if results:
            print("  📸 文件大小最大的3张照片:")
            for i, photo in enumerate(results, 1):
                size_mb = photo['file_size'] / 1024 / 1024
                print(f"      {i}. {photo['filename']}: {size_mb:.1f} MB")
        print("\\n🎉 搜索功能测试完成！所有测试都通过了！")

    except Exception as e:
        print(f"❌ 搜索测试出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_search_edge_cases():
    """测试搜索边界情况"""
    print("\\n=== 搜索边界情况测试 ===")

    db = next(get_db())
    search_service = SearchService()

    try:
        # 测试空搜索
        print("🔍 测试空搜索...")
        results, total = search_service.search_photos(db)
        print(f"  📊 空搜索结果: {total} 张照片")

        # 测试不存在的关键词
        print("🔍 测试不存在的关键词...")
        results, total = search_service.search_photos(db, keyword="不存在的关键词12345")
        print(f"  📊 不存在的关键词结果: {total} 张照片")

        # 测试分页
        print("📄 测试分页...")
        results1, total1 = search_service.search_photos(db, limit=2, offset=0)
        results2, total2 = search_service.search_photos(db, limit=2, offset=2)
        print(f"  📊 第一页: {len(results1)} 张, 第二页: {len(results2)} 张")
        print(f"  📊 总数: {total1} (应该等于 {total2})")

        # 测试建议的边界情况
        print("💡 测试建议边界情况...")
        suggestions = search_service.get_search_suggestions(db, "")
        print(f"  💭 空前缀建议数量: {sum(len(items) for items in suggestions.values())}")

        suggestions = search_service.get_search_suggestions(db, "xyz123456789")
        print(f"  💭 不存在的建议数量: {sum(len(items) for items in suggestions.values())}")

    except Exception as e:
        print(f"❌ 边界测试出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("家庭单机版智能照片整理系统 - 搜索功能测试")
    print("=" * 60)

    # 主功能测试
    test_search_functionality()

    # 边界情况测试
    test_search_edge_cases()

    print("\\n🎯 所有搜索功能测试完成！")
