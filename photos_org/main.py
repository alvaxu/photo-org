#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
家庭版智能照片系统 - 主入口文件

该文件是整个应用的主入口，负责：
1. 初始化FastAPI应用
2. 配置中间件
3. 注册路由
4. 启动服务器

作者：AI助手
创建日期：2025年9月9日

打包说明：
使用 PyInstaller 打包时，需要包含以下文件和目录：
- app/ 整个应用目录
- static/ 前端静态文件
- templates/ HTML模板文件
- config.json 配置文件
- requirements.txt 依赖列表
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.models import base
from app.services.storage_service import StorageService

# 创建FastAPI应用
app = FastAPI(
    title="家庭版智能照片系统",
    description="基于AI技术的智能照片管理平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置JSON响应，确保中文字符正确显示
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import json

# 重写FastAPI的默认JSON响应
from fastapi.responses import Response

class ChineseJSONResponse(Response):
    media_type = "application/json"
    
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str
        ).encode("utf-8")

# 替换默认的JSONResponse
app.default_response_class = ChineseJSONResponse

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix="/api/v1")

# 注册增强搜索API路由
from app.api.enhanced_search import router as enhanced_search_router
app.include_router(enhanced_search_router)


# 挂载静态文件
import sys
import os
from pathlib import Path

# 在PyInstaller打包环境中获取正确的静态文件路径
if getattr(sys, 'frozen', False):
    # PyInstaller打包后的环境
    base_path = sys._MEIPASS
    static_path = os.path.join(base_path, 'static')
else:
    # 开发环境
    static_path = 'static'

# 确保static目录存在
if not os.path.exists(static_path):
    print(f"Warning: Static directory not found at {static_path}")
    # 如果static目录不存在，使用当前目录下的static
    static_path = os.path.join(os.getcwd(), 'static')

app.mount("/static", StaticFiles(directory=static_path), name="static")

# 动态挂载照片存储目录（根据用户配置）
photos_storage_path = Path(settings.storage.base_path)

# 在PyInstaller打包环境中处理存储路径
if getattr(sys, 'frozen', False):
    # PyInstaller打包后的环境
    if photos_storage_path.is_absolute():
        # 如果是绝对路径，直接使用
        photos_storage_dir = str(photos_storage_path)
    else:
        # 如果是相对路径，相对于打包后的目录处理
        base_path = sys._MEIPASS
        if photos_storage_path.exists():
            # 如果相对路径存在（相对于原始工作目录），保持原样
            photos_storage_dir = str(photos_storage_path)
        else:
            # 如果不存在，尝试相对于打包目录查找
            alt_path = os.path.join(base_path, photos_storage_path.name)
            if os.path.exists(alt_path):
                photos_storage_dir = alt_path
            else:
                # 创建一个默认的存储目录
                photos_storage_dir = os.path.join(base_path, 'storage')
                os.makedirs(photos_storage_dir, exist_ok=True)
else:
    # 开发环境
    photos_storage_dir = str(photos_storage_path)

# 挂载存储目录
if os.path.exists(photos_storage_dir):
    app.mount("/photos_storage", StaticFiles(directory=photos_storage_dir), name="photos_storage")
    print(f"📁 Photos storage mounted at: {photos_storage_dir}")
else:
    # 如果存储目录不存在，创建一个默认的
    default_storage = os.path.join(sys._MEIPASS if getattr(sys, 'frozen', False) else '.', 'storage')
    os.makedirs(default_storage, exist_ok=True)
    app.mount("/photos_storage", StaticFiles(directory=default_storage), name="photos_storage")
    print(f"📁 Created default photos storage at: {default_storage}")

# 配置页面路由
from fastapi.responses import FileResponse

@app.get("/settings")
async def settings_page():
    """配置页面"""
    return FileResponse("templates/settings.html")

@app.get("/help-api-key")
async def help_api_key_page():
    """API密钥帮助页面"""
    return FileResponse("templates/help-api-key.html")

@app.get("/help-overview")
async def help_overview_page():
    """功能说明帮助页面"""
    return FileResponse("templates/help-overview.html")

# 健康检查接口
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "系统运行正常"}

# 根路径重定向到前端界面
@app.get("/")
async def root():
    """根路径 - 自动重定向到主功能页面"""
    return RedirectResponse(url="/static/index.html")


if __name__ == "__main__":
    import logging

    # ===== 应用初始化开始 =====

    # 确保数据库目录存在
    from pathlib import Path
    db_path = Path(settings.database.path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"✅ 数据库目录: {db_path.parent}")

    # 创建数据库表
    base.Base.metadata.create_all(bind=engine)

    # 初始化系统分类
    from app.services.init_system_categories import init_system_categories
    init_system_categories()

    # 初始化FTS表
    from app.services.fts_service import FTSService
    from app.db.session import get_db
    fts_service = FTSService()
    db = next(get_db())
    try:
        fts_service.create_fts_table(db)
    finally:
        db.close()

    # 设置日志
    setup_logging()

    # 初始化存储服务（自动创建目录）
    storage_service = StorageService()

    # 检查API_KEY配置
    api_key_status = "✅ 已配置" if settings.dashscope.api_key else "❌ 未配置"
    api_key_warning = "" if settings.dashscope.api_key else "⚠️  未配置API_KEY，AI分析功能将不可用"

    # 检查FTS表状态
    db_check = next(get_db())
    try:
        fts_status = "✅ 已创建" if fts_service.check_fts_table_exists(db_check) else "❌ 未创建"
    finally:
        db_check.close()

    # 启动成功提示
    print("=" * 60)
    print("🚀 家庭版智能照片系统启动成功！")
    print("=" * 60)
    print("✅ 数据库初始化完成")
    print("✅ 系统分类初始化完成")
    print("✅ 日志系统配置完成")
    print("✅ 存储服务初始化完成")
    print("✅ FastAPI应用配置完成")
    print(f"🔍 全文搜索表: {fts_status}")
    print(f"🔑 API_KEY状态: {api_key_status}")
    if api_key_warning:
        print(f"   {api_key_warning}")
    print("-" * 25+"本机访问地址"+"-" * 25)
    print(f"📁 存储路径: {settings.storage.base_path}")
    print(f"🌐 主页面: http://127.0.0.1:{settings.server_port}")
    print(f"📖 帮助页面: http://127.0.0.1:{settings.server_port}/help-overview")
    print(f"⚙️  API密钥申请帮助页面: http://127.0.0.1:{settings.server_port}/help-api-key")
    print(f"⚙️  配置页面: http://127.0.0.1:{settings.server_port}/settings")
    if not settings.dashscope.api_key:
        print(f"🔧 配置API_KEY: http://127.0.0.1:{settings.server_port}/settings")
   
    print("-" * 25+"远程访问地址"+"-" * 25)
    print(f"🌐 主页面: http://主机ip地址:{settings.server_port}")
    print(f"📖 帮助页面: http://主机ip地址:{settings.server_port}/help-overview")
    print("=" * 60)
    # ===== 应用初始化结束 =====

    # 禁用reload模式，避免watchfiles检测问题
    uvicorn.run(
        app,  # 直接传递app对象，避免PyInstaller环境下的模块导入问题
        host=settings.server_host,
        port=settings.server_port,
        reload=False,  # 完全禁用reload模式
        log_level=settings.logging.level.lower(),
        access_log=False  # 完全禁用访问日志
    )
