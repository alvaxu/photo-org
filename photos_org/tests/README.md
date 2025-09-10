# 测试目录结构说明

## 目录结构

```
tests/
├── integration/          # 集成测试
│   ├── test_ai_analysis.py              # AI分析功能测试
│   ├── test_analysis.py                 # 分析功能测试
│   ├── test_classification.py           # 分类功能测试
│   ├── test_complete_system.py          # 完整系统功能测试
│   ├── test_full_image_processing.py    # 完整图像处理流程测试
│   ├── test_package_import.py           # 包导入测试
│   ├── test_photo_analysis.py           # 照片分析测试（从1.prepare目录移入）
│   ├── test_photo_import.py             # 照片导入测试
│   ├── test_search_functionality.py     # 搜索功能测试
│   └── test_search.py                   # 搜索测试
├── unit/                 # 单元测试（待完善）
└── e2e/                  # 端到端测试
    ├── test_frontend.html               # 前端界面测试
    └── test_system.py                   # 系统端到端测试（从abandon目录移入）
```

## 测试类型说明

### 集成测试 (integration/)
测试多个组件之间的交互和协作，主要包括：
- AI分析服务与数据库的集成
- 照片导入与分析的完整流程
- 搜索功能与数据库的交互
- 分类服务与标签系统的协作

### 单元测试 (unit/)
测试单个组件的独立功能，目前为空，待后续完善。

### 端到端测试 (e2e/)
测试完整的用户使用流程，从前端界面到后端服务的全链路测试。

## 运行测试

### 运行所有集成测试
```bash
cd tests/integration
python test_complete_system.py  # 推荐：测试完整系统功能
```

### 运行特定功能测试
```bash
# 测试AI分析功能
python test_ai_analysis.py

# 测试搜索功能
python test_search_functionality.py

# 测试照片导入
python test_photo_import.py
```

## 测试文件命名规范

- `test_*.py` - 所有测试文件都以 `test_` 开头
- 文件名应清晰表达测试的功能模块
- 例如：`test_photo_import.py` 表示照片导入功能的测试

## 测试数据说明

测试文件使用项目中的实际照片数据进行测试：
- 测试照片位于 `1.prepare/photo/` 目录
- 数据库文件为 `data/photos.db`
- 测试会自动创建和清理测试数据

## 注意事项

1. 运行测试前确保系统服务已启动
2. 部分测试会修改数据库，请注意数据备份
3. 集成测试需要完整的系统环境
4. 建议按顺序运行测试：导入 -> 分析 -> 搜索 -> 完整系统
