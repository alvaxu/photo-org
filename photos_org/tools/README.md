# 工具目录

这个目录包含系统维护和管理的实用工具。

## 缩略图清理工具

`cleanup_thumbnails.py` - 清理孤立的缩略图文件

### 功能
- 扫描 `photos_storage/originals` 目录中的所有原始图片文件
- 扫描 `photos_storage/thumbnails` 目录中的所有缩略图文件
- 删除没有对应原始文件的孤立缩略图
- 保持存储数据的一致性

### 使用方法

```bash
# 预览模式（推荐先运行）
python tools/cleanup_thumbnails.py

# 执行实际删除
python tools/cleanup_thumbnails.py --execute
```

### 使用场景
- 系统维护时清理冗余文件
- 修复因异常中断导致的孤立缩略图
- 节省存储空间
- 保持数据一致性

### 安全特性
- 默认预览模式，不会意外删除文件
- 需要明确指定 `--execute` 参数才会执行删除
- 删除前会要求用户确认
- 详细的执行日志和结果报告
