"""
图像特征提取服务

基于ResNet50模型提取图像特征向量

## 功能特点：
1. 延迟加载PyTorch和ResNet50模型
2. 支持本地模型和在线模型
3. 支持HEIC格式（通过PIL）
4. 提取2048维特征向量
5. 自动L2归一化

## 与其他版本的不同点：
- 参考人脸识别服务的架构设计
- 使用异步处理提高性能
- 支持批量特征提取
"""

import asyncio
import json
import logging
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime
import numpy as np
import imagehash  # 用于perceptual_hash相似度计算

# 延迟导入重型库
torch = None
torchvision = None
PIL = None
Image = None
transforms = None
models = None
HEIC_SUPPORT = False
orjson = None  # 快速JSON库

def _lazy_import_dependencies():
    """延迟导入重型库"""
    global torch, torchvision, PIL, Image, transforms, models, HEIC_SUPPORT, orjson
    
    if torch is None:
        try:
            import torch
            import torchvision
            from torchvision import models, transforms
            from PIL import Image
            import PIL
            logging.info("✅ 成功加载图像特征提取依赖库")
            
            # HEIC支持
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
                HEIC_SUPPORT = True
            except ImportError:
                HEIC_SUPPORT = False
                logging.warning("pillow-heif未安装，HEIC格式支持受限")
                
        except ImportError as e:
            logging.error(f"图像特征提取依赖导入失败: {e}")
    
    # 延迟导入orjson（快速JSON库）
    # 注意：orjson会在首次使用时自动导入（在_fast_json_loads/_fast_json_dumps中）
    # 这里不强制导入，允许系统在orjson不可用时继续运行

from app.core.config import settings
from app.db.session import get_db
from app.models.photo import Photo
from app.core.logging import get_logger
from sqlalchemy.orm import Session

logger = get_logger(__name__)


def _fast_json_loads(json_str: str) -> list:
    """
    快速JSON解析（使用orjson，如果可用）
    
    :param json_str: JSON字符串
    :return: 解析后的Python对象
    """
    global orjson
    
    # 如果orjson还未导入，尝试导入
    if orjson is None:
        try:
            import orjson
            logger.debug("成功加载orjson快速JSON库")
        except ImportError:
            orjson = False  # 标记为不可用，避免重复尝试
            return json.loads(json_str)
    
    # 如果orjson可用，使用它
    if orjson is not False:
        try:
            return orjson.loads(json_str)
        except Exception as e:
            logger.warning(f"orjson解析失败，回退到标准json: {str(e)}")
            return json.loads(json_str)
    else:
        return json.loads(json_str)


def _fast_json_dumps(obj) -> str:
    """
    快速JSON序列化（使用orjson，如果可用）
    
    :param obj: 要序列化的Python对象
    :return: JSON字符串
    """
    global orjson
    
    # 如果orjson还未导入，尝试导入
    if orjson is None:
        try:
            import orjson
            logger.debug("成功加载orjson快速JSON库")
        except ImportError:
            orjson = False  # 标记为不可用，避免重复尝试
            return json.dumps(obj, separators=(',', ':'))
    
    # 如果orjson可用，使用它
    if orjson is not False:
        try:
            # orjson返回bytes，需要解码为字符串
            return orjson.dumps(obj, option=orjson.OPT_SERIALIZE_NUMPY).decode('utf-8')
        except Exception as e:
            logger.warning(f"orjson序列化失败，回退到标准json: {str(e)}")
            return json.dumps(obj, separators=(',', ':'))
    else:
        return json.dumps(obj, separators=(',', ':'))


class ImageFeatureService:
    """图像特征提取服务类"""
    
    def __init__(self):
        """初始化图像特征提取服务"""
        self.model = None
        self.preprocess = None
        self.is_initialized = False
        self.config = settings.image_features
        # 注意：不再在 __init__ 中固定 storage_base，改为动态读取
    
    @property
    def storage_base(self) -> Path:
        """动态获取存储基础路径（每次使用时读取最新配置）"""
        from app.core.config import get_settings
        from app.core.path_utils import resolve_resource_path
        return resolve_resource_path(get_settings().storage.base_path)
    
    def _get_full_path(self, image_path: str) -> Path:
        """
        构建完整的文件路径
        
        :param image_path: 相对路径或绝对路径
        :return: 完整路径
        """
        path = Path(image_path)
        if path.is_absolute():
            return path
        return self.storage_base / image_path
    
    async def initialize(self) -> bool:
        """
        初始化ResNet50模型
        
        :return: 是否初始化成功
        """
        # 延迟导入依赖
        _lazy_import_dependencies()
        
        try:
            if not torch:
                logger.error("PyTorch未安装，无法启用图像特征提取")
                return False
            
            if not self.config.enabled:
                logger.info("图像特征提取功能已禁用")
                return False
            
            logger.info("🔄 正在初始化ResNet50模型...")
            
            # 根据配置决定使用本地模型还是在线模型
            if self.config.use_local_model:
                # 使用本地模型路径（使用统一的路径解析函数）
                from app.core.path_utils import resolve_resource_path
                models_base_path = resolve_resource_path(self.config.models_base_path)
                model_file_path = models_base_path / self.config.model_file
                logger.info(f"使用本地模型路径: {model_file_path}")
                
                if not model_file_path.exists():
                    logger.error(f"本地模型文件不存在: {model_file_path}")
                    return False
                
                # 加载ResNet50模型
                # 先创建完整的模型结构
                model = models.resnet50(weights=None)
                
                # 从本地文件加载预训练权重
                state_dict = torch.load(str(model_file_path), map_location='cpu')
                model.load_state_dict(state_dict)
                logger.info("✅ 成功从本地文件加载模型权重")
            else:
                # 使用预训练模型（在线下载）
                logger.info(f"使用预训练模型: {self.config.model}")
                model = models.resnet50(weights='IMAGENET1K_V2')
            
            # 移除分类层，只保留特征提取部分
            # 移除最后两层：avgpool和fc
            backbone = torch.nn.Sequential(*list(model.children())[:-2])
            
            # 添加全局平均池化层，将特征图转换为向量
            # 结构：backbone -> AdaptiveAvgPool2d -> Flatten
            self.model = torch.nn.Sequential(
                backbone,
                torch.nn.AdaptiveAvgPool2d((1, 1)),  # 全局平均池化：7x7 -> 1x1
                torch.nn.Flatten()  # 展平：1x1x2048 -> 2048
            )
            
            # 设置为评估模式
            self.model.eval()
            
            # 定义图像预处理
            self.preprocess = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            
            self.is_initialized = True
            logger.info("✅ ResNet50模型初始化成功，已就绪")
            return True
            
        except Exception as e:
            logger.error(f"ResNet50模型初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_features(self, image_path: str) -> Optional[np.ndarray]:
        """
        提取单张照片的特征向量
        
        :param image_path: 照片路径（相对或绝对）
        :return: 特征向量（2048维，已归一化），失败返回None
        """
        if not self.is_initialized:
            logger.error("模型未初始化")
            return None
        
        try:
            full_path = self._get_full_path(image_path)
            
            if not full_path.exists():
                logger.error(f"照片文件不存在: {full_path}")
                return None
            
            # 加载图像（支持HEIC）
            if full_path.suffix.lower() in ['.heic', '.heif'] and HEIC_SUPPORT:
                from pillow_heif import read_heif
                heif_file = read_heif(full_path)
                image = Image.frombytes(
                    heif_file.mode,
                    heif_file.size,
                    heif_file.data,
                    "raw",
                    heif_file.mode,
                    heif_file.stride,
                )
            else:
                image = Image.open(full_path)
            
            # 转换为RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 预处理并添加批次维度
            input_tensor = self.preprocess(image)
            input_batch = input_tensor.unsqueeze(0)
            
            # 提取特征（模型已包含全局平均池化和展平）
            with torch.no_grad():
                feature = self.model(input_batch)  # [1, 2048]
            
            # 移除batch维度并转换为numpy
            feature = feature.squeeze(0)  # [2048]
            feature_vector = feature.numpy()
            
            # L2归一化
            feature_vector = feature_vector / np.linalg.norm(feature_vector)
            
            return feature_vector
            
        except Exception as e:
            logger.error(f"提取特征失败 {image_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_features_to_db(self, photo_id: int, features: np.ndarray, db_session: Session) -> bool:
        """
        保存特征向量到数据库
        
        :param photo_id: 照片ID
        :param features: 特征向量（numpy数组）
        :param db_session: 数据库会话
        :return: 是否保存成功
        """
        try:
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                logger.error(f"照片 {photo_id} 不存在")
                return False
            
            # 序列化为JSON（使用快速JSON库）
            features_json = _fast_json_dumps(features.tolist())
            
            # 更新数据库
            photo.image_features = features_json
            photo.image_features_extracted = True
            photo.image_features_extracted_at = datetime.now()
            
            db_session.commit()
            logger.debug(f"✅ 特征向量已保存到数据库 (photo_id: {photo_id})")
            return True
            
        except Exception as e:
            logger.error(f"保存特征向量失败 {photo_id}: {str(e)}")
            db_session.rollback()
            import traceback
            traceback.print_exc()
            return False
    
    def batch_save_features_to_db(self, features_data: List[Dict], db_session: Session) -> int:
        """
        批量保存特征向量到数据库
        
        :param features_data: 特征数据列表，每个元素包含 {'photo_id': int, 'features': np.ndarray}
        :param db_session: 数据库会话
        :return: 成功保存的数量
        """
        if not features_data:
            return 0
        
        try:
            # 获取所有照片ID
            photo_ids = [item['photo_id'] for item in features_data]
            photos = db_session.query(Photo).filter(Photo.id.in_(photo_ids)).all()
            photo_dict = {photo.id: photo for photo in photos}
            
            saved_count = 0
            current_time = datetime.now()
            
            for item in features_data:
                photo_id = item['photo_id']
                features = item['features']
                
                photo = photo_dict.get(photo_id)
                if not photo:
                    logger.warning(f"照片 {photo_id} 不存在，跳过保存")
                    continue
                
                try:
                    # 序列化为JSON
                    features_json = json.dumps(features.tolist(), separators=(',', ':'))
                    
                    # 更新数据库
                    photo.image_features = features_json
                    photo.image_features_extracted = True
                    photo.image_features_extracted_at = current_time
                    
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存照片 {photo_id} 特征向量失败: {str(e)}")
                    continue
            
            # 批量提交
            db_session.commit()
            logger.info(f"✅ 批量保存 {saved_count}/{len(features_data)} 个特征向量到数据库")
            return saved_count
            
        except Exception as e:
            logger.error(f"批量保存特征向量失败: {str(e)}")
            db_session.rollback()
            import traceback
            traceback.print_exc()
            return 0
    
    def load_features_from_db(self, photo: Photo) -> Optional[np.ndarray]:
        """
        从数据库加载特征向量
        
        :param photo: 照片对象
        :return: 特征向量（numpy数组），失败返回None
        """
        try:
            if not photo.image_features:
                return None
            
            # 反序列化JSON（使用快速JSON库）
            features_list = _fast_json_loads(photo.image_features)
            features = np.array(features_list)
            
            return features
            
        except Exception as e:
            logger.error(f"加载特征向量失败 {photo.id}: {str(e)}")
            return None
    
    def calculate_cosine_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        计算两个特征向量的余弦相似度
        
        :param features1: 第一个特征向量
        :param features2: 第二个特征向量
        :return: 相似度（0-1）
        """
        try:
            # 计算余弦相似度
            dot_product = np.dot(features1, features2)
            norm1 = np.linalg.norm(features1)
            norm2 = np.linalg.norm(features2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算余弦相似度失败: {str(e)}")
            return 0.0
    
    def _calculate_perceptual_hash_similarity(self, hash1: str, hash2: str) -> float:
        """
        计算两个perceptual_hash的相似度（优化版本：直接计算汉明距离，避免hash对象转换）
        
        :param hash1: 第一个哈希值（16进制字符串）
        :param hash2: 第二个哈希值（16进制字符串）
        :return: 相似度（0-1）
        """
        try:
            if not hash1 or not hash2:
                return 0.0
            
            # 检查哈希长度是否一致
            if len(hash1) != len(hash2):
                return 0.0
            
            # 优化：直接计算汉明距离，避免hash对象转换
            # 将16进制字符串转换为整数，然后使用XOR计算汉明距离
            try:
                # 转换为整数
                int1 = int(hash1, 16)
                int2 = int(hash2, 16)
                
                # 使用XOR计算不同位，然后统计1的个数（汉明距离）
                xor_result = int1 ^ int2
                # 使用最快的位计数方法（Python 3.10+有bit_count()，否则使用bin().count()）
                if hasattr(int, 'bit_count'):
                    hamming_dist = xor_result.bit_count()
                else:
                    hamming_dist = bin(xor_result).count('1')
            except ValueError:
                # 如果转换失败，回退到使用imagehash库
                h1 = imagehash.hex_to_hash(hash1)
                h2 = imagehash.hex_to_hash(hash2)
                hamming_dist = h1 - h2
            
            # 根据哈希长度设置最大距离
            # perceptual_hash通常是16个字符的16进制字符串，每个字符4位，总共64位
            max_distance = len(hash1) * 4  # 每个字符4位
            if max_distance == 0:
                return 0.0
            
            # 转换为相似度（0-1）
            similarity = max(0.0, 1 - (hamming_dist / max_distance))
            return similarity
            
        except Exception as e:
            logger.warning(f"计算perceptual_hash相似度失败: {str(e)}")
            return 0.0
    
    def find_similar_photos_by_features(
        self,
        db_session: Session,
        reference_photo_id: int,
        threshold: float = 0.7,
        limit: int = 20
    ) -> List[Dict]:
        """
        基于特征向量搜索相似照片（向量化优化版本 + perceptual_hash预筛选）
        
        使用perceptual_hash进行预筛选，大幅减少需要计算特征向量相似度的照片数量
        然后使用numpy向量化计算，进一步提升大数据量下的搜索性能
        对于40000张照片，性能提升可达5-10倍
        
        :param db_session: 数据库会话
        :param reference_photo_id: 参考照片ID
        :param threshold: 相似度阈值（0-1）
        :param limit: 返回数量限制
        :return: 相似照片列表
        """
        try:
            logger.info(f"[特征分析相似搜索] 开始搜索相似照片，参考照片ID: {reference_photo_id}, 阈值: {threshold}, 限制: {limit}")
            
            # 获取参考照片（需要包含perceptual_hash字段）
            reference_photo = db_session.query(Photo).filter(Photo.id == reference_photo_id).first()
            if not reference_photo:
                logger.error(f"[特征分析相似搜索] 参考照片 {reference_photo_id} 不存在")
                return []
            
            # 检查参考照片是否有perceptual_hash（预筛选必需）
            if not reference_photo.perceptual_hash:
                logger.warning(f"[特征分析相似搜索] 参考照片 {reference_photo_id} 没有perceptual_hash，无法使用预筛选优化")
                # 可以选择降级到不使用预筛选，但为了保持一致性，返回空结果
                # 提示用户先进行基础分析以生成perceptual_hash
                return []
            
            # 加载参考照片的特征向量
            reference_features = self.load_features_from_db(reference_photo)
            if reference_features is None:
                logger.warning(f"参考照片 {reference_photo_id} 没有特征向量")
                return []
            
            # 确保参考特征向量是numpy数组且为1D
            reference_features = np.array(reference_features).flatten()
            
            # 从配置文件读取perceptual_hash预筛选阈值（复用智能分析的配置）
            hash_threshold = settings.similarity.first_layer_thresholds.get('perceptual_hash', 0.4)
            logger.info(f"[特征分析相似搜索] 使用perceptual_hash预筛选阈值: {hash_threshold}")
            
            # 获取所有已提取特征且有perceptual_hash的照片（排除参考照片）
            # 查询完整的Photo对象，以便在API层直接使用
            photos_with_features = db_session.query(Photo).filter(
                Photo.id != reference_photo_id,
                Photo.image_features_extracted == True,
                Photo.image_features.isnot(None),
                Photo.perceptual_hash.isnot(None),  # 用于预筛选
                Photo.perceptual_hash != ''  # 排除空字符串
            ).all()
            
            logger.info(f"[特征分析相似搜索] 查询到有特征向量和perceptual_hash的照片数: {len(photos_with_features)}")
            
            if not photos_with_features:
                logger.info("[特征分析相似搜索] 没有符合条件的候选照片")
                return []
            
            # perceptual_hash预筛选：先快速过滤掉明显不相似的照片
            logger.info(f"[特征分析相似搜索] 开始perceptual_hash预筛选，候选照片数: {len(photos_with_features)}")
            reference_hash = reference_photo.perceptual_hash
            pre_screened_photos = []
            
            for photo in photos_with_features:
                # 计算perceptual_hash相似度
                hash_sim = self._calculate_perceptual_hash_similarity(reference_hash, photo.perceptual_hash)
                
                # 如果相似度低于阈值，跳过该照片（不再进行特征向量计算）
                if hash_sim < hash_threshold:
                    continue
                
                # 通过预筛选，保留该照片
                pre_screened_photos.append(photo)
            
            filter_rate = (1 - len(pre_screened_photos) / len(photos_with_features)) * 100 if photos_with_features else 0
            logger.info(f"[特征分析相似搜索] perceptual_hash预筛选完成，通过筛选: {len(pre_screened_photos)}/{len(photos_with_features)} (过滤率: {filter_rate:.1f}%)")
            
            if not pre_screened_photos:
                logger.info("[特征分析相似搜索] 预筛选后没有符合条件的照片")
                return []
            
            # 批量加载所有通过预筛选的照片的特征向量到numpy矩阵（向量化优化 + 快速JSON解析）
            photo_objects = []  # 存储Photo对象引用
            feature_matrix = []
            
            # 批量解析JSON（使用快速JSON库）
            reference_dim = reference_features.shape[0]
            logger.info(f"[特征分析相似搜索] 开始加载特征向量，照片数: {len(pre_screened_photos)}")
            for photo in pre_screened_photos:
                try:
                    # 跳过空的特征向量
                    if not photo.image_features:
                        continue
                    
                    # 使用快速JSON解析（orjson比标准json快3-5倍）
                    features_list = _fast_json_loads(photo.image_features)
                    features = np.array(features_list, dtype=np.float32).flatten()
                    
                    # 验证特征向量维度
                    if features.shape[0] != reference_dim:
                        logger.warning(f"照片 {photo.id} 特征向量维度不匹配: {features.shape[0]} vs {reference_dim}")
                        continue
                    
                    # 保留Photo对象引用
                    photo_objects.append(photo)
                    feature_matrix.append(features)
                    
                except Exception as e:
                    logger.warning(f"加载照片 {photo.id} 特征向量失败: {str(e)}")
                    continue
            
            if not feature_matrix:
                return []
            
            # 转换为numpy矩阵（N x feature_dim）
            # 使用float32减少内存占用（2048维特征向量，float32足够精确）
            feature_matrix = np.array(feature_matrix, dtype=np.float32)
            
            # 向量化计算所有余弦相似度（一次性计算，避免循环）
            # 参考向量归一化
            ref_norm = np.linalg.norm(reference_features)
            if ref_norm == 0:
                logger.warning("参考特征向量为零向量")
                return []
            
            # 计算所有照片特征向量的L2范数
            feature_norms = np.linalg.norm(feature_matrix, axis=1)
            
            # 避免除零错误
            valid_mask = feature_norms > 0
            if not np.any(valid_mask):
                return []
            
            # 计算点积（矩阵乘法：N x feature_dim @ feature_dim = N）
            dot_products = np.dot(feature_matrix[valid_mask], reference_features)
            
            # 计算余弦相似度（向量化）
            similarities = dot_products / (feature_norms[valid_mask] * ref_norm)
            
            # 筛选满足阈值的结果
            threshold_mask = similarities >= threshold
            
            # 获取满足条件的索引
            valid_indices = np.where(valid_mask)[0]
            
            if not np.any(threshold_mask):
                # 降级策略：如果没有满足阈值的照片，返回相似度最高的1张
                if len(valid_indices) > 0:
                    # 对所有有效照片按相似度排序
                    all_similarities = similarities[valid_mask]
                    sorted_indices = np.argsort(all_similarities)[::-1]  # 降序排序
                    # 只取相似度最高的1张
                    top_idx = valid_indices[sorted_indices[0]]
                    similar_photos = [{
                        'photo': photo_objects[top_idx],
                        'similarity': float(all_similarities[sorted_indices[0]])
                    }]
                    logger.info(f"[特征分析相似搜索] 没有满足阈值的照片，降级返回相似度最高的1张（相似度: {all_similarities[sorted_indices[0]]:.3f}）")
                    return similar_photos
                else:
                    return []
            
            threshold_indices = valid_indices[threshold_mask]
            threshold_similarities = similarities[threshold_mask]
            
            # 使用numpy的argsort进行排序（比Python排序快）
            sorted_indices = np.argsort(threshold_similarities)[::-1]  # 降序排序
            
            # 限制返回数量
            result_indices = sorted_indices[:limit]
            
            # 构建结果列表（返回包含Photo对象的字典，与智能搜索格式一致）
            similar_photos = []
            for idx in result_indices:
                photo_idx = threshold_indices[idx]
                similar_photos.append({
                    'photo': photo_objects[photo_idx],  # 保留Photo对象引用
                    'similarity': float(threshold_similarities[idx])
                })
            
            logger.info(f"[特征分析相似搜索] 搜索完成，找到 {len(similar_photos)} 张相似照片（阈值: {threshold}）")
            return similar_photos
            
        except Exception as e:
            logger.error(f"搜索相似照片失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []


# 全局服务实例
image_feature_service = ImageFeatureService()

