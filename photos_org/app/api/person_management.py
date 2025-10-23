"""
人物管理API接口

## 功能特点：
1. 人物聚类管理
2. 人物命名功能
3. 肖像照生成
4. 人物照片浏览
5. 与现有API结构集成

## 与其他版本的不同点：
- 集成到现有API结构
- 支持人物管理功能
- 提供肖像照生成
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

from app.db.session import get_db
from app.core.config import settings
from app.models.face import FaceDetection, FaceCluster, FaceClusterMember, Person
from app.models.photo import Photo
from app.services.face_crop_service import face_crop_service
from sqlalchemy import func

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/face-clusters", tags=["person_management"])

@router.get("/clusters")
async def get_all_clusters(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取所有聚类分组（简化版）
    :param limit: 限制数量
    :param offset: 偏移量
    :param db: 数据库会话
    :return: 聚类列表
    """
    try:
        clusters = db.query(FaceCluster).offset(offset).limit(limit).all()
        
        result = []
        for cluster in clusters:
            # 获取代表人脸（第一张照片）
            representative_face = db.query(FaceDetection).filter(
                FaceDetection.face_id == cluster.representative_face_id
            ).first()
            
            # 获取代表人脸的照片路径和人脸裁剪图
            representative_photo_path = None
            face_crop_url = None
            if representative_face:
                photo = db.query(Photo).filter(Photo.id == representative_face.photo_id).first()
                if photo:
                    representative_photo_path = photo.original_path
                    # 生成人脸裁剪图（添加30%填充，显示更完整的头部）
                    face_crop_url = face_crop_service.get_face_crop_url(
                        photo.original_path,
                        representative_face.face_rectangle,
                        crop_size=150,
                        crop_type="circle",
                        padding_ratio=0.3
                    )
            
            cluster_info = {
                "cluster_id": cluster.cluster_id,
                "person_name": cluster.person_name,
                "person_id": cluster.person_id,
                "face_count": cluster.face_count,
                "is_labeled": cluster.is_labeled,
                "confidence": cluster.confidence_score,
                "cluster_quality": cluster.cluster_quality,
                "representative_photo_id": representative_face.photo_id if representative_face else None,
                "representative_photo_path": representative_photo_path,
                "face_crop_url": face_crop_url,
                "created_at": cluster.created_at.isoformat() if cluster.created_at else None,
                "updated_at": cluster.updated_at.isoformat() if cluster.updated_at else None
            }
            result.append(cluster_info)
        
        return {
            "success": True,
            "clusters": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"获取聚类列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clusters/{cluster_id}/name")
async def name_cluster(
    cluster_id: str,
    request: Dict[str, str],
    db: Session = Depends(get_db)
):
    """
    标记聚类分组
    :param cluster_id: 聚类ID
    :param request: 请求数据
    :param db: 数据库会话
    :return: 标记结果
    """
    try:
        cluster = db.query(FaceCluster).filter(
            FaceCluster.cluster_id == cluster_id
        ).first()
        
        if not cluster:
            raise HTTPException(status_code=404, detail="分组不存在")
        
        person_name = request.get("person_name", "").strip()
        person_id = request.get("person_id", f"person_{cluster_id}_{int(time.time())}")
        
        if not person_name:
            raise HTTPException(status_code=400, detail="人物姓名不能为空")
        
        # 更新聚类标签
        cluster.person_name = person_name
        cluster.person_id = person_id
        cluster.is_labeled = True
        
        # 创建或更新人物记录
        person = db.query(Person).filter(
            Person.person_name == person_name
        ).first()
        
        if not person:
            person = Person(
                person_id=person_id,
                person_name=person_name,
                display_name=person_name
            )
            db.add(person)
            db.flush()
        
        cluster.person_id = person.person_id
        db.commit()
        
        return {
            "success": True,
            "message": f"聚类 {cluster_id} 已标记为 {person_name}"
        }
        
    except Exception as e:
        logger.error(f"标记聚类失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clusters/{cluster_id}/portrait")
async def get_cluster_portrait(
    cluster_id: str,
    db: Session = Depends(get_db)
):
    """
    获取聚类分组的肖像照
    :param cluster_id: 聚类ID
    :param db: 数据库会话
    :return: 肖像照信息
    """
    try:
        # 获取聚类信息
        cluster = db.query(FaceCluster).filter(
            FaceCluster.cluster_id == cluster_id
        ).first()
        
        if not cluster:
            raise HTTPException(status_code=404, detail="分组不存在")
        
        # 获取代表人脸（置信度最高的）
        representative_face = db.query(FaceDetection).filter(
            FaceDetection.face_id == cluster.representative_face_id
        ).first()
        
        if not representative_face:
            raise HTTPException(status_code=404, detail="未找到代表人脸")
        
        # 获取照片信息
        photo = db.query(Photo).filter(
            Photo.id == representative_face.photo_id
        ).first()
        
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 生成肖像照（裁剪人脸区域）
        portrait_url = await generate_portrait_image(
            photo.original_path,
            representative_face.face_rectangle
        )
        
        return {
            "success": True,
            "cluster_id": cluster_id,
            "portrait_url": portrait_url,
            "photo_id": photo.id,
            "face_confidence": representative_face.confidence
        }
        
    except Exception as e:
        logger.error(f"获取肖像照失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clusters/{cluster_id}/representative-face")
async def get_cluster_representative_face(
    cluster_id: str,
    db: Session = Depends(get_db)
):
    """
    获取聚类分组的代表人脸信息（用于前端显示）
    :param cluster_id: 聚类ID
    :param db: 数据库会话
    :return: 代表人脸信息
    """
    try:
        # 获取聚类信息
        cluster = db.query(FaceCluster).filter(
            FaceCluster.cluster_id == cluster_id
        ).first()
        
        if not cluster:
            raise HTTPException(status_code=404, detail="分组不存在")
        
        # 获取代表人脸
        representative_face = db.query(FaceDetection).filter(
            FaceDetection.face_id == cluster.representative_face_id
        ).first()
        
        if not representative_face:
            raise HTTPException(status_code=404, detail="未找到代表人脸")
        
        # 获取照片信息
        photo = db.query(Photo).filter(
            Photo.id == representative_face.photo_id
        ).first()
        
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        return {
            "success": True,
            "cluster_id": cluster_id,
            "representative_face": {
                "face_id": representative_face.face_id,
                "photo_id": photo.id,
                "photo_path": photo.original_path,
                "face_rectangle": representative_face.face_rectangle,
                "confidence": representative_face.confidence,
                "age_estimate": representative_face.age_estimate,
                "gender_estimate": representative_face.gender_estimate
            }
        }
        
    except Exception as e:
        logger.error(f"获取代表人脸失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clusters/{cluster_id}/photos")
async def get_cluster_photos(
    cluster_id: str,
    limit: int = 20,
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
        # 获取聚类成员
        members = db.query(FaceClusterMember, FaceDetection).join(
            FaceDetection, FaceClusterMember.face_id == FaceDetection.face_id
        ).filter(FaceClusterMember.cluster_id == cluster_id).offset(offset).limit(limit).all()
        
        result = []
        for member, face in members:
            # 获取照片信息
            photo = db.query(Photo).filter(Photo.id == face.photo_id).first()
            
            if photo:
                photo_info = {
                    "photo_id": photo.id,
                    "original_path": photo.original_path,
                    "face_id": face.face_id,
                    "face_rectangle": face.face_rectangle,
                    "confidence": face.confidence,
                    "similarity_score": member.similarity_score,
                    "created_at": photo.created_at.isoformat() if photo.created_at else None
                }
                result.append(photo_info)
        
        return {
            "success": True,
            "cluster_id": cluster_id,
            "photos": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"获取聚类照片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_portrait_image(photo_path: str, face_bbox: List[int]) -> str:
    """
    生成肖像照
    :param photo_path: 照片路径
    :param face_bbox: 人脸位置 [x, y, w, h]
    :return: 肖像照URL
    """
    try:
        # 构建完整路径
        storage_base = Path(settings.storage.base_path)
        full_path = storage_base / photo_path
        
        if not full_path.exists():
            raise ValueError(f"照片文件不存在: {full_path}")
        
        # 读取原图
        image = cv2.imread(str(full_path))
        if image is None:
            raise ValueError(f"无法读取图片: {full_path}")
        
        # 提取人脸区域
        x, y, w, h = face_bbox
        face_crop = image[y:y+h, x:x+w]
        
        # 调整大小到标准尺寸（200x200）
        face_resized = cv2.resize(face_crop, (200, 200))
        
        # 创建肖像照目录
        portrait_dir = storage_base / "portraits"
        portrait_dir.mkdir(exist_ok=True)
        
        # 保存肖像照
        portrait_filename = f"portrait_{int(time.time())}.jpg"
        portrait_path = portrait_dir / portrait_filename
        
        cv2.imwrite(str(portrait_path), face_resized)
        
        return f"/api/portraits/{portrait_filename}"
        
    except Exception as e:
        logger.error(f"生成肖像照失败: {e}")
        raise Exception(f"生成肖像照失败: {str(e)}")

@router.post("/cache/cleanup")
async def cleanup_face_cache(
    max_age_days: int = 30,
    db: Session = Depends(get_db)
):
    """
    清理过期的人脸裁剪缓存
    :param max_age_days: 最大保留天数
    :param db: 数据库会话
    :return: 清理结果
    """
    try:
        cleaned_count = face_crop_service.cleanup_old_cache(max_age_days)
        
        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"清理了 {cleaned_count} 个过期缓存文件"
        }
        
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear")
async def clear_face_cache(
    db: Session = Depends(get_db)
):
    """
    清空所有人脸裁剪缓存
    :param db: 数据库会话
    :return: 清理结果
    """
    try:
        success = face_crop_service.clear_cache()
        
        return {
            "success": success,
            "message": "缓存已清空" if success else "缓存清空失败"
        }
        
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/persons")
async def get_all_persons(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取所有已标记的人物
    :param limit: 限制数量
    :param offset: 偏移量
    :param db: 数据库会话
    :return: 人物列表
    """
    try:
        persons = db.query(Person).offset(offset).limit(limit).all()
        
        result = []
        for person in persons:
            # 获取该人物的聚类数量
            cluster_count = db.query(func.count(FaceCluster.id)).filter(
                FaceCluster.person_id == person.person_id
            ).scalar() or 0
            
            # 获取该人物的总人脸数
            face_count = db.query(func.count(FaceClusterMember.id)).join(
                FaceCluster, FaceClusterMember.cluster_id == FaceCluster.cluster_id
            ).filter(FaceCluster.person_id == person.person_id).scalar() or 0
            
            person_info = {
                "person_id": person.person_id,
                "person_name": person.person_name,
                "display_name": person.display_name,
                "cluster_count": cluster_count,
                "face_count": face_count,
                "created_at": person.created_at.isoformat() if person.created_at else None,
                "updated_at": person.updated_at.isoformat() if person.updated_at else None
            }
            result.append(person_info)
        
        return {
            "success": True,
            "persons": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"获取人物列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/persons/{person_id}")
async def update_person(
    person_id: str,
    request: Dict[str, str],
    db: Session = Depends(get_db)
):
    """
    更新人物信息
    :param person_id: 人物ID
    :param request: 请求数据
    :param db: 数据库会话
    :return: 更新结果
    """
    try:
        person = db.query(Person).filter(
            Person.person_id == person_id
        ).first()
        
        if not person:
            raise HTTPException(status_code=404, detail="人物不存在")
        
        # 更新人物信息
        if "person_name" in request:
            person.person_name = request["person_name"].strip()
        if "display_name" in request:
            person.display_name = request["display_name"].strip()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"人物 {person_id} 信息已更新"
        }
        
    except Exception as e:
        logger.error(f"更新人物信息失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/persons/{person_id}")
async def delete_person(
    person_id: str,
    db: Session = Depends(get_db)
):
    """
    删除人物（取消标记）
    :param person_id: 人物ID
    :param db: 数据库会话
    :return: 删除结果
    """
    try:
        person = db.query(Person).filter(
            Person.person_id == person_id
        ).first()
        
        if not person:
            raise HTTPException(status_code=404, detail="人物不存在")
        
        # 取消相关聚类的标记
        clusters = db.query(FaceCluster).filter(
            FaceCluster.person_id == person_id
        ).all()
        
        for cluster in clusters:
            cluster.person_name = None
            cluster.person_id = None
            cluster.is_labeled = False
        
        # 删除人物记录
        db.delete(person)
        db.commit()
        
        return {
            "success": True,
            "message": f"人物 {person_id} 已删除，相关聚类已取消标记"
        }
        
    except Exception as e:
        logger.error(f"删除人物失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_person_statistics(db: Session = Depends(get_db)):
    """
    获取人物统计信息
    :param db: 数据库会话
    :return: 统计信息
    """
    try:
        total_faces = db.query(func.count(FaceDetection.id)).scalar() or 0
        total_clusters = db.query(func.count(FaceCluster.id)).scalar() or 0
        labeled_clusters = db.query(func.count(FaceCluster.id)).filter(
            FaceCluster.is_labeled == True
        ).scalar() or 0
        
        # 获取涉及的照片数量
        photos_with_faces = db.query(func.count(func.distinct(FaceDetection.photo_id))).scalar() or 0
        
        # 获取已标记的人物数量
        total_persons = db.query(func.count(Person.id)).scalar() or 0
        
        return {
            "success": True,
            "statistics": {
                "total_faces": total_faces,
                "total_clusters": total_clusters,
                "labeled_clusters": labeled_clusters,
                "unlabeled_clusters": total_clusters - labeled_clusters,
                "photos_with_faces": photos_with_faces,
                "total_persons": total_persons
            }
        }
        
    except Exception as e:
        logger.error(f"获取人物统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
