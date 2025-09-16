# 家庭单机版智能照片整理系统 - API接口详细文档

## 一、文档基础信息

| 项目名称 | 家庭单机版智能照片整理系统 | 文档类型 | API接口详细文档 |
| -------- | ------------------------- | -------- | -------------- |
| 文档版本 | V2.0 | 文档状态 | ☑ 草稿 □ 评审中 □ 已确认 □ 已归档 |
| 编写人 | AI助手 | 编写日期 | 2025年1月9日 |
| 关联文档 | 《前端界面设计文档》《搜索检索模块详细设计文档》《照片导入模块详细设计文档》 | | |

## 二、API概览

### 2.1 实现状态总览

| 模块 | 实现状态 | 接口数量 | 说明 |
|------|----------|----------|------|
| 照片管理API | ✅ 完全实现 | 8个 | 照片CRUD、批量操作、统计 |
| 搜索检索API | 🔄 部分实现 | 7个 | 基础搜索和相似照片搜索已实现，智能推荐待开发 |
| 标签分类API | ✅ 完全实现 | 14个 | 标签和分类的完整CRUD操作 |
| 智能分析API | ✅ 完全实现 | 7个 | AI分析、质量评估、重复检测 |
| 存储管理API | ✅ 完全实现 | 8个 | 存储监控、备份恢复、维护 |
| 系统管理API | ✅ 完全实现 | 1个 | 健康检查 |
| 导入管理API | ✅ 完全实现 | 6个 | 文件上传、文件夹扫描 |
| FTS管理API | ✅ 完全实现 | 6个 | FTS表管理、数据同步、搜索测试 |

### 2.2 API设计原则

- **RESTful设计**：遵循RESTful API设计规范
- **实际实现优先**：文档完全基于实际代码实现
- **状态标记清晰**：明确标记每个接口的实现状态
- **开发指导明确**：为后续页面开发提供具体指导
- **错误处理统一**：使用FastAPI标准错误处理

### 2.3 基础信息

- **基础URL**：`http://localhost:8000/api/v1`
- **认证方式**：无需认证（单用户家庭使用）
- **数据格式**：JSON
- **字符编码**：UTF-8
- **时间格式**：ISO 8601 (YYYY-MM-DDTHH:mm:ssZ)
- **框架**：FastAPI + SQLAlchemy

### 2.4 实际响应格式

#### 2.4.1 标准成功响应（实际使用）
```json
{
  "photos": [...],
  "total": 7,
  "skip": 0,
  "limit": 50,
  "has_more": false
}
```

#### 2.4.2 错误响应（FastAPI标准）
```json
{
  "detail": "错误描述信息"
}
```

#### 2.4.3 分页响应（实际实现）
```json
{
  "items": [...],
      "total": 100,
  "skip": 0,
  "limit": 20,
  "has_more": true
}
```

### 2.5 开发指导

#### 2.5.1 后续页面开发优先级
1. **高级搜索页面**：基于现有搜索API扩展
2. **设置管理页面**：基于系统配置API
3. **相册管理页面**：基于分类管理API

#### 2.5.2 接口使用建议
- **照片管理**：使用 `/api/v1/photos` 系列接口
- **搜索功能**：使用 `/api/v1/search` 系列接口
- **标签分类**：使用 `/api/v1/tags` 和 `/api/v1/categories` 接口
- **批量操作**：优先使用批量接口提高效率

## 三、照片管理API ✅ 完全实现

### 3.1 照片查询接口

#### 3.1.1 获取照片列表 ✅ 已实现
**接口路径**：`GET /api/v1/photos`
**功能描述**：获取照片列表，支持分页、筛选和排序

**实际请求参数**：
| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| skip | integer | 否 | 0 | 跳过的记录数 |
| limit | integer | 否 | 50 | 返回的记录数，最大1000 |
| search | string | 否 | null | 搜索关键词 |
| sort_by | string | 否 | "created_at" | 排序字段 |
| sort_order | string | 否 | "desc" | 排序顺序 (asc/desc) |
| filters | string | 否 | null | 筛选条件JSON字符串 |

**实际响应格式**：
```json
{
  "photos": [
    {
      "id": 1,
      "filename": "IMG_001.jpg",
      "file_path": "/storage/photos/photo1.jpg",
      "thumbnail_path": "/storage/thumbnails/photo1.jpg",
      "file_size": 2621440,
      "width": 4032,
      "height": 3024,
      "format": "JPG",
      "status": "completed",
      "description": "照片描述",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "tags": ["生日", "蛋糕"],
      "categories": ["家庭", "聚会"],
      "analysis": {
        "description": "一位年轻女性坐在室内，面前是一个装饰有绿色水果和点燃蜡烛的生日蛋糕",
        "scene_type": "室内",
        "objects": ["生日蛋糕", "蜡烛", "眼镜"],
        "people_count": 1,
        "emotion": "欢乐",
        "tags": ["生日", "庆祝", "室内", "蛋糕", "许愿"],
        "confidence": 0.95,
        "type": "content"
      },
      "quality": {
        "quality_score": 73.48,
        "quality_level": "良好",
        "sharpness_score": 34.03,
        "brightness_score": 100.0,
        "contrast_score": 92.46,
        "color_score": 91.36,
        "composition_score": 73.85,
        "technical_issues": {
          "issues": [],
          "count": 0,
          "has_issues": false
        },
        "assessed_at": "2025-09-10T08:35:54"
      }
    }
  ],
  "total": 7,
  "skip": 0,
  "limit": 50,
  "has_more": false
}
```

#### 3.1.2 获取照片详情 ✅ 已实现
**接口路径**：`GET /api/v1/photos/{photo_id}`
**功能描述**：获取指定照片的详细信息

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**实际响应格式**：
```json
{
    "id": 1,
    "filename": "IMG_001.jpg",
    "original_path": "originals/2023/12/19/20231219_143025_IMG_001.jpg",
    "thumbnail_path": "thumbnails/2023/12/19/1_IMG_001_thumb.jpg",
    "taken_at": "2023-12-19T14:30:25Z",
    "file_size": 2621440,
    "width": 4032,
    "height": 3024,
    "format": "JPEG",
    "camera_make": "Apple",
    "camera_model": "iPhone 13 Pro",
    "quality_score": 85,
    "scene_type": "室内聚会",
    "description": "家庭成员在客厅庆祝生日",
    "categories": ["家庭", "生日"],
    "tags": ["生日", "蛋糕", "蜡烛"],
    "created_at": "2023-12-19T14:35:00Z",
    "updated_at": "2023-12-19T14:40:00Z"
  }
```

### 3.2 照片操作接口

#### 3.2.1 更新照片信息 ✅ 已实现
**接口路径**：`PUT /api/v1/photos/{photo_id}`
**功能描述**：更新照片的描述、标签、分类等信息

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**请求体**：
```json
{
  "description": "新的照片描述",
  "tags": ["新标签1", "新标签2"],
  "categories": [1, 2]
}
```

**实际响应格式**：
```json
{
  "id": 1,
  "filename": "IMG_001.jpg",
  "description": "新的照片描述",
  "tags": ["新标签1", "新标签2"],
  "categories": ["家庭", "生日"],
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### 3.2.2 删除照片 ✅ 已实现
**接口路径**：`DELETE /api/v1/photos/{photo_id}`
**功能描述**：删除指定照片

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**查询参数**：
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| delete_file | boolean | true | 是否删除物理文件 |

**实际响应格式**：
```json
{
  "message": "照片删除成功",
  "photo_id": 1
}
```

#### 3.2.3 批量删除照片 ✅ 已实现
**接口路径**：`POST /api/v1/photos/batch-delete`
**功能描述**：批量删除照片

**请求体**：
```json
{
  "photo_ids": [1, 2, 3],
  "delete_files": true
}
```

**实际响应格式**：
```json
{
  "total_requested": 3,
  "successful_deletions": 3,
  "failed_deletions": []
}
```

### 3.3 照片统计接口

#### 3.3.1 获取照片统计信息 ✅ 已实现
**接口路径**：`GET /api/v1/photos/statistics`
**功能描述**：获取照片统计信息

**实际响应格式**：
```json
{
  "total_photos": 150,
  "total_size": 1073741824,
  "total_size_mb": 1024.0,
  "status_distribution": {
    "completed": 120,
    "processing": 20,
    "failed": 10
  },
  "format_distribution": {
    "JPG": 100,
    "PNG": 30,
    "HEIC": 20
  },
  "yearly_distribution": {
    "2023": 100,
    "2024": 50
  },
  "quality_distribution": {
    "优秀": 25,
    "良好": 85,
    "一般": 35,
    "较差": 5
  },
  "last_updated": "2025-01-01T00:00:00Z"
}
```

#### 3.3.2 按分类获取照片 ✅ 已实现
**接口路径**：`GET /api/v1/photos/by-category/{category_id}`
**功能描述**：获取指定分类的照片

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| category_id | integer | 分类ID |

**查询参数**：
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| skip | integer | 0 | 跳过的记录数 |
| limit | integer | 50 | 返回的记录数 |

#### 3.3.3 按标签获取照片 ✅ 已实现
**接口路径**：`GET /api/v1/photos/by-tag/{tag_name}`
**功能描述**：获取指定标签的照片

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| tag_name | string | 标签名称 |

**查询参数**：
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| skip | integer | 0 | 跳过的记录数 |
| limit | integer | 50 | 返回的记录数 |

### 3.4 智能处理接口

#### 3.4.1 智能处理照片 ✅ 已实现
**接口路径**：`POST /api/v1/photos/batch-process`
**功能描述**：智能处理照片（AI分析、质量评估等）

**请求体**：
```json
{
  "photo_ids": [1, 2, 3],
  "analysis_types": ["content", "quality", "duplicate"]
}
```

**实际响应格式**：
```json
{
  "message": "智能处理任务已启动",
  "task_id": "batch_process_123",
  "total_photos": 50,
  "estimated_time": 300
}
```

## 四、导入管理API ✅ 完全实现

### 4.1 文件导入接口

#### 4.1.1 扫描文件夹导入照片 ✅ 已实现
**接口路径**：`POST /api/v1/import/scan-folder`
**功能描述**：扫描指定文件夹，导入其中的照片文件

**查询参数**：
| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| folder_path | string | 是 | - | 要扫描的文件夹路径 |
| recursive | boolean | 否 | true | 是否递归扫描子文件夹 |

**实际响应格式**：
```json
{
  "message": "成功导入7张照片",
  "scanned_files": 7,
  "imported_photos": 7,
  "duplicate_files": 0,
  "failed_files": 0
}
```

#### 4.1.2 上传照片文件 ✅ 已实现
**接口路径**：`POST /api/v1/import/upload`
**功能描述**：上传单张或多张照片文件

**请求参数**：
- Content-Type: multipart/form-data
- files: 照片文件（支持多个）

**实际响应格式**：
```json
{
  "message": "照片上传成功",
    "uploaded": [
      {
        "id": 1,
        "filename": "IMG_001.jpg",
        "status": "processing"
      }
    ],
  "failed": [],
  "duplicate_detected": []
}
```

#### 4.1.3 处理单个文件 ✅ 已实现
**接口路径**：`POST /api/v1/import/process-single`
**功能描述**：处理单个文件（用于重新处理）

**请求体**：
```json
{
  "file_path": "/path/to/file.jpg"
}
```

#### 4.1.4 获取支持的文件格式 ✅ 已实现
**接口路径**：`GET /api/v1/import/supported-formats`
**功能描述**：获取支持的文件格式列表

**实际响应格式**：
```json
{
  "supported_formats": [
    {
      "extension": ".jpg",
      "mime_type": "image/jpeg",
      "description": "JPEG图片格式"
    },
    {
      "extension": ".png",
      "mime_type": "image/png",
      "description": "PNG图片格式"
    }
  ]
}
```

#### 4.1.5 获取导入状态 ✅ 已实现
**接口路径**：`GET /api/v1/import/import-status`
**功能描述**：获取当前导入状态

#### 4.1.6 获取扫描任务状态 ✅ 已实现
**接口路径**：`GET /api/v1/import/scan-status/{task_id}`
**功能描述**：获取扫描任务状态

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| task_id | string | 任务ID |

## 五、智能分析API ✅ 完全实现

### 5.1 分析控制接口

#### 5.1.1 触发照片分析 ✅ 已实现
**接口路径**：`POST /api/v1/analysis/analyze`
**功能描述**：触发指定照片的智能分析

**请求体**：
```json
{
  "photo_id": 1
}
```

**实际响应格式**：
```json
{
  "photo_id": 1,
  "status": "processing",
  "message": "分析任务已提交",
  "estimated_time": 30
}
```

#### 5.1.2 批量分析照片 ✅ 已实现
**接口路径**：`POST /api/v1/analysis/batch-analyze`
**功能描述**：批量分析多张照片

**请求体**：
```json
{
  "photo_ids": [1, 2, 3],
  "analysis_type": "full"
}
```

**实际响应格式**：
```json
{
  "task_id": "batch_analyze_123",
  "total_photos": 3,
  "processing_status": "started",
  "estimated_time": 9
}
```

#### 5.1.3 获取分析状态 ✅ 已实现
**接口路径**：`GET /api/v1/analysis/status/{photo_id}`
**功能描述**：获取照片分析状态

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**实际响应格式**：
```json
{
  "photo_id": 1,
  "status": "completed",
  "message": "分析完成",
  "progress": 100
}
```

#### 5.1.4 获取分析结果 ✅ 已实现
**接口路径**：`GET /api/v1/analysis/results/{photo_id}`
**功能描述**：获取照片分析结果

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**实际响应格式**：
```json
{
  "photo_id": 1,
  "analysis_type": "content",
  "result": {
    "description": "一位年轻女性坐在室内，面前是一个装饰有绿色水果和点燃蜡烛的生日蛋糕",
    "scene_type": "室内",
    "objects": ["生日蛋糕", "蜡烛", "眼镜"],
    "people_count": 1,
    "emotion": "欢乐",
    "tags": ["生日", "庆祝", "室内", "蛋糕", "许愿"],
    "confidence": 0.95
  },
  "quality": {
    "quality_score": 73.48,
    "quality_level": "良好",
    "sharpness_score": 34.03,
    "brightness_score": 100.0,
    "contrast_score": 92.46,
    "color_score": 91.36,
    "composition_score": 73.85
  }
}
```

### 5.2 重复检测接口

#### 5.2.1 检测重复照片 ✅ 已实现
**接口路径**：`GET /api/v1/analysis/duplicates/{photo_id}`
**功能描述**：检测指定照片的重复项

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**实际响应格式**：
```json
{
  "photo_id": 1,
  "duplicates": [
    {
      "photo_id": 5,
      "similarity": 0.95,
      "filename": "IMG_005.jpg"
    }
  ],
  "total_duplicates": 1
}
```

### 5.3 其他分析接口

#### 5.3.1 生成照片标题 ✅ 已实现
**接口路径**：`POST /api/v1/analysis/caption`
**功能描述**：为照片生成标题

**请求体**：
```json
{
  "photo_id": 1,
  "style": "descriptive"
}
```

#### 5.3.2 获取分析队列状态 ✅ 已实现
**接口路径**：`GET /api/v1/analysis/queue/status`
**功能描述**：获取分析队列状态

**查询参数**：
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| initial_total | integer | null | 初始总数 |

## 六、分类标签API ✅ 完全实现

### 6.1 分类管理接口

#### 6.1.1 获取分类列表 ✅ 已实现
**接口路径**：`GET /api/v1/categories`
**功能描述**：获取所有分类及其统计信息

**查询参数**：
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| skip | integer | 0 | 跳过的记录数 |
| limit | integer | 100 | 返回的记录数 |
| search | string | null | 搜索关键词 |
| parent_id | integer | null | 父分类ID |

**实际响应格式**：
```json
[
      {
        "id": 1,
        "name": "家庭",
    "description": "家庭相关照片",
        "photo_count": 45,
    "parent_id": null,
    "created_at": "2023-12-19T10:00:00Z",
    "updated_at": "2023-12-19T10:00:00Z"
      },
      {
        "id": 2,
        "name": "旅行",
    "description": "旅行相关照片",
        "photo_count": 23,
    "parent_id": null,
    "created_at": "2023-12-19T10:05:00Z",
    "updated_at": "2023-12-19T10:05:00Z"
  }
]
```

#### 6.1.2 获取分类树结构 ✅ 已实现
**接口路径**：`GET /api/v1/categories/tree`
**功能描述**：获取分类树结构

**实际响应格式**：
```json
[
  {
    "id": 1,
    "name": "家庭",
    "children": [
      {
    "id": 3,
    "name": "生日",
        "children": []
      }
    ]
  }
]
```

#### 6.1.3 获取分类统计信息 ✅ 已实现
**接口路径**：`GET /api/v1/categories/stats`
**功能描述**：获取分类统计信息

#### 6.1.4 获取热门分类 ✅ 已实现
**接口路径**：`GET /api/v1/categories/popular`
**功能描述**：获取热门分类

**查询参数**：
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| limit | integer | 20 | 返回的分类数量 |

#### 6.1.5 获取分类详情 ✅ 已实现
**接口路径**：`GET /api/v1/categories/{category_id}`
**功能描述**：获取分类详情

#### 6.1.6 创建分类 ✅ 已实现
**接口路径**：`POST /api/v1/categories`
**功能描述**：创建新分类

**请求体**：
```json
{
  "name": "生日",
  "description": "生日相关的照片",
  "parent_id": 1
}
```

#### 6.1.7 更新分类 ✅ 已实现
**接口路径**：`PUT /api/v1/categories/{category_id}`
**功能描述**：更新分类信息

#### 6.1.8 删除分类 ✅ 已实现
**接口路径**：`DELETE /api/v1/categories/{category_id}`
**功能描述**：删除分类

### 6.2 标签管理接口

#### 6.2.1 获取标签统计信息 ✅ 已实现
**接口路径**：`GET /api/v1/tags/stats`
**功能描述**：获取标签统计信息

#### 6.2.2 获取标签列表 ✅ 已实现
**接口路径**：`GET /api/v1/tags`
**功能描述**：获取所有标签及其统计信息

**查询参数**：
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| skip | integer | 0 | 跳过的记录数 |
| limit | integer | 100 | 返回的记录数 |
| search | string | null | 搜索关键词 |

**实际响应格式**：
```json
[
      {
        "id": 1,
        "name": "生日",
    "description": "生日相关标签",
        "photo_count": 12,
    "created_at": "2023-12-19T10:00:00Z",
    "updated_at": "2023-12-19T10:00:00Z"
      },
      {
        "id": 2,
        "name": "蛋糕",
    "description": "蛋糕相关标签",
        "photo_count": 8,
    "created_at": "2023-12-19T10:05:00Z",
    "updated_at": "2023-12-19T10:05:00Z"
  }
]
```

#### 6.2.3 获取热门标签 ✅ 已实现
**接口路径**：`GET /api/v1/tags/popular`
**功能描述**：获取热门标签

**查询参数**：
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| limit | integer | 20 | 返回的标签数量 |

#### 6.2.4 获取标签详情 ✅ 已实现
**接口路径**：`GET /api/v1/tags/{tag_id}`
**功能描述**：获取标签详情

#### 6.2.5 创建标签 ✅ 已实现
**接口路径**：`POST /api/v1/tags`
**功能描述**：创建新标签

**请求体**：
```json
{
  "name": "生日",
  "description": "生日相关标签"
}
```

#### 6.2.6 更新标签 ✅ 已实现
**接口路径**：`PUT /api/v1/tags/{tag_id}`
**功能描述**：更新标签信息

#### 6.2.7 删除标签 ✅ 已实现
**接口路径**：`DELETE /api/v1/tags/{tag_id}`
**功能描述**：删除标签

## 七、搜索检索API 🔄 部分实现

### 7.1 已实现搜索接口

#### 7.1.1 综合搜索照片 ✅ 已实现
**接口路径**：`GET /api/v1/search/photos`
**功能描述**：综合搜索照片，支持多种搜索条件组合

**实际请求参数**：
| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| keyword | string | 否 | null | 关键词搜索 |
| search_type | string | 否 | "all" | 搜索类型 |
| camera_make | string | 否 | null | 相机品牌 |
| camera_model | string | 否 | null | 相机型号 |
| date_from | date | 否 | null | 开始日期 |
| date_to | date | 否 | null | 结束日期 |
| start_date | date | 否 | null | 自定义开始日期 |
| end_date | date | 否 | null | 自定义结束日期 |
| date_filter | string | 否 | null | 日期筛选类型 |
| quality_min | float | 否 | null | 最低质量分数 (0-100) |
| quality_level | string | 否 | null | 质量等级 |
| quality_filter | string | 否 | null | 质量筛选 |
| tags | array | 否 | null | 标签列表 |
| categories | array | 否 | null | 分类列表 |
| location_lat | float | 否 | null | 纬度 |
| location_lng | float | 否 | null | 经度 |
| location_radius | float | 否 | null | 搜索半径(公里) |
| sort_by | string | 否 | "taken_at" | 排序字段 |
| sort_order | string | 否 | "desc" | 排序顺序 |
| limit | integer | 否 | 50 | 返回数量，最大200 |
| offset | integer | 否 | 0 | 偏移量 |

**实际响应格式**：
```json
{
  "photos": [
    {
      "id": 2,
      "filename": "184dae88f85397feddac19c9f628ea93.JPG",
      "file_path": "/storage/photos/photo2.jpg",
      "thumbnail_path": "/storage/thumbnails/photo2.jpg",
      "file_size": 2488864,
      "width": 4032,
      "height": 3024,
      "format": "JPG",
      "status": "completed",
      "description": "室内场景中，一位老年女性和一位中年男性坐在桌子前，面前摆放着一个生日蛋糕",
      "created_at": "2025-09-10T08:35:52Z",
      "tags": ["生日", "家庭", "庆祝", "室内", "老人"],
      "categories": ["家庭", "庆祝"],
      "analysis": {
        "description": "室内场景中，一位老年女性和一位中年男性坐在桌子前，面前摆放着一个生日蛋糕",
        "scene_type": "室内",
        "objects": ["生日蛋糕", "蜡烛", "书法作品", "餐桌"],
        "people_count": 2,
        "emotion": "欢乐",
        "tags": ["生日", "家庭", "庆祝", "室内", "老人", "中年男性", "蛋糕"],
        "confidence": 0.95,
        "type": "content"
      },
      "quality": {
        "quality_score": 78.2,
        "quality_level": "良好",
        "sharpness_score": 45.8,
        "brightness_score": 95.2,
        "contrast_score": 88.9,
        "color_score": 87.6,
        "composition_score": 79.3,
        "technical_issues": {
          "issues": [],
          "count": 0,
          "has_issues": false
        },
        "assessed_at": "2025-09-10T08:35:54"
      }
    }
  ],
  "total": 5,
  "limit": 50,
  "offset": 0
}
```

#### 7.1.2 获取搜索建议 ✅ 已实现
**接口路径**：`GET /api/v1/search/suggestions`
**功能描述**：获取搜索建议

**实际请求参数**：
| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| prefix | string | 是 | - | 搜索前缀 |
| search_type | string | 否 | "all" | 搜索类型 |
| limit | integer | 否 | 10 | 建议数量限制 |

**实际响应格式**：
```json
{
    "tags": ["生日", "家庭", "庆祝", "室内"],
    "categories": ["家庭", "庆祝", "聚会"],
    "camera_makes": ["Canon", "Nikon", "Sony"],
    "camera_models": ["EOS 80D", "D750", "A7R"]
}
```

#### 7.1.3 获取搜索统计信息 ✅ 已实现
**接口路径**：`GET /api/v1/search/stats`
**功能描述**：获取搜索统计信息

**实际响应格式**：
```json
{
    "total_photos": 150,
    "total_tags": 45,
    "total_categories": 12,
    "photos_by_quality": {
      "优秀": 25,
      "良好": 85,
      "一般": 35,
      "较差": 5
    },
    "photos_by_date": {
      "2023": 120,
      "2024": 25,
      "2025": 5
  }
}
```

#### 7.1.4 获取照片详情（搜索模块） ✅ 已实现
**接口路径**：`GET /api/v1/search/photos/{photo_id}`
**功能描述**：获取照片详情（与照片管理API重复）

### 7.2 部分实现搜索接口（高级搜索页面）

#### 7.2.1 相似照片搜索 ✅ 已实现
**接口路径**：`GET /api/v1/search/similar/{photo_id}`
**功能描述**：搜索相似照片

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 参考照片ID |

**查询参数**：
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| threshold | float | 0.8 | 相似度阈值 |
| limit | integer | 10 | 结果数量限制 |

**实际响应格式**：
```json
{
  "reference_photo": {
    "id": 1,
    "filename": "IMG_001.jpg"
  },
  "similar_photos": [
    {
      "id": 5,
      "filename": "IMG_005.jpg",
      "similarity": 0.95,
      "thumbnail_path": "/thumbnails/photo5.jpg"
    }
  ],
  "total_found": 3
}
```

#### 7.2.2 智能推荐照片 ❌ 待开发
**接口路径**：`GET /api/v1/search/recommend/{photo_id}`
**功能描述**：基于内容相似度的照片推荐

#### 7.2.3 搜索历史管理 ❌ 待开发
**接口路径**：`GET /api/v1/search/history`
**功能描述**：获取搜索历史

**接口路径**：`POST /api/v1/search/history`
**功能描述**：保存搜索记录

#### 7.2.4 保存搜索条件 ❌ 待开发
**接口路径**：`POST /api/v1/search/save`
**功能描述**：保存搜索条件

**接口路径**：`GET /api/v1/search/saved`
**功能描述**：获取保存的搜索条件

### 7.3 搜索结果处理功能（基于现有接口）

#### 7.3.1 批量操作功能 ✅ 基于现有接口
**利用现有接口**：
- `POST /api/v1/photos/batch-delete` - 批量删除
- `PUT /api/v1/photos/{photo_id}` - 更新照片信息

#### 7.3.2 相似照片处理功能 ❌ 待开发
**计划接口**：
- `POST /api/v1/search/similar/process` - 处理相似照片
- 基于现有的 `DuplicateDetectionService` 实现

## 八、存储管理API ✅ 完全实现

### 8.1 存储信息接口

#### 8.1.1 获取存储信息 ✅ 已实现
**接口路径**：`GET /api/v1/storage/info`
**功能描述**：获取存储使用情况

**实际响应格式**：
```json
{
    "total_size": 1073741824,
    "used_size": 536870912,
    "free_size": 536870912,
    "originals_size": 402653184,
    "thumbnails_size": 134217728,
    "temp_size": 1048576,
    "backups_size": 67108864,
    "photo_count": 1250,
    "disk_info": {
      "total": 100000000000,
      "free": 30000000000
  }
}
```

#### 8.1.2 获取存储目录结构 ✅ 已实现
**接口路径**：`GET /api/v1/storage/structure`
**功能描述**：获取存储目录结构

#### 8.1.3 获取存储维护信息 ✅ 已实现
**接口路径**：`GET /api/v1/storage/maintenance`
**功能描述**：获取存储维护信息

### 8.2 备份恢复接口

#### 8.2.1 创建备份 ✅ 已实现
**接口路径**：`POST /api/v1/storage/backup`
**功能描述**：创建数据备份

**请求体**：
```json
{
  "backup_type": "incremental",
  "description": "定期备份"
}
```

**实际响应格式**：
```json
{
    "backup_type": "incremental",
    "backup_path": "backups/incremental_backup_20231219_143000.zip",
    "backup_size": 104857600,
    "backup_time": 45.2
}
```

#### 8.2.2 获取备份列表 ✅ 已实现
**接口路径**：`GET /api/v1/storage/backups`
**功能描述**：获取备份文件列表

#### 8.2.3 恢复备份 ✅ 已实现
**接口路径**：`POST /api/v1/storage/restore`
**功能描述**：从备份恢复数据

**请求体**：
```json
{
  "backup_file": "backups/full_backup_20231219_140000.zip"
}
```

### 8.3 存储维护接口

#### 8.3.1 清理临时文件 ✅ 已实现
**接口路径**：`POST /api/v1/storage/cleanup`
**功能描述**：清理临时文件和缓存

**请求体**：
```json
{
  "cleanup_type": "temp",
  "force": false
}
```

#### 8.3.2 检查文件完整性 ✅ 已实现
**接口路径**：`GET /api/v1/storage/integrity/{file_path:path}`
**功能描述**：检查文件完整性

**查询参数**：
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| expected_hash | string | null | 期望的哈希值 |

## 九、系统管理API ✅ 完全实现

### 9.1 健康检查接口

#### 9.1.1 健康检查 ✅ 已实现
**接口路径**：`GET /api/v1/health`
**功能描述**：系统健康检查

**实际响应格式**：
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00Z",
    "version": "1.0.0",
  "uptime": 3600
}
```

## 十、FTS全文搜索管理API ✅ 完全实现

### 10.1 FTS表管理接口

#### 10.1.1 检查FTS表状态 ✅ 已实现
**接口路径**：`GET /api/v1/fts/status`
**功能描述**：检查FTS表是否存在

**实际响应格式**：
```json
{
  "exists": true,
  "message": "FTS表已存在"
}
```

#### 10.1.2 创建FTS表 ✅ 已实现
**接口路径**：`POST /api/v1/fts/create`
**功能描述**：创建FTS全文搜索表

**实际响应格式**：
```json
{
  "success": true,
  "message": "FTS表创建成功"
}
```

#### 10.1.3 重建FTS表 ✅ 已实现
**接口路径**：`POST /api/v1/fts/rebuild`
**功能描述**：重建FTS表（删除后重新创建）

**实际响应格式**：
```json
{
  "success": true,
  "message": "FTS表重建成功"
}
```

#### 10.1.4 填充FTS表数据 ✅ 已实现
**接口路径**：`POST /api/v1/fts/populate`
**功能描述**：填充FTS表数据（将现有照片数据同步到FTS表）

**实际响应格式**：
```json
{
  "success": true,
  "message": "FTS表数据填充完成",
  "rows_affected": 150
}
```

#### 10.1.5 更新AI分析内容 ✅ 已实现
**接口路径**：`POST /api/v1/fts/update-analysis`
**功能描述**：更新FTS表中的AI分析内容

**实际响应格式**：
```json
{
  "success": true,
  "message": "AI分析内容更新完成",
  "rows_affected": 45
}
```

#### 10.1.6 FTS搜索测试 ✅ 已实现
**接口路径**：`GET /api/v1/fts/search`
**功能描述**：测试FTS搜索功能

**查询参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| keyword | string | 是 | 搜索关键词 |

**实际响应格式**：
```json
{
  "keyword": "生日",
  "results": [1, 2, 3, 5],
  "total_found": 4,
  "search_time_ms": 15
}
```

## 十一、错误码定义

### 11.1 FastAPI标准错误码

| HTTP状态码 | 描述 | 使用场景 |
|-----------|------|----------|
| 200 | 操作成功 | 正常响应 |
| 400 | 请求参数错误 | 参数验证失败 |
| 404 | 资源不存在 | 照片、标签、分类不存在 |
| 422 | 数据验证失败 | 请求体格式错误 |
| 500 | 服务器内部错误 | 系统异常 |

### 11.2 实际错误响应格式

```json
{
  "detail": "照片不存在"
}
```

## 十二、后续页面开发指导

### 12.1 高级搜索页面开发

#### 12.1.1 可用的现有接口
- `GET /api/v1/search/photos` - 综合搜索（已实现）
- `GET /api/v1/search/suggestions` - 搜索建议（已实现）
- `GET /api/v1/search/stats` - 搜索统计（已实现）
- `GET /api/v1/search/similar/{photo_id}` - 相似照片搜索（已实现）

#### 12.1.2 需要开发的新接口
- `GET /api/v1/search/recommend/{photo_id}` - 智能推荐
- `GET /api/v1/search/history` - 搜索历史
- `POST /api/v1/search/save` - 保存搜索条件

#### 12.1.3 开发建议
1. **相似照片搜索已实现**：可直接使用 `GET /api/v1/search/similar/{photo_id}` 接口
2. **利用现有批量操作接口**：`POST /api/v1/photos/batch-delete`、`PUT /api/v1/photos/{photo_id}`
3. **前端界面参考**：`doc/搜索检索模块详细设计文档.md` 第8.2节

### 12.2 设置管理页面开发

#### 12.2.1 可用的现有接口
- `GET /api/v1/storage/info` - 存储信息（已实现）
- `GET /api/v1/health` - 系统状态（已实现）
- `POST /api/v1/storage/cleanup` - 清理存储（已实现）

#### 12.2.2 需要开发的新接口
- `GET /api/v1/system/config` - 获取系统配置
- `PUT /api/v1/system/config` - 更新系统配置
- `GET /api/v1/system/logs` - 获取系统日志

#### 12.2.3 开发建议
1. **基于现有配置系统**：`app/core/config.py` 已实现
2. **前端界面参考**：`doc/前端界面设计文档.md` 第2.2节（未实现部分）

### 12.3 相册管理页面开发

#### 12.3.1 可用的现有接口
- `GET /api/v1/categories` - 分类列表（已实现）
- `POST /api/v1/categories` - 创建分类（已实现）
- `PUT /api/v1/categories/{category_id}` - 更新分类（已实现）
- `DELETE /api/v1/categories/{category_id}` - 删除分类（已实现）
- `GET /api/v1/categories/tree` - 分类树（已实现）

#### 12.3.2 需要开发的新接口
- `POST /api/v1/albums` - 创建相册
- `GET /api/v1/albums` - 相册列表
- `PUT /api/v1/albums/{album_id}` - 更新相册
- `DELETE /api/v1/albums/{album_id}` - 删除相册
- `POST /api/v1/albums/{album_id}/photos` - 添加照片到相册

#### 12.3.3 开发建议
1. **基于现有分类系统**：相册可以基于分类系统扩展
2. **数据库设计**：需要新增相册表和相册-照片关联表
3. **前端界面参考**：`doc/前端界面设计文档.md` 第2.2节（未实现部分）

## 十三、API调用示例

### 13.1 JavaScript调用示例

#### 13.1.1 获取照片列表（实际可用）
```javascript
// 获取照片列表
async function getPhotos(skip = 0, limit = 50, search = '') {
  try {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString()
    });
    if (search) params.append('search', search);
    
    const response = await fetch(`/api/v1/photos?${params}`);
    const result = await response.json();
    
    if (response.ok) {
      console.log('获取成功:', result);
      return result;
    } else {
      console.error('获取失败:', result.detail);
      return null;
    }
  } catch (error) {
    console.error('网络错误:', error);
    return null;
  }
}
```

#### 13.1.2 搜索照片（实际可用）
```javascript
// 搜索照片
async function searchPhotos(keyword, searchType = 'all') {
  try {
    const params = new URLSearchParams({
      keyword: keyword,
      search_type: searchType,
      limit: '50'
    });
    
    const response = await fetch(`/api/v1/search/photos?${params}`);
    const result = await response.json();
    
    if (response.ok) {
    return result;
    } else {
      console.error('搜索失败:', result.detail);
      return null;
    }
  } catch (error) {
    console.error('网络错误:', error);
    return null;
  }
}
```

### 13.2 Python调用示例

#### 13.2.1 使用requests库（实际可用）
```python
import requests

# 获取照片列表
def get_photos(skip=0, limit=50, search=''):
    try:
        params = {
            'skip': skip,
            'limit': limit
        }
        if search:
            params['search'] = search
            
        response = requests.get('/api/v1/photos', params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取失败: {e}")
        return None

# 搜索照片
def search_photos(keyword, search_type='all'):
    try:
        params = {
            'keyword': keyword,
            'search_type': search_type,
            'limit': 50
        }
        
        response = requests.get('/api/v1/search/photos', params=params)
        response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"搜索失败: {e}")
        return None
```

## 十四、总结

本API接口详细文档基于实际代码实现，为家庭单机版智能照片整理系统提供了完整的API规范：

### **✅ 已完全实现的功能**

**照片管理API**：
- 照片CRUD操作、智能处理、统计信息
- 支持分页、搜索、筛选、排序
- 完整的错误处理和参数验证

**搜索检索API**：
- 综合搜索、搜索建议、搜索统计
- 支持多维度搜索条件组合
- 为高级搜索页面提供基础

**标签分类API**：
- 完整的标签和分类CRUD操作
- 支持分类树结构、热门标签/分类
- 为相册管理页面提供基础

**智能分析API**：
- AI内容分析、质量评估、重复检测
- 支持批量分析和异步处理
- 完整的分析结果管理

**存储管理API**：
- 存储监控、备份恢复、维护功能
- 支持增量备份和文件完整性检查
- 为设置管理页面提供基础

**FTS管理API**：
- FTS表创建、重建、数据填充
- AI分析内容同步和更新
- FTS搜索功能测试和验证
- 为全文搜索功能提供管理支持

### **🚀 待开发的功能**

**高级搜索页面**：
- 相似照片搜索（已实现）、智能推荐
- 搜索历史管理、保存搜索条件
- 搜索结果处理功能

**设置管理页面**：
- 系统配置管理
- 日志查看和管理
- 性能监控

**相册管理页面**：
- 相册CRUD操作
- 相册-照片关联管理
- 相册分享功能

### **📈 开发建议**

**优先级1（短期）**：
1. 相似照片搜索功能已实现，可直接使用
2. 开发搜索结果处理功能（利用现有批量操作接口）
3. 完善高级搜索界面

**优先级2（中期）**：
1. 实现设置管理页面（基于现有配置系统）
2. 开发相册管理功能（基于现有分类系统）
3. 添加搜索历史管理功能

**优先级3（长期）**：
1. 实现智能推荐功能
2. 添加相册分享功能
3. 完善系统监控和日志管理

通过遵循本API文档，开发团队可以基于现有实现快速开发后续三个页面，为用户提供更完整、更强大的照片管理服务。
