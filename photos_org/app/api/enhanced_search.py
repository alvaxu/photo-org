"""
程序说明：

## 1. 增强搜索API
## 2. 使用多算法融合的相似照片检测
## 3. 提供更准确的相似照片搜索结果
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.photo import Photo
from app.services.enhanced_similarity_service import EnhancedSimilarityService
from app.schemas.photo import PhotoSearchResult

router = APIRouter(prefix="/api/v1/enhanced-search", tags=["enhanced-search"])


@router.get("/similar/{photo_id}")
async def search_enhanced_similar_photos(
    photo_id: int,
    threshold: float = Query(0.55, ge=0.0, le=1.0, description="相似度阈值"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    使用增强算法搜索相似照片
    
    融合感知哈希、时间、位置、标签等多种特征
    """
    try:
        # 获取参考照片
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 检查照片是否有感知哈希值
        if not photo.perceptual_hash:
            raise HTTPException(status_code=400, detail="照片缺少感知哈希值，无法进行相似搜索")
        
        # 使用增强相似性服务
        enhanced_service = EnhancedSimilarityService()
        
        # 搜索相似照片
        similar_photos = enhanced_service.find_enhanced_similar_photos(
            db_session=db,
            reference_photo_id=photo_id,
            threshold=threshold,
            limit=limit
        )
        
        # 格式化结果
        results = []
        for similar_photo in similar_photos:
            # 从数据库获取完整的照片对象
            photo_obj = db.query(Photo).filter(Photo.id == similar_photo['photo_id']).first()
            if photo_obj:
                result = {
                    "id": photo_obj.id,
                    "filename": photo_obj.filename,
                    "thumbnail_path": photo_obj.thumbnail_path,
                    "original_path": photo_obj.original_path,
                    "taken_at": photo_obj.taken_at.isoformat() if photo_obj.taken_at else None,
                    "created_at": photo_obj.created_at.isoformat() if photo_obj.created_at else None,
                    "similarity": similar_photo['similarity'],
                    "similarities": similar_photo.get('similarities', {})
                }
                results.append(result)
        
        return {
            "success": True,
            "data": {
                "reference_photo_id": photo_id,
                "reference_filename": photo.filename,
                "total": len(results),
                "similar_photos": results,
                "threshold": threshold
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索相似照片失败: {str(e)}")


@router.get("/similar-by-type/{photo_id}")
async def search_similar_by_type(
    photo_id: int,
    similarity_type: str = Query("combined", description="相似度类型: phash, time, location, tags, combined"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="相似度阈值"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    按特定类型搜索相似照片
    
    可以单独使用某种相似度算法
    """
    try:
        # 获取参考照片
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 使用增强相似性服务
        enhanced_service = EnhancedSimilarityService()
        
        # 获取所有其他照片
        other_photos = db.query(Photo).filter(
            Photo.id != photo_id,
            Photo.perceptual_hash.isnot(None)
        ).all()
        
        similar_photos = []
        
        for other_photo in other_photos:
            try:
                # 计算综合相似度
                similarities = enhanced_service.calculate_combined_similarity(photo, other_photo, db)
                
                # 根据类型选择相似度
                if similarity_type in similarities:
                    sim_score = similarities[similarity_type]
                else:
                    sim_score = similarities['combined']
                
                # 检查是否满足阈值
                if sim_score >= threshold:
                    similar_photos.append({
                        'photo_id': other_photo.id,
                        'filename': other_photo.filename,
                        'file_path': other_photo.original_path,
                        'thumbnail_path': other_photo.thumbnail_path,
                        'similarity': sim_score,
                        'similarities': similarities,
                        'taken_at': other_photo.taken_at,
                        'created_at': other_photo.created_at
                    })
                    
            except Exception as e:
                continue
        
        # 按相似度排序
        similar_photos.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 格式化结果
        results = []
        for similar_photo in similar_photos[:limit]:
            result = {
                "id": similar_photo['photo_id'],
                "filename": similar_photo['filename'],
                "thumbnail_path": similar_photo['thumbnail_path'],
                "original_path": similar_photo['file_path'],
                "taken_at": similar_photo['taken_at'].isoformat() if similar_photo['taken_at'] else None,
                "created_at": similar_photo['created_at'].isoformat() if similar_photo['created_at'] else None,
                "similarity": similar_photo['similarity'],
                "similarities": similar_photo.get('similarities', {})
            }
            results.append(result)
        
        return {
            "success": True,
            "data": {
                "reference_photo_id": photo_id,
                "reference_filename": photo.filename,
                "similarity_type": similarity_type,
                "total": len(results),
                "similar_photos": results,
                "threshold": threshold
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"按类型搜索相似照片失败: {str(e)}")


@router.get("/test-algorithms/{photo_id}")
async def test_algorithms(
    photo_id: int,
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    测试不同算法的效果
    
    返回各种算法的相似度分数，用于调试和优化
    """
    try:
        # 获取参考照片
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 使用增强相似性服务
        enhanced_service = EnhancedSimilarityService()
        
        # 获取所有其他照片
        other_photos = db.query(Photo).filter(
            Photo.id != photo_id,
            Photo.perceptual_hash.isnot(None)
        ).all()
        
        test_results = []
        
        for other_photo in other_photos[:limit]:
            try:
                # 计算综合相似度
                similarities = enhanced_service.calculate_combined_similarity(photo, other_photo, db)
                
                test_results.append({
                    "photo_id": other_photo.id,
                    "filename": other_photo.filename,
                    "similarities": similarities,
                    "taken_at": other_photo.taken_at.isoformat() if other_photo.taken_at else None
                })
                
            except Exception as e:
                continue
        
        # 按综合相似度排序
        test_results.sort(key=lambda x: x['similarities']['combined'], reverse=True)
        
        return {
            "success": True,
            "data": {
                "reference_photo_id": photo_id,
                "reference_filename": photo.filename,
                "test_results": test_results
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试算法失败: {str(e)}")


@router.get("/similar/first-layer/{photo_id}")
async def search_first_layer_similar_photos(
    photo_id: int,
    threshold: float = Query(0.1, ge=0.0, le=1.0, description="第一层相似度阈值"),
    limit: int = Query(12, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    第一层快速筛选相似照片（9种数据库相似度）
    
    使用时间、位置、相机、感知哈希、AI场景、AI对象、AI情感、AI活动、AI标签
    """
    try:
        # 获取参考照片
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 使用增强相似性服务
        enhanced_service = EnhancedSimilarityService()
        
        # 第一层快速筛选
        similar_photos = enhanced_service.find_first_layer_similar_photos(
            db_session=db,
            reference_photo_id=photo_id,
            threshold=threshold,
            limit=limit
        )
        
        # 转换为响应格式
        results = []
        for photo_data in similar_photos:
            results.append({
                "id": photo_data['photo'].id,
                "filename": photo_data['photo'].filename,
                "thumbnail_path": photo_data['photo'].thumbnail_path,
                "original_path": photo_data['photo'].original_path,
                "taken_at": photo_data['photo'].taken_at.isoformat() if photo_data['photo'].taken_at else None,
                "created_at": photo_data['photo'].created_at.isoformat() if photo_data['photo'].created_at else None,
                "similarity": photo_data['similarity'],
                "similarities": photo_data.get('details', {})
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
                "threshold": threshold,
                "layer": "first"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"第一层相似照片搜索失败: {str(e)}")


@router.get("/similar/second-layer/{reference_photo_id}")
async def search_second_layer_similar_photos(
    reference_photo_id: int,
    photo_ids: str = Query(..., description="照片ID列表，用逗号分隔"),
    threshold: float = Query(0.05, ge=0.0, le=1.0, description="第二层相似度阈值"),
    db: Session = Depends(get_db)
):
    """
    第二层精确匹配相似照片（3种复杂相似度）
    
    对指定的照片列表使用颜色直方图、结构相似度(SSIM)、AI描述相似度
    """
    try:
        # 获取参考照片
        reference_photo = db.query(Photo).filter(Photo.id == reference_photo_id).first()
        if not reference_photo:
            raise HTTPException(status_code=404, detail="参考照片不存在")
        
        # 解析照片ID列表
        photo_id_list = [int(id.strip()) for id in photo_ids.split(',') if id.strip()]
        
        # 获取候选照片
        candidate_photos = db.query(Photo).filter(Photo.id.in_(photo_id_list)).all()
        if not candidate_photos:
            raise HTTPException(status_code=404, detail="候选照片不存在")
        
        # 使用增强相似性服务
        enhanced_service = EnhancedSimilarityService()
        
        # 第二层精确匹配
        similar_photos = enhanced_service.find_second_layer_similar_photos(
            db_session=db,
            reference_photo=reference_photo,
            candidate_photos=candidate_photos,
            threshold=threshold
        )
        
        # 转换为响应格式
        results = []
        for photo_data in similar_photos:
            results.append({
                "id": photo_data['photo'].id,
                "filename": photo_data['photo'].filename,
                "thumbnail_path": photo_data['photo'].thumbnail_path,
                "original_path": photo_data['photo'].original_path,
                "taken_at": photo_data['photo'].taken_at.isoformat() if photo_data['photo'].taken_at else None,
                "created_at": photo_data['photo'].created_at.isoformat() if photo_data['photo'].created_at else None,
                "similarity": photo_data['similarity'],
                "similarities": photo_data.get('details', {})
            })
        
        return {
            "success": True,
            "data": {
                "reference_photo": {
                    "id": reference_photo.id,
                    "filename": reference_photo.filename,
                    "thumbnail_path": reference_photo.thumbnail_path
                },
                "similar_photos": results,
                "total": len(results),
                "threshold": threshold,
                "layer": "second"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"第二层相似照片搜索失败: {str(e)}")
