"""
家庭版智能照片系统 - 搜索服务
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
        search_type: str = "all",
        camera_make: Optional[str] = None,
        camera_model: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        quality_min: Optional[float] = None,
        quality_level: Optional[str] = None,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        tag_ids: Optional[List[int]] = None,
        category_ids: Optional[List[int]] = None,
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
            # 构建基础查询 - 搜索所有状态的照片（包括error状态）
            query = db.query(Photo).filter(Photo.status.in_([
                'imported', 'analyzing', 'quality_completed', 'content_completed', 'completed', 'error'
            ]))

            # 关键词搜索
            if keyword:
                query = self._apply_keyword_filter(query, keyword, search_type)

            # 相机筛选
            if camera_make:
                query = query.filter(Photo.camera_make == camera_make)
            if camera_model:
                query = query.filter(Photo.camera_model == camera_model)

            # 日期筛选
            if date_from == "no_date" and date_to == "no_date":
                # 特殊处理：筛选无拍摄时间的照片
                query = query.filter(Photo.taken_at.is_(None))
            elif date_from and date_from != "no_date" and date_to and date_to != "no_date":
                # 日期范围查询（同时设置开始和结束日期）
                query = query.filter(Photo.taken_at.between(date_from, date_to))
            elif date_from and date_from != "no_date":
                # 只设置开始日期
                query = query.filter(Photo.taken_at >= date_from)
            elif date_to and date_to != "no_date":
                # 只设置结束日期
                query = query.filter(Photo.taken_at <= date_to)

            # 质量筛选
            if quality_min or quality_level:
                query = self._apply_quality_filter(query, quality_min, quality_level)

            # 标签筛选
            if tags:
                query = self._apply_tags_filter(query, tags)
            
            # 标签ID筛选
            if tag_ids:
                query = self._apply_tag_ids_filter(query, tag_ids)

            # 分类筛选
            if categories:
                query = self._apply_categories_filter(query, categories)
            
            # 分类ID筛选
            if category_ids:
                query = self._apply_category_ids_filter(query, category_ids)

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

    def _apply_keyword_filter(self, query, keyword: str, search_type: str = "all"):
        """应用关键词筛选"""
        # 如果关键词为空，直接返回原查询
        if not keyword or not keyword.strip():
            return query
            
        # 根据搜索类型选择不同的搜索策略
        if search_type == "all":
            # 检查FTS表是否存在
            if self._check_fts_table_exists(query.session):
                try:
                    # 全部内容搜索，使用全文搜索
                    fts_query = f"""
                    SELECT photo_id
                    FROM photos_fts
                    WHERE photos_fts MATCH '{keyword}'
                    """

                    # 获取匹配的照片ID
                    result = query.session.execute(text(fts_query)).fetchall()
                    photo_ids = [row[0] for row in result]

                    # 如果FTS搜索没有结果，尝试前缀搜索（解决中文分词问题）
                    if not photo_ids:
                        # 处理多词搜索，将每个词都尝试前缀搜索
                        words = keyword.split()
                        if len(words) > 1:
                            # 多词搜索：尝试每个词的前缀搜索，使用AND关系
                            try:
                                prefix_words = [f"{word}*" for word in words]
                                fts_prefix_query = f"""
                                SELECT photo_id
                                FROM photos_fts
                                WHERE photos_fts MATCH '{" AND ".join(prefix_words)}'
                                """
                                result = query.session.execute(text(fts_prefix_query)).fetchall()
                                photo_ids = [row[0] for row in result]
                            except Exception:
                                pass
                        elif len(keyword) <= 3:  # 单词且短词尝试前缀搜索
                            try:
                                fts_prefix_query = f"""
                                SELECT photo_id
                                FROM photos_fts
                                WHERE photos_fts MATCH '{keyword}*'
                                """
                                result = query.session.execute(text(fts_prefix_query)).fetchall()
                                photo_ids = [row[0] for row in result]
                            except Exception:
                                pass

                    if photo_ids:
                        query = query.filter(Photo.id.in_(photo_ids))
                        return query
                except Exception as e:
                    # FTS搜索失败，继续使用LIKE查询
                    pass

        elif search_type == "filename":
            # 只搜索文件名
            query = query.filter(
                or_(
                    Photo.filename.ilike(f"%{keyword}%"),
                    Photo.original_path.ilike(f"%{keyword}%")
                )
            )
            return query

        elif search_type == "tags":
            # 只搜索标签
            query = query.filter(
                Photo.tags.any(PhotoTag.tag.has(Tag.name.ilike(f"%{keyword}%")))
            )
            return query

        elif search_type == "categories":
            # 只搜索分类
            query = query.filter(
                Photo.categories.any(PhotoCategory.category.has(Category.name.ilike(f"%{keyword}%")))
            )
            return query

        elif search_type == "description":
            # 搜索用户手动添加的照片描述
            query = query.filter(
                Photo.description.ilike(f"%{keyword}%")
            )
            return query

        elif search_type == "address":
            # 搜索拍摄地址信息
            query = query.filter(
                Photo.location_name.ilike(f"%{keyword}%")
            )
            return query

        elif search_type == "ai_analysis":
            # 搜索所有类型的AI分析结果（content, scene, objects, faces等）
            query = query.filter(
                Photo.analysis_results.any(
                    PhotoAnalysis.analysis_result.ilike(f"%{keyword}%")
                )
            )
            return query

        # 如果FTS失败或search_type为all，使用传统的LIKE查询作为后备
        if search_type == "all":
            # 搜索文件名、路径、描述、标签、分类、分析结果和地址信息
            query = query.filter(
                or_(
                    Photo.filename.ilike(f"%{keyword}%"),
                    Photo.original_path.ilike(f"%{keyword}%"),
                    Photo.description.ilike(f"%{keyword}%"),
                    Photo.location_name.ilike(f"%{keyword}%"),  # 搜索地址信息
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
            # 将英文质量等级转换为中文
            quality_mapping = {
                'excellent': '优秀',
                'good': '良好', 
                'average': '一般',
                'fair': '一般',
                'poor': '较差',
                'bad': '很差'
            }
            chinese_quality_level = quality_mapping.get(quality_level, quality_level)
            subquery = subquery.filter(PhotoQuality.quality_level == chinese_quality_level)

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

    def _apply_tag_ids_filter(self, query, tag_ids: List[int]):
        """应用标签ID筛选 - 与关系：照片必须包含所有选中的标签"""
        # 为每个标签ID创建一个子查询，确保照片包含该标签
        for tag_id in tag_ids:
            subquery = query.session.query(PhotoTag.photo_id).filter(
                and_(
                    PhotoTag.photo_id == Photo.id,
                    PhotoTag.tag_id == tag_id
                )
            )
            query = query.filter(subquery.exists())
        return query

    def _apply_category_ids_filter(self, query, category_ids: List[int]):
        """应用分类ID筛选 - 与关系：照片必须包含所有选中的分类"""
        # 为每个分类ID创建一个子查询，确保照片包含该分类
        for category_id in category_ids:
            subquery = query.session.query(PhotoCategory.photo_id).filter(
                and_(
                    PhotoCategory.photo_id == Photo.id,
                    PhotoCategory.category_id == category_id
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
        if sort_by == "quality_score":
            # 质量分数排序需要JOIN PhotoQuality表
            query = query.join(PhotoQuality, Photo.id == PhotoQuality.photo_id, isouter=True)
            sort_column = PhotoQuality.quality_score
        elif sort_by == "taken_at":
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
            "description": photo.description,
            "status": photo.status,
            "created_at": photo.created_at.isoformat() if photo.created_at else None,

            # AI分析结果（字段名必须与Pydantic模型匹配）
            "analysis": {
                "description": analysis.analysis_result.get("description", "") if analysis else "",
                "scene_type": analysis.analysis_result.get("scene_type", "") if analysis else "",
                "objects": analysis.analysis_result.get("objects", []) if analysis else [],
                "people_count": analysis.analysis_result.get("people_count", "") if analysis else "",
                "emotion": analysis.analysis_result.get("emotion", "") if analysis else "",
                "activity": analysis.analysis_result.get("activity", "") if analysis else "",
                "time_period": analysis.analysis_result.get("time_period", "") if analysis else "",
                "location_type": analysis.analysis_result.get("location_type", "") if analysis else "",
                "tags": analysis.analysis_result.get("tags", []) if analysis else [],
                "confidence": analysis.confidence_score if analysis else 0.0,
                "analyzed_at": analysis.created_at.isoformat() if analysis and analysis.created_at else None
            } if analysis else None,

            # 质量评估（字段名必须与Pydantic模型匹配）
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
            stats["total_photos"] = db.query(Photo).filter(Photo.status.in_([
                'imported', 'analyzing', 'quality_completed', 'content_completed', 'completed'
            ])).count()
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
                Photo.status.in_([
                    'imported', 'quality_completed', 'content_completed', 'completed'
                ]),
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
                Photo.status.in_([
                    'imported', 'quality_completed', 'content_completed', 'completed'
                ]),
                Photo.camera_make.isnot(None)
            ).group_by(Photo.camera_make).all()

            stats["camera_distribution"] = {
                make: count for make, count in camera_stats
            }

        except Exception as e:
            self.logger.error(f"获取搜索统计失败: {e}")

        return stats

    def _check_fts_table_exists(self, db: Session) -> bool:
        """
        检查FTS表是否存在
        
        :param db: 数据库会话
        :return: 是否存在
        """
        try:
            # 检查photos_fts表是否存在
            result = db.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='photos_fts'
            """)).fetchone()
            
            return result is not None
        except Exception as e:
            self.logger.error(f"检查FTS表存在性失败: {e}")
            return False
