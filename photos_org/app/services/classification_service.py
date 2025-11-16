"""
家庭版智能照片系统 - 分类标签服务
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

        # 新分类规则（5个主要分类，相册概念）
        self.album_categories = {
            '家庭照片': {
                'keywords': ['家庭', '家人', '孩子', '父母', '夫妻', '亲子', '家庭聚会', '孩子玩耍', '亲子活动'],
                'objects': ['人', '人物', '家庭', '孩子', '婴儿', '人像', '肖像', '自拍', '合影'],
                'location': ['家庭', '家里', '客厅', '卧室', '厨房', '家庭家里'],
                'activity': ['家庭聚会', '孩子玩耍', '亲子活动']
            },
            '旅行照片': {
                'keywords': ['旅行', '旅游', '度假', '出游', '景点', '风景', '旅行旅游', '度假出游', '景点观光'],
                'objects': ['风景', '建筑', '地标', '景点', '酒店', '山水', '湖泊', '森林', '城市建筑', '桥梁'],
                'location': ['户外', '景点', '酒店', '机场', '车站', '户外公园', '街道', '广场', '旅行景点'],
                'activity': ['旅行旅游', '度假出游', '景点观光']
            },
            '工作照片': {
                'keywords': ['工作', '办公', '会议', '商务', '出差', '工作办公', '会议商务', '出差培训'],
                'objects': ['办公室', '电脑', '文件', '会议室'],
                'location': ['办公室', '会议室', '商务场所', '办公室', '会议室'],
                'activity': ['工作办公', '会议商务', '出差培训']
            },
            '社交活动': {
                'keywords': ['聚会', '派对', '聚餐', '庆祝', '生日', '婚礼', '社交聚会', '派对聚餐', '庆祝生日', '婚礼节日'],
                'objects': ['蛋糕', '礼物', '装饰', '人群'],
                'location': ['餐厅', '餐厅'],
                'activity': ['社交聚会', '派对聚餐', '庆祝生日', '婚礼节日']
            },
            '日常生活': {
                'keywords': ['日常', '生活', '购物', '休闲', '日常购物', '休闲娱乐', '运动健身', '学习读书'],
                'objects': ['食物', '商品', '日常用品'],
                'location': ['户外公园', '街道', '广场'],
                'activity': ['日常购物', '休闲娱乐', '运动健身', '学习读书']
            }
        }

        # 标签规则（多维度标签）
        self.tag_rules = {
            'scene_tags': {
                '室内': ['室内房间', '客厅', '卧室', '厨房', '办公室'],
                '室外': ['户外公园', '街道', '广场', '庭院', '阳台'],
                '风景': ['山水', '湖泊', '森林', '沙漠', '雪景', '海滩', '山脉'],
                '城市': ['建筑', '桥梁', '摩天大楼', '商业区', '住宅区'],
                '人物': ['人像', '肖像', '自拍', '合影', '单人', '多人'],
                '自然': ['植物', '动物', '花卉', '树木', '天空', '云朵', '星空']
            },
            'activity_tags': {
                '聚会': ['派对', '聚餐', '宴会', '庆祝', '生日', '婚礼', '节日'],
                '旅行': ['旅游', '度假', '出游', '公路旅行', '自驾游', '观光'],
                '运动': ['健身', '跑步', '游泳', '篮球', '足球', '瑜伽', '骑行'],
                '学习': ['读书', '写作', '研究', '考试', '上课', '图书馆'],
                '工作': ['办公', '会议', '商务', '出差', '培训', '讲座'],
                '休闲': ['放松', '休息', '娱乐', '游戏', '观影', '听音乐'],
                '购物': ['逛街', '商场', '超市', '市场', '采购']
            },
            'time_tags': {
                '季节': ['春季', '夏季', '秋季', '冬季'],
                '时段': ['上午', '下午', '晚上', '深夜'],
                '节假日': ['春节', '中秋', '国庆', '五一', '端午', '清明', '元旦', '情人节', '圣诞节']
            },
            'quality_tags': {
                '优秀': lambda score: score >= 85,
                '良好': lambda score: 70 <= score < 85,
                '一般': lambda score: 50 <= score < 70,
                '较差': lambda score: score < 50
            },
            'emotion_tags': {
                '欢乐': ['开心', '快乐', '兴奋', '愉快'],
                '宁静': ['安静', '平和', '放松', '舒适'],
                '怀旧': ['回忆', '温馨', '感动', '怀念'],
                '兴奋': ['激动', '刺激', '紧张', '期待']
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

            # 根据分析结果类型生成相应的标签
            auto_tags = []

            # 检查是否有质量分析结果
            quality_analysis = None
            for analysis in analysis_results:
                if analysis.analysis_type == 'quality':
                    quality_analysis = analysis.analysis_result
                    break

            # 检查是否有内容分析结果
            content_analysis = None
            for analysis in analysis_results:
                if analysis.analysis_type == 'content':
                    content_analysis = analysis.analysis_result
                    break

            # 生成基础标签（如果有质量分析结果）
            if quality_analysis:
                basic_tags = self.generate_basic_tags(photo, quality_analysis, db)
                auto_tags.extend(basic_tags)

            # 生成AI标签（如果有内容分析结果）
            if content_analysis:
                ai_tags = self.generate_ai_tags(content_analysis)
                auto_tags.extend(ai_tags)

            saved_tags = self._save_auto_tags(photo_id, auto_tags, db) if auto_tags else []

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
        基于AI分析结果进行分类（多维度分类：内容分类 + 质量分类 + 设备分类）

        Args:
            photo: 照片对象
            analysis_results: AI分析结果列表

        Returns:
            分类结果列表（包含内容分类、质量分类、设备分类）
        """
        classifications = []

        # 1. 内容分类（相册概念，主要分类）
        assigned_category = self._assign_to_category(photo, analysis_results)
        if assigned_category:
            classifications.append({
                'name': assigned_category,
                'type': 'content',
                'confidence': 0.9
            })
        else:
            # 默认分配到"日常生活"分类
            classifications.append({
                'name': '日常生活',
                'type': 'content',
                'confidence': 0.5
            })
        
        # 2. 质量分类
        quality_classification = self._classify_by_quality(analysis_results)
        if quality_classification:
            classifications.append(quality_classification)
        
        # 3. 设备分类
        device_classification = self._classify_by_device(photo)
        if device_classification:
            classifications.append(device_classification)

        return classifications

    def _assign_to_category(self, photo: Photo, analysis_results: List[PhotoAnalysis]) -> str:
        """
        基于AI分析结果分配分类

        Args:
            photo: 照片对象
            analysis_results: AI分析结果列表

        Returns:
            分配的分类名称
        """
        # 按优先级匹配：家庭照片 → 旅行照片 → 工作照片 → 社交活动 → 日常生活
        for category_name, rules in self.album_categories.items():
            if self._matches_category_rules(photo, analysis_results, rules):
                return category_name
        return '日常生活'  # 默认分类

    def _classify_by_quality(self, analysis_results: List[PhotoAnalysis]) -> Dict[str, Any]:
        """
        基于质量分析结果进行质量分类
        
        Args:
            analysis_results: AI分析结果列表
            
        Returns:
            质量分类结果
        """
        for analysis in analysis_results:
            if analysis.analysis_type == 'quality':
                quality_score = analysis.analysis_result.get('quality_score', 0)
                
                if quality_score >= 85:
                    return {
                        'name': '优秀',
                        'type': 'quality',
                        'confidence': 0.9
                    }
                elif quality_score >= 70:
                    return {
                        'name': '良好',
                        'type': 'quality',
                        'confidence': 0.8
                    }
                elif quality_score >= 50:
                    return {
                        'name': '一般',
                        'type': 'quality',
                        'confidence': 0.7
                    }
                else:
                    return {
                        'name': '较差',
                        'type': 'quality',
                        'confidence': 0.6
                    }
        
        return None

    def _classify_by_device(self, photo: Photo) -> Dict[str, Any]:
        """
        基于EXIF信息进行设备分类
        
        Args:
            photo: 照片对象
            
        Returns:
            设备分类结果
        """
        device_info = []

        if photo.camera_make:
            device_info.append(photo.camera_make)
        if photo.camera_model:
            device_info.append(photo.camera_model)
        
        if device_info:
            device_name = ' '.join(device_info)
            return {
                'name': device_name,
                'type': 'device',
                'confidence': 1.0
            }
        
        return None

    def _matches_category_rules(self, photo: Photo, analysis_results: List[PhotoAnalysis], rules: Dict) -> bool:
        """
        检查照片是否匹配分类规则

        Args:
            photo: 照片对象
            analysis_results: AI分析结果列表
            rules: 分类规则

        Returns:
            是否匹配
        """
        for analysis in analysis_results:
            if analysis.analysis_type == 'content':
                analysis_result = analysis.analysis_result
                
                # 检查关键词匹配
                keywords = rules.get('keywords', [])
                for keyword in keywords:
                    if (keyword in analysis_result.get('description', '') or
                        keyword in analysis_result.get('activity', '') or
                        keyword in analysis_result.get('scene_type', '')):
                        return True
                
                # 检查对象匹配
                objects = rules.get('objects', [])
                ai_objects = analysis_result.get('objects', [])
                for obj in objects:
                    if any(obj in ai_obj for ai_obj in ai_objects):
                        return True
                
                # 检查地点匹配
                locations = rules.get('location', [])
                location_type = analysis_result.get('location_type', '')
                for location in locations:
                    if location in location_type:
                        return True
                
                # 检查活动匹配
                activities = rules.get('activity', [])
                activity = analysis_result.get('activity', '')
                for act in activities:
                    if act in activity:
                        return True
        
        return False





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
        """生成自动标签（多维度标签）"""
        tags = []

        # 从AI分析结果中提取标签
        for analysis in analysis_results:
            if analysis.analysis_type == 'content':
                content_tags = self._extract_tags_from_content(analysis.analysis_result)
                tags.extend(content_tags)

        # 添加时间标签（包括节假日）
        if photo.taken_at:
            time_tags = self._extract_time_tags(photo.taken_at)
            tags.extend(time_tags)

        # 添加质量标签
        for analysis in analysis_results:
            if analysis.analysis_type == 'quality':
                quality_tags = self._extract_quality_tags(analysis.analysis_result)
                tags.extend(quality_tags)

        # 从EXIF信息生成标签
        exif_tags = self._extract_tags_from_exif(photo)
        tags.extend(exif_tags)

        # 去重和标准化
        normalized_tags = self._normalize_tags(tags)
        # 标签生成日志已移除，减少日志输出

        return normalized_tags

    def generate_basic_tags(self, photo: Photo, quality_analysis: Optional[Dict] = None, db: Session = None) -> List[Dict[str, Any]]:
        """
        生成基础标签（非AI标签）
        包括：时间标签、质量标签、EXIF标签

        Args:
            photo: 照片对象
            quality_analysis: 质量分析结果（可选）
            db: 数据库会话

        Returns:
            基础标签列表
        """
        tags = []

        # 添加时间标签（包括节假日）
        if photo.taken_at:
            time_tags = self._extract_time_tags(photo.taken_at)
            tags.extend(time_tags)

        # 注意：质量信息不作为标签存储，而是在PhotoQuality表中作为专门字段

        # 从EXIF信息生成标签
        exif_tags = self._extract_tags_from_exif(photo)
        tags.extend(exif_tags)

        # 去重和标准化
        normalized_tags = self._normalize_tags(tags)

        return normalized_tags

    def generate_ai_tags(self, analysis_result: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        生成AI标签（基于AI内容分析）
        包括：场景标签、物体标签、活动标签、情感标签

        Args:
            analysis_result: AI内容分析结果

        Returns:
            AI标签列表
        """
        if not analysis_result:
            return []

        tags = []

        # 从AI分析结果中提取标签
        content_tags = self._extract_tags_from_content(analysis_result)
        tags.extend(content_tags)

        # 去重和标准化
        normalized_tags = self._normalize_tags(tags)

        return normalized_tags

    def generate_basic_classifications(self, photo: Photo) -> List[Dict[str, Any]]:
        """
        生成基础分类（非AI分类）

        注意：相机品牌和型号已存储在photo表中，无需生成设备分类

        Args:
            photo: 照片对象

        Returns:
            基础分类列表
        """
        classifications = []

        # 注意：不再生成设备分类，因为相机信息已存储在photo.camera_make和photo.camera_model字段中

        return classifications

    def generate_ai_classifications(self, photo: Photo, analysis_result: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        生成AI分类（基于AI内容分析）
        包括：内容分类、质量分类

        Args:
            photo: 照片对象
            analysis_result: AI内容分析结果

        Returns:
            AI分类列表
        """
        classifications = []

        # 内容分类（相册概念，主要分类）
        assigned_category = self._assign_to_category_from_analysis(analysis_result)
        if assigned_category:
            classifications.append({
                'name': assigned_category,
                'type': 'content',
                'confidence': 0.9
            })
        else:
            # 默认分配到"日常生活"分类
            classifications.append({
                'name': '日常生活',
                'type': 'content',
                'confidence': 0.5
            })

        # 质量分类（如果有质量分析结果）
        # 注意：质量分类需要质量分析结果，这里暂时不处理，因为质量分析在基础分析阶段完成

        return classifications

    def _assign_to_category_from_analysis(self, analysis_result: Optional[Dict]) -> Optional[str]:
        """
        基于AI分析结果分配到相册分类
        """
        if not analysis_result:
            return None

        # 提取关键词用于匹配
        keywords = []
        scene_type = analysis_result.get('scene_type', '')
        if scene_type:
            keywords.append(scene_type)

        objects = analysis_result.get('objects', [])
        keywords.extend(objects)

        activity = analysis_result.get('activity', '')
        if activity:
            keywords.append(activity)

        location_type = analysis_result.get('location_type', '')
        if location_type:
            keywords.append(location_type)

        emotions = analysis_result.get('emotions', [])
        keywords.extend(emotions)

        # 转换为小写以便匹配
        keywords_lower = [kw.lower() for kw in keywords]

        # 计算每个分类的匹配度
        category_scores = {}
        for category_name, category_rules in self.album_categories.items():
            score = 0

            # 检查关键词匹配
            for keyword in category_rules.get('keywords', []):
                if any(keyword.lower() in kw for kw in keywords_lower):
                    score += 2

            # 检查物体匹配
            for obj in category_rules.get('objects', []):
                if any(obj.lower() in kw for kw in keywords_lower):
                    score += 1.5

            # 检查位置匹配
            for location in category_rules.get('location', []):
                if any(location.lower() in kw for kw in keywords_lower):
                    score += 1

            # 检查活动匹配
            for activity_kw in category_rules.get('activity', []):
                if any(activity_kw.lower() in kw for kw in keywords_lower):
                    score += 1.5

            if score > 0:
                category_scores[category_name] = score

        # 返回匹配度最高的分类
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] >= 1:  # 设置最小匹配阈值
                return best_category[0]

        return None

    def _extract_tags_from_content(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从内容分析结果中提取标签（纯AI标签策略）"""
        tags = []

        if not analysis_result:
            return tags

        # 只使用AI生成的精质量标签，不补充任何结构化字段
        ai_tags = analysis_result.get('tags', [])
        if ai_tags and isinstance(ai_tags, list):
            for tag_name in ai_tags:
                if tag_name and isinstance(tag_name, str) and tag_name.strip():
                    tags.append({
                        'name': tag_name.strip(),
                        'type': 'ai_generated',
                        'confidence': 0.95,  # AI生成标签置信度较高
                        'source': 'ai_analysis'  # 标识AI标签来源
                    })

        # 不补充scene_type, activity, emotion, objects等结构化字段
        # 保持AI的原始标签意图，可能少于5个标签

        return tags

    def generate_exif_tags_from_metadata(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从metadata字典生成EXIF标签（镜头、光圈、焦距）

        :function: 从metadata字典中提取EXIF信息并生成标签，用于导入阶段
        :param metadata: 包含EXIF信息的metadata字典，可能包含lens_model、aperture、focal_length等字段
        :return: EXIF标签列表
        """
        tags = []

        # 镜头信息标签
        lens_model = metadata.get('lens_model') or metadata.get('lens')
        if lens_model:
            tags.append({
                'name': str(lens_model),
                'type': 'lens',
                'confidence': 1.0
            })

        # 光圈标签
        aperture = metadata.get('aperture') or metadata.get('f_number')
        if aperture:
            # 确保光圈值格式正确
            aperture_str = str(aperture)
            if not aperture_str.startswith('f/'):
                aperture_str = f'f/{aperture_str}'
            tags.append({
                'name': aperture_str,
                'type': 'aperture',
                'confidence': 1.0
            })

        # 焦距标签
        focal_length = metadata.get('focal_length')
        if focal_length:
            # 确保焦距值格式正确
            focal_str = str(focal_length)
            if not focal_str.endswith('mm'):
                focal_str = f'{focal_str}mm'
            tags.append({
                'name': focal_str,
                'type': 'focal_length',
                'confidence': 1.0
            })

        return tags

    def generate_time_tags_from_datetime(self, taken_at: datetime) -> List[Dict[str, Any]]:
        """
        从datetime对象生成时间标签（季节、时段、节假日）

        :function: 根据拍摄时间生成时间相关标签，用于导入阶段和taken_at更新时
        :param taken_at: 拍摄时间的datetime对象
        :return: 时间标签列表
        """
        if not taken_at:
            return []
        
        # 复用现有的_extract_time_tags方法
        return self._extract_time_tags(taken_at)

    def _extract_tags_from_exif(self, photo: Photo) -> List[Dict[str, Any]]:
        """从EXIF信息生成标签"""
        tags = []

        # 注意：相机品牌(camera_make)和型号(camera_model)已存储在photo表中，无需生成标签
        # 设备标签 - 只生成镜头信息
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
        created_count = 0
        updated_count = 0
        skipped_count = 0

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

            # 检查是否已存在相同的照片-标签关联，避免重复创建
            existing_photo_tag = db.query(PhotoTag).filter(
                PhotoTag.photo_id == photo_id,
                PhotoTag.tag_id == tag.id
            ).first()

            if not existing_photo_tag:
                # 创建照片-标签关联
                photo_tag = PhotoTag(
                    photo_id=photo_id,
                    tag_id=tag.id,
                    confidence=tag_data['confidence'],
                    source='auto'
                )
                db.add(photo_tag)

                # 更新标签使用次数（只有新增关联时才增加计数）
                tag.usage_count = (tag.usage_count or 0) + 1
                created_count += 1
            else:
                # 如果关联已存在，只更新置信度（如果新的置信度更高或现有置信度为None）
                # 🔥 修复：处理 existing_photo_tag.confidence 可能为 None 的情况
                # 注意：对于时间标签，在强制质量分析时，所有时间标签都已被清理，所以不会进入这个分支
                existing_confidence = existing_photo_tag.confidence
                new_confidence = tag_data['confidence']
                
                if existing_confidence is None or new_confidence > existing_confidence:
                    existing_photo_tag.confidence = new_confidence
                    updated_count += 1
                else:
                    skipped_count += 1

            saved_tags.append(tag_data['name'])

        # 记录保存结果
        if created_count > 0 or updated_count > 0:
            self.logger.debug(f"保存自动标签完成 photo_id={photo_id}, 创建={created_count}, 更新={updated_count}, 跳过={skipped_count}, tags={saved_tags}")

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

    def _extract_time_tags(self, taken_at: datetime) -> List[Dict[str, Any]]:
        """从拍摄时间提取时间标签"""
        tags = []
        
        # 季节标签
        month = taken_at.month
        if month in [3, 4, 5]:
            season = '春季'
        elif month in [6, 7, 8]:
            season = '夏季'
        elif month in [9, 10, 11]:
            season = '秋季'
        else:
            season = '冬季'
        
        tags.append({
            'name': season,
            'type': 'time',
            'confidence': 1.0
        })
        
        # 时段标签
        hour = taken_at.hour
        if 6 <= hour < 12:
            time_period = '上午'
        elif 12 <= hour < 18:
            time_period = '下午'
        elif 18 <= hour < 22:
            time_period = '晚上'
        else:
            time_period = '深夜'
        
        tags.append({
            'name': time_period,
            'type': 'time',
            'confidence': 1.0
        })
        
        # 节假日标签（使用chinese_calendar库）
        try:
            import chinese_calendar as cc  # type: ignore
            if cc.is_holiday(taken_at.date()):
                holiday_name = self._get_holiday_name_with_calendar(taken_at)
                if holiday_name:
                    tags.append({
                        'name': holiday_name,
                        'type': 'time',
                        'confidence': 1.0
                    })
        except ImportError:
            # 如果库不存在，使用简单的节假日判断
            holiday_name = self._get_holiday_name_simple(taken_at)
            if holiday_name:
                tags.append({
                    'name': holiday_name,
                    'type': 'time',
                    'confidence': 0.8
                })
        except Exception as e:
            # 其他异常，使用简单方法
            self.logger.warning(f"chinese_calendar库使用失败: {e}，使用简单方法")
            holiday_name = self._get_holiday_name_simple(taken_at)
            if holiday_name:
                tags.append({
                    'name': holiday_name,
                    'type': 'time',
                    'confidence': 0.8
                })
        
        return tags

    def _get_holiday_name_with_calendar(self, taken_at: datetime) -> str:
        """使用chinese_calendar库获取节假日名称"""
        try:
            import chinese_calendar as cc  # type: ignore

            if cc.is_holiday(taken_at.date()):
                # 从节假日详情中获取节假日名称
                holiday_detail = cc.get_holiday_detail(taken_at.date())
                if len(holiday_detail) >= 2:
                    holiday_name_en = holiday_detail[1]  # 英文节假日名称

                    # 直接从Holiday枚举获取中文名称
                    for holiday in cc.constants.Holiday:
                        # 特殊处理枚举名称到英文名称的映射
                        if holiday.name == 'new_years_day' and holiday_name_en == "New Year's Day":
                            return holiday.chinese
                        elif holiday.name == 'spring_festival' and holiday_name_en == 'Spring Festival':
                            return holiday.chinese
                        elif holiday.name == 'tomb_sweeping_day' and holiday_name_en == 'Tomb-sweeping Day':
                            return holiday.chinese
                        elif holiday.name == 'labour_day' and holiday_name_en == 'Labour Day':
                            return holiday.chinese
                        elif holiday.name == 'dragon_boat_festival' and holiday_name_en == 'Dragon Boat Festival':
                            return holiday.chinese
                        elif holiday.name == 'mid_autumn_festival' and holiday_name_en == 'Mid-autumn Festival':
                            return holiday.chinese
                        elif holiday.name == 'national_day' and holiday_name_en == 'National Day':
                            return holiday.chinese
                        elif holiday.name == 'anti_fascist_70th_day' and holiday_name_en == 'Anti-Fascist 70th Day':
                            return holiday.chinese

                # 如果无法从库中获取，使用简单方法作为备用
                return self._get_holiday_name_simple(taken_at)

            return None
        except Exception as e:
            self.logger.warning(f"获取节假日名称失败: {e}")
            return self._get_holiday_name_simple(taken_at)

    def _get_holiday_name_simple(self, taken_at: datetime) -> str:
        """简单的节假日判断（备用方法）"""
        month = taken_at.month
        day = taken_at.day
        
        # 简单的节假日判断（可以根据需要扩展）
        if month == 1 and day == 1:
            return '元旦'
        elif month == 2 and day == 14:
            return '情人节'
        elif month == 3 and day == 8:
            return '妇女节'
        elif month == 4 and day == 1:
            return '愚人节'
        elif month == 5 and day == 1:
            return '劳动节'
        elif month == 6 and day == 1:
            return '儿童节'
        elif month == 10 and day == 1:
            return '国庆节'
        elif month == 12 and day == 25:
            return '圣诞节'
        else:
            return None

    def _extract_quality_tags(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从质量分析结果提取质量标签"""
        tags = []
        
        quality_score = analysis_result.get('quality_score', 0)
        if quality_score >= 85:
            quality_level = '优秀'
        elif quality_score >= 70:
            quality_level = '良好'
        elif quality_score >= 50:
            quality_level = '一般'
        else:
            quality_level = '较差'
        
        tags.append({
            'name': quality_level,
            'type': 'quality',
            'confidence': 0.9
        })
        
        return tags
