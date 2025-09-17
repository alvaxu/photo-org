"""
家庭版智能照片系统 - 分类管理API
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.photo import Category, Photo, PhotoCategory

logger = get_logger(__name__)

router = APIRouter()


# 请求/响应模型
class CategoryCreate(BaseModel):
    """创建分类请求"""
    name: str = Field(..., description="分类名称", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="分类描述", max_length=200)
    parent_id: Optional[int] = Field(None, description="父分类ID")


class CategoryUpdate(BaseModel):
    """更新分类请求"""
    name: Optional[str] = Field(None, description="分类名称", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="分类描述", max_length=200)
    parent_id: Optional[int] = Field(None, description="父分类ID")


class CategoryResponse(BaseModel):
    """分类响应"""
    id: int = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    photo_count: int = Field(..., description="关联照片数量")
    children_count: int = Field(..., description="子分类数量")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class CategoryTreeResponse(BaseModel):
    """分类树响应"""
    id: int = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    photo_count: int = Field(..., description="关联照片数量")
    children: List['CategoryTreeResponse'] = Field(default_factory=list, description="子分类列表")


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=500, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    parent_id: Optional[int] = Query(None, description="父分类ID"),
    db: Session = Depends(get_db)
):
    """
    获取分类列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数上限
    - **search**: 搜索关键词
    - **parent_id**: 父分类ID（None表示顶级分类）
    """
    try:
        query = db.query(Category)

        # 父分类过滤
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        else:
            # 默认只返回顶级分类
            query = query.filter(Category.parent_id.is_(None))

        # 搜索过滤
        if search:
            query = query.filter(Category.name.ilike(f'%{search}%'))

        # 排序：系统分类优先，然后按ID排序
        query = query.order_by(
            Category.name.in_(['家庭照片', '旅行照片', '工作照片', '社交活动', '日常生活']).desc(),
            Category.id
        )

        # 获取分类
        categories = query.offset(skip).limit(limit).all()

        # 构建响应
        result = []
        for category in categories:
            # 计算关联照片数量
            photo_count = db.query(PhotoCategory).filter(PhotoCategory.category_id == category.id).count()

            # 计算子分类数量
            children_count = db.query(Category).filter(Category.parent_id == category.id).count()

            result.append(CategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                parent_id=category.parent_id,
                photo_count=photo_count,
                children_count=children_count,
                created_at=category.created_at.isoformat() if category.created_at else None,
                updated_at=category.updated_at.isoformat() if category.updated_at else None
            ))

        return result

    except Exception as e:
        logger.error(f"获取分类列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类列表失败: {str(e)}")


@router.get("/tree", response_model=List[CategoryTreeResponse])
async def get_category_tree(db: Session = Depends(get_db)):
    """
    获取分类树结构
    """
    try:
        def build_tree(parent_id: Optional[int] = None) -> List[CategoryTreeResponse]:
            """递归构建分类树"""
            categories = db.query(Category).filter(Category.parent_id == parent_id).all()

            result = []
            for category in categories:
                # 计算照片数量
                photo_count = db.query(PhotoCategory).filter(PhotoCategory.category_id == category.id).count()

                # 递归获取子分类
                children = build_tree(category.id)

                tree_item = CategoryTreeResponse(
                    id=category.id,
                    name=category.name,
                    description=category.description,
                    parent_id=category.parent_id,
                    photo_count=photo_count,
                    children=children
                )

                result.append(tree_item)

            return result

        # 构建顶级分类树
        return build_tree()

    except Exception as e:
        logger.error(f"获取分类树失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类树失败: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_category_statistics(db: Session = Depends(get_db)):
    """
    获取分类统计信息
    """
    try:
        from sqlalchemy import func

        # 基础统计
        total_categories = db.query(func.count(Category.id)).scalar() or 0
        total_photo_category_relations = db.query(func.count(PhotoCategory.id)).scalar() or 0

        # 顶级分类数量
        top_level_categories = db.query(func.count(Category.id)).filter(Category.parent_id.is_(None)).scalar() or 0

        # 平均每个分类的照片数量
        avg_photos_per_category = total_photo_category_relations / total_categories if total_categories > 0 else 0

        # 最热门的分类
        most_popular = db.query(
            Category.name,
            func.count(PhotoCategory.photo_id).label('usage_count')
        ).join(PhotoCategory)\
         .group_by(Category.id, Category.name)\
         .order_by(func.count(PhotoCategory.photo_id).desc())\
         .first()

        # 分类层级统计
        max_depth = 0
        def calculate_depth(category_id: int, current_depth: int = 1):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)

            children = db.query(Category).filter(Category.parent_id == category_id).all()
            for child in children:
                calculate_depth(child.id, current_depth + 1)

        # 计算所有顶级分类的深度
        top_categories = db.query(Category).filter(Category.parent_id.is_(None)).all()
        for category in top_categories:
            calculate_depth(category.id)

        return {
            "total_categories": total_categories,
            "top_level_categories": top_level_categories,
            "total_relations": total_photo_category_relations,
            "average_photos_per_category": round(avg_photos_per_category, 2),
            "max_depth": max_depth,
            "most_popular_category": {
                "name": most_popular[0] if most_popular else None,
                "usage_count": most_popular[1] if most_popular else 0
            } if most_popular else None,
            "last_updated": None  # 可以后续添加更新时间
        }

    except Exception as e:
        logger.error(f"获取分类统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类统计失败: {str(e)}")


@router.get("/popular", response_model=List[Dict[str, Any]])
async def get_popular_categories(
    limit: int = Query(20, ge=1, le=100, description="返回的分类数量"),
    db: Session = Depends(get_db)
):
    """
    获取热门分类（按照片数量排序）

    - **limit**: 返回的分类数量上限
    """
    try:
        from sqlalchemy import func

        # 查询分类使用频率
        category_usage = db.query(
            Category.id,
            Category.name,
            Category.description,
            func.count(PhotoCategory.photo_id).label('usage_count')
        ).join(PhotoCategory, Category.id == PhotoCategory.category_id)\
         .group_by(Category.id, Category.name, Category.description)\
         .order_by(func.count(PhotoCategory.photo_id).desc())\
         .limit(limit)\
         .all()

        result = []
        for category_id, name, description, usage_count in category_usage:
            result.append({
                "id": category_id,
                "name": name,
                "description": description,
                "usage_count": usage_count
            })

        return result

    except Exception as e:
        logger.error(f"获取热门分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取热门分类失败: {str(e)}")


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """
    获取分类详情

    - **category_id**: 分类ID
    """
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        # 计算关联照片数量
        photo_count = db.query(PhotoCategory).filter(PhotoCategory.category_id == category_id).count()

        # 计算子分类数量
        children_count = db.query(Category).filter(Category.parent_id == category_id).count()

        return CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            photo_count=photo_count,
            children_count=children_count,
            created_at=category.created_at.isoformat() if category.created_at else None,
            updated_at=category.updated_at.isoformat() if category.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类详情失败 category_id={category_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类详情失败: {str(e)}")


@router.post("/", response_model=CategoryResponse)
async def create_category(request: CategoryCreate, db: Session = Depends(get_db)):
    """
    创建新分类

    - **request**: 分类创建请求
    """
    try:
        # 检查分类名称是否已存在
        existing_category = db.query(Category).filter(Category.name == request.name).first()
        if existing_category:
            raise HTTPException(status_code=400, detail="分类名称已存在")

        # 检查父分类是否存在
        if request.parent_id:
            parent_category = db.query(Category).filter(Category.id == request.parent_id).first()
            if not parent_category:
                raise HTTPException(status_code=404, detail="父分类不存在")

        # 创建新分类
        category = Category(
            name=request.name,
            description=request.description,
            parent_id=request.parent_id
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            photo_count=0,
            children_count=0,
            created_at=category.created_at.isoformat() if category.created_at else None,
            updated_at=category.updated_at.isoformat() if category.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, request: CategoryUpdate, db: Session = Depends(get_db)):
    """
    更新分类信息

    - **category_id**: 分类ID
    - **request**: 分类更新请求
    """
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        # 检查新名称是否与其他分类冲突
        if request.name and request.name != category.name:
            existing_category = db.query(Category).filter(Category.name == request.name).first()
            if existing_category:
                raise HTTPException(status_code=400, detail="分类名称已存在")

        # 检查父分类是否存在（如果要更新父分类）
        if request.parent_id is not None:
            if request.parent_id != category.id:  # 不能将自己设为父分类
                if request.parent_id:
                    parent_category = db.query(Category).filter(Category.id == request.parent_id).first()
                    if not parent_category:
                        raise HTTPException(status_code=404, detail="父分类不存在")
                # 检查是否会形成循环引用
                if request.parent_id:
                    current_id = request.parent_id
                    visited = set([category_id])
                    while current_id:
                        if current_id in visited:
                            raise HTTPException(status_code=400, detail="不能形成循环引用")
                        visited.add(current_id)
                        parent = db.query(Category).filter(Category.id == current_id).first()
                        current_id = parent.parent_id if parent else None

        # 更新字段
        if request.name is not None:
            category.name = request.name
        if request.description is not None:
            category.description = request.description
        if request.parent_id is not None:
            category.parent_id = request.parent_id

        category.updated_at = None  # 让SQLAlchemy自动更新

        db.commit()
        db.refresh(category)

        # 计算关联照片数量
        photo_count = db.query(PhotoCategory).filter(PhotoCategory.category_id == category_id).count()

        # 计算子分类数量
        children_count = db.query(Category).filter(Category.parent_id == category_id).count()

        return CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            photo_count=photo_count,
            children_count=children_count,
            created_at=category.created_at.isoformat() if category.created_at else None,
            updated_at=category.updated_at.isoformat() if category.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新分类失败 category_id={category_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新分类失败: {str(e)}")


@router.delete("/{category_id}")
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    删除分类

    - **category_id**: 分类ID
    """
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        # 检查是否有子分类
        children_count = db.query(Category).filter(Category.parent_id == category_id).count()
        if children_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"分类有 {children_count} 个子分类，无法删除"
            )

        # 检查是否有照片使用此分类
        photo_count = db.query(PhotoCategory).filter(PhotoCategory.category_id == category_id).count()
        if photo_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"分类正在被 {photo_count} 张照片使用，无法删除"
            )

        # 删除分类
        db.delete(category)
        db.commit()

        return {
            "message": "分类删除成功",
            "category_id": category_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除分类失败 category_id={category_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除分类失败: {str(e)}")



