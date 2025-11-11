"""
相似照片聚类服务模块

## 功能特点：
1. 基于DBSCAN算法的相似照片聚类
2. 使用ResNet50特征向量进行聚类
3. 支持可配置的聚类参数
4. 与现有分析流程集成

## 与其他版本的不同点：
- 参考人脸聚类服务的架构设计
- 使用特征向量（image_features）进行聚类
- 不需要代表人脸选择逻辑
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json
import uuid  # 🔥 添加UUID用于生成唯一ID

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
            logging.info("成功加载相似照片聚类依赖库")
        except ImportError as e:
            logging.error(f"聚类依赖导入失败: {e}")

from app.core.config import settings
from app.db.session import get_db
from app.models.photo import Photo, DuplicateGroup, DuplicateGroupPhoto
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

# 全局聚类任务状态跟踪
cluster_task_status = {}

class SimilarPhotoClusterService:
    """相似照片聚类服务类"""
    
    def __init__(self):
        """初始化相似照片聚类服务"""
        pass
    
    @property
    def similarity_threshold(self) -> float:
        """
        动态获取相似度阈值（从config.json读取）
        
        注意：对于特征向量聚类，应该使用更严格的阈值（类似人脸聚类）
        人脸聚类使用0.7，这里也使用0.7，确保只有真正相似的照片才会被分到同一聚类
        """
        # 优先使用image_features配置中的阈值，如果没有则使用0.7（参考人脸聚类）
        if hasattr(settings, 'image_features') and hasattr(settings.image_features, 'similarity_threshold'):
            return settings.image_features.similarity_threshold
        # 如果没有配置，使用0.7（更严格的阈值，类似人脸聚类）
        return 0.7
    
    @property
    def large_cluster_threshold(self) -> int:
        """
        大聚类阈值：超过此数量的聚类将被二次细分
        """
        return 50  # 默认50张照片
    
    @property
    def refined_similarity_threshold(self) -> float:
        """
        二次细分的相似度阈值（更严格）
        
        计算方式：将余弦距离阈值减半
        - 原始相似度阈值对应的余弦距离 = 1 - similarity_threshold
        - 细化后的余弦距离 = (1 - similarity_threshold) / 2
        - 细化后的相似度阈值 = 1 - (1 - similarity_threshold) / 2
        
        例如：原始阈值0.78 → 距离0.22 → 细化距离0.11 → 细化阈值0.89
        """
        # 计算原始余弦距离
        original_distance = 1 - self.similarity_threshold
        # 将距离减半
        refined_distance = original_distance / 2
        # 转换回相似度阈值
        refined_threshold = 1 - refined_distance
        # 限制最大值，避免阈值过高导致无法聚类
        return min(0.95, refined_threshold)
    
    async def process_cluster_task(self, task_id: str) -> bool:
        """
        处理聚类任务（参考人脸识别任务的process_face_recognition_task）
        在后台任务内部创建数据库会话，避免阻塞事件循环
        
        :param task_id: 任务ID
        :return: 是否聚类成功
        """
        # 🔥 在后台任务内部创建新的数据库会话（参考人脸识别任务）
        db = next(get_db())
        
        try:
            # 调用实际的聚类方法
            result = await self.cluster_similar_photos(db, task_id)
            return result
        except Exception as e:
            # 🔥 捕获所有异常，防止进程退出
            logger.error(f"聚类任务执行失败: {str(e)}", exc_info=True)
            import traceback
            traceback.print_exc()
            if task_id:
                cluster_task_status[task_id] = {
                    "status": "failed",
                    "message": f"聚类任务执行失败: {str(e)}",
                    "end_time": datetime.now().isoformat()
                }
            return False
        finally:
            # 确保关闭数据库会话
            try:
                db.close()
            except Exception as e:
                logger.error(f"关闭数据库会话失败: {str(e)}")
    
    async def cluster_similar_photos(self, db: Session, task_id: Optional[str] = None) -> bool:
        """
        全量相似照片聚类分析
        
        :param db: 数据库会话
        :param task_id: 任务ID（可选）
        :return: 是否聚类成功
        """
        _lazy_import_dependencies()
        
        if np is None or DBSCAN is None:
            logger.error("聚类依赖库未加载，无法进行聚类")
            if task_id:
                cluster_task_status[task_id] = {
                    "status": "failed",
                    "message": "聚类依赖库未加载"
                }
            return False
        
        # 如果没有提供task_id，生成一个
        if not task_id:
            task_id = f"cluster_{int(datetime.now().timestamp())}"
        
        try:
            # 初始化任务状态
            cluster_task_status[task_id] = {
                "status": "processing",
                "message": "聚类分析进行中",
                "start_time": datetime.now().isoformat(),
                "current_stage": "initial_clustering",
                "progress_percentage": 0.0,
                "cluster_count": 0,
                "refined_count": 0,
                "total_photos": 0
            }
            
            logger.info(f"开始相似照片聚类分析（任务ID: {task_id}）...")
            
            # 1. 删除所有旧聚类（只删除有cluster_id的聚类，保留旧数据）
            logger.info("清理旧聚类数据...")
            self._update_task_status(task_id, {
                "message": "清理旧聚类数据...",
                "progress_percentage": 5.0
            })
            
            # 🔥 使用 asyncio.to_thread() 包装同步数据库操作（参考人脸识别任务）
            def cleanup_old_clusters():
                db.query(DuplicateGroupPhoto).filter(
                    DuplicateGroupPhoto.cluster_id.isnot(None)
                ).delete()
                db.query(DuplicateGroup).filter(
                    DuplicateGroup.cluster_id.isnot(None)
                ).delete()
                db.commit()
            
            await asyncio.to_thread(cleanup_old_clusters)
            
            # 2. 获取所有已提取特征的照片（按ID排序，确保顺序固定）
            def query_photos():
                return db.query(Photo).filter(
                    Photo.image_features_extracted == True,
                    Photo.image_features.isnot(None),
                    Photo.image_features != ''
                ).order_by(Photo.id).all()
            
            photos = await asyncio.to_thread(query_photos)
            
            logger.info(f"待聚类照片数量: {len(photos)}")
            self._update_task_status(task_id, {
                "message": f"准备聚类 {len(photos)} 张照片...",
                "progress_percentage": 10.0,
                "total_photos": len(photos)
            })
            
            if len(photos) < 2:
                logger.info("照片数量不足，跳过聚类")
                cluster_task_status[task_id] = {
                    "status": "completed",
                    "message": "照片数量不足，跳过聚类",
                    "progress_percentage": 100.0,
                    "end_time": datetime.now().isoformat()
                }
                return True
            
            # 🔥 检查照片数量，如果太多则警告
            if len(photos) > 20000:
                logger.warning(f"照片数量较多 ({len(photos)} 张)，聚类可能需要较长时间和大量内存")
                self._update_task_status(task_id, {
                    "message": f"照片数量较多 ({len(photos)} 张)，正在准备聚类（可能需要较长时间）...",
                    "progress_percentage": 10.0
                })
            
            # 3. 创建新聚类
            cluster_count = await self._create_new_clusters(photos, db, task_id)
            
            # 更新进度：初始聚类完成
            self._update_task_status(task_id, {
                "message": f"初始聚类完成，创建了 {cluster_count} 个聚类，开始细分大聚类...",
                "progress_percentage": 70.0,
                "cluster_count": cluster_count
            })
            
            # 4. 对大聚类进行二次细分
            refined_count = 0
            if cluster_count > 0:
                refined_count = await self._refine_large_clusters(db, task_id)
                if refined_count > 0:
                    logger.info(f"✅ 成功细分 {refined_count} 个大聚类")
            
            # 更新任务状态为完成
            cluster_task_status[task_id] = {
                "status": "completed",
                "message": f"聚类完成，共创建 {cluster_count} 个聚类，细分 {refined_count} 个大聚类",
                "cluster_count": cluster_count,
                "refined_count": refined_count,
                "progress_percentage": 100.0,
                "end_time": datetime.now().isoformat()
            }
            
            logger.info("相似照片聚类完成")
            return True
            
        except Exception as e:
            logger.error(f"相似照片聚类失败: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            db.rollback()
            if task_id:
                cluster_task_status[task_id] = {
                    "status": "failed",
                    "message": f"聚类失败: {str(e)}",
                    "end_time": datetime.now().isoformat()
                }
            return False
    
    def _update_task_status(self, task_id: str, updates: dict):
        """
        更新任务状态
        
        :param task_id: 任务ID
        :param updates: 要更新的字段字典
        """
        if task_id and task_id in cluster_task_status:
            cluster_task_status[task_id].update(updates)
    
    async def _create_new_clusters(self, photos: List[Photo], db: Session, task_id: Optional[str] = None) -> int:
        """
        创建新聚类（使用DBSCAN）
        
        :param photos: 照片列表
        :param db: 数据库会话
        :return: 创建的聚类数量
        """
        # 确保依赖库已加载
        _lazy_import_dependencies()
        
        if np is None or DBSCAN is None:
            logger.error("聚类依赖库未加载，无法创建聚类")
            return 0
        
        if len(photos) < 1:
            logger.info("照片数量不足，跳过聚类")
            return 0
        
        # 🔥 使用 asyncio.to_thread() 包装特征向量提取（避免阻塞）
        def extract_features():
            features = []
            photo_ids = []
            for photo in photos:
                if photo.image_features:
                    try:
                        # 解析JSON格式的特征向量
                        if isinstance(photo.image_features, str):
                            feature_vector = json.loads(photo.image_features)
                        else:
                            feature_vector = photo.image_features
                        
                        if isinstance(feature_vector, list) and len(feature_vector) > 0:
                            features.append(feature_vector)
                            photo_ids.append(photo.id)
                    except Exception as e:
                        logger.warning(f"解析照片 {photo.id} 的特征向量失败: {str(e)}")
                        continue
            return features, photo_ids
        
        features, photo_ids = await asyncio.to_thread(extract_features)
        
        if len(features) < 1:
            logger.info("有效特征向量不足，跳过聚类")
            return 0
        
        # 🔥 使用 run_in_executor() 包装 NumPy 和 DBSCAN 操作（CPU密集型）
        def perform_clustering():
            try:
                features_array = np.array(features)
                logger.info(f"提取了 {len(features_array)} 个有效特征向量，维度: {features_array.shape}")
                
                # 🔥 检查内存使用（估算）
                # 34914 * 2048 * 4 bytes ≈ 286MB (仅特征向量)
                # DBSCAN距离矩阵可能需要更多内存
                estimated_memory_mb = (len(features_array) * features_array.shape[1] * 4) / (1024 * 1024)
                logger.info(f"估算内存使用: {estimated_memory_mb:.1f}MB (仅特征向量)")
                
                # 使用DBSCAN进行聚类
                eps = 1 - self.similarity_threshold
                min_samples = 2
                
                logger.info(f"DBSCAN参数: eps={eps:.3f}, min_samples={min_samples}, metric='cosine'")
                logger.info(f"开始DBSCAN聚类计算（这可能需要几分钟）...")
                
                clustering = DBSCAN(
                    eps=eps,
                    min_samples=min_samples,
                    metric='cosine'
                )
                cluster_labels = clustering.fit_predict(features_array)
                
                logger.info(f"DBSCAN聚类计算完成")
                return features_array, cluster_labels
            except MemoryError as e:
                logger.error(f"内存不足，无法完成聚类: {str(e)}")
                raise Exception(f"内存不足，无法处理 {len(features)} 张照片。建议分批处理或减少照片数量。")
            except Exception as e:
                logger.error(f"DBSCAN聚类计算失败: {str(e)}", exc_info=True)
                raise
        
        # 🔥 在事件循环的线程池中执行CPU密集型操作，添加异常处理
        try:
            features_array, cluster_labels = await asyncio.get_event_loop().run_in_executor(
                None,  # 使用默认线程池
                perform_clustering
            )
        except Exception as e:
            logger.error(f"执行聚类计算失败: {str(e)}", exc_info=True)
            if task_id:
                self._update_task_status(task_id, {
                    "status": "failed",
                    "message": f"聚类计算失败: {str(e)}",
                    "end_time": datetime.now().isoformat()
                })
            raise
        
        # 更新进度：特征提取完成
        if task_id:
            self._update_task_status(task_id, {
                "message": f"已提取 {len(features_array)} 个特征向量，开始聚类...",
                "progress_percentage": 30.0
            })
        
        # 处理聚类结果
        unique_labels = set(cluster_labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)  # 移除噪声点
        
        logger.info(f"检测到 {len(unique_labels)} 个聚类，噪声点: {sum(cluster_labels == -1)}")
        
        # 更新进度：聚类计算完成
        if task_id:
            self._update_task_status(task_id, {
                "message": f"检测到 {len(unique_labels)} 个聚类，正在创建聚类记录...",
                "progress_percentage": 50.0
            })
        
        # 🔥 使用 asyncio.to_thread() 包装数据库操作（创建聚类记录）
        def create_cluster_records():
            try:
                clusters_info = []  # [(cluster_id, cluster_photo_ids, size, avg_similarity)]
                total_clusters = len(unique_labels)
                logger.info(f"开始创建 {total_clusters} 个聚类记录...")
                
                for idx, cluster_label in enumerate(unique_labels):
                    # 🔥 添加进度日志
                    if (idx + 1) % 50 == 0 or idx == 0:
                        logger.info(f"正在创建聚类记录: {idx + 1}/{total_clusters}")
                    
                    cluster_photo_ids = [photo_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_label]
                    
                    if len(cluster_photo_ids) < 1:
                        continue
                    
                    # 🔥 生成唯一的cluster_id（使用UUID确保唯一性）
                    uuid_short = uuid.uuid4().hex[:8]  # 使用8位UUID确保唯一性
                    cluster_id = f"cluster_{cluster_label}_{uuid_short}"
                    
                    # 🔥 对于大聚类，使用简化的相似度计算（避免内存溢出）
                    cluster_features = [features_array[i] for i, label in enumerate(cluster_labels) if label == cluster_label]
                    
                    # 如果聚类太大（>500张），使用采样方法计算平均相似度
                    if len(cluster_features) > 500:
                        logger.warning(f"聚类 {cluster_label} 包含 {len(cluster_features)} 张照片，使用采样方法计算平均相似度")
                        # 采样前100张和后100张照片计算相似度
                        sample_size = min(100, len(cluster_features) // 2)
                        sample_features = cluster_features[:sample_size] + cluster_features[-sample_size:]
                        avg_similarity = self._calculate_cluster_avg_similarity(sample_features)
                    else:
                        avg_similarity = self._calculate_cluster_avg_similarity(cluster_features)
                    
                    # 计算聚类质量
                    cluster_quality = self._calculate_cluster_quality(len(cluster_photo_ids), avg_similarity)
                    
                    # 创建聚类记录
                    representative_photo_id = cluster_photo_ids[0] if cluster_photo_ids else None
                    
                    cluster = DuplicateGroup(
                        cluster_id=cluster_id,
                        representative_photo_id=representative_photo_id,
                        photo_count=len(cluster_photo_ids),
                        avg_similarity=avg_similarity,
                        confidence_score=avg_similarity,
                        cluster_quality=cluster_quality,
                        similarity_threshold=self.similarity_threshold
                    )
                    db.add(cluster)
                    db.flush()  # 获取group_id
                    
                    # 添加聚类成员
                    for photo_id in cluster_photo_ids:
                        # 计算该照片与聚类中心的相似度
                        photo_idx = photo_ids.index(photo_id)
                        photo_feature = features_array[photo_idx]
                        
                        # 🔥 对于大聚类，使用采样特征计算相似度
                        if len(cluster_features) > 500:
                            similarity_score = self._calculate_photo_cluster_similarity(photo_feature, sample_features)
                        else:
                            similarity_score = self._calculate_photo_cluster_similarity(photo_feature, cluster_features)
                        
                        member = DuplicateGroupPhoto(
                            cluster_id=cluster_id,
                            group_id=cluster.id,
                            photo_id=photo_id,
                            similarity_score=similarity_score
                        )
                        db.add(member)
                    
                    clusters_info.append((cluster_id, cluster_photo_ids, len(cluster_photo_ids), avg_similarity))
                
                logger.info(f"开始提交数据库事务（创建 {len(clusters_info)} 个聚类）...")
                db.commit()
                logger.info(f"数据库事务提交完成")
                return clusters_info
            except MemoryError as e:
                logger.error(f"创建聚类记录时内存不足: {str(e)}", exc_info=True)
                db.rollback()
                raise Exception(f"内存不足，无法创建聚类记录。建议减少照片数量或分批处理。")
            except Exception as e:
                logger.error(f"创建聚类记录失败: {str(e)}", exc_info=True)
                db.rollback()
                raise
        
        clusters_info = await asyncio.to_thread(create_cluster_records)
        
        logger.info(f"✅ 成功创建 {len(clusters_info)} 个聚类")
        
        # 更新进度：聚类创建完成
        if task_id:
            self._update_task_status(task_id, {
                "message": f"成功创建 {len(clusters_info)} 个聚类",
                "progress_percentage": 65.0
            })
        
        # 统计信息
        if clusters_info:
            total_photos = sum(size for _, _, size, _ in clusters_info)
            avg_cluster_size = total_photos / len(clusters_info)
            logger.info(f"聚类统计: 总照片数={total_photos}, 平均聚类大小={avg_cluster_size:.1f}")
        
        return len(clusters_info)
    
    async def _refine_large_clusters(self, db: Session, task_id: Optional[str] = None) -> int:
        """
        对大聚类进行递归二次细分，直到所有聚类都小于等于阈值
        
        :param db: 数据库会话
        :return: 细分的聚类数量
        """
        _lazy_import_dependencies()
        
        if np is None or DBSCAN is None:
            logger.error("聚类依赖库未加载，无法进行二次细分")
            return 0
        
        try:
            refined_count = 0
            max_iterations = 15  # 增加迭代次数，适应更平缓的迭代趋势（5/6系数）
            iteration = 0
            
            # 🔥 在内存中维护待细分的照片ID列表（大于阈值的聚类）
            # 格式：{iteration: [photo_ids_list1, photo_ids_list2, ...]}
            pending_clusters_in_memory = []  # 存储待细分的照片ID列表
            
            # 计算初始余弦距离
            base_distance = 1 - self.similarity_threshold
            min_distance = 0.01  # 最小距离限制（对应最大相似度阈值0.99）
            
            while iteration < max_iterations:
                # 计算当前迭代的阈值
                # 🔥 使用乘以5/6的方式，让阈值变化更平缓（收敛更慢，减少噪声点）
                # 第1次迭代：base * (5/6)^1, 第2次迭代：base * (5/6)^2, 第3次迭代：base * (5/6)^3...
                current_distance = base_distance * ((5/6) ** (iteration + 1))
                
                # 确保距离不小于最小值
                if current_distance < min_distance:
                    current_distance = min_distance
                
                # 转换为相似度阈值
                current_threshold = 1 - current_distance
                
                # 🔥 从数据库和内存中获取待细分的聚类
                # 1. 从数据库查询大于阈值的聚类
                def query_large_clusters():
                    return db.query(DuplicateGroup).filter(
                        DuplicateGroup.cluster_id.isnot(None),
                        DuplicateGroup.photo_count > self.large_cluster_threshold
                    ).all()
                
                large_clusters = await asyncio.to_thread(query_large_clusters)
                
                # 2. 从内存中获取待细分的照片ID列表
                # 将内存中的照片ID列表转换为类似数据库查询的格式
                memory_clusters = []
                if pending_clusters_in_memory:
                    # 为内存中的每个照片ID列表创建一个虚拟的聚类对象
                    for photo_ids in pending_clusters_in_memory:
                        if len(photo_ids) > self.large_cluster_threshold:
                            # 创建一个简单的对象来模拟 DuplicateGroup
                            class MemoryCluster:
                                def __init__(self, photo_ids):
                                    self.cluster_id = f"memory_{id(photo_ids)}"  # 临时ID
                                    self.photo_ids = photo_ids
                                    self.photo_count = len(photo_ids)
                            memory_clusters.append(MemoryCluster(photo_ids))
                
                # 清空内存列表，本次迭代会重新填充
                pending_clusters_in_memory = []
                
                # 合并数据库和内存中的聚类
                all_large_clusters = list(large_clusters) + memory_clusters
                
                if not all_large_clusters:
                    logger.info(f"第 {iteration + 1} 次迭代：没有需要细分的大聚类，结束递归")
                    break
                
                logger.info(f"第 {iteration + 1} 次迭代：发现 {len(all_large_clusters)} 个大聚类需要细分"
                          f"（数据库: {len(large_clusters)}, 内存: {len(memory_clusters)}），"
                          f"使用阈值={current_threshold:.3f}（距离={current_distance:.4f}）")
                
                # 更新进度：开始递归细分迭代
                if task_id:
                    # 进度计算：70% + (当前迭代 / 最大迭代数) * 30%
                    base_progress = 70.0
                    iteration_progress = min(iteration / max_iterations, 1.0) * 30.0
                    self._update_task_status(task_id, {
                        "current_stage": "refining",
                        "message": f"第 {iteration + 1} 次迭代：正在细分 {len(large_clusters)} 个大聚类...",
                        "progress_percentage": base_progress + iteration_progress * 0.3,  # 先设置一个基础进度
                        "refining_iteration": iteration + 1,
                        "refining_total_clusters": len(all_large_clusters),
                        "refining_processed_clusters": 0
                    })
                
                iteration_refined = 0
                
                for large_cluster in all_large_clusters:
                    try:
                        # 🔥 判断是数据库聚类还是内存聚类
                        is_memory_cluster = hasattr(large_cluster, 'photo_ids')
                        
                        if is_memory_cluster:
                            # 内存聚类：直接使用照片ID列表
                            refined_photo_ids = large_cluster.photo_ids
                            logger.info(f"细分内存聚类，包含 {len(refined_photo_ids)} 张照片")
                            
                            # 从数据库查询照片对象（分批查询，避免SQLite参数限制）
                            def get_cluster_photos_from_ids():
                                photos = []
                                batch_size = 999  # SQLite IN子句限制
                                for i in range(0, len(refined_photo_ids), batch_size):
                                    batch_ids = refined_photo_ids[i:i+batch_size]
                                    batch_photos = db.query(Photo).filter(
                                        Photo.id.in_(batch_ids),
                                        Photo.image_features.isnot(None),
                                        Photo.image_features != ''
                                    ).order_by(Photo.id).all()
                                    photos.extend(batch_photos)
                                return photos
                            
                            photos = await asyncio.to_thread(get_cluster_photos_from_ids)
                        else:
                            # 数据库聚类：从数据库查询成员和照片
                            def get_cluster_members():
                                return db.query(DuplicateGroupPhoto).filter(
                                    DuplicateGroupPhoto.cluster_id == large_cluster.cluster_id
                                ).all()
                            
                            cluster_members = await asyncio.to_thread(get_cluster_members)
                            
                            if len(cluster_members) <= self.large_cluster_threshold:
                                continue
                            
                            logger.info(f"细分聚类 {large_cluster.cluster_id}，包含 {len(cluster_members)} 张照片")
                            
                            # 🔥 使用 JOIN 方式查询，避免 IN 子句的 SQLite 999 参数限制
                            def get_cluster_photos():
                                # 使用 JOIN 查询，不需要 IN 子句，避免 SQLite 参数限制
                                photos = db.query(Photo).join(
                                    DuplicateGroupPhoto, Photo.id == DuplicateGroupPhoto.photo_id
                                ).filter(
                                    DuplicateGroupPhoto.cluster_id == large_cluster.cluster_id,
                                    Photo.image_features.isnot(None),
                                    Photo.image_features != ''
                                ).order_by(Photo.id).all()
                                
                                return photos
                            
                            photos = await asyncio.to_thread(get_cluster_photos)
                            refined_photo_ids = [photo.id for photo in photos]
                        
                        if len(photos) < 2:
                            logger.warning(f"聚类 {large_cluster.cluster_id} 的有效照片不足，跳过细分")
                            continue
                        
                        # 🔥 使用 asyncio.to_thread() 包装特征向量提取
                        def extract_refined_features():
                            features = []
                            valid_photo_ids = []
                            for photo in photos:
                                if photo.image_features:
                                    try:
                                        if isinstance(photo.image_features, str):
                                            feature_vector = json.loads(photo.image_features)
                                        else:
                                            feature_vector = photo.image_features
                                        
                                        if isinstance(feature_vector, list) and len(feature_vector) > 0:
                                            features.append(feature_vector)
                                            valid_photo_ids.append(photo.id)
                                    except Exception as e:
                                        logger.warning(f"解析照片 {photo.id} 的特征向量失败: {str(e)}")
                                        continue
                            return features, valid_photo_ids
                        
                        features, valid_photo_ids = await asyncio.to_thread(extract_refined_features)
                        # 更新 refined_photo_ids 为有效的照片ID
                        refined_photo_ids = valid_photo_ids
                        
                        if len(features) < 2:
                            logger.warning(f"聚类 {large_cluster.cluster_id} 的有效特征向量不足，跳过细分")
                            continue
                        
                        # 🔥 使用 run_in_executor() 包装 DBSCAN 聚类（CPU密集型）
                        def perform_refined_clustering():
                            features_array = np.array(features)
                            
                            # 使用当前迭代的阈值进行聚类
                            refined_eps = current_distance
                            min_samples = 2
                            
                            logger.info(f"聚类参数: eps={refined_eps:.4f}, min_samples={min_samples}, "
                                      f"相似度阈值={current_threshold:.3f}")
                            
                            refined_clustering = DBSCAN(
                                eps=refined_eps,
                                min_samples=min_samples,
                                metric='cosine'
                            )
                            refined_labels = refined_clustering.fit_predict(features_array)
                            
                            return features_array, refined_labels
                        
                        features_array, refined_labels = await asyncio.get_event_loop().run_in_executor(
                            None,  # 使用默认线程池
                            perform_refined_clustering
                        )
                        
                        # 处理细分结果
                        refined_unique_labels = set(refined_labels)
                        if -1 in refined_unique_labels:
                            refined_unique_labels.remove(-1)  # 移除噪声点
                        
                        if len(refined_unique_labels) <= 1:
                            cluster_id = getattr(large_cluster, 'cluster_id', '内存聚类')
                            logger.info(f"聚类 {cluster_id} 细分后仍为1个聚类，跳过")
                            continue
                        
                        logger.info(f"聚类 {getattr(large_cluster, 'cluster_id', '内存聚类')} 细分为 {len(refined_unique_labels)} 个子聚类")
                        
                        # 🔥 使用 asyncio.to_thread() 包装数据库操作（删除原聚类并创建新聚类）
                        def create_refined_clusters(is_mem_cluster):
                            try:
                                # 🔥 创建 photo_id -> index 字典映射，避免重复的 O(n) 查找
                                photo_id_to_index = {photo_id: idx for idx, photo_id in enumerate(refined_photo_ids)}
                                
                                # 🔥 只删除数据库聚类，内存聚类不需要删除
                                if not is_mem_cluster:
                                    # 删除原聚类及其成员
                                    db.query(DuplicateGroupPhoto).filter(
                                        DuplicateGroupPhoto.cluster_id == large_cluster.cluster_id
                                    ).delete()
                                    db.delete(large_cluster)
                                    db.flush()
                                
                                # 🔥 批量创建所有聚类和成员，减少flush次数
                                refined_clusters = []  # 存储所有聚类对象
                                pending_clusters = []  # 存储待细分的照片ID列表
                                
                                # 第一遍：只创建最终确定的聚类（<=阈值），大于阈值的放在内存中
                                for refined_label in refined_unique_labels:
                                    refined_photo_ids_subset = [refined_photo_ids[i] 
                                                                for i, label in enumerate(refined_labels) 
                                                                if label == refined_label]
                                    
                                    if len(refined_photo_ids_subset) < 1:
                                        continue
                                    
                                    cluster_size = len(refined_photo_ids_subset)
                                    
                                    if cluster_size > self.large_cluster_threshold:
                                        # 🔥 大于阈值的聚类：放在内存中，不创建数据库记录
                                        pending_clusters.append(refined_photo_ids_subset)
                                        logger.debug(f"子聚类包含 {cluster_size} 张照片（>阈值），放入内存，将在下一次迭代中继续细分")
                                        continue
                                    
                                    # 🔥 只创建 <= 阈值的聚类（最终确定的聚类）
                                    uuid_short = uuid.uuid4().hex[:8]
                                    refined_cluster_id = f"cluster_refined_{iteration}_{refined_label}_{uuid_short}"
                                    
                                    # 计算真实平均相似度
                                    refined_cluster_features = [features_array[i] 
                                                                for i, label in enumerate(refined_labels) 
                                                                if label == refined_label]
                                    avg_similarity = self._calculate_cluster_avg_similarity(refined_cluster_features)
                                    
                                    # 计算聚类质量
                                    cluster_quality = self._calculate_cluster_quality(cluster_size, avg_similarity)
                                    
                                    # 创建新的聚类记录
                                    refined_cluster = DuplicateGroup(
                                        cluster_id=refined_cluster_id,
                                        representative_photo_id=refined_photo_ids_subset[0],
                                        photo_count=cluster_size,
                                        avg_similarity=avg_similarity,
                                        confidence_score=avg_similarity,
                                        cluster_quality=cluster_quality,
                                        similarity_threshold=current_threshold
                                    )
                                    db.add(refined_cluster)
                                    refined_clusters.append((refined_cluster, refined_cluster_id, refined_photo_ids_subset, refined_cluster_features))
                                
                                # 🔥 批量flush获取所有group_id（只flush一次）
                                logger.info(f"批量flush {len(refined_clusters)} 个聚类以获取group_id...")
                                db.flush()
                                
                                # 第二遍：创建所有成员对象
                                for refined_cluster, refined_cluster_id, refined_photo_ids_subset, refined_cluster_features in refined_clusters:
                                    # 🔥 对于大聚类，使用采样特征计算相似度（与第一次创建聚类保持一致）
                                    if len(refined_cluster_features) > 500:
                                        # 采样前100张和后100张照片的特征
                                        sample_size = min(100, len(refined_cluster_features) // 2)
                                        sample_features = refined_cluster_features[:sample_size] + refined_cluster_features[-sample_size:]
                                    else:
                                        sample_features = refined_cluster_features
                                    
                                    for photo_id in refined_photo_ids_subset:
                                        # 🔥 使用字典映射进行 O(1) 查找，替代 O(n) 的 index() 操作
                                        photo_idx = photo_id_to_index[photo_id]
                                        photo_feature = features_array[photo_idx]
                                        # 🔥 使用采样特征计算相似度（如果聚类太大）
                                        similarity_score = self._calculate_photo_cluster_similarity(
                                            photo_feature, sample_features
                                        )
                                        
                                        member = DuplicateGroupPhoto(
                                            cluster_id=refined_cluster_id,
                                            group_id=refined_cluster.id,
                                            photo_id=photo_id,
                                            similarity_score=similarity_score
                                        )
                                        db.add(member)
                                
                                logger.info(f"已创建 {len(refined_clusters)} 个最终聚类，"
                                          f"{len(pending_clusters)} 个大聚类放入内存待下次迭代")
                                return len(refined_clusters), pending_clusters
                            except Exception as e:
                                logger.error(f"创建细分聚类记录失败: {str(e)}", exc_info=True)
                                db.rollback()
                                raise
                        
                        iteration_refined_local, new_pending_clusters = await asyncio.to_thread(create_refined_clusters, is_memory_cluster)
                        iteration_refined += iteration_refined_local
                        # 🔥 将新的大聚类添加到内存列表
                        pending_clusters_in_memory.extend(new_pending_clusters)
                        
                        cluster_info = f"内存聚类" if is_memory_cluster else f"聚类 {large_cluster.cluster_id}"
                        logger.info(f"✅ {cluster_info} 细分完成，"
                                  f"原 {len(refined_photo_ids)} 张照片分为 {len(refined_unique_labels)} 个子聚类")
                        
                        # 🔥 显式释放大对象，释放内存（处理完一个大聚类后）
                        del features_array
                        del refined_photo_ids
                        del refined_labels
                        del refined_unique_labels
                        
                        # 更新进度：每个大聚类处理完成
                        if task_id:
                            # 计算当前迭代的进度
                            base_progress = 70.0
                            iteration_progress_range = 30.0  # 递归细分阶段占总进度的30%
                            # 当前迭代的进度 = (已处理聚类数 / 总聚类数) * 当前迭代的进度范围
                            current_iteration_progress = (iteration_refined / len(all_large_clusters)) * (iteration_progress_range / max_iterations) if len(all_large_clusters) > 0 else 0
                            # 总进度 = 70% + 之前迭代的进度 + 当前迭代的进度
                            total_progress = base_progress + (iteration / max_iterations) * iteration_progress_range + current_iteration_progress
                            
                            self._update_task_status(task_id, {
                                "message": f"第 {iteration + 1} 次迭代：已处理 {iteration_refined}/{len(all_large_clusters)} 个大聚类...",
                                "progress_percentage": min(total_progress, 99.0),  # 不超过99%，留1%给最终完成
                                "refining_processed_clusters": iteration_refined
                            })
                        
                    except Exception as e:
                        cluster_id = getattr(large_cluster, 'cluster_id', '内存聚类')
                        logger.error(f"细分聚类 {cluster_id} 失败: {str(e)}")
                        continue
                
                refined_count += iteration_refined
                
                # 如果没有成功细分任何聚类，退出循环
                if iteration_refined == 0:
                    logger.info(f"第 {iteration + 1} 次迭代：没有成功细分任何聚类，结束递归")
                    break
                
                # 🔥 使用 asyncio.to_thread() 包装数据库提交
                def commit_changes():
                    db.commit()
                
                await asyncio.to_thread(commit_changes)
                
                # 🔥 让出控制权，允许其他任务执行（参考人脸识别任务）
                await asyncio.sleep(0.01)
                
                iteration += 1
            
            if iteration >= max_iterations:
                logger.warning(f"达到最大迭代次数 {max_iterations}，停止递归细分")
            
            logger.info(f"递归细分完成，共进行 {iteration} 次迭代，细分了 {refined_count} 个聚类")
            return refined_count
            
        except Exception as e:
            logger.error(f"大聚类递归细分失败: {str(e)}")
            db.rollback()
            return 0
    
    def _calculate_cluster_avg_similarity(self, cluster_features: List) -> float:
        """
        计算聚类内平均相似度
        
        :param cluster_features: 聚类内的特征向量列表
        :return: 平均相似度（0-1）
        """
        # 确保依赖库已加载
        _lazy_import_dependencies()
        
        if np is None:
            logger.warning("numpy未加载，无法计算平均相似度")
            return 0.8  # 返回默认值
        
        if len(cluster_features) < 2:
            return 1.0
        
        try:
            features_array = np.array(cluster_features)
            
            # 🔥 对于大聚类（>500），使用采样方法避免内存溢出
            if len(features_array) > 500:
                # 采样计算：随机选择最多200个样本对
                sample_size = min(200, len(features_array))
                indices = np.random.choice(len(features_array), sample_size, replace=False)
                sample_features = features_array[indices]
                
                from sklearn.metrics.pairwise import cosine_similarity
                similarity_matrix = cosine_similarity(sample_features)
                
                # 取上三角矩阵（不包括对角线）
                upper_triangle = similarity_matrix[np.triu_indices(len(similarity_matrix), k=1)]
                
                # 返回平均值
                return float(np.mean(upper_triangle))
            
            # 对于小聚类，使用完整计算
            from sklearn.metrics.pairwise import cosine_similarity
            similarity_matrix = cosine_similarity(features_array)
            
            # 取上三角矩阵（不包括对角线）
            upper_triangle = similarity_matrix[np.triu_indices(len(similarity_matrix), k=1)]
            
            # 返回平均值
            return float(np.mean(upper_triangle))
        except MemoryError as e:
            logger.error(f"计算聚类平均相似度时内存不足: {str(e)}")
            # 使用简化的估算方法
            if len(cluster_features) >= 2:
                # 只计算前两个特征向量的相似度作为估算
                from sklearn.metrics.pairwise import cosine_similarity
                similarity = cosine_similarity([cluster_features[0]], [cluster_features[1]])[0][0]
                return float(similarity)
            return 0.8
        except Exception as e:
            logger.warning(f"计算聚类平均相似度失败: {str(e)}")
            return 0.8  # 默认值
    
    def _calculate_photo_cluster_similarity(self, photo_feature, cluster_features: List) -> float:
        """
        计算照片与聚类中心的相似度
        
        :param photo_feature: 照片的特征向量（可以是list或np.ndarray）
        :param cluster_features: 聚类内的特征向量列表
        :return: 相似度（0-1）
        """
        # 确保依赖库已加载
        _lazy_import_dependencies()
        
        if np is None:
            logger.warning("numpy未加载，无法计算照片聚类相似度")
            return 0.8  # 返回默认值
        
        try:
            # 确保photo_feature是numpy数组
            if not isinstance(photo_feature, np.ndarray):
                photo_feature = np.array(photo_feature)
            
            features_array = np.array(cluster_features)
            
            # 计算聚类中心（均值）
            cluster_center = np.mean(features_array, axis=0)
            
            # 计算照片与聚类中心的余弦相似度
            from sklearn.metrics.pairwise import cosine_similarity
            similarity = cosine_similarity([photo_feature], [cluster_center])[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.warning(f"计算照片聚类相似度失败: {str(e)}")
            return 0.8  # 默认值
    
    def _calculate_cluster_quality(self, photo_count: int, avg_similarity: float) -> str:
        """
        计算聚类质量
        
        :param photo_count: 照片数量
        :param avg_similarity: 平均相似度
        :return: 质量等级（high/medium/low）
        """
        if photo_count >= 5 and avg_similarity >= 0.8:
            return "high"
        elif photo_count >= 3 and avg_similarity >= 0.7:
            return "medium"
        else:
            return "low"

