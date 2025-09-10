#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
家庭单机版智能照片整理系统 - 主入口文件

该文件是整个应用的主入口，负责：
1. 初始化FastAPI应用
2. 配置中间件
3. 注册路由
4. 启动服务器

作者：AI助手
创建日期：2025年9月9日
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.models import base

# 创建数据库表
base.Base.metadata.create_all(bind=engine)

# 设置日志
setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="家庭单机版智能照片整理系统",
    description="基于AI技术的智能照片管理平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册API路由
app.include_router(api_router, prefix="/api/v1")

# 健康检查接口
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "系统运行正常"}

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用家庭单机版智能照片整理系统",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    # 使用更精确的文件监控策略
    # if settings.debug:
    #     # 开发模式：只监控特定的Python文件
    #     uvicorn.run(
    #         "main:app",
    #         host=settings.server_host,
    #         port=settings.server_port,
    #         reload=True,
    #         reload_dirs=["app"],
    #         reload_excludes=[
    #             "**/__pycache__/**",
    #             "**/*.pyc",
    #             "**/*.pyo",
    #             "**/.pytest_cache/**",
    #             "**/logs/**",
    #             "**/photos_storage/**",
    #             "**/data/**",
    #             "**/temp/**",
    #             "**/1.prepare/**",
    #             "**/doc/**",
    #             "**/venv/**",
    #         ],
    #         log_level="info"
    #     )
    # else:
    #     # 生产模式：禁用reload
    #     uvicorn.run(
    #         "main:app",
    #         host=settings.server_host,
    #         port=settings.server_port,
    #         reload=False,
    #         log_level="info"
    #     )
        # 禁用reload模式，避免watchfiles检测问题
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False,  # 完全禁用reload模式
        log_level="info"
    )
