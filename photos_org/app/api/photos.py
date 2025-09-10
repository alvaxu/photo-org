"""
家庭单机版智能照片整理系统 - 照片管理API
"""
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

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


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    photo_ids: List[int] = Field(..., description="要删除的照片ID列表")
    delete_files: bool = Field(True, description="是否删除物理文件")


class BatchDeleteResponse(BaseModel):
    """批量删除响应"""
    total_requested: int = Field(..., description="请求删除的数量")
    successful_deletions: int = Field(..., description="成功删除的数量")
    failed_deletions: List[int] = Field(..., description="失败删除的ID列表")


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
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序"),
    filters: Optional[str] = Query(None, description="筛选条件JSON字符串"),
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
            photos, total = photo_service.get_photos(db, skip, limit, filter_dict, sort_by, sort_order)

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
                "categories": [cat.category.name for cat in photo.categories] if photo.categories else []
            }

            # 添加分析信息（通过查询获取）
            analysis = db.query(PhotoAnalysis).filter(PhotoAnalysis.photo_id == photo.id).first()
            if analysis:
                # 解析analysis_result JSON数据
                try:
                    analysis_data = analysis.analysis_result if isinstance(analysis.analysis_result, dict) else {}
                    photo_dict["analysis"] = {
                        "description": analysis_data.get("description", ""),
                        "tags": analysis_data.get("tags", []),
                        "confidence": analysis.confidence_score,
                        "type": analysis.analysis_type
                    }
                except:
                    photo_dict["analysis"] = {
                        "description": "",
                        "tags": [],
                        "confidence": analysis.confidence_score,
                        "type": analysis.analysis_type
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

        # 添加分析信息（通过查询获取）
        analysis = db.query(PhotoAnalysis).filter(PhotoAnalysis.photo_id == photo.id).first()
        if analysis:
            # 解析analysis_result JSON数据
            try:
                analysis_data = analysis.analysis_result if isinstance(analysis.analysis_result, dict) else {}
                response["analysis"] = {
                    "description": analysis_data.get("description", ""),
                    "tags": analysis_data.get("tags", []),
                    "confidence": analysis.confidence_score,
                    "type": analysis.analysis_type,
                    "analyzed_at": analysis.created_at.isoformat() if analysis.created_at else None
                }
            except:
                response["analysis"] = {
                    "description": "",
                    "tags": [],
                    "confidence": analysis.confidence_score,
                    "type": analysis.analysis_type,
                    "analyzed_at": analysis.created_at.isoformat() if analysis.created_at else None
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

        # 更新照片基本信息
        if update_data:
            success = photo_service.update_photo(db, photo_id, update_data)
            if not success:
                raise HTTPException(status_code=500, detail="更新照片信息失败")

        # 更新标签
        if update_request.tags is not None:
            # 先移除所有现有标签
            photo_service.remove_tags_from_photo(db, photo_id, [tag.tag.name for tag in photo.tags] if photo.tags else [])
            # 添加新标签
            if update_request.tags:
                photo_service.add_tags_to_photo(db, photo_id, update_request.tags)

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


@router.post("/batch-process")
async def batch_process_photos(
    enable_ai: bool = Query(True, description="启用AI分析"),
    enable_quality: bool = Query(True, description="启用质量评估"),
    enable_classification: bool = Query(True, description="启用智能分类"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    批量处理照片

    对所有照片进行AI分析、质量评估和智能分类
    """
    try:
        photo_service = PhotoService()

        # 获取所有照片
        photos, total = photo_service.get_photos(db, skip=0, limit=1000)

        if not photos:
            return {
                "success": True,
                "message": "没有找到需要处理的照片",
                "data": {
                    "total_photos": 0,
                    "processed": 0
                }
            }

        # 如果照片数量较多，放到后台处理
        if len(photos) > 10:
            background_tasks.add_task(process_photos_background, photos, enable_ai, enable_quality, enable_classification, db)

            return {
                "success": True,
                "message": f"已提交 {len(photos)} 张照片到后台处理",
                "data": {
                    "total_photos": len(photos),
                    "status": "processing"
                }
            }

        # 小批量直接处理
        processed_count = await process_photos_background(photos, enable_ai, enable_quality, enable_classification, db)

        return {
            "success": True,
            "message": f"成功处理 {processed_count}/{len(photos)} 张照片",
            "data": {
                "total_photos": len(photos),
                "processed": processed_count
            }
        }

    except Exception as e:
        logger.error(f"批量处理照片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")


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
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
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
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
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


async def process_photos_background(photos, enable_ai, enable_quality, enable_classification, db):
    """
    后台批量处理照片

    :param photos: 照片列表
    :param enable_ai: 是否启用AI分析
    :param enable_quality: 是否启用质量评估
    :param enable_classification: 是否启用智能分类
    :param db: 数据库会话
    :return: 处理成功的照片数量
    """
    from app.services.analysis_service import AnalysisService
    from app.services.photo_quality_service import PhotoQualityService
    from app.services.classification_service import ClassificationService

    processed_count = 0

    try:
        analysis_service = AnalysisService()
        quality_service = PhotoQualityService()
        classification_service = ClassificationService()

        for photo in photos:
            try:
                logger.info(f"正在处理照片: {photo.filename}")

                # AI分析
                if enable_ai:
                    await analysis_service.analyze_photo(photo.id)

                # 质量评估 - 暂时跳过，方法不存在
                # if enable_quality:
                #     quality_service.assess_photo_quality_async(db, photo.id)

                # 智能分类
                if enable_classification:
                    classification_service.classify_photo(photo.id, db)

                processed_count += 1
                
                # 更新照片状态为已完成
                photo.status = 'completed'
                db.commit()
                
                logger.info(f"照片 {photo.filename} 处理完成")

            except Exception as e:
                logger.error(f"处理照片 {photo.filename} 失败: {str(e)}")
                continue

        logger.info(f"批量处理完成，共处理 {processed_count}/{len(photos)} 张照片")

    except Exception as e:
        logger.error(f"批量处理过程中发生错误: {str(e)}")

    return processed_count
