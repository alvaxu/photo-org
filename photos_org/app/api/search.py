"""
家庭单机版智能照片整理系统 - 搜索API
提供搜索相关的API接口
"""
from typing import List, Optional
from datetime import date
from urllib.parse import unquote
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.search_service import SearchService
from app.models.photo import Photo
from app.schemas.photo import PhotoSearchResponse, SearchSuggestionsResponse, SearchStatsResponse

router = APIRouter(tags=["搜索"])

search_service = SearchService()


@router.get("/photos", response_model=PhotoSearchResponse)
async def search_photos(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    camera_make: Optional[str] = Query(None, description="相机品牌"),
    camera_model: Optional[str] = Query(None, description="相机型号"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    quality_min: Optional[float] = Query(None, ge=0, le=100, description="最低质量分数"),
    quality_level: Optional[str] = Query(None, description="质量等级"),
    tags: Optional[List[str]] = Query(None, description="标签列表"),
    categories: Optional[List[str]] = Query(None, description="分类列表"),
    location_lat: Optional[float] = Query(None, description="纬度"),
    location_lng: Optional[float] = Query(None, description="经度"),
    location_radius: Optional[float] = Query(None, ge=0, description="搜索半径(公里)"),
    sort_by: str = Query("taken_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    综合搜索照片

    支持多种搜索条件组合：
    - 关键词搜索（文件名、描述、标签等）
    - 相机筛选
    - 日期范围筛选
    - 质量筛选
    - 标签筛选
    - 分类筛选
    - 地理位置筛选
    - 多维度排序和分页
    """
    try:
        # 处理中文关键词解码
        if keyword:
            keyword = unquote(keyword)
        
        results, total = search_service.search_photos(
            db=db,
            keyword=keyword,
            camera_make=camera_make,
            camera_model=camera_model,
            date_from=date_from,
            date_to=date_to,
            quality_min=quality_min,
            quality_level=quality_level,
            tags=tags,
            categories=categories,
            location_lat=location_lat,
            location_lng=location_lng,
            location_radius=location_radius,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )

        return PhotoSearchResponse(
            success=True,
            data=results,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    prefix: str = Query(..., min_length=1, max_length=50, description="搜索前缀"),
    limit: int = Query(10, ge=1, le=50, description="建议数量限制"),
    db: Session = Depends(get_db)
):
    """
    获取搜索建议

    根据输入的前缀提供智能搜索建议：
    - 标签建议
    - 分类建议
    - 相机品牌建议
    - 相机型号建议
    """
    try:
        suggestions = search_service.get_search_suggestions(
            db=db,
            prefix=prefix,
            limit=limit
        )

        return SearchSuggestionsResponse(
            success=True,
            data=suggestions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取搜索建议失败: {str(e)}")


@router.get("/stats", response_model=SearchStatsResponse)
async def get_search_stats(db: Session = Depends(get_db)):
    """
    获取搜索统计信息

    返回系统的统计数据：
    - 照片总数
    - 标签总数
    - 分类总数
    - 质量分布
    - 时间分布
    - 相机分布
    """
    try:
        stats = search_service.get_search_stats(db=db)

        return SearchStatsResponse(
            success=True,
            data=stats
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/photos/{photo_id}")
async def get_photo_detail(
    photo_id: int,
    db: Session = Depends(get_db)
):
    """
    获取照片详细信息

    返回指定照片的完整信息，包括：
    - 基本信息
    - AI分析结果
    - 质量评估
    - 标签和分类
    """
    try:
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")

        result = search_service._format_photo_result(db=db, photo=photo)

        if not result:
            raise HTTPException(status_code=404, detail="照片不存在")

        return {
            "success": True,
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取照片详情失败: {str(e)}")


@router.get("/advanced")
async def advanced_search_help():
    """
    高级搜索帮助

    返回高级搜索功能的详细说明和使用示例
    """
    help_info = {
        "search_parameters": {
            "keyword": "支持文件名、描述、标签的全文搜索",
            "camera_make": "相机品牌筛选",
            "camera_model": "相机型号筛选",
            "date_from": "开始日期 (YYYY-MM-DD)",
            "date_to": "结束日期 (YYYY-MM-DD)",
            "quality_min": "最低质量分数 (0-100)",
            "quality_level": "质量等级 (优秀/良好/一般/较差/很差)",
            "tags": "标签列表 (支持多个)",
            "categories": "分类列表 (支持多个)",
            "location_lat": "纬度",
            "location_lng": "经度",
            "location_radius": "搜索半径(公里)",
            "sort_by": "排序字段 (taken_at/filename/file_size/created_at)",
            "sort_order": "排序顺序 (asc/desc)",
            "limit": "返回数量 (1-200)",
            "offset": "偏移量 (分页使用)"
        },
        "examples": {
            "basic_search": "/search/photos?keyword=生日",
            "advanced_search": "/search/photos?camera_make=Apple&date_from=2025-01-01&quality_min=80&sort_by=taken_at&sort_order=desc",
            "location_search": "/search/photos?location_lat=31.264&location_lng=121.410&location_radius=5",
            "tag_search": "/search/photos?tags=室内&tags=自拍"
        },
        "sort_options": ["taken_at", "filename", "file_size", "created_at"],
        "quality_levels": ["优秀", "良好", "一般", "较差", "很差"]
    }

    return {
        "success": True,
        "data": help_info
    }
