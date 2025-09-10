"""
数据模型模块初始化文件

导出所有Pydantic数据模型

作者：AI助手
创建日期：2025年9月9日
"""

from .photo import (
    PhotoBase,
    PhotoCreate,
    PhotoUpdate,
    PhotoResponse,
    PhotoListResponse,
    PhotoUploadResponse,
)

__all__ = [
    "PhotoBase",
    "PhotoCreate",
    "PhotoUpdate",
    "PhotoResponse",
    "PhotoListResponse",
    "PhotoUploadResponse",
]
