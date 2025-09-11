"""
家庭单机版智能照片整理系统 - 分类标签服务
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, time
from app.core.logging import get_logger
from app.core.config import settings
from app.db.session import get_db
from app.models.photo import Photo, Category, Tag, PhotoCategory, PhotoTag, PhotoAnalysis
from sqlalchemy.orm import Session


class ClassificationService:
    """
    分类标签服务类
    负责照片的自动分类和标签管理
    """

    def __init__(self):
        """初始化分类标签服务"""
        self.logger = get_logger(__name__)

        # 预定义分类规则
        self.category_rules = {
            'scene': {
                '室内': ['室内', '房间', '客厅', '卧室', '厨房', '办公室'],
                '室外': ['室外', '户外', '公园', '街道', '广场', '山脉', '海边'],
                '风景': ['风景', '山水', '湖泊', '森林', '沙漠', '雪景'],
                '城市': ['城市', '建筑', '街道', '广场', '桥梁', '摩天大楼']
            },
            'activity': {
                '聚会': ['聚会', '派对', '庆祝', '生日', '婚礼', '节日'],
                '旅行': ['旅行', '度假', '出游', '公路旅行', '自驾游'],
                '运动': ['运动', '健身', '跑步', '游泳', '篮球', '足球'],
                '学习': ['学习', '读书', '写作', '会议', '培训'],
                '日常': ['日常', '家居', '生活', '工作', '购物']
            },
            'quality': {
                '优秀': lambda score: score >= 85,
                '良好': lambda score: 70 <= score < 85,
                '一般': lambda score: 50 <= score < 70,
                '较差': lambda score: score < 50
            }
        }

        # 中文标签映射
        self.chinese_tag_mapping = {
            'person': '人物',
            'people': '人物',
            'man': '男人',
            'woman': '女人',
            'child': '儿童',
            'baby': '婴儿',
            'family': '家庭',
            'group': '团体',
            'portrait': '肖像',
            'selfie': '自拍',

            'food': '食物',
            'meal': '餐食',
            'dinner': '晚餐',
            'lunch': '午餐',
            'breakfast': '早餐',
            'restaurant': '餐厅',
            'cake': '蛋糕',
            'pizza': '披萨',
            'coffee': '咖啡',

            'animal': '动物',
            'dog': '狗',
            'cat': '猫',
            'bird': '鸟',
            'pet': '宠物',

            'nature': '自然',
            'mountain': '山脉',
            'sea': '大海',
            'ocean': '海洋',
            'beach': '海滩',
            'forest': '森林',
            'tree': '树木',
            'flower': '花朵',
            'sky': '天空',
            'sunset': '日落',
            'sunrise': '日出',

            'building': '建筑',
            'house': '房屋',
            'office': '办公室',
            'school': '学校',
            'hospital': '医院',
            'church': '教堂',
            'temple': '寺庙',

            'vehicle': '交通工具',
            'car': '汽车',
            'bus': '公交车',
            'train': '火车',
            'airplane': '飞机',
            'bicycle': '自行车',

            'indoor': '室内',
            'outdoor': '室外',
            'night': '夜晚',
            'day': '白天',
            'sunny': '晴天',
            'cloudy': '多云',
            'rainy': '雨天'
        }

    def classify_photo(self, photo_id: int, db: Session = None) -> Dict[str, Any]:
        """
        对单张照片进行自动分类

        Args:
            photo_id: 照片ID
            db: 数据库会话

        Returns:
            分类结果字典
        """
        if db is None:
            db = next(get_db())

        try:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                raise Exception(f"照片不存在: {photo_id}")

            # 获取AI分析结果
            analysis_results = db.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id == photo_id
            ).all()

            # 基于AI分析结果进行分类
            classifications = self._analyze_and_classify(photo, analysis_results)

            # 保存分类结果
            saved_categories = self._save_classifications(photo_id, classifications, db)

            # 生成自动标签
            auto_tags = self._generate_auto_tags(photo, analysis_results)
            saved_tags = self._save_auto_tags(photo_id, auto_tags, db)

            return {
                'success': True,
                'photo_id': photo_id,
                'classifications': saved_categories,
                'tags': saved_tags,
                'message': f'照片分类完成，共生成 {len(saved_categories)} 个分类，{len(saved_tags)} 个标签'
            }

        except Exception as e:
            self.logger.error(f"照片分类失败: {e}")
            return {
                'success': False,
                'photo_id': photo_id,
                'error': str(e)
            }

    def _analyze_and_classify(self, photo: Photo, analysis_results: List[PhotoAnalysis]) -> List[Dict[str, Any]]:
        """
        基于AI分析结果进行分类

        Args:
            photo: 照片对象
            analysis_results: AI分析结果列表

        Returns:
            分类结果列表
        """
        classifications = []

        # 基于时间分类
        if photo.taken_at:
            time_classifications = self._classify_by_time(photo.taken_at)
            classifications.extend(time_classifications)

        # 基于AI分析结果分类
        for analysis in analysis_results:
            if analysis.analysis_type == 'content':  # 修正：AI分析类型是'content'
                content_classifications = self._classify_by_content(analysis.analysis_result)
                classifications.extend(content_classifications)
            elif analysis.analysis_type == 'quality':  # 修正：质量分析类型是'quality'
                quality_classifications = self._classify_by_quality(analysis.analysis_result)
                classifications.extend(quality_classifications)

        # 基于设备信息分类
        if photo.camera_make or photo.camera_model:
            device_classifications = self._classify_by_device(photo)
            classifications.extend(device_classifications)

        # 去重和合并相同分类
        unique_classifications = self._deduplicate_classifications(classifications)

        return unique_classifications

    def _classify_by_time(self, taken_at: datetime) -> List[Dict[str, Any]]:
        """基于时间进行分类"""
        classifications = []

        # 按年分类
        year_category = {
            'name': f'{taken_at.year}年',
            'type': 'time_year',
            'confidence': 1.0
        }
        classifications.append(year_category)

        # 按季节分类
        season_names = {
            'spring': '春季',
            'summer': '夏季',
            'autumn': '秋季',
            'winter': '冬季'
        }

        month = taken_at.month
        if month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        elif month in [9, 10, 11]:
            season = 'autumn'
        else:
            season = 'winter'

        season_category = {
            'name': season_names[season],
            'type': 'time_season',
            'confidence': 0.9
        }
        classifications.append(season_category)

        # 按时间段分类
        hour = taken_at.hour
        if 6 <= hour < 12:
            time_period = '上午'
        elif 12 <= hour < 18:
            time_period = '下午'
        elif 18 <= hour < 22:
            time_period = '晚上'
        else:
            time_period = '深夜'

        time_category = {
            'name': time_period,
            'type': 'time_period',
            'confidence': 0.8
        }
        classifications.append(time_category)

        return classifications

    def _classify_by_content(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于内容分析结果进行分类"""
        classifications = []

        if not analysis_result:
            return classifications

        # 场景分类
        scene_type = analysis_result.get('scene_type', '')
        if scene_type:
            for category_name, keywords in self.category_rules['scene'].items():
                if scene_type in keywords:
                    classifications.append({
                        'name': category_name,
                        'type': 'scene',
                        'confidence': 0.8
                    })
                    break

        # 活动分类
        activity = analysis_result.get('activity', '')
        if activity:
            for category_name, keywords in self.category_rules['activity'].items():
                if activity in keywords:
                    classifications.append({
                        'name': category_name,
                        'type': 'activity',
                        'confidence': 0.8
                    })
                    break

        return classifications

    def _classify_by_quality(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于质量评估进行分类"""
        classifications = []

        if not analysis_result:
            return classifications

        quality_score = analysis_result.get('quality_score', 0)
        for quality_level, condition_func in self.category_rules['quality'].items():
            if condition_func(quality_score):
                classifications.append({
                    'name': quality_level,
                    'type': 'quality',
                    'confidence': 0.9
                })
                break

        return classifications

    def _classify_by_device(self, photo: Photo) -> List[Dict[str, Any]]:
        """基于设备信息进行分类"""
        classifications = []

        if photo.camera_make:
            device_category = {
                'name': photo.camera_make,
                'type': 'device_make',
                'confidence': 1.0
            }
            classifications.append(device_category)

        if photo.camera_model:
            model_category = {
                'name': photo.camera_model,
                'type': 'device_model',
                'confidence': 1.0
            }
            classifications.append(model_category)

        return classifications

    def _deduplicate_classifications(self, classifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重和合并相同分类"""
        seen = {}
        for classification in classifications:
            name = classification['name']
            if name not in seen:
                seen[name] = classification
            else:
                # 保留置信度更高的分类
                if classification['confidence'] > seen[name]['confidence']:
                    seen[name] = classification

        return list(seen.values())

    def _generate_auto_tags(self, photo: Photo, analysis_results: List[PhotoAnalysis]) -> List[Dict[str, Any]]:
        """生成自动标签"""
        tags = []

        # 从AI分析结果中提取标签
        for analysis in analysis_results:
            if analysis.analysis_type == 'content':  # 修正：AI分析类型是'content'
                content_tags = self._extract_tags_from_content(analysis.analysis_result)
                tags.extend(content_tags)

        # 从EXIF信息生成标签
        exif_tags = self._extract_tags_from_exif(photo)
        tags.extend(exif_tags)

        # 去重和标准化
        normalized_tags = self._normalize_tags(tags)
        self.logger.info(f"最终生成的标签: {[t['name'] for t in normalized_tags]}")

        return normalized_tags

    def _extract_tags_from_content(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从内容分析结果中提取标签"""
        tags = []

        if not analysis_result:
            return tags

        # 使用AI分析结果中已经存在的标签
        ai_tags = analysis_result.get('tags', [])
        self.logger.info(f"AI分析结果中的标签: {ai_tags}")
        if ai_tags:
            for tag_name in ai_tags:
                tags.append({
                    'name': tag_name,
                    'type': 'ai_generated',
                    'confidence': 0.95
                })
        self.logger.info(f"从AI标签生成的标签: {[t['name'] for t in tags]}")

        # 从其他字段生成额外标签（无论是否有AI标签都执行）
        # 物体标签
        objects = analysis_result.get('objects', [])
        for obj in objects:
            chinese_name = self.chinese_tag_mapping.get(obj.lower(), obj)
            # 避免重复添加相同的标签
            if not any(tag['name'] == chinese_name for tag in tags):
                tags.append({
                    'name': chinese_name,
                    'type': 'object',
                    'confidence': 0.8
                })

        # 场景标签
        scene_type = analysis_result.get('scene_type', '')
        if scene_type:
            chinese_scene = self.chinese_tag_mapping.get(scene_type.lower(), scene_type)
            if not any(tag['name'] == chinese_scene for tag in tags):
                tags.append({
                    'name': chinese_scene,
                    'type': 'scene',
                    'confidence': 0.9
                })

        # 活动标签
        activity = analysis_result.get('activity', '')
        if activity:
            chinese_activity = self.chinese_tag_mapping.get(activity.lower(), activity)
            if not any(tag['name'] == chinese_activity for tag in tags):
                tags.append({
                    'name': chinese_activity,
                    'type': 'activity',
                    'confidence': 0.8
                })

        # 情感标签
        emotion = analysis_result.get('emotion', '')
        if emotion:
            chinese_emotion = self.chinese_tag_mapping.get(emotion.lower(), emotion)
            if not any(tag['name'] == chinese_emotion for tag in tags):
                tags.append({
                    'name': chinese_emotion,
                    'type': 'emotion',
                    'confidence': 0.85
                })

        return tags

    def _extract_tags_from_exif(self, photo: Photo) -> List[Dict[str, Any]]:
        """从EXIF信息生成标签"""
        tags = []

        # 设备标签
        if photo.camera_make:
            tags.append({
                'name': photo.camera_make,
                'type': 'device',
                'confidence': 1.0
            })

        if photo.camera_model:
            tags.append({
                'name': photo.camera_model,
                'type': 'device',
                'confidence': 1.0
            })

        # 镜头标签
        if photo.lens_model:
            tags.append({
                'name': photo.lens_model,
                'type': 'lens',
                'confidence': 1.0
            })

        # 拍摄参数标签
        if photo.aperture:
            tags.append({
                'name': f'f/{photo.aperture}',
                'type': 'aperture',
                'confidence': 1.0
            })

        if photo.focal_length:
            tags.append({
                'name': f'{photo.focal_length}mm',
                'type': 'focal_length',
                'confidence': 1.0
            })

        return tags

    def _normalize_tags(self, tags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """标签去重和标准化"""
        seen = {}
        for tag in tags:
            name = tag['name']
            if name not in seen:
                seen[name] = tag
            else:
                # 保留置信度更高的标签
                if tag['confidence'] > seen[name]['confidence']:
                    seen[name] = tag

        return list(seen.values())

    def _save_classifications(self, photo_id: int, classifications: List[Dict[str, Any]], db: Session) -> List[str]:
        """保存分类结果"""
        saved_categories = []

        for classification in classifications:
            # 查找或创建分类
            category = db.query(Category).filter(Category.name == classification['name']).first()
            if not category:
                category = Category(
                    name=classification['name'],
                    description=f'自动生成的{classification["type"]}分类'
                )
                db.add(category)
                # 不在这里提交，由调用方统一提交
                db.flush()  # 刷新以获取ID
                db.refresh(category)

            # 创建照片-分类关联
            photo_category = PhotoCategory(
                photo_id=photo_id,
                category_id=category.id,
                confidence=classification['confidence']
            )
            db.add(photo_category)

            saved_categories.append(classification['name'])

        # 不在这里提交，由调用方统一提交
        return saved_categories

    def _save_auto_tags(self, photo_id: int, tags: List[Dict[str, Any]], db: Session) -> List[str]:
        """保存自动标签"""
        saved_tags = []

        for tag_data in tags:
            # 查找或创建标签
            tag = db.query(Tag).filter(Tag.name == tag_data['name']).first()
            if not tag:
                tag = Tag(
                    name=tag_data['name'],
                    category=tag_data['type'],
                    description=f'自动生成的{tag_data["type"]}标签'
                )
                db.add(tag)
                # 不在这里提交，由调用方统一提交
                db.flush()  # 刷新以获取ID
                db.refresh(tag)

            # 创建照片-标签关联
            photo_tag = PhotoTag(
                photo_id=photo_id,
                tag_id=tag.id,
                confidence=tag_data['confidence'],
                source='auto'
            )
            db.add(photo_tag)
            
            # 更新标签使用次数
            tag.usage_count = (tag.usage_count or 0) + 1

            saved_tags.append(tag_data['name'])

        # 不在这里提交，由调用方统一提交
        return saved_tags

    def get_photo_classifications(self, photo_id: int, db: Session = None) -> List[Dict[str, Any]]:
        """获取照片的分类信息"""
        if db is None:
            db = next(get_db())

        try:
            photo_categories = db.query(PhotoCategory).filter(
                PhotoCategory.photo_id == photo_id
            ).join(Category).all()

            classifications = []
            for pc in photo_categories:
                classifications.append({
                    'id': pc.category.id,
                    'name': pc.category.name,
                    'type': pc.category.category_type,
                    'confidence': pc.confidence,
                    'created_at': pc.created_at.isoformat() if pc.created_at else None
                })

            return classifications

        except Exception as e:
            self.logger.error(f"获取照片分类失败: {e}")
            return []

    def get_photo_tags(self, photo_id: int, db: Session = None) -> List[Dict[str, Any]]:
        """获取照片的标签信息"""
        if db is None:
            db = next(get_db())

        try:
            photo_tags = db.query(PhotoTag).filter(
                PhotoTag.photo_id == photo_id
            ).join(Tag).all()

            tags = []
            for pt in photo_tags:
                tags.append({
                    'id': pt.tag.id,
                    'name': pt.tag.name,
                    'category': pt.tag.category,
                    'confidence': pt.confidence,
                    'source': pt.source,
                    'created_at': pt.created_at.isoformat() if pt.created_at else None
                })

            return tags

        except Exception as e:
            self.logger.error(f"获取照片标签失败: {e}")
            return []

    def create_manual_category(self, name: str, description: str = "", parent_id: int = None, db: Session = None) -> Dict[str, Any]:
        """创建手动分类"""
        if db is None:
            db = next(get_db())

        try:
            # 检查分类是否已存在
            existing_category = db.query(Category).filter(Category.name == name).first()
            if existing_category:
                return {
                    'success': False,
                    'error': '分类名称已存在'
                }

            category = Category(
                name=name,
                description=description,
                category_type='manual',
                parent_id=parent_id
            )
            db.add(category)
            db.commit()
            db.refresh(category)

            return {
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'type': category.category_type,
                    'parent_id': category.parent_id
                }
            }

        except Exception as e:
            self.logger.error(f"创建分类失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def add_manual_tag(self, photo_id: int, tag_name: str, db: Session = None) -> Dict[str, Any]:
        """为照片添加手动标签"""
        if db is None:
            db = next(get_db())

        try:
            # 查找或创建标签
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(
                    name=tag_name,
                    category='manual',
                    description='用户手动添加的标签'
                )
                db.add(tag)
                db.commit()
                db.refresh(tag)

            # 检查是否已经存在关联
            existing_association = db.query(PhotoTag).filter(
                PhotoTag.photo_id == photo_id,
                PhotoTag.tag_id == tag.id
            ).first()

            if existing_association:
                return {
                    'success': False,
                    'error': '标签已存在'
                }

            # 创建关联
            photo_tag = PhotoTag(
                photo_id=photo_id,
                tag_id=tag.id,
                confidence=1.0,
                source='manual'
            )
            db.add(photo_tag)
            db.commit()

            return {
                'success': True,
                'tag': {
                    'id': tag.id,
                    'name': tag.name,
                    'category': tag.category
                }
            }

        except Exception as e:
            self.logger.error(f"添加标签失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
