#!/usr/bin/env python3
"""
家庭单机版智能照片整理系统 - 搜索功能测试
"""
from app.db.session import get_db
from sqlalchemy import text

def test_fulltext_search():
    """测试全文搜索功能"""
    print("=== 全文搜索功能测试 ===")

    db = next(get_db())

    try:
        # 测试1: 搜索包含"室内"的照片
        print("🔍 搜索包含'室内'的照片...")
        result = db.execute(text("SELECT photo_id, filename FROM photos_fts WHERE photos_fts MATCH '室内'")).fetchall()
        print(f"  📊 找到 {len(result)} 张室内照片")

        # 测试2: 搜索标签
        print("🏷️ 搜索标签...")
        result = db.execute(text("SELECT tag_id, name FROM tags_fts WHERE tags_fts MATCH '生日'")).fetchall()
        print(f"  📊 找到 {len(result)} 个生日相关标签")

        # 测试3: 组合查询 - 通过标签找照片
        print("🔗 组合查询测试...")
        query = """
        SELECT p.filename, t.name as tag_name, pa.analysis_result
        FROM photos p
        JOIN photo_tags pt ON p.id = pt.photo_id
        JOIN tags t ON pt.tag_id = t.id
        LEFT JOIN photo_analysis pa ON p.id = pa.photo_id AND pa.analysis_type = 'content'
        WHERE t.name LIKE '%生日%'
        LIMIT 5
        """
        result = db.execute(text(query)).fetchall()
        print(f"  📊 找到 {len(result)} 张生日照片")

        # 测试4: 高级搜索 - 按时间和标签筛选
        print("⚡ 高级搜索测试...")
        query = """
        SELECT p.filename, p.taken_at, GROUP_CONCAT(t.name) as tags
        FROM photos p
        LEFT JOIN photo_tags pt ON p.id = pt.photo_id
        LEFT JOIN tags t ON pt.tag_id = t.id
        WHERE p.taken_at >= '2025-01-01'
        GROUP BY p.id
        ORDER BY p.taken_at DESC
        LIMIT 3
        """
        result = db.execute(text(query)).fetchall()
        print(f"  📊 找到 {len(result)} 张2025年以后的照片")

        # 测试5: 质量筛选
        print("⭐ 质量筛选测试...")
        query = """
        SELECT p.filename, pq.quality_score, pq.quality_level
        FROM photos p
        JOIN photo_quality pq ON p.id = pq.photo_id
        WHERE pq.quality_score >= 90
        ORDER BY pq.quality_score DESC
        LIMIT 3
        """
        result = db.execute(text(query)).fetchall()
        print(f"  📊 找到 {len(result)} 张高质量照片")

    except Exception as e:
        print(f"❌ 搜索测试出错: {e}")
    finally:
        db.close()

def test_index_performance():
    """测试索引性能"""
    print("\n=== 索引性能测试 ===")

    db = next(get_db())

    try:
        import time

        # 测试无索引 vs 有索引的查询
        print("⚡ 对比查询性能...")

        # 查询1: 按状态筛选（有索引）
        start_time = time.time()
        result = db.execute(text("SELECT COUNT(*) FROM photos WHERE status = 'processed'")).scalar()
        end_time = time.time()
        print(f"  📊 状态查询耗时: {end_time - start_time:.4f} 秒")
        # 查询2: 按相机品牌筛选（有索引）
        start_time = time.time()
        result = db.execute(text("SELECT COUNT(*) FROM photos WHERE camera_make = 'Apple'")).scalar()
        end_time = time.time()
        print(f"  📊 相机查询耗时: {end_time - start_time:.4f} 秒")
        # 查询3: 复合条件查询
        start_time = time.time()
        result = db.execute(text("""
            SELECT p.filename
            FROM photos p
            JOIN photo_tags pt ON p.id = pt.photo_id
            JOIN tags t ON pt.tag_id = t.id
            WHERE p.camera_make = 'Apple' AND t.name LIKE '%室内%'
        """)).fetchall()
        end_time = time.time()
        print(f"  📊 复合查询耗时: {end_time - start_time:.4f} 秒")
        # 查询4: 时间范围查询（有索引）
        start_time = time.time()
        result = db.execute(text("SELECT COUNT(*) FROM photos WHERE taken_at >= '2025-01-01'")).scalar()
        end_time = time.time()
        print(f"  📊 时间查询耗时: {end_time - start_time:.4f} 秒")
    except Exception as e:
        print(f"❌ 性能测试出错: {e}")
    finally:
        db.close()

def show_optimization_summary():
    """显示优化总结"""
    print("\n=== 数据库优化总结 ===")

    db = next(get_db())

    try:
        # 查看所有索引
        indexes = db.execute(text("""
            SELECT name, tbl_name, sql
            FROM sqlite_master
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY tbl_name, name
        """)).fetchall()

        print(f"📊 总索引数量: {len(indexes)}")

        # 按表分组显示
        current_table = None
        for idx in indexes:
            if current_table != idx[1]:
                if current_table is not None:
                    print()
                current_table = idx[1]
                print(f"📋 {current_table}表:")

            # 提取索引信息
            sql = idx[2] or ""
            if "UNIQUE" in sql:
                idx_type = "UNIQUE"
            else:
                idx_type = "普通"

            print(f"  - {idx[0]} ({idx_type})")

        # 查看虚拟表
        virtual_tables = db.execute(text("""
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND sql LIKE '%VIRTUAL%'
        """)).fetchall()

        print(f"\n🔍 全文搜索虚拟表: {len(virtual_tables)}")
        for vt in virtual_tables:
            print(f"  - {vt[0]}")

        # 数据统计
        stats = {
            "照片": db.execute(text("SELECT COUNT(*) FROM photos")).scalar(),
            "AI分析": db.execute(text("SELECT COUNT(*) FROM photo_analysis")).scalar(),
            "质量评估": db.execute(text("SELECT COUNT(*) FROM photo_quality")).scalar(),
            "标签": db.execute(text("SELECT COUNT(*) FROM tags")).scalar(),
            "分类": db.execute(text("SELECT COUNT(*) FROM categories")).scalar(),
        }

        print("\n📈 数据统计:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")

    except Exception as e:
        print(f"❌ 获取优化总结出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("家庭单机版智能照片整理系统 - 搜索功能测试")
    print("=" * 60)

    # 1. 测试全文搜索
    test_fulltext_search()

    # 2. 测试索引性能
    test_index_performance()

    # 3. 显示优化总结
    show_optimization_summary()

    print("\n🎯 搜索功能测试完成！")
