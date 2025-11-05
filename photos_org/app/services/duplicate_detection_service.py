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
        from app.core.config import settings
        self.logger = get_logger(__name__)
        self.hash_size = 16  # 哈希大小，影响精确度
        self.similarity_threshold = settings.analysis.duplicate_threshold  # 从配置获取相似度阈值

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

    def find_duplicates_in_photos(self, photo_paths: List[str]) -> Dict[str, List[Tuple[str, int]]]:
        """
        在一组照片中查找重复项

        Args:
            photo_paths: 照片文件路径列表

        Returns:
            重复组字典，key为代表照片路径，value为相似照片列表(路径,相似度)
        """
        try:
            # 计算所有照片的哈希
            photo_hashes = {}
            for path in photo_paths:
                try:
                    hash_value = self.calculate_perceptual_hash(path)
                    photo_hashes[path] = hash_value
                except Exception as e:
                    self.logger.warning(f"跳过无法处理的照片 {path}: {str(e)}")
                    continue

            # 查找相似照片
            duplicate_groups = defaultdict(list)

            processed_paths = list(photo_hashes.keys())

            for i, path1 in enumerate(processed_paths):
                group_found = False

                for j, path2 in enumerate(processed_paths):
                    if i >= j:  # 避免重复比较
                        continue

                    distance = self.calculate_hash_similarity(
                        photo_hashes[path1],
                        photo_hashes[path2]
                    )

                    if distance <= self.similarity_threshold:
                        # 找到相似照片
                        if not group_found:
                            # 以第一张照片作为组的代表
                            duplicate_groups[path1].append((path2, distance))
                            group_found = True
                        else:
                            # 添加到现有组中
                            duplicate_groups[path1].append((path2, distance))

            return dict(duplicate_groups)

        except Exception as e:
            self.logger.error(f"查找重复照片失败: {str(e)}")
            return {}

    def detect_duplicates_for_photo(self, photo_id: int, db_session) -> Dict[str, Any]:
        """
        为指定照片检测重复项

        Args:
            photo_id: 照片ID
            db_session: 数据库会话

        Returns:
            重复检测结果
        """
        try:
            # 获取目标照片
            target_photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            if not target_photo:
                raise Exception("照片不存在")

            if not target_photo.perceptual_hash:
                raise Exception("照片缺少感知哈希值")

            # 获取所有其他照片
            other_photos = db_session.query(Photo).filter(
                Photo.id != photo_id,
                Photo.perceptual_hash.isnot(None)
            ).all()

            duplicates = []
            for photo in other_photos:
                distance = self.calculate_hash_similarity(
                    target_photo.perceptual_hash,
                    photo.perceptual_hash
                )

                if distance <= self.similarity_threshold:
                    similarity_score = (64 - distance) / 64 * 100  # 转换为百分比

                    duplicates.append({
                        "photo_id": photo.id,
                        "filename": photo.filename,
                        "similarity_score": round(similarity_score, 2),
                        "distance": distance
                    })

            # 按相似度排序
            duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)

            return {
                "target_photo_id": photo_id,
                "target_filename": target_photo.filename,
                "duplicate_count": len(duplicates),
                "duplicates": duplicates[:10],  # 最多返回10个重复项
                "similarity_threshold": self.similarity_threshold
            }

        except Exception as e:
            self.logger.error(f"为照片{photo_id}检测重复项失败: {str(e)}")
            raise Exception(f"重复检测失败: {str(e)}")

    def create_duplicate_groups(self, duplicate_data: Dict[str, List[Tuple[str, int]]], db_session) -> List[Dict[str, Any]]:
        """
        创建重复照片组

        Args:
            duplicate_data: 重复数据字典
            db_session: 数据库会话

        Returns:
            创建的重复组信息
        """
        try:
            created_groups = []

            for representative_path, similar_photos in duplicate_data.items():
                # 查找代表照片
                representative_photo = db_session.query(Photo).filter(
                    Photo.original_path == representative_path
                ).first()

                if not representative_photo:
                    self.logger.warning(f"找不到代表照片: {representative_path}")
                    continue

                # 创建重复组
                duplicate_group = DuplicateGroup(
                    representative_photo_id=representative_photo.id
                )
                db_session.add(duplicate_group)
                db_session.flush()  # 获取group ID

                # 添加组成员
                group_members = []

                # 添加代表照片
                group_members.append({
                    "group_id": duplicate_group.id,
                    "photo_id": representative_photo.id,
                    "filename": representative_photo.filename,
                    "similarity_score": 100.0  # 代表照片相似度为100%
                })

                # 添加相似照片
                for similar_path, distance in similar_photos:
                    similar_photo = db_session.query(Photo).filter(
                        Photo.original_path == similar_path
                    ).first()

                    if similar_photo:
                        similarity_score = (64 - distance) / 64 * 100

                        group_member = DuplicateGroupPhoto(
                            group_id=duplicate_group.id,
                            photo_id=similar_photo.id
                        )
                        db_session.add(group_member)

                        group_members.append({
                            "group_id": duplicate_group.id,
                            "photo_id": similar_photo.id,
                            "filename": similar_photo.filename,
                            "similarity_score": round(similarity_score, 2)
                        })

                created_groups.append({
                    "group_id": duplicate_group.id,
                    "representative_photo": representative_photo.filename,
                    "member_count": len(group_members),
                    "members": group_members
                })

            db_session.commit()
            return created_groups

        except Exception as e:
            db_session.rollback()
            self.logger.error(f"创建重复组失败: {str(e)}")
            raise Exception(f"创建重复组失败: {str(e)}")

    def get_duplicate_groups(self, db_session) -> List[Dict[str, Any]]:
        """
        获取所有重复组

        Args:
            db_session: 数据库会话

        Returns:
            重复组列表
        """
        try:
            groups = db_session.query(DuplicateGroup).all()
            result = []

            for group in groups:
                members = []
                for member in group.photos:
                    similarity_score = 100.0 if member.photo_id == group.representative_photo_id else 0.0
                    members.append({
                        "photo_id": member.photo_id,
                        "filename": member.photo.filename,
                        "similarity_score": similarity_score
                    })

                result.append({
                    "group_id": group.id,
                    "representative_photo_id": group.representative_photo_id,
                    "representative_filename": group.representative_photo.filename,
                    "member_count": len(members),
                    "members": members,
                    "created_at": group.created_at.isoformat() if group.created_at else None
                })

            return result

        except Exception as e:
            self.logger.error(f"获取重复组失败: {str(e)}")
            raise Exception(f"获取重复组失败: {str(e)}")

    def update_photo_duplicate_status(self, photo_id: int, is_duplicate: bool, duplicate_group_id: Optional[int], db_session):
        """
        更新照片的重复状态

        Args:
            photo_id: 照片ID
            is_duplicate: 是否为重复照片
            duplicate_group_id: 重复组ID
            db_session: 数据库会话
        """
        try:
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            if photo:
                photo.is_duplicate = is_duplicate
                photo.duplicate_group_id = duplicate_group_id
                db_session.commit()

        except Exception as e:
            db_session.rollback()
            self.logger.error(f"更新照片重复状态失败 {photo_id}: {str(e)}")
            raise Exception(f"更新重复状态失败: {str(e)}")

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

    def optimize_similarity_threshold(self, test_photos: List[str]) -> int:
        """
        基于测试照片优化相似度阈值

        Args:
            test_photos: 测试照片路径列表

        Returns:
            推荐的相似度阈值
        """
        try:
            # 计算所有照片对的距离
            distances = []

            for i, path1 in enumerate(test_photos):
                for j, path2 in enumerate(test_photos):
                    if i < j:
                        try:
                            hash1 = self.calculate_perceptual_hash(path1)
                            hash2 = self.calculate_perceptual_hash(path2)
                            distance = self.calculate_hash_similarity(hash1, hash2)
                            distances.append(distance)
                        except:
                            continue

            if not distances:
                return self.similarity_threshold

            # 分析距离分布
            distances.sort()

            # 建议阈值：距离分布的25%分位数
            threshold_index = int(len(distances) * 0.25)
            recommended_threshold = distances[threshold_index] if threshold_index < len(distances) else self.similarity_threshold

            return min(recommended_threshold, 20)  # 最大不超过20

        except Exception as e:
            self.logger.error(f"优化相似度阈值失败: {str(e)}")
            return self.similarity_threshold
