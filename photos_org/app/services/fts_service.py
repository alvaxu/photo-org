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

            # 创建FTS表
            create_fts_sql = """
            CREATE VIRTUAL TABLE photos_fts USING fts5(
                photo_id UNINDEXED,           -- 照片ID（不索引，用于关联）
                filename,                     -- 文件名
                original_path,                -- 文件路径
                description,                  -- 用户描述
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
            # 照片插入触发器
            insert_trigger_sql = """
            CREATE TRIGGER photos_fts_insert AFTER INSERT ON photos
            BEGIN
                INSERT INTO photos_fts(
                    photo_id, filename, original_path, description,
                    tags_content, categories_content, analysis_content
                ) VALUES (
                    NEW.id,
                    NEW.filename,
                    NEW.original_path,
                    COALESCE(NEW.description, ''),
                    '',
                    '',
                    ''
                );
            END
            """
            db.execute(text(insert_trigger_sql))

            # 照片更新触发器
            update_trigger_sql = """
            CREATE TRIGGER photos_fts_update AFTER UPDATE ON photos
            BEGIN
                UPDATE photos_fts SET
                    filename = NEW.filename,
                    original_path = NEW.original_path,
                    description = COALESCE(NEW.description, '')
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
        重建FTS表
        
        :param db: 数据库会话
        :return: 是否重建成功
        """
        try:
            # 删除现有FTS表
            if self.check_fts_table_exists(db):
                db.execute(text("DROP TABLE photos_fts"))
                self.logger.info("删除现有FTS表")

            # 重新创建FTS表
            return self.create_fts_table(db)
            
        except Exception as e:
            self.logger.error(f"重建FTS表失败: {e}")
            return False

    def populate_fts_table(self, db: Session) -> bool:
        """
        填充FTS表数据
        将现有照片数据填充到FTS表中
        
        :param db: 数据库会话
        :return: 是否填充成功
        """
        try:
            if not self.check_fts_table_exists(db):
                self.logger.warning("FTS表不存在，无法填充数据")
                return False

            self.logger.info("开始填充FTS表数据...")
            
            # 清空现有数据
            db.execute(text("DELETE FROM photos_fts"))
            
            # 填充照片基础数据
            insert_sql = """
            INSERT INTO photos_fts(
                photo_id, filename, original_path, description,
                tags_content, categories_content, analysis_content
            )
            SELECT 
                p.id,
                p.filename,
                p.original_path,
                COALESCE(p.description, ''),
                COALESCE(
                    (SELECT GROUP_CONCAT(t.name, ' ')
                     FROM photo_tags pt
                     JOIN tags t ON pt.tag_id = t.id
                     WHERE pt.photo_id = p.id), ''
                ),
                COALESCE(
                    (SELECT GROUP_CONCAT(c.name, ' ')
                     FROM photo_categories pc
                     JOIN categories c ON pc.category_id = c.id
                     WHERE pc.photo_id = p.id), ''
                ),
                COALESCE(
                    (SELECT json_extract(pa.analysis_result, '$.description')
                     FROM photo_analysis pa
                     WHERE pa.photo_id = p.id
                     AND pa.analysis_type = 'content'
                     LIMIT 1), ''
                )
            FROM photos p
            """
            
            result = db.execute(text(insert_sql))
            db.commit()
            
            self.logger.info(f"FTS表数据填充完成，填充行数: {result.rowcount}")
            return True
            
        except Exception as e:
            self.logger.error(f"填充FTS表数据失败: {e}")
            db.rollback()
            return False

    def update_existing_analysis_content(self, db: Session) -> bool:
        """
        更新现有FTS表中的analysis_content字段
        将JSON格式转换为只包含description的纯文本
        
        :param db: 数据库会话
        :return: 是否更新成功
        """
        try:
            if not self.check_fts_table_exists(db):
                self.logger.warning("FTS表不存在，无法更新")
                return False

            self.logger.info("开始更新现有FTS表的analysis_content字段...")
            
            # 更新analysis_content字段，只提取description
            update_sql = """
            UPDATE photos_fts SET
                analysis_content = (
                    SELECT COALESCE(json_extract(pa.analysis_result, '$.description'), '')
                    FROM photo_analysis pa
                    WHERE pa.photo_id = photos_fts.photo_id
                    AND pa.analysis_type = 'content'
                )
            WHERE EXISTS (
                SELECT 1 FROM photo_analysis pa 
                WHERE pa.photo_id = photos_fts.photo_id
                AND pa.analysis_type = 'content'
            )
            """
            
            result = db.execute(text(update_sql))
            db.commit()
            
            self.logger.info(f"FTS表analysis_content字段更新完成，影响行数: {result.rowcount}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新FTS表analysis_content字段失败: {e}")
            db.rollback()
            return False
