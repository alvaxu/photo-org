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
    api_key: str = Field(default="", description="API密钥", env="DASHSCOPE_API_KEY")
    base_url: str = Field(default="https://dashscope.aliyuncs.com/api/v1", description="API基础URL")


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


# 创建全局配置实例
settings = Settings()
