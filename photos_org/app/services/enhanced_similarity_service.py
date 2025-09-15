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
from datetime import datetime
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
        self.logger = get_logger(__name__)
        self.hash_size = 16
        self.similarity_threshold = 0.55
        
        # 相似度权重配置
        self.SIMILARITY_WEIGHTS = {
            # 传统图像相似度
            'perceptual_hash': 0.25,      # 感知哈希
            'color_histogram': 0.15,      # 颜色直方图
            'structural': 0.10,           # 结构相似度
            
            # AI内容分析相似度
            'scene_type': 0.10,           # 场景类型
            'objects': 0.15,              # 对象
            'emotion': 0.05,              # 情感
            'activity': 0.05,             # 活动
            'description': 0.10,          # 描述
            'tags': 0.05,                 # 标签
            
            # EXIF元数据相似度
            'time': 0.15,                 # 时间
            'location': 0.10,             # 位置
            'camera': 0.05                # 相机参数
        }
        
        # 默认阈值
        self.DEFAULT_THRESHOLDS = {
            'perceptual_hash': 0.6,      # 感知哈希阈值
            'color_histogram': 0.7,      # 颜色直方图阈值
            'structural': 0.8,           # 结构相似度阈值
            'scene_type': 1.0,           # 场景类型阈值
            'objects': 0.5,              # 对象相似度阈值
            'emotion': 0.6,              # 情感相似度阈值
            'activity': 0.6,             # 活动相似度阈值
            'description': 0.5,          # 描述相似度阈值
            'tags': 0.5,                 # 标签相似度阈值
            'time': 0.8,                 # 时间相似度阈值
            'location': 0.9,             # 位置相似度阈值
            'camera': 0.7,               # 相机参数阈值
            'combined': 0.55             # 综合相似度阈值
        }

    def calculate_multiple_hashes(self, image_path: str) -> Dict[str, str]:
        """
        计算多种类型的哈希值
        
        :param image_path: 图像文件路径
        :return: 包含多种哈希值的字典
        """
        try:
            image = Image.open(image_path)
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
        
        :param image_path: 图像文件路径
        :return: 颜色直方图特征向量
        """
        try:
            # 使用OpenCV读取图像
            image = cv2.imread(image_path)
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
        
        :param image_path1: 第一张图像路径
        :param image_path2: 第二张图像路径
        :return: 结构相似性分数 (0-1)
        """
        try:
            # 读取图像
            img1 = cv2.imread(image_path1, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(image_path2, cv2.IMREAD_GRAYSCALE)
            
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
            
            # 获取所有其他照片
            all_photos = db_session.query(Photo).filter(Photo.id != reference_photo_id).all()
            
            candidates = []
            
            for photo in all_photos:
                similarities = {}
                
                # 1. 时间相似度
                if reference_photo.taken_at and photo.taken_at:
                    time_sim = self.calculate_time_similarity(reference_photo.taken_at, photo.taken_at)
                    similarities['time'] = time_sim
                
                # 2. 位置相似度
                if (reference_photo.location_lat and reference_photo.location_lng and 
                    photo.location_lat and photo.location_lng):
                    location_sim = self.calculate_location_similarity(
                        reference_photo.location_lat, reference_photo.location_lng,
                        photo.location_lat, photo.location_lng
                    )
                    similarities['location'] = location_sim
                
                # 3. 相机相似度
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
                
                # 4. 感知哈希相似度
                if reference_photo.perceptual_hash and photo.perceptual_hash:
                    hash_sim = self.calculate_perceptual_hash_similarity(reference_photo, photo)
                    similarities['perceptual_hash'] = hash_sim
                
                # 5-9. AI分析相似度（查询数据库）
                try:
                    from app.models.photo import PhotoAnalysis
                    analysis1 = db_session.query(PhotoAnalysis).filter(PhotoAnalysis.photo_id == reference_photo.id).first()
                    analysis2 = db_session.query(PhotoAnalysis).filter(PhotoAnalysis.photo_id == photo.id).first()
                    
                    if analysis1 and analysis2:
                        result1 = analysis1.analysis_result if analysis1.analysis_result else {}
                        result2 = analysis2.analysis_result if analysis2.analysis_result else {}
                        
                        # 场景类型相似度
                        scene1 = result1.get('scene_type', '')
                        scene2 = result2.get('scene_type', '')
                        if scene1 and scene2:
                            similarities['ai_scene'] = self.calculate_scene_type_similarity(scene1, scene2)
                        
                        # 对象相似度
                        objects1 = result1.get('objects', [])
                        objects2 = result2.get('objects', [])
                        if objects1 and objects2:
                            similarities['ai_objects'] = self.calculate_objects_similarity(objects1, objects2)
                        
                        # 情感相似度
                        emotion1 = result1.get('emotion', '')
                        emotion2 = result2.get('emotion', '')
                        if emotion1 and emotion2:
                            similarities['ai_emotion'] = self.calculate_emotion_similarity(emotion1, emotion2)
                        
                        # 活动相似度
                        activity1 = result1.get('activity', '')
                        activity2 = result2.get('activity', '')
                        if activity1 and activity2:
                            similarities['ai_activity'] = self.calculate_activity_similarity(activity1, activity2)
                        
                        # 标签相似度
                        tags1 = result1.get('tags', [])
                        tags2 = result2.get('tags', [])
                        if tags1 and tags2:
                            similarities['ai_tags'] = self.calculate_tags_similarity(tags1, tags2)
                
                except Exception:
                    pass
                
                # 计算第一层综合相似度
                if similarities:
                    first_layer_sim = sum(similarities.values()) / len(similarities)
                    candidates.append({
                        'photo': photo,
                        'similarity': first_layer_sim,
                        'details': similarities
                    })
            
            # 按相似度排序
            candidates.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 应用新的筛选逻辑
            # 1. 先筛选出相似度 > 0.5 的照片
            high_similarity = [c for c in candidates if c['similarity'] > 0.5]
            
            if high_similarity:
                # 如果有关似度 > 0.5 的照片，最多返回8张
                return high_similarity[:8]
            else:
                # 如果没有相似度 > 0.5 的照片，返回相似度最高的1张
                return candidates[:1] if candidates else []
            
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
