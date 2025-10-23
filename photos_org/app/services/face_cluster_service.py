"""
人脸聚类服务模块

## 功能特点：
1. 基于DBSCAN算法的人脸聚类
2. 支持Top N聚类限制
3. 聚类质量评估
4. 可配置的聚类参数
5. 与现有分析流程集成

## 与其他版本的不同点：
- 参考基础分析的批处理架构
- 支持Top N聚类限制
- 集成到现有分析流程
"""

import asyncio
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import uuid

try:
    from sklearn.cluster import DBSCAN
    from sklearn.metrics.pairwise import cosine_distances
    import matplotlib.pyplot as plt
    from tqdm import tqdm
except ImportError as e:
    logging.error(f"聚类依赖导入失败: {e}")
    DBSCAN = None

from app.core.config import settings
from app.db.session import get_db
from app.models.face import FaceDetection, FaceCluster, FaceClusterMember, Person
from app.models.photo import Photo
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

class FaceClusterService:
    """人脸聚类服务类"""
    
    def __init__(self):
        """初始化人脸聚类服务"""
        self.config = settings.face_recognition
        self.max_clusters = self.config.max_clusters
        self.min_cluster_size = self.config.min_cluster_size
        self.similarity_threshold = self.config.similarity_threshold
        self.cluster_quality_threshold = self.config.cluster_quality_threshold
        
    async def cluster_faces(self, db: Session) -> bool:
        """
        对人脸进行聚类分析
        :param db: 数据库会话
        :return: 是否聚类成功
        """
        try:
            logger.info("开始人脸聚类分析...")
            
            # 清理旧的聚类数据
            logger.info("清理旧的聚类数据...")
            db.query(FaceClusterMember).delete()
            db.query(FaceCluster).delete()
            db.commit()
            logger.info("✅ 旧聚类数据清理完成")
            
            # 获取所有人脸特征
            faces = db.query(FaceDetection).filter(
                FaceDetection.face_features.isnot(None)
            ).all()
            
            if len(faces) < self.min_cluster_size:
                logger.info("人脸数量不足，跳过聚类")
                return True
                
            # 提取特征向量
            features = []
            face_ids = []
            for face in faces:
                if face.face_features:
                    features.append(face.face_features)
                    face_ids.append(face.face_id)
            
            if len(features) < self.min_cluster_size:
                logger.info("有效人脸特征不足，跳过聚类")
                return True
                
            features = np.array(features)
            
            # 使用DBSCAN进行聚类
            clustering = DBSCAN(
                eps=1 - self.similarity_threshold,
                min_samples=self.min_cluster_size,
                metric='cosine'
            )
            cluster_labels = clustering.fit_predict(features)
            
            # 处理聚类结果
            unique_labels = set(cluster_labels)
            if -1 in unique_labels:
                unique_labels.remove(-1)  # 移除噪声点
                
            logger.info(f"检测到 {len(unique_labels)} 个聚类")
            
            # 限制聚类数量（Top N）
            if len(unique_labels) > self.max_clusters:
                # 按聚类大小排序，保留最大的N个
                cluster_sizes = {}
                for label in unique_labels:
                    cluster_sizes[label] = np.sum(cluster_labels == label)
                
                # 按大小排序，保留Top N
                sorted_clusters = sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True)
                top_clusters = [label for label, _ in sorted_clusters[:self.max_clusters]]
                
                logger.info(f"限制聚类数量为Top {self.max_clusters}，保留 {len(top_clusters)} 个聚类")
                unique_labels = set(top_clusters)
            
            # 保存聚类结果
            for cluster_label in unique_labels:
                cluster_faces = [face_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_label]
                
                if len(cluster_faces) < self.min_cluster_size:
                    continue
                    
                # 创建聚类
                cluster_id = f"cluster_{cluster_label}_{int(datetime.now().timestamp())}"
                cluster = FaceCluster(
                    cluster_id=cluster_id,
                    face_count=len(cluster_faces),
                    representative_face_id=cluster_faces[0],  # 使用第一个作为代表
                    confidence_score=0.8,  # 默认置信度
                    is_labeled=False,
                    cluster_quality="high" if len(cluster_faces) >= 5 else "medium"
                )
                db.add(cluster)
                db.flush()  # 获取cluster ID
                
                # 添加聚类成员
                for face_id in cluster_faces:
                    member = FaceClusterMember(
                        cluster_id=cluster_id,
                        face_id=face_id,
                        similarity_score=0.8  # 默认相似度
                    )
                    db.add(member)
            
            db.commit()
            logger.info(f"✅ 人脸聚类完成，创建了 {len(unique_labels)} 个聚类")
            return True
            
        except Exception as e:
            logger.error(f"人脸聚类失败: {e}")
            db.rollback()
            return False
    
    def calculate_face_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        计算人脸相似度
        :param embedding1: 第一个人脸特征向量
        :param embedding2: 第二个人脸特征向量
        :return: 相似度分数
        """
        try:
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)
            
            # 计算余弦相似度
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            return 0.0
    
    def _limit_clusters(self, clusters: Dict[str, List[str]], faces: List[Dict]) -> Dict[str, List[str]]:
        """
        限制聚类数量，保留质量最高的聚类
        :param clusters: 聚类结果
        :param faces: 人脸数据
        :return: 限制后的聚类结果
        """
        # 按聚类大小和质量排序
        cluster_scores = []
        
        for cluster_id, face_ids in clusters.items():
            # 计算聚类质量分数
            quality_score = self._calculate_cluster_quality(cluster_id, face_ids, faces)
            cluster_scores.append((cluster_id, len(face_ids), quality_score))
        
        # 按质量分数排序
        cluster_scores.sort(key=lambda x: (x[2], x[1]), reverse=True)
        
        # 保留前N个聚类
        limited_clusters = {}
        for i in range(min(self.max_clusters, len(cluster_scores))):
            cluster_id = cluster_scores[i][0]
            limited_clusters[cluster_id] = clusters[cluster_id]
        
        return limited_clusters
    
    def _calculate_cluster_quality(self, cluster_id: str, face_ids: List[str], faces: List[Dict]) -> float:
        """
        计算聚类质量分数
        :param cluster_id: 聚类ID
        :param face_ids: 人脸ID列表
        :param faces: 人脸数据
        :return: 质量分数
        """
        try:
            # 获取聚类中的人脸特征
            cluster_faces = [f for f in faces if f['face_id'] in face_ids]
            
            if len(cluster_faces) < 2:
                return 0.0
            
            # 计算聚类内相似度的平均值
            similarities = []
            for i in range(len(cluster_faces)):
                for j in range(i + 1, len(cluster_faces)):
                    sim = self.calculate_face_similarity(
                        cluster_faces[i]['face_features'],
                        cluster_faces[j]['face_features']
                    )
                    similarities.append(sim)
            
            if similarities:
                avg_similarity = np.mean(similarities)
                return avg_similarity
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"计算聚类质量失败: {e}")
            return 0.0
    
    async def get_cluster_statistics(self, db: Session) -> Dict:
        """
        获取聚类统计信息
        :param db: 数据库会话
        :return: 统计信息
        """
        try:
            total_faces = db.query(func.count(FaceDetection.id)).scalar() or 0
            total_clusters = db.query(func.count(FaceCluster.id)).scalar() or 0
            labeled_clusters = db.query(func.count(FaceCluster.id)).filter(
                FaceCluster.is_labeled == True
            ).scalar() or 0
            
            return {
                'total_faces': total_faces,
                'total_clusters': total_clusters,
                'labeled_clusters': labeled_clusters,
                'unlabeled_clusters': total_clusters - labeled_clusters
            }
            
        except Exception as e:
            logger.error(f"获取聚类统计失败: {e}")
            return {}

# 全局服务实例
cluster_service = FaceClusterService()
