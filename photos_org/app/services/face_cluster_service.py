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

def _lazy_import_dependencies():
    """延迟导入重型库"""
    global np, DBSCAN
    
    if np is None:
        try:
            import numpy as np
            from sklearn.cluster import DBSCAN
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
        # 注意：不再在 __init__ 中固定配置值，改为动态读取
        # 初始化肖像轮换管理器
        self.rotation_manager = PortraitRotationManager()
    
    @property
    def config(self):
        """动态获取人脸识别配置（每次使用时读取最新配置）"""
        from app.core.config import get_settings
        return get_settings().face_recognition
    
    @property
    def max_clusters(self) -> int:
        """动态获取最大聚类数（每次使用时读取最新配置）"""
        return self.config.max_clusters
    
    @property
    def min_cluster_size(self) -> int:
        """动态获取最小聚类大小（每次使用时读取最新配置）"""
        return self.config.min_cluster_size
    
    @property
    def similarity_threshold(self) -> float:
        """动态获取相似度阈值（每次使用时读取最新配置）"""
        return self.config.similarity_threshold
    
    @property
    def cluster_quality_threshold(self) -> float:
        """动态获取聚类质量阈值（每次使用时读取最新配置）"""
        return self.config.cluster_quality_threshold
        
    async def cluster_faces(self, db: Session, task_id: Optional[str] = None) -> bool:
        """
        全量人脸聚类分析（支持标签保留）
        :param db: 数据库会话
        :param task_id: 任务ID（可选）
        :return: 是否聚类成功
        """
        # 延迟导入依赖
        _lazy_import_dependencies()
        
        try:
            logger.info("开始人脸聚类分析...")
            
            # 1. 备份旧聚类标签（如果有）
            old_clusters = db.query(FaceCluster).filter(
                FaceCluster.face_count > 0
            ).all()
            
            old_cluster_labels = {}
            old_representative_features = {}
            
            if old_clusters:
                logger.info(f"发现 {len(old_clusters)} 个旧聚类，将备份标签")
                for cluster in old_clusters:
                    if cluster.person_name:  # 只备份有标签的
                        old_cluster_labels[cluster.cluster_id] = cluster.person_name
                    if cluster.representative_face_id:
                        face = db.query(FaceDetection).filter_by(face_id=cluster.representative_face_id).first()
                        if face and face.face_features:
                            old_representative_features[cluster.cluster_id] = face.face_features
            
            # 2. 删除所有旧聚类
            logger.info("删除旧聚类数据...")
            db.query(FaceClusterMember).delete()
            db.query(FaceCluster).delete()
            db.commit()
            
            # 3. 全量重新聚类所有面容（排除 processed_ 标记记录）
            logger.info("开始全量聚类...")
            all_faces = db.query(FaceDetection).filter(
                FaceDetection.face_features.isnot(None),
                ~FaceDetection.face_id.like('processed_%')
            ).all()
            
            logger.info(f"待聚类人脸数量: {len(all_faces)}")
            
            # 直接调用全量聚类
            await self._create_new_clusters(all_faces, db)
            
            # 4. 标签恢复：匹配新聚类 → 旧聚类标签
            if old_cluster_labels and old_representative_features:
                logger.info("开始恢复用户标签...")
                restored_count = await self._restore_labels(old_cluster_labels, old_representative_features, db)
                logger.info(f"✅ 恢复了 {restored_count} 个标签")
            
            logger.info("人脸聚类完成")
            return True
            
        except Exception as e:
            logger.error(f"人脸聚类失败: {e}")
            db.rollback()
            return False
    
    async def _restore_labels(self, old_cluster_labels: Dict, old_representative_features: Dict, db) -> int:
        """
        恢复用户标签：通过代表人脸特征匹配新聚类和旧聚类
        :param old_cluster_labels: {cluster_id: person_name}
        :param old_representative_features: {cluster_id: face_features}
        :param db: 数据库会话
        :return: 恢复的标签数量
        """
        import numpy as np
        
        # 获取所有新聚类
        new_clusters = db.query(FaceCluster).all()
        
        if not new_clusters:
            return 0
        
        # 获取新聚类的代表人脸特征
        new_cluster_features = {}
        new_rep_face_ids = [c.representative_face_id for c in new_clusters if c.representative_face_id]
        
        if not new_rep_face_ids:
            return 0
        
        new_rep_faces = db.query(FaceDetection).filter(
            FaceDetection.face_id.in_(new_rep_face_ids)
        ).all()
        
        for cluster in new_clusters:
            for face in new_rep_faces:
                if face.face_id == cluster.representative_face_id and face.face_features:
                    new_cluster_features[cluster.cluster_id] = face.face_features
                    break
        
        restored_count = 0
        
        # 🔥 优化：只匹配有标签的旧聚类，反向遍历（从旧聚类找新聚类）
        labeled_old_clusters = {
            old_id: old_features 
            for old_id, old_features in old_representative_features.items()
            if old_id in old_cluster_labels
        }
        
        logger.info(f"开始匹配：{len(labeled_old_clusters)} 个有标签的旧聚类 → {len(new_cluster_features)} 个新聚类")
        
        # 🔥 反向遍历：从有标签的旧聚类出发，找最匹配的新聚类
        total_old = len(labeled_old_clusters)
        used_new_cluster_ids = set()  # 记录已被使用的新聚类ID
        
        for idx, (old_cluster_id, old_features) in enumerate(labeled_old_clusters.items()):
            person_name = old_cluster_labels[old_cluster_id]
            logger.info(f"标签恢复进度: {idx + 1}/{total_old} (正在匹配: {person_name})")
            
            best_new_cluster = None
            best_sim = 0.0
            threshold = 0.55
            
            # 遍历所有新聚类，找最匹配的
            for new_cluster_id, new_features in new_cluster_features.items():
                # 跳过已被使用的新聚类
                if new_cluster_id in used_new_cluster_ids:
                    continue
                
                sim = self.calculate_face_similarity(new_features, old_features)
                if sim > best_sim and sim >= threshold:
                    best_sim = sim
                    best_new_cluster = new_cluster_id
            
            # 找到匹配的新聚类，恢复标签
            if best_new_cluster:
                cluster = db.query(FaceCluster).filter_by(cluster_id=best_new_cluster).first()
                if cluster:
                    cluster.person_name = person_name
                    cluster.is_labeled = True
                    restored_count += 1
                    used_new_cluster_ids.add(best_new_cluster)
                    logger.info(f"恢复标签: {best_new_cluster} → {person_name} (相似度: {best_sim:.3f})")
        
        db.commit()
        return restored_count
    
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
        
        # 🔥 优化：两阶段处理
        # 第一阶段：创建所有聚类，先简单选择代表人脸（使用第一个）
        clusters_info = []  # [(cluster_id, cluster_faces, size)]
        
        for cluster_label in unique_labels:
            cluster_faces = [face_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_label]
            
            if len(cluster_faces) < 1:
                continue
            
            # 暂时使用第一个人脸作为代表人脸
            simple_representative = cluster_faces[0]
            cluster_id = f"cluster_{cluster_label}_{int(datetime.now().timestamp())}"
            
            cluster = FaceCluster(
                cluster_id=cluster_id,
                face_count=len(cluster_faces),
                representative_face_id=simple_representative,
                confidence_score=0.8,
                is_labeled=False,
                cluster_quality="high" if len(cluster_faces) >= 5 else "medium"
            )
            db.add(cluster)
            
            # 添加聚类成员
            for face_id in cluster_faces:
                member = FaceClusterMember(
                    cluster_id=cluster_id,
                    face_id=face_id,
                    similarity_score=0.8
                )
                db.add(member)
            
            clusters_info.append((cluster_id, cluster_faces, len(cluster_faces)))
        
        db.commit()
        
        # 第二阶段：只对需要显示的聚类进行详细的代表人脸选择
        # 筛选条件：face_count >= min_cluster_size，前 max_clusters 个
        if clusters_info:
            # 按大小排序，筛选符合 min_cluster_size 的聚类
            valid_clusters = [
                (cid, cf, size) for cid, cf, size in clusters_info 
                if size >= self.min_cluster_size
            ]
            valid_clusters.sort(key=lambda x: x[2], reverse=True)
            
            # 只处理前 max_clusters 个
            top_clusters = valid_clusters[:self.max_clusters]
            
            if top_clusters:
                # 🔥 性能优化：只加载需要显示的聚类对应的照片质量分数（延迟加载）
                logger.info(f"批量加载前 {len(top_clusters)} 个聚类的照片质量分数...")
                top_cluster_face_ids = []
                for _, cluster_faces, _ in top_clusters:
                    top_cluster_face_ids.extend(cluster_faces)
                
                # 获取这些聚类中所有人脸对应的照片ID
                top_photo_ids = []
                face_map = {f.face_id: f for f in faces}
                for face_id in top_cluster_face_ids:
                    if face_id in face_map:
                        photo_id = face_map[face_id].photo_id
                        if photo_id:
                            top_photo_ids.append(photo_id)
                
                photo_quality_cache = {}
                if top_photo_ids:
                    try:
                        from app.models.photo import PhotoQuality
                        
                        # 去重
                        unique_photo_ids = list(set(top_photo_ids))
                        
                        # 批量查询照片质量
                        qualities = db.query(PhotoQuality).filter(
                            PhotoQuality.photo_id.in_(unique_photo_ids)
                        ).all()
                        
                        for q in qualities:
                            if q.quality_score:
                                photo_quality_cache[q.photo_id] = min(q.quality_score / 100.0, 1.0)
                            else:
                                photo_quality_cache[q.photo_id] = 0.5
                        
                        logger.info(f"成功加载 {len(photo_quality_cache)} 个照片质量分数到缓存（仅前 {len(top_clusters)} 个聚类）")
                    except Exception as e:
                        logger.warning(f"批量加载照片质量失败: {e}")
                        photo_quality_cache = {}
                else:
                    photo_quality_cache = {}
                
                logger.info(f"对 {len(top_clusters)} 个需要显示的聚类进行详细代表人脸选择（符合 min_cluster_size={self.min_cluster_size}，前 max_clusters={self.max_clusters} 个）...")
                
                for idx, (cluster_id, cluster_faces, _) in enumerate(top_clusters):
                    if idx % 100 == 0:
                        logger.info(f"代表人脸选择进度: {idx + 1}/{len(top_clusters)}")
                    
                    # 🔥 优化：首次聚类时不使用轮换逻辑（cluster_id=None），只选择1个最佳代表人脸
                    # 轮换功能仅在用户点击"优化肖像"按钮时使用（reselect_cluster_representative）
                    best_representative = self._select_best_representative_face(
                        cluster_faces, faces, db, 
                        cluster_id=None,  # 首次选择不使用轮换逻辑
                        photo_quality_cache=photo_quality_cache
                    )
                    
                    # 更新代表人脸
                    cluster = db.query(FaceCluster).filter_by(cluster_id=cluster_id).first()
                    if cluster:
                        cluster.representative_face_id = best_representative
                        db.add(cluster)
                
                db.commit()
                logger.info(f"完成了 {len(top_clusters)} 个聚类的详细代表人脸选择")
        
        return len(clusters_info)
    
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
    
    def _select_best_representative_face(self, cluster_face_ids: List[str], faces: List, db: Session, cluster_id: str = None, photo_quality_cache: Dict[int, float] = None) -> str:
        """
        选择最佳代表人脸
        
        :param cluster_face_ids: 聚类中的人脸ID列表
        :param faces: 人脸数据
        :param db: 数据库会话
        :param cluster_id: 聚类ID
            - None: 首次聚类时，只选择1个最佳代表人脸（不使用轮换）
            - 不为None: 优化肖像按钮点击时，使用轮换逻辑从前10个优质人脸中选择
        :param photo_quality_cache: 照片质量分数缓存 {photo_id: quality_score}
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
                photo_quality_score = self._get_photo_quality_score(photo_id, db, photo_quality_cache)
                
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
    
    def _get_photo_quality_score(self, photo_id: int, db: Session, photo_quality_cache: Dict[int, float] = None) -> float:
        """
        获取照片质量分数（优先使用缓存）
        :param photo_id: 照片ID
        :param db: 数据库会话
        :param photo_quality_cache: 照片质量分数缓存 {photo_id: quality_score}
        :return: 质量分数 (0-1)
        """
        # 🔥 性能优化：优先使用缓存
        if photo_quality_cache is not None:
            if photo_id in photo_quality_cache:
                return photo_quality_cache[photo_id]
            else:
                # 缓存中没有，返回默认值（不再查询数据库）
                return 0.5
        
        # 如果没有提供缓存，才查询数据库（向后兼容）
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
