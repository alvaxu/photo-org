# 家庭版智能照片系统

基于AI技术的智能照片管理平台，支持照片自动分析、分类、标签生成和重复检测。采用B/S架构，完全本地化部署，保护用户隐私。

## 🚀 核心功能特性

### 📸 照片管理
- **智能导入**：支持单文件上传、文件夹扫描、批量导入
- **元数据提取**：自动提取EXIF信息（拍摄时间、相机信息、GPS位置）
- **缩略图生成**：自动生成高质量缩略图，支持自定义尺寸和质量
- **文件组织**：按年月日自动创建文件夹结构，便于管理

### 🤖 AI智能分析
- **内容分析**：集成DashScope Qwen-VL模型，识别场景、物体、人物、情感
- **自动分类**：基于AI分析结果智能分类（家庭照片、旅行照片、工作照片、节日照片、其他）
- **标签生成**：自动生成中文描述性标签，支持手动编辑
- **质量评估**：分析照片清晰度、亮度、对比度等质量指标
- **重复检测**：智能识别和处理重复照片，支持智能处理

### 🔍 搜索与筛选
- **全文搜索**：基于SQLite FTS5的高效全文搜索，支持中文分词和复杂查询
- **多维度搜索**：支持关键词、相机信息、日期范围、质量等级搜索
- **高级筛选**：按标签、分类、地理位置、文件大小等条件筛选
- **相似照片**：基于AI分析结果推荐相似照片
- **智能排序**：支持按时间、质量、文件大小等多种方式排序

### ⚙️ 系统管理
- **配置管理**：Web界面配置系统参数，支持原生文件/目录选择对话框
- **存储管理**：灵活的存储路径配置，支持备份和恢复
- **用户界面**：响应式设计，支持桌面和移动设备
- **数据统计**：照片数量、存储空间、分类统计等

### 🔒 隐私保护
- **本地化部署**：所有数据存储在本地，不上传到云端
- **离线模式**：支持离线使用，AI分析结果可缓存
- **数据安全**：敏感配置通过环境变量管理

## 📦 快速开始（用户版）

### 一键安装包
如果您是普通用户，建议使用我们提供的一键安装包：

#### Windows 用户
1. 下载 `PhotoSystem-Installer.zip`
2. 解压到任意目录
3. 双击运行 `install.bat`
4. 按照提示选择安装和存储路径
5. 安装完成后，双击桌面快捷方式启动

#### Linux/macOS 用户
1. 下载 `PhotoSystem-Installer.tar.gz`
2. 解压：`tar -xzf PhotoSystem-Installer.tar.gz`
3. 运行：`chmod +x install.sh && ./install.sh`
4. 按照提示选择安装和存储路径
5. 安装完成后，点击桌面快捷图标启动

### 访问系统
安装完成后，在浏览器中访问：`http://localhost:8000`

---

## 🛠️ 开发者指南

### 环境搭建

#### 1. 克隆项目
```bash
git clone <repository-url>
cd photos_org
```

#### 2. 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量
```bash
# Windows
set DASHSCOPE_API_KEY=your_api_key_here

# Linux/macOS
export DASHSCOPE_API_KEY=your_api_key_here
```

#### 5. 初始化数据库
```bash
python main.py
```

### 打包分发

#### 生成安装包
```bash
# Windows
build_installer.bat

# Linux/macOS
chmod +x build_installer.sh
./build_installer.sh
```

打包完成后会在项目根目录生成：
- `PhotoSystem-Installer.zip` (Windows)
- `PhotoSystem-Installer.tar.gz` (Linux/macOS)

## 📋 系统要求

### 硬件要求
- **处理器**：Intel i5/Ryzen 5及以上（推荐i7/Ryzen 7）
- **内存**：8GB RAM及以上（推荐16GB）
- **存储**：100GB可用空间（推荐SSD，提高访问速度）
- **网络**：稳定的互联网连接（用于AI分析，支持离线缓存）

### 软件要求
- **Python**：3.8 - 3.11（推荐3.9+）
- **操作系统**：
  - Windows 10/11（主要支持）
  - macOS 10.15+
  - Ubuntu 18.04+
- **浏览器**：Chrome 90+、Firefox 88+、Safari 14+、Edge 90+

### 依赖服务
- **DashScope API**：阿里云大模型服务（用于AI分析）
- **SQLite**：内置数据库，无需额外安装

## 🛠️ 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <项目仓库地址>
cd photos_org

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. 安装依赖
```bash
# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 3. 配置系统
```bash
# 获取DashScope API密钥
# 访问 https://dashscope.aliyuncs.com/ 注册并获取API Key

# 设置环境变量（推荐方式）
set DASHSCOPE_API_KEY=your_actual_api_key_here  # Windows
export DASHSCOPE_API_KEY=your_actual_api_key_here  # macOS/Linux

# 或者直接编辑 config.json 文件
```

### 4. 启动系统
```bash
# 启动服务
python main.py

# 系统将在 http://127.0.0.1:8000 启动
# 访问 http://127.0.0.1:8000 开始使用
```

### 5. 首次使用
1. 访问系统配置页面：http://127.0.0.1:8000/settings
2. 配置照片存储目录和数据库位置
3. 导入照片并开始AI分析
4. 享受智能照片管理体验！

## 📖 使用指南

### 系统访问
- **主界面**：http://127.0.0.1:8000
- **配置管理**：http://127.0.0.1:8000/settings
- **API文档**：http://127.0.0.1:8000/docs
- **健康检查**：http://127.0.0.1:8000/health

### 主要功能使用

#### 1. 照片导入
- **单文件上传**：点击"导入照片"按钮，选择文件上传
- **文件夹扫描**：选择"扫描文件夹"模式，选择包含照片的文件夹
- **智能处理**：支持同时导入多张照片，自动生成缩略图

#### 2. AI智能分析
- **自动分析**：导入后自动进行内容分析、质量评估、重复检测
- **批量分析**：可对多张照片进行批量AI分析
- **分析结果**：查看照片的AI描述、质量评分、相似照片推荐

#### 3. 照片管理
- **浏览照片**：网格视图和列表视图切换
- **搜索筛选**：按关键词、日期、质量、标签等条件筛选
- **批量操作**：选择多张照片进行批量删除、分类等操作
- **照片详情**：点击照片查看详细信息、EXIF数据、AI分析结果

#### 4. 系统配置
- **存储设置**：配置照片存储目录和数据库位置
- **AI设置**：配置DashScope API密钥和模型选择
- **界面设置**：调整显示数量、排序方式等参数
- **搜索设置**：配置相似度阈值、重复检测参数

### 详细文档
- **用户配置管理使用指南**：`doc/用户配置管理使用指南.md`
- **开发环境搭建指南**：`doc/开发环境搭建指南.md`
- **API接口详细文档**：`doc/API接口详细文档.md`

## 🏗️ 技术架构

### 系统架构
- **前端**：HTML5 + CSS3 + JavaScript（ES6+） + Bootstrap 5.3 + 响应式设计
- **后端**：Python 3.8+ + FastAPI + SQLAlchemy 2.x + Pydantic-Settings
- **数据库**：SQLite（轻量级嵌入式数据库，内置FTS5全文搜索） + Alembic（数据库迁移）
- **AI服务**：DashScope Qwen-VL-Plus/Qwen-VL-Chat（阿里云大模型，支持多模型切换）
- **图像处理**：PIL + OpenCV + pillow-heif（HEIC支持） + imagehash（感知哈希）
- **异步处理**：asyncio + ThreadPoolExecutor + httpx
- **部署方式**：单机部署 + uvicorn服务器 + 本地Web服务

### 项目结构
```
photos_org/
├── app/                           # 应用核心代码
│   ├── api/                      # API路由层 (10个API模块, 70个接口)
│   │   ├── analysis.py           # AI分析API (7个接口)
│   │   ├── categories.py         # 分类管理API (8个接口)
│   │   ├── config.py             # 配置管理API (7个接口)
│   │   ├── enhanced_search.py    # 增强搜索API (5个接口)
│   │   ├── health.py             # 健康检查API (1个接口)
│   │   ├── import_photos.py      # 照片导入API (6个接口)
│   │   ├── photos.py             # 照片管理API (10个接口)
│   │   ├── search.py             # 基础搜索API (7个接口)
│   │   ├── storage.py            # 存储管理API (8个接口)
│   │   ├── tags.py               # 标签管理API (7个接口)
│   │   └── __init__.py           # API路由注册
│   ├── core/                     # 核心配置和工具
│   │   ├── config.py             # 配置管理
│   │   └── logging.py            # 日志管理
│   ├── db/                       # 数据库相关
│   │   └── session.py            # 数据库会话管理
│   ├── models/                   # 数据模型层
│   │   ├── base.py               # 基础模型
│   │   └── photo.py              # 照片相关模型
│   ├── schemas/                  # Pydantic数据模型
│   │   └── photo.py              # 照片数据模型
│   ├── services/                 # 业务服务层 (14个服务模块)
│   │   ├── analysis_service.py   # AI分析服务
│   │   ├── classification_service.py  # 分类服务
│   │   ├── dashscope_service.py  # DashScope API服务
│   │   ├── duplicate_detection_service.py  # 重复检测服务
│   │   ├── enhanced_similarity_service.py  # 增强相似度服务
│   │   ├── fts_service.py        # 全文搜索服务
│   │   ├── import_service.py     # 导入服务
│   │   ├── migration_service.py  # 数据库迁移服务
│   │   ├── photo_quality_service.py  # 照片质量服务
│   │   ├── photo_service.py      # 照片管理服务
│   │   ├── search_service.py     # 搜索服务
│   │   ├── storage_service.py    # 存储服务
│   │   └── enhanced_search_service.py  # 增强搜索服务
│   └── utils/                    # 工具函数
├── static/                       # 静态文件
│   ├── css/                      # 样式文件
│   ├── js/                       # JavaScript文件
│   │   ├── app-data.js           # 数据管理
│   │   ├── app-events.js         # 事件处理
│   │   ├── app-photos.js         # 照片管理
│   │   ├── app-ui.js             # UI组件
│   │   ├── user-config-manager.js  # 配置管理
│   │   └── ...                   # 其他JS模块
│   └── images/                   # 图片资源
├── templates/                    # 模板文件
│   └── settings.html             # 配置页面模板
├── tests/                        # 测试代码
│   ├── unit/                     # 单元测试
│   └── integration/              # 集成测试
├── doc/                          # 项目文档
│   ├── 用户配置管理使用指南.md      # 用户使用指南
│   ├── 开发环境搭建指南.md         # 开发指南
│   ├── API接口详细文档.md         # API文档
│   └── ...                       # 其他设计文档
├── utilities/                    # 工具脚本
├── config.json                   # 主配置文件
├── config.default.json           # 默认配置模板
├── main.py                       # 应用入口
├── requirements.txt              # 依赖包列表
└── README.md                     # 项目说明
```

## 🔧 配置说明

### 配置文件结构
- **config.json**：用户配置文件，包含用户可修改的参数
- **config_default.json**：系统默认配置文件，包含所有默认值
- **环境变量**：用于敏感信息（如API密钥），优先级最高
- **运行时配置**：支持部分配置的热更新，无需重启服务

### 核心配置项
```json
{
  "system": {
    "max_file_size": 52428800,           // 最大文件大小（50MB）
    "timeout": 10,                       // 请求超时时间（秒）
    "max_concurrent": 2,                 // 最大并发数
    "temp_file_max_age": 24              // 临时文件最大年龄（小时）
  },
  "database": {
    "path": "./photo_db/photos.db"       // 数据库文件路径
  },
  "dashscope": {
    "api_key": "${DASHSCOPE_API_KEY}",   // API密钥（环境变量优先）
    "model": "qwen-vl-plus",            // 当前使用的模型
    "available_models": [
      "qwen-vl-plus",
      "qwen-vl-plus-latest",
      "qwen-vl-plus-2025-08-15",
      "qwen-vl-plus-2025-05-07",
      "qwen-vl-plus-2025-01-25"
    ],  // 可用的模型列表
    "base_url": "https://dashscope.aliyuncs.com/api/v1",
    "timeout": 30,                       // API请求超时时间
    "max_retry_count": 3                 // 最大重试次数
  },
  "storage": {
    "base_path": "./storage",            // 存储根目录
    "originals_path": "originals",       // 原图存储路径
    "thumbnails_path": "thumbnails",     // 缩略图存储路径
    "thumbnail_size": 300,               // 缩略图尺寸
    "thumbnail_quality": 50              // 缩略图质量（1-100）
  },
  "ui": {
    "photos_per_page": 12,               // 每页显示照片数
    "similar_photos_count": 8,           // 相似照片显示数量
    "hot_tags_count": 10,                // 热门标签显示数量
    "hot_categories_count": 10           // 热门分类显示数量
  },
  "search": {
    "similarity_threshold": 0.6,         // 相似度阈值
    "duplicate_threshold": 5             // 重复检测阈值
  }
}
```

### 配置管理
- **Web界面配置**：访问 http://127.0.0.1:8000/settings
- **原生对话框**：支持文件/目录选择对话框（跨平台兼容）
- **环境变量优先**：API密钥等敏感信息优先使用环境变量
- **配置验证**：基于Pydantic的自动配置验证和类型检查
- **运行时更新**：部分配置支持热更新，无需重启服务
- **配置分层**：用户配置覆盖默认配置，灵活的配置管理

## 🧪 测试

### 测试框架
- **单元测试**：pytest + pytest-asyncio
- **集成测试**：httpx + FastAPI TestClient
- **测试覆盖**：核心业务逻辑和API接口

### 运行测试
```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行特定测试
pytest tests/integration/test_photo_import.py

# 生成测试报告
pytest --html=report.html --self-contained-html
```

### 测试内容
- **API接口测试**：所有REST API接口的功能测试
- **业务逻辑测试**：照片导入、AI分析、搜索等核心功能
- **数据库测试**：数据模型和数据库操作测试
- **前端测试**：用户界面交互测试

## 📚 开发文档

### 设计文档
- **家庭版详细设计文档.md**：系统整体架构和技术设计（v2.0）
- **数据库设计文档.md**：数据库结构设计和表关系（v2.0）
- **API接口详细文档.md**：REST API接口规范和示例（v3.0）
- **前端界面设计文档.md**：用户界面设计和交互规范（v2.0）

### 模块设计文档
- **照片导入模块详细设计文档.md**：照片导入功能设计（v2.0）
- **智能分析模块详细设计文档.md**：AI分析功能设计（v2.0）
- **分类标签模块详细设计文档.md**：分类和标签管理设计（v2.0）
- **搜索检索模块详细设计文档.md**：搜索功能设计（v2.0）
- **照片管理模块详细设计文档.md**：照片管理功能设计（v2.0）
- **存储管理模块详细设计文档.md**：文件存储管理设计（v2.0）
- **配置管理模块详细设计文档.md**：系统配置管理设计（v2.0）

### 用户文档
- **用户配置管理使用指南.md**：用户配置管理详细指南（v2.0）
- **开发环境搭建指南.md**：开发环境搭建和配置（v2.0）
- **服务人员配置管理手册.md**：系统管理员配置手册（v2.0）

### 技术规范
- **通用技术规范详细设计文档.md**：开发规范和编码标准
- **项目数据需求分析.md**：数据需求和业务分析

## 🤝 贡献指南

### 开发流程
1. Fork 项目到个人仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 遵循编码规范：使用 Black 格式化代码
4. 编写测试：确保新功能有对应的测试用例
5. 提交更改：`git commit -m 'Add some AmazingFeature'`
6. 推送分支：`git push origin feature/AmazingFeature`
7. 创建 Pull Request

### 编码规范
- **Python**：遵循 PEP 8，使用 Black 格式化，类型注解完整
- **JavaScript**：遵循 ES6+ 标准，使用 Prettier 格式化
- **注释**：函数和类必须有详细的文档字符串（支持中文）
- **测试**：新功能必须包含单元测试和集成测试
- **异步处理**：优先使用 asyncio，避免阻塞操作
- **配置管理**：使用 Pydantic-Settings，支持环境变量和验证

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 问题反馈

### 获取帮助
1. **查看文档**：首先查看 `doc/` 目录下的相关文档
2. **检查日志**：查看 `logs/app.log` 文件中的错误信息
3. **运行诊断**：使用 `utilities/diagnose_system.py` 进行系统诊断
4. **提交Issue**：在 GitHub Issues 中详细描述问题

### 问题报告模板
```markdown
**问题描述**：
**复现步骤**：
**期望行为**：
**实际行为**：
**系统环境**：
- 操作系统：
- Python版本：
- 浏览器版本：
**错误日志**：
```

## 🙏 致谢

### 开源项目
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的Web框架
- [SQLAlchemy](https://sqlalchemy.org/) - Python SQL工具包和ORM
- [SQLite](https://sqlite.org/) - 轻量级嵌入式数据库，支持FTS5全文搜索
- [Pydantic-Settings](https://pydantic-settings.readthedocs.io/) - 现代化配置管理
- [DashScope](https://dashscope.aliyun.com/) - 阿里云大模型服务
- [OpenCV](https://opencv.org/) - 计算机视觉库
- [Pillow](https://python-pillow.org/) - Python图像处理库
- [Bootstrap](https://getbootstrap.com/) - 前端UI框架
- [httpx](https://www.python-httpx.org/) - 异步HTTP客户端

### 技术栈
- **后端**：Python 3.8+ + FastAPI + SQLAlchemy 2.x + Pydantic-Settings + SQLite + Alembic
- **前端**：HTML5 + CSS3 + JavaScript（ES6+） + Bootstrap 5.3 + 响应式设计
- **AI服务**：DashScope Qwen-VL-Plus/Qwen-VL-Chat（支持多模型切换）
- **图像处理**：PIL + OpenCV + pillow-heif（HEIC支持） + imagehash（感知哈希）
- **异步处理**：asyncio + ThreadPoolExecutor + httpx
- **测试**：pytest + pytest-asyncio + httpx
- **全文搜索**：SQLite FTS5（高效中文全文搜索）

---

**版本**：v2.0.0
**最后更新**：2025年9月17日
**维护状态**：积极维护中 🚀
