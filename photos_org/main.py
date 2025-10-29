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
import sys
import os
import socket
from pathlib import Path

from app.api import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.models import base
# 导入所有模型以确保表被创建
from app.models import (
    Photo,
    PhotoAnalysis,
    PhotoQuality,
    Tag,
    Category,
    PhotoTag,
    PhotoCategory,
    DuplicateGroup,
    DuplicateGroupPhoto,
    FaceDetection,
    FaceCluster,
    FaceClusterMember,
    Person,
)
from app.services.storage_service import StorageService

import warnings
# 抑制 jieba 相关的警告
warnings.filterwarnings('ignore', category=SyntaxWarning, module='jieba.*')
warnings.filterwarnings('ignore', message='pkg_resources is deprecated', module='jieba.*')

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



# FastAPI应用已在上面创建

# 添加应用启动和关闭事件处理器
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("🚀 应用启动事件触发")
    yield
    # 关闭时
    print("🛑 应用关闭事件触发 - 清理后台任务...")
    try:
        # 这里可以添加清理逻辑，比如等待后台任务完成
        # 但是由于BackgroundTasks是异步的，这里主要用于日志记录
        print("✅ 后台任务清理完成")
    except Exception as e:
        print(f"⚠️ 后台任务清理过程中出现异常: {e}")

# 更新FastAPI应用配置
app = FastAPI(
    title="家庭版智能照片系统",
    description="基于AI技术的智能照片管理平台",
    version="4.0.0",  # 更新版本号
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # 使用新的生命周期管理
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

# 注册地图API路由
from app.api.maps import router as maps_router
app.include_router(maps_router, prefix="/api/maps")


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
config_path = Path(settings.storage.base_path)

if getattr(sys, 'frozen', False):
    # PyInstaller打包环境
    exe_dir = Path(sys.executable).parent

    if config_path.is_absolute():
        # 绝对路径：直接使用用户指定的路径
        photos_storage_dir = config_path
        print(f"📦 PyInstaller环境：使用绝对路径 {photos_storage_dir}")
    else:
        # 相对路径：相对于exe目录解析
        photos_storage_dir = exe_dir / config_path
        print(f"📦 PyInstaller环境：相对路径解析为 {photos_storage_dir}")

    # 确保存储目录存在
    photos_storage_dir.mkdir(parents=True, exist_ok=True)
else:
    # 开发环境
    if config_path.is_absolute():
        photos_storage_dir = config_path
        print(f"🔧 开发环境：使用绝对路径 {photos_storage_dir}")
    else:
        # 相对路径：相对于项目根目录
        project_root = Path(__file__).parent
        photos_storage_dir = project_root / config_path
        print(f"🔧 开发环境：相对路径解析为 {photos_storage_dir}")

    # 确保存储目录存在
    photos_storage_dir.mkdir(parents=True, exist_ok=True)

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

@app.get("/help-gaode-api-key")
async def help_gaode_api_key_page():
    """高德地图API配置帮助页面"""
    return FileResponse(get_template_path("help_gaode_api_key.html"))

@app.get("/people")
async def people_management_page():
    """人物管理页面"""
    return FileResponse(get_template_path("people-management.html"))

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

    # ===== 应用初始化开始 =====
    print("\n" + "="*60)
    print("🏠 家庭版智能照片系统")
    print("="*60)

    # 显示运行模式
    if getattr(sys, 'frozen', False):
        print("📦 运行模式: 打包环境")
    else:
        print("🔧 运行模式: 开发环境 (直接Python运行)")

    print("🚀 正在启动系统，首次启动需要1分钟左右，请稍候...")
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
    print("🗄️  正在创建或检查数据库表...")
    base.Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建或检查完成")

    # 优化人脸识别数据库（添加索引和清理无效数据）
    print("🔧 正在优化人脸识别数据库...")
    from app.services.face_database_optimization_service import optimize_face_recognition_database
    optimize_face_recognition_database()
    print("✅ 人脸识别数据库优化完成")

    # 初始化系统分类
    print("🏷️  正在初始化系统分类...")
    from app.services.init_system_categories import init_system_categories
    init_system_categories()
    print("✅ 系统分类初始化完成")

    # 初始化/升级FTS表
    print("🔍 正在初始化全文搜索...")
    from app.services.fts_service import FTSService
    from app.db.session import get_db
    fts_service = FTSService()
    db = next(get_db())
    try:
        # 检查FTS表是否存在
        if not fts_service.check_fts_table_exists(db):
            # 新建数据库，从0开始
            print("🆕 新建数据库，创建FTS表和触发器...")
            success = fts_service.create_fts_table(db)
            if success:
                print("✅ 全文搜索表创建完成")
            else:
                print("❌ 全文搜索表创建失败")
        else:
            # 已有数据库，检查FTS表版本
            print("🔍 检测到FTS表存在，检查版本...")
            current_version = fts_service.get_fts_version(db)

            try:
                if current_version < 3:
                    # 老版本FTS表，需要重建为V3
                    print(f"⬆️  FTS表版本{current_version}，重建到V3...")
                    success = fts_service.rebuild_fts_table_v3(db)
                    if success:
                        print("✅ FTS表重建到V3完成")
                    else:
                        print("❌ FTS表重建失败")
                else:
                    # 最新版本FTS表（V3），直接跳过
                    print(f"✅ FTS表已是最新版本{current_version}，无需操作")

                # 清理可能的备份表
                fts_service._cleanup_backup_table(db)

            except Exception as e:
                print(f"❌ FTS处理异常: {e}")
                # 继续启动，不因为FTS失败而停止应用
    finally:
        db.close()

    # 初始化数据库索引
    print("📊 正在检查数据库索引...")
    from app.services.index_management_service import IndexManagementService
    index_service = IndexManagementService()
    db = next(get_db())
    try:
        if index_service.ensure_indexes_exist(db):
            print("✅ 数据库索引检查完成")
        else:
            print("⚠️ 数据库索引检查失败，但不影响系统启动")
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
    print(f"📁 配置存储路径: {settings.storage.base_path}")
    print(f"📂 实际存储路径: {photos_storage_dir}")


    # 启动定期缓存清理任务
    print("🧹 启动定期缓存清理任务...")
    import threading
    import time
    from app.services.face_crop_service import face_crop_service
    
    def periodic_cache_cleanup():
        """定期清理过期缓存（同步版本）"""
        while True:
            try:
                # 每24小时清理一次过期缓存
                time.sleep(24 * 60 * 60)  # 24小时
                cleaned_count = face_crop_service.cleanup_old_cache(max_age_days=30)
                if cleaned_count > 0:
                    print(f"🧹 自动清理了 {cleaned_count} 个过期的人脸裁剪缓存文件")
            except Exception as e:
                print(f"❌ 定期缓存清理失败: {e}")
    
    # 在后台线程启动定期清理任务
    cleanup_thread = threading.Thread(target=periodic_cache_cleanup, daemon=True)
    cleanup_thread.start()
    print("✅ 定期缓存清理任务已启动")

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
    print("-" * 15+"其他设备访问地址（同一网络）"+"-" * 15)
    print(f"🌐 网络访问: http://{local_ip}:{settings.server_port}")
    print(f"📖 网络帮助页面: http://{local_ip}:{settings.server_port}/help-overview")
    print(f"⚙️ 网络配置页面: http://{local_ip}:{settings.server_port}/settings")
    print("=" * 60)
    
    # 启动服务器
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.logging.level.lower(),
        access_log=False,
        reload=False
    )
