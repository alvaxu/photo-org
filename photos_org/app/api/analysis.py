"""
家庭版智能照片系统 - 智能分析API
"""
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.services.analysis_service import AnalysisService
from app.models.photo import Photo, PhotoAnalysis

logger = get_logger(__name__)

router = APIRouter()

# 全局分析任务状态跟踪（类似导入模块的task_status）
analysis_task_status = {}

# 任务状态清理配置
TASK_STATUS_CLEANUP_HOURS = 1  # 任务完成后1小时清理状态


# 请求/响应模型
class AnalysisRequest(BaseModel):
    """分析请求"""
    photo_ids: List[int] = Field(..., description="要分析的照片ID列表")
    analysis_types: List[str] = Field(["content"], description="分析类型")
    force_reprocess: bool = Field(False, description="是否强制重新处理已分析的照片")


class AnalysisResponse(BaseModel):
    """分析响应"""
    photo_id: int = Field(..., description="照片ID")
    status: str = Field(..., description="分析状态")
    content_analysis: Optional[Dict[str, Any]] = Field(None, description="内容分析结果")
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

        # 根据force_reprocess参数决定处理哪些照片
        if request.force_reprocess:
            # 强制重新处理所有照片
            photos_to_process = existing_photos
            logger.info("启用强制重新处理模式，将处理所有选中的照片")
        else:
            # 只处理imported和error状态的照片
            photos_to_process = [photo for photo in existing_photos if photo.status in ['imported', 'error']]
            logger.info("使用默认模式，只处理未分析的照片")
        
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


@router.get("/pending-photos")
async def get_pending_photos(db: Session = Depends(get_db)):
    """
    获取所有待处理的照片ID列表

    返回状态为'imported'或'error'的所有照片ID，用于智能处理
    """
    try:
        # 获取所有状态为imported或error的照片ID
        pending_photos = db.query(Photo.id).filter(Photo.status.in_(['imported', 'error'])).all()

        photo_ids = [photo.id for photo in pending_photos]

        return {
            "photo_ids": photo_ids,
            "total_count": len(photo_ids),
            "message": f"找到 {len(photo_ids)} 张待处理的照片"
        }

    except Exception as e:
        logger.error(f"获取待处理照片列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取待处理照片列表失败: {str(e)}")


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
        quality_completed_photos = db.query(Photo).filter(Photo.status == 'quality_completed').count()
        content_completed_photos = db.query(Photo).filter(Photo.status == 'content_completed').count()
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
            "quality_completed_photos": quality_completed_photos,
            "content_completed_photos": content_completed_photos,
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


@router.get("/ai-pending-count")
async def get_ai_pending_count(db: Session = Depends(get_db)):
    """
    获取需要AI分析的照片数量统计
    AI分析：只包含内容分析，不包含质量评估
    """
    try:
        # 统计需要AI分析的照片：没有AI内容分析结果的照片
        pending_count = db.query(Photo).filter(
            ~db.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id == Photo.id,
                PhotoAnalysis.analysis_type == 'content'
            ).exists()
        ).count()

        return {
            "count": pending_count,
            "message": f"发现 {pending_count} 张照片需要AI分析"
        }
    except Exception as e:
        logger.error(f"获取AI分析统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取AI分析统计失败: {str(e)}")


@router.get("/ai-pending-photos")
async def get_ai_pending_photos(db: Session = Depends(get_db)):
    """
    获取需要AI分析的照片ID列表
    返回没有AI内容分析结果的照片ID
    """
    try:
        # 只查找没有content分析记录的照片
        no_analysis_photos = db.query(Photo.id).filter(
            ~db.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id == Photo.id,
                PhotoAnalysis.analysis_type == 'content'
            ).exists()
        ).all()
        
        photo_ids = [photo.id for photo in no_analysis_photos]
        
        logger.info(f"AI待处理照片统计: 未处理 {len(photo_ids)} 张")
        
        return {
            "photo_ids": photo_ids,
            "total_count": len(photo_ids),
            "message": f"找到 {len(photo_ids)} 张需要AI分析的照片"
        }
    except Exception as e:
        logger.error(f"获取AI分析照片列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取AI分析照片列表失败: {str(e)}")


@router.post("/photos/{photo_id}/analyze-ai")
async def analyze_photo_ai_sync(
    photo_id: int,
    db: Session = Depends(get_db)
):
    """
    同步分析单张照片的AI内容
    
    - **photo_id**: 要分析的照片ID
    """
    try:
        # 验证照片存在
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")

        # 获取分析服务
        analysis_service = AnalysisService()
        
        # 同步执行AI分析
        logger.info(f"开始同步AI分析照片: {photo_id}")
        result = await analysis_service.analyze_photo(
            photo_id=photo_id,
            analysis_types=['content'],
            db=db,
            original_status=photo.status
        )
        
        logger.info(f"照片 {photo_id} AI分析完成")
        
        return {
            "success": True,
            "photo_id": photo_id,
            "result": result,
            "message": "AI分析完成"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步AI分析失败 {photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI分析失败: {str(e)}")


@router.post("/start-analysis")
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    开始条件分析（支持基础分析和AI分析）
    根据analysis_types参数只执行指定的分析类型
    """
    try:
        logger.info(f"=== 开始条件分析 ===")
        logger.info(f"分析类型: {request.analysis_types}")
        logger.info(f"照片数量: {len(request.photo_ids)}")
        logger.info(f"强制重新处理: {request.force_reprocess}")

        # 验证分析类型（只支持AI内容分析）
        valid_types = ['content']
        invalid_types = [t for t in request.analysis_types if t not in valid_types]
        if invalid_types:
            raise HTTPException(status_code=400, detail=f"无效的分析类型: {invalid_types}，支持的类型: {valid_types}")

        # 获取分析服务
        analysis_service = AnalysisService()

        # 过滤需要分析的照片
        if request.force_reprocess:
            # 强制重新处理所有指定的照片
            photos_to_analyze = request.photo_ids
        else:
            # 只处理还没有对应分析结果的照片
            photos_to_analyze = []
            for photo_id in request.photo_ids:
                needs_analysis = False

                if 'content' in request.analysis_types:
                    # 检查是否有内容分析结果
                    has_content = db.query(PhotoAnalysis).filter(
                        PhotoAnalysis.photo_id == photo_id,
                        PhotoAnalysis.analysis_type == 'content'
                    ).first() is not None
                    if not has_content:
                        needs_analysis = True

                if needs_analysis:
                    photos_to_analyze.append(photo_id)

        if not photos_to_analyze:
            return {
                "task_id": None,
                "total_photos": 0,
                "message": "所有照片都已完成指定类型的分析"
            }

        logger.info(f"实际需要分析的照片: {len(photos_to_analyze)} 张")

        # 记录原始状态并设置为analyzing状态
        original_statuses = {}
        for photo_id in photos_to_analyze:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if photo:
                original_statuses[photo_id] = photo.status  # 记录原始状态
                photo.status = 'analyzing'  # 任何分析过程中都设为analyzing
                logger.info(f"照片 {photo_id} 状态从 {original_statuses[photo_id]} 设为 analyzing")
        
        db.commit()
        
        # 将原始状态传递给后台任务
        task_original_statuses = original_statuses

        # 生成任务ID
        import uuid
        task_id = str(uuid.uuid4())

        # 添加后台任务
        background_tasks.add_task(
            process_analysis_task,
            task_id=task_id,
            photo_ids=photos_to_analyze,
            analysis_types=request.analysis_types,
            original_statuses=task_original_statuses
        )

        return {
            "task_id": task_id,
            "total_photos": len(photos_to_analyze),
            "analysis_types": request.analysis_types,
            "message": f"已开始分析 {len(photos_to_analyze)} 张照片"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始条件分析失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"开始条件分析失败: {str(e)}")


@router.get("/task-status/{task_id}")
async def get_analysis_task_status(task_id: str, initial_total: int = None, db: Session = Depends(get_db)):
    """
    获取分析任务状态
    支持条件分析的状态查询

    - **task_id**: 任务ID
    - **initial_total**: 任务开始时的待处理照片总数（imported + error）
    """
    try:
        # 优先检查任务状态跟踪字典
        task_data = analysis_task_status.get(task_id)
        if task_data:
            # 任务存在于内存中，直接返回任务状态
            status = task_data["status"]
            total_photos = task_data["total_photos"]
            completed_photos = task_data["completed_photos"]
            failed_photos = task_data["failed_photos"]
            progress_percentage = task_data["progress_percentage"]
            processing_photos = total_photos - completed_photos - failed_photos

            return {
                "task_id": task_id,
                "status": status,
                "total_photos": total_photos,
                "completed_photos": completed_photos,
                "failed_photos": failed_photos,
                "progress_percentage": round(progress_percentage, 2),
                "processing_photos": processing_photos
            }

        # 任务不存在于内存中（可能已清理或从未启动），回退到数据库统计
        logger.warning(f"任务 {task_id} 状态不存在于内存中，回退到数据库统计")

        # 获取当前数据库中的统计信息
        imported_count = db.query(Photo).filter(Photo.status == 'imported').count()
        error_count = db.query(Photo).filter(Photo.status == 'error').count()
        analyzing_count = db.query(Photo).filter(Photo.status == 'analyzing').count()
        completed_count = db.query(Photo).filter(Photo.status == 'completed').count()

        # 当前待处理的照片总数（imported + error）
        current_pending_total = imported_count + error_count

        # 使用提供的 initial_total 作为分母（如果提供的话）
        display_total = initial_total if initial_total is not None else current_pending_total

        # 回退逻辑：基于数据库统计估算状态
        if analyzing_count == 0:
            # 没有正在分析的照片，认为任务已完成
            status = "completed"
            # 已完成的照片数基于数据库统计
            completed_photos = completed_count
            failed_photos = 0
        else:
            # 有照片正在分析，认为任务进行中
            status = "processing"
            # 已完成的照片数基于数据库统计
            completed_photos = completed_count
            failed_photos = 0

        progress_percentage = (completed_photos / display_total * 100) if display_total > 0 else 100

        return {
            "task_id": task_id,
            "status": status,
            "total_photos": display_total,
            "completed_photos": completed_photos,
            "failed_photos": failed_photos,
            "progress_percentage": round(progress_percentage, 2),
            "processing_photos": analyzing_count
        }

    except Exception as e:
        logger.error(f"获取分析状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分析状态失败: {str(e)}")


# 批量状态查询请求模型
class BatchStatusRequest(BaseModel):
    """批量分析任务状态查询请求"""
    task_ids: List[str] = Field(..., description="任务ID列表")
    initial_totals: Optional[Dict[str, int]] = Field(None, description="各任务的初始照片总数 {task_id: count}")


@router.post("/batch-status")
async def get_analysis_batch_status(request: BatchStatusRequest, db: Session = Depends(get_db)):
    """
    获取多个分析任务的聚合状态（类似导入的batch-status）

    使用任务状态字典查询，避免前端发起过多并发请求
    """
    try:
        logger.info(f"批量查询分析任务状态，任务数量: {len(request.task_ids)}")

        if not request.task_ids:
            raise HTTPException(status_code=400, detail="任务ID列表不能为空")

        batch_results = []
        total_completed_photos = 0
        total_analyzing_photos = 0
        total_failed_photos = 0
        completed_tasks = 0

        # 查询每个任务的状态 - 使用任务状态字典
        for task_id in request.task_ids:
            try:
                # 从任务状态字典获取任务状态
                task_data = analysis_task_status.get(task_id)

                if task_data:
                    # 任务存在，使用任务状态
                    status = task_data["status"]
                    total_photos = task_data["total_photos"]
                    completed_photos = task_data["completed_photos"]
                    failed_photos = task_data["failed_photos"]
                    progress_percentage = task_data["progress_percentage"]
                    processing_photos = total_photos - completed_photos - failed_photos
                else:
                    # 任务不存在（可能已清理或从未启动），标记为错误
                    logger.warning(f"任务 {task_id} 状态不存在")
                    status = "error"
                    total_photos = 0
                    completed_photos = 0
                    failed_photos = 0
                    progress_percentage = 0
                    processing_photos = 0

                task_result = {
                    "task_id": task_id,
                    "status": status,
                    "total_photos": total_photos,
                    "completed_photos": completed_photos,
                    "failed_photos": failed_photos,
                    "progress_percentage": round(progress_percentage, 2),
                    "processing_photos": processing_photos
                }

                batch_results.append(task_result)

                # 累积统计
                total_completed_photos += completed_photos
                total_analyzing_photos += processing_photos
                total_failed_photos += failed_photos

                if status == "completed":
                    completed_tasks += 1

            except Exception as e:
                logger.warning(f"查询任务 {task_id} 状态失败: {str(e)}")
                # 任务查询失败，记录为错误状态
                batch_results.append({
                    "task_id": task_id,
                    "status": "error",
                    "error": str(e),
                    "total_photos": 0,
                    "completed_photos": 0,
                    "failed_photos": 0,
                    "progress_percentage": 0,
                    "processing_photos": 0
                })

        # 计算总体状态
        total_tasks = len(request.task_ids)
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # 总体状态判断：所有任务都完成才算完成
        overall_status = "completed" if completed_tasks == total_tasks else "processing"

        result = {
            "overall_status": overall_status,
            "overall_progress_percentage": round(overall_progress, 2),
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "total_completed_photos": total_completed_photos,
            "total_analyzing_photos": total_analyzing_photos,
            "total_failed_photos": total_failed_photos,
            "task_details": batch_results
        }

        logger.info(f"分析批次聚合状态: {completed_tasks}/{total_tasks} 完成，总体进度: {overall_progress}%")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量查询分析任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量查询分析任务状态失败: {str(e)}")


async def process_analysis_task(task_id: str, photo_ids: List[int], analysis_types: List[str], original_statuses: Dict[int, str] = None):
    """
    处理分析任务（后台任务）- 使用asyncio并发处理
    支持两种模式：导航栏批次处理和选中照片单次处理
    """
    logger.info(f"=== 开始处理分析任务 {task_id} ===")
    logger.info(f"照片数量: {len(photo_ids)}, 分析类型: {analysis_types}")

    # 创建数据库会话
    db = next(get_db())

    # 使用传入的原始状态，如果没有则从数据库获取
    if original_statuses is None:
        original_statuses = {}
        for photo_id in photo_ids:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if photo:
                original_statuses[photo_id] = photo.status

    # 初始化任务状态
    analysis_task_status[task_id] = {
        "status": "processing",
        "total_photos": len(photo_ids),
        "completed_photos": 0,
        "failed_photos": 0,
        "progress_percentage": 0.0,
        "start_time": datetime.now().isoformat(),
        "analysis_types": analysis_types,
        "error_details": [],  # 新增：记录具体错误信息
        "original_statuses": original_statuses  # 新增：记录原始状态
    }

    try:
        analysis_service = AnalysisService()
        
        # 🔥 关键改进：使用现有配置的并发数
        from app.core.config import settings
        max_concurrent = settings.analysis.concurrent  # 使用现有的concurrent配置
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_single_photo_with_semaphore(photo_id: int):
            """使用信号量控制并发处理单张照片"""
            async with semaphore:
                try:
                    # logger.info(f"开始分析照片 {photo_id}")
                    original_status = original_statuses.get(photo_id, 'imported')
                    result = await analysis_service.analyze_photo(
                        photo_id, analysis_types, db, original_status
                    )
                    # logger.info(f"照片 {photo_id} 分析完成")
                    return {"photo_id": photo_id, "status": "success", "result": result}
                    
                except Exception as e:
                    logger.error(f"照片 {photo_id} 分析失败: {str(e)}")
                    
                    # 保存错误信息并恢复原始状态
                    error_info = {
                        "error": str(e),
                        "error_type": "analysis_error",
                        "failed_at": datetime.now().isoformat()
                    }
                    original_status = original_statuses.get(photo_id, 'imported')
                    analysis_service._save_error_result(
                        photo_id, error_info, db, original_status, 
                        analysis_types[0] if analysis_types else None
                    )
                    
                    return {"photo_id": photo_id, "status": "error", "error": str(e)}
        
        # 🔥 关键改进：并发执行所有分析任务
        logger.info(f"开始并发分析 {len(photo_ids)} 张照片，最大并发数: {max_concurrent}")
        tasks = [analyze_single_photo_with_semaphore(photo_id) for photo_id in photo_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果和更新状态
        successful_analyses = 0
        failed_analyses = 0
        
        for result in results:
            if isinstance(result, Exception):
                failed_analyses += 1
                logger.error(f"任务执行异常: {str(result)}")
                continue
                
            if result["status"] == "success":
                successful_analyses += 1
            else:
                failed_analyses += 1
                analysis_task_status[task_id]["error_details"].append({
                    "photo_id": result["photo_id"],
                    "error": result["error"],
                    "error_type": "analysis_error",
                    "timestamp": datetime.now().isoformat()
                })

        # 更新最终状态
        analysis_task_status[task_id].update({
            "status": "completed",
            "completed_photos": successful_analyses,
            "failed_photos": failed_analyses,
            "end_time": datetime.now().isoformat(),
            "progress_percentage": 100.0
        })

        logger.info(f"=== 分析任务 {task_id} 完成 ===")
        logger.info(f"成功: {successful_analyses}, 失败: {failed_analyses}")

        # 延迟清理任务状态，避免内存泄漏
        async def cleanup_task_status():
            await asyncio.sleep(TASK_STATUS_CLEANUP_HOURS * 3600)  # 延迟清理
            if task_id in analysis_task_status:
                del analysis_task_status[task_id]
                logger.info(f"清理已完成的任务状态: {task_id}")

        # 启动后台清理任务
        asyncio.create_task(cleanup_task_status())

    except Exception as e:
        logger.error(f"处理分析任务失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")

        # 标记任务失败
        analysis_task_status[task_id].update({
            "status": "failed",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })
    finally:
        try:
            db.close()
        except:
            pass



