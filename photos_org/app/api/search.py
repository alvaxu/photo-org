"""
家庭版智能照片系统 - 搜索API
提供搜索相关的API接口
"""
from typing import List, Optional
from datetime import date
from urllib.parse import unquote
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.search_service import SearchService
from app.models.photo import Photo, PhotoAnalysis, PhotoQuality, PhotoTag, PhotoCategory
from app.schemas.photo import PhotoSearchResponse, SearchSuggestionsResponse, SearchStatsResponse

router = APIRouter(tags=["搜索"])

search_service = SearchService()


@router.get("/photos", response_model=PhotoSearchResponse)
async def search_photos(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    search_type: str = Query("all", description="搜索类型"),
    camera_make: Optional[str] = Query(None, description="相机品牌"),
    camera_model: Optional[str] = Query(None, description="相机型号"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    start_date: Optional[date] = Query(None, description="自定义开始日期"),
    end_date: Optional[date] = Query(None, description="自定义结束日期"),
    date_filter: Optional[str] = Query(None, description="日期筛选类型"),
    quality_min: Optional[float] = Query(None, ge=0, le=100, description="最低质量分数"),
    quality_level: Optional[str] = Query(None, description="质量等级"),
    quality_filter: Optional[str] = Query(None, description="质量筛选"),
    face_count_min: Optional[int] = Query(None, ge=0, description="最少人脸数"),
    face_count_max: Optional[int] = Query(None, ge=0, description="最多人脸数"),
    face_count_filter: Optional[str] = Query(None, description="人脸数量筛选"),
    format_filter: Optional[str] = Query(None, description="格式筛选"),
    camera_filter: Optional[str] = Query(None, description="相机筛选"),
    person_filter: str = Query("all", description="人物筛选"),
    tags: Optional[List[str]] = Query(None, description="标签列表"),
    categories: Optional[List[str]] = Query(None, description="分类列表"),
    tag_ids: Optional[str] = Query(None, description="标签ID列表(逗号分隔)"),
    category_ids: Optional[str] = Query(None, description="分类ID列表(逗号分隔)"),
    location_lat: Optional[float] = Query(None, description="纬度"),
    location_lng: Optional[float] = Query(None, description="经度"),
    location_radius: Optional[float] = Query(None, ge=0, description="搜索半径(公里)"),
    sort_by: str = Query("taken_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序"),
    limit: int = Query(50, ge=1, le=1000, description="返回数量"),
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
    - 标签筛选（与关系：必须包含所有选中的标签）
    - 分类筛选（与关系：必须包含所有选中的分类）
    - 地理位置筛选
    - 多维度排序和分页
    """
    try:
        # 处理中文关键词解码
        if keyword:
            keyword = unquote(keyword)
        
        # 处理日期筛选
        processed_date_from = date_from
        processed_date_to = date_to
        
        # 如果使用自定义日期范围
        if start_date or end_date:
            processed_date_from = start_date
            processed_date_to = end_date
        # 如果使用预设日期筛选
        elif date_filter:
            from datetime import datetime, timedelta
            today = datetime.now().date()

            if date_filter == "today":
                processed_date_from = today
                processed_date_to = today
            elif date_filter == "yesterday":
                yesterday = today - timedelta(days=1)
                processed_date_from = yesterday
                processed_date_to = yesterday
            elif date_filter == "last_7_days":
                processed_date_from = today - timedelta(days=7)
                processed_date_to = today
            elif date_filter == "last_30_days":
                processed_date_from = today - timedelta(days=30)
                processed_date_to = today
            elif date_filter == "last_month":
                # 获取上个月的日期范围
                first_day_of_current_month = today.replace(day=1)
                last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
                first_day_of_last_month = last_day_of_last_month.replace(day=1)
                processed_date_from = first_day_of_last_month
                processed_date_to = last_day_of_last_month
            elif date_filter == "this_year":
                processed_date_from = today.replace(month=1, day=1)
                processed_date_to = today
            elif date_filter == "last_year":
                processed_date_from = date(today.year - 1, 1, 1)
                processed_date_to = date(today.year - 1, 12, 31)
            elif date_filter == "no_date":
                # 特殊处理：无拍摄时间，使用特殊标识值
                processed_date_from = "no_date"
                processed_date_to = "no_date"
        
        # 处理质量筛选
        processed_quality_level = quality_level or quality_filter
        
        # 处理人脸数量筛选
        processed_face_count_min = face_count_min
        processed_face_count_max = face_count_max
        
        if face_count_filter:
            # 处理预设的人脸数量筛选
            if face_count_filter == "0":
                processed_face_count_min = 0
                processed_face_count_max = 0
            elif face_count_filter == "1":
                processed_face_count_min = 1
                processed_face_count_max = 1
            elif face_count_filter == "2":
                processed_face_count_min = 2
                processed_face_count_max = 2
            elif face_count_filter == "3":
                processed_face_count_min = 3
                processed_face_count_max = 3
            elif face_count_filter == "4":
                processed_face_count_min = 4
                processed_face_count_max = 4
            elif face_count_filter == "5":
                processed_face_count_min = 5
                processed_face_count_max = 5
            elif face_count_filter == "6":
                processed_face_count_min = 6
                processed_face_count_max = 6
            elif face_count_filter == "7":
                processed_face_count_min = 7
                processed_face_count_max = 7
            elif face_count_filter == "8":
                processed_face_count_min = 8
                processed_face_count_max = 8
            elif face_count_filter == "9":
                processed_face_count_min = 9
                processed_face_count_max = 9
            elif face_count_filter == "10":
                processed_face_count_min = 10
                processed_face_count_max = 10
            elif face_count_filter == "4-5":
                processed_face_count_min = 4
                processed_face_count_max = 5
            elif face_count_filter == "6-9":
                processed_face_count_min = 6
                processed_face_count_max = 9
            elif face_count_filter == "9+":
                processed_face_count_min = 10
                processed_face_count_max = None
            elif face_count_filter == "1+":
                processed_face_count_min = 1
                processed_face_count_max = None
        
        # 处理标签ID和分类ID参数
        processed_tag_ids = None
        processed_category_ids = None
        
        if tag_ids:
            try:
                processed_tag_ids = [int(id.strip()) for id in tag_ids.split(',') if id.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="标签ID格式错误")
        
        if category_ids:
            try:
                processed_category_ids = [int(id.strip()) for id in category_ids.split(',') if id.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="分类ID格式错误")
        
        results, total = search_service.search_photos(
            db=db,
            keyword=keyword,
            search_type=search_type,
            camera_make=camera_make,
            camera_model=camera_model,
            date_from=processed_date_from,
            date_to=processed_date_to,
            quality_min=quality_min,
            quality_level=processed_quality_level,
            face_count_min=processed_face_count_min,
            face_count_max=processed_face_count_max,
            format_filter=format_filter,
            camera_filter=camera_filter,
            person_filter=person_filter,
            tags=tags,
            categories=categories,
            tag_ids=processed_tag_ids,
            category_ids=processed_category_ids,
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
async def get_search_stats(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    search_type: str = Query("all", description="搜索类型"),
    quality_filter: Optional[str] = Query(None, description="质量筛选"),
    year_filter: Optional[str] = Query(None, description="年份筛选"),
    format_filter: Optional[str] = Query(None, description="格式筛选"),
    camera_filter: Optional[str] = Query(None, description="相机筛选"),
    face_count_filter: Optional[str] = Query(None, description="人脸数量筛选"),
    tag_ids: Optional[str] = Query(None, description="标签ID列表，逗号分隔"),
    category_ids: Optional[str] = Query(None, description="分类ID列表，逗号分隔"),
    person_filter: Optional[str] = Query(None, description="人物筛选"),
    date_from: Optional[str] = Query(None, description="开始日期"),
    date_to: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取搜索统计信息

    返回系统的统计数据：
    - 照片总数
    - 标签总数
    - 分类总数
    - 总存储量(MB)
    - 时间跨度(年)
    - 平均质量分
    - 图表数据（质量分布、年度分布、格式分布、相机分布）
    """
    try:
        # 解析标签和分类ID列表
        tag_ids_list = [int(id) for id in tag_ids.split(',')] if tag_ids else None
        category_ids_list = [int(id) for id in category_ids.split(',')] if category_ids else None

        # 处理中文关键词解码
        processed_keyword = None
        if keyword:
            from urllib.parse import unquote
            processed_keyword = unquote(keyword)

        stats = search_service.get_search_stats(
            db=db,
            keyword=processed_keyword,
            search_type=search_type,
            quality_filter=quality_filter,
            year_filter=year_filter,
            format_filter=format_filter,
            camera_filter=camera_filter,
            face_count_filter=face_count_filter,
            tag_ids=tag_ids_list,
            category_ids=category_ids_list,
            person_filter=person_filter,
            date_from=date_from,
            date_to=date_to
        )

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


@router.get("/similar/{photo_id}")
async def search_similar_photos(
    photo_id: int,
    threshold: float = Query(None, ge=0.0, le=1.0, description="相似度阈值"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    搜索相似照片
    
    基于感知哈希算法搜索与指定照片相似的照片
    """
    try:
        # 使用配置中的默认相似度阈值
        from app.core.config import settings
        if threshold is None:
            threshold = settings.search.similarity_threshold
        
        # 性能优化：预加载参考照片的关联数据
        from sqlalchemy.orm import joinedload
        photo = db.query(Photo).options(
            joinedload(Photo.tags).joinedload(PhotoTag.tag),
            joinedload(Photo.categories).joinedload(PhotoCategory.category),
            joinedload(Photo.analysis_results),
            joinedload(Photo.quality_assessments)
        ).filter(Photo.id == photo_id).first()
        
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 检查照片是否有感知哈希值
        if not photo.perceptual_hash:
            raise HTTPException(status_code=400, detail="照片缺少感知哈希值，无法进行相似搜索")
        
        # 使用重复检测服务搜索相似照片
        from app.services.duplicate_detection_service import DuplicateDetectionService
        duplicate_service = DuplicateDetectionService()
        
        # 搜索相似照片
        similar_photos = duplicate_service.find_similar_photos(
            db_session=db,
            reference_photo_id=photo_id,
            threshold=threshold,
            limit=limit
        )
        
        # 性能优化：批量查询所有相似照片并预加载关联数据，避免N+1查询
        similar_photo_ids = [sp['photo_id'] for sp in similar_photos]
        if similar_photo_ids:
            from sqlalchemy.orm import joinedload
            photos_dict = {
                p.id: p for p in db.query(Photo).options(
                    joinedload(Photo.tags).joinedload(PhotoTag.tag),
                    joinedload(Photo.categories).joinedload(PhotoCategory.category),
                    joinedload(Photo.analysis_results),
                    joinedload(Photo.quality_assessments)
                ).filter(Photo.id.in_(similar_photo_ids)).all()
            }
            
            # 批量查询analysis和quality
            analyses = db.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id.in_(similar_photo_ids),
                PhotoAnalysis.analysis_type == 'content'
            ).all()
            analysis_dict = {a.photo_id: a for a in analyses}
            
            qualities = db.query(PhotoQuality).filter(PhotoQuality.photo_id.in_(similar_photo_ids)).all()
            quality_dict = {q.photo_id: q for q in qualities}
        else:
            photos_dict = {}
            analysis_dict = {}
            quality_dict = {}
        
        # 格式化结果
        results = []
        for similar_photo in similar_photos:
            photo_obj = photos_dict.get(similar_photo['photo_id'])
            if photo_obj:
                result = search_service._format_photo_result(
                    db=db, 
                    photo=photo_obj,
                    analysis=analysis_dict.get(photo_obj.id),
                    quality=quality_dict.get(photo_obj.id)
                )
                if result:
                    result['similarity'] = similar_photo.get('similarity', 0.0)
                    results.append(result)
        
        # 获取参考照片的analysis和quality（使用已预加载的photo对象）
        ref_analysis = None
        ref_quality = None
        if photo.analysis_results:
            for a in photo.analysis_results:
                if a.analysis_type == 'content':
                    ref_analysis = a
                    break
        if photo.quality_assessments:
            ref_quality = photo.quality_assessments[0]
        
        return {
            "success": True,
            "data": {
                "reference_photo": search_service._format_photo_result(
                    db=db, 
                    photo=photo,
                    analysis=ref_analysis,
                    quality=ref_quality
                ),
                "similar_photos": results,
                "total": len(results),
                "threshold": threshold
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索相似照片失败: {str(e)}")


@router.get("/similar/by-features/{photo_id}")
async def search_similar_photos_by_features(
    photo_id: int,
    threshold: float = Query(None, ge=0.0, le=1.0, description="相似度阈值"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    基于特征向量搜索相似照片
    
    使用ResNet50提取的图像特征向量进行相似度匹配
    """
    try:
        # 使用配置中的默认相似度阈值
        from app.core.config import settings
        if threshold is None:
            threshold = settings.image_features.similarity_threshold
        
        # 性能优化：预加载参考照片的关联数据
        from sqlalchemy.orm import joinedload
        photo = db.query(Photo).options(
            joinedload(Photo.tags).joinedload(PhotoTag.tag),
            joinedload(Photo.categories).joinedload(PhotoCategory.category),
            joinedload(Photo.analysis_results),
            joinedload(Photo.quality_assessments)
        ).filter(Photo.id == photo_id).first()
        
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 检查照片是否已提取特征向量
        if not photo.image_features_extracted or not photo.image_features:
            raise HTTPException(
                status_code=400,
                detail="照片尚未提取特征向量，请先运行特征提取任务"
            )
        
        # 使用图像特征服务搜索相似照片
        from app.services.image_feature_service import image_feature_service
        
        # 搜索相似照片（服务层已返回包含Photo对象的字典）
        similar_photos = image_feature_service.find_similar_photos_by_features(
            db_session=db,
            reference_photo_id=photo_id,
            threshold=threshold,
            limit=limit
        )
        
        # 性能优化：像智能搜索一样，手动构建简单字典，只返回显示所需的基本字段
        results = []
        for photo_data in similar_photos:
            photo_obj = photo_data['photo']
            results.append({
                "id": photo_obj.id,
                "filename": photo_obj.filename,
                "thumbnail_path": photo_obj.thumbnail_path,
                "original_path": photo_obj.original_path,
                "width": photo_obj.width,
                "height": photo_obj.height,
                "format": photo_obj.format,
                "taken_at": photo_obj.taken_at.isoformat() if photo_obj.taken_at else None,
                "created_at": photo_obj.created_at.isoformat() if photo_obj.created_at else None,
                "similarity": photo_data['similarity']
            })
        
        return {
            "success": True,
            "data": {
                "reference_photo": {
                    "id": photo.id,
                    "filename": photo.filename,
                    "thumbnail_path": photo.thumbnail_path
                },
                "similar_photos": results,
                "total": len(results),
                "threshold": threshold
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索相似照片失败: {str(e)}")


@router.post("/similar/process")
async def process_similar_photos(
    photo_ids: List[int],
    action: str = Query(..., description="处理动作: delete, keep_best, group"),
    db: Session = Depends(get_db)
):
    """
    处理相似照片
    
    支持批量删除、保留最佳、分组等操作
    """
    try:
        if not photo_ids:
            raise HTTPException(status_code=400, detail="请提供照片ID列表")
        
        if action not in ["delete", "keep_best", "group"]:
            raise HTTPException(status_code=400, detail="不支持的处理动作")
        
        if action == "delete":
            # 批量删除
            from app.api.photos import batch_delete_photos
            return await batch_delete_photos(
                photo_ids=photo_ids,
                delete_files=True,
                db=db
            )
        
        elif action == "keep_best":
            # 保留质量最高的照片
            photos = db.query(Photo).filter(Photo.id.in_(photo_ids)).all()
            if not photos:
                raise HTTPException(status_code=404, detail="照片不存在")
            
            # 找到质量最高的照片
            best_photo = max(photos, key=lambda p: p.quality_score or 0)
            other_ids = [p.id for p in photos if p.id != best_photo.id]
            
            if other_ids:
                from app.api.photos import batch_delete_photos
                delete_result = await batch_delete_photos(
                    photo_ids=other_ids,
                    delete_files=True,
                    db=db
                )
                
                return {
                    "success": True,
                    "data": {
                        "kept_photo": best_photo.id,
                        "deleted_photos": other_ids,
                        "message": f"已保留质量最高的照片: {best_photo.filename}"
                    }
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "message": "只有一张照片，无需处理"
                    }
                }
        
        elif action == "group":
            # TODO: 实现相似照片分组功能
            return {
                "success": True,
                "data": {
                    "message": "相似照片分组功能开发中"
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理相似照片失败: {str(e)}")


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


@router.post("/similar-photos/cluster")
async def cluster_similar_photos(
    db: Session = Depends(get_db)
):
    """
    执行相似照片聚类分析
    
    :param db: 数据库会话（仅用于验证，不在后台任务中使用）
    :return: 聚类任务启动结果
    """
    try:
        import asyncio
        from app.services.similar_photo_cluster_service import SimilarPhotoClusterService
        import uuid
        from datetime import datetime
        
        cluster_service = SimilarPhotoClusterService()
        
        # 生成任务ID
        task_id = f"cluster_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        # 🔥 使用 asyncio.create_task() 启动真正的异步任务（参考人脸识别任务）
        asyncio.create_task(cluster_service.process_cluster_task(task_id))
        
        return {
            "success": True,
            "message": "已开始相似照片聚类分析",
            "task_id": task_id
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"相似照片聚类API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar-photos/cluster/status/{task_id}")
async def get_cluster_task_status(task_id: str):
    """
    获取聚类任务状态
    
    :param task_id: 任务ID
    :return: 任务状态
    """
    try:
        from app.services.similar_photo_cluster_service import cluster_task_status
        
        task_status = cluster_task_status.get(task_id)
        
        if not task_status:
            return {
                "success": False,
                "status": "not_found",
                "message": "任务不存在或已过期"
            }
        
        return {
            "success": True,
            "task_id": task_id,
            **task_status
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"获取聚类任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
