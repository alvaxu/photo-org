"""
日志配置模块

负责配置应用日志，包括：
1. 控制台日志输出
2. 文件日志输出
3. 日志轮转
4. 日志格式化

作者：AI助手
创建日期：2025年9月9日
"""

import logging
import logging.handlers
from pathlib import Path

from app.core.config import settings


def setup_logging():
    """设置应用日志配置"""

    # 创建logs目录
    log_dir = Path(settings.logging.file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.logging.level.upper()))

    # 清除现有处理器
    logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.logging.level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（带轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.logging.file_path,
        maxBytes=parse_size(settings.logging.max_size),
        backupCount=settings.logging.backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, settings.logging.level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 设置第三方库的日志级别
    uvicorn_level = getattr(logging, settings.logging.level.upper())
    logging.getLogger('uvicorn').setLevel(uvicorn_level)
    logging.getLogger('uvicorn.access').setLevel(uvicorn_level)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

    logger.info("日志系统初始化完成")


def parse_size(size_str: str) -> int:
    """解析大小字符串，返回字节数"""
    size_str = size_str.upper()
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # 默认按字节处理
        return int(size_str)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的logger"""
    return logging.getLogger(name)
