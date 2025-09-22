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
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.formparsers import MultiPartParser
import sys
import os
import socket
from pathlib import Path

from app.api import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.models import base
from app.services.storage_service import StorageService

# 辅助函数：获取模板文件路径（兼容PyInstaller环境）
def get_template_path(filename):
    """获取模板文件路径，支持PyInstaller环境"""
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的环境：模板文件在_internal目录中
        exe_dir = Path(sys.executable).parent
        internal_dir = exe_dir / '_internal'
        return str(internal_dir / 'templates' / filename)
    else:
        # 开发环境
        return os.path.join('templates', filename)


# 辅助函数：获取本机IP地址
def get_local_ip():
    """获取本机IP地址"""
    try:
        # 创建一个socket连接到外部服务器来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # 连接到Google DNS服务器
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # 如果无法获取外部IP，尝试获取本地网络接口IP
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip
        except Exception:
            return "127.0.0.1"  # 最后的fallback



# 创建FastAPI应用
app = FastAPI(
    title="家庭版智能照片系统",
    description="基于AI技术的智能照片管理平台",
    version="2.1.2",
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

# 创建自定义的multipart解析器
from starlette.formparsers import MultiPartParser as OriginalMultiPartParser

class CustomMultiPartParser(OriginalMultiPartParser):
    """自定义MultiPartParser，支持更多文件"""

    def __init__(self, headers, stream, *, max_files=5000, max_fields=5000):
        super().__init__(headers, stream, max_files=max_files, max_fields=max_fields)

# 替换默认的MultiPartParser
import starlette.formparsers
starlette.formparsers.MultiPartParser = CustomMultiPartParser

print(f"✅ 已替换MultiPartParser类，默认限制: max_files=5000, max_fields=5000")

# 注册API路由
app.include_router(api_router, prefix="/api/v1")

# 注册增强搜索API路由
from app.api.enhanced_search import router as enhanced_search_router
app.include_router(enhanced_search_router)


# 挂载静态文件
import sys
import os
from pathlib import Path

# 获取正确的文件路径（支持PyInstaller环境）
if getattr(sys, 'frozen', False):
    # PyInstaller打包后的环境：静态文件在_internal目录中
    exe_dir = Path(sys.executable).parent
    internal_dir = exe_dir / '_internal'
    static_path = str(internal_dir / 'static')
    templates_path = str(internal_dir / 'templates')
else:
    # 开发环境
    static_path = 'static'
    templates_path = 'templates'

app.mount("/static", StaticFiles(directory=static_path), name="static")

# 动态挂载照片存储目录（根据用户配置）
photos_storage_path = Path(settings.storage.base_path)

# 在PyInstaller打包环境中处理存储路径
if getattr(sys, 'frozen', False):
    # 解压目录运行时，storage目录与exe在同一级目录
    exe_dir = Path(sys.executable).parent
    photos_storage_dir = exe_dir / "storage"
    photos_storage_dir.mkdir(exist_ok=True)
else:
    # 开发环境
    photos_storage_dir = Path(settings.storage.base_path)

# 挂载存储目录
app.mount("/photos_storage", StaticFiles(directory=str(photos_storage_dir)), name="photos_storage")

# 配置页面路由

@app.get("/settings")
async def settings_page():
    """配置页面"""
    return FileResponse(get_template_path("settings.html"))

@app.get("/help-api-key")
async def help_api_key_page():
    """API密钥帮助页面"""
    return FileResponse(get_template_path("help-api-key.html"))

@app.get("/help-overview")
async def help_overview_page():
    """功能说明帮助页面"""
    return FileResponse(get_template_path("help-overview.html"))

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
    print("\n" + "="*60)
    print("🏠 家庭版智能照片系统")
    print("="*60)

    # 显示运行模式
    if getattr(sys, 'frozen', False):
        print("📦 运行模式: PyInstaller打包环境")
    else:
        print("🔧 运行模式: 开发环境 (直接Python运行)")

    print("🚀 正在启动系统，请稍候...")
    print()

    # ===== 系统初始化 =====

    # 确保数据库目录存在
    print("📁 正在检查数据库目录...")
    from pathlib import Path

    # 在PyInstaller环境下，确保数据库路径相对于可执行文件目录
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        db_path = exe_dir / settings.database.path.lstrip('./')
    else:
        db_path = Path(settings.database.path)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"✅ 数据库目录: {db_path.parent}")

    # 更新配置中的数据库路径（如果需要）
    if getattr(sys, 'frozen', False) and not settings.database.path.startswith(str(exe_dir)):
        settings.database.path = str(db_path)

    # 创建数据库表
    print("🗄️  正在创建数据库表...")
    base.Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")

    # 初始化系统分类
    print("🏷️  正在初始化系统分类...")
    from app.services.init_system_categories import init_system_categories
    init_system_categories()
    print("✅ 系统分类初始化完成")

    # 初始化FTS表
    print("🔍 正在初始化全文搜索...")
    from app.services.fts_service import FTSService
    from app.db.session import get_db
    fts_service = FTSService()
    db = next(get_db())
    try:
        fts_service.create_fts_table(db)
        print("✅ 全文搜索初始化完成")
    finally:
        db.close()

    # 设置日志系统
    print("📝 正在配置日志系统...")
    setup_logging()
    print("✅ 日志系统配置完成")

    # 初始化存储服务
    print("💾 正在初始化存储服务...")
    storage_service = StorageService()
    print("✅ 存储服务初始化完成")

    # ===== 系统状态检查 =====

    # 检查API_KEY配置
    print("🔑 正在检查API配置...")
    api_key_status = "✅ 已配置" if settings.dashscope.api_key else "❌ 未配置"
    api_key_warning = "" if settings.dashscope.api_key else "⚠️  未配置API_KEY，AI分析功能将不可用"
    print(f"   API_KEY状态: {api_key_status}")

    # 检查FTS表状态
    print("🔍 正在检查搜索功能...")
    db_check = next(get_db())
    try:
        fts_status = "✅ 已创建" if fts_service.check_fts_table_exists(db_check) else "❌ 未创建"
        print(f"   全文搜索状态: {fts_status}")
    finally:
        db_check.close()

    # ===== 初始化完成 =====
    print("\n" + "="*60)
    print("✅ 系统初始化完成")
    print("="*60)
    print(f"📁 存储路径: {settings.storage.base_path}")
    print(f"🔑 API_KEY状态: {api_key_status}")
    if api_key_warning:
        print(f"   {api_key_warning}")

    # ===== 启动服务器 =====
    # 获取本机IP地址用于显示
    local_ip = get_local_ip()

    print("\n🌐 正在启动Web服务器...")
    print(f"   绑定地址: {settings.server_host}")
    print(f"   端口: {settings.server_port}")
    print(f"   本机IP: {local_ip}")
    print(f"   日志级别: {settings.logging.level.lower()}")

    # 启动成功提示
    print("=" * 60)
    print("🚀 家庭版智能照片系统启动成功！")
    print("=" * 60)
    print()
    print("-" * 15+"请按住ctrl键点击如下链接打开系统页面"+"-" * 15)
    print(f"🌐 本机访问: http://127.0.0.1:{settings.server_port}")
    print(f"📖 本机帮助页面: http://127.0.0.1:{settings.server_port}/help-overview")
    print(f"⚙️ 本机配置页面: http://127.0.0.1:{settings.server_port}/settings")
    if not settings.dashscope.api_key:
        print(f"🔧 配置API_KEY: http://127.0.0.1:{settings.server_port}/settings")
    print("-" * 15+"其他设备访问地址（同一网络）"+"-" * 15)
    print(f"🌐 网络访问: http://{local_ip}:{settings.server_port}")
    print(f"📖 网络帮助页面: http://{local_ip}:{settings.server_port}/help-overview")
    print(f"⚙️ 网络配置页面: http://{local_ip}:{settings.server_port}/settings")
    print("=" * 60)
    # 禁用reload模式，避免watchfiles检测问题
    uvicorn.run(
        app,  # 直接传递app对象，避免PyInstaller环境下的模块导入问题
        host=settings.server_host,
        port=settings.server_port,
        reload=False,  # 完全禁用reload模式
        log_level=settings.logging.level.lower(),
        access_log=False  # 完全禁用访问日志
    )
