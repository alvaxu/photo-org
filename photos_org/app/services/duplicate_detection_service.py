"""
家庭版智能照片系统 - 重复检测服务
"""
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict
import math
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.photo import Photo, DuplicateGroup, DuplicateGroupPhoto

# 延迟导入重型库
imagehash = None
Image = None
np = None
HEIC_SUPPORT = False

def _lazy_import_dependencies():
    """延迟导入imagehash, PIL, numpy"""
    global imagehash, Image, np, HEIC_SUPPORT
    
    if imagehash is None:
        import imagehash
        from PIL import Image
        import numpy as np
        
        # 导入HEIC支持
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
            HEIC_SUPPORT = True
        except ImportError:
            HEIC_SUPPORT = False


class DuplicateDetectionService:
    """
    重复检测服务类
    使用感知哈希算法检测重复照片
    """

    def __init__(self):
        """初始化重复检测服务"""
        self.logger = get_logger(__name__)
        self.hash_size = 16  # 哈希大小，影响精确度

    def calculate_perceptual_hash(self, image_path: str) -> str:
        """
        计算图像的感知哈希值

        Args:
            image_path: 图像文件路径

        Returns:
            十六进制哈希字符串
        """
        # 延迟导入依赖
        _lazy_import_dependencies()
        
        try:
            # 打开图片并转换为灰度
            image = Image.open(image_path)

            # 转换为RGB模式（处理可能的调色板模式）
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # 计算感知哈希
            hash_value = imagehash.phash(image, hash_size=self.hash_size)

            # 转换为十六进制字符串
            hash_hex = str(hash_value)

            return hash_hex

        except Exception as e:
            self.logger.error(f"计算感知哈希失败 {image_path}: {str(e)}")
            raise Exception(f"计算感知哈希失败: {str(e)}")

    def calculate_hash_similarity(self, hash1: str, hash2: str) -> int:
        """
        计算两个哈希值的相似度

        Args:
            hash1: 第一个哈希值
            hash2: 第二个哈希值

        Returns:
            相似度分数（0-64，越小越相似）
        """
        # 延迟导入依赖
        _lazy_import_dependencies()
        
        try:
            # 将十六进制字符串转换为imagehash对象
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)

            # 计算汉明距离
            distance = h1 - h2

            return distance

        except Exception as e:
            self.logger.error(f"计算哈希相似度失败: {str(e)}")
            return 64  # 最大距离，表示完全不同

    def calculate_similarity_percentage(self, distance: int) -> float:
        """
        将汉明距离转换为相似度百分比

        Args:
            distance: 汉明距离

        Returns:
            相似度百分比
        """
        max_distance = self.hash_size * self.hash_size  # 256 for hash_size=16
        similarity = (max_distance - distance) / max_distance * 100
        return round(similarity, 2)

    def find_similar_photos(self, db_session, reference_photo_id: int, threshold: float = 0.8, limit: int = 20) -> List[Dict]:
        """
        搜索与指定照片相似的照片

        Args:
            db_session: 数据库会话
            reference_photo_id: 参考照片ID
            threshold: 相似度阈值 (0.0-1.0)
            limit: 返回数量限制

        Returns:
            相似照片列表，包含相似度信息
        """
        try:
            # 获取参考照片
            reference_photo = db_session.query(Photo).filter(Photo.id == reference_photo_id).first()
            if not reference_photo or not reference_photo.perceptual_hash:
                return []

            reference_hash = reference_photo.perceptual_hash
            
            # 根据实际hash长度动态计算max_distance
            # 16字符 = 64位 (hash_size=8, 8x8=64)
            # 64字符 = 256位 (hash_size=16, 16x16=256)
            hash_length = len(reference_hash)
            if hash_length == 16:
                # 16字符 = 64位
                max_distance = 64
            elif hash_length == 64:
                # 64字符 = 256位
                max_distance = 256
            else:
                # 其他长度，根据字符数估算（每个字符4位，但实际是hash_size^2）
                # 尝试反向计算hash_size: hash_size = sqrt(len(hash) * 4)
                estimated_bits = hash_length * 4
                estimated_hash_size = int(math.sqrt(estimated_bits))
                max_distance = estimated_hash_size * estimated_hash_size
                self.logger.warning(f"未知hash长度 {hash_length}，估算max_distance={max_distance}")
            
            # 将阈值转换为汉明距离
            hamming_threshold = int(max_distance * (1 - threshold))

            # 获取所有有感知哈希的照片（排除参考照片）
            photos_with_hash = db_session.query(Photo).filter(
                Photo.id != reference_photo_id,
                Photo.perceptual_hash.isnot(None),
                Photo.perceptual_hash != ''
            ).all()

            similar_photos = []

            for photo in photos_with_hash:
                try:
                    # 检查hash长度是否一致（不同长度的hash不能比较）
                    if len(photo.perceptual_hash) != hash_length:
                        continue
                    
                    # 计算汉明距离
                    distance = self._calculate_hamming_distance(reference_hash, photo.perceptual_hash)
                    
                    # 检查是否满足相似度阈值
                    if distance <= hamming_threshold:
                        similarity = (max_distance - distance) / max_distance
                        similar_photos.append({
                            'photo_id': photo.id,
                            'filename': photo.filename,
                            'file_path': photo.original_path,
                            'thumbnail_path': photo.thumbnail_path,
                            'similarity': similarity,
                            'hamming_distance': distance,
                            'taken_at': photo.taken_at,
                            'created_at': photo.created_at
                        })
                except Exception as e:
                    self.logger.warning(f"计算照片 {photo.id} 相似度失败: {str(e)}")
                    continue

            # 按相似度排序（降序）
            similar_photos.sort(key=lambda x: x['similarity'], reverse=True)

            # 限制返回数量
            return similar_photos[:limit]

        except Exception as e:
            self.logger.error(f"搜索相似照片失败: {str(e)}")
            raise Exception(f"搜索相似照片失败: {str(e)}")

    def _calculate_hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        计算两个感知哈希之间的汉明距离

        Args:
            hash1: 第一个哈希值（16进制字符串）
            hash2: 第二个哈希值（16进制字符串）

        Returns:
            汉明距离
        """
        try:
            # 延迟导入依赖
            _lazy_import_dependencies()
            
            # 使用imagehash库正确计算汉明距离（支持不同长度的hash）
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            
            # 直接相减得到汉明距离
            return h1 - h2
        except Exception as e:
            self.logger.error(f"计算汉明距离失败: {str(e)}")
            return float('inf')  # 返回无穷大表示无法计算

