"""
配置管理模块

负责加载和管理系统配置，包括：
1. JSON配置文件加载
2. 环境变量覆盖
3. 配置验证
4. 默认值设置

作者：AI助手
创建日期：2025年9月9日
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class SystemConfig(BaseSettings):
    """系统基础配置"""
    max_file_size: int = Field(default=52428800, description="单文件最大大小（字节）")
    timeout: int = Field(default=10, description="请求超时时间（秒）")
    max_concurrent: int = Field(default=2, description="最大并发数")
    temp_file_max_age: int = Field(default=24, description="临时文件最大年龄（小时）")


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    path: str = Field(default="./data/photos.db", description="数据库文件路径")


class DashScopeConfig(BaseSettings):
    """DashScope API配置"""
    api_key: Optional[str] = Field(default=None, description="API密钥", env="DASHSCOPE_API_KEY")
    base_url: str = Field(default="https://dashscope.aliyuncs.com/api/v1", description="API基础URL")
    model: str = Field(default="qwen-vl-plus-latest", description="当前使用的模型")
    available_models: list = Field(default=["qwen-vl-plus-latest"], description="可用的模型列表")
    timeout: int = Field(default=30, description="API请求超时时间（秒）")
    max_retry_count: int = Field(default=3, description="最大重试次数")


class StorageConfig(BaseSettings):
    """存储配置"""
    base_path: str = Field(default="./photos_storage", description="存储根目录")
    originals_path: str = Field(default="originals", description="原图存储路径")
    thumbnails_path: str = Field(default="thumbnails", description="缩略图存储路径")
    temp_path: str = Field(default="temp", description="临时文件存储路径")
    backups_path: str = Field(default="backups", description="备份文件存储路径")
    thumbnail_size: int = Field(default=300, description="缩略图尺寸")
    thumbnail_quality: int = Field(default=85, description="缩略图质量")


class AnalysisConfig(BaseSettings):
    """分析配置"""
    duplicate_threshold: int = Field(default=5, description="重复检测阈值")
    quality_threshold: int = Field(default=0, description="质量评估阈值")
    concurrent: int = Field(default=2, description="分析并发数")
    timeout: int = Field(default=30, description="分析超时时间（秒）")
    batch_size: int = Field(default=10, description="批量分析大小")
    batch_threshold: int = Field(default=200, description="分析分批阈值")


class LoggingConfig(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    file_path: str = Field(default="./logs/app.log", description="日志文件路径")
    max_size: str = Field(default="10MB", description="日志文件最大大小")
    backup_count: int = Field(default=5, description="日志备份文件数量")


class ServerConfig(BaseSettings):
    """服务器配置"""
    host: str = Field(default="127.0.0.1", description="服务器主机地址")
    port: int = Field(default=8000, description="服务器端口")
    debug: bool = Field(default=True, description="调试模式")


class UIConfig(BaseSettings):
    """用户界面配置"""
    photos_per_page: int = Field(default=12, description="每页显示照片数量")
    similar_photos_limit: int = Field(default=8, description="相似照片最多显示数量")
    hot_tags_limit: int = Field(default=10, description="热门标签显示数量")
    hot_categories_limit: int = Field(default=10, description="热门分类显示数量")


class SearchConfig(BaseSettings):
    """搜索配置"""
    similarity_threshold: float = Field(default=0.8, description="相似度阈值")
    timeout: int = Field(default=5, description="搜索超时时间（秒）")
    default_page_size: int = Field(default=20, description="默认分页大小")
    max_page_size: int = Field(default=100, description="最大分页大小")
    suggestion_limit: int = Field(default=10, description="搜索建议数量")
    history_limit: int = Field(default=50, description="搜索历史数量")


class SimilarityConfig(BaseSettings):
    """相似度检测配置"""
    first_layer_weights: dict = Field(default={
        "perceptual_hash": 0.25,
        "objects": 0.15,
        "time": 0.15,
        "color_histogram": 0.15,
        "scene_type": 0.10,
        "location": 0.10,
        "description": 0.10,
        "emotion": 0.05,
        "activity": 0.05,
        "tags": 0.05,
        "camera": 0.05,
        "structural": 0.10
    }, description="第一层权重配置")
    first_layer_thresholds: dict = Field(default={
        "perceptual_hash": 0.6,
        "color_histogram": 0.7,
        "structural": 0.8,
        "scene_type": 1.0,
        "objects": 0.5,
        "emotion": 0.6,
        "activity": 0.6,
        "description": 0.5,
        "tags": 0.5,
        "time": 0.8,
        "location": 0.9,
        "camera": 0.7,
        "combined": 0.55
    }, description="第一层阈值配置")
    algorithms: dict = Field(default={
        "primary_algorithm": "perceptual_hash",
        "fallback_algorithms": ["color_histogram", "structural"],
        "ai_enabled": True,
        "exif_enabled": True
    }, description="算法配置")
    performance: dict = Field(default={
        "batch_size": 100,
        "cache_enabled": True,
        "cache_ttl": 3600,
        "max_concurrent": 5
    }, description="性能配置")
    pre_screening: dict = Field(default={
        "time_margin_days": 30,
        "location_margin": 0.1
    }, description="预筛选配置")


class ImportConfig(BaseSettings):
    """导入配置"""
    supported_formats: list = Field(default=[".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".bmp", ".gif", ".heic", ".heif"], description="支持的文件格式")
    max_upload_files: int = Field(default=50, description="单次最大上传文件数")
    scan_batch_size: int = Field(default=100, description="文件夹扫描批次大小")
    batch_threshold: int = Field(default=200, description="导入分批阈值")


class QualityConfig(BaseSettings):
    """质量评估配置"""
    weights: dict = Field(default={
        "sharpness": 0.3,
        "brightness": 0.2,
        "contrast": 0.2,
        "color": 0.15,
        "composition": 0.15
    }, description="质量评估权重")
    thresholds: dict = Field(default={
        "excellent": 80,
        "good": 60,
        "fair": 40,
        "poor": 20
    }, description="质量阈值")

class MapConfig(BaseSettings):
    """地图API配置"""
    provider: str = Field(default="amap", description="地图服务提供商 (amap/baidu/google)")
    api_key: str = Field(default="", description="地图API Key")
    timeout: int = Field(default=10, description="API调用超时时间（秒）")
    rate_limit: int = Field(default=180, description="每分钟最大API调用次数")
    cache_enabled: bool = Field(default=True, description="是否启用地址缓存")
    cache_ttl: int = Field(default=86400, description="地址缓存时间（秒）")
    batch_size: int = Field(default=10, description="批量处理大小")
    configured: bool = Field(default=False, description="是否已配置地图API")
    offline_geocoding_db_path: str = Field(default="offline_geocoding.db", description="离线地理编码数据库路径")


class PersonPhotosPaginationConfig(BaseSettings):
    """人物照片分页配置"""
    page_size: int = Field(default=12, description="每页显示照片数量")
    max_pages_shown: int = Field(default=5, description="分页控件最多显示的页码数")
    loading_delay: int = Field(default=300, description="加载延迟（毫秒）")


class FaceRecognitionConfig(BaseSettings):
    """人脸识别配置"""
    enabled: bool = Field(default=True, description="是否启用人脸识别")
    model: str = Field(default="buffalo_l", description="人脸识别模型")
    use_local_model: bool = Field(default=True, description="是否使用本地模型")
    models_base_path: str = Field(default="./models", description="模型文件基础路径")
    detection_threshold: float = Field(default=0.6, description="人脸检测置信度阈值")
    similarity_threshold: float = Field(default=0.7, description="人脸相似度阈值")
    max_faces_per_photo: int = Field(default=10, description="每张照片最大检测人脸数")
    batch_size: int = Field(default=30, description="人脸识别批次大小")
    batch_threshold: int = Field(default=10, description="分批处理阈值")
    max_concurrent_batches: int = Field(default=3, description="最大并发批次")
    max_concurrent_photos: int = Field(default=3, description="单批次内最大并发照片数")
    max_progress_checks: int = Field(default=1800, description="最大进度检查次数")
    max_clusters: int = Field(default=60, description="最大聚类数量（Top N）")
    min_cluster_size: int = Field(default=2, description="最小聚类大小")
    auto_cluster: bool = Field(default=True, description="是否自动聚类")
    cluster_quality_threshold: float = Field(default=0.8, description="聚类质量阈值")
    person_photos_pagination: PersonPhotosPaginationConfig = Field(default_factory=PersonPhotosPaginationConfig, description="人物照片分页配置")


class ImageFeaturesConfig(BaseSettings):
    """图像特征提取配置"""
    
    class Config:
        protected_namespaces = ('settings_',)  # 解决model_file字段命名冲突警告
    
    enabled: bool = Field(default=True, description="是否启用图像特征提取")
    model: str = Field(default="resnet50", description="使用的模型名称")
    use_local_model: bool = Field(default=True, description="是否使用本地模型")
    models_base_path: str = Field(default="./models", description="模型存储基础路径")
    model_file: str = Field(default="resnet50/resnet50-0676ba61.pth", description="模型文件名（相对于models_base_path）")
    feature_dim: int = Field(default=2048, description="特征向量维度")
    batch_size: int = Field(default=50, description="批量处理大小")
    batch_threshold: int = Field(default=100, description="分批阈值（超过此数量将分批处理）")
    max_concurrent_batches: int = Field(default=3, description="最大并发批次数")
    max_concurrent_photos: int = Field(default=6, description="每批最大并发照片数")
    similarity_threshold: float = Field(default=0.75, description="相似度阈值（用于相似照片搜索）")
    extraction_timeout: int = Field(default=30, description="特征提取超时时间（秒）")


def is_msix_environment() -> bool:
    """
    检测是否运行在 MSIX 环境中
    
    :return: 如果存在 .msix 标记文件，返回 True；否则返回 False
    """
    import sys
    from pathlib import Path
    
    # 获取应用目录
    if getattr(sys, 'frozen', False):
        # PyInstaller打包环境：配置文件位于可执行文件所在目录
        exe_path = Path(sys.executable)
        app_dir = exe_path.parent
    else:
        # 开发环境：从当前文件位置推断
        current_path = Path(__file__).resolve()
        app_dir = current_path.parent.parent.parent  # app/core/config.py -> app -> project_root
    
    # 检查标记文件是否存在
    marker_file = app_dir / '.msix'
    return marker_file.exists()


def get_config_paths() -> tuple[Path, Path]:
    """
    获取配置文件的路径
    
    根据运行环境（MSIX 或 Portable）返回正确的配置路径：
    - MSIX 环境：用户配置保存在 %LOCALAPPDATA%\\PhotoSystem\\config.json
    - Portable 环境：用户配置保存在应用目录的 config.json
    
    :return: (用户配置路径, 默认配置路径)
    """
    import sys
    from pathlib import Path
    
    # 获取应用目录
    if getattr(sys, 'frozen', False):
        # PyInstaller打包环境：配置文件位于可执行文件所在目录
        exe_path = Path(sys.executable)
        app_dir = exe_path.parent
    else:
        # 开发环境：从当前文件位置推断
        current_path = Path(__file__).resolve()
        app_dir = current_path.parent.parent.parent  # app/core/config.py -> app -> project_root
    
    # 检测环境
    is_msix = is_msix_environment()
    
    if is_msix:
        # MSIX 环境：用户配置在 AppData
        local_appdata = Path(os.getenv('LOCALAPPDATA', ''))
        if not local_appdata:
            # 如果环境变量不存在，回退到应用目录
            user_config_path = app_dir / 'config.json'
        else:
            user_config_dir = local_appdata / 'PhotoSystem'
            user_config_dir.mkdir(parents=True, exist_ok=True)
            user_config_path = user_config_dir / 'config.json'
    else:
        # Portable 环境：用户配置在应用目录
        user_config_path = app_dir / 'config.json'
    
    # 默认配置始终在应用目录
    default_config_path = app_dir / 'config_default.json'
    
    return user_config_path, default_config_path


class Settings(BaseSettings):
    """全局配置类"""

    # 子配置
    system: SystemConfig
    database: DatabaseConfig
    dashscope: DashScopeConfig
    storage: StorageConfig
    analysis: AnalysisConfig
    logging: LoggingConfig
    server: ServerConfig
    ui: UIConfig
    search: SearchConfig
    similarity: SimilarityConfig
    import_config: ImportConfig = Field(alias="import")
    quality: QualityConfig
    maps: MapConfig
    face_recognition: FaceRecognitionConfig
    image_features: ImageFeaturesConfig

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        # 首先尝试从JSON配置文件加载
        config_data = self._load_config_from_json()

        # 合并命令行参数
        config_data.update(kwargs)

        # 初始化父类
        super().__init__(**config_data)

    def _load_config_from_json(self) -> Dict[str, Any]:
        """
        从JSON配置文件加载配置
        
        加载优先级：
        1. 用户配置（config.json）- 根据环境在应用目录或 AppData
        2. 默认配置（config_default.json）- 应用目录
        3. 代码默认值（如果都不存在）
        """
        user_config_path, default_config_path = get_config_paths()
        
        config_data = {}
        
        # 1. 优先加载用户配置
        if user_config_path.exists():
            try:
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 处理环境变量替换
                self._process_env_vars(config_data)
                
                # 特殊处理 api_key：优先从环境变量读取
                if 'dashscope' in config_data and 'api_key' in config_data['dashscope']:
                    env_api_key = os.getenv('DASHSCOPE_API_KEY')
                    if env_api_key:
                        config_data['dashscope']['api_key'] = env_api_key
                    elif config_data['dashscope']['api_key'] is None:
                        # 如果配置文件中为 null 且环境变量不存在，保持 None
                        pass
                
                return config_data
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                print(f"警告：无法加载用户配置文件 {user_config_path}: {e}")
                print("将尝试加载默认配置")
                config_data = {}
        
        # 2. 如果用户配置不存在或加载失败，加载默认配置
        if not config_data and default_config_path.exists():
            try:
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 处理环境变量替换
                self._process_env_vars(config_data)
                
                # 特殊处理 api_key：优先从环境变量读取
                if 'dashscope' in config_data and 'api_key' in config_data['dashscope']:
                    env_api_key = os.getenv('DASHSCOPE_API_KEY')
                    if env_api_key:
                        config_data['dashscope']['api_key'] = env_api_key
                    elif config_data['dashscope']['api_key'] is None:
                        # 如果配置文件中为 null 且环境变量不存在，保持 None
                        pass
                
                return config_data
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                print(f"警告：无法加载默认配置文件 {default_config_path}: {e}")
                print("将使用代码默认值")
        
        # 3. 如果都不存在，返回空字典（使用代码默认值）
        return {}

    def _process_env_vars(self, config_data: Dict[str, Any]) -> None:
        """处理环境变量替换"""
        def replace_env_vars(obj):
            if isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                return os.getenv(env_var, obj)
            elif isinstance(obj, dict):
                return {k: replace_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_env_vars(item) for item in obj]
            else:
                return obj

        # 原地修改config_data
        for key, value in config_data.items():
            config_data[key] = replace_env_vars(value)

    @property
    def server_host(self) -> str:
        """获取服务器主机地址"""
        return self.server.host

    @property
    def server_port(self) -> int:
        """获取服务器端口"""
        return self.server.port

    @property
    def debug(self) -> bool:
        """获取调试模式"""
        return self.server.debug

    def get_user_config(self) -> Dict[str, Any]:
        """获取用户可配置的参数"""
        return {
            "dashscope": {
                "model": self.dashscope.model,
                "api_key": self.dashscope.api_key,
                "available_models": self.dashscope.available_models
            },
            "storage": {
                "base_path": self.storage.base_path,
                "thumbnail_quality": self.storage.thumbnail_quality,
                "thumbnail_size": self.storage.thumbnail_size
            },
            # 数据库路径已从用户界面移除，但保留在完整配置中
            "system": {
                "max_file_size": self.system.max_file_size
            },
            "ui": {
                "photos_per_page": self.ui.photos_per_page,
                "similar_photos_limit": self.ui.similar_photos_limit
            },
            "search": {
                "similarity_threshold": self.search.similarity_threshold
            },
            "analysis": {
                "duplicate_threshold": self.analysis.duplicate_threshold,
                "quality_threshold": self.analysis.quality_threshold,
                "concurrent": self.analysis.concurrent,
                "timeout": self.analysis.timeout,
                "batch_size": self.analysis.batch_size,
                "batch_threshold": self.analysis.batch_threshold
            },
            "import": {
                "max_upload_files": self.import_config.max_upload_files,
                "scan_batch_size": self.import_config.scan_batch_size,
                "batch_threshold": self.import_config.batch_threshold,
                "supported_formats": self.import_config.supported_formats
            },
            "maps": {
                "provider": self.maps.provider,
                "api_key": self.maps.api_key,
                "timeout": self.maps.timeout,
                "rate_limit": self.maps.rate_limit,
                "cache_enabled": self.maps.cache_enabled,
                "cache_ttl": self.maps.cache_ttl,
                "batch_size": self.maps.batch_size,
                "configured": self.maps.configured,
                "offline_geocoding_db_path": self.maps.offline_geocoding_db_path
            },
            "face_recognition": {
                "model": self.face_recognition.model,
                "use_local_model": self.face_recognition.use_local_model,
                "models_base_path": self.face_recognition.models_base_path,
                "detection_threshold": self.face_recognition.detection_threshold,
                "similarity_threshold": self.face_recognition.similarity_threshold,
                "max_faces_per_photo": self.face_recognition.max_faces_per_photo,
                "batch_size": self.face_recognition.batch_size,
                "batch_threshold": self.face_recognition.batch_threshold,
                "max_concurrent_batches": self.face_recognition.max_concurrent_batches,
                "max_concurrent_photos": self.face_recognition.max_concurrent_photos,
                "max_progress_checks": self.face_recognition.max_progress_checks,
                "max_clusters": self.face_recognition.max_clusters,
                "min_cluster_size": self.face_recognition.min_cluster_size,
                "auto_cluster": self.face_recognition.auto_cluster,
                "cluster_quality_threshold": self.face_recognition.cluster_quality_threshold,
                "person_photos_pagination": {
                    "page_size": self.face_recognition.person_photos_pagination.page_size,
                    "max_pages_shown": self.face_recognition.person_photos_pagination.max_pages_shown,
                    "loading_delay": self.face_recognition.person_photos_pagination.loading_delay
                }
            },
            "image_features": {
                "enabled": self.image_features.enabled,
                "model": self.image_features.model,
                "use_local_model": self.image_features.use_local_model,
                "models_base_path": self.image_features.models_base_path,
                "model_file": self.image_features.model_file,
                "feature_dim": self.image_features.feature_dim,
                "batch_size": self.image_features.batch_size,
                "batch_threshold": self.image_features.batch_threshold,
                "max_concurrent_batches": self.image_features.max_concurrent_batches,
                "max_concurrent_photos": self.image_features.max_concurrent_photos,
                "similarity_threshold": self.image_features.similarity_threshold,
                "extraction_timeout": self.image_features.extraction_timeout
            }
        }

    def update_user_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户配置"""
        # 这里只是返回配置数据，实际更新需要重新加载配置文件
        # 真正的更新逻辑将在API层实现
        return config_data

    def get_full_config(self) -> Dict[str, Any]:
        """获取完整系统配置"""
        return {
            "system": self.system.dict(),
            "database": self.database.dict(),
            "dashscope": self.dashscope.dict(),
            "storage": self.storage.dict(),
            "analysis": self.analysis.dict(),
            "logging": self.logging.dict(),
            "server": self.server.dict(),
            "ui": self.ui.dict(),
            "search": self.search.dict(),
            "similarity": self.similarity.dict(),
            "import": self.import_config.dict(),
            "quality": self.quality.dict(),
            "maps": self.maps.dict(),
            "face_recognition": self.face_recognition.dict(),
            "image_features": self.image_features.dict()
        }


# 全局配置实例（延迟初始化）
_settings_instance = None


def get_settings() -> Settings:
    """
    获取配置实例（延迟初始化）
    
    首次调用时创建 Settings 实例，后续调用返回同一个实例。
    这样可以确保在 setup_msix_first_run() 完成后再初始化配置。
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings() -> Settings:
    """
    重新加载配置（用于配置更新后）
    
    在配置更新后调用此函数，会重新创建 Settings 实例，使用最新的配置文件。
    """
    global _settings_instance
    _settings_instance = None
    return get_settings()


# 为了向后兼容，提供一个 settings 对象
# 注意：为了延迟初始化，这里使用一个包装类
class _SettingsWrapper:
    """Settings 包装类，用于延迟初始化"""
    def __getattr__(self, name):
        return getattr(get_settings(), name)
    
    def __setattr__(self, name, value):
        # 允许设置属性（用于更新配置）
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            setattr(get_settings(), name, value)

# 创建 settings 对象（延迟初始化）
settings = _SettingsWrapper()
