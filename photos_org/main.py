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
from fastapi.responses import RedirectResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sys
import os
import socket
from pathlib import Path
import io
import qrcode

from app.api import router as api_router
# 注意：settings 和 engine 现在使用延迟初始化，不在模块级别导入
# from app.core.config import settings  # ❌ 删除，改为在函数内导入
# from app.db.session import engine  # ❌ 删除，改为在函数内导入
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

# 初始化模板引擎（用于渲染启动信息页面）
def init_templates():
    """初始化Jinja2模板引擎"""
    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller环境
            exe_dir = Path(sys.executable).parent
            internal_dir = exe_dir / '_internal'
            templates_dir = str(internal_dir / 'templates')
        else:
            # 开发环境
            templates_dir = 'templates'
        from fastapi.templating import Jinja2Templates
        return Jinja2Templates(directory=templates_dir)
    except Exception as e:
        print(f"⚠️ 模板引擎初始化失败: {e}")
        return None

templates = init_templates()


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
    
    # 服务器启动后自动打开浏览器
    try:
        import webbrowser
        import threading
        import time
        
        def open_browser():
            """延迟打开浏览器，确保服务器完全启动"""
            time.sleep(2)  # 等待2秒确保服务器完全启动
            url = f"http://127.0.0.1:{settings.server_port}"
            try:
                webbrowser.open(url)
                print(f"✅ 已自动打开浏览器: {url}")
            except Exception as e:
                print(f"⚠️ 自动打开浏览器失败: {e}")
                print(f"   请手动在浏览器中访问: {url}")
        
        # 在后台线程中打开浏览器
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
    except Exception as e:
        print(f"⚠️ 浏览器自动打开功能初始化失败: {e}")
    
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

# 注意：存储目录挂载已移到 initialize_application() 函数中
# 这样可以确保在配置完成后才挂载存储目录

# 配置页面路由

@app.get("/settings")
async def settings_page():
    """配置页面"""
    return FileResponse(get_template_path("settings.html"))

@app.get("/people")
async def people_page():
    """人物管理页面"""
    return FileResponse(get_template_path("people-management.html"))

@app.get("/similar-photos")
async def similar_photos_page():
    """相似照识别页面"""
    return FileResponse(get_template_path("similar-photos.html"))

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

@app.get("/privacy-policy")
async def privacy_policy_page():
    """隐私策略页面"""
    return FileResponse(get_template_path("privacy-policy.html"))

@app.get("/people")
async def people_page():
    """人物管理页面"""
    return FileResponse(get_template_path("people-management.html"))

@app.get("/startup-info")
async def startup_info_page(request: Request):
    """启动信息页面 - 显示二维码和访问信息"""
    try:
        local_ip = get_local_ip()
        server_port = settings.server_port
        access_url = f"http://{local_ip}:{server_port}"
        
        if templates:
            return templates.TemplateResponse("startup-info.html", {
                "request": request,
                "local_ip": local_ip,
                "server_port": server_port,
                "access_url": access_url
            })
        else:
            # 如果模板引擎不可用，返回简单文本
            return Response(
                content=f"访问地址: {access_url}\n本机IP: {local_ip}\n端口: {server_port}",
                media_type="text/plain"
            )
    except Exception as e:
        return Response(
            content=f"错误: {str(e)}",
            status_code=500,
            media_type="text/plain"
        )

@app.get("/api/v1/startup-info/qrcode")
async def generate_qrcode():
    """生成访问二维码图片"""
    try:
        local_ip = get_local_ip()
        server_port = settings.server_port
        access_url = f"http://{local_ip}:{server_port}"
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(access_url)
        qr.make(fit=True)
        
        # 创建二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 将图片转换为字节流
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return Response(
            content=img_buffer.getvalue(),
            media_type="image/png"
        )
    except Exception as e:
        # 如果生成失败，返回一个简单的错误图片
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (200, 200), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 90), "QR Code\nError", fill='black')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return Response(
            content=img_buffer.getvalue(),
            media_type="image/png",
            status_code=500
        )

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


def setup_msix_first_run():
    """
    MSIX 环境首次启动配置
    
    如果检测到 MSIX 环境且路径为空，弹出对话框让用户选择基础目录
    """
    from app.core.config import is_msix_environment, get_config_paths
    import shutil
    import json
    
    # 检查是否是 MSIX 环境
    if not is_msix_environment():
        return False
    
    user_config_path, default_config_path = get_config_paths()
    
    # 如果用户配置不存在，拷贝默认配置
    if not user_config_path.exists() and default_config_path.exists():
        print("📋 首次启动：正在初始化用户配置...")
        user_config_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(default_config_path, user_config_path)
        print(f"✅ 已拷贝默认配置到: {user_config_path}")
        
        # 获取应用目录（使用与 get_config_paths() 相同的方式，确保一致性）
        import sys
        from pathlib import Path
        if getattr(sys, 'frozen', False):
            # PyInstaller打包环境：配置文件位于可执行文件所在目录
            exe_path = Path(sys.executable)
            app_dir = exe_path.parent
        else:
            # 开发环境：从当前文件位置推断
            app_dir = Path(__file__).parent
        
        # 注意：在 MSIX 环境下，default_config_path 的父目录就是应用目录
        # 使用 default_config_path 的父目录更可靠
        if default_config_path.exists():
            app_dir = default_config_path.parent
        
        # 加载配置并修改模型路径和 GPS 数据库路径为绝对路径
        with open(user_config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 修改人脸识别模型路径
        if 'face_recognition' in config_data:
            if 'models_base_path' in config_data['face_recognition']:
                models_path = Path(config_data['face_recognition']['models_base_path'])
                if not models_path.is_absolute():
                    # 相对路径：转换为绝对路径
                    config_data['face_recognition']['models_base_path'] = str((app_dir / models_path).resolve())
                    print(f"✅ 已设置人脸识别模型路径: {config_data['face_recognition']['models_base_path']}")
        
        # 修改图像特征提取模型路径
        if 'image_features' in config_data:
            if 'models_base_path' in config_data['image_features']:
                models_path = Path(config_data['image_features']['models_base_path'])
                if not models_path.is_absolute():
                    # 相对路径：转换为绝对路径
                    config_data['image_features']['models_base_path'] = str((app_dir / models_path).resolve())
                    print(f"✅ 已设置图像特征提取模型路径: {config_data['image_features']['models_base_path']}")
        
        # 修改 GPS 数据库路径
        if 'maps' in config_data:
            if 'offline_geocoding_db_path' in config_data['maps']:
                db_path = Path(config_data['maps']['offline_geocoding_db_path'])
                if not db_path.is_absolute():
                    # 相对路径：转换为绝对路径
                    config_data['maps']['offline_geocoding_db_path'] = str((app_dir / db_path).resolve())
                    print(f"✅ 已设置 GPS 数据库路径: {config_data['maps']['offline_geocoding_db_path']}")
        
        # 保存修改后的配置
        with open(user_config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        # 重新加载配置
        import importlib
        import app.core.config
        importlib.reload(app.core.config)
    
    # 检查关键路径是否为空（使用最新的 settings）
    from app.core.config import settings
    if not settings.database.path or not settings.storage.base_path or not settings.logging.file_path:
        print("\n" + "="*60)
        print("🔧 首次启动配置")
        print("="*60)
        print("检测到路径未配置，需要选择数据存储目录")
        print()
        
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox
            
            # 创建根窗口
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            root.attributes('-topmost', True)  # 置顶显示
            
            # 显示提示信息
            messagebox.showinfo(
                "首次启动配置",
                "欢迎使用家庭版智能照片系统！\n\n"
                "请选择一个目录用于存储您的照片数据。\n"
                "建议选择一个有足够空间的位置，例如：\n"
                "- D:\\PhotoSystem\n"
                "- E:\\MyPhotos\\PhotoSystem\n\n"
                "系统将在此目录下创建以下子目录：\n"
                "- photo_db/ (数据库)\n"
                "- storage/ (照片存储)\n"
                "- logs/ (日志文件)"
            )
            
            # 选择基础目录
            base_dir = filedialog.askdirectory(
                title="选择数据存储目录",
                initialdir="C:\\"
            )
            
            root.destroy()
            
            if not base_dir:
                print("❌ 用户取消配置，系统无法启动")
                print("   请重新启动应用并完成配置")
                sys.exit(1)
            
            base_path = Path(base_dir)
            print(f"✅ 用户选择的基础目录: {base_path}")
            
            # 复制"使用说明.pdf"到用户选择的目录
            try:
                # 在 MSIX 环境中，查找"使用说明.pdf"的位置
                if getattr(sys, 'frozen', False):
                    exe_path = Path(sys.executable)
                    app_dir = exe_path.parent
                else:
                    app_dir = Path(__file__).parent
                
                # 尝试在多个可能的位置查找"使用说明.pdf"
                manual_pdf_source = None
                possible_locations = [
                    app_dir / "Assets" / "使用说明.pdf",  # 最常见的位置
                    app_dir / "使用说明.pdf",  # 应用目录根目录
                    app_dir.parent / "Assets" / "使用说明.pdf",  # 如果 app_dir 是 PhotoSystem 子目录
                    app_dir.parent / "使用说明.pdf",  # 父目录
                ]
                
                # 如果 app_dir 是 PhotoSystem 子目录，也检查同级的 Assets
                if app_dir.name == "PhotoSystem":
                    possible_locations.extend([
                        app_dir.parent / "PhotoSystem" / "Assets" / "使用说明.pdf",
                        app_dir.parent / "PhotoSystem" / "使用说明.pdf",
                    ])
                
                for location in possible_locations:
                    if location.exists() and location.is_file():
                        manual_pdf_source = location
                        print(f"📄 找到使用说明.pdf: {location}")
                        break
                
                if manual_pdf_source:
                    manual_pdf_dest = base_path / "使用说明.pdf"
                    try:
                        # 如果目标文件已存在，询问是否覆盖（这里直接覆盖，因为是首次配置）
                        if manual_pdf_dest.exists():
                            print(f"⚠️  目标文件已存在，将覆盖: {manual_pdf_dest}")
                        shutil.copy2(manual_pdf_source, manual_pdf_dest)
                        print(f"✅ 已复制使用说明.pdf到: {manual_pdf_dest}")
                    except Exception as e:
                        print(f"⚠️  复制使用说明.pdf失败: {e}")
                else:
                    # 不显示警告，因为这不是关键功能
                    pass  # 静默失败，不影响配置流程
            except Exception as e:
                # 静默处理错误，不影响配置流程
                pass  # 不显示错误，因为这不是关键功能
            
            # 根据基础目录生成三个路径
            database_path = base_path / "photo_db" / "photos.db"
            storage_base_path = base_path / "storage"
            logging_file_path = base_path / "logs" / "app.log"
            
            # 加载当前配置
            with open(user_config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新路径
            config_data['database']['path'] = str(database_path)
            config_data['storage']['base_path'] = str(storage_base_path)
            config_data['logging']['file_path'] = str(logging_file_path)
            
            # 保存配置
            with open(user_config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 配置已保存:")
            print(f"   数据库路径: {database_path}")
            print(f"   存储路径: {storage_base_path}")
            print(f"   日志路径: {logging_file_path}")
            
            # 重新加载配置（使用新的 reload_settings 函数）
            from app.core.config import reload_settings
            reload_settings()
            
            print("✅ 配置加载完成")
            print()
            return True
            
        except Exception as e:
            print(f"❌ 配置过程出错: {e}")
            print("   请重新启动应用并完成配置")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    return False


def initialize_application():
    """
    初始化应用（在配置完成后调用）
    
    此函数会：
    1. 重新加载配置（确保使用最新配置）
    2. 重新创建数据库引擎（使用最新路径）
    3. 初始化日志系统（使用最新路径）
    4. 挂载存储目录（使用最新路径）
    5. 初始化数据库
    
    返回 settings 和 engine 对象
    """
    from app.core.config import get_settings, reload_settings
    from app.db.session import get_engine, reload_engine
    from app.core.logging import setup_logging
    
    # 重新加载配置（确保使用最新配置）
    print("📋 正在加载配置...")
    settings = reload_settings()
    print("✅ 配置加载完成")
    
    # 重新创建数据库引擎（使用最新路径）
    print("🔧 正在初始化数据库引擎...")
    engine = reload_engine()
    print("✅ 数据库引擎初始化完成")
    
    # 初始化日志系统（使用最新路径）
    print("📝 正在配置日志系统...")
    setup_logging()
    print("✅ 日志系统配置完成")
    
    # 挂载存储目录（使用最新路径）
    print("📁 正在挂载存储目录...")
    from app.core.path_utils import resolve_resource_path
    photos_storage_dir = resolve_resource_path(settings.storage.base_path)
    
    # 确保存储目录存在
    photos_storage_dir.mkdir(parents=True, exist_ok=True)
    
    # 挂载存储目录
    app.mount("/photos_storage", StaticFiles(directory=str(photos_storage_dir)), name="photos_storage")
    print(f"✅ 存储目录已挂载")
    
    return settings, engine, photos_storage_dir


# 路径解析函数已移至 app.core.path_utils，这里导入以便向后兼容
from app.core.path_utils import resolve_resource_path


def print_resource_paths(settings, storage_path=None, database_path=None):
    """
    打印当前环境下真正起作用的资源路径（用于诊断）
    
    :param settings: 应用配置对象
    :param storage_path: 存储路径（Path对象，可选）
    :param database_path: 数据库路径（Path对象，可选）
    """
    import sys
    from app.core.config import is_msix_environment
    from pathlib import Path
    
    # 判断当前运行环境
    if getattr(sys, 'frozen', False):
        if is_msix_environment():
            env_name = "MSIX环境"
        else:
            env_name = "PyInstaller Portable环境"
    else:
        env_name = "开发环境"
    
    print("\n" + "="*60)
    print(f"📁 资源路径配置（{env_name}）")
    print("="*60)
    
    # 导入路径解析函数（在函数内部导入，避免循环依赖）
    from app.core.path_utils import resolve_resource_path
    
    # 1. 数据库路径
    if database_path:
        db_path = Path(database_path)
        print(f"   数据库路径: {db_path}")
        if not db_path.parent.exists():
            print(f"   ⚠️  警告: 数据库目录不存在")
    
    # 2. 存储路径
    if storage_path:
        storage_dir = Path(storage_path)
        print(f"   存储路径: {storage_dir}")
        if not storage_dir.exists():
            print(f"   ⚠️  警告: 存储目录不存在")
    
    # 3. 人脸识别模型路径
    if hasattr(settings, 'face_recognition') and settings.face_recognition.models_base_path:
        face_models_path = resolve_resource_path(settings.face_recognition.models_base_path)
        print(f"   人脸识别模型路径: {face_models_path}")
        if not face_models_path.exists():
            print(f"   ⚠️  警告: 路径不存在")
    
    # 4. 图像特征提取模型路径
    if hasattr(settings, 'image_features') and settings.image_features.models_base_path:
        image_models_path = resolve_resource_path(settings.image_features.models_base_path)
        print(f"   图像特征提取模型路径: {image_models_path}")
        if not image_models_path.exists():
            print(f"   ⚠️  警告: 路径不存在")
    
    # 5. GPS数据库路径
    if hasattr(settings, 'maps') and settings.maps.offline_geocoding_db_path:
        gps_db_path = resolve_resource_path(settings.maps.offline_geocoding_db_path)
        print(f"   GPS数据库路径: {gps_db_path}")
        if not gps_db_path.exists():
            print(f"   ⚠️  警告: 路径不存在")
    
    print("="*60)
    print()


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

    # ===== MSIX 首次启动配置检查 =====
    setup_msix_first_run()

    print("🚀 正在启动系统，首次启动需要1分钟左右，请稍候...")
    print()

    # ===== 初始化应用（在配置完成后） =====
    settings, engine, photos_storage_dir = initialize_application()

    # ===== 系统初始化 =====

    # 确保数据库目录存在
    print("📁 正在检查数据库目录...")
    from pathlib import Path

    # 处理数据库路径（使用统一的路径解析函数）
    from app.core.path_utils import resolve_resource_path
    db_path = resolve_resource_path(settings.database.path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 更新配置中的数据库路径为绝对路径
    settings.database.path = str(db_path)

    # ===== 打印资源路径（用于诊断） =====
    print_resource_paths(settings, storage_path=photos_storage_dir, database_path=db_path)

    # 创建数据库表
    print("🗄️  正在创建或检查数据库表...")
    base.Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建或检查完成")

    # 检查并添加缺失的数据库字段
    print("🔧 正在检查数据库字段...")
    # 临时禁用INFO日志
    import logging
    migration_logger = logging.getLogger('app.services.database_migration_service')
    original_level = migration_logger.level
    migration_logger.setLevel(logging.WARNING)
    
    try:
        from app.services.database_migration_service import (
            check_and_add_image_features_fields,
            check_and_add_similar_photo_cluster_fields,
            check_and_add_favorite_field
        )
        check_and_add_image_features_fields()
        check_and_add_similar_photo_cluster_fields()
        check_and_add_favorite_field()
    finally:
        migration_logger.setLevel(original_level)
    print("✅ 数据库字段检查完成")

    # 优化人脸识别数据库（添加索引和清理无效数据）
    print("🔧 正在优化人脸识别数据库...")
    # 临时禁用INFO日志
    optimization_logger = logging.getLogger('app.services.face_database_optimization_service')
    original_level = optimization_logger.level
    optimization_logger.setLevel(logging.WARNING)
    
    try:
        from app.services.face_database_optimization_service import optimize_face_recognition_database
        optimize_face_recognition_database()
    finally:
        optimization_logger.setLevel(original_level)
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
    # 临时禁用INFO日志
    index_logger = logging.getLogger('app.services.index_management_service')
    original_level = index_logger.level
    index_logger.setLevel(logging.WARNING)
    
    try:
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
    finally:
        index_logger.setLevel(original_level)

    # 注意：日志系统已在 initialize_application() 中配置

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
    print("-" * 15+"请按住ctrl键点击如下链接打开系统页面或等待自动进入系统页面"+"-" * 15)
    print(f"🌐 本机访问: http://127.0.0.1:{settings.server_port}")
    print(f"📱 二维码页面: http://127.0.0.1:{settings.server_port}/startup-info")
    print("-" * 15+"其他设备访问地址（同一网络）"+"-" * 15)
    print(f"🌐 网络访问: http://{local_ip}:{settings.server_port}")
    print("💡 提示：打开二维码页面，手机📱扫描二维码即可快速连接！")
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
