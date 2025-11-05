"""
API路由模块初始化文件

负责API路由的注册和组织

作者：AI助手
创建日期：2025年9月9日
"""

from fastapi import APIRouter

from .health import router as health_router
from .photos import router as photos_router
from .import_photos import router as import_router
from .analysis import router as analysis_router
from .tags import router as tags_router
from .categories import router as categories_router
from .storage import router as storage_router
from .search import router as search_router
from .enhanced_search import router as enhanced_search_router
from .config import router as config_router
from .face import router as face_router
from .person_management import router as person_management_router
from .image_features import router as image_features_router

# 创建主API路由
router = APIRouter()

# 注册子路由
router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(photos_router, prefix="/photos", tags=["photos"])
router.include_router(import_router, prefix="/import", tags=["import"])
router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
router.include_router(tags_router, prefix="/tags", tags=["tags"])
router.include_router(categories_router, prefix="/categories", tags=["categories"])
router.include_router(storage_router, prefix="/storage", tags=["storage"])
router.include_router(search_router, prefix="/search", tags=["search"])
router.include_router(enhanced_search_router, prefix="/enhanced-search", tags=["enhanced-search"])
router.include_router(config_router, prefix="/config", tags=["config"])
router.include_router(face_router, tags=["face_recognition"])
router.include_router(person_management_router, tags=["person_management"])
router.include_router(image_features_router, tags=["image_features"])

__all__ = ["router"]
