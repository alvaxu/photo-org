"""
数据库迁移服务

自动检查并添加缺失的数据库字段

## 功能特点：
1. 自动检查image_features相关字段是否存在
2. 不存在则自动添加
3. 已存在则跳过
4. 支持启动时自动调用

## 与其他版本的不同点：
- 参考add_face_count_fields.py的实现模式
- 集成到启动流程中
"""

from sqlalchemy import text
from app.db.session import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)


def check_and_add_image_features_fields():
    """
    检查并添加图像特征提取相关字段
    
    功能：
    - 检查 image_features_extracted 字段是否存在，不存在则添加
    - 检查 image_features_extracted_at 字段是否存在，不存在则添加
    - 检查 image_features 字段是否存在，不存在则添加
    
    Returns:
        bool: 是否成功
    """
    db = next(get_db())
    try:
        logger.info("开始检查图像特征提取相关字段...")
        
        # 定义需要添加的字段
        fields_to_add = [
            {
                'name': 'image_features_extracted',
                'sql': 'ALTER TABLE photos ADD COLUMN image_features_extracted BOOLEAN DEFAULT 0',
                'description': '是否已提取特征'
            },
            {
                'name': 'image_features_extracted_at',
                'sql': 'ALTER TABLE photos ADD COLUMN image_features_extracted_at DATETIME',
                'description': '特征提取时间'
            },
            {
                'name': 'image_features',
                'sql': 'ALTER TABLE photos ADD COLUMN image_features TEXT',
                'description': '特征向量（JSON格式）'
            }
        ]
        
        added_count = 0
        skipped_count = 0
        
        for field in fields_to_add:
            # 检查字段是否已存在
            check_result = db.execute(text(f"""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('photos') 
                WHERE name = '{field['name']}'
            """)).fetchone()
            
            if check_result[0] == 0:
                # 字段不存在，添加字段
                logger.info(f"添加 {field['name']} 字段 ({field['description']})...")
                db.execute(text(field['sql']))
                logger.info(f"✅ {field['name']} 字段添加成功")
                added_count += 1
            else:
                # 字段已存在，跳过
                logger.info(f"{field['name']} 字段已存在，跳过")
                skipped_count += 1
        
        # 提交更改
        db.commit()
        
        if added_count > 0:
            logger.info(f"🎉 数据库迁移完成！添加了 {added_count} 个字段，跳过 {skipped_count} 个已存在的字段")
        else:
            logger.info(f"✅ 所有字段已存在，无需迁移。跳过 {skipped_count} 个字段")
        
        # 验证字段添加结果
        verify_fields = db.execute(text("""
            SELECT name, type, dflt_value 
            FROM pragma_table_info('photos') 
            WHERE name IN ('image_features_extracted', 'image_features_extracted_at', 'image_features')
            ORDER BY name
        """)).fetchall()
        
        if verify_fields:
            logger.info("字段验证结果：")
            for field in verify_fields:
                logger.info(f"  - {field[0]}: {field[1]} (默认值: {field[2]})")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库字段检查失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def check_and_add_similar_photo_cluster_fields():
    """
    检查并添加相似照片聚类相关字段
    
    功能：
    - duplicate_groups表：添加id, cluster_id, avg_similarity, confidence_score, cluster_quality, created_at, updated_at
    - duplicate_group_photos表：添加id, cluster_id, created_at
    
    Returns:
        bool: 是否成功
    """
    db = next(get_db())
    try:
        logger.info("开始检查相似照片聚类相关字段...")
        
        # duplicate_groups表的字段
        duplicate_groups_fields = [
            {
                'name': 'id',
                'sql': 'ALTER TABLE duplicate_groups ADD COLUMN id INTEGER',
                'description': '主键ID（注意：SQLite不支持ALTER TABLE添加PRIMARY KEY，需要手动处理）',
                'table': 'duplicate_groups'
            },
            {
                'name': 'cluster_id',
                'sql': 'ALTER TABLE duplicate_groups ADD COLUMN cluster_id VARCHAR(50)',
                'description': '聚类业务标识',
                'table': 'duplicate_groups'
            },
            {
                'name': 'avg_similarity',
                'sql': 'ALTER TABLE duplicate_groups ADD COLUMN avg_similarity REAL',
                'description': '聚类内平均相似度',
                'table': 'duplicate_groups'
            },
            {
                'name': 'confidence_score',
                'sql': 'ALTER TABLE duplicate_groups ADD COLUMN confidence_score REAL',
                'description': '聚类置信度',
                'table': 'duplicate_groups'
            },
            {
                'name': 'cluster_quality',
                'sql': 'ALTER TABLE duplicate_groups ADD COLUMN cluster_quality VARCHAR(20)',
                'description': '聚类质量',
                'table': 'duplicate_groups'
            },
            {
                'name': 'created_at',
                'sql': 'ALTER TABLE duplicate_groups ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP',
                'description': '创建时间',
                'table': 'duplicate_groups'
            },
            {
                'name': 'updated_at',
                'sql': 'ALTER TABLE duplicate_groups ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP',
                'description': '更新时间',
                'table': 'duplicate_groups'
            }
        ]
        
        # duplicate_group_photos表的字段
        duplicate_group_photos_fields = [
            {
                'name': 'id',
                'sql': 'ALTER TABLE duplicate_group_photos ADD COLUMN id INTEGER',
                'description': '主键ID（注意：SQLite不支持ALTER TABLE添加PRIMARY KEY，需要手动处理）',
                'table': 'duplicate_group_photos'
            },
            {
                'name': 'cluster_id',
                'sql': 'ALTER TABLE duplicate_group_photos ADD COLUMN cluster_id VARCHAR(50)',
                'description': '聚类业务标识',
                'table': 'duplicate_group_photos'
            },
            {
                'name': 'created_at',
                'sql': 'ALTER TABLE duplicate_group_photos ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP',
                'description': '创建时间',
                'table': 'duplicate_group_photos'
            }
        ]
        
        added_count = 0
        skipped_count = 0
        
        # 处理duplicate_groups表
        for field in duplicate_groups_fields:
            check_result = db.execute(text(f"""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('duplicate_groups') 
                WHERE name = '{field['name']}'
            """)).fetchone()
            
            if check_result[0] == 0:
                logger.info(f"添加 duplicate_groups.{field['name']} 字段 ({field['description']})...")
                try:
                    db.execute(text(field['sql']))
                    logger.info(f"✅ duplicate_groups.{field['name']} 字段添加成功")
                    added_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ duplicate_groups.{field['name']} 字段添加失败: {str(e)}")
            else:
                logger.debug(f"duplicate_groups.{field['name']} 字段已存在，跳过")
                skipped_count += 1
        
        # 处理duplicate_group_photos表
        for field in duplicate_group_photos_fields:
            check_result = db.execute(text(f"""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('duplicate_group_photos') 
                WHERE name = '{field['name']}'
            """)).fetchone()
            
            if check_result[0] == 0:
                logger.info(f"添加 duplicate_group_photos.{field['name']} 字段 ({field['description']})...")
                try:
                    db.execute(text(field['sql']))
                    logger.info(f"✅ duplicate_group_photos.{field['name']} 字段添加成功")
                    added_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ duplicate_group_photos.{field['name']} 字段添加失败: {str(e)}")
            else:
                logger.debug(f"duplicate_group_photos.{field['name']} 字段已存在，跳过")
                skipped_count += 1
        
        # 提交更改
        db.commit()
        
        logger.info(f"✅ 相似照片聚类字段检查完成（新增: {added_count}, 已存在: {skipped_count}）")
        return True
    except Exception as e:
        logger.error(f"检查相似照片聚类字段失败: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def check_and_add_favorite_field():
    """
    检查并添加收藏字段
    
    功能：
    - 检查 is_favorite 字段是否存在，不存在则添加
    
    Returns:
        bool: 是否成功
    """
    db = next(get_db())
    try:
        logger.info("开始检查收藏字段...")
        
        # 定义需要添加的字段
        field_to_add = {
            'name': 'is_favorite',
            'sql': 'ALTER TABLE photos ADD COLUMN is_favorite BOOLEAN DEFAULT 0',
            'description': '是否收藏'
        }
        
        # 检查字段是否已存在
        check_result = db.execute(text(f"""
            SELECT COUNT(*) as count 
            FROM pragma_table_info('photos') 
            WHERE name = '{field_to_add['name']}'
        """)).fetchone()
        
        if check_result[0] == 0:
            # 字段不存在，添加字段
            logger.info(f"添加 {field_to_add['name']} 字段 ({field_to_add['description']})...")
            db.execute(text(field_to_add['sql']))
            logger.info(f"✅ {field_to_add['name']} 字段添加成功")
            db.commit()
            
            # 验证字段添加结果
            verify_field = db.execute(text("""
                SELECT name, type, dflt_value 
                FROM pragma_table_info('photos') 
                WHERE name = 'is_favorite'
            """)).fetchone()
            
            if verify_field:
                logger.info(f"字段验证结果: {verify_field[0]}: {verify_field[1]} (默认值: {verify_field[2]})")
            
            return True
        else:
            # 字段已存在，跳过
            logger.info(f"{field_to_add['name']} 字段已存在，跳过")
            return True
            
    except Exception as e:
        logger.error(f"数据库字段检查失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()