#!/usr/bin/env python3
"""
程序说明：

## 1. 数据库索引检查工具
## 2. 验证系统启动时是否正确创建了索引
## 3. 检查索引的性能表现
"""

from app.db.session import get_db
from app.services.index_management_service import IndexManagementService
import time


def check_indexes():
    """检查数据库索引状态"""
    print("🔍 检查数据库索引状态")
    print("=" * 60)

    db = next(get_db())
    service = IndexManagementService()

    try:
        # 1. 验证索引存在性
        print("📊 验证索引存在性...")
        perf_result = service.validate_indexes_performance(db)

        if "error" not in perf_result:
            print(f"✅ 发现 {perf_result.get('index_count', 0)} 个索引")
        else:
            print(f"❌ 索引检查失败: {perf_result['error']}")

        # 2. 列出关键索引
        print("\n🔑 关键索引检查:")
        critical_indexes = [
            "idx_photos_taken_at",  # 时间预筛选
            "idx_photos_location",  # 位置预筛选
            "idx_photos_perceptual_hash",  # 哈希相似度
            "idx_photos_status",  # 状态筛选
            "idx_photo_analysis_composite",  # AI分析查询
        ]

        for index_name in critical_indexes:
            exists = check_index_exists(db, index_name)
            status = "✅ 存在" if exists else "❌ 缺失"
            print(f"   {status} - {index_name}")

        # 3. 性能测试
        print("\n⚡ 相似搜索相关查询性能测试...")

        # 测试时间范围查询
        print("   测试时间范围查询...")
        start_time = time.time()
        result = db.execute("""
            SELECT COUNT(*) FROM photos
            WHERE taken_at BETWEEN '2024-01-01' AND '2024-12-31'
            AND status IN ('completed', 'quality_completed', 'content_completed')
        """).scalar()
        time_query = time.time() - start_time
        print(f"   📊 时间查询耗时: {time_query:.4f} 秒")
        # 测试位置范围查询
        print("   测试位置范围查询...")
        start_time = time.time()
        result = db.execute("""
            SELECT COUNT(*) FROM photos
            WHERE location_lat BETWEEN 39.5 AND 40.5
            AND location_lng BETWEEN 116.0 AND 117.0
            AND location_lat IS NOT NULL AND location_lng IS NOT NULL
        """).scalar()
        location_query = time.time() - start_time
        print(f"   📊 位置查询耗时: {location_query:.4f} 秒")
        # 测试哈希查询
        print("   测试哈希相似查询...")
        start_time = time.time()
        result = db.execute("""
            SELECT COUNT(*) FROM photos
            WHERE perceptual_hash IS NOT NULL
            AND perceptual_hash LIKE 'a%'
        """).scalar()
        hash_query = time.time() - start_time
        print(f"   📊 哈希查询耗时: {hash_query:.4f} 秒")
        print("\n📋 性能评估:")
        if time_query < 0.1 and location_query < 0.1 and hash_query < 0.1:
            print("   ✅ 所有查询性能良好 (< 100ms)")
        else:
            print("   ⚠️ 部分查询可能需要优化")

        # 4. 给出建议
        print("\n💡 优化建议:")
        if perf_result.get('index_count', 0) < 15:
            print("   • 建议创建更多索引以提升查询性能")
        if time_query > 0.5:
            print("   • 时间查询性能较慢，检查taken_at索引")
        if location_query > 0.5:
            print("   • 位置查询性能较慢，检查location索引")

    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
    finally:
        db.close()


def check_index_exists(db, index_name):
    """检查索引是否存在"""
    try:
        result = db.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name = ?
        """, (index_name,)).fetchone()
        return result is not None
    except:
        return False


if __name__ == "__main__":
    print("家庭版智能照片系统 - 索引检查工具")
    print("=" * 60)

    check_indexes()

    print("\n🎯 索引检查完成！")
