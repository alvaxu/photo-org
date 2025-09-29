#!/usr/bin/env python3
"""
家庭版智能照片系统 - 数据库优化工具
执行数据关联优化、查询性能优化和索引优化
"""
from app.db.session import get_db
from sqlalchemy import text, create_engine
import time

def create_optimized_indexes():
    """创建优化的数据库索引"""
    print("=== 创建优化的数据库索引 ===")

    db = next(get_db())

    # 获取当前的数据库连接
    connection = db.connection()

    try:
        # 1. Photos表优化索引
        print("📸 优化Photos表索引...")

        # 文件哈希唯一索引（如果不存在）
        try:
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_photos_file_hash ON photos(file_hash)"))
            print("  ✅ 创建 file_hash 唯一索引")
        except Exception as e:
            print(f"  ⚠️  file_hash 索引已存在或创建失败: {e}")

        # 状态索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_status ON photos(status)"))
        print("  ✅ 创建 status 索引")

        # 拍摄时间索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_taken_at ON photos(taken_at)"))
        print("  ✅ 创建 taken_at 索引")

        # 相机品牌+型号复合索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_camera ON photos(camera_make, camera_model)"))
        print("  ✅ 创建 camera_make+camera_model 复合索引")

        # GPS位置索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_location ON photos(location_lat, location_lng) WHERE location_lat IS NOT NULL AND location_lng IS NOT NULL"))
        print("  ✅ 创建 location 复合索引")

        # 2. Photo_Analysis表优化索引
        print("\n🤖 优化Photo_Analysis表索引...")

        # 复合索引：photo_id + analysis_type（最常用查询）
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_photo_analysis_composite ON photo_analysis(photo_id, analysis_type)"))
        print("  ✅ 创建 photo_id+analysis_type 复合索引")

        # 置信度索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_photo_analysis_confidence ON photo_analysis(confidence_score)"))
        print("  ✅ 创建 confidence_score 索引")

        # 3. Photo_Quality表优化索引
        print("\n📊 优化Photo_Quality表索引...")

        # 质量分数索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_photo_quality_score ON photo_quality(quality_score)"))
        print("  ✅ 创建 quality_score 索引")

        # 质量等级索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_photo_quality_level ON photo_quality(quality_level)"))
        print("  ✅ 创建 quality_level 索引")

        # 4. Tags表优化索引
        print("\n🏷️ 优化Tags表索引...")

        # 标签名称索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)"))
        print("  ✅ 创建 name 索引")

        # 标签类别索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category)"))
        print("  ✅ 创建 category 索引")

        # 使用次数索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_tags_usage ON tags(usage_count)"))
        print("  ✅ 创建 usage_count 索引")

        # 5. Categories表优化索引
        print("\n📂 优化Categories表索引...")

        # 父分类索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id)"))
        print("  ✅ 创建 parent_id 索引")

        # 分类名称索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name)"))
        print("  ✅ 创建 name 索引")

        # 排序索引
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_categories_sort ON categories(sort_order)"))
        print("  ✅ 创建 sort_order 索引")

        # 6. 创建全文搜索虚拟表
        print("\n🔍 创建全文搜索功能...")

        # 为照片内容创建FTS5虚拟表
        fts_sql = """
        CREATE VIRTUAL TABLE IF NOT EXISTS photos_fts USING fts5(
            photo_id UNINDEXED,
            filename, original_path,
            analysis_content, tags_content,
            content=photos,
            content_rowid=id
        )
        """
        connection.execute(text(fts_sql))
        print("  ✅ 创建 FTS5 全文搜索虚拟表")

        # 为标签创建FTS5虚拟表
        fts_tags_sql = """
        CREATE VIRTUAL TABLE IF NOT EXISTS tags_fts USING fts5(
            tag_id UNINDEXED,
            name, description,
            content=tags,
            content_rowid=id
        )
        """
        connection.execute(text(fts_tags_sql))
        print("  ✅ 创建标签 FTS5 全文搜索虚拟表")

        # 填充FTS数据
        populate_fts_sql = """
        INSERT OR REPLACE INTO photos_fts(rowid, photo_id, filename, original_path, analysis_content, tags_content)
        SELECT
            p.id,
            p.id,
            p.filename,
            p.original_path,
            COALESCE(pa.analysis_result, ''),
            COALESCE(
                GROUP_CONCAT(t.name, ' '),
                ''
            )
        FROM photos p
        LEFT JOIN photo_analysis pa ON p.id = pa.photo_id AND pa.analysis_type = 'content'
        LEFT JOIN photo_tags pt ON p.id = pt.photo_id
        LEFT JOIN tags t ON pt.tag_id = t.id
        GROUP BY p.id
        """
        connection.execute(text(populate_fts_sql))
        print("  ✅ 填充 FTS 搜索数据")

        # 填充标签FTS数据
        populate_tags_fts_sql = """
        INSERT OR REPLACE INTO tags_fts(rowid, tag_id, name, description)
        SELECT id, id, name, description FROM tags
        """
        connection.execute(text(populate_tags_fts_sql))
        print("  ✅ 填充标签 FTS 搜索数据")

        # 7. 创建触发器保持FTS同步
        print("\n🔄 创建FTS同步触发器...")

        # Photos FTS触发器
        triggers = [
            # 插入触发器
            """
            CREATE TRIGGER IF NOT EXISTS photos_fts_insert AFTER INSERT ON photos
            BEGIN
                INSERT INTO photos_fts(rowid, photo_id, filename, original_path)
                VALUES (new.id, new.id, new.filename, new.original_path);
            END
            """,
            # 更新触发器
            """
            CREATE TRIGGER IF NOT EXISTS photos_fts_update AFTER UPDATE ON photos
            BEGIN
                UPDATE photos_fts SET
                    filename = new.filename,
                    original_path = new.original_path
                WHERE rowid = new.id;
            END
            """,
            # 删除触发器
            """
            CREATE TRIGGER IF NOT EXISTS photos_fts_delete AFTER DELETE ON photos
            BEGIN
                DELETE FROM photos_fts WHERE rowid = old.id;
            END
            """
        ]

        for trigger_sql in triggers:
            connection.execute(text(trigger_sql))

        print("  ✅ 创建 FTS 同步触发器")

        db.commit()
        print("\n🎉 数据库优化完成！")

    except Exception as e:
        print(f"❌ 优化过程中出错: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def test_query_performance():
    """测试查询性能"""
    print("\n=== 查询性能测试 ===")

    db = next(get_db())

    try:
        # 测试1: 基础查询性能
        print("🧪 测试基础查询...")

        start_time = time.time()
        result = db.execute(text("SELECT COUNT(*) FROM photos")).scalar()
        end_time = time.time()
        print(f"  📊 基础查询耗时: {end_time - start_time:.4f} 秒")
        # 测试2: 带索引的查询
        print("🧪 测试带索引查询...")

        start_time = time.time()
        result = db.execute(text("SELECT * FROM photos WHERE status = 'processed'")).fetchall()
        end_time = time.time()
        print(f"  📊 索引查询耗时: {end_time - start_time:.4f} 秒")
        # 测试3: 复合查询
        print("🧪 测试复合查询...")

        start_time = time.time()
        result = db.execute(text("""
            SELECT p.filename, pa.analysis_result, GROUP_CONCAT(t.name) as tags
            FROM photos p
            LEFT JOIN photo_analysis pa ON p.id = pa.photo_id AND pa.analysis_type = 'content'
            LEFT JOIN photo_tags pt ON p.id = pt.photo_id
            LEFT JOIN tags t ON pt.tag_id = t.id
            WHERE p.status = 'processed'
            GROUP BY p.id
        """)).fetchall()
        end_time = time.time()
        print(f"  📊 复合查询耗时: {end_time - start_time:.4f} 秒")
        # 测试4: 全文搜索测试
        print("🧪 测试全文搜索...")

        start_time = time.time()
        result = db.execute(text("SELECT * FROM photos_fts WHERE photos_fts MATCH '室内'")).fetchall()
        end_time = time.time()
        print(f"  📊 全文搜索耗时: {end_time - start_time:.4f} 秒")
    except Exception as e:
        print(f"❌ 性能测试出错: {e}")
    finally:
        db.close()

def optimize_database_settings():
    """优化数据库设置"""
    print("\n=== 数据库设置优化 ===")

    db = next(get_db())

    try:
        # 启用WAL模式（提高并发性能）
        db.execute(text("PRAGMA journal_mode=WAL"))
        print("✅ 启用 WAL 模式")

        # 设置同步模式
        db.execute(text("PRAGMA synchronous=NORMAL"))
        print("✅ 设置同步模式为 NORMAL")

        # 设置缓存大小
        db.execute(text("PRAGMA cache_size=-64000"))  # 64MB缓存
        print("✅ 设置缓存大小为 64MB")

        # 启用外键约束
        db.execute(text("PRAGMA foreign_keys=ON"))
        print("✅ 启用外键约束")

        # 设置临时存储
        db.execute(text("PRAGMA temp_store=MEMORY"))
        print("✅ 设置临时存储为内存模式")

        db.commit()

    except Exception as e:
        print(f"❌ 设置优化出错: {e}")
        db.rollback()
    finally:
        db.close()

def optimize_indexes():
    """优化和验证数据库索引"""
    print("\n=== 数据库索引优化 ===")

    from app.services.index_management_service import IndexManagementService
    from app.db.session import get_db

    index_service = IndexManagementService()
    db = next(get_db())

    try:
        # 1. 确保索引存在
        print("📊 检查并创建缺失的索引...")
        if index_service.ensure_indexes_exist(db):
            print("✅ 索引检查完成")

            # 2. 验证索引性能
            print("\n📈 验证索引性能...")
            perf_result = index_service.validate_indexes_performance(db)

            if "error" not in perf_result:
                print(f"   📊 总索引数量: {perf_result.get('index_count', 0)}")

                # 显示性能检查结果
                for check_name, check_data in perf_result.get("performance_checks", {}).items():
                    uses_index = check_data.get("uses_index", False)
                    status = "✅ 使用索引" if uses_index else "⚠️ 未使用索引"
                    print(f"   {status} - {check_name}")

                # 显示建议
                if perf_result.get("recommendations"):
                    print("\n💡 优化建议:")
                    for rec in perf_result["recommendations"]:
                        print(f"   • {rec}")
            else:
                print(f"   ⚠️ 性能验证失败: {perf_result['error']}")

        else:
            print("❌ 索引优化失败")

    except Exception as e:
        print(f"❌ 索引优化过程出错: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("家庭版智能照片系统 - 数据库优化工具")
    print("=" * 60)

    # 1. 优化数据库设置
    optimize_database_settings()

    # 2. 创建优化的索引
    create_optimized_indexes()

    # 3. 使用新的索引管理服务进行优化
    optimize_indexes()

    # 4. 测试查询性能
    test_query_performance()

    print("\n🎯 数据库优化任务完成！")
    print("现在可以享受更快的查询性能和更好的搜索体验！")
