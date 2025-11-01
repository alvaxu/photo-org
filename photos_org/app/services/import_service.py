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

# 延迟导入PIL, imagehash
Image = None
ExifTags = None
imagehash = None

# HEIC支持标志
HEIC_SUPPORT = False

def _lazy_import_pil():
    """延迟导入PIL和imagehash"""
    global Image, ExifTags, imagehash, HEIC_SUPPORT
    
    if Image is None:
        from PIL import Image, ExifTags
        import imagehash
        
        # 导入HEIC支持
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
            HEIC_SUPPORT = True
        except ImportError:
            HEIC_SUPPORT = False

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
        'GIF': ['.gif'],
        'HEIC': ['.heic', '.heif']
    }

    # 支持的MIME类型
    SUPPORTED_MIMETYPES = [
        'image/jpeg',
        'image/png',
        'image/tiff',
        'image/webp',
        'image/bmp',
        'image/gif',
        'image/heic',
        'image/heif'
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
        # 延迟导入PIL
        _lazy_import_pil()
        
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
        
        # 特殊处理HEIC格式
        if file_path.suffix.lower() in ['.heic', '.heif']:
            if not HEIC_SUPPORT:
                return False, "HEIC格式需要安装pillow-heif库支持", None
            # HEIC格式的MIME类型可能不准确，手动设置
            mime_type = 'image/heic'
        
        # 检查MIME类型是否支持
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
        # 延迟导入PIL
        _lazy_import_pil()
        
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
        # 延迟导入PIL
        _lazy_import_pil()
        
        metadata = {}

        try:
            # 🔥 简化：直接提取EXIF，失败就返回空metadata
            # 在并发场景下，如果提取失败，另一个线程可能已经成功提取并保存到数据库
            # 最终的数据库记录会通过IntegrityError检测返回已存在记录（包含EXIF）
            with Image.open(file_path) as img:
                # 获取EXIF数据 - 同时获取处理过的和原始的EXIF数据
                processed_exif = {}
                raw_exif = {}

                # 获取处理过的EXIF数据（用于标准标签）
                if hasattr(img, 'getexif'):
                    processed_exif = img.getexif() or {}
                elif hasattr(img, '_getexif'):
                    processed_exif = img._getexif() or {}

                # 获取原始EXIF数据（用于GPS等特殊数据）
                if hasattr(img, '_getexif'):
                    raw_exif = img._getexif() or {}
                elif hasattr(img, 'getexif'):
                    raw_exif = img.getexif() or {}

                # 处理标准EXIF标签
                if processed_exif:
                    # 创建EXIF标签映射
                    exif_tags = {v: k for k, v in ExifTags.TAGS.items()}

                    for tag, value in processed_exif.items():
                        tag_name = exif_tags.get(tag, tag)

                        # 处理常见标签（使用标准名称）
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

                        # 处理实际标签ID（针对不同相机厂商的特殊情况）
                        elif tag == 271:  # 相机品牌
                            metadata['camera_make'] = value
                        elif tag == 272:  # 相机型号
                            metadata['camera_model'] = value
                        elif tag == 306:  # 拍摄时间
                            metadata['taken_at'] = self._parse_exif_datetime(value)
                        elif tag == 36867:  # 另一种拍摄时间格式
                            metadata['taken_at'] = self._parse_exif_datetime(value)
                        elif tag == 37377:  # 光圈
                            metadata['aperture'] = float(value) if isinstance(value, (int, float)) else None
                        elif tag == 37378:  # 快门速度
                            metadata['shutter_speed'] = str(value)
                        elif tag == 33437:  # ISO
                            metadata['iso'] = int(value) if isinstance(value, (int, float)) else None

                # 处理GPS信息 - 使用原始EXIF数据
                gps_info = self._extract_gps_info(raw_exif)
                if gps_info:
                    metadata.update(gps_info)

        except Exception as e:
            # EXIF提取失败，返回空metadata
            # 在并发场景下，另一个线程可能已经成功提取并保存到数据库
            # 最终的数据库记录会通过IntegrityError检测返回已存在记录（包含EXIF）
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
            if gps_data and isinstance(gps_data, dict):
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

    def _fix_image_orientation(self, img) -> object:
        """
        根据EXIF方向信息修复图片方向
        
        :param img: PIL Image对象
        :return: 修复方向后的Image对象
        """
        try:
            # 获取EXIF数据
            exif = img.getexif()
            if not exif:
                return img
            
            # 获取方向信息
            orientation = exif.get(274)  # Orientation标签ID
            if not orientation:
                return img
            
            # 根据方向值旋转图片
            if orientation == 1:
                # 正常方向，无需旋转
                return img
            elif orientation == 2:
                # 水平翻转
                return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                # 旋转180度
                return img.transpose(Image.Transpose.ROTATE_180)
            elif orientation == 4:
                # 垂直翻转
                return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                # 水平翻转 + 逆时针90度
                return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).transpose(Image.Transpose.ROTATE_90)
            elif orientation == 6:
                # 顺时针90度
                return img.transpose(Image.Transpose.ROTATE_270)
            elif orientation == 7:
                # 水平翻转 + 顺时针90度
                return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).transpose(Image.Transpose.ROTATE_270)
            elif orientation == 8:
                # 逆时针90度
                return img.transpose(Image.Transpose.ROTATE_90)
            else:
                # 未知方向，返回原图
                return img
                
        except Exception as e:
            print(f"修复图片方向失败: {str(e)}")
            return img

    def generate_thumbnail(self, source_path: str, max_size: int = None, file_hash: str = None) -> Optional[str]:
        """
        生成缩略图

        :param source_path: 源文件路径
        :param max_size: 缩略图最大尺寸
        :param file_hash: 文件哈希值（用于生成基于哈希的文件名）
        :return: 缩略图路径
        """
        # 延迟导入PIL
        _lazy_import_pil()
        
        if max_size is None:
            max_size = settings.storage.thumbnail_size

        # 🔥 优化：如果提供了file_hash，先检查缩略图是否已存在（避免并发时重复生成）
        if file_hash:
            existing_thumbnail = self._check_thumbnail_by_hash(file_hash)
            if existing_thumbnail:
                # 缩略图已存在，直接返回，避免重复I/O
                return existing_thumbnail

        try:
            with Image.open(source_path) as img:
                # 🔥 修复：根据EXIF方向信息旋转图片
                img = self._fix_image_orientation(img)
                
                # 计算缩略图尺寸
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                # 生成缩略图文件名
                if file_hash:
                    thumbnail_filename = f"{file_hash}_thumb.jpg"
                else:
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

    def convert_heic_to_jpeg(self, heic_path: str, jpeg_path: str, quality: int = 95) -> bool:
        """
        将HEIC格式转换为JPEG格式
        
        :param heic_path: HEIC源文件路径
        :param jpeg_path: 目标JPEG文件路径
        :param quality: JPEG质量 (1-100)，默认95保持高质量
        :return: 是否转换成功
        """
        # 延迟导入PIL
        _lazy_import_pil()
        
        if not HEIC_SUPPORT:
            raise Exception("HEIC格式需要安装pillow-heif库支持")
        
        try:
            # 使用PIL读取HEIC文件
            with Image.open(heic_path) as img:
                # 根据EXIF方向信息旋转图片（保持与缩略图生成一致）
                img = self._fix_image_orientation(img)
                
                # 处理RGBA透明通道（转换为RGB+白色背景）
                if img.mode in ('RGBA', 'LA'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])  # 使用alpha通道作为mask
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    # 转换为RGB格式
                    img = img.convert('RGB')
                
                # 保存为JPEG格式（高质量）
                jpeg_path_obj = Path(jpeg_path)
                jpeg_path_obj.parent.mkdir(parents=True, exist_ok=True)
                img.save(jpeg_path, 'JPEG', quality=quality, optimize=True)
                
                return True
                
        except Exception as e:
            print(f"HEIC转JPEG失败: {str(e)}")
            return False

    def move_to_storage(self, source_path: str, filename: str, file_hash: str = None) -> str:
        """
        将文件移动到存储目录（使用哈希值作为文件名以避免OpenCV中文路径问题）

        :param source_path: 源文件路径
        :param filename: 原始文件名（用于数据库filename字段，保留中文名）
        :param file_hash: 文件哈希值（如果提供，将使用哈希值作为文件系统文件名）
        :return: 存储路径（相对路径）
        """
        # 构造存储路径（按日期组织）
        now = datetime.now()
        date_path = self.originals_path / f"{now.year}" / f"{now.month:02d}"

        # 确保日期目录存在
        date_path.mkdir(parents=True, exist_ok=True)

        # 生成文件系统文件名：如果提供了file_hash，使用哈希值（纯英文，OpenCV友好）
        # 否则使用原始文件名（向后兼容）
        if file_hash:
            file_ext = Path(filename).suffix
            target_filename = f"{file_hash}{file_ext}"
        else:
            target_filename = filename

        # 构造目标路径
        target_path = date_path / target_filename

        # 🔥 修复并发竞态条件：先检查文件是否存在，如果存在则验证hash
        if target_path.exists() and file_hash:
            # 验证已存在文件的hash
            existing_hash = self.calculate_file_hash(str(target_path))
            if existing_hash == file_hash:
                # 是同一个文件，不重复保存
                # 如果是move操作，删除源文件（因为已经有相同文件）
                if Path(source_path).exists():
                    try:
                        Path(source_path).unlink()
                    except Exception:
                        pass  # 忽略删除失败（可能已被其他线程处理）
                try:
                    relative_path = target_path.relative_to(self.storage_base)
                    return str(relative_path)
                except ValueError:
                    return str(target_path)
            # hash不同，极小概率的hash冲突，添加时间戳
            timestamp = int(now.timestamp())
            stem = target_path.stem
            suffix = target_path.suffix
            target_path = date_path / f"{stem}_{timestamp}{suffix}"
        elif target_path.exists():
            # 未提供file_hash，使用时间戳避免冲突
            timestamp = int(now.timestamp())
            stem = target_path.stem
            suffix = target_path.suffix
            target_path = date_path / f"{stem}_{timestamp}{suffix}"

        # 🔥 修复并发竞态条件：使用异常处理捕获文件已存在的情况
        import shutil
        try:
            # 尝试移动文件（原子操作）
            shutil.move(source_path, target_path)
        except (FileExistsError, OSError) as e:
            # 文件已存在（可能是并发导致的），检查是否为相同文件
            if file_hash and target_path.exists():
                existing_hash = self.calculate_file_hash(str(target_path))
                if existing_hash == file_hash:
                    # 是同一个文件，删除源文件，返回已存在路径
                    try:
                        if Path(source_path).exists():
                            Path(source_path).unlink()
                    except Exception:
                        pass
                    try:
                        relative_path = target_path.relative_to(self.storage_base)
                        return str(relative_path)
                    except ValueError:
                        return str(target_path)
            # hash不同或无法判断，添加时间戳重试
            timestamp = int(datetime.now().timestamp())
            stem = Path(target_path).stem
            suffix = Path(target_path).suffix
            target_path = date_path / f"{stem}_{timestamp}{suffix}"
            # 如果源文件还存在，重试移动
            if Path(source_path).exists():
                shutil.move(source_path, target_path)
            else:
                # 源文件已被删除（可能被其他线程处理），检查目标文件是否已存在
                if target_path.exists():
                    try:
                        relative_path = target_path.relative_to(self.storage_base)
                        return str(relative_path)
                    except ValueError:
                        return str(target_path)
                # 如果目标文件也不存在，返回原目标路径（虽然不应该到这里）
                try:
                    relative_path = target_path.relative_to(self.storage_base)
                    return str(relative_path)
                except ValueError:
                    return str(target_path)

        # 返回相对路径（相对于storage_base）
        try:
            relative_path = target_path.relative_to(self.storage_base)
            return str(relative_path)
        except ValueError:
            # 如果路径不在storage_base下，返回绝对路径
            return str(target_path)

    def copy_to_storage(self, source_path: str, filename: str, file_hash: str = None) -> str:
        """
        将文件复制到存储目录（使用哈希值作为文件名以避免OpenCV中文路径问题）

        :param source_path: 源文件路径
        :param filename: 原始文件名（用于数据库filename字段，保留中文名）
        :param file_hash: 文件哈希值（如果提供，将使用哈希值作为文件系统文件名）
        :return: 存储路径（相对路径）
        """
        # 构造存储路径（按日期组织）
        now = datetime.now()
        date_path = self.originals_path / f"{now.year}" / f"{now.month:02d}"

        # 确保日期目录存在
        date_path.mkdir(parents=True, exist_ok=True)

        # 生成文件系统文件名：如果提供了file_hash，使用哈希值（纯英文，OpenCV友好）
        # 否则使用原始文件名（向后兼容）
        if file_hash:
            file_ext = Path(filename).suffix
            target_filename = f"{file_hash}{file_ext}"
        else:
            target_filename = filename

        # 构造目标路径
        target_path = date_path / target_filename

        # 🔥 修复并发竞态条件：先检查文件是否存在，如果存在则验证hash
        if target_path.exists() and file_hash:
            # 验证已存在文件的hash
            existing_hash = self.calculate_file_hash(str(target_path))
            if existing_hash == file_hash:
                # 是同一个文件，不重复保存，直接返回已存在的路径
                try:
                    relative_path = target_path.relative_to(self.storage_base)
                    return str(relative_path)
                except ValueError:
                    return str(target_path)
            # hash不同，极小概率的hash冲突，添加时间戳
            timestamp = int(now.timestamp())
            stem = target_path.stem
            suffix = target_path.suffix
            target_path = date_path / f"{stem}_{timestamp}{suffix}"
        elif target_path.exists():
            # 未提供file_hash，使用时间戳避免冲突
            timestamp = int(now.timestamp())
            stem = target_path.stem
            suffix = target_path.suffix
            target_path = date_path / f"{stem}_{timestamp}{suffix}"

        # 🔥 修复并发竞态条件：使用异常处理捕获文件已存在的情况
        import shutil
        try:
            # 尝试复制文件（原子操作）
            shutil.copy2(source_path, target_path)
        except (FileExistsError, OSError) as e:
            # 文件已存在（可能是并发导致的），检查是否为相同文件
            if file_hash and target_path.exists():
                existing_hash = self.calculate_file_hash(str(target_path))
                if existing_hash == file_hash:
                    # 是同一个文件，返回已存在路径（copy操作不需要删除源文件）
                    try:
                        relative_path = target_path.relative_to(self.storage_base)
                        return str(relative_path)
                    except ValueError:
                        return str(target_path)
            # hash不同或无法判断，添加时间戳重试
            timestamp = int(datetime.now().timestamp())
            stem = Path(target_path).stem
            suffix = Path(target_path).suffix
            target_path = date_path / f"{stem}_{timestamp}{suffix}"
            # 重试复制
            shutil.copy2(source_path, target_path)

        # 返回相对路径（相对于storage_base）
        try:
            relative_path = target_path.relative_to(self.storage_base)
            return str(relative_path)
        except ValueError:
            # 如果路径不在storage_base下，返回绝对路径
            return str(target_path)

    def _check_duplicate_file(self, file_hash: str, db_session) -> Dict:
        """
        检查文件是否重复（简化版：只检查数据库）
        
        :param file_hash: 文件哈希值
        :param db_session: 数据库会话
        :return: 重复检查结果
        """
        from app.models.photo import Photo
        
        # 查询数据库是否有相同hash的记录
        existing_photo = db_session.query(Photo).filter(Photo.file_hash == file_hash).first()
        
        if existing_photo:
            # 数据库有记录 = 完全重复，跳过导入
            # 数据库是权威来源，不需要检查文件是否存在
            # 文件丢失/恢复应在维护流程中处理，不在导入流程中
            return {
                "is_duplicate": True,
                "message": "文件已存在，跳过导入",
                "duplicate_type": "full_duplicate",
                "existing_photo": existing_photo
            }
        
        # 数据库无记录 = 全新文件
        return {
            "is_duplicate": False,
            "message": "全新文件",
            "duplicate_type": "new_file"
        }

    def _check_thumbnail_by_hash(self, file_hash: str) -> Optional[str]:
        """基于哈希值检查缩略图是否存在"""
        thumbnail_path = self.thumbnails_path / f"{file_hash}_thumb.jpg"
        if thumbnail_path.exists():
            return str(thumbnail_path)
        return None

    def _get_thumbnail_path_by_hash(self, file_hash: str) -> str:
        """根据文件哈希值生成缩略图路径"""
        return str(self.thumbnails_path / f"{file_hash}_thumb.jpg")

    def _handle_full_duplicate_completed(self, duplicate_result: Dict) -> Tuple[bool, str, Optional[PhotoCreate], Optional[Dict]]:
        """处理已完成智能处理的完全重复文件"""
        return False, duplicate_result['message'], None, None

    def _handle_full_duplicate_incomplete(self, duplicate_result: Dict) -> Tuple[bool, str, Optional[PhotoCreate], Optional[Dict]]:
        """处理未完成智能处理的完全重复文件"""
        existing_photo = duplicate_result['existing_photo']
        
        if existing_photo.status == 'error':
            # 错误状态，重新开始处理
            existing_photo.status = 'imported'
            # 注意：这里需要db_session，但方法签名中没有，需要在调用时处理
            return True, "文件已存在，重新开始智能处理", None, None
        elif existing_photo.status == 'imported':
            # 已导入但未处理，继续处理
            return True, "文件已存在，继续智能处理", None, None
        elif existing_photo.status == 'analyzing':
            # 正在处理中，提供选项
            return False, "文件正在处理中，请稍候或选择强制重新处理", None, {
                'force_retry': True,
                'current_status': 'analyzing'
            }
        
        return False, "未知状态", None, None

    def _handle_orphan_cleaned(self, duplicate_result: Dict, file_path: str, file_hash: str, db_session=None, original_filename: Optional[str] = None) -> Tuple[bool, str, Optional[PhotoCreate], Optional[Dict]]:
        """处理孤儿记录清理后的文件"""
        print(f"孤儿记录已清理: {duplicate_result['message']}")
        
        # 检查是否有对应的缩略图需要清理
        thumbnail_path = self._get_thumbnail_path_by_hash(file_hash)
        if thumbnail_path and Path(thumbnail_path).exists():
            Path(thumbnail_path).unlink()
            print(f"清理孤儿缩略图: {thumbnail_path}")
        
        # 清理孤儿记录的分析结果
        if db_session:
            self._cleanup_orphan_analysis_results(file_hash, db_session)
        
        # 继续正常处理流程
        return self._handle_new_file(file_path, file_hash, move_file=True, db_session=db_session, original_filename=original_filename)

    def _cleanup_orphan_analysis_results(self, file_hash: str, db_session=None):
        """清理孤儿记录的分析结果"""
        if not db_session:
            print(f"清理孤儿分析结果需要数据库会话: {file_hash}")
            return
            
        try:
            from app.models.photo import Photo, PhotoAnalysis, PhotoQuality, PhotoCategory

            # 清理AI分析结果
            analysis_results = db_session.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id.in_(
                    db_session.query(Photo.id).filter(Photo.file_hash == file_hash)
                )
            ).all()
            for result in analysis_results:
                db_session.delete(result)

            # 清理质量评估结果
            quality_results = db_session.query(PhotoQuality).filter(
                PhotoQuality.photo_id.in_(
                    db_session.query(Photo.id).filter(Photo.file_hash == file_hash)
                )
            ).all()
            for result in quality_results:
                db_session.delete(result)

            # 清理照片分类结果（PhotoCategory表）
            category_results = db_session.query(PhotoCategory).filter(
                PhotoCategory.photo_id.in_(
                    db_session.query(Photo.id).filter(Photo.file_hash == file_hash)
                )
            ).all()
            for result in category_results:
                db_session.delete(result)

            db_session.commit()
            print(f"清理孤儿分析结果完成: {file_hash}")

        except Exception as e:
            print(f"清理孤儿分析结果失败: {e}")
            db_session.rollback()

    def _handle_physical_duplicate(self, duplicate_result: Dict, file_path: str, file_hash: str, original_filename: Optional[str] = None) -> Tuple[bool, str, Optional[PhotoCreate], Optional[Dict]]:
        """
        处理物理重复的文件
        
        :param original_filename: 原始文件名（保留参数以保持API一致性，但不再使用）
        """
        existing_path = duplicate_result['existing_path']
        
        # 检查缩略图是否已存在
        existing_thumbnail = self._check_thumbnail_by_hash(file_hash)
        if existing_thumbnail:
            thumbnail_path = existing_thumbnail
        else:
            thumbnail_path = self.generate_thumbnail(existing_path, file_hash=file_hash)
        
        # 提取元数据
        exif_data = self.extract_exif_metadata(existing_path)
        
        # 创建数据库记录（filename会使用existing_path中的文件名，保持与original_path一致）
        photo_data = self.create_photo_record(existing_path, {
            'thumbnail_path': thumbnail_path,
            **exif_data
        })
        
        return True, "文件已存在，使用现有文件", photo_data, None

    def _handle_new_file(self, file_path: str, file_hash: str, move_file: bool, db_session=None, original_filename: Optional[str] = None) -> Tuple[bool, str, Optional[PhotoCreate], Optional[Dict]]:
        """
        处理全新文件
        
        :param file_path: 文件路径
        :param file_hash: 文件哈希值
        :param move_file: 是否移动文件
        :param db_session: 数据库会话
        :param original_filename: 原始文件名（用户上传的文件名，用于存储文件时作为目标文件名）
        :return: (是否成功, 消息, 照片数据, 重复信息)
        """
        try:
            # 🔥 优化：在文件系统操作前检查数据库（唯一检查点，减少并发窗口期）
            # 这样即使第一个线程刚commit，第二个线程也能立即看到并跳过文件系统操作
            if db_session:
                from app.models.photo import Photo
                existing_photo = db_session.query(Photo).filter(Photo.file_hash == file_hash).first()
                if existing_photo:
                    # 数据库已有记录，跳过导入（不操作文件系统）
                    return False, "文件已存在，跳过导入", None, {
                        "is_duplicate": True,
                        "message": "文件已存在，跳过导入",
                        "duplicate_type": "full_duplicate",
                        "existing_photo": existing_photo
                    }
            
            # 先验证文件，获取格式信息
            is_valid, error_msg, file_info = self.validate_photo_file(file_path)
            if not is_valid:
                return False, error_msg, None, None
            
            format_name = file_info.get('format', '').upper() if file_info else ''
            is_heic = format_name in ['HEIC', 'HEIF']
            
            # 确保有原始文件名（用于数据库filename字段，保留中文名）
            if original_filename is None:
                original_filename = Path(file_path).name
            
            # 存储文件（使用哈希值作为文件名，避免OpenCV中文路径问题）
            # HEIC文件会先存储为HEIC格式，然后转换为JPEG，但保留HEIC原图
            # 注意：存储方法返回的是相对路径（相对于storage_base）
            if move_file:
                storage_path = self.move_to_storage(file_path, original_filename, file_hash=file_hash)
            else:
                storage_path = self.copy_to_storage(file_path, original_filename, file_hash=file_hash)
            
            # 构建完整路径（用于后续的文件操作）
            storage_base = self.storage_base
            
            # 如果是HEIC格式，需要特殊处理：先提取元数据，再转换
            if is_heic:
                # storage_path已经是相对路径，需要构建完整路径用于文件操作
                heic_full_path = storage_base / storage_path  # 完整的HEIC文件路径
                
                # 🔥 关键修复：在转换前从原始HEIC文件提取EXIF元数据
                # 这样可以确保获取到完整的元数据，因为转换后的JPEG可能丢失EXIF信息
                exif_data = self.extract_exif_metadata(str(heic_full_path))
                
                # 生成JPEG路径（使用相同文件名但扩展名为.jpg）
                jpeg_relative_path = Path(storage_path).with_suffix('.jpg')
                jpeg_full_path = storage_base / jpeg_relative_path
                
                # 🔥 优化：检查JPEG是否已存在（避免重复转换和不必要的提示）
                if jpeg_full_path.exists():
                    # JPEG已存在，直接使用，不进行转换
                    storage_path = str(jpeg_relative_path)
                    storage_full_path = jpeg_full_path
                    # 不输出提示，因为并没有进行转换
                else:
                    # JPEG不存在，需要转换
                    try:
                        # 转换为JPEG（不删除HEIC原图，让它和JPEG共存）
                        success = self.convert_heic_to_jpeg(str(heic_full_path), str(jpeg_full_path))
                        if not success:
                            return False, "HEIC转JPEG失败", None, None
                        
                        # 不删除HEIC原图，保留它用于下载
                        # HEIC原图：originals/2025/10/{file_hash}.heic
                        # JPEG文件：originals/2025/10/{file_hash}.jpg
                        
                        # 使用JPEG相对路径作为storage_path（用于所有处理）
                        storage_path = str(jpeg_relative_path)
                        storage_full_path = jpeg_full_path
                        print(f"HEIC已转换为JPEG，原图已保留: {heic_full_path}")
                        
                    except Exception as e:
                        print(f"HEIC转JPEG失败: {e}")
                        return False, f"HEIC转JPEG失败: {str(e)}", None, None
            else:
                # 非HEIC格式：构建完整路径
                storage_full_path = storage_base / storage_path
                # 提取元数据（从原始文件）
                exif_data = self.extract_exif_metadata(str(storage_full_path))
            
            # 生成缩略图（使用完整路径）
            thumbnail_path = self.generate_thumbnail(str(storage_full_path), file_hash=file_hash)
            
            # 如果是HEIC格式，在metadata中传递原始format（用于数据库记录）
            # 因为storage_path已经是JPEG了，create_photo_record会读取为JPEG
            metadata_for_record = {
                'thumbnail_path': thumbnail_path,
                **exif_data
            }
            if is_heic:
                # 传递原始格式信息，create_photo_record会优先使用这个
                metadata_for_record['original_format'] = format_name  # 'HEIC'或'HEIF'
            
            # 创建数据库记录
            # 对于HEIC格式，filename应该保持原始HEIC文件名（.heic扩展名），而不是转换后的JPEG文件名
            # 但original_path指向转换后的JPEG路径（用于所有处理）
            record_filename = None
            if is_heic and original_filename:
                # 保持原始HEIC文件名
                record_filename = original_filename
            # create_photo_record需要完整路径用于读取文件信息
            photo_data = self.create_photo_record(str(storage_full_path), metadata_for_record, record_filename=record_filename)
            
            return True, "文件导入成功", photo_data, None
            
        except Exception as e:
            print(f"处理全新文件失败: {e}")
            return False, f"文件处理失败: {str(e)}", None, None

    def create_photo_record(self, file_path: str, metadata: Dict[str, Any], record_filename: Optional[str] = None) -> PhotoCreate:
        """
        创建照片记录

        :param file_path: 文件路径（存储后的文件路径）
        :param metadata: 元数据
        :param record_filename: 用于数据库filename字段的文件名（如果提供，优先使用；否则使用file_path中的文件名）
                               对于HEIC格式，应该传递原始HEIC文件名以保持.heic扩展名
        :return: PhotoCreate对象
        """
        file_path_obj = Path(file_path)

        # 基本文件信息
        # 如果提供了record_filename（如HEIC格式的原始文件名），优先使用
        # 否则使用存储后的文件名（与original_path保持一致）
        filename = record_filename if record_filename else file_path_obj.name
        file_size = file_path_obj.stat().st_size

        # 获取图像尺寸
        width, height = 0, 0
        format_name = ""
        
        # 如果metadata中提供了original_format（HEIC转换的情况），优先使用原始格式
        if metadata.get('original_format'):
            format_name = metadata.get('original_format')
            # 仍然需要从文件读取尺寸
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
            except Exception as e:
                print(f"获取图像尺寸失败: {str(e)}")
        else:
            # 正常情况：从文件读取格式和尺寸
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

        # 计算相对路径（相对于storage_base）
        try:
            relative_path = file_path_obj.relative_to(self.storage_base)
        except ValueError:
            # 如果路径不在storage_base下，使用绝对路径
            relative_path = file_path_obj

        # 处理缩略图路径
        thumbnail_path = metadata.get('thumbnail_path', '')
        if thumbnail_path:
            try:
                thumbnail_path_obj = Path(thumbnail_path)
                thumbnail_relative = thumbnail_path_obj.relative_to(self.storage_base)
                metadata['thumbnail_path'] = str(thumbnail_relative)
            except ValueError:
                # 如果缩略图路径不在storage_base下，保持原路径
                pass

        # 合并元数据
        photo_data = {
            'filename': filename,
            'original_path': str(relative_path),  # 存储相对路径
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

    def process_single_photo(self, file_path: str, move_file: bool = True, db_session=None, original_filename: Optional[str] = None) -> Tuple[bool, str, Optional[PhotoCreate], Optional[Dict]]:
        """
        处理单个照片文件的完整流程

        :param file_path: 文件路径
        :param move_file: 是否移动文件
        :param db_session: 数据库会话（用于重复检查）
        :param original_filename: 原始文件名（用户上传的文件名，用于存储文件时作为目标文件名）
        :return: (是否成功, 消息, 照片数据, 重复信息)
        """
        try:
            # 1. 文件验证
            is_valid, error_msg, file_info = self.validate_photo_file(file_path)
            if not is_valid:
                return False, error_msg, None, None

            # 2. 计算文件哈希
            file_hash = self.calculate_file_hash(file_path)
            
            # 3. 正常处理流程（重复检查移到 _handle_new_file 中进行，减少窗口期）
            # 如果没有提供original_filename，尝试从file_path推断（用于文件夹路径导入的情况）
            if original_filename is None:
                # 对于文件夹路径导入，file_path本身就是真实路径，文件名是正确的
                original_filename = Path(file_path).name
            
            success, message, photo_data, duplicate_info = self._handle_new_file(file_path, file_hash, move_file, db_session, original_filename=original_filename)
            
            return success, message, photo_data, duplicate_info
            
        except Exception as e:
            print(f"处理照片时发生错误: {e}")
            return False, f"处理失败: {str(e)}", None, None
