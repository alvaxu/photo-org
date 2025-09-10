"""
家庭单机版智能照片整理系统 - 搜索服务
提供强大的搜索和筛选功能
"""
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from sqlalchemy import text, and_, or_, desc, asc, func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.photo import Photo, PhotoAnalysis, PhotoQuality, Category, Tag, PhotoTag, PhotoCategory


class SearchService:
    """
    搜索服务类
    提供照片搜索、筛选、排序等功能
    """

    def __init__(self):
        """初始化搜索服务"""
        self.logger = get_logger(__name__)

    def search_photos(
        self,
        db: Session,
        keyword: Optional[str] = None,
        camera_make: Optional[str] = None,
        camera_model: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        quality_min: Optional[float] = None,
        quality_level: Optional[str] = None,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        location_lat: Optional[float] = None,
        location_lng: Optional[float] = None,
        location_radius: Optional[float] = None,  # 公里
        sort_by: str = "taken_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        综合搜索照片

        Args:
            db: 数据库会话
            keyword: 关键词搜索
            camera_make: 相机品牌
            camera_model: 相机型号
            date_from: 开始日期
            date_to: 结束日期
            quality_min: 最低质量分数
            quality_level: 质量等级
            tags: 标签列表
            categories: 分类列表
            location_lat: 纬度
            location_lng: 经度
            location_radius: 搜索半径（公里）
            sort_by: 排序字段
            sort_order: 排序顺序
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            (照片列表, 总数)
        """
        try:
            # 构建基础查询 - 只搜索已完成的照片
            query = db.query(Photo).filter(Photo.status.in_(['imported', 'completed']))

            # 关键词搜索
            if keyword:
                query = self._apply_keyword_filter(query, keyword)

            # 相机筛选
            if camera_make:
                query = query.filter(Photo.camera_make == camera_make)
            if camera_model:
                query = query.filter(Photo.camera_model == camera_model)

            # 日期筛选
            if date_from:
                query = query.filter(Photo.taken_at >= date_from)
            if date_to:
                query = query.filter(Photo.taken_at <= date_to)

            # 质量筛选
            if quality_min or quality_level:
                query = self._apply_quality_filter(query, quality_min, quality_level)

            # 标签筛选
            if tags:
                query = self._apply_tags_filter(query, tags)

            # 分类筛选
            if categories:
                query = self._apply_categories_filter(query, categories)

            # 地理位置筛选
            if location_lat and location_lng and location_radius:
                query = self._apply_location_filter(query, location_lat, location_lng, location_radius)

            # 获取总数
            total_count = query.count()

            # 排序
            query = self._apply_sorting(query, sort_by, sort_order)

            # 分页
            query = query.limit(limit).offset(offset)

            # 执行查询
            photos = query.all()

            # 格式化结果
            results = []
            for photo in photos:
                result = self._format_photo_result(db, photo)
                results.append(result)

            return results, total_count

        except Exception as e:
            self.logger.error(f"搜索照片失败: {e}")
            raise Exception(f"搜索照片失败: {e}")

    def _apply_keyword_filter(self, query, keyword: str):
        """应用关键词筛选"""
        try:
            # 首先尝试使用全文搜索
            fts_query = f"""
            SELECT rowid
            FROM photos_fts
            WHERE photos_fts MATCH '{keyword}'
            """

            # 获取匹配的照片ID
            result = query.session.execute(text(fts_query)).fetchall()
            photo_ids = [row[0] for row in result]

            if photo_ids:
                query = query.filter(Photo.id.in_(photo_ids))
                return query

        except Exception as e:
            self.logger.warning(f"FTS搜索失败，使用LIKE查询: {e}")

        # 如果FTS失败，使用传统的LIKE查询作为后备
        # 搜索文件名、路径、标签、分类和分析结果
        query = query.filter(
            or_(
                Photo.filename.ilike(f"%{keyword}%"),
                Photo.original_path.ilike(f"%{keyword}%"),
                Photo.description.ilike(f"%{keyword}%"),
                # 搜索标签
                Photo.tags.any(PhotoTag.tag.has(Tag.name.ilike(f"%{keyword}%"))),
                # 搜索分类
                Photo.categories.any(PhotoCategory.category.has(Category.name.ilike(f"%{keyword}%"))),
                # 搜索分析结果中的描述和标签
                Photo.analysis_results.any(
                    PhotoAnalysis.analysis_result.ilike(f"%{keyword}%")
                )
            )
        )

        return query

    def _apply_quality_filter(self, query, quality_min: Optional[float], quality_level: Optional[str]):
        """应用质量筛选"""
        subquery = query.session.query(PhotoQuality.photo_id).filter(
            PhotoQuality.photo_id == Photo.id
        )

        if quality_min:
            subquery = subquery.filter(PhotoQuality.quality_score >= quality_min)

        if quality_level:
            subquery = subquery.filter(PhotoQuality.quality_level == quality_level)

        query = query.filter(subquery.exists())
        return query

    def _apply_tags_filter(self, query, tags: List[str]):
        """应用标签筛选"""
        for tag_name in tags:
            subquery = query.session.query(PhotoTag.photo_id).join(Tag).filter(
                and_(
                    PhotoTag.photo_id == Photo.id,
                    Tag.name.ilike(f"%{tag_name}%")
                )
            )
            query = query.filter(subquery.exists())
        return query

    def _apply_categories_filter(self, query, categories: List[str]):
        """应用分类筛选"""
        for category_name in categories:
            subquery = query.session.query(PhotoCategory.photo_id).join(Category).filter(
                and_(
                    PhotoCategory.photo_id == Photo.id,
                    Category.name.ilike(f"%{category_name}%")
                )
            )
            query = query.filter(subquery.exists())
        return query

    def _apply_location_filter(self, query, lat: float, lng: float, radius_km: float):
        """应用地理位置筛选"""
        # 简化的距离计算（球面距离近似）
        # 注意：这只是近似计算，实际应用中可能需要更精确的地理计算

        # 每度纬度的距离约111公里
        lat_diff = radius_km / 111.0
        # 每度经度的距离随纬度变化
        lng_diff = radius_km / (111.0 * abs(lat) * 3.14159 / 180.0)

        query = query.filter(
            and_(
                Photo.location_lat.between(lat - lat_diff, lat + lat_diff),
                Photo.location_lng.between(lng - lng_diff, lng + lng_diff)
            )
        )

        return query

    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """应用排序"""
        sort_column = None

        if sort_by == "taken_at":
            sort_column = Photo.taken_at
        elif sort_by == "filename":
            sort_column = Photo.filename
        elif sort_by == "file_size":
            sort_column = Photo.file_size
        elif sort_by == "created_at":
            sort_column = Photo.created_at
        else:
            sort_column = Photo.taken_at  # 默认排序

        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        return query

    def _format_photo_result(self, db: Session, photo: Photo) -> Dict[str, Any]:
        """格式化照片搜索结果"""
        # 获取分析结果
        analysis = db.query(PhotoAnalysis).filter(
            PhotoAnalysis.photo_id == photo.id,
            PhotoAnalysis.analysis_type == 'content'
        ).first()

        # 获取质量评估
        quality = db.query(PhotoQuality).filter(
            PhotoQuality.photo_id == photo.id
        ).first()

        # 获取标签
        tags_query = db.query(Tag.name).join(PhotoTag).filter(
            PhotoTag.photo_id == photo.id
        )
        tags = [tag[0] for tag in tags_query.all()]

        # 获取分类
        categories_query = db.query(Category.name).join(PhotoCategory).filter(
            PhotoCategory.photo_id == photo.id
        )
        categories = [cat[0] for cat in categories_query.all()]

        result = {
            "id": photo.id,
            "filename": photo.filename,
            "original_path": photo.original_path,
            "thumbnail_path": photo.thumbnail_path,
            "file_size": photo.file_size,
            "width": photo.width,
            "height": photo.height,
            "format": photo.format,
            "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
            "camera_make": photo.camera_make,
            "camera_model": photo.camera_model,
            "location_lat": photo.location_lat,
            "location_lng": photo.location_lng,
            "location_name": photo.location_name,
            "status": photo.status,
            "created_at": photo.created_at.isoformat() if photo.created_at else None,

            # AI分析结果
            "analysis": {
                "description": analysis.analysis_result.get("description", "") if analysis else "",
                "scene_type": analysis.analysis_result.get("scene_type", "") if analysis else "",
                "objects": analysis.analysis_result.get("objects", []) if analysis else [],
                "tags": analysis.analysis_result.get("tags", []) if analysis else [],
                "confidence": analysis.confidence_score if analysis else 0.0
            } if analysis else None,

            # 质量评估
            "quality": {
                "score": quality.quality_score if quality else 0.0,
                "level": quality.quality_level if quality else "",
                "sharpness": quality.sharpness_score if quality else 0.0,
                "brightness": quality.brightness_score if quality else 0.0,
                "contrast": quality.contrast_score if quality else 0.0,
                "color": quality.color_score if quality else 0.0,
                "composition": quality.composition_score if quality else 0.0,
                "issues": quality.technical_issues if quality else {}
            } if quality else None,

            # 标签和分类
            "tags": tags,
            "categories": categories
        }

        return result

    def get_search_suggestions(self, db: Session, prefix: str, limit: int = 10) -> Dict[str, List[str]]:
        """
        获取搜索建议

        Args:
            db: 数据库会话
            prefix: 前缀
            limit: 建议数量限制

        Returns:
            搜索建议字典
        """
        suggestions = {
            "tags": [],
            "categories": [],
            "camera_makes": [],
            "camera_models": []
        }

        try:
            # 标签建议
            tags_query = db.query(Tag.name).filter(
                Tag.name.ilike(f"{prefix}%")
            ).limit(limit)
            suggestions["tags"] = [tag[0] for tag in tags_query.all()]

            # 分类建议
            categories_query = db.query(Category.name).filter(
                Category.name.ilike(f"{prefix}%")
            ).limit(limit)
            suggestions["categories"] = [cat[0] for cat in categories_query.all()]

            # 相机品牌建议
            camera_make_query = db.query(Photo.camera_make).filter(
                Photo.camera_make.ilike(f"{prefix}%")
            ).distinct().limit(limit)
            suggestions["camera_makes"] = [make[0] for make in camera_make_query.all()]

            # 相机型号建议
            camera_model_query = db.query(Photo.camera_model).filter(
                Photo.camera_model.ilike(f"{prefix}%")
            ).distinct().limit(limit)
            suggestions["camera_models"] = [model[0] for model in camera_model_query.all()]

        except Exception as e:
            self.logger.error(f"获取搜索建议失败: {e}")

        return suggestions

    def get_search_stats(self, db: Session) -> Dict[str, Any]:
        """
        获取搜索统计信息

        Args:
            db: 数据库会话

        Returns:
            统计信息字典
        """
        stats = {}

        try:
            # 基本统计
            stats["total_photos"] = db.query(Photo).filter(Photo.status.in_(['imported', 'completed'])).count()
            stats["total_tags"] = db.query(Tag).count()
            stats["total_categories"] = db.query(Category).count()

            # 质量分布
            quality_stats = db.query(
                PhotoQuality.quality_level,
                func.count(PhotoQuality.id)
            ).group_by(PhotoQuality.quality_level).all()

            stats["quality_distribution"] = {
                level: count for level, count in quality_stats
            }

            # 时间分布（按年份）
            year_stats = db.query(
                func.strftime('%Y', Photo.taken_at),
                func.count(Photo.id)
            ).filter(
                Photo.status.in_(['imported', 'completed']),
                Photo.taken_at.isnot(None)
            ).group_by(func.strftime('%Y', Photo.taken_at)).all()

            stats["year_distribution"] = {
                year: count for year, count in year_stats
            }

            # 相机统计
            camera_stats = db.query(
                Photo.camera_make,
                func.count(Photo.id)
            ).filter(
                Photo.status.in_(['imported', 'completed']),
                Photo.camera_make.isnot(None)
            ).group_by(Photo.camera_make).all()

            stats["camera_distribution"] = {
                make: count for make, count in camera_stats
            }

        except Exception as e:
            self.logger.error(f"获取搜索统计失败: {e}")

        return stats
