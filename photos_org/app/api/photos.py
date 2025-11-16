"""
家庭版智能照片系统 - 照片管理API
"""
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import os
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.photo import Photo, Tag, Category, PhotoAnalysis
from app.schemas.photo import PhotoResponse
from app.services.photo_service import PhotoService

logger = get_logger(__name__)

router = APIRouter()


# 请求/响应模型
class PhotoFilters(BaseModel):
    """照片筛选条件"""
    status: Optional[str] = Field(None, description="照片状态")
    format: Optional[str] = Field(None, description="照片格式")
    min_size: Optional[int] = Field(None, description="最小文件大小")
    max_size: Optional[int] = Field(None, description="最大文件大小")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    min_quality: Optional[float] = Field(None, description="最小质量分数")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    categories: Optional[List[int]] = Field(None, description="分类ID列表")


class PhotoUpdateRequest(BaseModel):
    """照片更新请求"""
    description: Optional[str] = Field(None, description="照片描述")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    categories: Optional[List[int]] = Field(None, description="分类ID列表")
    filename: Optional[str] = Field(None, description="照片文件名")
    taken_at: Optional[str] = Field(None, description="拍摄时间（ISO格式字符串）")
    location_name: Optional[str] = Field(None, description="位置名称")
    is_favorite: Optional[bool] = Field(None, description="是否收藏")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    photo_ids: List[int] = Field(..., description="要删除的照片ID列表")
    delete_files: bool = Field(True, description="是否删除物理文件")


class BatchDeleteResponse(BaseModel):
    """批量删除响应"""
    total_requested: int = Field(..., description="请求删除的数量")
    successful_deletions: int = Field(..., description="成功删除的数量")
    failed_deletions: List[int] = Field(..., description="失败删除的ID列表")


class BatchEditRequest(BaseModel):
    """批量编辑请求"""
    photo_ids: List[int] = Field(..., description="要编辑的照片ID列表")
    
    # 标签操作
    tags_operation: Optional[str] = Field(None, description="标签操作类型: add/remove/replace/clear")
    tags: Optional[List[str]] = Field(None, description="标签列表（用于add/replace操作）")
    tags_to_remove: Optional[List[str]] = Field(None, description="要移除的标签列表（用于remove操作）")
    
    # 分类操作
    categories_operation: Optional[str] = Field(None, description="分类操作类型: add/remove/replace/clear")
    category_ids: Optional[List[int]] = Field(None, description="分类ID列表（用于add/replace操作）")
    category_ids_to_remove: Optional[List[int]] = Field(None, description="要移除的分类ID列表（用于remove操作）")
    
    # 拍摄时间操作
    taken_at_operation: Optional[str] = Field(None, description="拍摄时间操作: set/fill_empty/clear")
    taken_at: Optional[str] = Field(None, description="拍摄时间（ISO格式），用于set/fill_empty操作")
    
    # 位置操作
    location_name_operation: Optional[str] = Field(None, description="位置操作: set/fill_empty/clear")
    location_name: Optional[str] = Field(None, description="位置名称，用于set/fill_empty操作")
    
    # 描述操作
    description_operation: Optional[str] = Field(None, description="描述操作: set/append/clear")
    description: Optional[str] = Field(None, description="描述内容，用于set/append操作")
    
    # 文件名操作
    filename_operation: Optional[str] = Field(None, description="文件名操作: add_prefix/add_suffix/set")
    filename_prefix: Optional[str] = Field(None, description="文件名前缀（用于add_prefix操作）")
    filename_suffix: Optional[str] = Field(None, description="文件名后缀（用于add_suffix操作）")
    filename_template: Optional[str] = Field(None, description="文件名模板（用于set操作，支持{序号}占位符，如：照片_{序号}）")
    filename_start_index: Optional[int] = Field(1, description="文件名序号起始值（用于set操作，默认从1开始）", ge=1)


class BatchEditResponse(BaseModel):
    """批量编辑响应"""
    total_requested: int = Field(..., description="请求编辑的照片数量")
    filename_updated: int = Field(0, description="文件名更新数量")
    successful_edits: int = Field(..., description="成功编辑的数量")
    failed_edits: List[int] = Field(default_factory=list, description="编辑失败的照片ID列表")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细操作结果")


class PhotoStatistics(BaseModel):
    """照片统计信息"""
    total_photos: int = Field(..., description="总照片数")
    total_size: int = Field(..., description="总文件大小(字节)")
    total_size_mb: float = Field(..., description="总文件大小(MB)")
    status_distribution: Dict[str, int] = Field(..., description="状态分布")
    format_distribution: Dict[str, int] = Field(..., description="格式分布")
    yearly_distribution: Dict[str, int] = Field(..., description="年度分布")
    quality_distribution: Dict[str, int] = Field(..., description="质量分布")
    last_updated: str = Field(..., description="最后更新时间")


@router.get("/", response_model=Dict[str, Any])
async def get_photos(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=1000, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序"),
    filters: Optional[str] = Query(None, description="筛选条件JSON字符串"),
    person_filter: str = Query("all", description="人物筛选"),
    db: Session = Depends(get_db)
):
    """
    获取照片列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数上限
    - **search**: 搜索关键词
    - **sort_by**: 排序字段 (created_at, updated_at, file_size, etc.)
    - **sort_order**: 排序顺序 (asc, desc)
    - **filters**: 筛选条件JSON字符串
    """
    try:
        photo_service = PhotoService()

        # 解析筛选条件
        filter_dict = None
        if filters:
            try:
                filter_dict = json.loads(filters)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="筛选条件格式错误")

        # 搜索或获取所有照片
        if search:
            photos, total = photo_service.search_photos(db, search, skip, limit)
        else:
            photos, total = photo_service.get_photos(db, skip, limit, filter_dict, sort_by, sort_order, person_filter)

        # 性能优化：批量查询所有analysis，避免N+1查询
        photo_ids = [photo.id for photo in photos]
        analyses = db.query(PhotoAnalysis).filter(PhotoAnalysis.photo_id.in_(photo_ids)).all()
        analysis_dict = {a.photo_id: a for a in analyses}

        # 转换为响应格式
        photo_list = []
        for photo in photos:
            photo_dict = {
                "id": photo.id,
                "filename": photo.filename,
                "file_path": photo.original_path,
                "file_size": photo.file_size,
                "width": photo.width,
                "height": photo.height,
                "format": photo.format,
                "status": photo.status,
                "description": photo.description,
                "created_at": photo.created_at.isoformat() if photo.created_at else None,
                "updated_at": photo.updated_at.isoformat() if photo.updated_at else None,
                "thumbnail_path": photo.thumbnail_path,
                "tags": [tag.tag.name for tag in photo.tags] if photo.tags else [],
                "categories": [cat.category.name for cat in photo.categories] if photo.categories else [],
                "location_name": photo.location_name,
                "location_lat": photo.location_lat,
                "location_lng": photo.location_lng,
                "location_alt": photo.location_alt,
                # 统一处理 is_favorite：确保返回布尔值（SQLite Boolean 可能返回 0/1）
                "is_favorite": bool(photo.is_favorite) if hasattr(photo, 'is_favorite') and photo.is_favorite is not None else False
            }

            # 从批量查询的字典中获取analysis
            analysis = analysis_dict.get(photo.id)
            if analysis:
                # 解析analysis_result JSON数据
                try:
                    # ChineseFriendlyJSON应该自动反序列化为dict，但这里确保兼容性
                    if isinstance(analysis.analysis_result, dict):
                        analysis_data = analysis.analysis_result
                    elif isinstance(analysis.analysis_result, str):
                        import json
                        analysis_data = json.loads(analysis.analysis_result)
                    else:
                        analysis_data = {}

                    photo_dict["analysis"] = {
                        "description": analysis_data.get("description", ""),
                        "tags": analysis_data.get("tags", []),
                        "confidence": analysis.confidence_score,
                        "type": analysis.analysis_type
                    }
                except Exception as e:
                    # 如果解析失败，至少返回基本信息
                    photo_dict["analysis"] = {
                        "description": "",
                        "tags": [],
                        "confidence": analysis.confidence_score,
                        "type": analysis.analysis_type,
                        "parse_error": str(e)
                    }

            photo_list.append(photo_dict)

        return {
            "photos": photo_list,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": skip + len(photos) < total
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取照片列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取照片列表失败: {str(e)}")


@router.get("/{photo_id}", response_model=Dict[str, Any])
async def get_photo_detail(photo_id: int, db: Session = Depends(get_db)):
    """
    获取照片详情

    - **photo_id**: 照片ID
    """
    try:
        photo_service = PhotoService()
        photo = photo_service.get_photo_by_id(db, photo_id)

        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")

        # 构建详细响应
        response = {
            "id": photo.id,
            "filename": photo.filename,
            "file_path": photo.original_path,
            "file_size": photo.file_size,
            "width": photo.width,
            "height": photo.height,
            "format": photo.format,
            "status": photo.status,
            "description": photo.description,
            "created_at": photo.created_at.isoformat() if photo.created_at else None,
            "updated_at": photo.updated_at.isoformat() if photo.updated_at else None,
            "thumbnail_path": photo.thumbnail_path,
            "tags": [tag.tag.name for tag in photo.tags] if photo.tags else [],
            "categories": [cat.category.name for cat in photo.categories] if photo.categories else [],
            "location_name": photo.location_name,
            "location_lat": photo.location_lat,
            "location_lng": photo.location_lng,
            "location_alt": photo.location_alt,
            # 统一处理 is_favorite：确保返回布尔值（SQLite Boolean 可能返回 0/1）
            "is_favorite": bool(photo.is_favorite) if hasattr(photo, 'is_favorite') and photo.is_favorite is not None else False,
            "metadata": {}
        }

        # 添加EXIF信息
        if photo.camera_make or photo.focal_length:
            response["metadata"]["exif"] = {
                "camera_make": photo.camera_make,
                "camera_model": photo.camera_model,
                "focal_length": photo.focal_length,
                "aperture": photo.aperture,
                "shutter_speed": photo.shutter_speed,
                "iso": photo.iso,
                "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
                "location_lat": photo.location_lat,
                "location_lng": photo.location_lng
            }

        # 性能优化：使用预加载的analysis，避免重复查询
        # get_photo_by_id已经预加载了analysis_results，直接使用
        analysis = None
        if photo.analysis_results:
            # 查找content类型的分析结果
            for a in photo.analysis_results:
                if a.analysis_type == 'content':
                    analysis = a
                    break
        if analysis:
            # 解析analysis_result JSON数据
            try:
                # ChineseFriendlyJSON应该自动反序列化为dict，但这里确保兼容性
                if isinstance(analysis.analysis_result, dict):
                    analysis_data = analysis.analysis_result
                elif isinstance(analysis.analysis_result, str):
                    import json
                    analysis_data = json.loads(analysis.analysis_result)
                else:
                    analysis_data = {}

                response["analysis"] = {
                    "description": analysis_data.get("description", ""),
                    "tags": analysis_data.get("tags", []),
                    "confidence": analysis.confidence_score,
                    "type": analysis.analysis_type,
                    "analyzed_at": analysis.created_at.isoformat() if analysis.created_at else None
                }
            except Exception as e:
                # 如果解析失败，至少返回基本信息
                response["analysis"] = {
                    "description": "",
                    "tags": [],
                    "confidence": analysis.confidence_score,
                    "type": analysis.analysis_type,
                    "analyzed_at": analysis.created_at.isoformat() if analysis.created_at else None,
                    "parse_error": str(e)
                }


        # 添加质量信息
        if photo.quality_assessments:
            latest_quality = max(photo.quality_assessments, key=lambda q: q.created_at)
            response["quality"] = {
                "quality_score": latest_quality.quality_score,
                "sharpness_score": latest_quality.sharpness_score,
                "brightness_score": latest_quality.brightness_score,
                "contrast_score": latest_quality.contrast_score,
                "color_score": latest_quality.color_score,
                "composition_score": latest_quality.composition_score,
                "quality_level": latest_quality.quality_level,
                "technical_issues": latest_quality.technical_issues,
                "assessed_at": latest_quality.assessed_at.isoformat() if latest_quality.assessed_at else None
            }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取照片详情失败 photo_id={photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取照片详情失败: {str(e)}")


@router.put("/{photo_id}", response_model=Dict[str, Any])
async def update_photo(
    photo_id: int,
    update_request: PhotoUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新照片信息

    - **photo_id**: 照片ID
    - **update_request**: 更新请求数据
    """
    try:
        photo_service = PhotoService()

        # 检查照片是否存在
        photo = photo_service.get_photo_by_id(db, photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")

        # 准备更新数据
        update_data = {}
        if update_request.description is not None:
            update_data["description"] = update_request.description
        if update_request.filename is not None:
            # 验证文件名不能为空
            if not update_request.filename.strip():
                raise HTTPException(status_code=400, detail="文件名不能为空")
            update_data["filename"] = update_request.filename.strip()
        if update_request.taken_at is not None:
            # 🔥 修复：不考虑时区，直接解析为本地时间（naive datetime）
            from datetime import datetime
            try:
                if update_request.taken_at.strip():  # 非空字符串
                    # 格式可能是 YYYY-MM-DDTHH:mm:00 或 YYYY-MM-DDTHH:mm:SS
                    # 使用strptime解析，当作本地时间（无时区）
                    taken_at_str = update_request.taken_at.strip()
                    # 尝试不同的格式
                    if len(taken_at_str) == 19:  # YYYY-MM-DDTHH:mm:SS
                        update_data["taken_at"] = datetime.strptime(taken_at_str, '%Y-%m-%dT%H:%M:%S')
                    elif len(taken_at_str) == 16:  # YYYY-MM-DDTHH:mm
                        update_data["taken_at"] = datetime.strptime(taken_at_str, '%Y-%m-%dT%H:%M')
                    else:
                        # 尝试ISO格式（可能带时区）
                        parsed = datetime.fromisoformat(taken_at_str.replace('Z', '+00:00'))
                        # 如果是带时区的，转换为本地时间（移除时区信息）
                        if parsed.tzinfo:
                            # 转为naive datetime（假设已经是本地时间）
                            update_data["taken_at"] = parsed.replace(tzinfo=None)
                        else:
                            update_data["taken_at"] = parsed
                else:
                    update_data["taken_at"] = None  # 清空时间
            except (ValueError, TypeError) as e:
                raise HTTPException(status_code=400, detail=f"拍摄时间格式错误: {str(e)}，请使用格式：2023-12-19T14:30:00")
        if update_request.location_name is not None:
            update_data["location_name"] = update_request.location_name
        if update_request.is_favorite is not None:
            update_data["is_favorite"] = update_request.is_favorite

        # 阶段二：检查是否更新了taken_at，如果更新了，自动更新时间标签
        taken_at_updated = False
        new_taken_at = None
        old_taken_at = photo.taken_at  # 保存原始值用于比较
        
        if 'taken_at' in update_data:
            new_taken_at = update_data.get('taken_at')
            # 判断值是否实际变化（考虑None的情况）
            if old_taken_at != new_taken_at:
                taken_at_updated = True
        
        # 更新照片基本信息
        if update_data:
            success = photo_service.update_photo(db, photo_id, update_data)
            if not success:
                raise HTTPException(status_code=500, detail="更新照片信息失败")
        
        # 🔥 修复bug：调整执行顺序，先处理tags更新，再处理taken_at更新
        # 这样可以确保新生成的时间标签不会被tags更新删除
        
        # 更新标签（先执行）
        if update_request.tags is not None:
            # 🔥 修复：保存现有标签的source信息，以便在重新添加时保留
            existing_tags_source = {}
            if photo.tags:
                for photo_tag in photo.tags:
                    existing_tags_source[photo_tag.tag.name] = photo_tag.source
            
            # 先移除所有现有标签
            photo_service.remove_tags_from_photo(db, photo_id, [tag.tag.name for tag in photo.tags] if photo.tags else [])
            # 添加新标签，传入原有标签的source信息
            if update_request.tags:
                photo_service.add_tags_to_photo(db, photo_id, update_request.tags, tags_with_source=existing_tags_source)

        # 阶段二：如果taken_at已更新，自动更新时间标签（后执行，确保新生成的时间标签不会被tags更新删除）
        if taken_at_updated:
            try:
                from app.services.classification_service import ClassificationService
                from app.models.photo import Tag, PhotoTag
                from sqlalchemy import and_
                
                classification_service = ClassificationService()
                
                # 1. 删除旧的时间标签（type='time'的标签）
                # 获取所有时间标签
                time_tags = db.query(Tag).filter(Tag.category == 'time').all()
                time_tag_ids = [tag.id for tag in time_tags]
                
                if time_tag_ids:
                    # 删除该照片的所有时间标签关联
                    db.query(PhotoTag).filter(
                        and_(
                            PhotoTag.photo_id == photo_id,
                            PhotoTag.tag_id.in_(time_tag_ids)
                        )
                    ).delete(synchronize_session=False)
                
                # 2. 生成新的时间标签（如果new_taken_at不为None）
                if new_taken_at:
                    logger.debug(f"开始生成新时间标签 photo_id={photo_id}, new_taken_at={new_taken_at}")
                    new_time_tags = classification_service.generate_time_tags_from_datetime(new_taken_at)
                    logger.debug(f"生成的时间标签数量: {len(new_time_tags) if new_time_tags else 0}, tags={[tag.get('name') for tag in new_time_tags] if new_time_tags else []}")
                    if new_time_tags:
                        # 使用ClassificationService的_save_auto_tags方法保存新标签
                        saved_tags = classification_service._save_auto_tags(photo_id, new_time_tags, db)
                        logger.info(f"为照片添加时间标签成功 photo_id={photo_id}, tags={saved_tags}")
                    else:
                        logger.warning(f"生成的时间标签为空 photo_id={photo_id}, new_taken_at={new_taken_at}")
                else:
                    logger.debug(f"new_taken_at为None，不生成新时间标签 photo_id={photo_id}")
                
                # 提交时间标签更新
                db.commit()
                logger.info(f"照片taken_at更新，已自动更新时间标签 photo_id={photo_id}")
            except Exception as e:
                logger.warning(f"自动更新时间标签失败 photo_id={photo_id}: {str(e)}")
                # 时间标签更新失败不影响照片更新，只记录日志并回滚标签相关操作
                db.rollback()

        # 更新分类
        if update_request.categories is not None:
            # 先移除所有现有分类
            photo_service.remove_photo_from_categories(db, photo_id, [cat.id for cat in photo.categories] if photo.categories else [])
            # 添加新分类
            if update_request.categories:
                photo_service.add_photo_to_categories(db, photo_id, update_request.categories)

        # 重新获取更新后的照片
        updated_photo = photo_service.get_photo_by_id(db, photo_id)
        return {
            "id": updated_photo.id,
            "filename": updated_photo.filename,
            "description": updated_photo.description,
            "taken_at": updated_photo.taken_at.isoformat() if updated_photo.taken_at else None,
            "location_name": updated_photo.location_name,
            "updated_at": updated_photo.updated_at.isoformat() if updated_photo.updated_at else None,
            "tags": [tag.tag.name for tag in updated_photo.tags] if updated_photo.tags else [],
            "categories": [cat.category.name for cat in updated_photo.categories] if updated_photo.categories else [],
            "message": "照片更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新照片失败 photo_id={photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新照片失败: {str(e)}")


class FavoriteUpdateRequest(BaseModel):
    """收藏状态更新请求"""
    is_favorite: bool = Field(..., description="是否收藏")


@router.put("/{photo_id}/favorite", response_model=Dict[str, Any])
async def update_photo_favorite(
    photo_id: int,
    favorite_request: FavoriteUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新照片收藏状态

    - **photo_id**: 照片ID
    - **favorite_request**: 收藏状态请求
    """
    try:
        photo_service = PhotoService()

        # 检查照片是否存在
        photo = photo_service.get_photo_by_id(db, photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")

        # 更新收藏状态
        update_data = {"is_favorite": favorite_request.is_favorite}
        success = photo_service.update_photo(db, photo_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="更新收藏状态失败")

        # 重新获取更新后的照片
        updated_photo = photo_service.get_photo_by_id(db, photo_id)
        return {
            "success": True,
            "photo_id": updated_photo.id,
            # 统一处理 is_favorite：确保返回布尔值（SQLite Boolean 可能返回 0/1）
            "is_favorite": bool(updated_photo.is_favorite),
            "message": "已添加到收藏" if updated_photo.is_favorite else "已取消收藏"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新收藏状态失败 photo_id={photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新收藏状态失败: {str(e)}")


@router.delete("/{photo_id}")
async def delete_photo(photo_id: int, delete_file: bool = True, db: Session = Depends(get_db)):
    """
    删除照片

    - **photo_id**: 照片ID
    - **delete_file**: 是否删除物理文件 (默认True)
    """
    try:
        photo_service = PhotoService()
        success = photo_service.delete_photo(db, photo_id, delete_file)

        if not success:
            raise HTTPException(status_code=404, detail="照片不存在或删除失败")

        return {
            "message": "照片删除成功",
            "photo_id": photo_id,
            "file_deleted": delete_file
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除照片失败 photo_id={photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除照片失败: {str(e)}")


@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_photos(request: BatchDeleteRequest, db: Session = Depends(get_db)):
    """
    批量删除照片

    - **request**: 批量删除请求
    """
    try:
        if not request.photo_ids:
            raise HTTPException(status_code=400, detail="照片ID列表不能为空")

        photo_service = PhotoService()
        successful_deletions, failed_ids = photo_service.batch_delete_photos(
            db, request.photo_ids, request.delete_files
        )

        return BatchDeleteResponse(
            total_requested=len(request.photo_ids),
            successful_deletions=successful_deletions,
            failed_deletions=failed_ids
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除照片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量删除照片失败: {str(e)}")


@router.post("/batch-edit", response_model=BatchEditResponse)
async def batch_edit_photos(
    request: BatchEditRequest,
    db: Session = Depends(get_db)
):
    """
    批量编辑照片

    - **request**: 批量编辑请求
    """
    try:
        if not request.photo_ids:
            raise HTTPException(status_code=400, detail="照片ID列表不能为空")

        photo_service = PhotoService()
        successful_edits, failed_ids, details = photo_service.batch_edit_photos(
            db, request
        )

        return BatchEditResponse(
            total_requested=len(request.photo_ids),
            successful_edits=successful_edits,
            failed_edits=failed_ids,
            details=details
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量编辑照片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量编辑照片失败: {str(e)}")


@router.get("/statistics", response_model=PhotoStatistics)
async def get_photo_statistics(db: Session = Depends(get_db)):
    """
    获取照片统计信息
    """
    try:
        photo_service = PhotoService()
        stats = photo_service.get_photo_statistics(db)
        return PhotoStatistics(**stats)

    except Exception as e:
        logger.error(f"获取照片统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/by-category/{category_id}")
async def get_photos_by_category(
    category_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """
    获取分类下的照片

    - **category_id**: 分类ID
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数上限
    """
    try:
        # 检查分类是否存在
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        photo_service = PhotoService()
        photos, total = photo_service.get_photos_by_category(db, category_id, skip, limit)

        return {
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description
            },
            "photos": [
                {
                    "id": photo.id,
                    "filename": photo.filename,
                    "thumbnail_path": photo.thumbnail_path,
                    "created_at": photo.created_at.isoformat() if photo.created_at else None
                }
                for photo in photos
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类照片失败 category_id={category_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类照片失败: {str(e)}")


@router.get("/by-tag/{tag_name}")
async def get_photos_by_tag(
    tag_name: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """
    获取标签下的照片

    - **tag_name**: 标签名称
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数上限
    """
    try:
        # 检查标签是否存在
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")

        photo_service = PhotoService()
        photos, total = photo_service.get_photos_by_tag(db, tag.id, skip, limit)

        return {
            "tag": {
                "id": tag.id,
                "name": tag.name
            },
            "photos": [
                {
                    "id": photo.id,
                    "filename": photo.filename,
                    "thumbnail_path": photo.thumbnail_path,
                    "created_at": photo.created_at.isoformat() if photo.created_at else None
                }
                for photo in photos
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取标签照片失败 tag_name='{tag_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签照片失败: {str(e)}")


@router.get("/{photo_id}/download")
async def download_photo(photo_id: int, db: Session = Depends(get_db)):
    """
    下载照片原图
    
    :param photo_id: 照片ID
    :param db: 数据库会话
    :return: 照片文件
    """
    try:
        # 获取照片信息
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 构建存储基础路径（使用统一的路径解析函数）
        from app.core.path_utils import resolve_resource_path
        storage_base = resolve_resource_path(settings.storage.base_path)
        
        is_heic = photo.format and photo.format.upper() in ['HEIC', 'HEIF']
        
        # 构建文件路径
        # HEIC格式：使用original_path但扩展名改为.heic（HEIC原图和JPEG在同一目录）
        # 其他格式：直接使用original_path
        if photo.original_path:
            if is_heic:
                # HEIC格式：修改original_path的扩展名为.heic
                heic_path = Path(photo.original_path).with_suffix('.heic')
                file_path = storage_base / heic_path
            else:
                # 非HEIC格式：直接使用original_path
                file_path = storage_base / photo.original_path
            file_path = str(file_path)
        else:
            # 如果没有original_path，尝试使用thumbnail_path
            if photo.thumbnail_path:
                file_path = storage_base / photo.thumbnail_path
                file_path = str(file_path)
            else:
                raise HTTPException(status_code=404, detail="照片文件路径不存在")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"照片文件不存在: path={file_path}, photo_id={photo_id}, format={photo.format}")
            raise HTTPException(status_code=404, detail="照片文件不存在")
        
        # 生成下载文件名
        # 去掉photo.filename的扩展名，得到文件名前缀
        filename_stem = os.path.splitext(photo.filename)[0]
        
        # 根据format字段决定扩展名
        if is_heic:
            file_extension = '.heic'
        else:
            # 使用原文件名的扩展名，或从original_path推断，或默认.jpg
            file_extension = os.path.splitext(photo.filename)[1] or os.path.splitext(photo.original_path or '')[1] or '.jpg'
        
        download_filename = f"{filename_stem}{file_extension}"
        
        logger.info(f"用户下载照片: {photo.filename} -> {download_filename} (格式: {photo.format})")
        
        # 返回文件
        return FileResponse(
            path=file_path,
            filename=download_filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载照片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载照片失败: {str(e)}")
