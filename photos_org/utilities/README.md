# 工具脚本目录

## 目录说明

这个目录包含了项目开发和维护过程中使用的各种工具脚本，主要用于：

- 数据库分析和优化
- 系统诊断和调试
- 数据迁移和清理
- 开发辅助工具

## 脚本列表

### 数据库相关
- `analyze_database.py` - 分析数据库结构和数据
- `analyze_database_schema.py` - 分析数据库模式
- `check_db_structure.py` - 检查数据库结构
- `check_fts_tables.py` - 检查全文搜索表
- `optimize_database.py` - 数据库优化工具
- `clear_database.py` - 清空数据库数据

### 系统诊断
- `check_analysis_results.py` - 检查分析结果
- `check_api_endpoints.py` - 检查API端点
- `diagnose_system.py` - 系统诊断工具
- `debug_search.py` - 搜索功能调试

### 数据处理
- `add_description_field.py` - 添加描述字段
- `run_system_test.py` - 运行系统测试

## 使用方法

### 数据库分析
```bash
# 分析数据库结构
python utilities/analyze_database.py

# 检查数据库完整性
python utilities/check_db_structure.py

# 优化数据库性能
python utilities/optimize_database.py
```

### 系统诊断
```bash
# 系统健康检查
python utilities/diagnose_system.py

# API端点检查
python utilities/check_api_endpoints.py

# 搜索功能调试
python utilities/debug_search.py
```

### 数据维护
```bash
# 清空数据库（危险操作，谨慎使用）
python utilities/clear_database.py

# 添加新的数据字段
python utilities/add_description_field.py
```

## 注意事项

1. **危险操作**：`clear_database.py` 会删除所有数据，使用前请备份
2. **开发环境**：这些脚本主要用于开发和调试环境
3. **数据安全**：运行任何数据库操作脚本前，请确保有数据备份
4. **权限要求**：部分脚本需要数据库写入权限

## 脚本分类

### 🔍 分析工具
- analyze_database.py
- analyze_database_schema.py
- check_analysis_results.py

### 🔧 维护工具
- optimize_database.py
- clear_database.py
- add_description_field.py

### 🐛 调试工具
- debug_search.py
- diagnose_system.py
- check_api_endpoints.py

### 🧪 测试工具
- run_system_test.py

## 贡献指南

如果添加新的工具脚本，请：

1. 添加清晰的文档注释
2. 在此README中添加说明
3. 遵循现有的命名规范
4. 添加错误处理和日志记录
