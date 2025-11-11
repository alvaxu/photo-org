"""
相似照片聚类管理API接口

## 功能特点：
1. 相似照片聚类管理
2. 聚类照片浏览
3. 聚类统计信息
4. 与现有API结构集成

## 与其他版本的不同点：
- 参考人物管理API的结构设计
- 支持相似照片聚类管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging
from sqlalchemy import func

from app.db.session import get_db
from app.models.photo import Photo, DuplicateGroup, DuplicateGroupPhoto, PhotoTag, PhotoCategory
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/similar-photos-clusters", tags=["similar_photo_clusters"])


@router.get("/clusters")
async def get_all_clusters(
    limit: Optional[int] = Query(None, description="每页显示数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取所有相似照片聚类
    
    :param limit: 限制数量（默认从config.json读取photos_per_page）
    :param offset: 偏移量
    :param db: 数据库会话
    :return: 聚类列表
    """
    try:
        # 如果没有指定limit，从配置读取
        if limit is None:
            limit = getattr(settings.ui, 'photos_per_page', 30)
        
        # 只获取有cluster_id的聚类（排除旧的重复组数据）
        query = db.query(DuplicateGroup).filter(
            DuplicateGroup.cluster_id.isnot(None)
        ).order_by(
            DuplicateGroup.photo_count.desc()
        )
        
        total = query.count()
        
        # 应用分页
        query = query.offset(offset).limit(limit)
        
        clusters = query.all()
        
        result = []
        for cluster in clusters:
            # 获取第一张照片作为预览
            preview_photo = None
            first_member = db.query(DuplicateGroupPhoto).filter(
                DuplicateGroupPhoto.cluster_id == cluster.cluster_id
            ).order_by(DuplicateGroupPhoto.similarity_score.desc()).first()
            
            if first_member:
                photo = db.query(Photo).filter(Photo.id == first_member.photo_id).first()
                if photo:
                    # 确保路径使用正斜杠，避免URL解析问题
                    thumbnail_path = photo.thumbnail_path.replace('\\', '/') if photo.thumbnail_path else None
                    original_path = photo.original_path.replace('\\', '/') if photo.original_path else None
                    preview_photo = {
                        'id': photo.id,
                        'filename': photo.filename,
                        'thumbnail_path': thumbnail_path,
                        'original_path': original_path
                    }
            
            cluster_info = {
                "cluster_id": cluster.cluster_id,
                "photo_count": cluster.photo_count,
                "avg_similarity": cluster.avg_similarity,
                "confidence_score": cluster.confidence_score,
                "cluster_quality": cluster.cluster_quality,
                "similarity_threshold": cluster.similarity_threshold,
                "preview_photo": preview_photo,
                "created_at": cluster.created_at.isoformat() if cluster.created_at else None,
                "updated_at": cluster.updated_at.isoformat() if cluster.updated_at else None
            }
            result.append(cluster_info)
        
        return {
            "success": True,
            "clusters": result,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"获取相似照片聚类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters/{cluster_id}/photos")
async def get_cluster_photos(
    cluster_id: str,
    limit: int = None,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取聚类中的所有照片
    
    :param cluster_id: 聚类ID
    :param limit: 限制数量
    :param offset: 偏移量
    :param db: 数据库会话
    :return: 照片列表
    """
    try:
        # 获取聚类信息
        cluster = db.query(DuplicateGroup).filter(
            DuplicateGroup.cluster_id == cluster_id
        ).first()
        
        if not cluster:
            raise HTTPException(status_code=404, detail="聚类不存在")
        
        # 获取聚类成员
        query = db.query(DuplicateGroupPhoto, Photo).join(
            Photo, DuplicateGroupPhoto.photo_id == Photo.id
        ).filter(
            DuplicateGroupPhoto.cluster_id == cluster_id
        ).order_by(
            Photo.taken_at.desc().nulls_last(),  # 按拍摄时间降序，NULL值排在最后
            DuplicateGroupPhoto.similarity_score.desc()  # 如果拍摄时间相同，按相似度排序
        )
        
        total = query.count()
        
        if limit:
            query = query.offset(offset).limit(limit)
        
        members = query.all()
        
        result = []
        for member, photo in members:
            # 确保路径使用正斜杠，避免URL解析问题
            thumbnail_path = photo.thumbnail_path.replace('\\', '/') if photo.thumbnail_path else None
            original_path = photo.original_path.replace('\\', '/') if photo.original_path else None
            
            photo_info = {
                "photo_id": photo.id,
                "filename": photo.filename,
                "original_path": original_path,
                "thumbnail_path": thumbnail_path,
                "width": photo.width,
                "height": photo.height,
                "format": photo.format,
                "similarity_score": member.similarity_score,
                "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
                "created_at": photo.created_at.isoformat() if photo.created_at else None
            }
            result.append(photo_info)
        
        return {
            "success": True,
            "cluster_id": cluster_id,
            "photos": result,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聚类照片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clusters/{cluster_id}")
async def delete_cluster(
    cluster_id: str,
    db: Session = Depends(get_db)
):
    """
    删除聚类
    
    :param cluster_id: 聚类ID
    :param db: 数据库会话
    :return: 删除结果
    """
    try:
        # 获取聚类信息
        cluster = db.query(DuplicateGroup).filter(
            DuplicateGroup.cluster_id == cluster_id
        ).first()
        
        if not cluster:
            raise HTTPException(status_code=404, detail="聚类不存在")
        
        # 删除聚类成员（级联删除）
        db.query(DuplicateGroupPhoto).filter(
            DuplicateGroupPhoto.cluster_id == cluster_id
        ).delete()
        
        # 删除聚类
        db.delete(cluster)
        db.commit()
        
        return {
            "success": True,
            "message": "聚类已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除聚类失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/photos/{photo_id}/cluster")
async def get_photo_cluster(
    photo_id: int,
    db: Session = Depends(get_db)
):
    """
    根据照片ID查找它所属的聚类
    
    :param photo_id: 照片ID
    :param db: 数据库会话
    :return: 聚类信息
    """
    try:
        # 获取照片信息
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 检查照片是否有特征向量
        has_features = photo.image_features_extracted == True and photo.image_features is not None and photo.image_features != ''
        
        # 检查是否已经运行过聚类（通过检查是否有任何聚类存在）
        has_clusters = db.query(DuplicateGroup).filter(
            DuplicateGroup.cluster_id.isnot(None)
        ).count() > 0
        
        # 查找照片所属的聚类（只查找有cluster_id的聚类）
        cluster_member = db.query(DuplicateGroupPhoto).filter(
            DuplicateGroupPhoto.photo_id == photo_id,
            DuplicateGroupPhoto.cluster_id.isnot(None)
        ).first()
        
        if cluster_member:
            # 获取聚类信息
            cluster = db.query(DuplicateGroup).filter(
                DuplicateGroup.cluster_id == cluster_member.cluster_id
            ).first()
            
            if cluster:
                return {
                    "success": True,
                    "in_cluster": True,
                    "cluster_id": cluster.cluster_id,
                    "has_features": has_features,
                    "has_clusters": has_clusters,
                    "cluster_info": {
                        "photo_count": cluster.photo_count,
                        "avg_similarity": cluster.avg_similarity,
                        "cluster_quality": cluster.cluster_quality
                    }
                }
        
        # 照片不在任何聚类中
        # 根据是否运行过聚类来判断提示信息
        if has_clusters:
            # 已经运行过聚类，但照片不在任何聚类中（可能是噪声点或聚类后添加的照片）
            message = "照片不在任何聚类中，未找到相似照片"
        else:
            # 还没有运行过聚类
            message = "照片尚未进行聚类，请先运行聚类功能"
        
        return {
            "success": True,
            "in_cluster": False,
            "has_features": has_features,
            "has_clusters": has_clusters,
            "message": message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查找照片聚类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/photos/{photo_id}/similar-photos")
async def get_similar_photos_from_cluster(
    photo_id: int,
    limit: Optional[int] = Query(None, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    从聚类中获取与指定照片相似的照片（计算源照片与聚类中每张照片的相似度）
    
    :param photo_id: 源照片ID
    :param limit: 返回数量限制（默认从config.json读取similar_photos_limit）
    :param db: 数据库会话
    :return: 相似照片列表（按相似度降序排序）
    """
    try:
        from app.services.image_feature_service import image_feature_service
        import numpy as np
        
        # 如果没有指定limit，从配置读取
        if limit is None:
            limit = getattr(settings.ui, 'similar_photos_limit', 8)
        
        # 获取照片信息（预加载关联数据，用于格式化reference_photo）
        from sqlalchemy.orm import joinedload
        photo = db.query(Photo).options(
            joinedload(Photo.tags).joinedload(PhotoTag.tag),
            joinedload(Photo.categories).joinedload(PhotoCategory.category),
            joinedload(Photo.analysis_results),
            joinedload(Photo.quality_assessments)
        ).filter(Photo.id == photo_id).first()
        
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 检查照片是否有特征向量
        if not photo.image_features_extracted or not photo.image_features or photo.image_features == '':
            raise HTTPException(status_code=400, detail="照片尚未提取特征向量，请先运行特征提取")
        
        # 查找照片所属的聚类
        cluster_member = db.query(DuplicateGroupPhoto).filter(
            DuplicateGroupPhoto.photo_id == photo_id,
            DuplicateGroupPhoto.cluster_id.isnot(None)
        ).first()
        
        if not cluster_member:
            raise HTTPException(status_code=404, detail="照片不在任何聚类中，请先运行聚类功能")
        
        cluster_id = cluster_member.cluster_id
        
        # 获取聚类中的所有照片（排除源照片）
        cluster_members = db.query(DuplicateGroupPhoto, Photo).join(
            Photo, DuplicateGroupPhoto.photo_id == Photo.id
        ).filter(
            DuplicateGroupPhoto.cluster_id == cluster_id,
            DuplicateGroupPhoto.photo_id != photo_id  # 排除源照片
        ).all()
        
        if not cluster_members:
            # 格式化参考照片信息
            reference_thumbnail_path = photo.thumbnail_path.replace('\\', '/') if photo.thumbnail_path else None
            reference_original_path = photo.original_path.replace('\\', '/') if photo.original_path else None
            
            reference_photo = {
                "id": photo.id,
                "filename": photo.filename,
                "thumbnail_path": reference_thumbnail_path,
                "original_path": reference_original_path,
                "width": photo.width,
                "height": photo.height,
                "format": photo.format,
                "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
                "created_at": photo.created_at.isoformat() if photo.created_at else None
            }
            
            return {
                "success": True,
                "photos": [],
                "reference_photo": reference_photo,
                "total": 0,
                "message": "聚类中只有这一张照片"
            }
        
        # 加载源照片的特征向量
        reference_features = image_feature_service.load_features_from_db(photo)
        if reference_features is None:
            raise HTTPException(status_code=400, detail="无法加载源照片的特征向量")
        
        reference_features = np.array(reference_features).flatten()
        ref_norm = np.linalg.norm(reference_features)
        if ref_norm == 0:
            raise HTTPException(status_code=400, detail="源照片特征向量为零向量")
        
        # 计算源照片与聚类中每张照片的相似度
        similar_photos = []
        for member, cluster_photo in cluster_members:
            # 加载照片的特征向量
            photo_features = image_feature_service.load_features_from_db(cluster_photo)
            if photo_features is None:
                continue
            
            photo_features = np.array(photo_features).flatten()
            photo_norm = np.linalg.norm(photo_features)
            if photo_norm == 0:
                continue
            
            # 计算余弦相似度
            similarity = np.dot(photo_features, reference_features) / (photo_norm * ref_norm)
            
            # 确保路径使用正斜杠
            thumbnail_path = cluster_photo.thumbnail_path.replace('\\', '/') if cluster_photo.thumbnail_path else None
            original_path = cluster_photo.original_path.replace('\\', '/') if cluster_photo.original_path else None
            
            similar_photos.append({
                "photo": cluster_photo,  # 返回完整的Photo对象
                "similarity": float(similarity),
                "photo_id": cluster_photo.id,
                "filename": cluster_photo.filename,
                "thumbnail_path": thumbnail_path,
                "original_path": original_path,
                "width": cluster_photo.width,
                "height": cluster_photo.height,
                "format": cluster_photo.format,
                "taken_at": cluster_photo.taken_at.isoformat() if cluster_photo.taken_at else None,
                "created_at": cluster_photo.created_at.isoformat() if cluster_photo.created_at else None
            })
        
        # 按相似度降序排序
        similar_photos.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 限制返回数量
        result_photos = similar_photos[:limit]
        
        # 格式化参考照片信息（与老方法格式一致）
        # 确保路径使用正斜杠
        reference_thumbnail_path = photo.thumbnail_path.replace('\\', '/') if photo.thumbnail_path else None
        reference_original_path = photo.original_path.replace('\\', '/') if photo.original_path else None
        
        reference_photo = {
            "id": photo.id,
            "filename": photo.filename,
            "thumbnail_path": reference_thumbnail_path,
            "original_path": reference_original_path,
            "width": photo.width,
            "height": photo.height,
            "format": photo.format,
            "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
            "created_at": photo.created_at.isoformat() if photo.created_at else None
        }
        
        return {
            "success": True,
            "photos": result_photos,
            "reference_photo": reference_photo,
            "total": len(similar_photos),
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从聚类获取相似照片失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    db: Session = Depends(get_db)
):
    """
    获取相似照片聚类统计信息
    
    :param db: 数据库会话
    :return: 统计信息
    """
    try:
        # 只统计有cluster_id的聚类
        clusters = db.query(DuplicateGroup).filter(
            DuplicateGroup.cluster_id.isnot(None)
        ).all()
        
        total_clusters = len(clusters)
        total_photos = sum(cluster.photo_count for cluster in clusters)
        
        # 按质量统计
        high_quality = sum(1 for c in clusters if c.cluster_quality == 'high')
        medium_quality = sum(1 for c in clusters if c.cluster_quality == 'medium')
        low_quality = sum(1 for c in clusters if c.cluster_quality == 'low')
        
        # 计算平均相似度
        avg_similarity = None
        if clusters:
            similarities = [c.avg_similarity for c in clusters if c.avg_similarity is not None]
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
        
        return {
            "success": True,
            "statistics": {
                "total_clusters": total_clusters,
                "total_photos": total_photos,
                "high_quality_clusters": high_quality,
                "medium_quality_clusters": medium_quality,
                "low_quality_clusters": low_quality,
                "avg_similarity": avg_similarity
            }
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

