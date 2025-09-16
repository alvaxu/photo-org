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
    similar_photos_limit: int = Field(default=8, description="相似照片显示数量")
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


class ImportConfig(BaseSettings):
    """导入配置"""
    supported_formats: list = Field(default=[".jpg", ".jpeg", ".png", ".tiff", ".webp", ".bmp", ".gif"], description="支持的文件格式")
    max_upload_files: int = Field(default=50, description="单次最大上传文件数")
    scan_batch_size: int = Field(default=100, description="文件夹扫描批次大小")


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
        """从JSON配置文件加载配置"""
        # 获取项目根目录路径
        current_path = Path(__file__).resolve()
        project_root = current_path.parent.parent.parent  # app/core/config.py -> app -> project_root
        config_path = project_root / "config.json"

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
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
                print(f"警告：无法加载配置文件 config.json: {e}")
                print("将使用默认配置")

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
                "duplicate_threshold": self.analysis.duplicate_threshold
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
            "quality": self.quality.dict()
        }


# 创建全局配置实例
settings = Settings()
