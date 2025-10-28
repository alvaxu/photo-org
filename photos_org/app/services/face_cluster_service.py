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
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import uuid

# 延迟导入重型库
np = None
DBSCAN = None
cosine_distances = None
plt = None
tqdm = None

def _lazy_import_dependencies():
    """延迟导入重型库"""
    global np, DBSCAN, cosine_distances, plt, tqdm
    
    if np is None:
        try:
            import numpy as np
            from sklearn.cluster import DBSCAN
            from sklearn.metrics.pairwise import cosine_distances
            import matplotlib.pyplot as plt
            from tqdm import tqdm
            logging.info("成功加载人脸聚类依赖库")
        except ImportError as e:
            logging.error(f"聚类依赖导入失败: {e}")

from app.core.config import settings
from app.db.session import get_db
from app.models.face import FaceDetection, FaceCluster, FaceClusterMember, Person
from app.models.photo import Photo
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)


class PortraitRotationManager:
    """
    肖像轮换管理器
    
    管理每个聚类的代表人脸轮换状态，支持在前10个优质人脸间轮换
    """
    
    def __init__(self):
        # 轮换状态: {cluster_id: {'faces': [...], 'index': 0}}
        self.rotation_state: Dict[str, Dict] = {}
    
    def get_next_representative(self, cluster_id: str, top_10_faces: List[Tuple[str, float]]) -> str:
        """
        获取下一个代表人脸
        
        :param cluster_id: 聚类ID
        :param top_10_faces: 前10个优质人脸 [(face_id, score), ...]
        :return: 选择的人脸ID
        """
        if not top_10_faces:
            return ""
        
        # 提取人脸ID列表
        face_ids = [face_id for face_id, _ in top_10_faces]
        
        if cluster_id not in self.rotation_state:
            # 第一次，初始化状态
            self.rotation_state[cluster_id] = {
                'faces': face_ids,
                'index': 0
            }
            logger.info(f"初始化聚类 {cluster_id} 的轮换状态，共 {len(face_ids)} 个优质人脸")
        
        state = self.rotation_state[cluster_id]
        
        # 如果人脸列表发生变化，重新初始化
        if state['faces'] != face_ids:
            state['faces'] = face_ids
            state['index'] = 0
            logger.info(f"聚类 {cluster_id} 的人脸列表已更新，重新开始轮换")
        
        # 选择当前索引的人脸
        current_index = state['index']
        selected_face_id = state['faces'][current_index]
        
        # 更新索引（循环）
        state['index'] = (current_index + 1) % len(state['faces'])
        
        logger.info(f"聚类 {cluster_id} 选择代表人脸: {selected_face_id} (第 {current_index + 1}/{len(state['faces'])} 个)")
        
        return selected_face_id
    
    def reset_cluster_rotation(self, cluster_id: str):
        """
        重置指定聚类的轮换状态
        
        :param cluster_id: 聚类ID
        """
        if cluster_id in self.rotation_state:
            self.rotation_state[cluster_id]['index'] = 0
            logger.info(f"重置聚类 {cluster_id} 的轮换状态")
    
    def get_rotation_info(self, cluster_id: str) -> Optional[Dict]:
        """
        获取聚类的轮换信息
        
        :param cluster_id: 聚类ID
        :return: 轮换信息字典
        """
        if cluster_id not in self.rotation_state:
            return None
        
        state = self.rotation_state[cluster_id]
        return {
            'total_faces': len(state['faces']),
            'current_index': state['index'],
            'current_face': state['faces'][state['index']] if state['faces'] else None
        }


class FaceClusterService:
    """人脸聚类服务类"""
    
    def __init__(self):
        """初始化人脸聚类服务"""
        self.config = settings.face_recognition
        self.max_clusters = self.config.max_clusters
        self.min_cluster_size = self.config.min_cluster_size
        self.similarity_threshold = self.config.similarity_threshold
        self.cluster_quality_threshold = self.config.cluster_quality_threshold
        
        # 初始化肖像轮换管理器
        self.rotation_manager = PortraitRotationManager()
        
    async def cluster_faces(self, db: Session, task_id: Optional[str] = None) -> bool:
        """
        增量人脸聚类分析
        :param db: 数据库会话
        :param task_id: 任务ID，用于识别新人脸（可选）
        :return: 是否聚类成功
        """
        # 延迟导入依赖
        _lazy_import_dependencies()
        
        try:
            logger.info("开始增量人脸聚类分析...")
            
            # 🔥 策略：保留旧聚类，只处理新人脸
            # 1. 获取所有已聚类的旧聚类（保留用户数据）
            old_clusters = db.query(FaceCluster).filter(
                FaceCluster.face_count > 0
            ).all()
            
            if old_clusters:
                logger.info(f"发现 {len(old_clusters)} 个旧聚类，将保留用户命名和肖像选择")
            else:
                logger.info("首次聚类，将创建所有新聚类")
            
            # 🔥 增量聚类策略
            if old_clusters:
                # 2. 识别未被聚类的新人脸
                clustered_face_ids = set()
                for cluster in old_clusters:
                    members = db.query(FaceClusterMember).filter_by(cluster_id=cluster.cluster_id).all()
                    clustered_face_ids.update([m.face_id for m in members])
                
                # 获取所有未聚类的人脸
                all_faces = db.query(FaceDetection).filter(
                    FaceDetection.face_features.isnot(None)
                ).all()
                
                unclustered_faces = [f for f in all_faces if f.face_id not in clustered_face_ids]
                
                if not unclustered_faces:
                    logger.info("没有新的人脸需要聚类")
                    return True
                
                logger.info(f"发现 {len(unclustered_faces)} 个未被聚类的新人脸")
                
                # 3. 尝试将新人脸匹配到旧聚类
                matched_count = 0
                for face in unclustered_faces:
                    best_cluster = self._match_to_existing_cluster(face, old_clusters, db)
                    if best_cluster:
                        # 添加到旧聚类
                        member = FaceClusterMember(
                            cluster_id=best_cluster.cluster_id,
                            face_id=face.face_id,
                            similarity_score=0.8
                        )
                        db.add(member)
                        # 更新聚类计数
                        best_cluster.face_count += 1
                        matched_count += 1
                
                if matched_count > 0:
                    logger.info(f"✅ 匹配了 {matched_count} 个人脸到旧聚类")
                    db.commit()
                
                # 4. 对无法匹配的人脸进行聚类
                unmatched_faces = [f for f in unclustered_faces if f.face_id not in {
                    m.face_id for m in db.query(FaceClusterMember).all()
                }]
                
                if unmatched_faces:
                    logger.info(f"对 {len(unmatched_faces)} 个无法匹配的人脸进行新聚类")
                    new_clusters = await self._create_new_clusters(unmatched_faces, db)
                    logger.info(f"✅ 创建了 {new_clusters} 个新聚类")
                    
            else:
                # 首次聚类：全量聚类所有面容
                logger.info("首次聚类，对所有面容进行聚类")
                await self._create_new_clusters(
                    db.query(FaceDetection).filter(FaceDetection.face_features.isnot(None)).all(),
                    db
                )
            
            return True
            
        except Exception as e:
            logger.error(f"人脸聚类失败: {e}")
            db.rollback()
            return False
    
    def _match_to_existing_cluster(self, face, old_clusters: List, db) -> Optional[object]:
        """
        尝试将新人脸匹配到旧聚类
        :param face: 新人脸对象
        :param old_clusters: 旧聚类列表
        :param db: 数据库会话
        :return: 匹配成功的聚类，或None
        """
        if not face.face_features:
            return None
        
        import numpy as np
        
        best_cluster = None
        best_similarity = 0.0
        match_threshold = self.similarity_threshold
        
        for cluster in old_clusters:
            # 获取聚类中所有人脸的特征
            members = db.query(FaceClusterMember).filter_by(
                cluster_id=cluster.cluster_id
            ).limit(10).all()  # 只取前10个成员计算平均相似度（性能优化）
            
            if not members:
                continue
            
            # 获取成员的人脸特征
            cluster_face_ids = [m.face_id for m in members]
            cluster_faces = db.query(FaceDetection).filter(
                FaceDetection.face_id.in_(cluster_face_ids)
            ).all()
            
            # 计算与聚类中所有人脸的平均相似度
            similarities = []
            for cluster_face in cluster_faces:
                if cluster_face.face_features:
                    sim = self.calculate_face_similarity(face.face_features, cluster_face.face_features)
                    similarities.append(sim)
            
            if similarities:
                avg_similarity = np.mean(similarities)
                if avg_similarity > best_similarity and avg_similarity >= match_threshold:
                    best_similarity = avg_similarity
                    best_cluster = cluster
        
        if best_cluster:
            logger.debug(f"匹配人脸 {face.face_id} 到聚类 {best_cluster.cluster_id} (相似度: {best_similarity:.3f})")
        
        return best_cluster
    
    async def _create_new_clusters(self, faces: List, db) -> int:
        """
        创建新聚类（使用DBSCAN）
        :param faces: 人脸列表
        :param db: 数据库会话
        :return: 创建的聚类数量
        """
        import numpy as np
        
        # 🔥 修改：不限制最小人脸数，允许单人照聚类
        if len(faces) < 1:
            logger.info(f"人脸数量不足，跳过聚类")
            return 0
        
        # 提取特征向量
        features = []
        face_ids = []
        for face in faces:
            if face.face_features:
                features.append(face.face_features)
                face_ids.append(face.face_id)
        
        if len(features) < 1:
            logger.info("有效人脸特征不足，跳过聚类")
            return 0
        
        features = np.array(features)
        
        # 使用DBSCAN进行聚类
        # 🔥 修改：min_samples=1，允许单人照聚类
        clustering = DBSCAN(
            eps=1 - self.similarity_threshold,
            min_samples=1,  # 允许单人照
            metric='cosine'
        )
        cluster_labels = clustering.fit_predict(features)
        
        # 处理聚类结果
        unique_labels = set(cluster_labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)  # 移除噪声点
        
        logger.info(f"检测到 {len(unique_labels)} 个新聚类")
        
        # 保存聚类结果
        created_count = 0
        for cluster_label in unique_labels:
            cluster_faces = [face_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_label]
            
            # 🔥 修改：不限制聚类大小，保存所有聚类（包括单人照）
            # 显示时将根据 min_cluster_size 进行过滤
            if len(cluster_faces) < 1:
                continue  # 至少要有1张照片（真正的人脸）
            
            # 创建聚类
            cluster_id = f"cluster_{cluster_label}_{int(datetime.now().timestamp())}"
            
            # 选择最佳代表人脸
            best_representative = self._select_best_representative_face(cluster_faces, faces, db)
            
            cluster = FaceCluster(
                cluster_id=cluster_id,
                face_count=len(cluster_faces),
                representative_face_id=best_representative,
                confidence_score=0.8,
                is_labeled=False,
                cluster_quality="high" if len(cluster_faces) >= 5 else "medium"
            )
            db.add(cluster)
            db.flush()
            
            # 添加聚类成员
            for face_id in cluster_faces:
                member = FaceClusterMember(
                    cluster_id=cluster_id,
                    face_id=face_id,
                    similarity_score=0.8
                )
                db.add(member)
            
            created_count += 1
        
        db.commit()
        return created_count
    
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
    
    def _select_best_representative_face(self, cluster_face_ids: List[str], faces: List, db: Session, cluster_id: str = None) -> str:
        """
        选择最佳代表人脸（支持轮换）
        :param cluster_face_ids: 聚类中的人脸ID列表
        :param faces: 人脸数据
        :param db: 数据库会话
        :param cluster_id: 聚类ID（用于轮换）
        :return: 最佳代表人脸ID
        """
        try:
            if not cluster_face_ids:
                return ""
            
            # 获取聚类中的人脸数据（FaceDetection对象）
            cluster_faces = [f for f in faces if f.face_id in cluster_face_ids]
            
            if not cluster_faces:
                return cluster_face_ids[0]  # 回退到第一个
            
            # 计算每个人脸的综合质量分数
            face_scores = []
            
            for face_obj in cluster_faces:
                face_id = face_obj.face_id
                photo_id = face_obj.photo_id
                
                # 1. 人脸检测置信度 (权重: 0.3)
                confidence_score = face_obj.confidence or 0.0
                
                # 2. 照片质量分数 (权重: 0.4)
                photo_quality_score = self._get_photo_quality_score(photo_id, db)
                
                # 3. 人脸大小分数 (权重: 0.2)
                face_size_score = self._calculate_face_size_score(face_obj)
                
                # 4. 人脸角度分数 (权重: 0.1)
                face_angle_score = self._calculate_face_angle_score(face_obj)
                
                # 综合分数计算
                total_score = (
                    confidence_score * 0.3 +
                    photo_quality_score * 0.4 +
                    face_size_score * 0.2 +
                    face_angle_score * 0.1
                )
                
                face_scores.append((face_id, total_score, confidence_score, photo_quality_score))
            
            # 按综合分数排序
            face_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 🔥 轮换逻辑：如果提供了cluster_id，使用轮换管理器
            if cluster_id:
                # 取前10个优质人脸进行轮换，转换为轮换管理器期望的格式
                top_10_faces = [(face_id, total_score) for face_id, total_score, _, _ in face_scores[:10]]
                best_face_id = self.rotation_manager.get_next_representative(cluster_id, top_10_faces)
                
                # 找到选中人脸的详细信息用于日志
                selected_info = next((info for info in face_scores if info[0] == best_face_id), None)
                if selected_info:
                    logger.info(f"轮换选择代表人脸: {best_face_id}, 分数: {selected_info[1]:.3f} "
                               f"(置信度: {selected_info[2]:.3f}, 照片质量: {selected_info[3]:.3f})")
                
                return best_face_id
            else:
                # 传统逻辑：选择分数最高的
                best_face_id = face_scores[0][0]
                logger.info(f"选择代表人脸: {best_face_id}, 分数: {face_scores[0][1]:.3f} "
                           f"(置信度: {face_scores[0][2]:.3f}, 照片质量: {face_scores[0][3]:.3f})")
                return best_face_id
            
        except Exception as e:
            logger.error(f"选择代表人脸失败: {e}")
            return cluster_face_ids[0]  # 回退到第一个
    
    def _get_photo_quality_score(self, photo_id: int, db: Session) -> float:
        """
        获取照片质量分数
        :param photo_id: 照片ID
        :param db: 数据库会话
        :return: 质量分数 (0-1)
        """
        try:
            from app.models.photo import PhotoQuality
            
            quality = db.query(PhotoQuality).filter(
                PhotoQuality.photo_id == photo_id
            ).first()
            
            if quality and quality.quality_score:
                # 将质量分数标准化到0-1范围
                return min(quality.quality_score / 100.0, 1.0)
            else:
                return 0.5  # 默认中等质量
                
        except Exception as e:
            logger.warning(f"获取照片质量分数失败: {e}")
            return 0.5
    
    def _calculate_face_size_score(self, face_obj) -> float:
        """
        计算人脸大小分数
        :param face_obj: FaceDetection对象
        :return: 大小分数 (0-1)
        """
        try:
            face_rectangle = face_obj.face_rectangle
            if not face_rectangle or len(face_rectangle) != 4:
                return 0.5
            
            # 计算人脸区域面积
            width = face_rectangle[2] - face_rectangle[0]
            height = face_rectangle[3] - face_rectangle[1]
            area = width * height
            
            # 人脸面积越大分数越高，但不要太小也不要太大
            # 理想人脸面积范围：1000-10000像素
            if area < 500:
                return 0.2
            elif area < 1000:
                return 0.4
            elif area < 5000:
                return 0.8
            elif area < 10000:
                return 1.0
            else:
                return 0.6  # 太大的人脸可能失真
                
        except Exception as e:
            logger.warning(f"计算人脸大小分数失败: {e}")
            return 0.5
    
    def _calculate_face_angle_score(self, face_obj) -> float:
        """
        计算人脸角度分数
        :param face_obj: FaceDetection对象
        :return: 角度分数 (0-1)
        """
        try:
            # 这里可以根据人脸关键点计算角度
            # 目前简化处理，返回默认分数
            # 未来可以基于landmark计算人脸偏转角度
            
            confidence = face_obj.confidence or 0.0
            # 置信度越高，通常角度越好
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.warning(f"计算人脸角度分数失败: {e}")
            return 0.5

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
            # 从配置获取最小聚类大小
            min_cluster_size = self.min_cluster_size
            
            # 排除处理标记记录（face_id以"processed_"开头的记录）
            total_faces = db.query(func.count(FaceDetection.id)).filter(
                ~FaceDetection.face_id.like('processed_%')
            ).scalar() or 0
            
            # 🔥 只统计符合min_cluster_size条件的聚类
            total_clusters = db.query(func.count(FaceCluster.id)).filter(
                FaceCluster.face_count >= min_cluster_size
            ).scalar() or 0
            
            # 只统计符合条件且已标记的聚类
            labeled_clusters = db.query(func.count(FaceCluster.id)).filter(
                FaceCluster.is_labeled == True,
                FaceCluster.face_count >= min_cluster_size
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
