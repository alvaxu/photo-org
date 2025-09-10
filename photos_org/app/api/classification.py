"""
分类标签API接口
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.classification_service import ClassificationService
from app.schemas.photo import PhotoResponse

router = APIRouter()


@router.post("/photos/{photo_id}/classify", response_model=dict)
async def classify_photo(
    photo_id: int,
    db: Session = Depends(get_db)
):
    """
    对指定照片进行自动分类和标签生成

    Args:
        photo_id: 照片ID

    Returns:
        分类结果
    """
    service = ClassificationService()
    result = service.classify_photo(photo_id, db)

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.get("/photos/{photo_id}/classifications", response_model=List[dict])
async def get_photo_classifications(
    photo_id: int,
    db: Session = Depends(get_db)
):
    """
    获取照片的分类信息

    Args:
        photo_id: 照片ID

    Returns:
        分类信息列表
    """
    service = ClassificationService()
    classifications = service.get_photo_classifications(photo_id, db)
    return classifications


@router.get("/photos/{photo_id}/tags", response_model=List[dict])
async def get_photo_tags(
    photo_id: int,
    db: Session = Depends(get_db)
):
    """
    获取照片的标签信息

    Args:
        photo_id: 照片ID

    Returns:
        标签信息列表
    """
    service = ClassificationService()
    tags = service.get_photo_tags(photo_id, db)
    return tags


@router.post("/categories", response_model=dict)
async def create_category(
    name: str,
    description: str = "",
    parent_id: int = None,
    db: Session = Depends(get_db)
):
    """
    创建新的分类

    Args:
        name: 分类名称
        description: 分类描述
        parent_id: 父分类ID

    Returns:
        创建结果
    """
    service = ClassificationService()
    result = service.create_manual_category(name, description, parent_id, db)

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.post("/photos/{photo_id}/tags", response_model=dict)
async def add_photo_tag(
    photo_id: int,
    tag_name: str,
    db: Session = Depends(get_db)
):
    """
    为照片添加标签

    Args:
        photo_id: 照片ID
        tag_name: 标签名称

    Returns:
        添加结果
    """
    service = ClassificationService()
    result = service.add_manual_tag(photo_id, tag_name, db)

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.get("/categories", response_model=List[dict])
async def get_categories(
    category_type: str = None,
    db: Session = Depends(get_db)
):
    """
    获取所有分类

    Args:
        category_type: 分类类型过滤 (auto/manual)

    Returns:
        分类列表
    """
    from app.models.photo import Category

    query = db.query(Category)

    if category_type:
        query = query.filter(Category.category_type == category_type)

    categories = query.order_by(Category.sort_order).all()

    result = []
    for category in categories:
        result.append({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'type': category.category_type,
            'parent_id': category.parent_id,
            'sort_order': category.sort_order,
            'created_at': category.created_at.isoformat() if category.created_at else None
        })

    return result


@router.get("/tags", response_model=List[dict])
async def get_tags(
    category: str = None,
    db: Session = Depends(get_db)
):
    """
    获取所有标签

    Args:
        category: 标签类别过滤

    Returns:
        标签列表
    """
    from app.models.photo import Tag

    query = db.query(Tag)

    if category:
        query = query.filter(Tag.category == category)

    tags = query.order_by(Tag.usage_count.desc()).all()

    result = []
    for tag in tags:
        result.append({
            'id': tag.id,
            'name': tag.name,
            'description': tag.description,
            'category': tag.category,
            'usage_count': tag.usage_count,
            'created_at': tag.created_at.isoformat() if tag.created_at else None
        })

    return result


@router.get("/categories/{category_id}/photos", response_model=List[dict])
async def get_category_photos(
    category_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取指定分类下的照片

    Args:
        category_id: 分类ID
        skip: 跳过的记录数
        limit: 返回记录数限制

    Returns:
        照片列表
    """
    from app.models.photo import PhotoCategory, Photo

    photo_ids = db.query(PhotoCategory.photo_id).filter(
        PhotoCategory.category_id == category_id
    ).offset(skip).limit(limit).all()

    photo_ids = [pid[0] for pid in photo_ids]

    if not photo_ids:
        return []

    photos = db.query(Photo).filter(Photo.id.in_(photo_ids)).all()

    result = []
    for photo in photos:
        result.append({
            'id': photo.id,
            'filename': photo.filename,
            'file_size': photo.file_size,
            'thumbnail_path': photo.thumbnail_path,
            'taken_at': photo.taken_at.isoformat() if photo.taken_at else None,
            'camera_model': photo.camera_model,
            'width': photo.width,
            'height': photo.height
        })

    return result


@router.get("/tags/{tag_id}/photos", response_model=List[dict])
async def get_tag_photos(
    tag_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取指定标签下的照片

    Args:
        tag_id: 标签ID
        skip: 跳过的记录数
        limit: 返回记录数限制

    Returns:
        照片列表
    """
    from app.models.photo import PhotoTag, Photo

    photo_ids = db.query(PhotoTag.photo_id).filter(
        PhotoTag.tag_id == tag_id
    ).offset(skip).limit(limit).all()

    photo_ids = [pid[0] for pid in photo_ids]

    if not photo_ids:
        return []

    photos = db.query(Photo).filter(Photo.id.in_(photo_ids)).all()

    result = []
    for photo in photos:
        result.append({
            'id': photo.id,
            'filename': photo.filename,
            'file_size': photo.file_size,
            'thumbnail_path': photo.thumbnail_path,
            'taken_at': photo.taken_at.isoformat() if photo.taken_at else None,
            'camera_model': photo.camera_model,
            'width': photo.width,
            'height': photo.height
        })

    return result
