"""
照片数据模型

定义照片相关的Pydantic数据模型

作者：AI助手
创建日期：2025年9月9日
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PhotoBase(BaseModel):
    """照片基础模型"""
    filename: str = Field(..., max_length=255, description="文件名")
    original_path: str = Field(..., max_length=500, description="原始文件路径")
    thumbnail_path: Optional[str] = Field(None, max_length=500, description="缩略图路径")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    width: int = Field(..., ge=0, description="图片宽度")
    height: int = Field(..., ge=0, description="图片高度")
    format: str = Field(..., max_length=10, description="图片格式")
    file_hash: str = Field(..., max_length=64, description="文件MD5哈希")
    perceptual_hash: Optional[str] = Field(None, max_length=16, description="感知哈希")


class PhotoCreate(PhotoBase):
    """创建照片的请求模型"""
    pass


class PhotoUpdate(BaseModel):
    """更新照片的请求模型"""
    filename: Optional[str] = Field(None, max_length=255)
    thumbnail_path: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=20)
    import_source: Optional[str] = Field(None, max_length=100)


class PhotoResponse(PhotoBase):
    """照片响应模型"""
    id: int
    taken_at: Optional[datetime]
    camera_make: Optional[str] = Field(None, max_length=100)
    camera_model: Optional[str] = Field(None, max_length=100)
    lens_model: Optional[str] = Field(None, max_length=100)
    focal_length: Optional[float]
    aperture: Optional[float]
    shutter_speed: Optional[str] = Field(None, max_length=20)
    iso: Optional[int]
    flash: Optional[str] = Field(None, max_length=20)
    white_balance: Optional[str] = Field(None, max_length=20)
    exposure_mode: Optional[str] = Field(None, max_length=20)
    metering_mode: Optional[str] = Field(None, max_length=20)
    orientation: Optional[int]
    location_lat: Optional[float]
    location_lng: Optional[float]
    location_alt: Optional[float]
    location_name: Optional[str] = Field(None, max_length=200)
    status: str = Field(..., max_length=20)
    import_source: Optional[str] = Field(None, max_length=100)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PhotoListResponse(BaseModel):
    """照片列表响应模型"""
    items: List[PhotoResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class PhotoUploadResponse(BaseModel):
    """照片上传响应模型"""
    id: int
    filename: str
    file_size: int
    upload_status: str
    message: str
