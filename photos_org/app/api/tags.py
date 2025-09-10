"""
家庭单机版智能照片整理系统 - 标签管理API
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.photo import Tag, Photo, PhotoTag

logger = get_logger(__name__)

router = APIRouter()


# 请求/响应模型
class TagCreate(BaseModel):
    """创建标签请求"""
    name: str = Field(..., description="标签名称", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="标签描述", max_length=200)


class TagUpdate(BaseModel):
    """更新标签请求"""
    name: Optional[str] = Field(None, description="标签名称", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="标签描述", max_length=200)


class TagResponse(BaseModel):
    """标签响应"""
    id: int = Field(..., description="标签ID")
    name: str = Field(..., description="标签名称")
    description: Optional[str] = Field(None, description="标签描述")
    photo_count: int = Field(..., description="关联照片数量")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


# 注意：路由顺序很重要，具体的路由必须在参数路由之前

@router.get("/stats", response_model=Dict[str, Any])
async def get_tag_statistics(db: Session = Depends(get_db)):
    """
    获取标签统计信息
    """
    try:
        from sqlalchemy import func

        # 基础统计
        total_tags = db.query(func.count(Tag.id)).scalar() or 0
        total_photo_tag_relations = db.query(func.count(PhotoTag.id)).scalar() or 0

        # 平均每个标签的使用次数
        avg_usage = total_photo_tag_relations / total_tags if total_tags > 0 else 0

        # 最热门的标签
        most_popular = db.query(
            Tag.name,
            func.count(PhotoTag.photo_id).label('usage_count')
        ).join(PhotoTag)\
         .group_by(Tag.id, Tag.name)\
         .order_by(func.count(PhotoTag.photo_id).desc())\
         .first()

        return {
            "total_tags": total_tags,
            "total_relations": total_photo_tag_relations,
            "average_usage": round(avg_usage, 2),
            "most_popular_tag": {
                "name": most_popular[0] if most_popular else None,
                "usage_count": most_popular[1] if most_popular else 0
            } if most_popular else None,
            "last_updated": None  # 可以后续添加更新时间
        }

    except Exception as e:
        logger.error(f"获取标签统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签统计失败: {str(e)}")


@router.get("/", response_model=List[TagResponse])
async def get_tags(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=500, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取标签列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数上限
    - **search**: 搜索关键词
    """
    try:
        query = db.query(Tag)

        # 搜索过滤
        if search:
            query = query.filter(Tag.name.ilike(f'%{search}%'))

        # 获取标签和关联照片数量
        tags = query.offset(skip).limit(limit).all()

        # 构建响应
        result = []
        for tag in tags:
            # 计算关联照片数量
            photo_count = db.query(PhotoTag).filter(PhotoTag.tag_id == tag.id).count()

            result.append(TagResponse(
                id=tag.id,
                name=tag.name,
                description=tag.description,
                photo_count=photo_count,
                created_at=tag.created_at.isoformat() if tag.created_at else None,
                updated_at=tag.updated_at.isoformat() if tag.updated_at else None
            ))

        return result

    except Exception as e:
        logger.error(f"获取标签列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签列表失败: {str(e)}")


@router.get("/popular", response_model=List[Dict[str, Any]])
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100, description="返回的标签数量"),
    db: Session = Depends(get_db)
):
    """
    获取热门标签（按使用频率排序）

    - **limit**: 返回的标签数量上限
    """
    try:
        from sqlalchemy import func

        # 查询标签使用频率
        tag_usage = db.query(
            Tag.id,
            Tag.name,
            Tag.description,
            func.count(PhotoTag.photo_id).label('usage_count')
        ).join(PhotoTag, Tag.id == PhotoTag.tag_id)\
         .group_by(Tag.id, Tag.name, Tag.description)\
         .order_by(func.count(PhotoTag.photo_id).desc())\
         .limit(limit)\
         .all()

        result = []
        for tag_id, name, description, usage_count in tag_usage:
            result.append({
                "id": tag_id,
                "name": name,
                "description": description,
                "usage_count": usage_count
            })

        return result

    except Exception as e:
        logger.error(f"获取热门标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取热门标签失败: {str(e)}")


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: int, db: Session = Depends(get_db)):
    """
    获取标签详情

    - **tag_id**: 标签ID
    """
    try:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")

        # 计算关联照片数量
        photo_count = db.query(PhotoTag).filter(PhotoTag.tag_id == tag_id).count()

        return TagResponse(
            id=tag.id,
            name=tag.name,
            description=tag.description,
            photo_count=photo_count,
            created_at=tag.created_at.isoformat() if tag.created_at else None,
            updated_at=tag.updated_at.isoformat() if tag.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取标签详情失败 tag_id={tag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签详情失败: {str(e)}")


@router.post("/", response_model=TagResponse)
async def create_tag(request: TagCreate, db: Session = Depends(get_db)):
    """
    创建新标签

    - **request**: 标签创建请求
    """
    try:
        # 检查标签名称是否已存在
        existing_tag = db.query(Tag).filter(Tag.name == request.name).first()
        if existing_tag:
            raise HTTPException(status_code=400, detail="标签名称已存在")

        # 创建新标签
        tag = Tag(
            name=request.name,
            description=request.description
        )

        db.add(tag)
        db.commit()
        db.refresh(tag)

        return TagResponse(
            id=tag.id,
            name=tag.name,
            description=tag.description,
            photo_count=0,
            created_at=tag.created_at.isoformat() if tag.created_at else None,
            updated_at=tag.updated_at.isoformat() if tag.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建标签失败: {str(e)}")


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: int, request: TagUpdate, db: Session = Depends(get_db)):
    """
    更新标签信息

    - **tag_id**: 标签ID
    - **request**: 标签更新请求
    """
    try:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")

        # 检查新名称是否与其他标签冲突
        if request.name and request.name != tag.name:
            existing_tag = db.query(Tag).filter(Tag.name == request.name).first()
            if existing_tag:
                raise HTTPException(status_code=400, detail="标签名称已存在")

        # 更新字段
        if request.name is not None:
            tag.name = request.name
        if request.description is not None:
            tag.description = request.description

        tag.updated_at = None  # 让SQLAlchemy自动更新

        db.commit()
        db.refresh(tag)

        # 计算关联照片数量
        photo_count = db.query(PhotoTag).filter(PhotoTag.tag_id == tag_id).count()

        return TagResponse(
            id=tag.id,
            name=tag.name,
            description=tag.description,
            photo_count=photo_count,
            created_at=tag.created_at.isoformat() if tag.created_at else None,
            updated_at=tag.updated_at.isoformat() if tag.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新标签失败 tag_id={tag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新标签失败: {str(e)}")


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """
    删除标签

    - **tag_id**: 标签ID
    """
    try:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")

        # 检查是否有照片使用此标签
        photo_count = db.query(PhotoTag).filter(PhotoTag.tag_id == tag_id).count()
        if photo_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"标签正在被 {photo_count} 张照片使用，无法删除"
            )

        # 删除标签
        db.delete(tag)
        db.commit()

        return {
            "message": "标签删除成功",
            "tag_id": tag_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除标签失败 tag_id={tag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除标签失败: {str(e)}")


