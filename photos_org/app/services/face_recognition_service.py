"""
人脸识别服务模块

## 功能特点：
1. 基于InsightFace的人脸检测和特征提取
2. 支持批量处理照片
3. 自动人脸聚类功能
4. 可配置的聚类参数
5. 本地处理，保护隐私

## 与其他版本的不同点：
- 使用InsightFace替代face_recognition
- 支持Top N聚类限制
- 集成到现有分析流程
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json

# 延迟导入重型库
insightface = None
FaceAnalysis = None
ins_get_image = None
cv2 = None
DBSCAN = None
cosine_similarity = None
plt = None
tqdm = None

from app.core.config import settings
from app.db.session import get_db
from app.models.face import FaceDetection, FaceCluster, FaceClusterMember, Person
from app.models.photo import Photo
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    """人脸识别服务类"""
    
    def __init__(self):
        """初始化人脸识别服务"""
        self.app = None
        self.is_initialized = False
        self.config = settings.face_recognition
        
    def _lazy_import_dependencies(self):
        """延迟导入重型库"""
        global insightface, FaceAnalysis, ins_get_image, cv2, DBSCAN, cosine_similarity, plt, tqdm
        
        if insightface is None:
            try:
                import numpy as np
                import insightface
                from insightface.app import FaceAnalysis
                from insightface.data import get_image as ins_get_image
                import cv2
                from sklearn.cluster import DBSCAN
                from sklearn.metrics.pairwise import cosine_similarity
                import matplotlib.pyplot as plt
                from tqdm import tqdm
                logger.info("成功加载人脸识别依赖库")
            except ImportError as e:
                logger.error(f"人脸识别依赖导入失败: {e}")
    
    async def initialize(self) -> bool:
        """
        初始化人脸识别模型
        :return: 是否初始化成功
        """
        # 延迟导入依赖
        self._lazy_import_dependencies()
        
        try:
            if not insightface:
                logger.error("InsightFace未安装，无法启用人脸识别")
                return False
                
            if not self.config.enabled:
                logger.info("人脸识别功能已禁用")
                return False
                
            logger.info("正在初始化人脸识别模型...")
            
            # 根据配置决定使用本地模型还是在线模型
            if self.config.use_local_model:
                # 使用本地模型路径（参考存储服务的路径处理方式）
                models_base_path = Path(self.config.models_base_path).resolve()
                model_path = models_base_path / self.config.model
                logger.info(f"使用本地模型路径: {model_path}")
                
                if not model_path.exists():
                    logger.error(f"本地模型路径不存在: {model_path}")
                    return False
                
                # 初始化InsightFace应用（使用绝对路径）
                self.app = FaceAnalysis(name=str(model_path))
            else:
                # 使用在线模型（默认行为）
                logger.info(f"使用在线模型: {self.config.model}")
                self.app = FaceAnalysis(name=self.config.model)
            
            # 🔥 质量优化：调整检测参数
            # 使用适中的检测尺寸以平衡质量和速度
            det_size = (640, 640)  # 恢复到640x640以提高检测精度
            logger.info(f"设置检测尺寸: {det_size}")
            
            # 准备模型，使用CPU上下文
            self.app.prepare(ctx_id=0, det_size=det_size)
            
            logger.info("人脸识别模型初始化成功")
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"人脸识别模型初始化失败: {e}")
            return False
    
    async def detect_faces_in_photo(self, photo_path: str, photo_id: int) -> List[Dict]:
        """
        检测单张照片中的人脸
        :param photo_path: 照片路径
        :param photo_id: 照片ID
        :return: 人脸检测结果列表
        """
        if not self.is_initialized:
            logger.warning("人脸识别服务未初始化")
            return []
            
        try:
            # 检查文件路径
            import os
            file_exists = os.path.exists(photo_path)
            
            if not file_exists:
                logger.error(f"文件不存在: {photo_path}")
                return []
            
            # 读取图像
            img = cv2.imread(photo_path)
            
            if img is None:
                # 尝试其他方法读取
                try:
                    with open(photo_path, 'rb') as f:
                        img_data = f.read()
                    import numpy as np
                    nparr = np.frombuffer(img_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is None:
                        return []
                except Exception as e:
                    logger.error(f"图像读取失败: {e}")
                    return []
            
            # 🔥 质量优化：使用原始图像进行人脸检测
            # 移除图像缩放，确保坐标一致性
            height, width = img.shape[:2]
            # logger.info(f"使用原始图像进行人脸检测: {width}x{height}")
            
            try:
                # 🔥 性能优化：设置检测阈值
                # 使用更高的检测阈值，减少低质量人脸的检测
                detection_threshold = self.config.detection_threshold
                
                # 临时设置检测阈值
                original_thresh = self.app.det_thresh
                self.app.det_thresh = detection_threshold
                
                # 🔥 真正的并发：将同步调用包装成异步
                faces = await asyncio.get_event_loop().run_in_executor(
                    None,  # 使用默认线程池
                    self.app.get,  # 同步方法
                    img  # 参数
                )
                
                # 恢复原始阈值
                self.app.det_thresh = original_thresh
                
            except Exception as e:
                logger.error(f"InsightFace检测失败: {e}")
                raise e
            
            # 🔥 关键：记录真实检测到的人脸数量
            real_face_count = len(faces)  # 这是真实检测到的人数！
            
            # 🔥 性能优化：限制处理的人脸数量
            max_faces = self.config.max_faces_per_photo
            if len(faces) > max_faces:
                # 按检测分数排序，只处理前N个最高分的人脸
                faces = sorted(faces, key=lambda f: f.det_score, reverse=True)[:max_faces]
                logger.info(f"限制人脸数量: 从 {real_face_count} 个减少到 {max_faces} 个")
            
            # 处理检测到的人脸
            results = []
            for i, face in enumerate(faces):
                try:
                    det_score = face.det_score
                    bbox = face.bbox
                    embedding = face.embedding
                    
                    # 检查关键属性
                    if bbox is None or embedding is None:
                        continue
                        
                except Exception as e:
                    logger.error(f"处理人脸 {i+1} 失败: {e}")
                    continue
                
                if det_score < self.config.detection_threshold:
                    continue
                
                # 生成人脸唯一ID
                face_id = f"face_{photo_id}_{i}_{int(datetime.now().timestamp())}"
                
                # 提取人脸特征
                face_features = embedding.tolist()
                
                # 获取人脸位置
                bbox_int = bbox.astype(int)
                face_rectangle = [int(bbox_int[0]), int(bbox_int[1]), int(bbox_int[2] - bbox_int[0]), int(bbox_int[3] - bbox_int[1])]
                
                result = {
                    'face_id': face_id,
                    'photo_id': photo_id,
                    'face_rectangle': face_rectangle,
                    'confidence': float(det_score),
                    'face_features': face_features,
                    'age_estimate': int(face.age) if hasattr(face, 'age') else None,
                    'gender_estimate': face.sex if hasattr(face, 'sex') else None
                }
                results.append(result)
                
            # 🔥 优化：简化日志输出
            logger.info(f"照片 {photo_id} 处理完成: 检测到 {real_face_count} 个人脸，处理了 {len(results)} 个")
            
            # 🔥 关键：返回检测结果和真实人数
            return {
                'detections': results,
                'real_face_count': real_face_count  # 真实检测到的人数
            }
            
        except Exception as e:
            logger.error(f"人脸检测失败 {photo_path}: {e}")
            raise e
    
    async def save_face_detections(self, detections: List[Dict], db: Session) -> bool:
        """
        保存人脸检测结果到数据库
        :param detections: 人脸检测结果列表
        :param db: 数据库会话
        :return: 是否保存成功
        """
        try:
            for detection in detections:
                face_detection = FaceDetection(
                    photo_id=detection['photo_id'],
                    face_id=detection['face_id'],
                    face_rectangle=detection['face_rectangle'],
                    confidence=detection['confidence'],
                    face_features=detection['face_features'],
                    age_estimate=detection.get('age_estimate'),
                    gender_estimate=detection.get('gender_estimate')
                )
                db.add(face_detection)
            
            db.commit()
            logger.info(f"成功保存 {len(detections)} 个人脸检测结果")
            return True
            
        except Exception as e:
            logger.error(f"保存人脸检测结果失败: {e}")
            db.rollback()
            return False
    
    async def cluster_faces(self, db: Session) -> bool:
        """
        对人脸进行聚类分析
        :param db: 数据库会话
        :return: 是否聚类成功
        """
        # 延迟导入依赖
        self._lazy_import_dependencies()
        import numpy as np
        
        try:
            logger.info("开始人脸聚类分析...")
            
            # 获取所有人脸特征
            faces = db.query(FaceDetection).filter(
                FaceDetection.face_features.isnot(None)
            ).all()
            
            if len(faces) < 2:
                logger.info("人脸数量不足，跳过聚类")
                return True
                
            # 提取特征向量
            features = []
            face_ids = []
            for face in faces:
                if face.face_features:
                    features.append(face.face_features)
                    face_ids.append(face.face_id)
            
            if len(features) < 2:
                logger.info("有效人脸特征不足，跳过聚类")
                return True
                
            features = np.array(features)
            
            # 使用DBSCAN进行聚类
            clustering = DBSCAN(
                eps=1 - self.config.similarity_threshold,
                min_samples=self.config.min_cluster_size,
                metric='cosine'
            )
            cluster_labels = clustering.fit_predict(features)
            
            # 处理聚类结果
            unique_labels = set(cluster_labels)
            if -1 in unique_labels:
                unique_labels.remove(-1)  # 移除噪声点
                
            logger.info(f"检测到 {len(unique_labels)} 个聚类")
            
            # 限制聚类数量（Top N）
            if len(unique_labels) > self.config.max_clusters:
                # 按聚类大小排序，保留最大的N个
                cluster_sizes = {}
                for label in unique_labels:
                    cluster_sizes[label] = np.sum(cluster_labels == label)
                
                # 按大小排序，保留Top N
                sorted_clusters = sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True)
                top_clusters = [label for label, _ in sorted_clusters[:self.config.max_clusters]]
                
                logger.info(f"限制聚类数量为Top {self.config.max_clusters}，保留 {len(top_clusters)} 个聚类")
                unique_labels = set(top_clusters)
            
            # 保存聚类结果
            for cluster_label in unique_labels:
                cluster_faces = [face_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_label]
                
                if len(cluster_faces) < self.config.min_cluster_size:
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
            logger.info(f"人脸聚类完成，创建了 {len(unique_labels)} 个聚类")
            return True
            
        except Exception as e:
            logger.error(f"人脸聚类失败: {e}")
            db.rollback()
            return False
    
    
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
    
    async def mark_photos_as_processed(self, photo_ids: set, db: Session):
        """
        标记照片为已处理（即使没有检测到人脸）
        :param photo_ids: 已处理的照片ID集合
        :param db: 数据库会话
        """
        try:
            for photo_id in photo_ids:
                # 检查是否已经有处理记录
                existing_record = db.query(FaceDetection).filter(
                    FaceDetection.photo_id == photo_id,
                    FaceDetection.face_id.like(f"processed_{photo_id}_%")
                ).first()
                
                if not existing_record:
                    # 创建处理记录（没有检测到人脸的标记）
                    processed_face_id = f"processed_{photo_id}_{int(datetime.now().timestamp())}"
                    processed_record = FaceDetection(
                        face_id=processed_face_id,
                        photo_id=photo_id,
                        face_rectangle=[0, 0, 0, 0],  # 空的人脸位置
                        confidence=0.0,  # 0表示没有检测到人脸
                        face_features=None,  # 没有特征
                        age_estimate=None,
                        gender_estimate=None,
                        created_at=datetime.now()
                    )
                    db.add(processed_record)
            
            db.commit()
            logger.info(f"标记了 {len(photo_ids)} 张照片为已处理")
            
        except Exception as e:
            logger.error(f"标记照片处理状态失败: {e}")
            db.rollback()

    async def batch_save_face_detections(self, all_detection_results: List[Dict], db: Session) -> bool:
        """
        批量保存人脸检测结果到数据库（包含人脸数量）
        :param all_detection_results: 检测结果列表，包含人数信息
        :param db: 数据库会话
        :return: 是否保存成功
        """
        try:
            if not all_detection_results:
                return True
            
            # 按照片ID分组统计人脸数量
            photo_face_counts = {}
            detection_time = datetime.now()  # 检测时间
            
            for result in all_detection_results:
                photo_id = result['photo_id']
                real_face_count = result['real_face_count']
                detections = result['detections']
                
                # 记录人脸数量
                photo_face_counts[photo_id] = real_face_count
                
                # 保存人脸检测记录
                for detection in detections:
                    face_detection = FaceDetection(
                        photo_id=detection['photo_id'],
                        face_id=detection['face_id'],
                        face_rectangle=detection['face_rectangle'],
                        confidence=detection['confidence'],
                        face_features=detection['face_features'],
                        age_estimate=detection.get('age_estimate'),
                        gender_estimate=detection.get('gender_estimate'),
                        created_at=detection_time
                    )
                    db.add(face_detection)
            
            # 🔥 关键：在同一个事务中更新Photo表的人脸数量和时间
            for photo_id, face_count in photo_face_counts.items():
                photo = db.query(Photo).filter(Photo.id == photo_id).first()
                if photo:
                    photo.face_count = face_count  # 保存真实检测到的人数
                    photo.face_detected_at = detection_time  # 保存检测时间
            
            logger.info(f"准备批量保存 {len(all_detection_results)} 个人脸检测结果，更新 {len(photo_face_counts)} 张照片的人脸数量")
            return True
            
        except Exception as e:
            logger.error(f"批量保存人脸检测结果失败: {e}")
            return False

    async def batch_mark_photos_as_processed(self, all_processed_photos: set, db: Session) -> bool:
        """
        批量标记照片为已处理（不提交事务）
        :param all_processed_photos: 已处理的照片ID集合
        :param db: 数据库会话
        :return: 是否保存成功
        """
        try:
            if not all_processed_photos:
                return True
            
            for photo_id in all_processed_photos:
                # 检查是否已经有处理记录
                existing_record = db.query(FaceDetection).filter(
                    FaceDetection.photo_id == photo_id,
                    FaceDetection.face_id.like(f"processed_{photo_id}_%")
                ).first()
                
                if not existing_record:
                    # 创建处理记录（没有检测到人脸的标记）
                    processed_face_id = f"processed_{photo_id}_{int(datetime.now().timestamp())}"
                    processed_record = FaceDetection(
                        face_id=processed_face_id,
                        photo_id=photo_id,
                        face_rectangle=[0, 0, 0, 0],  # 空的人脸位置
                        confidence=0.0,  # 0表示没有检测到人脸
                        face_features=None,  # 没有特征
                        age_estimate=None,
                        gender_estimate=None,
                        created_at=datetime.now()
                    )
                    db.add(processed_record)
            
            logger.info(f"准备批量标记 {len(all_processed_photos)} 张照片为已处理")
            return True
            
        except Exception as e:
            logger.error(f"批量标记照片已处理失败: {e}")
            return False

# 懒加载实例
_face_service_instance = None

def get_face_service():
    """获取人脸识别服务实例（单例模式）"""
    global _face_service_instance
    if _face_service_instance is None:
        _face_service_instance = FaceRecognitionService()
    return _face_service_instance

# 为了向后兼容，提供全局访问
def __getattr__(name):
    if name == 'face_service':
        return get_face_service()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
