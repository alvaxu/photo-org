"""
家庭版智能照片系统 - 智能分析服务
"""
import os
import asyncio
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.core.config import settings
from app.db.session import get_db
from app.models.photo import Photo, PhotoAnalysis, PhotoQuality
from app.services.dashscope_service import DashScopeService
from app.services.photo_quality_service import PhotoQualityService
from app.services.duplicate_detection_service import DuplicateDetectionService


class AnalysisService:
    """
    智能分析服务类
    整合各种分析功能，提供统一的分析接口
    """

    def __init__(self):
        """初始化分析服务"""
        self.logger = get_logger(__name__)
        self.dashscope_service = DashScopeService()
        self.quality_service = PhotoQualityService()
        self.duplicate_service = DuplicateDetectionService()

        # 线程池用于并发处理
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def analyze_photo(self, photo_id: int, analysis_types: List[str] = None, db: Session = None) -> Dict[str, Any]:
        """
        分析单张照片

        Args:
            photo_id: 照片ID
            analysis_types: 分析类型列表 ['content', 'quality', 'duplicate']，如果为None则执行所有分析
            db: 数据库会话，如果为None则创建新的

        Returns:
            分析结果字典
        """
        # 标记是否需要关闭数据库会话
        should_close_db = False
        
        try:
            # 如果没有传入数据库会话，创建一个新的
            if db is None:
                db = next(get_db())
                should_close_db = True
                
            photo = db.query(Photo).filter(Photo.id == photo_id).first()

            if not photo:
                raise Exception("照片不存在")

            if not photo.original_path:
                raise Exception("照片路径为空")
            
            # 构建完整的文件路径
            storage_base = Path(settings.storage.base_path)
            full_path = storage_base / photo.original_path
            
            if not full_path.exists():
                raise Exception(f"照片文件不存在: {full_path}")

            self.logger.info(f"开始分析照片 {photo_id}: {photo.filename}, 分析类型: {analysis_types}")

            # 根据分析类型有条件地执行分析
            tasks = []
            task_indices = {}  # 记录任务在results数组中的索引

            if analysis_types is None or 'content' in analysis_types:
                tasks.append(self._analyze_content_async(str(full_path)))
                task_indices['content'] = len(tasks) - 1

            if analysis_types is None or 'quality' in analysis_types:
                tasks.append(self._analyze_quality_async(str(full_path)))
                task_indices['quality'] = len(tasks) - 1

            # 注意：duplicate分析已被移除，因为感知哈希在导入时已计算

            if not tasks:
                self.logger.warning(f"没有有效的分析类型: {analysis_types}")
                return {"photo_id": photo_id, "message": "没有有效的分析类型"}

            # 等待所有分析完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 根据任务索引处理结果
            content_result = None
            quality_result = None

            if 'content' in task_indices:
                content_idx = task_indices['content']
                content_result = results[content_idx] if not isinstance(results[content_idx], Exception) else None

            if 'quality' in task_indices:
                quality_idx = task_indices['quality']
                quality_result = results[quality_idx] if not isinstance(results[quality_idx], Exception) else None

            hash_result = None  # 感知哈希已在导入时计算，不再重复计算

            # 保存分析结果到数据库
            analysis_result = self._save_analysis_results(
                photo_id, content_result, quality_result, hash_result, db
            )

            self.logger.info(f"照片 {photo_id} 分析完成")
            return analysis_result

        except Exception as e:
            self.logger.error(f"照片分析失败 {photo_id}: {str(e)}")
            raise Exception(f"照片分析失败: {str(e)}")
        finally:
            # 如果创建了新的数据库会话，需要关闭它
            if should_close_db and db is not None:
                db.close()

    async def _analyze_content_async(self, image_path: str) -> Dict[str, Any]:
        """
        异步分析照片内容

        Args:
            image_path: 照片文件路径

        Returns:
            内容分析结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.dashscope_service.analyze_photo_content,
            image_path
        )

    async def _analyze_quality_async(self, image_path: str) -> Dict[str, Any]:
        """
        异步分析照片质量

        Args:
            image_path: 照片文件路径

        Returns:
            质量分析结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.quality_service.assess_quality,
            image_path
        )


    def _save_analysis_results(self, photo_id: int, content_result: Optional[Dict],
                            quality_result: Optional[Dict], hash_result: Optional[str],
                            db) -> Dict[str, Any]:
        """
        保存分析结果到数据库

        Args:
            photo_id: 照片ID
            content_result: 内容分析结果
            quality_result: 质量分析结果
            hash_result: 哈希结果
            db: 数据库会话

        Returns:
            保存的分析结果
        """
        try:
            # 保存内容分析结果
            if content_result:
                analysis_record = PhotoAnalysis(
                    photo_id=photo_id,
                    analysis_type="content",
                    analysis_result=content_result,
                    confidence_score=content_result.get("confidence", 0.0)
                )
                db.add(analysis_record)

            # 保存质量分析结果
            if quality_result:
                quality_record = PhotoQuality(
                    photo_id=photo_id,
                    quality_score=quality_result.get("quality_score"),
                    sharpness_score=quality_result.get("sharpness_score"),
                    brightness_score=quality_result.get("brightness_score"),
                    contrast_score=quality_result.get("contrast_score"),
                    color_score=quality_result.get("color_score"),
                    composition_score=quality_result.get("composition_score"),
                    quality_level=quality_result.get("quality_level"),
                    technical_issues=quality_result.get("technical_issues", [])
                )
                db.add(quality_record)

            # 更新照片状态（感知哈希已在导入时保存）
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if photo:
                # 根据分析结果设置精确的状态
                if quality_result and content_result:
                    photo.status = 'completed'  # 完整分析完成（质量+内容）
                elif quality_result:
                    photo.status = 'quality_completed'  # 仅质量分析完成
                elif content_result:
                    photo.status = 'content_completed'  # 仅内容分析完成
                # 如果都没有结果，保持原有状态（理论上不会发生）

                photo.updated_at = datetime.now()

            # 先提交分析结果到数据库
            db.commit()

            # 根据分析类型调用相应的标签和分类生成服务
            try:
                from app.services.classification_service import ClassificationService
                classification_service = ClassificationService()

                # 如果有质量分析结果，生成基础标签和设备分类
                if quality_result:
                    # 清理现有的基础标签（避免标签累积）- 使用子查询避免join+delete问题
                    # 注意：不再清理'device'标签，因为相机品牌和型号已存储在photo表中
                    from app.models.photo import PhotoTag, Tag
                    tag_ids_to_delete = db.query(PhotoTag.id).join(Tag).filter(
                        PhotoTag.photo_id == photo_id,
                        PhotoTag.source == 'auto',
                        Tag.category.in_(['time', 'lens', 'aperture', 'focal_length'])
                    ).subquery()
                    db.query(PhotoTag).filter(PhotoTag.id.in_(tag_ids_to_delete)).delete(synchronize_session=False)

                    basic_tags = classification_service.generate_basic_tags(photo, quality_result, db)
                    basic_classifications = classification_service.generate_basic_classifications(photo)

                    # 保存基础标签
                    if basic_tags:
                        saved_basic_tags = classification_service._save_auto_tags(photo_id, basic_tags, db)

                    # 保存基础分类
                    if basic_classifications:
                        saved_basic_categories = classification_service._save_classifications(photo_id, basic_classifications, db)

                # 如果有内容分析结果，生成AI标签和内容分类
                if content_result:
                    # 清理现有的AI标签（避免标签累积）- 使用子查询避免join+delete问题
                    from app.models.photo import PhotoTag, Tag
                    tag_ids_to_delete = db.query(PhotoTag.id).join(Tag).filter(
                        PhotoTag.photo_id == photo_id,
                        PhotoTag.source == 'auto',
                        Tag.category.in_(['scene', 'activity', 'emotion', 'object'])
                    ).subquery()
                    db.query(PhotoTag).filter(PhotoTag.id.in_(tag_ids_to_delete)).delete(synchronize_session=False)

                    # 清理现有的AI分类（避免分类累积）
                    from app.models.photo import PhotoCategory
                    db.query(PhotoCategory).filter(PhotoCategory.photo_id == photo_id).delete()

                    ai_tags = classification_service.generate_ai_tags(content_result)
                    ai_classifications = classification_service.generate_ai_classifications(photo, content_result)

                    # 保存AI标签
                    if ai_tags:
                        saved_ai_tags = classification_service._save_auto_tags(photo_id, ai_tags, db)

                    # 保存AI分类
                    if ai_classifications:
                        saved_ai_categories = classification_service._save_classifications(photo_id, ai_classifications, db)

            except Exception as e:
                self.logger.error(f"照片 {photo_id}: 标签和分类生成失败: {str(e)}")
                import traceback
                self.logger.error(f"照片 {photo_id}: 详细错误: {traceback.format_exc()}")
                raise

            # 提交所有标签和分类的数据库操作
            db.commit()

            # 返回综合结果（移除感知哈希，因为已在导入时计算）
            return {
                "photo_id": photo_id,
                "content_analysis": content_result,
                "quality_analysis": quality_result,
                "perceptual_hash_calculated_at_import": True,  # 标记哈希在导入时已计算
                "analyzed_at": datetime.now().isoformat()
            }

        except Exception as e:
            db.rollback()
            self.logger.error(f"保存分析结果失败 {photo_id}: {str(e)}")
            raise Exception(f"保存分析结果失败: {str(e)}")


    async def batch_analyze_photos(self, photo_ids: List[int], db: Session = None) -> Dict[str, Any]:
        """
        批量分析照片

        Args:
            photo_ids: 照片ID列表
            db: 数据库会话

        Returns:
            批量分析结果
        """
        try:
            self.logger.info(f"开始批量分析 {len(photo_ids)} 张照片")
            
            # 验证输入参数
            if not photo_ids:
                self.logger.warning("照片ID列表为空")
                return {
                    "total_photos": 0,
                    "successful_analyses": 0,
                    "failed_analyses": 0,
                    "results": [],
                    "errors": [],
                    "completed_at": datetime.now().isoformat()
                }

            results = {
                "total_photos": len(photo_ids),
                "successful_analyses": 0,
                "failed_analyses": 0,
                "results": [],
                "errors": []
            }

            # 限制并发数量，避免资源耗尽
            semaphore = asyncio.Semaphore(2)
            # 设置并发限制

            async def analyze_with_semaphore(photo_id: int):
                async with semaphore:
                    try:
                        result = await self.analyze_photo(photo_id, db)
                        return {"photo_id": photo_id, "status": "success", "result": result}
                    except Exception as e:
                        self.logger.error(f"照片 {photo_id} 分析失败: {str(e)}")
                        import traceback
                        self.logger.error(f"照片 {photo_id} 详细错误: {traceback.format_exc()}")
                        return {"photo_id": photo_id, "status": "error", "error": str(e)}

            # 并发执行分析任务
            # 开始并发执行分析任务
            try:
                tasks = [analyze_with_semaphore(photo_id) for photo_id in photo_ids]
                
                task_results = await asyncio.gather(*tasks)
                
            except Exception as e:
                self.logger.error(f"并发执行任务时出错: {str(e)}")
                import traceback
                self.logger.error(f"并发执行详细错误: {traceback.format_exc()}")
                raise

            # 处理结果
            # 处理任务结果
            for result in task_results:
                if result["status"] == "success":
                    results["successful_analyses"] += 1
                    results["results"].append(result)
                else:
                    results["failed_analyses"] += 1
                    results["errors"].append(result)
                    self.logger.error(f"照片 {result['photo_id']} 分析失败: {result['error']}")

            results["completed_at"] = datetime.now().isoformat()

            self.logger.info(f"批量分析完成: {results['successful_analyses']}/{results['total_photos']} 成功")
            return results

        except Exception as e:
            self.logger.error(f"批量分析失败: {str(e)}")
            import traceback
            self.logger.error(f"批量分析详细错误: {traceback.format_exc()}")
            raise Exception(f"批量分析失败: {str(e)}")

    def get_analysis_status(self, photo_id: int, db_session) -> Dict[str, Any]:
        """
        获取照片分析状态

        Args:
            photo_id: 照片ID
            db_session: 数据库会话

        Returns:
            分析状态信息
        """
        try:
            # 查询内容分析
            content_analysis = db_session.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id == photo_id,
                PhotoAnalysis.analysis_type == "content"
            ).first()

            # 查询质量分析
            quality_analysis = db_session.query(PhotoQuality).filter(
                PhotoQuality.photo_id == photo_id
            ).first()

            # 查询照片（感知哈希已在导入时设置）
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            has_perceptual_hash = photo.perceptual_hash is not None if photo else False

            status = {
                "photo_id": photo_id,
                "has_content_analysis": content_analysis is not None,
                "has_quality_analysis": quality_analysis is not None,
                "has_perceptual_hash": has_perceptual_hash,  # 仅用于状态检查，不再在分析时计算
                "analysis_complete": (
                    content_analysis is not None and
                    quality_analysis is not None
                    # 不再要求必须有感知哈希，因为导入时已计算
                )
            }

            if content_analysis:
                status["content_analysis_time"] = content_analysis.created_at.isoformat() if content_analysis.created_at else None
                status["content_confidence"] = content_analysis.confidence_score

            if quality_analysis:
                status["quality_analysis_time"] = quality_analysis.created_at.isoformat() if quality_analysis.created_at else None
                status["quality_score"] = quality_analysis.quality_score

            return status

        except Exception as e:
            self.logger.error(f"获取分析状态失败 {photo_id}: {str(e)}")
            raise Exception(f"获取分析状态失败: {str(e)}")

    def get_analysis_results(self, photo_id: int, db_session) -> Dict[str, Any]:
        """
        获取照片分析结果

        Args:
            photo_id: 照片ID
            db_session: 数据库会话

        Returns:
            完整的分析结果
        """
        try:
            # 查询内容分析
            content_analysis = db_session.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id == photo_id,
                PhotoAnalysis.analysis_type == "content"
            ).first()

            # 查询质量分析
            quality_analysis = db_session.query(PhotoQuality).filter(
                PhotoQuality.photo_id == photo_id
            ).first()

            # 查询照片基本信息
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()

            result = {
                "photo_id": photo_id,
                "filename": photo.filename if photo else None,
                "content_analysis": content_analysis.analysis_result if content_analysis else None,
                "quality_analysis": {
                    "quality_score": quality_analysis.quality_score if quality_analysis else None,
                    "sharpness_score": quality_analysis.sharpness_score if quality_analysis else None,
                    "brightness_score": quality_analysis.brightness_score if quality_analysis else None,
                    "contrast_score": quality_analysis.contrast_score if quality_analysis else None,
                    "color_score": quality_analysis.color_score if quality_analysis else None,
                    "composition_score": quality_analysis.composition_score if quality_analysis else None,
                    "quality_level": quality_analysis.quality_level if quality_analysis else None,
                    "technical_issues": quality_analysis.technical_issues if quality_analysis else None
                } if quality_analysis else None,
                "perceptual_hash": photo.perceptual_hash if photo else None,  # 保留以保持API兼容性
                "note": "感知哈希在导入时已计算，此处仅为显示"
            }

            return result

        except Exception as e:
            self.logger.error(f"获取分析结果失败 {photo_id}: {str(e)}")
            raise Exception(f"获取分析结果失败: {str(e)}")

    async def generate_photo_caption(self, photo_id: int, style: str = "natural") -> str:
        """
        为照片生成标题

        Args:
            photo_id: 照片ID
            style: 生成风格

        Returns:
            生成的标题
        """
        try:
            db = next(get_db())
            photo = db.query(Photo).filter(Photo.id == photo_id).first()

            if not photo or not photo.original_path:
                raise Exception("照片不存在或文件路径无效")

            # 构建完整的文件路径
            storage_base = Path(settings.storage.base_path)
            full_path = storage_base / photo.original_path
            
            if not full_path.exists():
                raise Exception(f"照片文件不存在: {full_path}")

            # 使用DashScope生成标题
            caption = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.dashscope_service.generate_photo_caption,
                str(full_path),
                style
            )

            return caption

        except Exception as e:
            self.logger.error(f"生成照片标题失败 {photo_id}: {str(e)}")
            raise Exception(f"生成标题失败: {str(e)}")

    def detect_duplicates_for_photo(self, photo_id: int, db_session) -> Dict[str, Any]:
        """
        检测指定照片的重复项

        Args:
            photo_id: 照片ID
            db_session: 数据库会话

        Returns:
            重复检测结果
        """
        return self.duplicate_service.detect_duplicates_for_photo(photo_id, db_session)
