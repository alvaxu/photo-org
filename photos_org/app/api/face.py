"""
人脸识别API接口

## 功能特点：
1. 人脸检测API
2. 人脸聚类API
3. 聚类管理API
4. 统计信息API

## 与其他版本的不同点：
- 集成到现有API结构
- 支持批量处理
- 提供聚类管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging

from app.db.session import get_db
from app.services.face_recognition_service import face_service
from app.services.face_recognition_task import start_face_recognition_task, get_face_recognition_task_status
from app.models.face import FaceDetection, FaceCluster, FaceClusterMember, Person
from app.models.photo import Photo
from sqlalchemy import func

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/face", tags=["face_recognition"])


@router.post("/cluster")
async def cluster_faces(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    执行人脸聚类分析
    :param background_tasks: 后台任务
    :param db: 数据库会话
    :return: 聚类结果
    """
    try:
        if not face_service.is_initialized:
            await face_service.initialize()
            
        if not face_service.is_initialized:
            raise HTTPException(status_code=500, detail="人脸识别服务未初始化")
        
        # 异步执行聚类
        background_tasks.add_task(face_service.cluster_faces, db)
        
        return {
            "success": True,
            "message": "已开始人脸聚类分析"
        }
        
    except Exception as e:
        logger.error(f"人脸聚类API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clusters")
async def get_clusters(
    limit: int = None,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取人脸聚类列表
    :param limit: 限制数量
    :param offset: 偏移量
    :param db: 数据库会话
    :return: 聚类列表
    """
    try:
        # 如果没有指定limit，使用配置中的max_clusters
        if limit is None:
            from app.core.config import settings
            limit = settings.face_recognition.max_clusters
        
        clusters = db.query(FaceCluster).offset(offset).limit(limit).all()
        
        result = []
        for cluster in clusters:
            # 获取代表人脸信息
            representative_face = db.query(FaceDetection).filter(
                FaceDetection.face_id == cluster.representative_face_id
            ).first()
            
            cluster_info = {
                "cluster_id": cluster.cluster_id,
                "person_name": cluster.person_name,
                "face_count": cluster.face_count,
                "confidence_score": cluster.confidence_score,
                "is_labeled": cluster.is_labeled,
                "cluster_quality": cluster.cluster_quality,
                "representative_face": {
                    "face_id": cluster.representative_face_id,
                    "photo_id": representative_face.photo_id if representative_face else None
                } if representative_face else None,
                "created_at": cluster.created_at.isoformat() if cluster.created_at else None
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

@router.get("/clusters/{cluster_id}/members")
async def get_cluster_members(
    cluster_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定聚类的成员
    :param cluster_id: 聚类ID
    :param db: 数据库会话
    :return: 聚类成员列表
    """
    try:
        cluster = db.query(FaceCluster).filter(
            FaceCluster.cluster_id == cluster_id
        ).first()
        
        if not cluster:
            raise HTTPException(status_code=404, detail="聚类不存在")
        
        # 获取聚类成员
        members = db.query(FaceClusterMember, FaceDetection).join(
            FaceDetection, FaceClusterMember.face_id == FaceDetection.face_id
        ).filter(FaceClusterMember.cluster_id == cluster_id).all()
        
        result = []
        for member, face in members:
            member_info = {
                "face_id": face.face_id,
                "photo_id": face.photo_id,
                "face_rectangle": face.face_rectangle,
                "confidence": face.confidence,
                "similarity_score": member.similarity_score,
                "age_estimate": face.age_estimate,
                "gender_estimate": face.gender_estimate
            }
            result.append(member_info)
        
        return {
            "success": True,
            "cluster_id": cluster_id,
            "members": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"获取聚类成员失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/clusters/{cluster_id}/label")
async def label_cluster(
    cluster_id: str,
    person_name: str,
    db: Session = Depends(get_db)
):
    """
    标记聚类（给聚类命名）
    :param cluster_id: 聚类ID
    :param person_name: 人物姓名
    :param db: 数据库会话
    :return: 标记结果
    """
    try:
        cluster = db.query(FaceCluster).filter(
            FaceCluster.cluster_id == cluster_id
        ).first()
        
        if not cluster:
            raise HTTPException(status_code=404, detail="聚类不存在")
        
        # 更新聚类标签
        cluster.person_name = person_name
        cluster.is_labeled = True
        
        # 创建或更新人物记录
        person = db.query(Person).filter(
            Person.person_name == person_name
        ).first()
        
        if not person:
            person = Person(
                person_id=f"person_{person_name}_{int(datetime.now().timestamp())}",
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

@router.get("/statistics")
async def get_face_statistics(db: Session = Depends(get_db)):
    """
    获取人脸识别统计信息
    :param db: 数据库会话
    :return: 统计信息
    """
    try:
        stats = await face_service.get_cluster_statistics(db)
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/photos/{photo_id}/faces")
async def get_photo_faces(
    photo_id: int,
    db: Session = Depends(get_db)
):
    """
    获取照片中的人脸信息
    :param photo_id: 照片ID
    :param db: 数据库会话
    :return: 人脸信息列表
    """
    try:
        faces = db.query(FaceDetection).filter(
            FaceDetection.photo_id == photo_id
        ).all()
        
        result = []
        for face in faces:
            face_info = {
                "face_id": face.face_id,
                "face_rectangle": face.face_rectangle,
                "confidence": face.confidence,
                "age_estimate": face.age_estimate,
                "gender_estimate": face.gender_estimate,
                "created_at": face.created_at.isoformat() if face.created_at else None
            }
            result.append(face_info)
        
        return {
            "success": True,
            "photo_id": photo_id,
            "faces": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"获取照片人脸信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending-photos-count")
async def get_pending_face_recognition_count(db: Session = Depends(get_db)):
    """
    获取需要人脸识别的照片数量统计
    """
    try:
        # 统计需要人脸识别的照片：在face_detections表中没有记录的照片
        # 包括没有检测到人脸的照片（confidence=0.0的记录）
        photos_with_faces = db.query(FaceDetection.photo_id).distinct().subquery()
        pending_count = db.query(Photo).filter(
            ~Photo.id.in_(db.query(photos_with_faces.c.photo_id))
        ).count()
        
        return {
            "success": True,
            "count": pending_count
        }
        
    except Exception as e:
        logger.error(f"获取待处理照片数量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending-photos")
async def get_pending_face_recognition_photos(db: Session = Depends(get_db)):
    """
    获取需要人脸识别的照片ID列表
    """
    try:
        # 获取需要人脸识别的照片：在face_detections表中没有记录的照片
        photos_with_faces = db.query(FaceDetection.photo_id).distinct().subquery()
        pending_photos = db.query(Photo).filter(
            ~Photo.id.in_(db.query(photos_with_faces.c.photo_id))
        ).all()
        
        photo_ids = [photo.id for photo in pending_photos]
        
        return {
            "success": True,
            "photo_ids": photo_ids,
            "count": len(photo_ids)
        }
        
    except Exception as e:
        logger.error(f"获取待处理照片列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-recognition")
async def start_face_recognition(
    request: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    开始人脸识别处理（支持分批处理）
    :param request: 请求数据，可包含photo_ids字段
    :param background_tasks: 后台任务
    :param db: 数据库会话
    :return: 任务信息
    """
    try:
        # 初始化人脸识别服务
        if not face_service.is_initialized:
            await face_service.initialize()
            
        if not face_service.is_initialized:
            return {
                "success": False,
                "task_id": None,
                "total_photos": 0,
                "message": "人脸识别服务初始化失败"
            }
        
        # 获取要处理的照片ID列表
        photo_ids = request.get("photo_ids", [])
        
        if not photo_ids:
            # 如果没有提供照片ID，获取所有需要人脸识别的照片
            photos_with_faces = db.query(FaceDetection.photo_id).distinct().subquery()
            photos_to_process = db.query(Photo).filter(
                ~Photo.id.in_(db.query(photos_with_faces.c.photo_id))
            ).all()
            photo_ids = [photo.id for photo in photos_to_process]
        
        if not photo_ids:
            return {
                "success": True,
                "task_id": None,
                "total_photos": 0,
                "message": "没有需要人脸识别的照片"
            }
        
        # 启动人脸识别任务
        task_result = await start_face_recognition_task(photo_ids)
        
        return {
            "success": True,
            "task_id": task_result["task_id"],
            "total_photos": task_result["total_photos"],
            "message": task_result["message"]
        }
        
    except Exception as e:
        logger.error(f"启动人脸识别失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-task-status/{task_id}")
async def test_face_recognition_task_status(task_id: str):
    """
    测试人脸识别任务状态（调试用）
    """
    try:
        from app.services.face_recognition_task import get_face_recognition_task_status
        
        status = get_face_recognition_task_status(task_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "raw_status": status,
            "wrapped_status": {
                "success": True,
                "task_id": task_id,
                "status": status
            }
        }
        
    except Exception as e:
        logger.error(f"测试任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task-status/{task_id}")
async def get_face_recognition_task_status_api(
    task_id: str
):
    """
    获取人脸识别任务状态（参考基础分析的get_analysis_task_status）
    :param task_id: 任务ID
    :return: 任务状态
    """
    try:
        status = get_face_recognition_task_status(task_id)
        
        # 🔥 修复：直接返回状态数据，与基础分析保持一致
        if status.get("status") == "not_found":
            return {
                "task_id": task_id,
                "status": "not_found",
                "message": "任务不存在或已过期"
            }
        
        # 直接返回状态数据，不包装
        return status
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
