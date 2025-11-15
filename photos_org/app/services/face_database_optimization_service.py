"""
人脸识别数据库优化服务

## 功能特点：
1. 为人脸识别相关表添加必要的索引
2. 优化查询性能
3. 清理无效数据
4. 更新数据库统计信息

## 与其他版本的不同点：
- 从utilities目录迁移到app/services目录
- 作为应用启动时的核心服务
- 集成到应用的生命周期管理中
"""

import sqlite3
import logging
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

def optimize_face_recognition_database():
    """
    优化人脸识别数据库
    
    :return: 是否优化成功
    """
    try:
        from app.core.path_utils import resolve_resource_path
        db_path = resolve_resource_path(settings.database.path)
        if not db_path.exists():
            logger.error(f"数据库文件不存在: {db_path}")
            return False
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        logger.info("开始优化人脸识别数据库...")
        
        # 1. 添加索引
        indexes = [
            # FaceDetection表索引
            "CREATE INDEX IF NOT EXISTS idx_face_detection_photo_id ON face_detections(photo_id)",
            "CREATE INDEX IF NOT EXISTS idx_face_detection_face_id ON face_detections(face_id)",
            "CREATE INDEX IF NOT EXISTS idx_face_detection_confidence ON face_detections(confidence)",
            "CREATE INDEX IF NOT EXISTS idx_face_detection_created_at ON face_detections(created_at)",
            
            # FaceCluster表索引
            "CREATE INDEX IF NOT EXISTS idx_face_cluster_person_id ON face_clusters(person_id)",
            "CREATE INDEX IF NOT EXISTS idx_face_cluster_quality ON face_clusters(cluster_quality)",
            "CREATE INDEX IF NOT EXISTS idx_face_cluster_created_at ON face_clusters(created_at)",
            
            # FaceClusterMember表索引
            "CREATE INDEX IF NOT EXISTS idx_face_cluster_member_cluster_id ON face_cluster_members(cluster_id)",
            "CREATE INDEX IF NOT EXISTS idx_face_cluster_member_face_id ON face_cluster_members(face_id)",
            "CREATE INDEX IF NOT EXISTS idx_face_cluster_member_similarity ON face_cluster_members(similarity_score)",
            
            # Person表索引
            "CREATE INDEX IF NOT EXISTS idx_person_name ON persons(person_name)",
            "CREATE INDEX IF NOT EXISTS idx_person_created_at ON persons(created_at)",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                logger.info(f"创建索引: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                logger.warning(f"创建索引失败: {e}")
        
        # 2. 清理无效数据
        cleanup_queries = [
            # 清理没有对应照片的人脸检测记录
            "DELETE FROM face_detections WHERE photo_id NOT IN (SELECT id FROM photos)",
            
            # 清理没有代表人脸的人脸聚类
            "DELETE FROM face_clusters WHERE representative_face_id NOT IN (SELECT face_id FROM face_detections)",
            
            # 清理没有对应人脸检测的聚类成员
            "DELETE FROM face_cluster_members WHERE face_id NOT IN (SELECT face_id FROM face_detections)",
            
            # 清理没有对应聚类的聚类成员
            "DELETE FROM face_cluster_members WHERE cluster_id NOT IN (SELECT cluster_id FROM face_clusters)",
        ]
        
        for cleanup_sql in cleanup_queries:
            try:
                result = cursor.execute(cleanup_sql)
                deleted_count = result.rowcount
                if deleted_count > 0:
                    logger.info(f"清理了 {deleted_count} 条无效记录")
            except Exception as e:
                logger.warning(f"清理数据失败: {e}")
        
        # 3. 更新统计信息
        cursor.execute("ANALYZE")
        
        # 4. 提交更改
        conn.commit()
        
        logger.info("✅ 人脸识别数据库优化完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库优化失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    optimize_face_recognition_database()
