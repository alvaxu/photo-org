"""
家庭版智能照片系统 - 智能分析API
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.services.analysis_service import AnalysisService
from app.models.photo import Photo

logger = get_logger(__name__)

router = APIRouter()


# 请求/响应模型
class AnalysisRequest(BaseModel):
    """分析请求"""
    photo_ids: List[int] = Field(..., description="要分析的照片ID列表")
    analysis_types: List[str] = Field(["content", "quality", "duplicate"], description="分析类型")


class AnalysisResponse(BaseModel):
    """分析响应"""
    photo_id: int = Field(..., description="照片ID")
    status: str = Field(..., description="分析状态")
    content_analysis: Optional[Dict[str, Any]] = Field(None, description="内容分析结果")
    quality_analysis: Optional[Dict[str, Any]] = Field(None, description="质量分析结果")
    perceptual_hash: Optional[str] = Field(None, description="感知哈希")
    analyzed_at: str = Field(..., description="分析时间")


class BatchAnalysisResponse(BaseModel):
    """批量分析响应"""
    total_photos: int = Field(..., description="总照片数")
    successful_analyses: int = Field(..., description="成功分析数")
    failed_analyses: int = Field(..., description="失败分析数")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="分析结果列表")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")
    completed_at: str = Field(..., description="完成时间")


class CaptionRequest(BaseModel):
    """标题生成请求"""
    photo_id: int = Field(..., description="照片ID")
    style: str = Field("natural", description="生成风格", pattern="^(natural|creative|poetic)$")


class CaptionResponse(BaseModel):
    """标题生成响应"""
    photo_id: int = Field(..., description="照片ID")
    caption: str = Field(..., description="生成的标题")
    style: str = Field(..., description="生成风格")


class DuplicateDetectionResponse(BaseModel):
    """重复检测响应"""
    target_photo_id: int = Field(..., description="目标照片ID")
    target_filename: str = Field(..., description="目标照片文件名")
    duplicate_count: int = Field(..., description="重复照片数量")
    duplicates: List[Dict[str, Any]] = Field(default_factory=list, description="重复照片列表")
    similarity_threshold: int = Field(..., description="相似度阈值")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_photo(
    photo_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    分析单张照片

    - **photo_id**: 要分析的照片ID
    """
    try:
        # 验证照片存在
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")

        # 创建分析服务
        analysis_service = AnalysisService()

        # 添加后台分析任务
        background_tasks.add_task(perform_analysis, photo_id)

        return AnalysisResponse(
            photo_id=photo_id,
            status="analyzing",
            analyzed_at=datetime.now().isoformat(),
            content_analysis=None,
            quality_analysis=None,
            perceptual_hash=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动照片分析失败 {photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动分析失败: {str(e)}")


@router.post("/batch-analyze", response_model=BatchAnalysisResponse)
async def batch_analyze_photos(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量分析照片

    - **photo_ids**: 要分析的照片ID列表
    - **analysis_types**: 分析类型列表
    """
    try:
        # 验证照片存在并过滤状态
        existing_photos = db.query(Photo).filter(Photo.id.in_(request.photo_ids)).all()
        existing_ids = {photo.id for photo in existing_photos}

        if len(existing_ids) != len(request.photo_ids):
            missing_ids = set(request.photo_ids) - existing_ids
            raise HTTPException(status_code=404, detail=f"照片不存在: {list(missing_ids)}")

        # 只处理imported和error状态的照片
        photos_to_process = [photo for photo in existing_photos if photo.status in ['imported', 'error']]
        
        logger.info(f"批量分析请求: 总照片数={len(existing_photos)}, 需要处理的照片数={len(photos_to_process)}")
        for photo in existing_photos:
            logger.info(f"照片ID={photo.id}, 状态={photo.status}")
        
        if not photos_to_process:
            logger.info("没有需要处理的照片，返回空结果")
            return BatchAnalysisResponse(
                total_photos=0,
                successful_analyses=0,
                failed_analyses=0,
                results=[],
                errors=[],
                completed_at=datetime.now().isoformat(),
                message="没有需要处理的照片，所有照片都已完成分析"
            )

        # 创建分析服务
        analysis_service = AnalysisService()

        # 添加后台批量分析任务
        photo_ids_to_process = [photo.id for photo in photos_to_process]
        background_tasks.add_task(perform_batch_analysis, photo_ids_to_process)

        return BatchAnalysisResponse(
            total_photos=len(photo_ids_to_process),
            successful_analyses=0,
            failed_analyses=0,
            results=[],
            errors=[],
            completed_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动批量分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动批量分析失败: {str(e)}")


@router.get("/status/{photo_id}")
async def get_analysis_status(photo_id: int, db: Session = Depends(get_db)):
    """
    获取照片分析状态

    - **photo_id**: 照片ID
    """
    try:
        # 验证照片存在
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")

        analysis_service = AnalysisService()
        status = analysis_service.get_analysis_status(photo_id, db)

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析状态失败 {photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分析状态失败: {str(e)}")


@router.get("/results/{photo_id}")
async def get_analysis_results(photo_id: int, db: Session = Depends(get_db)):
    """
    获取照片分析结果

    - **photo_id**: 照片ID
    """
    try:
        # 验证照片存在
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")

        analysis_service = AnalysisService()
        results = analysis_service.get_analysis_results(photo_id, db)

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析结果失败 {photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分析结果失败: {str(e)}")


@router.post("/caption", response_model=CaptionResponse)
async def generate_caption(request: CaptionRequest):
    """
    为照片生成标题

    - **photo_id**: 照片ID
    - **style**: 生成风格 (natural/creative/poetic)
    """
    try:
        analysis_service = AnalysisService()
        caption = await analysis_service.generate_photo_caption(request.photo_id, request.style)

        return CaptionResponse(
            photo_id=request.photo_id,
            caption=caption,
            style=request.style
        )

    except Exception as e:
        logger.error(f"生成照片标题失败 {request.photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成标题失败: {str(e)}")


@router.get("/duplicates/{photo_id}", response_model=DuplicateDetectionResponse)
async def detect_duplicates(photo_id: int, db: Session = Depends(get_db)):
    """
    检测照片重复项

    - **photo_id**: 要检测的照片ID
    """
    try:
        # 验证照片存在
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")

        analysis_service = AnalysisService()
        result = analysis_service.detect_duplicates_for_photo(photo_id, db)

        return DuplicateDetectionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重复检测失败 {photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重复检测失败: {str(e)}")


@router.get("/queue/status")
async def get_analysis_queue_status(initial_total: int = None, db: Session = Depends(get_db)):
    """
    获取分析队列状态
    """
    try:
        # 统计各种状态的照片数量
        all_photos = db.query(Photo).count()
        imported_photos = db.query(Photo).filter(Photo.status == 'imported').count()
        analyzing_photos = db.query(Photo).filter(Photo.status == 'analyzing').count()
        completed_photos = db.query(Photo).filter(Photo.status == 'completed').count()
        error_photos = db.query(Photo).filter(Photo.status == 'error').count()
        
        # 计算当前批次需要处理的照片数（imported + error状态的照片）
        current_pending_photos = imported_photos + error_photos
        
        # 使用传入的初始总数作为分母，如果没有传入则使用当前总数
        if initial_total is not None and initial_total > 0:
            total_batch_photos = initial_total
            # 分子：初始总数 - 当前剩余的待处理照片数
            batch_completed_photos = total_batch_photos - current_pending_photos
        else:
            # 如果没有传入初始总数，使用当前所有照片数（兼容旧版本）
            current_processing_or_completed = analyzing_photos + completed_photos
            total_batch_photos = current_pending_photos + current_processing_or_completed
            batch_completed_photos = current_processing_or_completed

        if total_batch_photos > 0:
            progress_percentage = (batch_completed_photos / total_batch_photos * 100)
        else:
            progress_percentage = 100  # 如果没有需要处理的照片，显示100%
        
        # 计算处理状态
        processing_photos = imported_photos + analyzing_photos + error_photos
        is_processing = analyzing_photos > 0
        is_complete = processing_photos == 0 and current_pending_photos > 0
        
        return {
            "all_photos": all_photos,  # 所有照片总数
            "batch_total_photos": total_batch_photos,  # 当前批次总照片数
            "batch_completed_photos": batch_completed_photos,  # 当前批次已完成照片数
            "batch_pending_photos": current_pending_photos,  # 当前批次待处理照片数（imported + error）
            "imported_photos": imported_photos,
            "analyzing_photos": analyzing_photos,
            "completed_photos": completed_photos,
            "error_photos": error_photos,
            "processing_photos": processing_photos,
            "progress_percentage": round(progress_percentage, 2),
            "is_processing": is_processing,
            "is_complete": is_complete,
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取队列状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取队列状态失败: {str(e)}")


# 后台任务函数
async def perform_analysis(photo_id: int):
    """
    执行照片分析任务

    Args:
        photo_id: 照片ID
    """
    try:
        logger.info(f"开始后台分析照片: {photo_id}")
        analysis_service = AnalysisService()
        result = await analysis_service.analyze_photo(photo_id)
        logger.info(f"后台分析照片完成: {photo_id}")

    except Exception as e:
        logger.error(f"后台分析照片失败 {photo_id}: {str(e)}")


async def perform_batch_analysis(photo_ids: List[int]):
    """
    执行批量分析任务

    Args:
        photo_ids: 照片ID列表
    """
    try:
        logger.info(f"=== 开始后台批量分析照片: {len(photo_ids)} 张 ===")
        logger.info(f"照片ID列表: {photo_ids}")
        
        # 验证输入参数
        if not photo_ids:
            logger.warning("照片ID列表为空，跳过批量分析")
            return
            
        analysis_service = AnalysisService()
        logger.info("AnalysisService 创建成功")
        
        # 创建新的数据库会话用于后台任务
        logger.info("开始创建数据库会话...")
        try:
            db = next(get_db())
            logger.info("数据库会话创建成功")
        except Exception as e:
            logger.error(f"创建数据库会话失败: {str(e)}")
            import traceback
            logger.error(f"数据库会话创建详细错误: {traceback.format_exc()}")
            raise
            
        try:
            logger.info("开始调用 batch_analyze_photos...")
            result = await analysis_service.batch_analyze_photos(photo_ids, db)
            logger.info(f"=== 后台批量分析完成: {result['successful_analyses']}/{result['total_photos']} ===")
            logger.info(f"成功分析的照片: {[r['photo_id'] for r in result.get('results', [])]}")
            if result.get('errors'):
                logger.error(f"分析失败的照片: {[e['photo_id'] for e in result['errors']]}")
        except Exception as e:
            logger.error(f"batch_analyze_photos 调用失败: {str(e)}")
            import traceback
            logger.error(f"batch_analyze_photos 详细错误: {traceback.format_exc()}")
            raise
        finally:
            try:
                db.close()
                logger.info("数据库会话已关闭")
            except Exception as e:
                logger.error(f"关闭数据库会话失败: {str(e)}")

    except Exception as e:
        logger.error(f"后台批量分析失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")


# 导入必要的模块
from datetime import datetime
