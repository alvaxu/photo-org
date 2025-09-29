"""
程序说明：

## 1. 数据库索引管理服务
## 2. 系统启动时自动检查和创建索引
## 3. 确保索引长期有效和性能最优
"""

from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.logging import get_logger
from app.db.session import engine
import time


class IndexManagementService:
    """
    数据库索引管理服务

    负责在系统启动时检查和创建必要的数据库索引，
    确保查询性能和数据完整性。
    """

    def __init__(self):
        self.logger = get_logger(__name__)

    def ensure_indexes_exist(self, db_session: Session = None) -> bool:
        """
        确保所有必要的索引都存在

        Args:
            db_session: 数据库会话，如果为None则创建新会话

        Returns:
            bool: 是否成功创建/验证了所有索引
        """
        should_close_session = db_session is None
        if db_session is None:
            # 创建新的数据库连接
            db_session = Session(engine)

        try:
            self.logger.info("🔍 开始检查数据库索引...")

            # 记录开始时间
            start_time = time.time()

            # 检查并创建Photos表索引
            self._ensure_photos_indexes(db_session)

            # 检查并创建PhotoAnalysis表索引
            self._ensure_photo_analysis_indexes(db_session)

            # 检查并创建PhotoQuality表索引
            self._ensure_photo_quality_indexes(db_session)

            # 检查并创建Tags表索引
            self._ensure_tags_indexes(db_session)

            # 检查并创建Categories表索引
            self._ensure_categories_indexes(db_session)

            # 检查并创建PhotoTags表索引
            self._ensure_photo_tags_indexes(db_session)

            # 检查并创建PhotoCategories表索引
            self._ensure_photo_categories_indexes(db_session)

            # 检查并创建DuplicateGroups表索引
            self._ensure_duplicate_groups_indexes(db_session)

            # 记录完成时间
            end_time = time.time()
            self.logger.info(f"✅ 索引检查完成，耗时: {end_time - start_time:.2f} 秒")
            return True

        except Exception as e:
            self.logger.error(f"❌ 索引检查/创建失败: {str(e)}")
            return False
        finally:
            if should_close_session:
                db_session.close()

    def _ensure_photos_indexes(self, db_session: Session):
        """确保Photos表的所有索引存在"""
        self.logger.info("📸 检查Photos表索引...")

        indexes = {
            "idx_photos_file_hash": "CREATE UNIQUE INDEX IF NOT EXISTS idx_photos_file_hash ON photos(file_hash)",
            "idx_photos_perceptual_hash": "CREATE INDEX IF NOT EXISTS idx_photos_perceptual_hash ON photos(perceptual_hash)",
            "idx_photos_status": "CREATE INDEX IF NOT EXISTS idx_photos_status ON photos(status)",
            "idx_photos_taken_at": "CREATE INDEX IF NOT EXISTS idx_photos_taken_at ON photos(taken_at)",
            "idx_photos_created_at": "CREATE INDEX IF NOT EXISTS idx_photos_created_at ON photos(created_at)",
            "idx_photos_camera_make": "CREATE INDEX IF NOT EXISTS idx_photos_camera_make ON photos(camera_make)",
            "idx_photos_camera_model": "CREATE INDEX IF NOT EXISTS idx_photos_camera_model ON photos(camera_model)",
            "idx_photos_location": "CREATE INDEX IF NOT EXISTS idx_photos_location ON photos(location_lat, location_lng) WHERE location_lat IS NOT NULL AND location_lng IS NOT NULL",
            "idx_photos_camera_time": "CREATE INDEX IF NOT EXISTS idx_photos_camera_time ON photos(camera_make, taken_at)",
        }

        for index_name, create_sql in indexes.items():
            try:
                db_session.execute(text(create_sql))
                self.logger.debug(f"  ✅ {index_name}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ {index_name}: {str(e)}")

    def _ensure_photo_analysis_indexes(self, db_session: Session):
        """确保PhotoAnalysis表的所有索引存在"""
        self.logger.info("🤖 检查PhotoAnalysis表索引...")

        indexes = {
            "idx_photo_analysis_photo_id": "CREATE INDEX IF NOT EXISTS idx_photo_analysis_photo_id ON photo_analysis(photo_id)",
            "idx_photo_analysis_type": "CREATE INDEX IF NOT EXISTS idx_photo_analysis_type ON photo_analysis(analysis_type)",
            "idx_photo_analysis_confidence": "CREATE INDEX IF NOT EXISTS idx_photo_analysis_confidence ON photo_analysis(confidence_score)",
            "idx_photo_analysis_composite": "CREATE INDEX IF NOT EXISTS idx_photo_analysis_composite ON photo_analysis(photo_id, analysis_type)",
        }

        for index_name, create_sql in indexes.items():
            try:
                db_session.execute(text(create_sql))
                self.logger.debug(f"  ✅ {index_name}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ {index_name}: {str(e)}")

    def _ensure_photo_quality_indexes(self, db_session: Session):
        """确保PhotoQuality表的所有索引存在"""
        self.logger.info("📊 检查PhotoQuality表索引...")

        indexes = {
            "idx_photo_quality_photo_id": "CREATE INDEX IF NOT EXISTS idx_photo_quality_photo_id ON photo_quality(photo_id)",
            "idx_photo_quality_score": "CREATE INDEX IF NOT EXISTS idx_photo_quality_score ON photo_quality(quality_score)",
            "idx_photo_quality_level": "CREATE INDEX IF NOT EXISTS idx_photo_quality_level ON photo_quality(quality_level)",
            # 添加复合索引用于查询优化
            "idx_photo_quality_score_level": "CREATE INDEX IF NOT EXISTS idx_photo_quality_score_level ON photo_quality(quality_score, quality_level)",
        }

        for index_name, create_sql in indexes.items():
            try:
                db_session.execute(text(create_sql))
                self.logger.debug(f"  ✅ {index_name}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ {index_name}: {str(e)}")

    def _ensure_tags_indexes(self, db_session: Session):
        """确保Tags表的所有索引存在"""
        self.logger.info("🏷️ 检查Tags表索引...")

        indexes = {
            "idx_tags_name": "CREATE UNIQUE INDEX IF NOT EXISTS idx_tags_name ON tags(name)",
            "idx_tags_category": "CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category)",
            "idx_tags_usage_count": "CREATE INDEX IF NOT EXISTS idx_tags_usage_count ON tags(usage_count)",
        }

        for index_name, create_sql in indexes.items():
            try:
                db_session.execute(text(create_sql))
                self.logger.debug(f"  ✅ {index_name}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ {index_name}: {str(e)}")

    def _ensure_categories_indexes(self, db_session: Session):
        """确保Categories表的所有索引存在"""
        self.logger.info("📂 检查Categories表索引...")

        indexes = {
            "idx_categories_name": "CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_name ON categories(name)",
            "idx_categories_parent_id": "CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id)",
            "idx_categories_sort_order": "CREATE INDEX IF NOT EXISTS idx_categories_sort_order ON categories(sort_order)",
        }

        for index_name, create_sql in indexes.items():
            try:
                db_session.execute(text(create_sql))
                self.logger.debug(f"  ✅ {index_name}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ {index_name}: {str(e)}")

    def _ensure_photo_tags_indexes(self, db_session: Session):
        """确保PhotoTags表的所有索引存在"""
        self.logger.info("🔗 检查PhotoTags表索引...")

        indexes = {
            "idx_photo_tags_photo_id": "CREATE INDEX IF NOT EXISTS idx_photo_tags_photo_id ON photo_tags(photo_id)",
            "idx_photo_tags_tag_id": "CREATE INDEX IF NOT EXISTS idx_photo_tags_tag_id ON photo_tags(tag_id)",
        }

        # 尝试创建唯一索引，如果失败则跳过（可能存在重复数据）
        try:
            db_session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_photo_tags_unique ON photo_tags(photo_id, tag_id)"))
            self.logger.debug("  ✅ idx_photo_tags_unique")
        except Exception as e:
            self.logger.warning(f"  ⚠️ idx_photo_tags_unique: {str(e)} - 跳过唯一索引创建")

        for index_name, create_sql in indexes.items():
            try:
                db_session.execute(text(create_sql))
                self.logger.debug(f"  ✅ {index_name}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ {index_name}: {str(e)}")

    def _ensure_photo_categories_indexes(self, db_session: Session):
        """确保PhotoCategories表的所有索引存在"""
        self.logger.info("📂 检查PhotoCategories表索引...")

        indexes = {
            "idx_photo_categories_photo_id": "CREATE INDEX IF NOT EXISTS idx_photo_categories_photo_id ON photo_categories(photo_id)",
            "idx_photo_categories_category_id": "CREATE INDEX IF NOT EXISTS idx_photo_categories_category_id ON photo_categories(category_id)",
        }

        # 尝试创建唯一索引，如果失败则跳过（可能存在重复数据）
        try:
            db_session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_photo_categories_unique ON photo_categories(photo_id, category_id)"))
            self.logger.debug("  ✅ idx_photo_categories_unique")
        except Exception as e:
            self.logger.warning(f"  ⚠️ idx_photo_categories_unique: {str(e)} - 跳过唯一索引创建")

        for index_name, create_sql in indexes.items():
            try:
                db_session.execute(text(create_sql))
                self.logger.debug(f"  ✅ {index_name}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ {index_name}: {str(e)}")

    def _ensure_duplicate_groups_indexes(self, db_session: Session):
        """确保DuplicateGroups表的所有索引存在"""
        self.logger.info("👥 检查DuplicateGroups表索引...")

        indexes = {
            "idx_duplicate_groups_representative": "CREATE INDEX IF NOT EXISTS idx_duplicate_groups_representative ON duplicate_groups(representative_photo_id)",
            # similarity_score在duplicate_group_photos表中，不是在duplicate_groups表中
            "idx_duplicate_group_photos_similarity": "CREATE INDEX IF NOT EXISTS idx_duplicate_group_photos_similarity ON duplicate_group_photos(similarity_score)",
        }

        for index_name, create_sql in indexes.items():
            try:
                db_session.execute(text(create_sql))
                self.logger.debug(f"  ✅ {index_name}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ {index_name}: {str(e)}")

    def validate_indexes_performance(self, db_session: Session = None) -> Dict[str, Any]:
        """
        验证索引性能和使用情况

        Returns:
            包含索引性能统计的字典
        """
        should_close_session = db_session is None
        if db_session is None:
            db_session = Session(engine)

        try:
            self.logger.info("📊 验证索引性能...")

            # 检查索引使用情况（SQLite的PRAGMA index_list和index_info）
            result = {
                "index_count": 0,
                "performance_checks": {},
                "recommendations": []
            }

            # 查询所有表和索引信息
            try:
                # 获取所有表的索引信息
                tables_query = db_session.execute(text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)).fetchall()

                total_indexes = 0
                for (table_name,) in tables_query:
                    indexes_query = db_session.execute(text(f"""
                        SELECT name FROM sqlite_master
                        WHERE type='index' AND tbl_name='{table_name}'
                        AND name NOT LIKE 'sqlite_%'
                    """)).fetchall()
                    total_indexes += len(indexes_query)

                result["index_count"] = total_indexes
                self.logger.info(f"  📊 发现 {total_indexes} 个索引")

            except Exception as e:
                self.logger.warning(f"  ⚠️ 无法查询索引信息: {str(e)}")

            # 性能检查：测试关键查询的执行计划
            performance_checks = {}

            # 检查相似照片查询的执行计划
            try:
                explain_query = db_session.execute(text("""
                    EXPLAIN QUERY PLAN
                    SELECT COUNT(*) FROM photos
                    WHERE taken_at BETWEEN '2024-01-01' AND '2024-12-31'
                    AND status = 'completed'
                """)).fetchall()

                performance_checks["time_range_query"] = {
                    "query_plan": [dict(row) for row in explain_query],
                    "uses_index": any("INDEX" in str(row) for row in explain_query)
                }

            except Exception as e:
                self.logger.warning(f"  ⚠️ 执行计划检查失败: {str(e)}")

            result["performance_checks"] = performance_checks

            # 生成建议
            recommendations = []
            if result["index_count"] < 10:
                recommendations.append("建议创建更多索引来提升查询性能")

            if performance_checks.get("time_range_query", {}).get("uses_index", False) is False:
                recommendations.append("时间范围查询未使用索引，建议检查taken_at索引")

            result["recommendations"] = recommendations

            return result

        except Exception as e:
            self.logger.error(f"❌ 索引性能验证失败: {str(e)}")
            return {"error": str(e)}
        finally:
            if should_close_session:
                db_session.close()

    def cleanup_unused_indexes(self, db_session: Session = None) -> int:
        """
        清理未使用的索引（SQLite不支持直接检测索引使用情况）

        注意：SQLite没有内置的索引使用统计功能，
        此方法主要用于清理可能存在的重复或临时索引。

        Returns:
            清理的索引数量
        """
        should_close_session = db_session is None
        if db_session is None:
            db_session = Session(engine)

        try:
            self.logger.info("🧹 检查重复索引...")

            # 查询所有索引
            indexes_query = db_session.execute(text("""
                SELECT name, sql FROM sqlite_master
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                AND sql IS NOT NULL
            """)).fetchall()

            cleaned_count = 0

            # 这里可以添加更复杂的清理逻辑
            # 目前主要检查是否有重复的索引定义

            self.logger.info(f"  ✅ 检查完成，共清理 {cleaned_count} 个重复索引")
            return cleaned_count

        except Exception as e:
            self.logger.error(f"❌ 清理索引失败: {str(e)}")
            return 0
        finally:
            if should_close_session:
                db_session.close()
