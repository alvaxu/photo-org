"""
家庭版智能照片系统 - 配置管理API
"""
import json
import os
import sys
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings, get_config_paths
from app.core.logging import get_logger
import importlib

logger = get_logger(__name__)
router = APIRouter()

def is_local_access(request: Request) -> bool:
    """检测是否为本地访问"""
    client_ip = request.client.host
    # 检查是否为本地IP
    local_ips = ['127.0.0.1', 'localhost', '::1', '0.0.0.0']
    return client_ip in local_ips or client_ip.startswith('127.') or client_ip.startswith('192.168.') or client_ip.startswith('10.')

async def reload_config():
    """重新加载配置"""
    try:
        # 使用新的 reload_settings() 函数重新加载配置
        from app.core.config import reload_settings
        reload_settings()
        
        # 更新全局配置实例引用（向后兼容）
        global settings
        from app.core.config import get_settings
        settings = get_settings()
        
        logger.info("配置重新加载成功")
    except Exception as e:
        logger.error(f"配置重新加载失败: {str(e)}")
        raise e


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    dashscope: Optional[Dict[str, Any]] = None
    storage: Optional[Dict[str, Any]] = None
    database: Optional[Dict[str, Any]] = None
    system: Optional[Dict[str, Any]] = None
    ui: Optional[Dict[str, Any]] = None
    search: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None
    face_recognition: Optional[Dict[str, Any]] = None
    image_features: Optional[Dict[str, Any]] = None
    # maps 配置通过专门的API更新，不在这里处理


@router.get("/user")
async def get_user_config():
    """获取用户可配置的参数"""
    try:
        config = settings.get_user_config()
        return {
            "success": True,
            "data": config
        }
    except Exception as e:
        logger.error(f"获取用户配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取用户配置失败: {str(e)}")


@router.put("/user")
async def update_user_config(request: ConfigUpdateRequest, http_request: Request):
    """
    更新用户配置
    
    只更新页面上显示的参数，其他参数保持不变（特别是 database.path、storage.base_path、logging.file_path）
    """
    try:
        # 检查存储目录修改是否为本地访问
        if request.storage and 'base_path' in request.storage:
            if not is_local_access(http_request):
                raise HTTPException(status_code=403, detail="存储目录修改仅限本地访问")
        
        # 获取配置路径
        user_config_path, default_config_path = get_config_paths()
        
        # 读取现有用户配置（如果存在），否则从默认配置开始
        if user_config_path.exists():
            try:
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
            except Exception as e:
                logger.warning(f"无法读取现有用户配置: {e}，将使用默认配置")
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
        else:
            # 如果用户配置不存在，从默认配置开始
            with open(default_config_path, 'r', encoding='utf-8') as f:
                current_config = json.load(f)
        
        # 确保所有必需的配置字段都存在
        required_fields = ["system", "database", "dashscope", "storage", "analysis", "logging", "server", "ui", "search", "similarity", "import", "quality", "maps", "face_recognition", "image_features"]
        for field in required_fields:
            if field not in current_config:
                logger.warning(f"配置中缺少必需字段: {field}")
                # 从默认配置中获取
                if default_config_path.exists():
                    with open(default_config_path, 'r', encoding='utf-8') as f:
                        default_config = json.load(f)
                        if field in default_config:
                            current_config[field] = default_config[field]
                # 如果默认配置也没有，从 settings 对象获取
                if field not in current_config and hasattr(settings, field):
                    current_config[field] = getattr(settings, field).dict()

        # 只更新页面上显示的参数，其他参数保持不变
        # 页面上显示的参数：
        # - dashscope: model, api_key
        # - storage: thumbnail_quality, thumbnail_size（注意：base_path 不在页面上，需要保护）
        # - system: max_file_size
        # - ui: photos_per_page, similar_photos_limit
        # - search: similarity_threshold
        # - image_features: similarity_threshold
        # - analysis: duplicate_threshold
        
        if request.dashscope:
            if "dashscope" not in current_config:
                current_config["dashscope"] = {}
            # 只更新 model 和 api_key
            if "model" in request.dashscope:
                current_config["dashscope"]["model"] = request.dashscope["model"]
            if "api_key" in request.dashscope:
                current_config["dashscope"]["api_key"] = request.dashscope["api_key"]
            if "available_models" in request.dashscope:
                current_config["dashscope"]["available_models"] = request.dashscope["available_models"]
        
        if request.storage:
            if "storage" not in current_config:
                current_config["storage"] = {}
            # 只更新 thumbnail_quality 和 thumbnail_size，保护 base_path
            if "thumbnail_quality" in request.storage:
                current_config["storage"]["thumbnail_quality"] = request.storage["thumbnail_quality"]
            if "thumbnail_size" in request.storage:
                current_config["storage"]["thumbnail_size"] = request.storage["thumbnail_size"]
            # 注意：base_path 不在页面上，不应该被更新（除非明确请求）
            if "base_path" in request.storage:
                # 只有在本地访问时才允许更新 base_path
                if is_local_access(http_request):
                    current_config["storage"]["base_path"] = request.storage["base_path"]
                else:
                    logger.warning("远程访问尝试修改 base_path，已拒绝")
        
        if request.system:
            if "system" not in current_config:
                current_config["system"] = {}
            # 只更新 max_file_size
            if "max_file_size" in request.system:
                current_config["system"]["max_file_size"] = request.system["max_file_size"]
        
        if request.ui:
            if "ui" not in current_config:
                current_config["ui"] = {}
            # 只更新 photos_per_page 和 similar_photos_limit
            if "photos_per_page" in request.ui:
                current_config["ui"]["photos_per_page"] = request.ui["photos_per_page"]
            if "similar_photos_limit" in request.ui:
                current_config["ui"]["similar_photos_limit"] = request.ui["similar_photos_limit"]
        
        if request.search:
            if "search" not in current_config:
                current_config["search"] = {}
            # 只更新 similarity_threshold
            if "similarity_threshold" in request.search:
                current_config["search"]["similarity_threshold"] = request.search["similarity_threshold"]
        
        if request.image_features:
            if "image_features" not in current_config:
                current_config["image_features"] = {}
            # 只更新 similarity_threshold
            if "similarity_threshold" in request.image_features:
                current_config["image_features"]["similarity_threshold"] = request.image_features["similarity_threshold"]
        
        if request.analysis:
            if "analysis" not in current_config:
                current_config["analysis"] = {}
            # 只更新 duplicate_threshold
            if "duplicate_threshold" in request.analysis:
                current_config["analysis"]["duplicate_threshold"] = request.analysis["duplicate_threshold"]
        
        if request.face_recognition:
            if "face_recognition" not in current_config:
                current_config["face_recognition"] = {}
            # 只更新 min_cluster_size 和 max_clusters（页面上显示的参数）
            if "min_cluster_size" in request.face_recognition:
                current_config["face_recognition"]["min_cluster_size"] = request.face_recognition["min_cluster_size"]
            if "max_clusters" in request.face_recognition:
                current_config["face_recognition"]["max_clusters"] = request.face_recognition["max_clusters"]
        
        # maps 配置通过专门的API更新，不在这里处理

        # 保存到配置文件（根据环境自动选择路径）
        user_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(user_config_path, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, indent=2, ensure_ascii=False)
        
        # 重新加载配置
        await reload_config()
        
        logger.info("用户配置更新成功")
        return {
            "success": True,
            "message": "用户配置更新成功",
            "data": settings.get_user_config()
        }
    except Exception as e:
        logger.error(f"更新用户配置失败: {str(e)}")
        return {
            "success": False,
            "message": f"更新用户配置失败: {str(e)}"
        }


@router.post("/user/reset")
async def reset_user_config():
    """
    重置用户配置为默认值
    
    只重置页面上显示的参数为默认值，其他参数保持不变（特别是 database.path、storage.base_path、logging.file_path）
    """
    try:
        # 获取配置路径
        user_config_path, default_config_path = get_config_paths()
        
        if not default_config_path.exists():
            raise HTTPException(status_code=404, detail="默认配置文件不存在")

        # 读取现有用户配置（如果存在），保护关键路径
        if user_config_path.exists():
            try:
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
            except Exception as e:
                logger.warning(f"无法读取现有用户配置: {e}，将使用默认配置")
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
        else:
            # 如果用户配置不存在，从默认配置开始
            with open(default_config_path, 'r', encoding='utf-8') as f:
                current_config = json.load(f)

        # 读取默认配置
        with open(default_config_path, 'r', encoding='utf-8') as f:
            default_config = json.load(f)

        # 保护关键路径（这些路径不在页面上，不应该被重置）
        # 注意：即使路径为空字符串，也应该保护（因为空字符串表示未配置，不应该被重置）
        protected_paths = {
            "database_path": current_config.get("database", {}).get("path"),
            "storage_base_path": current_config.get("storage", {}).get("base_path"),
            "logging_file_path": current_config.get("logging", {}).get("file_path")
        }

        # 只重置页面上显示的参数为默认值，其他参数保持不变
        # 页面上显示的参数：
        # - dashscope: model, api_key
        # - storage: thumbnail_quality, thumbnail_size（注意：base_path 需要保护）
        # - system: max_file_size
        # - ui: photos_per_page, similar_photos_limit
        # - search: similarity_threshold
        # - image_features: similarity_threshold
        # - analysis: duplicate_threshold
        # - face_recognition: min_cluster_size, max_clusters
        
        # 重置 dashscope（只重置 model 和 api_key）
        if "dashscope" in default_config:
            if "dashscope" not in current_config:
                current_config["dashscope"] = {}
            if "model" in default_config["dashscope"]:
                current_config["dashscope"]["model"] = default_config["dashscope"]["model"]
            if "api_key" in default_config["dashscope"]:
                current_config["dashscope"]["api_key"] = default_config["dashscope"]["api_key"]
            if "available_models" in default_config["dashscope"]:
                current_config["dashscope"]["available_models"] = default_config["dashscope"]["available_models"]
        
        # 重置 storage（只重置 thumbnail_quality 和 thumbnail_size，保护 base_path）
        if "storage" in default_config:
            if "storage" not in current_config:
                current_config["storage"] = {}
            if "thumbnail_quality" in default_config["storage"]:
                current_config["storage"]["thumbnail_quality"] = default_config["storage"]["thumbnail_quality"]
            if "thumbnail_size" in default_config["storage"]:
                current_config["storage"]["thumbnail_size"] = default_config["storage"]["thumbnail_size"]
            # 保护 base_path（如果存在，包括空字符串）
            if protected_paths["storage_base_path"] is not None:
                current_config["storage"]["base_path"] = protected_paths["storage_base_path"]
        
        # 重置 system（只重置 max_file_size）
        if "system" in default_config:
            if "system" not in current_config:
                current_config["system"] = {}
            if "max_file_size" in default_config["system"]:
                current_config["system"]["max_file_size"] = default_config["system"]["max_file_size"]
        
        # 重置 ui（只重置 photos_per_page 和 similar_photos_limit）
        if "ui" in default_config:
            if "ui" not in current_config:
                current_config["ui"] = {}
            if "photos_per_page" in default_config["ui"]:
                current_config["ui"]["photos_per_page"] = default_config["ui"]["photos_per_page"]
            if "similar_photos_limit" in default_config["ui"]:
                current_config["ui"]["similar_photos_limit"] = default_config["ui"]["similar_photos_limit"]
        
        # 重置 search（只重置 similarity_threshold）
        if "search" in default_config:
            if "search" not in current_config:
                current_config["search"] = {}
            if "similarity_threshold" in default_config["search"]:
                current_config["search"]["similarity_threshold"] = default_config["search"]["similarity_threshold"]
        
        # 重置 image_features（只重置 similarity_threshold）
        if "image_features" in default_config:
            if "image_features" not in current_config:
                current_config["image_features"] = {}
            if "similarity_threshold" in default_config["image_features"]:
                current_config["image_features"]["similarity_threshold"] = default_config["image_features"]["similarity_threshold"]
        
        # 重置 analysis（只重置 duplicate_threshold）
        if "analysis" in default_config:
            if "analysis" not in current_config:
                current_config["analysis"] = {}
            if "duplicate_threshold" in default_config["analysis"]:
                current_config["analysis"]["duplicate_threshold"] = default_config["analysis"]["duplicate_threshold"]
        
        # 重置 face_recognition（只重置 min_cluster_size 和 max_clusters）
        if "face_recognition" in default_config:
            if "face_recognition" not in current_config:
                current_config["face_recognition"] = {}
            if "min_cluster_size" in default_config["face_recognition"]:
                current_config["face_recognition"]["min_cluster_size"] = default_config["face_recognition"]["min_cluster_size"]
            if "max_clusters" in default_config["face_recognition"]:
                current_config["face_recognition"]["max_clusters"] = default_config["face_recognition"]["max_clusters"]
        
        # 保护关键路径（恢复被保护的路径）
        if "database" not in current_config:
            current_config["database"] = {}
        if protected_paths["database_path"] is not None:
            current_config["database"]["path"] = protected_paths["database_path"]
        
        if "logging" not in current_config:
            current_config["logging"] = {}
        if protected_paths["logging_file_path"] is not None:
            current_config["logging"]["file_path"] = protected_paths["logging_file_path"]

        # 保存为用户配置（根据环境自动选择路径）
        user_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(user_config_path, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, indent=2, ensure_ascii=False)
        
        # 重新加载配置
        await reload_config()
        
        logger.info("用户配置重置成功")
        return {
            "success": True,
            "message": "用户配置重置成功",
            "data": settings.get_user_config()
        }
    except Exception as e:
        logger.error(f"重置用户配置失败: {str(e)}")
        return {
            "success": False,
            "message": f"重置用户配置失败: {str(e)}"
        }


@router.get("/full")
async def get_full_config():
    """获取完整系统配置（包含高级参数）"""
    try:
        config = settings.get_full_config()
        return {
            "success": True,
            "data": config
        }
    except Exception as e:
        logger.error(f"获取完整配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取完整配置失败: {str(e)}")


@router.put("/full")
async def update_full_config(config_data: Dict[str, Any]):
    """更新完整系统配置"""
    try:
        # 保存到配置文件
        config_path = "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        # 重新加载配置
        await reload_config()
        
        logger.info("完整配置更新成功")
        return {
            "success": True,
            "message": "完整配置更新成功",
            "data": config_data
        }
    except Exception as e:
        logger.error(f"更新完整配置失败: {str(e)}")
        return {
            "success": False,
            "message": f"更新完整配置失败: {str(e)}"
        }


@router.post("/reload")
async def reload_config_endpoint():
    """手动重新加载配置"""
    try:
        await reload_config()
        return {
            "success": True,
            "message": "配置重新加载成功",
            "data": settings.get_user_config()
        }
    except Exception as e:
        logger.error(f"重新加载配置失败: {str(e)}")
        return {
            "success": False,
            "message": f"重新加载配置失败: {str(e)}"
        }


@router.get("/export")
async def export_config():
    """导出完整配置文件"""
    try:
        config_data = settings.get_full_config()
        
        # 创建临时文件
        temp_file = "config_export.json"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        return FileResponse(
            path=temp_file,
            filename="config.json",
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"导出配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")


@router.get("/models")
async def get_available_models():
    """获取可用的AI模型列表"""
    try:
        models = settings.dashscope.available_models
        current_model = settings.dashscope.model
        
        return {
            "success": True,
            "data": {
                "available_models": models,
                "current_model": current_model
            }
        }
    except Exception as e:
        logger.error(f"获取可用模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取可用模型失败: {str(e)}")


@router.post("/select-directory")
async def select_directory(request: Request):
    """选择目录API"""
    # 检查是否为本地访问
    if not is_local_access(request):
        raise HTTPException(status_code=403, detail="此操作仅限本地访问")
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # 创建根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 设置窗口属性
        root.attributes('-topmost', True)  # 置顶显示
        root.state('withdrawn')  # 完全隐藏主窗口
        
        # 选择目录
        directory = filedialog.askdirectory(
            title="选择照片存储目录",
            initialdir="C:\\"  # 默认从C盘开始
        )
        
        root.destroy()  # 销毁窗口
        
        if directory:
            return {
                "success": True,
                "path": directory
            }
        else:
            return {
                "success": False,
                "message": "用户取消选择"
            }
            
    except Exception as e:
        logger.error(f"选择目录失败: {str(e)}")
        return {
            "success": False,
            "message": f"选择目录失败: {str(e)}"
        }


@router.post("/select-database-file")
async def select_database_file():
    """选择数据库文件"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # 创建根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 设置窗口属性
        root.attributes('-topmost', True)  # 置顶显示
        root.state('withdrawn')  # 完全隐藏主窗口
        
        # 选择数据库文件
        file_path = filedialog.askopenfilename(
            title="选择数据库文件",
            filetypes=[
                ("数据库文件", "*.db"),
                ("SQLite数据库", "*.sqlite"),
                ("所有文件", "*.*")
            ],
            initialdir="C:\\"
        )
        
        root.destroy()  # 销毁窗口
        
        if file_path:
            return {
                "success": True,
                "path": file_path
            }
        else:
            return {
                "success": False,
                "message": "用户取消选择"
            }
            
    except Exception as e:
        logger.error(f"选择数据库文件失败: {str(e)}")
        return {
            "success": False,
            "message": f"选择数据库文件失败: {str(e)}"
        }


@router.get("/defaults")
async def get_default_config():
    """获取系统默认配置值"""
    try:
        # 获取默认配置路径
        _, default_config_path = get_config_paths()
        
        if not default_config_path.exists():
            raise HTTPException(status_code=404, detail="默认配置文件不存在")
        
        with open(default_config_path, 'r', encoding='utf-8') as f:
            default_config = json.load(f)
        
        # 只返回用户可配置的部分（数据库路径已从用户界面移除）
        user_defaults = {
            "dashscope": {
                "model": default_config.get("dashscope", {}).get("model", ""),
                "api_key": default_config.get("dashscope", {}).get("api_key", ""),
                "available_models": default_config.get("dashscope", {}).get("available_models", [])
            },
            "storage": {
                "base_path": default_config.get("storage", {}).get("base_path", ""),
                "thumbnail_quality": default_config.get("storage", {}).get("thumbnail_quality", 85),
                "thumbnail_size": default_config.get("storage", {}).get("thumbnail_size", 300)
            },
            # 数据库路径已从用户界面移除
            "system": {
                "max_file_size": default_config.get("system", {}).get("max_file_size", 52428800)
            },
            "ui": {
                "photos_per_page": default_config.get("ui", {}).get("photos_per_page", 12),
                "similar_photos_limit": default_config.get("ui", {}).get("similar_photos_limit", 8)
            },
            "search": {
                "similarity_threshold": default_config.get("search", {}).get("similarity_threshold", 0.6)
            },
            "analysis": {
                "duplicate_threshold": default_config.get("analysis", {}).get("duplicate_threshold", 5)
            },
            "image_features": {
                "similarity_threshold": default_config.get("image_features", {}).get("similarity_threshold", 0.5)
            }
        }
        
        return {
            "success": True,
            "data": user_defaults
        }
    except Exception as e:
        logger.error(f"获取默认配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取默认配置失败: {str(e)}")