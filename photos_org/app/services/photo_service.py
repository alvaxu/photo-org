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

            # 性能优化：使用joinedload预加载关联数据，避免N+1查询
            from sqlalchemy.orm import joinedload
            query = query.options(
                joinedload(Photo.tags).joinedload(PhotoTag.tag),
                joinedload(Photo.categories).joinedload(PhotoCategory.category)
            )

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
            # 性能优化：使用joinedload预加载关联数据，避免N+1查询
            from sqlalchemy.orm import joinedload
            photo = db.query(Photo).options(
                joinedload(Photo.quality_assessments),
                joinedload(Photo.analysis_results),
                joinedload(Photo.tags).joinedload(PhotoTag.tag),
                joinedload(Photo.categories).joinedload(PhotoCategory.category)
            ).filter(Photo.id == photo_id).first()
            return photo
        except Exception as e:
            self.logger.error(f"获取照片失败 photo_id={photo_id}: {str(e)}")
            return None

    def create_photo(self, db: Session, photo_data: PhotoCreate, 
                     quality_result: Optional[Dict[str, Any]] = None,
                     exif_tags: Optional[List[Dict[str, Any]]] = None,
                     time_tags: Optional[List[Dict[str, Any]]] = None,
                     auto_commit: bool = True) -> Tuple[Optional[Photo], bool]:
        """
        创建照片记录

        :function: 创建照片记录，并可选择同时创建质量分析和标签
        :param db: 数据库会话
        :param photo_data: 照片数据
        :param quality_result: 质量分析结果（可选）
        :param exif_tags: EXIF标签列表（可选）
        :param time_tags: 时间标签列表（可选）
        :return: (photo, is_new): 照片对象和是否为新创建的标志
            - photo: Photo对象或None（失败时）
            - is_new: True表示新创建，False表示已存在（并发情况）
        """
        try:
            # 检查是否已存在相同哈希的照片
            existing_photo = db.query(Photo).filter(Photo.file_hash == photo_data.file_hash).first()
            if existing_photo:
                self.logger.warning(f"照片已存在，跳过创建: {photo_data.filename}")
                return existing_photo, False  # 返回已存在的记录，is_new=False
            
            # 将Pydantic模型转换为字典
            photo_dict = photo_data.dict()
            
            # 创建Photo对象
            photo = Photo(**photo_dict)
            
            # 保存到数据库（先保存以获取photo_id）
            db.add(photo)
            db.flush()  # 刷新以获取photo_id，但不提交（等待质量分析和标签一起提交）
            db.refresh(photo)
            
            # 阶段一：在同一个事务中创建质量分析和标签
            try:
                # 1. 创建质量分析记录
                quality_analysis_success = False
                if quality_result:
                    from app.models.photo import PhotoQuality
                    technical_issues = quality_result.get("technical_issues", {})
                    if isinstance(technical_issues, list):
                        technical_issues_data = {
                            "issues": technical_issues,
                            "count": len(technical_issues),
                            "has_issues": len(technical_issues) > 0
                        }
                    else:
                        technical_issues_data = technical_issues
                    
                    # 检查质量分析结果是否有效（包含quality_score）
                    if quality_result.get("quality_score") is not None:
                        quality_record = PhotoQuality(
                            photo_id=photo.id,
                            quality_score=quality_result.get("quality_score"),
                            sharpness_score=quality_result.get("sharpness_score"),
                            brightness_score=quality_result.get("brightness_score"),
                            contrast_score=quality_result.get("contrast_score"),
                            color_score=quality_result.get("color_score"),
                            composition_score=quality_result.get("composition_score"),
                            quality_level=quality_result.get("quality_level"),
                            technical_issues=technical_issues_data
                        )
                        db.add(quality_record)
                        quality_analysis_success = True
                
                # 2. 创建标签记录（EXIF标签 + 时间标签）
                all_tags = []
                if exif_tags:
                    all_tags.extend(exif_tags)
                if time_tags:
                    all_tags.extend(time_tags)
                
                if all_tags:
                    from app.models.photo import Tag, PhotoTag
                    from app.services.classification_service import ClassificationService
                    classification_service = ClassificationService()
                    # 使用ClassificationService的_save_auto_tags方法保存标签
                    saved_tags = classification_service._save_auto_tags(photo.id, all_tags, db)
                    self.logger.debug(f"为照片创建标签成功 photo_id={photo.id}, tags={saved_tags}")
                
                # 3. 根据质量分析结果更新status
                # 如果质量分析成功，status更新为'quality_completed'；否则保持'imported'
                if quality_analysis_success:
                    photo.status = 'quality_completed'
                    self.logger.debug(f"照片质量分析成功，status更新为quality_completed photo_id={photo.id}")
                # 如果质量分析失败或不存在，保持status为'imported'（已在create_photo_record中设置）
                
            except Exception as tag_error:
                # 标签创建失败不影响照片创建，只记录日志
                self.logger.warning(f"创建质量分析或标签失败 photo_id={photo.id}: {str(tag_error)}")
                # 如果质量分析失败，保持status为'imported'
            
            # 提交所有更改（照片 + 质量分析 + 标签 + status更新）
            if auto_commit:
                db.commit()
            
            self.logger.info(f"照片创建成功: {photo.filename}")
            return photo, True  # 返回新创建的记录，is_new=True
            
        except Exception as e:
            # 批次模式下不自动回滚，由调用方处理
            if auto_commit:
                db.rollback()
            # 检查是否是唯一约束冲突（file_hash重复）
            from sqlalchemy.exc import IntegrityError
            if isinstance(e, IntegrityError):
                # 并发导入时可能发生：两个线程同时检查都看不到记录，都尝试插入
                # 第二个会触发唯一约束冲突，此时查询已存在的记录并返回
                existing_photo = db.query(Photo).filter(Photo.file_hash == photo_data.file_hash).first()
                if existing_photo:
                    self.logger.warning(f"照片已存在（并发冲突），跳过创建: {photo_data.filename}")
                    return existing_photo, False  # 返回已存在的记录，is_new=False
            
            self.logger.error(f"创建照片失败: {str(e)}")
            return None, False

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
            
            # 🔥 新增：清理相似照片聚类相关数据
            self._cleanup_similar_photo_cluster_data(db, photo_id)

            # 删除物理文件
            if delete_file:
                try:
                    # 构建完整的文件路径（使用最新配置）
                    from app.core.config import get_settings
                    from app.core.path_utils import resolve_resource_path
                    current_settings = get_settings()
                    storage_base = resolve_resource_path(current_settings.storage.base_path)
                    full_original_path = storage_base / photo.original_path
                    
                    # 删除原图（JPEG或其他格式）
                    if full_original_path.exists():
                        os.remove(full_original_path)
                        self.logger.info(f"已删除原图文件: {full_original_path}")
                    
                    # 如果是HEIC格式，还需要删除HEIC原图（与JPEG在同一目录，扩展名为.heic）
                    is_heic = photo.format and photo.format.upper() in ['HEIC', 'HEIF']
                    if is_heic:
                        # HEIC原图与JPEG在同一目录，只需修改扩展名
                        heic_original_path = full_original_path.with_suffix('.heic')
                        if heic_original_path.exists():
                            os.remove(heic_original_path)
                            self.logger.info(f"已删除HEIC原图文件: {heic_original_path}")
                        else:
                            self.logger.warning(f"HEIC原图文件不存在: {heic_original_path}")

                    # 删除缩略图
                    if photo.thumbnail_path:
                        full_thumbnail_path = storage_base / photo.thumbnail_path
                        if full_thumbnail_path.exists():
                            os.remove(full_thumbnail_path)
                            self.logger.info(f"已删除缩略图文件: {full_thumbnail_path}")

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

    def _cleanup_similar_photo_cluster_data(self, db: Session, photo_id: int):
        """
        清理照片相关的相似照片聚类数据
        
        Args:
            db: 数据库会话
            photo_id: 照片ID
        """
        try:
            # 1. 获取该照片所属的所有聚类
            cluster_members = db.query(DuplicateGroupPhoto).filter(
                DuplicateGroupPhoto.photo_id == photo_id
            ).all()
            
            if not cluster_members:
                return  # 没有聚类数据，直接返回
            
            affected_cluster_ids = set()
            for member in cluster_members:
                affected_cluster_ids.add(member.cluster_id)
            
            self.logger.info(f"清理照片 {photo_id} 的相似照片聚类数据，涉及 {len(affected_cluster_ids)} 个聚类")
            
            # 2. 删除聚类成员记录
            deleted_members = db.query(DuplicateGroupPhoto).filter(
                DuplicateGroupPhoto.photo_id == photo_id
            ).delete(synchronize_session=False)
            
            if deleted_members > 0:
                self.logger.info(f"删除了 {deleted_members} 个聚类成员记录")
            
            # 3. 更新受影响的聚类的photo_count，如果只剩1张或0张则删除聚类
            deleted_cluster_ids = []
            for cluster_id in affected_cluster_ids:
                cluster = db.query(DuplicateGroup).filter(
                    DuplicateGroup.cluster_id == cluster_id
                ).first()
                
                if cluster:
                    # 重新计算聚类中的照片数量
                    remaining_count = db.query(DuplicateGroupPhoto).filter(
                        DuplicateGroupPhoto.cluster_id == cluster_id
                    ).count()
                    
                    # 如果只剩1张或0张照片，删除聚类
                    if remaining_count <= 1:
                        # 删除剩余的聚类成员记录（如果有）
                        db.query(DuplicateGroupPhoto).filter(
                            DuplicateGroupPhoto.cluster_id == cluster_id
                        ).delete()
                        # 删除聚类
                        db.delete(cluster)
                        deleted_cluster_ids.append(cluster_id)
                        self.logger.info(f"聚类 {cluster_id} 只剩 {remaining_count} 张照片，已自动删除")
                    else:
                        cluster.photo_count = remaining_count
                        self.logger.info(f"更新聚类 {cluster_id} 的照片数量为: {remaining_count}")
            
            # 如果有被删除的聚类，记录日志
            if deleted_cluster_ids:
                self.logger.info(f"因照片数量不足，已删除 {len(deleted_cluster_ids)} 个聚类: {deleted_cluster_ids}")
            
            self.logger.info(f"照片 {photo_id} 的相似照片聚类数据清理完成")
            
        except Exception as e:
            self.logger.error(f"清理相似照片聚类数据失败 photo_id={photo_id}: {str(e)}")
            raise  # 重新抛出异常，让上层处理

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
                
                # 🔥 更新聚类的人脸数量
                cluster.face_count = remaining_members
                
                if remaining_members == 0:
                    # 🔥 直接删除空聚类（简化逻辑）
                    self.logger.info(f"删除空聚类: {cluster_id} (命名: {cluster.person_name or '未命名'})")
                    db.delete(cluster)
                else:
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

    def batch_edit_photos(self, db: Session, request) -> Tuple[int, List[int], Dict[str, Any]]:
        """
        批量编辑照片

        Args:
            db: 数据库会话
            request: 批量编辑请求对象（BatchEditRequest）

        Returns:
            (成功编辑数量, 失败的ID列表, 详细操作结果)
        """
        successful_edits = 0
        failed_ids = []
        details = {
            'tags_updated': 0,
            'categories_updated': 0,
            'taken_at_updated': 0,
            'taken_at_filled': 0,
            'location_name_updated': 0,
            'location_name_filled': 0,
            'description_updated': 0,
            'description_appended': 0,
            'filename_updated': 0
        }

        for photo_id in request.photo_ids:
            try:
                photo = self.get_photo_by_id(db, photo_id)
                if not photo:
                    failed_ids.append(photo_id)
                    continue

                update_data = {}
                
                # 处理拍摄时间
                if request.taken_at_operation:
                    if request.taken_at_operation == 'set':
                        # 覆盖模式：为所有照片设置拍摄时间
                        if request.taken_at:
                            try:
                                taken_at_str = request.taken_at.strip()
                                if len(taken_at_str) == 19:
                                    update_data["taken_at"] = datetime.strptime(taken_at_str, '%Y-%m-%dT%H:%M:%S')
                                elif len(taken_at_str) == 16:
                                    update_data["taken_at"] = datetime.strptime(taken_at_str, '%Y-%m-%dT%H:%M')
                                else:
                                    parsed = datetime.fromisoformat(taken_at_str.replace('Z', '+00:00'))
                                    update_data["taken_at"] = parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
                                details['taken_at_updated'] += 1
                            except (ValueError, TypeError) as e:
                                self.logger.warning(f"照片 {photo_id} 拍摄时间解析失败: {e}")
                        else:
                            update_data["taken_at"] = None
                            details['taken_at_updated'] += 1
                    elif request.taken_at_operation == 'fill_empty':
                        # 填充模式：只更新空值
                        if not photo.taken_at and request.taken_at:
                            try:
                                taken_at_str = request.taken_at.strip()
                                if len(taken_at_str) == 19:
                                    update_data["taken_at"] = datetime.strptime(taken_at_str, '%Y-%m-%dT%H:%M:%S')
                                elif len(taken_at_str) == 16:
                                    update_data["taken_at"] = datetime.strptime(taken_at_str, '%Y-%m-%dT%H:%M')
                                else:
                                    parsed = datetime.fromisoformat(taken_at_str.replace('Z', '+00:00'))
                                    update_data["taken_at"] = parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
                                details['taken_at_filled'] += 1
                            except (ValueError, TypeError) as e:
                                self.logger.warning(f"照片 {photo_id} 拍摄时间解析失败: {e}")
                    elif request.taken_at_operation == 'clear':
                        # 清空模式
                        update_data["taken_at"] = None
                        details['taken_at_updated'] += 1

                # 处理位置
                if request.location_name_operation:
                    if request.location_name_operation == 'set':
                        update_data["location_name"] = request.location_name
                        details['location_name_updated'] += 1
                    elif request.location_name_operation == 'fill_empty':
                        if not photo.location_name and request.location_name:
                            update_data["location_name"] = request.location_name
                            details['location_name_filled'] += 1
                    elif request.location_name_operation == 'clear':
                        update_data["location_name"] = None
                        details['location_name_updated'] += 1

                # 处理描述
                if request.description_operation:
                    if request.description_operation == 'set':
                        update_data["description"] = request.description
                        details['description_updated'] += 1
                    elif request.description_operation == 'append':
                        if request.description:
                            if photo.description:
                                update_data["description"] = photo.description + request.description
                            else:
                                update_data["description"] = request.description
                            details['description_appended'] += 1
                    elif request.description_operation == 'clear':
                        update_data["description"] = None
                        details['description_updated'] += 1

                # 处理文件名
                if request.filename_operation:
                    import os
                    if request.filename_operation == 'add_prefix':
                        # 添加前缀模式
                        if request.filename_prefix:
                            # 获取原文件名的扩展名
                            name, ext = os.path.splitext(photo.filename)
                            new_filename = f"{request.filename_prefix}{name}{ext}"
                            update_data["filename"] = new_filename
                            details['filename_updated'] += 1
                    elif request.filename_operation == 'add_suffix':
                        # 添加后缀模式（在扩展名前）
                        if request.filename_suffix:
                            name, ext = os.path.splitext(photo.filename)
                            new_filename = f"{name}{request.filename_suffix}{ext}"
                            update_data["filename"] = new_filename
                            details['filename_updated'] += 1
                    elif request.filename_operation == 'set':
                        # 统一重命名模式（带序号）
                        if request.filename_template:
                            # 获取文件扩展名（保留原扩展名）
                            _, ext = os.path.splitext(photo.filename)
                            # 获取起始序号（默认为1）
                            start_index = request.filename_start_index if hasattr(request, 'filename_start_index') and request.filename_start_index is not None else 1
                            if start_index < 1:
                                start_index = 1  # 确保起始序号至少为1
                            # 计算当前照片在批量列表中的序号（从指定起始值开始）
                            index = request.photo_ids.index(photo_id) + start_index
                            # 替换模板中的{序号}占位符
                            new_filename = request.filename_template.replace('{序号}', str(index))
                            new_filename = new_filename.replace('{index}', str(index))  # 兼容英文
                            # 如果模板中没有扩展名，则添加原扩展名
                            if not os.path.splitext(new_filename)[1]:
                                new_filename += ext
                            update_data["filename"] = new_filename
                            details['filename_updated'] += 1

                # 阶段二：检查是否更新了taken_at，如果更新了，自动更新时间标签
                taken_at_updated = False
                new_taken_at = None
                old_taken_at = photo.taken_at  # 保存原始值用于比较
                
                if 'taken_at' in update_data:
                    new_taken_at = update_data.get('taken_at')
                    # 判断值是否实际变化（考虑None的情况）
                    if old_taken_at != new_taken_at:
                        taken_at_updated = True
                
                # 更新基本信息
                if update_data:
                    for key, value in update_data.items():
                        if hasattr(photo, key):
                            setattr(photo, key, value)
                    photo.updated_at = datetime.now()
                
                # 阶段二：如果taken_at已更新，自动更新时间标签（在db.commit()之前）
                if taken_at_updated:
                    try:
                        from app.services.classification_service import ClassificationService
                        from app.models.photo import Tag, PhotoTag
                        from sqlalchemy import and_
                        
                        classification_service = ClassificationService()
                        
                        # 1. 删除旧的时间标签（category='time'的标签）
                        time_tags = db.query(Tag).filter(Tag.category == 'time').all()
                        time_tag_ids = [tag.id for tag in time_tags]
                        
                        if time_tag_ids:
                            # 删除该照片的所有时间标签关联
                            db.query(PhotoTag).filter(
                                and_(
                                    PhotoTag.photo_id == photo_id,
                                    PhotoTag.tag_id.in_(time_tag_ids)
                                )
                            ).delete(synchronize_session=False)
                        
                        # 2. 生成新的时间标签（如果new_taken_at不为None）
                        if new_taken_at:
                            self.logger.debug(f"批量编辑：开始生成新时间标签 photo_id={photo_id}, new_taken_at={new_taken_at}")
                            new_time_tags = classification_service.generate_time_tags_from_datetime(new_taken_at)
                            self.logger.debug(f"批量编辑：生成的时间标签数量: {len(new_time_tags) if new_time_tags else 0}, tags={[tag.get('name') for tag in new_time_tags] if new_time_tags else []}")
                            if new_time_tags:
                                # 使用ClassificationService的_save_auto_tags方法保存新标签
                                saved_tags = classification_service._save_auto_tags(photo_id, new_time_tags, db)
                                self.logger.info(f"批量编辑：为照片添加时间标签成功 photo_id={photo_id}, tags={saved_tags}")
                            else:
                                self.logger.warning(f"批量编辑：生成的时间标签为空 photo_id={photo_id}, new_taken_at={new_taken_at}")
                        else:
                            self.logger.debug(f"批量编辑：new_taken_at为None，不生成新时间标签 photo_id={photo_id}")
                    except Exception as e:
                        self.logger.warning(f"批量编辑：自动更新时间标签失败 photo_id={photo_id}: {str(e)}")
                        # 时间标签更新失败不影响照片更新，只记录日志

                # 处理标签
                if request.tags_operation:
                    if request.tags_operation == 'add':
                        # 追加标签（不提交，由外层统一提交）
                        if request.tags:
                            self.add_tags_to_photo(db, photo_id, request.tags, auto_commit=False)
                            details['tags_updated'] += 1
                    elif request.tags_operation == 'remove':
                        # 移除指定标签（不提交，由外层统一提交）
                        if request.tags_to_remove:
                            self.remove_tags_from_photo(db, photo_id, request.tags_to_remove, auto_commit=False)
                            details['tags_updated'] += 1
                    elif request.tags_operation == 'replace':
                        # 替换所有标签（保留原有标签的source）
                        existing_tags_source = {}
                        if photo.tags:
                            for photo_tag in photo.tags:
                                existing_tags_source[photo_tag.tag.name] = photo_tag.source
                        self.remove_tags_from_photo(db, photo_id, [tag.tag.name for tag in photo.tags] if photo.tags else [], auto_commit=False)
                        if request.tags:
                            self.add_tags_to_photo(db, photo_id, request.tags, tags_with_source=existing_tags_source, auto_commit=False)
                        details['tags_updated'] += 1
                    elif request.tags_operation == 'clear':
                        # 清空所有标签（不提交，由外层统一提交）
                        if photo.tags:
                            self.remove_tags_from_photo(db, photo_id, [tag.tag.name for tag in photo.tags], auto_commit=False)
                            details['tags_updated'] += 1

                # 处理分类
                if request.categories_operation:
                    if request.categories_operation == 'add':
                        # 追加分类（不提交，由外层统一提交）
                        if request.category_ids:
                            self.add_photo_to_categories(db, photo_id, request.category_ids, auto_commit=False)
                            details['categories_updated'] += 1
                    elif request.categories_operation == 'remove':
                        # 移除指定分类（不提交，由外层统一提交）
                        if request.category_ids_to_remove:
                            self.remove_photo_from_categories(db, photo_id, request.category_ids_to_remove, auto_commit=False)
                            details['categories_updated'] += 1
                    elif request.categories_operation == 'replace':
                        # 替换所有分类
                        existing_category_ids = [cat.id for cat in photo.categories] if photo.categories else []
                        if existing_category_ids:
                            self.remove_photo_from_categories(db, photo_id, existing_category_ids, auto_commit=False)
                        if request.category_ids:
                            self.add_photo_to_categories(db, photo_id, request.category_ids, auto_commit=False)
                        details['categories_updated'] += 1
                    elif request.categories_operation == 'clear':
                        # 清空所有分类（不提交，由外层统一提交）
                        if photo.categories:
                            self.remove_photo_from_categories(db, photo_id, [cat.id for cat in photo.categories], auto_commit=False)
                            details['categories_updated'] += 1

                # 提交更改
                db.commit()
                successful_edits += 1

            except Exception as e:
                db.rollback()
                self.logger.error(f"批量编辑照片失败 photo_id={photo_id}: {str(e)}")
                failed_ids.append(photo_id)

        self.logger.info(f"批量编辑完成: {successful_edits}成功, {len(failed_ids)}失败")
        return successful_edits, failed_ids, details

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
            
            # 性能优化：使用joinedload预加载关联数据，避免N+1查询
            from sqlalchemy.orm import joinedload
            photos = db.query(Photo).options(
                joinedload(Photo.tags).joinedload(PhotoTag.tag),
                joinedload(Photo.categories).joinedload(PhotoCategory.category)
            ).filter(search_filter).offset(skip).limit(limit).all()

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
            
            # 性能优化：使用joinedload预加载关联数据，避免N+1查询
            from sqlalchemy.orm import joinedload
            photos = query.options(
                joinedload(Photo.tags).joinedload(PhotoTag.tag),
                joinedload(Photo.categories).joinedload(PhotoCategory.category)
            ).offset(skip).limit(limit).all()

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
            
            # 性能优化：使用joinedload预加载关联数据，避免N+1查询
            from sqlalchemy.orm import joinedload
            photos = query.options(
                joinedload(Photo.tags).joinedload(PhotoTag.tag),
                joinedload(Photo.categories).joinedload(PhotoCategory.category)
            ).offset(skip).limit(limit).all()

            return photos, total

        except Exception as e:
            self.logger.error(f"获取标签照片失败 tag_id={tag_id}: {str(e)}")
            return [], 0

    def add_tags_to_photo(self, db: Session, photo_id: int, tag_names: List[str], tags_with_source: Optional[Dict[str, str]] = None, auto_commit: bool = True) -> bool:
        """
        为照片添加标签

        Args:
            db: 数据库会话
            photo_id: 照片ID
            tag_names: 标签名称列表
            tags_with_source: 标签名称到source的映射（用于保留原有标签的source）

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
                    # 🔥 修复：根据原有标签的source信息设置source，如果是新标签则设为'manual'
                    source = 'manual'  # 默认为'manual'（用户手动添加）
                    if tags_with_source and tag_name in tags_with_source:
                        # 保留原有标签的source（'auto'或'manual'）
                        source = tags_with_source[tag_name]
                    
                    photo_tag = PhotoTag(photo_id=photo_id, tag_id=tag.id, source=source)
                    db.add(photo_tag)

            if auto_commit:
                db.commit()
            self.logger.info(f"为照片添加标签成功 photo_id={photo_id}, tags={tag_names}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"为照片添加标签失败 photo_id={photo_id}: {str(e)}")
            return False

    def remove_tags_from_photo(self, db: Session, photo_id: int, tag_names: List[str], auto_commit: bool = True) -> bool:
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

            if auto_commit:
                db.commit()
            self.logger.info(f"从照片移除标签成功 photo_id={photo_id}, tags={tag_names}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"从照片移除标签失败 photo_id={photo_id}: {str(e)}")
            return False

    def add_photo_to_categories(self, db: Session, photo_id: int, category_ids: List[int], auto_commit: bool = True) -> bool:
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

            if auto_commit:
                db.commit()
            self.logger.info(f"将照片添加到分类成功 photo_id={photo_id}, categories={category_ids}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"将照片添加到分类失败 photo_id={photo_id}: {str(e)}")
            return False

    def remove_photo_from_categories(self, db: Session, photo_id: int, category_ids: List[int], auto_commit: bool = True) -> bool:
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

            if auto_commit:
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
                format_filter = filters["format"]
                # 处理合并格式：TIFF/TIF 和 HEIC/HEIF
                if format_filter == 'TIFF/TIF':
                    query = query.filter(Photo.format.in_(['TIFF', 'TIF']))
                elif format_filter == 'HEIC/HEIF':
                    query = query.filter(Photo.format.in_(['HEIC', 'HEIF']))
                else:
                    query = query.filter(Photo.format == format_filter)

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