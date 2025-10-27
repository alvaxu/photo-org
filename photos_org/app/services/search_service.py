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
        face_count_min: Optional[int] = None,
        face_count_max: Optional[int] = None,
        format_filter: Optional[str] = None,
        camera_filter: Optional[str] = None,
        person_filter: str = "all",
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
            face_count_min: 最少人脸数
            face_count_max: 最多人脸数
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

            # 格式筛选
            if format_filter:
                query = query.filter(Photo.format == format_filter)

            # 相机品牌筛选（用于图表点击筛选）
            if camera_filter:
                if camera_filter == 'unknown':
                    # 特殊处理：筛选无相机信息的照片
                    query = query.filter(Photo.camera_make.is_(None))
                elif camera_filter == 'other':
                    # 特殊处理：筛选其他品牌的照片（不在前9名中）
                    # 获取前9个品牌的列表
                    top9_brands = db.query(Photo.camera_make).filter(
                        Photo.status.in_(['imported', 'quality_completed', 'content_completed', 'completed']),
                        Photo.camera_make.isnot(None)
                    ).group_by(Photo.camera_make).order_by(func.count(Photo.id).desc()).limit(9).all()
                    top9_brand_names = [brand[0] for brand in top9_brands]
                    query = query.filter(
                        Photo.camera_make.isnot(None),
                        Photo.camera_make.notin_(top9_brand_names)
                    )
                else:
                    # 普通相机品牌筛选
                    query = query.filter(Photo.camera_make == camera_filter)

            # 人物筛选
            if person_filter != "all":
                query = self._apply_person_filter(query, person_filter)

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

            # 人脸数量筛选
            if face_count_min is not None or face_count_max is not None:
                query = self._apply_face_count_filter(query, face_count_min, face_count_max)

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

    def _apply_face_count_filter(self, query, face_count_min: Optional[int], face_count_max: Optional[int]):
        """应用人脸数量筛选"""
        if face_count_min is not None:
            query = query.filter(Photo.face_count >= face_count_min)
        if face_count_max is not None:
            query = query.filter(Photo.face_count <= face_count_max)
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

    def get_search_stats(self, db: Session, keyword: Optional[str] = None,
                         search_type: str = "all", quality_filter: Optional[str] = None,
                         year_filter: Optional[str] = None, format_filter: Optional[str] = None,
                         camera_filter: Optional[str] = None, face_count_filter: Optional[str] = None,
                         tag_ids: Optional[List[int]] = None, category_ids: Optional[List[int]] = None, 
                         person_filter: Optional[str] = None, date_from: Optional[str] = None, 
                         date_to: Optional[str] = None) -> Dict[str, Any]:
        """
        获取搜索统计信息

        Args:
            db: 数据库会话
            keyword: 关键词搜索
            search_type: 搜索类型
            quality_filter: 质量筛选
            year_filter: 年份筛选
            format_filter: 格式筛选
            camera_filter: 相机筛选
            face_count_filter: 人脸数量筛选
            tag_ids: 标签ID列表
            category_ids: 分类ID列表
            person_filter: 人物筛选
            date_from: 开始日期
            date_to: 结束日期

        Returns:
            统计信息字典
        """
        stats = {}

        try:
            # 基础查询：获取有效照片（与search_photos保持一致）
            base_query = db.query(Photo).filter(Photo.status.in_([
                'imported', 'analyzing', 'quality_completed', 'content_completed', 'completed', 'error'
            ]))

            # 应用筛选条件（与search_photos完全相同的顺序和逻辑）

            # 关键词搜索（优先应用，作为第一步筛选）
            if keyword:
                base_query = self._apply_keyword_filter(base_query, keyword, search_type)

            # 格式筛选（在search_photos中排在前面）
            if format_filter:
                base_query = base_query.filter(Photo.format == format_filter)

            # 相机品牌筛选（用于图表点击筛选）
            if camera_filter:
                if camera_filter == 'unknown':
                    # 特殊处理：筛选无相机信息的照片
                    base_query = base_query.filter(Photo.camera_make.is_(None))
                elif camera_filter == 'other':
                    # 特殊处理：筛选其他品牌的照片（不在前9名中）
                    # 获取前9个品牌的列表
                    top9_brands = db.query(Photo.camera_make).filter(
                        Photo.status.in_(['imported', 'analyzing', 'quality_completed', 'content_completed', 'completed', 'error']),
                        Photo.camera_make.isnot(None)
                    ).group_by(Photo.camera_make).order_by(func.count(Photo.id).desc()).limit(9).all()
                    top9_brand_names = [brand[0] for brand in top9_brands]
                    base_query = base_query.filter(
                        Photo.camera_make.isnot(None),
                        Photo.camera_make.notin_(top9_brand_names)
                    )
                else:
                    # 普通相机品牌筛选
                    base_query = base_query.filter(Photo.camera_make == camera_filter)

            # 日期筛选（与search_photos完全相同）
            if date_from or date_to:
                if date_from == "no_date" and date_to == "no_date":
                    # 特殊处理：筛选无拍摄时间的照片
                    base_query = base_query.filter(Photo.taken_at.is_(None))
                elif date_from and date_from != "no_date" and date_to and date_to != "no_date":
                    # 日期范围查询（同时设置开始和结束日期）
                    base_query = base_query.filter(Photo.taken_at.between(date_from, date_to))
                elif date_from and date_from != "no_date":
                    # 只设置开始日期
                    base_query = base_query.filter(Photo.taken_at >= date_from)
                elif date_to and date_to != "no_date":
                    # 只设置结束日期
                    base_query = base_query.filter(Photo.taken_at <= date_to)

            # 质量筛选
            if quality_filter:
                base_query = self._apply_quality_filter(base_query, None, quality_filter)

            # 人脸数量筛选
            if face_count_filter:
                # 处理预设的人脸数量筛选
                face_count_min = None
                face_count_max = None
                
                if face_count_filter == "0":
                    face_count_min = 0
                    face_count_max = 0
                elif face_count_filter == "1":
                    face_count_min = 1
                    face_count_max = 1
                elif face_count_filter == "2":
                    face_count_min = 2
                    face_count_max = 2
                elif face_count_filter == "3":
                    face_count_min = 3
                    face_count_max = 3
                elif face_count_filter == "4":
                    face_count_min = 4
                    face_count_max = 4
                elif face_count_filter == "5":
                    face_count_min = 5
                    face_count_max = 5
                elif face_count_filter == "6":
                    face_count_min = 6
                    face_count_max = 6
                elif face_count_filter == "7":
                    face_count_min = 7
                    face_count_max = 7
                elif face_count_filter == "8":
                    face_count_min = 8
                    face_count_max = 8
                elif face_count_filter == "9":
                    face_count_min = 9
                    face_count_max = 9
                elif face_count_filter == "10":
                    face_count_min = 10
                    face_count_max = 10
                elif face_count_filter == "4-5":
                    face_count_min = 4
                    face_count_max = 5
                elif face_count_filter == "6-9":
                    face_count_min = 6
                    face_count_max = 9
                elif face_count_filter == "9+":
                    face_count_min = 10
                    face_count_max = None
                elif face_count_filter == "1+":
                    face_count_min = 1
                    face_count_max = None
                
                base_query = self._apply_face_count_filter(base_query, face_count_min, face_count_max)

            # 标签ID筛选
            if tag_ids:
                base_query = self._apply_tag_ids_filter(base_query, tag_ids)

            # 分类ID筛选
            if category_ids:
                base_query = self._apply_category_ids_filter(base_query, category_ids)

            # 人物筛选
            if person_filter and person_filter != 'all':
                base_query = self._apply_person_filter(base_query, person_filter)

            # 年份筛选（特殊处理）
            if year_filter:
                base_query = base_query.filter(func.strftime('%Y', Photo.taken_at) == year_filter)

            # 基本统计
            stats["total_photos"] = base_query.count()
            # 注意：total_tags和total_categories应该是全局统计，不随筛选变化
            stats["total_tags"] = db.query(Tag).count()
            stats["total_categories"] = db.query(Category).count()

            # 筛选结果的存储量（GB）
            total_size_bytes = db.query(func.sum(Photo.file_size)).filter(
                Photo.id.in_(base_query.with_entities(Photo.id))
            ).scalar() or 0
            stats["total_storage_gb"] = round(total_size_bytes / (1024 * 1024 * 1024), 1)

            # 筛选结果的时间跨度（年）
            date_range = db.query(
                func.min(Photo.taken_at),
                func.max(Photo.taken_at)
            ).filter(
                Photo.id.in_(base_query.with_entities(Photo.id)),
                Photo.taken_at.isnot(None)
            ).first()

            if date_range and date_range[0] and date_range[1]:
                min_year = date_range[0].year
                max_year = date_range[1].year
                stats["time_span_years"] = max_year - min_year + 1
            else:
                stats["time_span_years"] = 0

            # 筛选结果的平均质量分
            avg_quality = db.query(func.avg(PhotoQuality.quality_score)).join(
                Photo, Photo.id == PhotoQuality.photo_id
            ).filter(
                Photo.id.in_(base_query.with_entities(Photo.id))
            ).scalar()
            stats["avg_quality"] = round(avg_quality, 1) if avg_quality else 0.0

            # 筛选结果的分析状态统计
            status_counts = db.query(Photo.status, func.count(Photo.id)).filter(
                Photo.id.in_(base_query.with_entities(Photo.id))
            ).group_by(Photo.status).all()

            # 初始化为0
            stats["photos_unanalyzed"] = 0
            stats["photos_basic_analyzed"] = 0
            stats["photos_ai_analyzed"] = 0
            stats["photos_fully_analyzed"] = 0

            # 填充实际统计数据
            for status, count in status_counts:
                if status == 'imported':
                    stats["photos_unanalyzed"] = count
                elif status == 'quality_completed':
                    stats["photos_basic_analyzed"] = count
                elif status == 'content_completed':
                    stats["photos_ai_analyzed"] = count
                elif status == 'completed':
                    stats["photos_fully_analyzed"] = count

            # 筛选结果的GPS统计
            stats["photos_with_gps"] = db.query(func.count(Photo.id)).filter(
                Photo.id.in_(base_query.with_entities(Photo.id)),
                Photo.location_lat.isnot(None),
                Photo.location_lng.isnot(None)
            ).scalar()

            stats["photos_geocoded"] = db.query(func.count(Photo.id)).filter(
                Photo.id.in_(base_query.with_entities(Photo.id)),
                Photo.location_name.isnot(None)
            ).scalar()

            # 质量分布图表数据（基于筛选结果）
            quality_stats = db.query(
                PhotoQuality.quality_level,
                func.count(PhotoQuality.id)
            ).join(Photo, Photo.id == PhotoQuality.photo_id).filter(
                Photo.id.in_(base_query.with_entities(Photo.id))
            ).group_by(PhotoQuality.quality_level).all()

            # 转换为图表格式
            quality_level_map = {
                '优秀': {'order': 0, 'color': '#28a745'},
                '良好': {'order': 1, 'color': '#20c997'},
                '一般': {'order': 2, 'color': '#ffc107'},
                '较差': {'order': 3, 'color': '#fd7e14'},
                '很差': {'order': 4, 'color': '#dc3545'}
            }

            quality_data = []
            quality_labels = []
            quality_colors = []

            for level, count in quality_stats:
                if level in quality_level_map:
                    quality_data.append(count)
                    quality_labels.append(level)
                    quality_colors.append(quality_level_map[level]['color'])

            # 按质量等级排序
            sorted_indices = sorted(range(len(quality_labels)),
                                  key=lambda i: quality_level_map[quality_labels[i]]['order'])

            stats["charts"] = {
                "quality": {
                    "labels": [quality_labels[i] for i in sorted_indices],
                    "data": [quality_data[i] for i in sorted_indices],
                    "colors": [quality_colors[i] for i in sorted_indices]
                }
            }

            # 人脸数量分布图表数据（基于筛选结果）
            face_count_stats = db.query(
                Photo.face_count,
                func.count(Photo.id)
            ).filter(
                Photo.id.in_(base_query.with_entities(Photo.id)),
                Photo.face_count.isnot(None)
            ).group_by(Photo.face_count).order_by(Photo.face_count).all()

            # 转换为图表格式 - 1-9人分别显示，9人以上合并
            face_count_labels = []
            face_count_data = []
            face_count_colors = []

            # 定义人脸数量范围的颜色
            face_count_colors_map = {
                0: '#6c757d',    # 无人 - 灰色
                1: '#007bff',    # 1人 - 蓝色
                2: '#28a745',    # 2人 - 绿色
                3: '#ffc107',    # 3人 - 黄色
                4: '#fd7e14',    # 4人 - 橙色
                5: '#dc3545',    # 5人 - 红色
                6: '#6f42c1',    # 6人 - 紫色
                7: '#20c997',    # 7人 - 青色
                8: '#e83e8c',    # 8人 - 粉色
                9: '#fd7e14'     # 9人 - 橙色
            }

            # 初始化0-9人的数据
            face_count_dict = {}
            for i in range(10):  # 0-9人
                face_count_dict[i] = 0

            # 填充实际数据
            for face_count, count in face_count_stats:
                if face_count <= 9:
                    face_count_dict[face_count] = count
                else:
                    # 9人以上合并（10人及以上）
                    if 10 not in face_count_dict:
                        face_count_dict[10] = 0
                    face_count_dict[10] += count

            # 生成图表数据
            for i in range(10):  # 0-9人
                if face_count_dict[i] > 0:
                    face_count_labels.append(f"{i}人")
                    face_count_data.append(face_count_dict[i])
                    face_count_colors.append(face_count_colors_map.get(i, '#6c757d'))

            # 添加9人以上
            if 10 in face_count_dict and face_count_dict[10] > 0:
                face_count_labels.append("9人以上")
                face_count_data.append(face_count_dict[10])
                face_count_colors.append('#dc3545')

            stats["charts"]["face_count"] = {
                "labels": face_count_labels,
                "data": face_count_data,
                "colors": face_count_colors
            }

            # 年份分布图表数据（基于筛选结果）
            year_stats = db.query(
                func.strftime('%Y', Photo.taken_at),
                func.count(Photo.id)
            ).filter(
                Photo.id.in_(base_query.with_entities(Photo.id)),
                Photo.taken_at.isnot(None)
            ).group_by(func.strftime('%Y', Photo.taken_at)).order_by(func.strftime('%Y', Photo.taken_at)).all()

            # 获取无拍摄时间的照片数量（基于筛选结果）
            no_date_count = db.query(func.count(Photo.id)).filter(
                Photo.id.in_(base_query.with_entities(Photo.id)),
                Photo.taken_at.is_(None)
            ).scalar()

            # 合并年份统计和无拍摄时间统计
            year_labels = [year for year, count in year_stats]
            year_data = [count for year, count in year_stats]

            # 如果有无拍摄时间的照片，添加到统计中
            if no_date_count > 0:
                year_labels.append('无拍摄时间')
                year_data.append(no_date_count)

            stats["charts"]["year"] = {
                "labels": year_labels,
                "data": year_data,
                "colors": ['#007bff'] * len(year_stats) + (['#dc3545'] if no_date_count > 0 else [])
            }

            # 格式分布图表数据（基于筛选结果）
            format_stats = db.query(
                Photo.format,
                func.count(Photo.id)
            ).filter(
                Photo.id.in_(base_query.with_entities(Photo.id))
            ).group_by(Photo.format).all()

            format_colors = {
                'JPG': '#28a745', 'JPEG': '#28a745',
                'PNG': '#007bff',
                'HEIC': '#6f42c1', 'HEIF': '#6f42c1',
                'TIFF': '#fd7e14', 'TIF': '#fd7e14',
                'BMP': '#dc3545',
                'WEBP': '#20c997',
                'GIF': '#ffc107'
            }

            stats["charts"]["format"] = {
                "labels": [fmt.upper() for fmt, count in format_stats],
                "data": [count for fmt, count in format_stats],
                "colors": [format_colors.get(fmt.upper(), '#6c757d') for fmt, count in format_stats]
            }

            # 相机分布图表数据（前9个品牌 + 其他品牌 + 未知相机，基于筛选结果）
            camera_stats = db.query(
                Photo.camera_make,
                func.count(Photo.id)
            ).filter(
                Photo.id.in_(base_query.with_entities(Photo.id)),
                Photo.camera_make.isnot(None)
            ).group_by(Photo.camera_make).order_by(func.count(Photo.id).desc()).limit(9).all()

            # 获取其他品牌的照片数量（第10名及以后，基于筛选结果）
            other_camera_count = db.query(func.count(Photo.id)).filter(
                Photo.id.in_(base_query.with_entities(Photo.id)),
                Photo.camera_make.isnot(None),
                Photo.camera_make.notin_([make for make, count in camera_stats])
            ).scalar()

            # 获取未知相机的照片数量（基于筛选结果）
            unknown_camera_count = db.query(func.count(Photo.id)).filter(
                Photo.id.in_(base_query.with_entities(Photo.id)),
                Photo.camera_make.is_(None)
            ).scalar()

            # 合并相机统计
            camera_labels = [make for make, count in camera_stats]
            camera_data = [count for make, count in camera_stats]

            # 添加其他品牌统计（放在倒数第二）
            if other_camera_count > 0:
                camera_labels.append('其他品牌')
                camera_data.append(other_camera_count)

            # 添加未知相机统计（放在最后）
            if unknown_camera_count > 0:
                camera_labels.append('未知相机')
                camera_data.append(unknown_camera_count)

            # 设置颜色：前9个品牌紫色，其他品牌橙色，未知相机红色
            colors = (['#6f42c1'] * len(camera_stats) +
                     (['#fd7e14'] if other_camera_count > 0 else []) +
                     (['#dc3545'] if unknown_camera_count > 0 else []))

            stats["charts"]["camera"] = {
                "labels": camera_labels,
                "data": camera_data,
                "colors": colors
            }

        except Exception as e:
            self.logger.error(f"获取搜索统计失败: {e}")
            # 返回基本统计作为fallback
            stats = {
                "total_photos": 0,
                "total_tags": 0,
                "total_categories": 0,
                "total_storage_gb": 0,
                "time_span_years": 0,
                "avg_quality": 0.0,
                "photos_unanalyzed": 0,
                "photos_basic_analyzed": 0,
                "photos_ai_analyzed": 0,
                "photos_fully_analyzed": 0,
                "photos_with_gps": 0,
                "photos_geocoded": 0,
                "charts": {
                    "quality": {"labels": [], "data": [], "colors": []},
                    "year": {"labels": [], "data": [], "colors": []},
                    "format": {"labels": [], "data": [], "colors": []},
                    "camera": {"labels": [], "data": [], "colors": []}
                }
            }

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

    def _apply_person_filter(self, query, person_filter: str):
        """
        应用人物筛选条件
        
        Args:
            query: SQLAlchemy查询对象
            person_filter: 人物筛选条件
            
        Returns:
            修改后的查询对象
        """
        try:
            from app.models.face import FaceDetection, FaceClusterMember, FaceCluster
            
            if person_filter == "unlabeled":
                # 查询未标记人物的照片
                query = query.join(FaceDetection, Photo.id == FaceDetection.photo_id)\
                           .join(FaceClusterMember, FaceDetection.face_id == FaceClusterMember.face_id)\
                           .join(FaceCluster, FaceClusterMember.cluster_id == FaceCluster.cluster_id)\
                           .filter(FaceCluster.is_labeled == False)
            else:
                # 查询特定聚类的照片
                query = query.join(FaceDetection, Photo.id == FaceDetection.photo_id)\
                           .join(FaceClusterMember, FaceDetection.face_id == FaceClusterMember.face_id)\
                           .filter(FaceClusterMember.cluster_id == person_filter)
            
            return query

        except Exception as e:
            self.logger.error(f"应用人物筛选条件失败: {str(e)}")
            return query
