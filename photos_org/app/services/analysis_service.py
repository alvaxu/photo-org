"""
家庭单机版智能照片整理系统 - 智能分析服务
"""
import os
import asyncio
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
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

    async def analyze_photo(self, photo_id: int) -> Dict[str, Any]:
        """
        分析单张照片

        Args:
            photo_id: 照片ID

        Returns:
            分析结果字典
        """
        try:
            db = next(get_db())
            photo = db.query(Photo).filter(Photo.id == photo_id).first()

            if not photo:
                raise Exception("照片不存在")

            if not photo.original_path or not Path(photo.original_path).exists():
                raise Exception("照片文件不存在")

            self.logger.info(f"开始分析照片: {photo.filename}")

            # 并发执行各项分析
            tasks = [
                self._analyze_content_async(photo.original_path),
                self._analyze_quality_async(photo.original_path),
                self._calculate_duplicate_hash_async(photo.original_path)
            ]

            # 等待所有分析完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            content_result = results[0] if not isinstance(results[0], Exception) else None
            quality_result = results[1] if not isinstance(results[1], Exception) else None
            hash_result = results[2] if not isinstance(results[2], Exception) else None

            # 保存分析结果到数据库
            analysis_result = self._save_analysis_results(
                photo_id, content_result, quality_result, hash_result, db
            )

            self.logger.info(f"照片分析完成: {photo.filename}")
            return analysis_result

        except Exception as e:
            self.logger.error(f"照片分析失败 {photo_id}: {str(e)}")
            raise Exception(f"照片分析失败: {str(e)}")

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

    async def _calculate_duplicate_hash_async(self, image_path: str) -> str:
        """
        异步计算重复检测哈希

        Args:
            image_path: 照片文件路径

        Returns:
            感知哈希值
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.duplicate_service.calculate_perceptual_hash,
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

            # 更新照片的哈希值和状态
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if photo:
                if hash_result:
                    photo.perceptual_hash = hash_result
                # 更新照片状态为已完成
                photo.status = 'completed'
                photo.updated_at = datetime.now()

            # 调用分类服务生成完整的标签和分类
            try:
                from app.services.classification_service import ClassificationService
                classification_service = ClassificationService()
                classification_result = classification_service.classify_photo(photo_id, db)
                self.logger.info(f"分类服务完成: {classification_result.get('message', '')}")
            except Exception as e:
                self.logger.error(f"分类服务失败: {str(e)}")

            db.commit()

            # 返回综合结果
            return {
                "photo_id": photo_id,
                "content_analysis": content_result,
                "quality_analysis": quality_result,
                "perceptual_hash": hash_result,
                "analyzed_at": datetime.now().isoformat()
            }

        except Exception as e:
            db.rollback()
            self.logger.error(f"保存分析结果失败 {photo_id}: {str(e)}")
            raise Exception(f"保存分析结果失败: {str(e)}")


    async def batch_analyze_photos(self, photo_ids: List[int]) -> Dict[str, Any]:
        """
        批量分析照片

        Args:
            photo_ids: 照片ID列表

        Returns:
            批量分析结果
        """
        try:
            self.logger.info(f"开始批量分析 {len(photo_ids)} 张照片")

            results = {
                "total_photos": len(photo_ids),
                "successful_analyses": 0,
                "failed_analyses": 0,
                "results": [],
                "errors": []
            }

            # 限制并发数量，避免资源耗尽
            semaphore = asyncio.Semaphore(2)

            async def analyze_with_semaphore(photo_id: int):
                async with semaphore:
                    try:
                        result = await self.analyze_photo(photo_id)
                        return {"photo_id": photo_id, "status": "success", "result": result}
                    except Exception as e:
                        self.logger.error(f"批量分析照片失败 {photo_id}: {str(e)}")
                        return {"photo_id": photo_id, "status": "error", "error": str(e)}

            # 并发执行分析任务
            tasks = [analyze_with_semaphore(photo_id) for photo_id in photo_ids]
            task_results = await asyncio.gather(*tasks)

            # 处理结果
            for result in task_results:
                if result["status"] == "success":
                    results["successful_analyses"] += 1
                    results["results"].append(result)
                else:
                    results["failed_analyses"] += 1
                    results["errors"].append(result)

            results["completed_at"] = datetime.now().isoformat()

            self.logger.info(f"批量分析完成: {results['successful_analyses']}/{results['total_photos']}")
            return results

        except Exception as e:
            self.logger.error(f"批量分析失败: {str(e)}")
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

            # 查询照片哈希
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            hash_value = photo.perceptual_hash if photo else None

            status = {
                "photo_id": photo_id,
                "has_content_analysis": content_analysis is not None,
                "has_quality_analysis": quality_analysis is not None,
                "has_perceptual_hash": hash_value is not None,
                "analysis_complete": (
                    content_analysis is not None and
                    quality_analysis is not None and
                    hash_value is not None
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
                "perceptual_hash": photo.perceptual_hash if photo else None
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

            # 使用DashScope生成标题
            caption = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.dashscope_service.generate_photo_caption,
                photo.original_path,
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
