# 家庭单机版智能照片整理系统

基于AI技术的智能照片管理平台，支持照片自动分析、分类、标签生成和重复检测。

## 🚀 功能特性

- **智能分析**：集成DashScope Qwen-VL模型，自动分析照片内容
- **自动分类**：基于AI分析结果智能分类家庭照片
- **标签管理**：自动生成中文标签，支持手动编辑
- **重复检测**：智能识别和处理重复照片
- **质量评估**：分析照片清晰度、亮度、对比度等质量指标
- **本地化存储**：完全本地化部署，保护用户隐私

## 📋 系统要求

### 硬件要求
- **处理器**：Intel i5/Ryzen 5及以上
- **内存**：8GB RAM及以上
- **存储**：100GB可用空间（推荐SSD）
- **网络**：稳定的互联网连接（用于AI分析）

### 软件要求
- **Python**：3.8 - 3.11
- **操作系统**：
  - Windows 10/11
  - macOS 10.15+
  - Ubuntu 18.04+

## 🛠️ 安装部署

### 1. 克隆项目
```bash
git clone <项目仓库地址>
cd photos_org
```

### 2. 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
# 复制环境变量模板
cp env.example .env

# 编辑.env文件，填入DashScope API密钥
# DASHSCOPE_API_KEY=your_actual_api_key_here
```

### 5. 初始化数据库
```bash
python -c "from app.db.session import create_database; create_database()"
```

### 6. 启动服务
```bash
python main.py
```

服务将在 http://127.0.0.1:8000 启动

## 📖 使用指南

### 访问系统
打开浏览器访问：http://127.0.0.1:8000

### API文档
- **Swagger UI**：http://127.0.0.1:8000/docs
- **ReDoc**：http://127.0.0.1:8000/redoc

### 健康检查
访问：http://127.0.0.1:8000/health

## 🏗️ 项目结构

```
photos_org/
├── app/                    # 应用核心代码
│   ├── api/               # API路由层
│   ├── core/              # 核心配置和工具
│   ├── models/            # 数据模型层
│   ├── schemas/           # Pydantic数据模型
│   ├── services/          # 业务服务层
│   └── utils/             # 工具函数
├── static/                # 静态文件
│   ├── css/
│   ├── js/
│   └── images/
├── tests/                 # 测试代码
│   ├── unit/
│   └── integration/
├── data/                  # 数据存储目录
├── logs/                  # 日志文件目录
├── doc/                   # 项目文档
├── config.json           # 配置文件
├── env.example          # 环境变量模板
├── main.py              # 应用入口
├── requirements.txt     # 依赖包列表
└── README.md           # 项目说明
```

## 🔧 配置说明

### 主要配置文件
- **config.json**：系统配置参数
- **.env**：环境变量（敏感信息）

### 核心配置项
```json
{
  "system": {
    "max_file_size": 52428800,    // 最大文件大小（50MB）
    "timeout": 10,                // 请求超时时间（秒）
    "max_concurrent": 2           // 最大并发数
  },
  "dashscope": {
    "api_key": "${DASHSCOPE_API_KEY}",  // API密钥
    "base_url": "https://dashscope.aliyuncs.com/api/v1"
  },
  "storage": {
    "base_path": "./photos_storage",     // 存储根目录
    "thumbnail_size": 300               // 缩略图尺寸
  }
}
```

## 🧪 测试

### 运行单元测试
```bash
pytest tests/unit/
```

### 运行集成测试
```bash
pytest tests/integration/
```

### 运行所有测试
```bash
pytest
```

## 📚 开发文档

详细的设计文档位于 `doc/` 目录：

- **开发计划.md**：项目开发计划和里程碑
- **家庭单机版简要设计文档.md**：系统整体设计
- **家庭单机版详细设计文档.md**：详细技术设计
- **数据库设计文档.md**：数据库结构设计
- **API接口详细文档.md**：API接口规范

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送分支：`git push origin feature/AmazingFeature`
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 问题反馈

如果遇到问题，请：

1. 查看[故障排查手册](doc/故障排查手册.md)
2. 在 Issues 中提交问题
3. 提供详细的错误信息和系统环境

## 🙏 致谢

- [DashScope](https://dashscope.aliyun.com/) - 提供AI分析服务
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [SQLAlchemy](https://sqlalchemy.org/) - ORM框架
- [OpenCV](https://opencv.org/) - 图像处理库

---

**版本**：v1.0.0
**最后更新**：2025年9月9日
