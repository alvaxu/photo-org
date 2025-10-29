"""
人脸裁剪服务

程序说明：
## 1. 提供人脸区域裁剪功能，从照片中提取人脸部分
## 2. 支持生成圆形头像和矩形头像
## 3. 缓存裁剪后的人脸图片，避免重复处理
"""

import os
from pathlib import Path
from typing import Optional, Tuple
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class FaceCropService:
    """人脸裁剪服务类"""
    
    def __init__(self):
        """初始化人脸裁剪服务"""
        self.cache_dir = Path(settings.storage.base_path) / "face_crops"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def crop_face_from_photo(self, photo_path: str, face_rectangle, 
                           crop_size: int = 150, crop_type: str = "circle", 
                           padding_ratio: float = 0.3) -> Optional[str]:
        """
        从照片中裁剪人脸区域
        
        :param photo_path: 照片路径
        :param face_rectangle: 人脸矩形区域 [x, y, w, h] 或 {"x": int, "y": int, "w": int, "h": int}
        :param crop_size: 裁剪后图片的边长（正方形）
        :param crop_type: 裁剪类型 ("circle" 或 "square")
        :param padding_ratio: 裁剪区域相对于人脸宽度/高度的额外填充比例 (0.0 - 1.0)
        :return: 裁剪后图片的缓存路径
        """
        try:
            # 延迟导入cv2, numpy
            import cv2
            import numpy as np
            import PIL
            from PIL import Image
            HEIC_SUPPORT = False
            
            # 尝试导入 HEIC 支持
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
                HEIC_SUPPORT = True
            except ImportError:
                HEIC_SUPPORT = False
            
            # 构建完整照片路径
            storage_base = Path(settings.storage.base_path)
            full_photo_path = storage_base / photo_path
            
            if not full_photo_path.exists():
                logger.warning(f"照片文件不存在: {full_photo_path}")
                return None
            
            # 获取人脸区域坐标（用于生成缓存文件名）
            if isinstance(face_rectangle, list) and len(face_rectangle) >= 4:
                x_orig, y_orig, w_orig, h_orig = int(face_rectangle[0]), int(face_rectangle[1]), int(face_rectangle[2]), int(face_rectangle[3])
            elif isinstance(face_rectangle, dict):
                x_orig, y_orig, w_orig, h_orig = int(face_rectangle['x']), int(face_rectangle['y']), int(face_rectangle['w']), int(face_rectangle['h'])
            else:
                logger.error(f"不支持的人脸矩形格式: {face_rectangle}")
                return None
            
            # 生成缓存文件名（包含填充比例）
            photo_name = Path(photo_path).stem
            cache_filename = f"{photo_name}_face_{x_orig}_{y_orig}_{w_orig}_{h_orig}_{crop_size}_{crop_type}_pad{int(padding_ratio*100)}.jpg"
            cache_path = self.cache_dir / cache_filename
            
            # 如果缓存已存在，直接返回
            if cache_path.exists():
                return str(cache_path.relative_to(storage_base))
            
            # 读取照片（支持HEIC格式）
            photo_path_lower = str(full_photo_path).lower()
            is_heic = photo_path_lower.endswith(('.heic', '.heif'))
            
            if is_heic and HEIC_SUPPORT and PIL:
                # HEIC 格式：使用 PIL 读取并转换为 OpenCV 格式
                try:
                    pil_img = Image.open(str(full_photo_path))
                    # 转换为 RGB（HEIC 可能是 RGBA）
                    if pil_img.mode == 'RGBA':
                        # 创建白色背景
                        background = Image.new('RGB', pil_img.size, (255, 255, 255))
                        background.paste(pil_img, mask=pil_img.split()[3])  # 3 是 alpha 通道
                        pil_img = background
                    elif pil_img.mode != 'RGB':
                        pil_img = pil_img.convert('RGB')
                    
                    # 转换为 numpy 数组并转为 BGR（OpenCV 格式）
                    img_array = np.array(pil_img)
                    image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    logger.info(f"HEIC 图像读取成功（肖像裁剪）: {full_photo_path}")
                except Exception as e:
                    logger.error(f"HEIC 图像读取失败（肖像裁剪）: {e}")
                    return None
            else:
                # 非 HEIC 格式：使用 OpenCV 读取
                image = cv2.imread(str(full_photo_path))
                if image is None:
                    logger.error(f"无法读取照片: {full_photo_path}")
                    return None
            
            # 尝试填充裁剪，如果失败则使用原始区域
            try:
                # 计算填充后的裁剪区域
                # 扩展宽度和高度
                pad_w = int(w_orig * padding_ratio)
                pad_h = int(h_orig * padding_ratio)
                
                # 计算新的裁剪框坐标
                x1 = max(0, x_orig - pad_w)
                y1 = max(0, y_orig - pad_h)
                x2 = min(image.shape[1], x_orig + w_orig + pad_w)
                y2 = min(image.shape[0], y_orig + h_orig + pad_h)
                
                # 确保裁剪框是正方形，以适应圆形裁剪
                # 取扩展后宽度和高度的最大值作为边长
                side_length = max(x2 - x1, y2 - y1)
                
                # 重新调整坐标以确保是正方形且居中
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                x1_square = max(0, center_x - side_length // 2)
                y1_square = max(0, center_y - side_length // 2)
                x2_square = min(image.shape[1], center_x + side_length // 2)
                y2_square = min(image.shape[0], center_y + side_length // 2)
                
                # 再次调整以确保边长一致
                final_side_length = min(x2_square - x1_square, y2_square - y1_square)
                x1_final = center_x - final_side_length // 2
                y1_final = center_y - final_side_length // 2
                x2_final = center_x + final_side_length // 2
                y2_final = center_y + final_side_length // 2
                
                # 最终边界检查
                x1_final = max(0, x1_final)
                y1_final = max(0, y1_final)
                x2_final = min(image.shape[1], x2_final)
                y2_final = min(image.shape[0], y2_final)
                
                # 确保最终区域有效
                if x2_final <= x1_final or y2_final <= y1_final:
                    raise ValueError("填充裁剪区域无效")
                
                # 裁剪图像
                face_crop = image[y1_final:y2_final, x1_final:x2_final]
                
                if face_crop.size == 0:
                    raise ValueError("填充裁剪后图像为空")
                    
            except Exception as e:
                logger.warning(f"填充裁剪失败，使用原始区域: {e}")
                # 使用原始人脸区域进行裁剪
                x1_final = max(0, x_orig)
                y1_final = max(0, y_orig)
                x2_final = min(image.shape[1], x_orig + w_orig)
                y2_final = min(image.shape[0], y_orig + h_orig)
                
                # 确保区域有效
                if x2_final <= x1_final or y2_final <= y1_final:
                    logger.error(f"原始裁剪区域也无效: ({x1_final},{y1_final},{x2_final},{y2_final})")
                    return None
                
                # 裁剪图像
                face_crop = image[y1_final:y2_final, x1_final:x2_final]
                
                if face_crop.size == 0:
                    logger.error(f"原始裁剪后图像也为空")
                    return None
            
            # 调整尺寸
            face_resized = cv2.resize(face_crop, (crop_size, crop_size))
            
            if crop_type == "circle":
                # 创建圆形遮罩
                face_resized = self._create_circular_crop(face_resized)
            
            # 保存到缓存
            cv2.imwrite(str(cache_path), face_resized)
            
            logger.info(f"人脸裁剪完成: {cache_path}")
            return str(cache_path.relative_to(storage_base))
            
        except Exception as e:
            logger.error(f"人脸裁剪失败: {e}")
            return None
    
    def _create_circular_crop(self, image) -> object:
        """
        创建圆形裁剪
        
        :param image: 输入图像
        :return: 圆形裁剪后的图像
        """
        try:
            import cv2
            import numpy as np
            
            height, width = image.shape[:2]
            
            # 创建圆形遮罩
            mask = np.zeros((height, width), dtype=np.uint8)
            center = (width // 2, height // 2)
            radius = min(width, height) // 2
            cv2.circle(mask, center, radius, 255, -1)
            
            # 应用遮罩
            result = image.copy()
            result[mask == 0] = [255, 255, 255]  # 背景设为白色
            
            return result
            
        except Exception as e:
            logger.error(f"创建圆形裁剪失败: {e}")
            return image
    
    def get_face_crop_url(self, photo_path: str, face_rectangle, 
                         crop_size: int = 150, crop_type: str = "circle", 
                         padding_ratio: float = 0.3) -> str:
        """
        获取人脸裁剪图片的URL
        
        :param photo_path: 照片路径
        :param face_rectangle: 人脸矩形区域
        :param crop_size: 裁剪尺寸
        :param crop_type: 裁剪类型
        :param padding_ratio: 填充比例
        :return: 图片URL
        """
        crop_path = self.crop_face_from_photo(photo_path, face_rectangle, crop_size, crop_type, padding_ratio)
        
        if crop_path:
            return f"/photos_storage/{crop_path.replace('\\', '/')}"
        else:
            # 返回默认占位符
            return "/static/images/placeholder.jpg"
    
    def clear_cache(self) -> bool:
        """
        清理缓存
        
        :return: 是否清理成功
        """
        try:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("人脸裁剪缓存已清理")
                return True
            return False
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return False
    
    def cleanup_old_cache(self, max_age_days: int = 30) -> int:
        """
        清理过期的缓存文件
        
        :param max_age_days: 最大保留天数
        :return: 清理的文件数量
        """
        try:
            import time
            from datetime import datetime, timedelta
            
            if not self.cache_dir.exists():
                return 0
            
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            cleaned_count = 0
            
            for cache_file in self.cache_dir.glob("*.jpg"):
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_time < cutoff_time:
                    cache_file.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个过期的人脸裁剪缓存文件")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0

# 懒加载实例
_face_crop_service_instance = None

def get_face_crop_service():
    """获取人脸裁剪服务实例（单例模式）"""
    global _face_crop_service_instance
    if _face_crop_service_instance is None:
        _face_crop_service_instance = FaceCropService()
    return _face_crop_service_instance

# 为了向后兼容，提供全局访问
def __getattr__(name):
    if name == 'face_crop_service':
        return get_face_crop_service()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
