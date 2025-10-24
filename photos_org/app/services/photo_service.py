"""
家庭版智能照片系统 - 照片管理服务
"""
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from app.core.config import settings
from app.core.logging import get_logger
from app.models.photo import Photo, PhotoTag, PhotoCategory, Tag, Category, PhotoAnalysis, PhotoQuality
from app.models.photo import DuplicateGroup, DuplicateGroupPhoto
from app.schemas.photo import PhotoCreate


class PhotoService:
    """
    照片管理服务类
    提供照片的增删改查、筛选、统计等功能
    """

    def __init__(self):
        """初始化照片服务"""
        self.logger = get_logger(__name__)

    def get_photos(self, db: Session, skip: int = 0, limit: int = 50,
                   filters: Optional[Dict[str, Any]] = None,
                   sort_by: str = "created_at", sort_order: str = "desc",
                   person_filter: str = "all") -> Tuple[List[Photo], int]:
        """
        获取照片列表

        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的记录数上限
            filters: 筛选条件
            sort_by: 排序字段
            sort_order: 排序顺序

        Returns:
            (照片列表, 总数)
        """
        try:
            # 构建基础查询 - 包含所有状态的照片（包括error状态）
            query = db.query(Photo).filter(Photo.status.in_([
                'imported', 'analyzing', 'quality_completed', 'content_completed', 'completed', 'error'
            ]))

            # 应用筛选条件
            if filters:
                query = self._apply_filters(query, filters)

            # 应用人物筛选
            if person_filter != "all":
                query = self._apply_person_filter(query, person_filter)

            # 获取总数
            total = query.count()

            # 应用排序
            if hasattr(Photo, sort_by):
                sort_column = getattr(Photo, sort_by)
                if sort_order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))

            # 应用分页
            photos = query.offset(skip).limit(limit).all()

            return photos, total

        except Exception as e:
            self.logger.error(f"获取照片列表失败: {str(e)}")
            return [], 0

    def get_photo_by_id(self, db: Session, photo_id: int) -> Optional[Photo]:
        """
        根据ID获取照片

        Args:
            db: 数据库会话
            photo_id: 照片ID

        Returns:
            照片对象或None
        """
        try:
            # 加载关联关系，确保quality_assessments和analysis_results被加载
            from sqlalchemy.orm import joinedload
            photo = db.query(Photo).options(
                joinedload(Photo.quality_assessments),
                joinedload(Photo.analysis_results)
            ).filter(Photo.id == photo_id).first()
            return photo
        except Exception as e:
            self.logger.error(f"获取照片失败 photo_id={photo_id}: {str(e)}")
            return None

    def create_photo(self, db: Session, photo_data: PhotoCreate) -> Optional[Photo]:
        """
        创建照片记录

        Args:
            db: 数据库会话
            photo_data: 照片数据

        Returns:
            创建的照片对象或None
        """
        try:
            # 检查是否已存在相同哈希的照片
            existing_photo = db.query(Photo).filter(Photo.file_hash == photo_data.file_hash).first()
            if existing_photo:
                self.logger.warning(f"照片已存在，跳过创建: {photo_data.filename}")
                return existing_photo
            
            # 将Pydantic模型转换为字典
            photo_dict = photo_data.dict()
            
            # 创建Photo对象
            photo = Photo(**photo_dict)
            
            # 保存到数据库
            db.add(photo)
            db.commit()
            db.refresh(photo)
            
            self.logger.info(f"照片创建成功: {photo.filename}")
            return photo
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"创建照片失败: {str(e)}")
            return None

    def update_photo(self, db: Session, photo_id: int, update_data: Dict[str, Any]) -> bool:
        """
        更新照片信息

        Args:
            db: 数据库会话
            photo_id: 照片ID
            update_data: 更新数据

        Returns:
            更新是否成功
        """
        try:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return False

            # 更新字段
            for key, value in update_data.items():
                if hasattr(photo, key):
                    setattr(photo, key, value)

            photo.updated_at = datetime.now()
            db.commit()

            self.logger.info(f"照片更新成功 photo_id={photo_id}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"更新照片失败 photo_id={photo_id}: {str(e)}")
            return False

    def delete_photo(self, db: Session, photo_id: int, delete_file: bool = True) -> bool:
        """
        删除照片

        Args:
            db: 数据库会话
            photo_id: 照片ID
            delete_file: 是否删除物理文件

        Returns:
            删除是否成功
        """
        try:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return False

            # 🔥 新增：清理人脸识别相关数据
            self._cleanup_face_recognition_data(db, photo_id)

            # 删除物理文件
            if delete_file:
                try:
                    # 构建完整的文件路径
                    from app.core.config import settings
                    storage_base = Path(settings.storage.base_path)
                    full_original_path = storage_base / photo.original_path
                    
                    if full_original_path.exists():
                        os.remove(full_original_path)

                    # 删除缩略图
                    if photo.thumbnail_path:
                        full_thumbnail_path = storage_base / photo.thumbnail_path
                        if full_thumbnail_path.exists():
                            os.remove(full_thumbnail_path)

                except Exception as e:
                    self.logger.warning(f"删除物理文件失败: {str(e)}")

            # 删除数据库记录（级联删除）
            db.delete(photo)
            db.commit()

            self.logger.info(f"照片删除成功 photo_id={photo_id}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"删除照片失败 photo_id={photo_id}: {str(e)}")
            return False

    def _cleanup_face_recognition_data(self, db: Session, photo_id: int):
        """
        清理照片相关的人脸识别数据
        
        Args:
            db: 数据库会话
            photo_id: 照片ID
        """
        try:
            from app.models.face import FaceDetection, FaceClusterMember, FaceCluster, Person
            
            # 1. 获取该照片的所有人脸检测记录
            face_detections = db.query(FaceDetection).filter(FaceDetection.photo_id == photo_id).all()
            face_ids = [fd.face_id for fd in face_detections]
            
            if not face_ids:
                return  # 没有人脸数据，直接返回
            
            self.logger.info(f"清理照片 {photo_id} 的人脸识别数据，涉及 {len(face_ids)} 个人脸")
            
            # 2. 获取受影响的聚类ID
            affected_cluster_ids = set()
            for face_id in face_ids:
                cluster_members = db.query(FaceClusterMember).filter(FaceClusterMember.face_id == face_id).all()
                for member in cluster_members:
                    affected_cluster_ids.add(member.cluster_id)
            
            # 3. 删除聚类成员记录
            deleted_members = db.query(FaceClusterMember).filter(
                FaceClusterMember.face_id.in_(face_ids)
            ).delete(synchronize_session=False)
            
            if deleted_members > 0:
                self.logger.info(f"删除了 {deleted_members} 个聚类成员记录")
            
            # 4. 处理受影响的聚类
            for cluster_id in affected_cluster_ids:
                cluster = db.query(FaceCluster).filter(FaceCluster.cluster_id == cluster_id).first()
                if not cluster:
                    continue
                
                # 检查聚类是否还有成员
                remaining_members = db.query(FaceClusterMember).filter(
                    FaceClusterMember.cluster_id == cluster_id
                ).count()
                
                if remaining_members == 0:
                    # 聚类为空，删除聚类
                    self.logger.info(f"删除空聚类: {cluster_id}")
                    db.delete(cluster)
                else:
                    # 更新聚类的人脸数量
                    cluster.face_count = remaining_members
                    
                    # 如果代表人脸被删除，需要重新选择代表人脸
                    if cluster.representative_face_id in face_ids:
                        # 选择剩余成员中的第一个作为新的代表人脸
                        new_representative = db.query(FaceClusterMember).filter(
                            FaceClusterMember.cluster_id == cluster_id
                        ).first()
                        if new_representative:
                            cluster.representative_face_id = new_representative.face_id
                            self.logger.info(f"更新聚类 {cluster_id} 的代表人脸为: {new_representative.face_id}")
            
            # 5. 删除人脸检测记录
            deleted_detections = db.query(FaceDetection).filter(
                FaceDetection.photo_id == photo_id
            ).delete(synchronize_session=False)
            
            if deleted_detections > 0:
                self.logger.info(f"删除了 {deleted_detections} 个人脸检测记录")
            
            # 6. 检查并清理没有聚类的人物记录
            self._cleanup_orphan_persons(db)
            
            self.logger.info(f"照片 {photo_id} 的人脸识别数据清理完成")
            
        except Exception as e:
            self.logger.error(f"清理人脸识别数据失败 photo_id={photo_id}: {str(e)}")
            raise  # 重新抛出异常，让上层处理

    def _cleanup_orphan_persons(self, db: Session):
        """
        清理没有聚类的人物记录
        
        Args:
            db: 数据库会话
        """
        try:
            from app.models.face import Person, FaceCluster
            
            # 查找没有聚类的人物
            orphan_persons = db.query(Person).filter(
                ~Person.person_id.in_(
                    db.query(FaceCluster.person_id).filter(FaceCluster.person_id.isnot(None))
                )
            ).all()
            
            for person in orphan_persons:
                self.logger.info(f"删除没有聚类的人物: {person.person_name} ({person.person_id})")
                db.delete(person)
                
        except Exception as e:
            self.logger.error(f"清理孤儿人物记录失败: {str(e)}")

    def batch_delete_photos(self, db: Session, photo_ids: List[int], delete_files: bool = True) -> Tuple[int, List[int]]:
        """
        批量删除照片

        Args:
            db: 数据库会话
            photo_ids: 照片ID列表
            delete_files: 是否删除物理文件

        Returns:
            (成功删除数量, 失败的ID列表)
        """
        successful_deletions = 0
        failed_ids = []

        for photo_id in photo_ids:
            if self.delete_photo(db, photo_id, delete_files):
                successful_deletions += 1
            else:
                failed_ids.append(photo_id)

        self.logger.info(f"批量删除完成: {successful_deletions}成功, {len(failed_ids)}失败")
        return successful_deletions, failed_ids

    def get_photo_statistics(self, db: Session) -> Dict[str, Any]:
        """
        获取照片统计信息

        Args:
            db: 数据库会话

        Returns:
            统计信息字典
        """
        try:
            # 基本统计
            total_photos = db.query(func.count(Photo.id)).scalar() or 0
            total_size = db.query(func.sum(Photo.file_size)).scalar() or 0

            # 状态统计
            status_stats = db.query(
                Photo.status,
                func.count(Photo.id)
            ).group_by(Photo.status).all()

            # 格式统计
            format_stats = db.query(
                Photo.format,
                func.count(Photo.id)
            ).group_by(Photo.format).all()

            # 时间分布（按年份）
            year_stats = db.query(
                func.strftime('%Y', Photo.created_at),
                func.count(Photo.id)
            ).group_by(func.strftime('%Y', Photo.created_at)).all()

            # 质量统计
            quality_stats = db.query(
                PhotoAnalysis.quality_rating,
                func.count(PhotoAnalysis.id)
            ).join(Photo).group_by(PhotoAnalysis.quality_rating).all()

            return {
                "total_photos": total_photos,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "status_distribution": dict(status_stats),
                "format_distribution": dict(format_stats),
                "yearly_distribution": dict(year_stats),
                "quality_distribution": dict(quality_stats),
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {
                "total_photos": 0,
                "total_size": 0,
                "error": str(e)
            }

    def search_photos(self, db: Session, query: str, skip: int = 0, limit: int = 50) -> Tuple[List[Photo], int]:
        """
        搜索照片

        Args:
            db: 数据库会话
            query: 搜索关键词
            skip: 跳过的记录数
            limit: 返回的记录数上限

        Returns:
            (照片列表, 总数)
        """
        try:
            # 基础搜索：文件名、描述、标签
            search_filter = or_(
                Photo.filename.ilike(f'%{query}%'),
                Photo.description.ilike(f'%{query}%'),
                # 通过标签搜索
                Photo.id.in_(
                    db.query(PhotoTag.photo_id).join(Tag).filter(Tag.name.ilike(f'%{query}%'))
                )
            )

            total = db.query(func.count(Photo.id)).filter(search_filter).scalar() or 0
            photos = db.query(Photo).filter(search_filter).offset(skip).limit(limit).all()

            return photos, total

        except Exception as e:
            self.logger.error(f"搜索照片失败 query='{query}': {str(e)}")
            return [], 0

    def get_photos_by_category(self, db: Session, category_id: int,
                              skip: int = 0, limit: int = 50) -> Tuple[List[Photo], int]:
        """
        获取分类下的照片

        Args:
            db: 数据库会话
            category_id: 分类ID
            skip: 跳过的记录数
            limit: 返回的记录数上限

        Returns:
            (照片列表, 总数)
        """
        try:
            query = db.query(Photo).join(PhotoCategory).filter(PhotoCategory.category_id == category_id)
            total = query.count()
            photos = query.offset(skip).limit(limit).all()

            return photos, total

        except Exception as e:
            self.logger.error(f"获取分类照片失败 category_id={category_id}: {str(e)}")
            return [], 0

    def get_photos_by_tag(self, db: Session, tag_id: int,
                         skip: int = 0, limit: int = 50) -> Tuple[List[Photo], int]:
        """
        获取标签下的照片

        Args:
            db: 数据库会话
            tag_id: 标签ID
            skip: 跳过的记录数
            limit: 返回的记录数上限

        Returns:
            (照片列表, 总数)
        """
        try:
            query = db.query(Photo).join(PhotoTag).filter(PhotoTag.tag_id == tag_id)
            total = query.count()
            photos = query.offset(skip).limit(limit).all()

            return photos, total

        except Exception as e:
            self.logger.error(f"获取标签照片失败 tag_id={tag_id}: {str(e)}")
            return [], 0

    def add_tags_to_photo(self, db: Session, photo_id: int, tag_names: List[str]) -> bool:
        """
        为照片添加标签

        Args:
            db: 数据库会话
            photo_id: 照片ID
            tag_names: 标签名称列表

        Returns:
            添加是否成功
        """
        try:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return False

            for tag_name in tag_names:
                # 获取或创建标签
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                    db.flush()

                # 检查是否已存在关联
                existing = db.query(PhotoTag).filter(
                    and_(PhotoTag.photo_id == photo_id, PhotoTag.tag_id == tag.id)
                ).first()

                if not existing:
                    photo_tag = PhotoTag(photo_id=photo_id, tag_id=tag.id)
                    db.add(photo_tag)

            db.commit()
            self.logger.info(f"为照片添加标签成功 photo_id={photo_id}, tags={tag_names}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"为照片添加标签失败 photo_id={photo_id}: {str(e)}")
            return False

    def remove_tags_from_photo(self, db: Session, photo_id: int, tag_names: List[str]) -> bool:
        """
        从照片移除标签

        Args:
            db: 数据库会话
            photo_id: 照片ID
            tag_names: 标签名称列表

        Returns:
            移除是否成功
        """
        try:
            for tag_name in tag_names:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if tag:
                    db.query(PhotoTag).filter(
                        and_(PhotoTag.photo_id == photo_id, PhotoTag.tag_id == tag.id)
                    ).delete()

            db.commit()
            self.logger.info(f"从照片移除标签成功 photo_id={photo_id}, tags={tag_names}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"从照片移除标签失败 photo_id={photo_id}: {str(e)}")
            return False

    def add_photo_to_categories(self, db: Session, photo_id: int, category_ids: List[int]) -> bool:
        """
        将照片添加到分类

        Args:
            db: 数据库会话
            photo_id: 照片ID
            category_ids: 分类ID列表

        Returns:
            添加是否成功
        """
        try:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return False

            for category_id in category_ids:
                # 检查分类是否存在
                category = db.query(Category).filter(Category.id == category_id).first()
                if not category:
                    continue

                # 检查是否已存在关联
                existing = db.query(PhotoCategory).filter(
                    and_(PhotoCategory.photo_id == photo_id, PhotoCategory.category_id == category_id)
                ).first()

                if not existing:
                    photo_category = PhotoCategory(photo_id=photo_id, category_id=category_id)
                    db.add(photo_category)

            db.commit()
            self.logger.info(f"将照片添加到分类成功 photo_id={photo_id}, categories={category_ids}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"将照片添加到分类失败 photo_id={photo_id}: {str(e)}")
            return False

    def remove_photo_from_categories(self, db: Session, photo_id: int, category_ids: List[int]) -> bool:
        """
        从分类移除照片

        Args:
            db: 数据库会话
            photo_id: 照片ID
            category_ids: 分类ID列表

        Returns:
            移除是否成功
        """
        try:
            for category_id in category_ids:
                db.query(PhotoCategory).filter(
                    and_(PhotoCategory.photo_id == photo_id, PhotoCategory.category_id == category_id)
                ).delete()

            db.commit()
            self.logger.info(f"从分类移除照片成功 photo_id={photo_id}, categories={category_ids}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"从分类移除照片失败 photo_id={photo_id}: {str(e)}")
            return False

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """
        应用筛选条件

        Args:
            query: 基础查询
            filters: 筛选条件字典

        Returns:
            应用筛选后的查询
        """
        try:
            # 状态筛选
            if "status" in filters:
                if isinstance(filters["status"], list):
                    # 支持多个状态筛选
                    query = query.filter(Photo.status.in_(filters["status"]))
                else:
                    # 单个状态筛选
                    query = query.filter(Photo.status == filters["status"])

            # 格式筛选
            if "format" in filters:
                query = query.filter(Photo.format == filters["format"])

            # 大小范围筛选
            if "min_size" in filters:
                query = query.filter(Photo.file_size >= filters["min_size"])
            if "max_size" in filters:
                query = query.filter(Photo.file_size <= filters["max_size"])

            # 时间范围筛选
            if "start_date" in filters:
                query = query.filter(Photo.created_at >= filters["start_date"])
            if "end_date" in filters:
                query = query.filter(Photo.created_at <= filters["end_date"])

            # 质量筛选
            if "min_quality" in filters:
                query = query.join(PhotoQuality).filter(PhotoQuality.quality_score >= filters["min_quality"])

            # 标签筛选
            if "tags" in filters and filters["tags"]:
                tag_names = filters["tags"] if isinstance(filters["tags"], list) else [filters["tags"]]
                for tag_name in tag_names:
                    query = query.join(PhotoTag).join(Tag).filter(Tag.name == tag_name)

            # 分类筛选
            if "categories" in filters and filters["categories"]:
                category_ids = filters["categories"] if isinstance(filters["categories"], list) else [filters["categories"]]
                for category_id in category_ids:
                    query = query.join(PhotoCategory).filter(PhotoCategory.category_id == category_id)

            return query

        except Exception as e:
            self.logger.error(f"应用筛选条件失败: {str(e)}")
            return query

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