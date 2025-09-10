"""
照片导入服务

负责照片文件的导入、校验、元数据提取、缩略图生成等核心功能

作者：AI助手
创建日期：2025年9月9日
"""

import os
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import mimetypes

from PIL import Image, ExifTags
import imagehash

from app.core.config import settings
from app.models.photo import Photo
from app.schemas.photo import PhotoCreate


class ImportService:
    """照片导入服务类"""

    # 支持的文件格式
    SUPPORTED_FORMATS = {
        'JPEG': ['.jpg', '.jpeg'],
        'PNG': ['.png'],
        'TIFF': ['.tiff', '.tif'],
        'WebP': ['.webp'],
        'BMP': ['.bmp'],
        'GIF': ['.gif']
    }

    # 支持的MIME类型
    SUPPORTED_MIMETYPES = [
        'image/jpeg',
        'image/png',
        'image/tiff',
        'image/webp',
        'image/bmp',
        'image/gif'
    ]

    def __init__(self):
        """初始化导入服务"""
        self.storage_base = Path(settings.storage.base_path)
        self.originals_path = self.storage_base / settings.storage.originals_path
        self.thumbnails_path = self.storage_base / settings.storage.thumbnails_path
        self.temp_path = self.storage_base / settings.storage.temp_path

        # 确保目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.storage_base,
            self.originals_path,
            self.thumbnails_path,
            self.temp_path
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def validate_photo_file(self, file_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        验证照片文件

        :param file_path: 文件路径
        :return: (是否有效, 错误信息, 文件信息)
        """
        file_path = Path(file_path)

        # 检查文件存在性
        if not file_path.exists():
            return False, "文件不存在", None

        # 检查文件大小
        file_size = file_path.stat().st_size
        if file_size > settings.system.max_file_size:
            return False, f"文件大小超过限制({settings.system.max_file_size}字节)", None

        if file_size == 0:
            return False, "文件为空", None

        # 检查文件格式
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type not in self.SUPPORTED_MIMETYPES:
            return False, f"不支持的文件格式: {mime_type}", None

        # 检查文件扩展名
        if not self._is_supported_extension(file_path.suffix.lower()):
            return False, f"不支持的文件扩展名: {file_path.suffix}", None

        # 验证图像文件完整性
        try:
            with Image.open(file_path) as img:
                img.verify()  # 验证文件完整性

            # 重新打开获取图像信息
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format

        except Exception as e:
            return False, f"图像文件损坏或无效: {str(e)}", None

        file_info = {
            'file_size': file_size,
            'width': width,
            'height': height,
            'format': format_name,
            'mime_type': mime_type
        }

        return True, "", file_info

    def _is_supported_extension(self, extension: str) -> bool:
        """检查文件扩展名是否支持"""
        for format_extensions in self.SUPPORTED_FORMATS.values():
            if extension in format_extensions:
                return True
        return False

    def calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件的MD5哈希值

        :param file_path: 文件路径
        :return: MD5哈希值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def calculate_perceptual_hash(self, file_path: str) -> Optional[str]:
        """
        计算图像的感知哈希值

        :param file_path: 文件路径
        :return: 感知哈希值（16进制字符串）
        """
        try:
            with Image.open(file_path) as img:
                # 转换为灰度图像
                if img.mode != 'L':
                    img = img.convert('L')

                # 计算感知哈希
                phash = imagehash.phash(img)

                # 返回16进制字符串
                return str(phash)

        except Exception as e:
            print(f"计算感知哈希失败: {str(e)}")
            return None

    def extract_exif_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        提取EXIF元数据

        :param file_path: 文件路径
        :return: EXIF元数据字典
        """
        metadata = {}

        try:
            with Image.open(file_path) as img:
                # 获取EXIF数据
                exif_data = img._getexif()

                if exif_data:
                    # 创建EXIF标签映射
                    exif_tags = {v: k for k, v in ExifTags.TAGS.items()}

                    for tag, value in exif_data.items():
                        tag_name = exif_tags.get(tag, tag)

                        # 处理常见标签
                        if tag_name == 'DateTimeOriginal':
                            metadata['taken_at'] = self._parse_exif_datetime(value)
                        elif tag_name == 'Make':
                            metadata['camera_make'] = value
                        elif tag_name == 'Model':
                            metadata['camera_model'] = value
                        elif tag_name == 'LensModel':
                            metadata['lens_model'] = value
                        elif tag_name == 'FocalLength':
                            metadata['focal_length'] = float(value) if isinstance(value, (int, float)) else None
                        elif tag_name == 'FNumber':
                            metadata['aperture'] = float(value) if isinstance(value, (int, float)) else None
                        elif tag_name == 'ExposureTime':
                            metadata['shutter_speed'] = str(value)
                        elif tag_name == 'ISOSpeedRatings':
                            metadata['iso'] = value if isinstance(value, int) else None
                        elif tag_name == 'Flash':
                            metadata['flash'] = str(value)
                        elif tag_name == 'WhiteBalance':
                            metadata['white_balance'] = str(value)
                        elif tag_name == 'ExposureMode':
                            metadata['exposure_mode'] = str(value)
                        elif tag_name == 'MeteringMode':
                            metadata['metering_mode'] = str(value)
                        elif tag_name == 'Orientation':
                            metadata['orientation'] = value if isinstance(value, int) else None

                    # 处理GPS信息
                    gps_info = self._extract_gps_info(exif_data)
                    if gps_info:
                        metadata.update(gps_info)

        except Exception as e:
            print(f"EXIF提取失败: {str(e)}")

        return metadata

    def _parse_exif_datetime(self, datetime_str: str) -> Optional[datetime]:
        """
        解析EXIF日期时间字符串

        :param datetime_str: EXIF日期时间字符串
        :return: datetime对象
        """
        try:
            # EXIF格式通常为: "2023:09:09 14:30:00"
            return datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S')
        except (ValueError, TypeError):
            return None

    def _extract_gps_info(self, exif_data: Dict) -> Dict[str, Any]:
        """
        提取GPS信息

        :param exif_data: EXIF数据
        :return: GPS信息字典
        """
        gps_info = {}

        try:
            gps_data = exif_data.get(34853)  # GPS IFD
            if gps_data:
                # GPS纬度
                lat = self._convert_gps_coordinate(gps_data.get(2), gps_data.get(1))
                if lat is not None:
                    gps_info['location_lat'] = lat

                # GPS经度
                lng = self._convert_gps_coordinate(gps_data.get(4), gps_data.get(3))
                if lng is not None:
                    gps_info['location_lng'] = lng

                # GPS海拔
                alt = gps_data.get(6)
                if alt is not None:
                    gps_info['location_alt'] = float(alt)

        except Exception as e:
            print(f"GPS信息提取失败: {str(e)}")

        return gps_info

    def _convert_gps_coordinate(self, coordinate: Optional[List], reference: Optional[str]) -> Optional[float]:
        """
        转换GPS坐标

        :param coordinate: GPS坐标列表
        :param reference: 参考方向 (N/S/E/W)
        :return: 十进制坐标
        """
        if not coordinate or len(coordinate) != 3:
            return None

        try:
            degrees = coordinate[0]
            minutes = coordinate[1]
            seconds = coordinate[2]

            # 转换为十进制
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

            # 处理南北半球
            if reference in ('S', 'W'):
                decimal = -decimal

            return decimal

        except (TypeError, ValueError, ZeroDivisionError):
            return None

    def generate_thumbnail(self, source_path: str, max_size: int = None) -> Optional[str]:
        """
        生成缩略图

        :param source_path: 源文件路径
        :param max_size: 缩略图最大尺寸
        :return: 缩略图路径
        """
        if max_size is None:
            max_size = settings.storage.thumbnail_size

        try:
            with Image.open(source_path) as img:
                # 计算缩略图尺寸
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                # 生成缩略图文件名
                source_name = Path(source_path).stem
                thumbnail_filename = f"{source_name}_thumb.jpg"
                thumbnail_path = self.thumbnails_path / thumbnail_filename

                # 保存缩略图
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                img.save(thumbnail_path, 'JPEG', quality=settings.storage.thumbnail_quality)

                return str(thumbnail_path)

        except Exception as e:
            print(f"缩略图生成失败: {str(e)}")
            return None

    def move_to_storage(self, source_path: str, filename: str) -> str:
        """
        将文件移动到存储目录

        :param source_path: 源文件路径
        :param filename: 目标文件名
        :return: 存储路径
        """
        # 构造存储路径（按日期组织）
        now = datetime.now()
        date_path = self.originals_path / f"{now.year}" / f"{now.month:02d}"

        # 确保日期目录存在
        date_path.mkdir(parents=True, exist_ok=True)

        # 构造目标路径
        target_path = date_path / filename

        # 如果文件已存在，添加时间戳避免冲突
        if target_path.exists():
            timestamp = int(now.timestamp())
            stem = target_path.stem
            suffix = target_path.suffix
            target_path = date_path / f"{stem}_{timestamp}{suffix}"

        # 移动文件
        import shutil
        shutil.move(source_path, target_path)

        return str(target_path)

    def create_photo_record(self, file_path: str, metadata: Dict[str, Any]) -> PhotoCreate:
        """
        创建照片记录

        :param file_path: 文件路径
        :param metadata: 元数据
        :return: PhotoCreate对象
        """
        file_path_obj = Path(file_path)

        # 基本文件信息
        filename = file_path_obj.name
        file_size = file_path_obj.stat().st_size

        # 获取图像尺寸
        width, height = 0, 0
        format_name = ""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format or ""
        except Exception as e:
            print(f"获取图像尺寸失败: {str(e)}")

        # 计算文件哈希
        file_hash = self.calculate_file_hash(file_path)

        # 计算感知哈希
        perceptual_hash = self.calculate_perceptual_hash(file_path)

        # 合并元数据
        photo_data = {
            'filename': filename,
            'original_path': file_path,
            'file_size': file_size,
            'width': width,
            'height': height,
            'format': format_name,
            'file_hash': file_hash,
            'perceptual_hash': perceptual_hash,
            'status': 'imported'
        }

        # 添加EXIF元数据
        photo_data.update(metadata)

        return PhotoCreate(**photo_data)

    def scan_folder(self, folder_path: str, recursive: bool = True) -> List[str]:
        """
        扫描文件夹获取照片文件

        :param folder_path: 文件夹路径
        :param recursive: 是否递归扫描
        :return: 照片文件路径列表
        """
        photo_files = []
        folder_path = Path(folder_path)

        if not folder_path.exists() or not folder_path.is_dir():
            raise ValueError(f"文件夹不存在或不是目录: {folder_path}")

        # 扫描文件
        pattern = "**/*" if recursive else "*"

        for file_path in folder_path.glob(pattern):
            if file_path.is_file():
                # 检查文件扩展名
                if self._is_supported_extension(file_path.suffix.lower()):
                    # 验证文件
                    is_valid, error_msg, _ = self.validate_photo_file(str(file_path))
                    if is_valid:
                        photo_files.append(str(file_path))
                    else:
                        print(f"跳过无效文件 {file_path}: {error_msg}")

        return photo_files

    def process_single_photo(self, file_path: str) -> Tuple[bool, str, Optional[PhotoCreate]]:
        """
        处理单个照片文件

        :param file_path: 文件路径
        :return: (是否成功, 消息, 照片数据)
        """
        try:
            # 验证文件
            is_valid, error_msg, file_info = self.validate_photo_file(file_path)
            if not is_valid:
                return False, error_msg, None

            # 提取元数据
            metadata = self.extract_exif_metadata(file_path)

            # 生成缩略图
            thumbnail_path = self.generate_thumbnail(file_path)
            if thumbnail_path:
                metadata['thumbnail_path'] = thumbnail_path

            # 创建照片记录
            photo_data = self.create_photo_record(file_path, metadata)

            return True, "照片处理成功", photo_data

        except Exception as e:
            return False, f"照片处理失败: {str(e)}", None
