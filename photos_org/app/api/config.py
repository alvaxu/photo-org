"""
家庭单机版智能照片整理系统 - 配置管理API
"""
import json
import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
import importlib

logger = get_logger(__name__)
router = APIRouter()

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
async def update_user_config(request: ConfigUpdateRequest):
    """更新用户配置"""
    try:
        # 获取当前配置
        current_config = settings.get_full_config()
        
        # 更新用户配置部分
        if request.dashscope:
            current_config["dashscope"].update(request.dashscope)
        if request.storage:
            current_config["storage"].update(request.storage)
        if request.database:
            current_config["database"].update(request.database)
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
async def select_directory():
    """选择目录API"""
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
