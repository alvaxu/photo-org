"""
程序说明：

## 1. 增强相似照片检测服务
## 2. 融合多种算法提高检测准确性
## 3. 针对不同场景优化检测策略
"""

import imagehash
from PIL import Image
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
import cv2
from pathlib import Path
import math
import json
from datetime import datetime, timedelta

# 导入HEIC支持
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORT = True
except ImportError:
    HEIC_SUPPORT = False
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.photo import Photo, PhotoAnalysis, PhotoQuality, PhotoTag, Tag


class EnhancedSimilarityService:
    """
    增强相似照片检测服务
    融合多种算法提高检测准确性
    """

    def __init__(self):
        """初始化增强相似性服务"""
        from app.core.config import settings

        self.logger = get_logger(__name__)
        self.hash_size = 16

        # 从配置文件读取所有相似度相关配置
        self.similarity_threshold = settings.search.similarity_threshold  # 从search配置读取
        self.SIMILARITY_WEIGHTS = settings.similarity.first_layer_weights  # 从similarity配置读取
        self.DEFAULT_THRESHOLDS = settings.similarity.first_layer_thresholds  # 从similarity配置读取

        # 从配置文件读取预筛选参数
        self.time_margin_days = settings.similarity.pre_screening["time_margin_days"]
        self.location_margin = settings.similarity.pre_screening["location_margin"]
        
        # 存储基础路径（用于构建完整文件路径）
        self.storage_base = Path(settings.storage.base_path).resolve()

    def _get_full_path(self, image_path: str) -> Path:
        """
        构建完整的文件路径
        
        :param image_path: 相对路径或绝对路径
        :return: 完整路径
        """
        path = Path(image_path)
        # 如果是绝对路径，直接返回
        if path.is_absolute():
            return path
        # 如果是相对路径，添加storage_base前缀
        return self.storage_base / image_path

    def calculate_multiple_hashes(self, image_path: str) -> Dict[str, str]:
        """
        计算多种类型的哈希值
        
        :param image_path: 图像文件路径（相对路径或绝对路径）
        :return: 包含多种哈希值的字典
        """
        try:
            # 构建完整路径
            full_path = self._get_full_path(image_path)
            
            image = Image.open(str(full_path))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 计算多种哈希
            hashes = {
                'phash': str(imagehash.phash(image, hash_size=self.hash_size)),
                'dhash': str(imagehash.dhash(image, hash_size=self.hash_size)),
                'ahash': str(imagehash.average_hash(image, hash_size=self.hash_size)),
                'whash': str(imagehash.whash(image, hash_size=self.hash_size))
            }
            
            return hashes
            
        except Exception as e:
            self.logger.error(f"计算多哈希失败 {image_path}: {str(e)}")
            raise Exception(f"计算多哈希失败: {str(e)}")

    def calculate_color_histogram(self, image_path: str) -> np.ndarray:
        """
        计算颜色直方图特征
        
        :param image_path: 图像文件路径（相对路径或绝对路径）
        :return: 颜色直方图特征向量
        """
        try:
            # 构建完整路径
            full_path = self._get_full_path(image_path)
            
            # 使用OpenCV读取图像
            image = cv2.imread(str(full_path))
            if image is None:
                raise Exception("无法读取图像")
            
            # 转换到HSV色彩空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 计算HSV直方图
            hist_h = cv2.calcHist([hsv], [0], None, [50], [0, 180])
            hist_s = cv2.calcHist([hsv], [1], None, [60], [0, 256])
            hist_v = cv2.calcHist([hsv], [2], None, [60], [0, 256])
            
            # 合并直方图
            hist = np.concatenate([hist_h.flatten(), hist_s.flatten(), hist_v.flatten()])
            
            # 归一化
            hist = hist / (hist.sum() + 1e-7)
            
            return hist
            
        except Exception as e:
            self.logger.error(f"计算颜色直方图失败 {image_path}: {str(e)}")
            return np.zeros(170)  # 返回零向量作为默认值

    def calculate_structural_similarity(self, image_path1: str, image_path2: str) -> float:
        """
        计算结构相似性（SSIM）
        
        :param image_path1: 第一张图像路径（相对路径或绝对路径）
        :param image_path2: 第二张图像路径（相对路径或绝对路径）
        :return: 结构相似性分数 (0-1)
        """
        try:
            # 构建完整路径
            full_path1 = self._get_full_path(image_path1)
            full_path2 = self._get_full_path(image_path2)
            
            # 读取图像
            img1 = cv2.imread(str(full_path1), cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(str(full_path2), cv2.IMREAD_GRAYSCALE)
            
            if img1 is None or img2 is None:
                return 0.0
            
            # 调整图像大小到相同尺寸
            target_size = (256, 256)
            img1 = cv2.resize(img1, target_size)
            img2 = cv2.resize(img2, target_size)
            
            # 计算SSIM
            from skimage.metrics import structural_similarity as ssim
            similarity = ssim(img1, img2)
            
            return max(0.0, similarity)  # 确保非负
            
        except Exception as e:
            self.logger.error(f"计算结构相似性失败: {str(e)}")
            return 0.0

    def get_photo_analysis(self, photo_id: int, db_session: Session) -> Optional[Dict]:
        """获取照片的AI分析结果"""
        try:
            analysis = db_session.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id == photo_id
            ).first()
            
            if analysis and analysis.analysis_result:
                if isinstance(analysis.analysis_result, str):
                    return json.loads(analysis.analysis_result)
                else:
                    return analysis.analysis_result
            return None
        except Exception:
            return None

    def calculate_scene_type_similarity(self, scene1: str, scene2: str) -> float:
        """计算场景类型相似度（支持部分匹配）"""
        if not scene1 or not scene2:
            return 0.0
        
        # 完全匹配
        if scene1 == scene2:
            return 1.0
        
        # 处理包含关系（如"风景/人物"包含"风景"）
        scene1_parts = set(scene1.split('/'))
        scene2_parts = set(scene2.split('/'))
        
        # 计算交集和并集
        intersection = scene1_parts.intersection(scene2_parts)
        union = scene1_parts.union(scene2_parts)
        
        if not intersection:
            return 0.0
        
        # 使用Jaccard相似度计算部分匹配
        jaccard_sim = len(intersection) / len(union)
        
        # 如果完全包含，给更高分数
        if scene1_parts.issubset(scene2_parts) or scene2_parts.issubset(scene1_parts):
            return max(0.8, jaccard_sim)
        
        return jaccard_sim

    def calculate_objects_similarity(self, objects1: List, objects2: List) -> float:
        """计算对象相似度（Jaccard）"""
        if not objects1 or not objects2:
            return 0.0
        
        set1 = set(objects1) if isinstance(objects1, list) else set()
        set2 = set(objects2) if isinstance(objects2, list) else set()
        
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def calculate_emotion_similarity(self, emotion1: str, emotion2: str) -> float:
        """计算情感相似度（Jaccard）"""
        if not emotion1 or not emotion2:
            return 0.0
        
        # 支持多情感，用逗号分隔
        set1 = set(emotion1.split(',')) if isinstance(emotion1, str) else set()
        set2 = set(emotion2.split(',')) if isinstance(emotion2, str) else set()
        
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def calculate_activity_similarity(self, activity1: str, activity2: str) -> float:
        """计算活动相似度（Jaccard）"""
        if not activity1 or not activity2:
            return 0.0
        
        set1 = set(activity1.split(',')) if isinstance(activity1, str) else set()
        set2 = set(activity2.split(',')) if isinstance(activity2, str) else set()
        
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def calculate_description_similarity(self, desc1: str, desc2: str) -> float:
        """计算描述相似度（jieba + 余弦）"""
        if not desc1 or not desc2:
            return 0.0
        
        try:
            # 延迟导入jieba和sklearn
            import jieba
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            # 1. 分词
            words1 = ' '.join(jieba.cut(desc1))
            words2 = ' '.join(jieba.cut(desc2))
            
            # 2. 去除停用词
            stop_words = {'的', '了', '在', '是', '有', '和', '与', '等', '一个', '一些', '很', '非常', '特别'}
            words1 = ' '.join([w for w in jieba.cut(desc1) if w not in stop_words and len(w) > 1])
            words2 = ' '.join([w for w in jieba.cut(desc2) if w not in stop_words and len(w) > 1])
            
            if not words1 or not words2:
                return 0.0
            
            # 3. TF-IDF向量化
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([words1, words2])
            
            # 4. 计算余弦相似度
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
            
        except Exception:
            return 0.0

    def calculate_camera_similarity(self, camera1: Dict, camera2: Dict) -> float:
        """计算相机参数相似度"""
        if not camera1 or not camera2:
            return 0.0
        
        similarities = {}
        
        # 相机品牌
        if camera1.get('make') and camera2.get('make'):
            similarities['make'] = 1.0 if camera1['make'] == camera2['make'] else 0.0
        else:
            similarities['make'] = 0.0
        
        # 相机型号
        if camera1.get('model') and camera2.get('model'):
            similarities['model'] = 1.0 if camera1['model'] == camera2['model'] else 0.0
        else:
            similarities['model'] = 0.0
        
        # 镜头型号
        if camera1.get('lens') and camera2.get('lens'):
            similarities['lens'] = 1.0 if camera1['lens'] == camera2['lens'] else 0.0
        else:
            similarities['lens'] = 0.0
        
        # 焦距相似度
        if camera1.get('focal_length') and camera2.get('focal_length'):
            try:
                focal1 = float(camera1['focal_length'])
                focal2 = float(camera2['focal_length'])
                if focal1 > 0 and focal2 > 0:
                    ratio = min(focal1, focal2) / max(focal1, focal2)
                    similarities['focal_length'] = ratio
                else:
                    similarities['focal_length'] = 0.0
            except (ValueError, TypeError):
                similarities['focal_length'] = 0.0
        else:
            similarities['focal_length'] = 0.0
        
        # 光圈相似度
        if camera1.get('aperture') and camera2.get('aperture'):
            try:
                aperture1 = float(camera1['aperture'])
                aperture2 = float(camera2['aperture'])
                if aperture1 > 0 and aperture2 > 0:
                    ratio = min(aperture1, aperture2) / max(aperture1, aperture2)
                    similarities['aperture'] = ratio
                else:
                    similarities['aperture'] = 0.0
            except (ValueError, TypeError):
                similarities['aperture'] = 0.0
        else:
            similarities['aperture'] = 0.0
        
        # 返回加权平均
        weights = {'make': 0.3, 'model': 0.3, 'lens': 0.2, 'focal_length': 0.1, 'aperture': 0.1}
        weighted_sum = sum(similarities[key] * weights[key] for key in weights)
        total_weight = sum(weights[key] for key in weights)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def calculate_perceptual_hash_similarity(self, photo1: Photo, photo2: Photo) -> float:
        """计算感知哈希相似度（多种哈希融合）"""
        try:
            # 优先使用数据库中的哈希值
            if photo1.perceptual_hash and photo2.perceptual_hash:
                # 使用数据库中的phash计算相似度
                h1 = imagehash.hex_to_hash(photo1.perceptual_hash)
                h2 = imagehash.hex_to_hash(photo2.perceptual_hash)
                hamming_dist = h1 - h2
                # 根据哈希长度设置最大距离
                max_distance = len(photo1.perceptual_hash) * 4  # 每个字符4位
                return max(0.0, 1 - (hamming_dist / max_distance))
            
            # 如果数据库中没有哈希值，则实时计算
            hashes1 = self.calculate_multiple_hashes(photo1.original_path)
            hashes2 = self.calculate_multiple_hashes(photo2.original_path)
            
            if not hashes1 or not hashes2:
                return 0.0
            
            similarities = {}
            for hash_type in ['phash', 'dhash', 'ahash', 'whash']:
                if hashes1.get(hash_type) and hashes2.get(hash_type):
                    # 使用imagehash库计算汉明距离
                    h1 = imagehash.hex_to_hash(hashes1[hash_type])
                    h2 = imagehash.hex_to_hash(hashes2[hash_type])
                    hamming_dist = h1 - h2
                    # 转换为相似度（0-1）
                    max_distance = 64  # 16x16的哈希
                    similarities[hash_type] = max(0.0, 1 - (hamming_dist / max_distance))
                else:
                    similarities[hash_type] = 0.0
            
            # 返回平均相似度
            return sum(similarities.values()) / len(similarities) if similarities else 0.0
            
        except Exception:
            return 0.0

    def calculate_color_histogram_similarity(self, photo1: Photo, photo2: Photo) -> float:
        """计算颜色直方图相似度"""
        try:
            hist1 = self.calculate_color_histogram(photo1.original_path)
            hist2 = self.calculate_color_histogram(photo2.original_path)
            
            if hist1 is None or hist2 is None:
                return 0.0
            
            # 使用巴氏距离计算相似度
            try:
                from scipy.spatial.distance import bhattacharyya
                distance = bhattacharyya(hist1, hist2)
                similarity = 1 - distance
                return max(0.0, similarity)
            except ImportError:
                # 如果bhattacharyya不可用，使用替代方法
                import numpy as np
                distance = 1 - np.sum(np.sqrt(hist1 * hist2))
                return max(0.0, distance)
            
        except Exception:
            return 0.0

    def calculate_time_similarity(self, time1, time2) -> float:
        """计算时间相似度"""
        if not time1 or not time2:
            return 0.0
        
        try:
            if isinstance(time1, str) and isinstance(time2, str):
                dt1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
                dt2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
            else:
                dt1 = time1
                dt2 = time2
            
            # 计算时间差（小时）
            time_diff = abs((dt1 - dt2).total_seconds() / 3600)
            
            # 时间差越小，相似度越高
            if time_diff <= 1:  # 1小时内
                return 1.0
            elif time_diff <= 24:  # 24小时内
                return 0.8
            elif time_diff <= 168:  # 1周内
                return 0.6
            elif time_diff <= 720:  # 1月内
                return 0.4
            else:
                return 0.2
        except Exception:
            return 0.0

    def calculate_location_similarity(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """计算位置相似度"""
        if not all([lat1, lng1, lat2, lng2]):
            return 0.0
        
        try:
            from geopy.distance import geodesic
            
            # 计算地理距离（公里）
            distance = geodesic((lat1, lng1), (lat2, lng2)).kilometers
            
            # 距离越小，相似度越高
            if distance <= 0.1:  # 100米内
                return 1.0
            elif distance <= 1:  # 1公里内
                return 0.9
            elif distance <= 10:  # 10公里内
                return 0.7
            elif distance <= 100:  # 100公里内
                return 0.5
            else:
                return 0.2
        except Exception:
            return 0.0

    def _pre_screen_candidates(self, db_session, reference_photo: Photo) -> List[Photo]:
        """
        预筛选候选照片：基于时间和位置进行快速过滤
        显著减少需要进行详细相似度计算的照片数量
        """
        try:
            query = db_session.query(Photo).filter(Photo.id != reference_photo.id)

            # 时间预筛选（如果参考照片有拍摄时间）
            if reference_photo.taken_at:
                # 时间范围：从配置文件读取
                time_start = reference_photo.taken_at - timedelta(days=self.time_margin_days)
                time_end = reference_photo.taken_at + timedelta(days=self.time_margin_days)
                query = query.filter(Photo.taken_at.between(time_start, time_end))

            # 位置预筛选（如果参考照片有GPS信息）
            if reference_photo.location_lat and reference_photo.location_lng:
                # 位置范围：从配置文件读取
                lat_min = reference_photo.location_lat - self.location_margin
                lat_max = reference_photo.location_lat + self.location_margin
                lng_min = reference_photo.location_lng - self.location_margin
                lng_max = reference_photo.location_lng + self.location_margin
                query = query.filter(
                    Photo.location_lat.between(lat_min, lat_max),
                    Photo.location_lng.between(lng_min, lng_max)
                )

            # 如果都没有时间位置信息，至少保证有感知哈希（用于哈希相似度计算）
            if not (reference_photo.taken_at or (reference_photo.location_lat and reference_photo.location_lng)):
                query = query.filter(Photo.perceptual_hash.isnot(None))

            candidates = query.all()
            self.logger.debug(f"预筛选结果: {len(candidates)} 张候选照片 (原总数需实时计算)")

            return candidates

        except Exception as e:
            self.logger.warning(f"预筛选失败，使用全量照片: {str(e)}")
            # 降级策略：返回有感知哈希的所有照片
            return db_session.query(Photo).filter(
                Photo.id != reference_photo.id,
                Photo.perceptual_hash.isnot(None)
            ).all()

    def _get_photo_tags_from_db(self, db_session, photo_id: int) -> List[str]:
        """
        从数据库获取照片的基础标签（非AI分析标签）
        """
        try:
            from app.models.photo import Tag, PhotoTag
            # 查询照片关联的标签
            tags = db_session.query(Tag.name).join(PhotoTag).filter(PhotoTag.photo_id == photo_id).all()
            return [tag[0] for tag in tags]
        except Exception:
            return []

    def calculate_tags_similarity(self, tags1: List, tags2: List) -> float:
        """计算标签相似度（Jaccard）"""
        if not tags1 or not tags2:
            return 0.0
        
        set1 = set(tags1) if isinstance(tags1, list) else set()
        set2 = set(tags2) if isinstance(tags2, list) else set()
        
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def calculate_ai_tags_similarity(self, photo1: Photo, photo2: Photo, db_session=None) -> float:
        """计算AI标签相似度"""
        try:
            from app.models.photo import PhotoAnalysis
            
            if not db_session:
                from app.db.session import get_db
                db_session = next(get_db())
            
            # 查询AI分析结果
            analysis1 = db_session.query(PhotoAnalysis).filter(PhotoAnalysis.photo_id == photo1.id).first()
            analysis2 = db_session.query(PhotoAnalysis).filter(PhotoAnalysis.photo_id == photo2.id).first()
            
            if not analysis1 or not analysis2:
                return 0.0
            
            # 从analysis_result中提取tags
            result1 = analysis1.analysis_result if analysis1.analysis_result else {}
            result2 = analysis2.analysis_result if analysis2.analysis_result else {}
            
            tags1 = result1.get('tags', [])
            tags2 = result2.get('tags', [])
            
            # 调用标签相似度计算方法
            return self.calculate_tags_similarity(tags1, tags2)
            
        except Exception:
            return 0.0

    def find_first_layer_similar_photos(self, db_session, reference_photo_id: int, threshold: float = 0.5, limit: int = 8) -> List[Dict]:
        """
        第一层快速筛选相似照片（9种数据库相似度）
        """
        try:
            # 获取参考照片
            reference_photo = db_session.query(Photo).filter(Photo.id == reference_photo_id).first()
            if not reference_photo:
                return []

            # 预筛选：基于时间和位置快速过滤候选照片
            candidate_photos = self._pre_screen_candidates(db_session, reference_photo)

            # 只有预筛选后还有候选照片，才进行详细计算
            if not candidate_photos:
                return []

            candidates = []

            for photo in candidate_photos:
                similarities = {}

                # 第一层：快速特征计算（带阈值筛选）
                # 1. 感知哈希相似度（最重要，第一个检查）
                if reference_photo.perceptual_hash and photo.perceptual_hash:
                    hash_sim = self.calculate_perceptual_hash_similarity(reference_photo, photo)
                    similarities['perceptual_hash'] = hash_sim

                    # Early stopping: 如果感知哈希相似度太低，跳过这个候选照片
                    hash_threshold = self.DEFAULT_THRESHOLDS.get('perceptual_hash', 0.6)
                    if hash_sim < hash_threshold:
                        continue  # 跳过这个候选照片，不再计算其他特征

                # 2. 时间相似度
                if reference_photo.taken_at and photo.taken_at:
                    time_sim = self.calculate_time_similarity(reference_photo.taken_at, photo.taken_at)
                    similarities['time'] = time_sim

                    # Early stopping: 时间相似度太低
                    time_threshold = self.DEFAULT_THRESHOLDS.get('time', 0.8)
                    if time_sim < time_threshold:
                        continue

                # 3. 位置相似度
                if (reference_photo.location_lat and reference_photo.location_lng and
                    photo.location_lat and photo.location_lng):
                    location_sim = self.calculate_location_similarity(
                        reference_photo.location_lat, reference_photo.location_lng,
                        photo.location_lat, photo.location_lng
                    )
                    similarities['location'] = location_sim

                    # Early stopping: 位置相似度太低
                    location_threshold = self.DEFAULT_THRESHOLDS.get('location', 0.9)
                    if location_sim < location_threshold:
                        continue

                # 4. 相机相似度
                camera1 = {
                    'make': reference_photo.camera_make,
                    'model': reference_photo.camera_model,
                    'lens': reference_photo.lens_model,
                    'focal_length': reference_photo.focal_length,
                    'aperture': reference_photo.aperture
                }
                camera2 = {
                    'make': photo.camera_make,
                    'model': photo.camera_model,
                    'lens': photo.lens_model,
                    'focal_length': photo.focal_length,
                    'aperture': photo.aperture
                }
                camera_sim = self.calculate_camera_similarity(camera1, camera2)
                similarities['camera'] = camera_sim

                # AI特征计算（可选加分项，不参与Early stopping）
                try:
                    from app.models.photo import PhotoAnalysis
                    analysis1 = db_session.query(PhotoAnalysis).filter(PhotoAnalysis.photo_id == reference_photo.id).first()
                    analysis2 = db_session.query(PhotoAnalysis).filter(PhotoAnalysis.photo_id == photo.id).first()

                    # AI特征是可选的，即使没有AI分析数据也能继续
                    if analysis1 and analysis2:
                        result1 = analysis1.analysis_result if analysis1.analysis_result else {}
                        result2 = analysis2.analysis_result if analysis2.analysis_result else {}

                        # 场景类型相似度（可选加分）
                        scene1 = result1.get('scene_type', '')
                        scene2 = result2.get('scene_type', '')
                        if scene1 and scene2:
                            scene_sim = self.calculate_scene_type_similarity(scene1, scene2)
                            similarities['ai_scene'] = scene_sim

                        # 对象相似度（可选加分）
                        objects1 = result1.get('objects', [])
                        objects2 = result2.get('objects', [])
                        if objects1 and objects2:
                            objects_sim = self.calculate_objects_similarity(objects1, objects2)
                            similarities['ai_objects'] = objects_sim

                        # 情感相似度（可选加分）
                        emotion1 = result1.get('emotion', '')
                        emotion2 = result2.get('emotion', '')
                        if emotion1 and emotion2:
                            emotion_sim = self.calculate_emotion_similarity(emotion1, emotion2)
                            similarities['ai_emotion'] = emotion_sim

                        # 活动相似度（可选加分）
                        activity1 = result1.get('activity', '')
                        activity2 = result2.get('activity', '')
                        if activity1 and activity2:
                            activity_sim = self.calculate_activity_similarity(activity1, activity2)
                            similarities['ai_activity'] = activity_sim

                    # 无论是否有AI分析，都尝试计算基础标签相似度
                    # 这里使用数据库中的标签，而不是AI分析结果中的标签
                    # 因为大部分照片只有基础标签
                    try:
                        # 从数据库获取标签信息（基础分析产生的标签）
                        ref_tags = self._get_photo_tags_from_db(db_session, reference_photo.id)
                        cand_tags = self._get_photo_tags_from_db(db_session, photo.id)

                        if ref_tags and cand_tags:
                            tags_sim = self.calculate_tags_similarity(ref_tags, cand_tags)
                            similarities['basic_tags'] = tags_sim
                    except Exception:
                        pass

                except Exception:
                    pass

                # 如果通过了所有阈值检查，计算加权综合相似度
                if similarities:
                    # 使用配置的权重计算加权相似度
                    weighted_sim = 0.0
                    total_weight = 0.0

                    for feature, sim_value in similarities.items():
                        weight = self.SIMILARITY_WEIGHTS.get(feature, 0.0)
                        weighted_sim += sim_value * weight
                        total_weight += weight

                    # 如果有权重配置，使用加权平均；否则使用简单平均
                    if total_weight > 0:
                        first_layer_sim = weighted_sim / total_weight
                    else:
                        first_layer_sim = sum(similarities.values()) / len(similarities)

                    candidates.append({
                        'photo': photo,
                        'similarity': first_layer_sim,
                        'details': similarities
                    })
            
            # 按相似度排序
            candidates.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 应用最终的相似度阈值筛选
            final_threshold = self.similarity_threshold  # 从配置读取
            filtered_candidates = [c for c in candidates if c['similarity'] >= final_threshold]

            if filtered_candidates:
                # 返回指定数量的候选照片
                return filtered_candidates[:limit]
            else:
                # 如果没有达到阈值的候选，返回相似度最高的几个（降级策略）
                return candidates[:min(limit, len(candidates))] if candidates else []
            
        except Exception as e:
            print(f"第一层相似照片搜索失败: {e}")
            return []

    def find_second_layer_similar_photos(self, db_session, reference_photo: Photo, candidate_photos: List[Photo], threshold: float = 0.05) -> List[Dict]:
        """
        第二层精确匹配相似照片（3种复杂相似度）
        """
        try:
            final_results = []
            
            for photo in candidate_photos:
                complex_similarities = {}
                
                # 1. 颜色直方图相似度
                try:
                    color_sim = self.calculate_color_histogram_similarity(reference_photo, photo)
                    complex_similarities['color'] = color_sim
                except Exception:
                    complex_similarities['color'] = 0.0
                
                # 2. 结构相似度（SSIM）
                try:
                    ssim_sim = self.calculate_structural_similarity(reference_photo.original_path, photo.original_path)
                    complex_similarities['ssim'] = ssim_sim
                except Exception:
                    complex_similarities['ssim'] = 0.0
                
                # 3. AI描述相似度
                try:
                    # 从数据库获取AI分析结果
                    analysis1 = self.get_photo_analysis(reference_photo.id, db_session)
                    analysis2 = self.get_photo_analysis(photo.id, db_session)
                    
                    if analysis1 and analysis2:
                        desc1 = analysis1.get('description', '')
                        desc2 = analysis2.get('description', '')
                        description_sim = self.calculate_description_similarity(desc1, desc2)
                    else:
                        description_sim = 0.0
                    
                    complex_similarities['description'] = description_sim
                except Exception:
                    complex_similarities['description'] = 0.0
                
                # 计算第二层综合相似度
                if complex_similarities:
                    second_layer_sim = sum(complex_similarities.values()) / len(complex_similarities)
                    
                    if second_layer_sim > threshold:
                        final_results.append({
                            'photo': photo,
                            'similarity': second_layer_sim,
                            'details': complex_similarities
                        })
            
            # 按相似度排序
            final_results.sort(key=lambda x: x['similarity'], reverse=True)
            return final_results
            
        except Exception as e:
            print(f"第二层相似照片搜索失败: {e}")
            return []

    def calculate_combined_similarity(self, photo1: Photo, photo2: Photo, db_session=None) -> Dict[str, float]:
        """
        计算综合相似度分数（12种特征融合）
        
        :param photo1: 第一张照片
        :param photo2: 第二张照片
        :param db_session: 数据库会话
        :return: 包含各种相似度分数的字典
        """
        try:
            similarities = {}
            
            # 1. 传统图像相似度
            similarities['perceptual_hash'] = self.calculate_perceptual_hash_similarity(photo1, photo2)
            similarities['color_histogram'] = self.calculate_color_histogram_similarity(photo1, photo2)
            similarities['structural'] = self.calculate_structural_similarity(photo1.original_path, photo2.original_path)
            
            # 2. AI内容分析相似度
            analysis1 = self.get_photo_analysis(photo1.id, db_session)
            analysis2 = self.get_photo_analysis(photo2.id, db_session)
            
            if analysis1 and analysis2:
                similarities['scene_type'] = self.calculate_scene_type_similarity(
                    analysis1.get('scene_type'), analysis2.get('scene_type')
                )
                similarities['objects'] = self.calculate_objects_similarity(
                    analysis1.get('objects'), analysis2.get('objects')
                )
                similarities['emotion'] = self.calculate_emotion_similarity(
                    analysis1.get('emotion'), analysis2.get('emotion')
                )
                similarities['activity'] = self.calculate_activity_similarity(
                    analysis1.get('activity'), analysis2.get('activity')
                )
                similarities['description'] = self.calculate_description_similarity(
                    analysis1.get('description'), analysis2.get('description')
                )
                similarities['tags'] = self.calculate_tags_similarity(
                    analysis1.get('tags'), analysis2.get('tags')
                )
            else:
                # 如果AI分析结果不可用，使用默认值
                for key in ['scene_type', 'objects', 'emotion', 'activity', 'description', 'tags']:
                    similarities[key] = 0.0
            
            # 3. EXIF元数据相似度
            similarities['time'] = self.calculate_time_similarity(photo1.taken_at, photo2.taken_at)
            similarities['location'] = self.calculate_location_similarity(
                photo1.location_lat, photo1.location_lng,
                photo2.location_lat, photo2.location_lng
            )
            similarities['camera'] = self.calculate_camera_similarity(
                {
                    'make': photo1.camera_make,
                    'model': photo1.camera_model,
                    'lens': photo1.lens_model,
                    'focal_length': photo1.focal_length,
                    'aperture': photo1.aperture
                },
                {
                    'make': photo2.camera_make,
                    'model': photo2.camera_model,
                    'lens': photo2.lens_model,
                    'focal_length': photo2.focal_length,
                    'aperture': photo2.aperture
                }
            )
            
            # 4. 计算加权平均
            weighted_sum = sum(similarities[key] * self.SIMILARITY_WEIGHTS[key] for key in self.SIMILARITY_WEIGHTS)
            total_weight = sum(self.SIMILARITY_WEIGHTS[key] for key in self.SIMILARITY_WEIGHTS)
            
            combined_similarity = weighted_sum / total_weight if total_weight > 0 else 0.0
            
            # 5. 返回详细结果
            similarities['combined'] = combined_similarity
            return similarities
            
        except Exception as e:
            self.logger.error(f"计算综合相似度失败: {str(e)}")
            return {'combined': 0.0}


    def find_enhanced_similar_photos(self, db_session, reference_photo_id: int, 
                                   threshold: float = 0.55, limit: int = 20) -> List[Dict]:
        """
        使用增强算法搜索相似照片
        
        :param db_session: 数据库会话
        :param reference_photo_id: 参考照片ID
        :param threshold: 相似度阈值
        :param limit: 返回数量限制
        :return: 相似照片列表
        """
        try:
            # 获取参考照片
            reference_photo = db_session.query(Photo).filter(Photo.id == reference_photo_id).first()
            if not reference_photo:
                return []
            
            # 获取所有其他照片
            other_photos = db_session.query(Photo).filter(
                Photo.id != reference_photo_id,
                Photo.perceptual_hash.isnot(None)
            ).all()
            
            similar_photos = []
            
            for photo in other_photos:
                try:
                    # 计算综合相似度
                    similarities = self.calculate_combined_similarity(reference_photo, photo, db_session)
                    combined_sim = similarities['combined']
                    
                    # 检查是否满足阈值
                    if combined_sim >= threshold:
                        similar_photos.append({
                            'photo_id': photo.id,
                            'filename': photo.filename,
                            'file_path': photo.original_path,
                            'thumbnail_path': photo.thumbnail_path,
                            'similarity': combined_sim,
                            'similarities': similarities,
                            'taken_at': photo.taken_at,
                            'created_at': photo.created_at
                        })
                        
                except Exception as e:
                    self.logger.warning(f"计算照片 {photo.id} 相似度失败: {str(e)}")
                    continue
            
            # 按相似度排序
            similar_photos.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similar_photos[:limit]
            
        except Exception as e:
            self.logger.error(f"搜索增强相似照片失败: {str(e)}")
            raise Exception(f"搜索增强相似照片失败: {str(e)}")
