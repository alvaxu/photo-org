"""
家庭单机版智能照片整理系统 - 配置管理API
"""
import json
import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
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
        # 重新导入配置模块
        import app.core.config
        importlib.reload(app.core.config)
        
        # 更新全局配置实例
        global settings
        settings = app.core.config.settings
        
        logger.info("配置重新加载成功")
    except Exception as e:
        logger.error(f"配置重新加载失败: {str(e)}")
        raise e


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    dashscope: Dict[str, Any] = None
    storage: Dict[str, Any] = None
    database: Dict[str, Any] = None
    system: Dict[str, Any] = None
    ui: Dict[str, Any] = None
    search: Dict[str, Any] = None
    analysis: Dict[str, Any] = None


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
    """更新用户配置"""
    try:
        # 检查存储目录修改是否为本地访问
        if request.storage and 'base_path' in request.storage:
            if not is_local_access(http_request):
                raise HTTPException(status_code=403, detail="存储目录修改仅限本地访问")
        
        # 获取当前配置
        current_config = settings.get_full_config()
        
        # 更新用户配置部分（数据库路径已从用户界面移除）
        if request.dashscope:
            current_config["dashscope"].update(request.dashscope)
        if request.storage:
            current_config["storage"].update(request.storage)
        # 数据库路径不再通过用户界面更新
        if request.system:
            current_config["system"].update(request.system)
        if request.ui:
            current_config["ui"].update(request.ui)
        if request.search:
            current_config["search"].update(request.search)
        if request.analysis:
            current_config["analysis"].update(request.analysis)
        
        # 保存到配置文件
        config_path = "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
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
    """重置用户配置为默认值"""
    try:
        # 加载默认配置
        default_config_path = "config.default.json"
        if not os.path.exists(default_config_path):
            raise HTTPException(status_code=404, detail="默认配置文件不存在")
        
        with open(default_config_path, 'r', encoding='utf-8') as f:
            default_config = json.load(f)
        
        # 保存为当前配置
        config_path = "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
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
        # 读取 config_default.json 文件
        default_config_path = "config_default.json"
        if not os.path.exists(default_config_path):
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
            }
        }
        
        return {
            "success": True,
            "data": user_defaults
        }
    except Exception as e:
        logger.error(f"获取默认配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取默认配置失败: {str(e)}")