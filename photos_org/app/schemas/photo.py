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
    taken_at: Optional[datetime] = Field(None, description="拍摄时间")
    camera_make: Optional[str] = Field(None, max_length=100, description="相机品牌")
    camera_model: Optional[str] = Field(None, max_length=100, description="相机型号")
    lens_model: Optional[str] = Field(None, max_length=100, description="镜头型号")
    focal_length: Optional[float] = Field(None, description="焦距")
    aperture: Optional[float] = Field(None, description="光圈")
    shutter_speed: Optional[str] = Field(None, max_length=20, description="快门速度")
    iso: Optional[int] = Field(None, description="ISO")
    flash: Optional[str] = Field(None, max_length=50, description="闪光灯")
    white_balance: Optional[str] = Field(None, max_length=50, description="白平衡")
    exposure_mode: Optional[str] = Field(None, max_length=50, description="曝光模式")
    metering_mode: Optional[str] = Field(None, max_length=50, description="测光模式")
    orientation: Optional[int] = Field(None, description="方向")
    location_lat: Optional[float] = Field(None, description="GPS纬度")
    location_lng: Optional[float] = Field(None, description="GPS经度")
    location_alt: Optional[float] = Field(None, description="GPS海拔")
    location_name: Optional[str] = Field(None, max_length=200, description="地点名称")
    import_source: Optional[str] = Field(None, max_length=100, description="导入来源")


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


# 搜索相关的数据模型

class PhotoAnalysisInfo(BaseModel):
    """照片分析信息"""
    description: str = Field("", description="AI生成的描述")
    scene_type: str = Field("", description="场景类型")
    objects: List[str] = Field(default_factory=list, description="识别的物体")
    tags: List[str] = Field(default_factory=list, description="AI生成的标签")
    confidence: float = Field(0.0, description="置信度")


class PhotoQualityInfo(BaseModel):
    """照片质量信息"""
    score: float = Field(0.0, description="综合质量分数")
    level: str = Field("", description="质量等级")
    sharpness: float = Field(0.0, description="清晰度分数")
    brightness: float = Field(0.0, description="亮度分数")
    contrast: float = Field(0.0, description="对比度分数")
    color: float = Field(0.0, description="色彩质量分数")
    composition: float = Field(0.0, description="构图分数")
    issues: dict = Field(default_factory=dict, description="技术问题")


class PhotoSearchResult(BaseModel):
    """搜索结果中的照片信息"""
    id: int = Field(..., description="照片ID")
    filename: str = Field(..., description="文件名")
    original_path: str = Field(..., description="原始路径")
    thumbnail_path: Optional[str] = Field(None, description="缩略图路径")
    file_size: int = Field(..., description="文件大小")
    width: int = Field(..., description="宽度")
    height: int = Field(..., description="高度")
    format: str = Field(..., description="格式")
    taken_at: Optional[str] = Field(None, description="拍摄时间")
    camera_make: Optional[str] = Field(None, description="相机品牌")
    camera_model: Optional[str] = Field(None, description="相机型号")
    location_lat: Optional[float] = Field(None, description="纬度")
    location_lng: Optional[float] = Field(None, description="经度")
    location_name: Optional[str] = Field(None, description="地点名称")
    description: Optional[str] = Field(None, description="照片描述")
    status: str = Field(..., description="状态")
    created_at: Optional[str] = Field(None, description="创建时间")
    is_favorite: bool = Field(False, description="是否收藏")

    analysis: Optional[PhotoAnalysisInfo] = Field(None, description="AI分析结果")
    quality: Optional[PhotoQualityInfo] = Field(None, description="质量评估")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    categories: List[str] = Field(default_factory=list, description="分类列表")


class PhotoSearchResponse(BaseModel):
    """照片搜索响应"""
    success: bool = Field(True, description="是否成功")
    data: List[PhotoSearchResult] = Field(default_factory=list, description="搜索结果")
    total: int = Field(0, description="总结果数")
    limit: int = Field(50, description="每页数量")
    offset: int = Field(0, description="偏移量")


class SearchSuggestionsResponse(BaseModel):
    """搜索建议响应"""
    success: bool = Field(True, description="是否成功")
    data: dict = Field(default_factory=dict, description="搜索建议")


class SearchStatsResponse(BaseModel):
    """搜索统计响应"""
    success: bool = Field(True, description="是否成功")
    data: dict = Field(default_factory=dict, description="统计数据")
