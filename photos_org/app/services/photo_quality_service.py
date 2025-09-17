"""
家庭版智能照片系统 - 照片质量评估服务
"""
import cv2
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image
import math
from app.core.logging import get_logger

# 导入HEIC支持
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORT = True
except ImportError:
    HEIC_SUPPORT = False


class PhotoQualityService:
    """
    照片质量评估服务类
    使用OpenCV进行照片质量评估
    """

    def __init__(self):
        """初始化质量评估服务"""
        self.logger = get_logger(__name__)

    def assess_quality(self, image_path: str) -> Dict[str, Any]:
        """
        评估照片质量

        Args:
            image_path: 照片文件路径

        Returns:
            质量评估结果字典
        """
        try:
            # 读取图片 - 处理中文文件名问题
            image = None
            
            # 首先尝试直接读取
            image = cv2.imread(image_path)

            # 如果直接读取失败或返回None，使用备用方案
            if image is None:
                # 使用np.fromfile和imdecode作为备用方案
                try:
                    with open(image_path, 'rb') as f:
                        image_data = np.frombuffer(f.read(), dtype=np.uint8)
                    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                except Exception as np_error:
                    print(f"cv2.imdecode异常: {str(np_error)}")
                
                # 如果cv2.imdecode也失败或返回None，尝试使用PIL作为中间桥梁
                if image is None:
                    try:
                        pil_image = Image.open(image_path)
                        # 转换为RGB格式
                        if pil_image.mode != 'RGB':
                            pil_image = pil_image.convert('RGB')
                        # 转换为numpy数组
                        image_array = np.array(pil_image)
                        # 转换为BGR格式（OpenCV默认格式）
                        image = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                    except Exception as pil_error:
                        raise Exception(f"无法读取图片文件，所有读取方法都失败: pil_error={str(pil_error)}")

            # 最终检查
            if image is None:
                raise Exception("无法读取图片文件")

            # 转换为RGB色彩空间（用于PIL处理）
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)

            # 各项质量评估
            sharpness_score = self._assess_sharpness(image)
            brightness_score = self._assess_brightness(image)
            contrast_score = self._assess_contrast(image)
            color_score = self._assess_color_quality(image)
            composition_score = self._assess_composition(image)

            # 技术问题检测
            technical_issues_raw = self._detect_technical_issues(image, pil_image)
            # 将列表转换为字典格式以兼容数据库存储
            technical_issues = {
                "issues": technical_issues_raw,
                "count": len(technical_issues_raw),
                "has_issues": len(technical_issues_raw) > 0
            }

            # 综合质量评分（加权平均）
            weights = {
                'sharpness': 0.3,
                'brightness': 0.2,
                'contrast': 0.2,
                'color': 0.15,
                'composition': 0.15
            }

            quality_score = (
                sharpness_score * weights['sharpness'] +
                brightness_score * weights['brightness'] +
                contrast_score * weights['contrast'] +
                color_score * weights['color'] +
                composition_score * weights['composition']
            )

            # 质量等级
            quality_level = self._get_quality_level(quality_score)

            return {
                "quality_score": round(quality_score, 2),
                "sharpness_score": round(sharpness_score, 2),
                "brightness_score": round(brightness_score, 2),
                "contrast_score": round(contrast_score, 2),
                "color_score": round(color_score, 2),
                "composition_score": round(composition_score, 2),
                "quality_level": quality_level,
                "technical_issues": technical_issues
            }

        except Exception as e:
            self.logger.error(f"照片质量评估失败 {image_path}: {str(e)}")
            raise Exception(f"照片质量评估失败: {str(e)}")

    def _assess_sharpness(self, image: np.ndarray) -> float:
        """
        评估图像清晰度

        Args:
            image: OpenCV图像数组

        Returns:
            清晰度评分 (0-100)
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 使用Laplacian算子评估清晰度
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()

            # 归一化到0-100分
            # 经验值：variance > 100 为清晰，variance < 10 为模糊
            score = min(100, max(0, (variance - 10) / 90 * 100))

            return score

        except Exception as e:
            self.logger.error(f"清晰度评估失败: {str(e)}")
            return 50.0

    def _assess_brightness(self, image: np.ndarray) -> float:
        """
        评估图像亮度

        Args:
            image: OpenCV图像数组

        Returns:
            亮度评分 (0-100)
        """
        try:
            # 计算平均亮度
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray)

            # 理想亮度范围：100-200
            if 100 <= avg_brightness <= 200:
                score = 100
            elif avg_brightness < 50 or avg_brightness > 250:
                score = 20  # 过暗或过亮
            else:
                # 距离理想范围的惩罚
                distance = min(abs(avg_brightness - 100), abs(avg_brightness - 200))
                score = max(20, 100 - distance)

            return score

        except Exception as e:
            self.logger.error(f"亮度评估失败: {str(e)}")
            return 50.0

    def _assess_contrast(self, image: np.ndarray) -> float:
        """
        评估图像对比度

        Args:
            image: OpenCV图像数组

        Returns:
            对比度评分 (0-100)
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 计算标准差作为对比度指标
            contrast = np.std(gray)

            # 归一化到0-100分
            # 经验值：contrast > 50 为高对比度
            score = min(100, max(0, contrast / 50 * 100))

            return score

        except Exception as e:
            self.logger.error(f"对比度评估失败: {str(e)}")
            return 50.0

    def _assess_color_quality(self, image: np.ndarray) -> float:
        """
        评估图像色彩质量

        Args:
            image: OpenCV图像数组

        Returns:
            色彩质量评分 (0-100)
        """
        try:
            # 分离颜色通道
            b, g, r = cv2.split(image)

            # 计算各通道的平均值和标准差
            channels = [r, g, b]
            channel_means = [np.mean(channel) for channel in channels]
            channel_stds = [np.std(channel) for channel in channels]

            # 色彩平衡评分（各通道平均值差异）
            mean_diff = np.std(channel_means)
            balance_score = max(0, 100 - mean_diff * 2)

            # 色彩丰富度评分（各通道标准差平均值）
            richness_score = min(100, np.mean(channel_stds) * 2)

            # 综合色彩评分
            color_score = (balance_score + richness_score) / 2

            return color_score

        except Exception as e:
            self.logger.error(f"色彩质量评估失败: {str(e)}")
            return 50.0

    def _assess_composition(self, image: np.ndarray) -> float:
        """
        评估图像构图

        Args:
            image: OpenCV图像数组

        Returns:
            构图评分 (0-100)
        """
        try:
            height, width = image.shape[:2]

            # 简单的构图评估：检查是否接近黄金比例
            ratio = width / height if width > height else height / width

            # 黄金比例约1.618
            golden_ratio = 1.618
            ratio_diff = abs(ratio - golden_ratio)

            # 比例越接近黄金比例，分数越高
            composition_score = max(0, 100 - ratio_diff * 50)

            # 简单的对称性检查（简化版）
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            symmetry_score = self._check_symmetry(gray)

            # 综合构图评分
            final_score = (composition_score + symmetry_score) / 2

            return final_score

        except Exception as e:
            self.logger.error(f"构图评估失败: {str(e)}")
            return 50.0

    def _check_symmetry(self, gray_image: np.ndarray) -> float:
        """
        检查图像对称性

        Args:
            gray_image: 灰度图像

        Returns:
            对称性评分 (0-100)
        """
        try:
            height, width = gray_image.shape

            # 简单的左右对称性检查
            left_half = gray_image[:, :width//2]
            right_half = cv2.flip(gray_image[:, width//2:], 1)  # 水平翻转右半部分

            # 计算差异
            if left_half.shape != right_half.shape:
                # 调整大小以匹配
                min_width = min(left_half.shape[1], right_half.shape[1])
                left_half = left_half[:, :min_width]
                right_half = right_half[:, :min_width]

            diff = cv2.absdiff(left_half, right_half)
            symmetry_score = 100 - np.mean(diff)

            return max(0, symmetry_score)

        except Exception as e:
            return 50.0

    def _detect_technical_issues(self, image: np.ndarray, pil_image: Image.Image) -> List[str]:
        """
        检测技术问题

        Args:
            image: OpenCV图像数组
            pil_image: PIL图像对象

        Returns:
            技术问题列表
        """
        issues = []

        try:
            # 检查过曝光
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            overexposed_pixels = np.sum(gray > 240)
            total_pixels = gray.size
            overexposed_ratio = overexposed_pixels / total_pixels

            if overexposed_ratio > 0.1:
                issues.append(f"过曝光区域过多 ({overexposed_ratio:.1%})")

            # 检查欠曝光
            underexposed_pixels = np.sum(gray < 15)
            underexposed_ratio = underexposed_pixels / total_pixels

            if underexposed_ratio > 0.1:
                issues.append(f"欠曝光区域过多 ({underexposed_ratio:.1%})")

            # 检查模糊
            sharpness = self._assess_sharpness(image)
            if sharpness < 30:
                issues.append("图像模糊")

            # 检查色彩失真（简化检查）
            if self._assess_color_quality(image) < 40:
                issues.append("色彩质量较差")

        except Exception as e:
            self.logger.error(f"技术问题检测失败: {str(e)}")

        return issues

    def _get_quality_level(self, score: float) -> str:
        """
        根据评分确定质量等级

        Args:
            score: 质量评分

        Returns:
            质量等级字符串
        """
        if score >= 85:
            return "优秀"
        elif score >= 70:
            return "良好"
        elif score >= 50:
            return "一般"
        elif score >= 30:
            return "较差"
        else:
            return "很差"

    def _get_average_brightness(self, image: np.ndarray) -> float:
        """获取平均亮度"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))

    def _get_contrast_ratio(self, image: np.ndarray) -> float:
        """获取对比度比例"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(np.std(gray))

    def _get_average_saturation(self, image: np.ndarray) -> float:
        """获取平均饱和度"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        return float(np.mean(hsv[:, :, 1]))

    def _assess_noise(self, image: np.ndarray) -> float:
        """评估噪声水平"""
        try:
            # 简单的噪声评估：计算图像梯度的标准差
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient = np.sqrt(sobel_x**2 + sobel_y**2)
            noise_level = np.std(gradient)
            return float(noise_level)
        except:
            return 0.0

    def _assess_dynamic_range(self, image: np.ndarray) -> float:
        """评估动态范围"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            min_val = np.min(gray)
            max_val = np.max(gray)
            dynamic_range = max_val - min_val
            return float(dynamic_range)
        except:
            return 0.0
