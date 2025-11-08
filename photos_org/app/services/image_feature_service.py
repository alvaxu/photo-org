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
        return Path(get_settings().storage.base_path).resolve()
    
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
                # 使用本地模型路径
                models_base_path = Path(self.config.models_base_path).resolve()
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
    
    def find_similar_photos_by_features(
        self,
        db_session: Session,
        reference_photo_id: int,
        threshold: float = 0.7,
        limit: int = 20
    ) -> List[Dict]:
        """
        基于特征向量搜索相似照片（向量化优化版本）
        
        使用numpy向量化计算，大幅提升大数据量下的搜索性能
        对于40000张照片，性能提升可达10-100倍
        
        :param db_session: 数据库会话
        :param reference_photo_id: 参考照片ID
        :param threshold: 相似度阈值（0-1）
        :param limit: 返回数量限制
        :return: 相似照片列表
        """
        try:
            # 获取参考照片
            reference_photo = db_session.query(Photo).filter(Photo.id == reference_photo_id).first()
            if not reference_photo:
                logger.error(f"参考照片 {reference_photo_id} 不存在")
                return []
            
            # 加载参考照片的特征向量
            reference_features = self.load_features_from_db(reference_photo)
            if reference_features is None:
                logger.warning(f"参考照片 {reference_photo_id} 没有特征向量")
                return []
            
            # 确保参考特征向量是numpy数组且为1D
            reference_features = np.array(reference_features).flatten()
            
            # 获取所有已提取特征的照片（排除参考照片）
            # 只查询必要的字段，减少内存占用
            photos_with_features = db_session.query(
                Photo.id,
                Photo.filename,
                Photo.original_path,
                Photo.thumbnail_path,
                Photo.image_features,
                Photo.taken_at,
                Photo.created_at
            ).filter(
                Photo.id != reference_photo_id,
                Photo.image_features_extracted == True,
                Photo.image_features.isnot(None)
            ).all()
            
            if not photos_with_features:
                return []
            
            # 批量加载所有特征向量到numpy矩阵（向量化优化 + 快速JSON解析）
            photo_ids = []
            photo_info = []  # 存储照片的其他信息
            feature_matrix = []
            
            # 批量解析JSON（使用快速JSON库）
            reference_dim = reference_features.shape[0]
            for photo in photos_with_features:
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
                    
                    photo_ids.append(photo.id)
                    photo_info.append({
                        'filename': photo.filename,
                        'file_path': photo.original_path,
                        'thumbnail_path': photo.thumbnail_path,
                        'taken_at': photo.taken_at,
                        'created_at': photo.created_at
                    })
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
            
            if not np.any(threshold_mask):
                return []
            
            # 获取满足条件的索引
            valid_indices = np.where(valid_mask)[0]
            threshold_indices = valid_indices[threshold_mask]
            threshold_similarities = similarities[threshold_mask]
            
            # 使用numpy的argsort进行排序（比Python排序快）
            sorted_indices = np.argsort(threshold_similarities)[::-1]  # 降序排序
            
            # 限制返回数量
            result_indices = sorted_indices[:limit]
            
            # 构建结果列表
            similar_photos = []
            for idx in result_indices:
                photo_idx = threshold_indices[idx]
                similar_photos.append({
                    'photo_id': photo_ids[photo_idx],
                    'filename': photo_info[photo_idx]['filename'],
                    'file_path': photo_info[photo_idx]['file_path'],
                    'thumbnail_path': photo_info[photo_idx]['thumbnail_path'],
                    'similarity': float(threshold_similarities[idx]),
                    'taken_at': photo_info[photo_idx]['taken_at'],
                    'created_at': photo_info[photo_idx]['created_at']
                })
            
            return similar_photos
            
        except Exception as e:
            logger.error(f"搜索相似照片失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []


# 全局服务实例
image_feature_service = ImageFeatureService()

