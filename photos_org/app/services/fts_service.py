"""
程序说明：

## 1. FTS表管理服务
负责创建、检查和维护全文搜索表

## 2. 功能特点
- 在系统启动时创建FTS表和触发器
- 检查FTS表是否存在，避免重复创建
- 创建触发器保持数据同步
- 提供数据填充和重建功能

## 3. 数据同步机制
- 通过数据库触发器自动维护FTS表
- 当主表数据变化时，触发器自动更新FTS表
- 确保FTS表与主表数据一致
"""

from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.photo import Photo, PhotoAnalysis, PhotoQuality, Category, Tag, PhotoTag, PhotoCategory


class FTSService:
    """
    FTS表管理服务
    负责创建、检查和维护全文搜索表
    """

    def __init__(self):
        """初始化FTS服务"""
        self.logger = get_logger(__name__)

    def check_fts_table_exists(self, db: Session) -> bool:
        """
        检查FTS表是否存在

        :param db: 数据库会话
        :return: 是否存在
        """
        try:
            # 检查photos_fts表是否存在
            result = db.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='photos_fts'
            """)).fetchone()

            return result is not None
        except Exception as e:
            self.logger.error(f"检查FTS表存在性失败: {e}")
            return False

    def get_fts_version(self, db: Session) -> int:
        """
        获取FTS表版本

        :param db: 数据库会话
        :return: 版本号 (0=不存在, 1=旧版, 2=新版包含地址)
        """
        try:
            if not self.check_fts_table_exists(db):
                return 0

            # 检查是否存在location_name字段
            result = db.execute(text("""
                PRAGMA table_info(photos_fts)
            """)).fetchall()

            columns = [row[1] for row in result]  # 列名在第2个位置
            return 2 if 'location_name' in columns else 1
        except Exception as e:
            self.logger.error(f"获取FTS版本失败: {e}")
            return 0

    def create_fts_table(self, db: Session) -> bool:
        """
        创建FTS表
        
        :param db: 数据库会话
        :return: 是否创建成功
        """
        try:
            # 检查表是否已存在
            if self.check_fts_table_exists(db):
                self.logger.info("FTS表已存在，跳过创建")
                return True

            self.logger.info("开始创建FTS表...")

            # 创建FTS表 (V2版本，包含地址字段)
            create_fts_sql = """
            CREATE VIRTUAL TABLE photos_fts USING fts5(
                photo_id UNINDEXED,           -- 照片ID（不索引，用于关联）
                filename,                     -- 文件名
                original_path,                -- 文件路径
                description,                  -- 用户描述
                location_name,                -- 地址信息
                tags_content,                 -- 所有标签名称（空格分隔）
                categories_content,           -- 所有分类名称（空格分隔）
                analysis_content              -- AI分析结果
            )
            """
            
            db.execute(text(create_fts_sql))
            
            # 创建触发器保持数据同步
            self._create_fts_triggers(db)
            
            db.commit()
            self.logger.info("FTS表创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建FTS表失败: {e}")
            db.rollback()
            return False

    def _create_fts_triggers(self, db: Session):
        """
        创建FTS表触发器
        
        :param db: 数据库会话
        """
        try:
            # 照片插入触发器 (V2版本，包含地址)
            insert_trigger_sql = """
            CREATE TRIGGER photos_fts_insert AFTER INSERT ON photos
            BEGIN
                INSERT INTO photos_fts(
                    photo_id, filename, original_path, description, location_name,
                    tags_content, categories_content, analysis_content
                ) VALUES (
                    NEW.id,
                    NEW.filename,
                    NEW.original_path,
                    COALESCE(NEW.description, ''),
                    COALESCE(NEW.location_name, ''),
                    '',
                    '',
                    ''
                );
            END
            """
            db.execute(text(insert_trigger_sql))

            # 照片更新触发器 (V2版本，包含地址)
            update_trigger_sql = """
            CREATE TRIGGER photos_fts_update AFTER UPDATE ON photos
            BEGIN
                UPDATE photos_fts SET
                    filename = NEW.filename,
                    original_path = NEW.original_path,
                    description = COALESCE(NEW.description, ''),
                    location_name = COALESCE(NEW.location_name, '')
                WHERE photo_id = NEW.id;
            END
            """
            db.execute(text(update_trigger_sql))

            # 照片删除触发器
            delete_trigger_sql = """
            CREATE TRIGGER photos_fts_delete AFTER DELETE ON photos
            BEGIN
                DELETE FROM photos_fts WHERE photo_id = OLD.id;
            END
            """
            db.execute(text(delete_trigger_sql))

            # 标签更新触发器
            tags_update_trigger_sql = """
            CREATE TRIGGER photos_fts_tags_update AFTER INSERT ON photo_tags
            BEGIN
                UPDATE photos_fts SET
                    tags_content = (
                        SELECT GROUP_CONCAT(t.name, ' ')
                        FROM photo_tags pt
                        JOIN tags t ON pt.tag_id = t.id
                        WHERE pt.photo_id = NEW.photo_id
                    )
                WHERE photo_id = NEW.photo_id;
            END
            """
            db.execute(text(tags_update_trigger_sql))

            # 标签删除触发器
            tags_delete_trigger_sql = """
            CREATE TRIGGER photos_fts_tags_delete AFTER DELETE ON photo_tags
            BEGIN
                UPDATE photos_fts SET
                    tags_content = (
                        SELECT GROUP_CONCAT(t.name, ' ')
                        FROM photo_tags pt
                        JOIN tags t ON pt.tag_id = t.id
                        WHERE pt.photo_id = OLD.photo_id
                    )
                WHERE photo_id = OLD.photo_id;
            END
            """
            db.execute(text(tags_delete_trigger_sql))

            # 分类更新触发器
            categories_update_trigger_sql = """
            CREATE TRIGGER photos_fts_categories_update AFTER INSERT ON photo_categories
            BEGIN
                UPDATE photos_fts SET
                    categories_content = (
                        SELECT GROUP_CONCAT(c.name, ' ')
                        FROM photo_categories pc
                        JOIN categories c ON pc.category_id = c.id
                        WHERE pc.photo_id = NEW.photo_id
                    )
                WHERE photo_id = NEW.photo_id;
            END
            """
            db.execute(text(categories_update_trigger_sql))

            # 分类删除触发器
            categories_delete_trigger_sql = """
            CREATE TRIGGER photos_fts_categories_delete AFTER DELETE ON photo_categories
            BEGIN
                UPDATE photos_fts SET
                    categories_content = (
                        SELECT GROUP_CONCAT(c.name, ' ')
                        FROM photo_categories pc
                        JOIN categories c ON pc.category_id = c.id
                        WHERE pc.photo_id = OLD.photo_id
                    )
                WHERE photo_id = OLD.photo_id;
            END
            """
            db.execute(text(categories_delete_trigger_sql))

            # 分析结果更新触发器
            analysis_update_trigger_sql = """
            CREATE TRIGGER photos_fts_analysis_update AFTER INSERT ON photo_analysis
            BEGIN
                UPDATE photos_fts SET
                    analysis_content = (
                        SELECT COALESCE(json_extract(pa.analysis_result, '$.description'), '')
                        FROM photo_analysis pa
                        WHERE pa.photo_id = NEW.photo_id
                        AND pa.analysis_type = 'content'
                    )
                WHERE photo_id = NEW.photo_id;
            END
            """
            db.execute(text(analysis_update_trigger_sql))

            # 分析结果删除触发器
            analysis_delete_trigger_sql = """
            CREATE TRIGGER photos_fts_analysis_delete AFTER DELETE ON photo_analysis
            BEGIN
                UPDATE photos_fts SET
                    analysis_content = (
                        SELECT COALESCE(json_extract(pa.analysis_result, '$.description'), '')
                        FROM photo_analysis pa
                        WHERE pa.photo_id = OLD.photo_id
                        AND pa.analysis_type = 'content'
                    )
                WHERE photo_id = OLD.photo_id;
            END
            """
            db.execute(text(analysis_delete_trigger_sql))

            self.logger.info("FTS触发器创建成功")
            
        except Exception as e:
            self.logger.error(f"创建FTS触发器失败: {e}")
            raise


    def search_fts(self, db: Session, keyword: str) -> list:
        """
        使用FTS搜索照片
        
        :param db: 数据库会话
        :param keyword: 搜索关键词
        :return: 照片ID列表
        """
        try:
            if not self.check_fts_table_exists(db):
                return []

            # 执行FTS搜索
            fts_query = """
            SELECT photo_id
            FROM photos_fts
            WHERE photos_fts MATCH ?
            """
            
            result = db.execute(text(fts_query), (keyword,)).fetchall()
            return [row[0] for row in result]
            
        except Exception as e:
            self.logger.error(f"FTS搜索失败: {e}")
            return []

    def rebuild_fts_table(self, db: Session) -> bool:
        """
        重建FTS表到V2版本（包含location_name字段）

        :param db: 数据库会话
        :return: 是否重建成功
        """
        try:
            self.logger.info("开始重建FTS表到V2版本...")

            # 1. 删除现有触发器
            self._drop_fts_triggers(db)
            self.logger.info("现有触发器删除完成")

            # 2. 删除现有FTS表
            db.execute(text("DROP TABLE IF EXISTS photos_fts"))
            self.logger.info("FTS表删除完成")

            # 3. 创建新的V2版本FTS表
            create_fts_sql = """
            CREATE VIRTUAL TABLE photos_fts USING fts5(
                photo_id UNINDEXED,
                filename,
                original_path,
                description,
                location_name,
                tags_content,
                categories_content,
                analysis_content
            )
            """
            db.execute(text(create_fts_sql))
            self.logger.info("新FTS表创建完成")

            # 4. 创建V2版本触发器
            self._create_fts_triggers_v2(db)
            self.logger.info("V2触发器创建完成")

            # 5. 填充所有数据
            populate_sql = """
            INSERT INTO photos_fts(
                photo_id, filename, original_path, description, location_name,
                tags_content, categories_content, analysis_content
            )
            SELECT
                p.id,
                p.filename,
                p.original_path,
                COALESCE(p.description, ''),
                COALESCE(p.location_name, ''),
                COALESCE((
                    SELECT GROUP_CONCAT(t.name, ' ')
                    FROM photo_tags pt
                    JOIN tags t ON pt.tag_id = t.id
                    WHERE pt.photo_id = p.id
                ), ''),
                COALESCE((
                    SELECT GROUP_CONCAT(c.name, ' ')
                    FROM photo_categories pc
                    JOIN categories c ON pc.category_id = c.id
                    WHERE pc.photo_id = p.id
                ), ''),
                COALESCE((
                    SELECT json_extract(pa.analysis_result, '$.description')
                    FROM photo_analysis pa
                    WHERE pa.photo_id = p.id
                    AND pa.analysis_type = 'content'
                    LIMIT 1
                ), '')
            FROM photos p
            """
            result = db.execute(text(populate_sql))
            self.logger.info(f"FTS表数据填充完成，填充行数: {result.rowcount}")

            db.commit()
            return True

        except Exception as e:
            self.logger.error(f"FTS表重建失败: {e}")
            db.rollback()
            return False



    def _drop_fts_triggers(self, db: Session):
        """
        删除所有FTS相关的触发器

        :param db: 数据库会话
        """
        try:
            # 获取所有FTS相关的触发器
            trigger_names = [
                'photos_fts_insert',
                'photos_fts_update',
                'photos_fts_delete',
                'photos_fts_tags_update',
                'photos_fts_tags_delete',
                'photos_fts_categories_update',
                'photos_fts_categories_delete',
                'photos_fts_analysis_update',
                'photos_fts_analysis_delete'
            ]

            for trigger_name in trigger_names:
                try:
                    db.execute(text(f"DROP TRIGGER IF EXISTS {trigger_name}"))
                except Exception as e:
                    self.logger.warning(f"删除触发器 {trigger_name} 失败: {e}")

            self.logger.info("FTS相关触发器删除完成")

        except Exception as e:
            self.logger.error(f"删除FTS触发器失败: {e}")

    def _create_fts_triggers_v2(self, db: Session):
        """
        创建V2版本触发器（包含地址字段）

        :param db: 数据库会话
        """
        try:
            # 照片插入触发器 - 包含地址
            insert_trigger_sql = """
            CREATE TRIGGER photos_fts_insert AFTER INSERT ON photos
            BEGIN
                INSERT INTO photos_fts(
                    photo_id, filename, original_path, description, location_name,
                    tags_content, categories_content, analysis_content
                ) VALUES (
                    NEW.id,
                    NEW.filename,
                    NEW.original_path,
                    COALESCE(NEW.description, ''),
                    COALESCE(NEW.location_name, ''),
                    '', '', ''
                );
            END
            """
            db.execute(text(insert_trigger_sql))

            # 照片更新触发器 - 包含地址更新
            update_trigger_sql = """
            CREATE TRIGGER photos_fts_update AFTER UPDATE ON photos
            BEGIN
                UPDATE photos_fts SET
                    filename = NEW.filename,
                    original_path = NEW.original_path,
                    description = COALESCE(NEW.description, ''),
                    location_name = COALESCE(NEW.location_name, '')
                WHERE photo_id = NEW.id;
            END
            """
            db.execute(text(update_trigger_sql))

            # 照片删除触发器
            delete_trigger_sql = """
            CREATE TRIGGER photos_fts_delete AFTER DELETE ON photos
            BEGIN
                DELETE FROM photos_fts WHERE photo_id = OLD.id;
            END
            """
            db.execute(text(delete_trigger_sql))

            # 标签更新触发器
            tags_update_trigger_sql = """
            CREATE TRIGGER photos_fts_tags_update AFTER INSERT ON photo_tags
            BEGIN
                UPDATE photos_fts SET
                    tags_content = (
                        SELECT GROUP_CONCAT(t.name, ' ')
                        FROM photo_tags pt
                        JOIN tags t ON pt.tag_id = t.id
                        WHERE pt.photo_id = NEW.photo_id
                    )
                WHERE photo_id = NEW.photo_id;
            END
            """
            db.execute(text(tags_update_trigger_sql))

            # 标签删除触发器
            tags_delete_trigger_sql = """
            CREATE TRIGGER photos_fts_tags_delete AFTER DELETE ON photo_tags
            BEGIN
                UPDATE photos_fts SET
                    tags_content = (
                        SELECT GROUP_CONCAT(t.name, ' ')
                        FROM photo_tags pt
                        JOIN tags t ON pt.tag_id = t.id
                        WHERE pt.photo_id = OLD.photo_id
                    )
                WHERE photo_id = OLD.photo_id;
            END
            """
            db.execute(text(tags_delete_trigger_sql))

            # 分类更新触发器
            categories_update_trigger_sql = """
            CREATE TRIGGER photos_fts_categories_update AFTER INSERT ON photo_categories
            BEGIN
                UPDATE photos_fts SET
                    categories_content = (
                        SELECT GROUP_CONCAT(c.name, ' ')
                        FROM photo_categories pc
                        JOIN categories c ON pc.category_id = c.id
                        WHERE pc.photo_id = NEW.photo_id
                    )
                WHERE photo_id = NEW.photo_id;
            END
            """
            db.execute(text(categories_update_trigger_sql))

            # 分类删除触发器
            categories_delete_trigger_sql = """
            CREATE TRIGGER photos_fts_categories_delete AFTER DELETE ON photo_categories
            BEGIN
                UPDATE photos_fts SET
                    categories_content = (
                        SELECT GROUP_CONCAT(c.name, ' ')
                        FROM photo_categories pc
                        JOIN categories c ON pc.category_id = c.id
                        WHERE pc.photo_id = OLD.photo_id
                    )
                WHERE photo_id = OLD.photo_id;
            END
            """
            db.execute(text(categories_delete_trigger_sql))

            # 分析结果更新触发器
            analysis_update_trigger_sql = """
            CREATE TRIGGER photos_fts_analysis_update AFTER INSERT ON photo_analysis
            BEGIN
                UPDATE photos_fts SET
                    analysis_content = (
                        SELECT COALESCE(json_extract(pa.analysis_result, '$.description'), '')
                        FROM photo_analysis pa
                        WHERE pa.photo_id = NEW.photo_id
                        AND pa.analysis_type = 'content'
                    )
                WHERE photo_id = NEW.photo_id;
            END
            """
            db.execute(text(analysis_update_trigger_sql))

            # 分析结果删除触发器
            analysis_delete_trigger_sql = """
            CREATE TRIGGER photos_fts_analysis_delete AFTER DELETE ON photo_analysis
            BEGIN
                UPDATE photos_fts SET
                    analysis_content = (
                        SELECT COALESCE(json_extract(pa.analysis_result, '$.description'), '')
                        FROM photo_analysis pa
                        WHERE pa.photo_id = OLD.photo_id
                        AND pa.analysis_type = 'content'
                    )
                WHERE photo_id = OLD.photo_id;
            END
            """
            db.execute(text(analysis_delete_trigger_sql))

            self.logger.info("FTS V2触发器创建成功")

        except Exception as e:
            self.logger.error(f"创建FTS V2触发器失败: {e}")
            raise



    def _cleanup_backup_table(self, db: Session):
        """
        清理备份表（升级成功后）

        :param db: 数据库会话
        """
        try:
            # 检查备份表是否存在
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='photos_fts_backup'")).fetchone()
            if result:
                # 删除备份表
                db.execute(text("DROP TABLE photos_fts_backup"))
                self.logger.info("FTS备份表已清理")
            else:
                self.logger.debug("没有找到FTS备份表，无需清理")

        except Exception as e:
            self.logger.warning(f"清理FTS备份表失败: {e}")




