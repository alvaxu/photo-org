# 家庭单机版智能照片整理系统 - API接口详细文档

## 一、文档基础信息

| 项目名称 | 家庭单机版智能照片整理系统 | 文档类型 | API接口详细文档 |
| -------- | ------------------------- | -------- | -------------- |
| 文档版本 | V1.0 | 文档状态 | ☑ 草稿 □ 评审中 □ 已确认 □ 已归档 |
| 编写人 | AI助手 | 编写日期 | 2025年9月9日 |
| 关联文档 | 《通用技术规范详细设计文档》《数据库设计文档》 | | |

## 二、API概览

### 2.1 API设计原则

- **RESTful设计**：遵循RESTful API设计规范
- **统一格式**：请求和响应使用统一的数据格式
- **版本控制**：通过URL路径进行API版本控制
- **状态码规范**：使用标准HTTP状态码
- **错误处理**：统一的错误响应格式
- **文档完整**：每个接口都有详细的文档说明

### 2.2 基础信息

- **基础URL**：`http://localhost:8000/api/v1`
- **认证方式**：无需认证（单用户家庭使用）
- **数据格式**：JSON
- **字符编码**：UTF-8
- **时间格式**：ISO 8601 (YYYY-MM-DDTHH:mm:ssZ)

### 2.3 响应格式

#### 2.3.1 成功响应
```json
{
  "success": true,
  "data": {
    // 响应数据
  },
  "meta": {
    "timestamp": "2025-01-01T00:00:00Z",
    "request_id": "uuid-string"
  }
}
```

#### 2.3.2 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {
      // 详细错误信息
    }
  },
  "meta": {
    "timestamp": "2025-01-01T00:00:00Z",
    "request_id": "uuid-string"
  }
}
```

#### 2.3.3 分页响应
```json
{
  "success": true,
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  },
  "meta": {
    "timestamp": "2025-01-01T00:00:00Z",
    "request_id": "uuid-string"
  }
}
```

## 三、照片管理API

### 3.1 照片查询接口

#### 3.1.1 获取照片列表
**接口路径**：`GET /api/v1/photos`
**功能描述**：获取照片列表，支持分页、筛选和排序

**请求参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| skip | integer | 否 | 跳过的记录数，默认0 |
| limit | integer | 否 | 返回的记录数，默认50，最大100 |
| search | string | 否 | 搜索关键词 |
| sort_by | string | 否 | 排序字段，默认created_at |
| sort_order | string | 否 | 排序顺序，默认desc (asc/desc) |
| filters | string | 否 | 筛选条件JSON字符串 |

**响应示例**：
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
}
```

#### 3.1.2 获取照片详情
**接口路径**：`GET /api/v1/photos/{photo_id}`
**功能描述**：获取指定照片的详细信息

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**响应示例**：
```json
{
  "success": true,
  "data": {
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
}
```

### 3.2 照片导入接口

#### 3.2.1 扫描文件夹导入照片
**接口路径**：`POST /api/v1/import/scan-folder`
**功能描述**：扫描指定文件夹，导入其中的照片文件

**请求参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| folder_path | string | 是 | 要扫描的文件夹路径 |

**请求示例**：
```bash
curl -X POST "http://localhost:8000/api/v1/import/scan-folder?folder_path=1.prepare/photo"
```

**响应示例**：
```json
{
  "success": true,
  "message": "成功导入7张照片",
  "data": {
    "scanned_files": 7,
    "imported_photos": 7
  }
}
```

#### 3.2.2 上传单张照片
**接口路径**：`POST /api/v1/import/upload`
**功能描述**：上传单张照片文件

**请求参数**：
- Content-Type: multipart/form-data
- 文件字段名：`file`

**请求示例**：
```bash
curl -X POST "http://localhost:8000/api/v1/import/upload" \
  -F "file=@photo.jpg"
```

**响应示例**：
```json
{
  "success": true,
  "message": "照片上传成功",
  "data": {
    "photo_id": 1,
    "filename": "photo.jpg",
    "file_path": "/storage/photos/photo.jpg"
  }
}
```

### 3.3 照片操作接口

#### 3.3.1 更新照片信息
**接口路径**：`POST /api/v1/photos/upload`
**功能描述**：上传单张或多张照片

**请求参数**：
- Content-Type: multipart/form-data
- files: 照片文件（支持多个）

**响应示例**：
```json
{
  "success": true,
  "data": {
    "uploaded": [
      {
        "id": 1,
        "filename": "IMG_001.jpg",
        "status": "processing"
      }
    ],
    "failed": []
  }
}
```

#### 3.2.2 删除照片
**接口路径**：`DELETE /api/v1/photos/{photo_id}`
**功能描述**：删除指定照片

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "deleted": true,
    "photo_id": 1
  }
}
```

#### 3.2.3 批量删除照片
**接口路径**：`POST /api/v1/photos/batch-delete`
**功能描述**：批量删除照片

**请求体**：
```json
{
  "photo_ids": [1, 2, 3]
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "deleted_count": 3,
    "failed_ids": []
  }
}
```

## 四、智能分析API

### 4.1 分析控制接口

#### 4.1.1 触发照片分析
**接口路径**：`POST /api/v1/analysis/analyze`
**功能描述**：触发指定照片的智能分析

**请求体**：
```json
{
  "photo_ids": [1, 2, 3],
  "analysis_types": ["content", "quality", "duplicate"]
}
```

**参数说明**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| photo_ids | array | 是 | 要分析的照片ID列表 |
| analysis_types | array | 否 | 分析类型，默认["content", "quality", "duplicate"] |

**响应示例**：
```json
{
  "photo_id": 1,
  "status": "processing",
  "message": "分析任务已提交",
  "estimated_time": 30
}
```

#### 4.1.2 获取分析状态
**接口路径**：`GET /api/v1/analysis/status/{photo_id}`
**功能描述**：获取照片分析状态

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**响应示例**：
```json
{
  "photo_id": 1,
  "status": "completed",
  "message": "分析完成",
  "progress": 100
}
```

#### 4.1.3 获取分析结果
**接口路径**：`GET /api/v1/analysis/results/{photo_id}`
**功能描述**：获取照片分析结果

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**响应示例**：
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

#### 4.1.4 批量分析照片
**接口路径**：`POST /api/v1/analysis/batch-analyze`
**功能描述**：批量分析多张照片

**请求体**：
```json
{
  "photo_ids": [1, 2, 3],
  "analysis_type": "full"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "task_id": "batch_analyze_123",
    "total_photos": 3,
    "processing_status": "started",
    "estimated_time": 9
  }
}
```

### 4.2 重复检测接口

#### 4.2.1 检测重复照片
**接口路径**：`POST /api/v1/photos/duplicates`
**功能描述**：检测重复照片

**请求参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| photo_id | integer | 否 | 指定照片ID，不传则检测所有 |
| threshold | float | 否 | 相似度阈值，默认0.8 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "duplicate_groups": [
      {
        "group_id": 1,
        "representative_photo": 1,
        "photos": [1, 5, 12],
        "similarity": 0.95
      }
    ],
    "total_groups": 1
  }
}
```

## 五、分类标签API

### 5.1 分类管理接口

#### 5.1.1 获取分类列表
**接口路径**：`GET /api/v1/categories`
**功能描述**：获取所有分类及其统计信息

**响应示例**：
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "id": 1,
        "name": "家庭",
        "photo_count": 45,
        "created_at": "2023-12-19T10:00:00Z"
      },
      {
        "id": 2,
        "name": "旅行",
        "photo_count": 23,
        "created_at": "2023-12-19T10:05:00Z"
      }
    ]
  }
}
```

#### 5.1.2 创建分类
**接口路径**：`POST /api/v1/categories`
**功能描述**：创建新分类

**请求体**：
```json
{
  "name": "生日",
  "description": "生日相关的照片"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": 3,
    "name": "生日",
    "description": "生日相关的照片",
    "created_at": "2023-12-19T15:00:00Z"
  }
}
```

#### 5.1.3 为照片添加分类
**接口路径**：`POST /api/v1/photos/{photo_id}/categories`
**功能描述**：为照片添加分类

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**请求体**：
```json
{
  "category_id": 1
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "photo_id": 1,
    "category_id": 1,
    "added": true
  }
}
```

### 5.2 标签管理接口

#### 5.2.1 获取标签列表
**接口路径**：`GET /api/v1/tags`
**功能描述**：获取所有标签及其统计信息

**请求参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| search | string | 否 | 标签搜索关键词 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "tags": [
      {
        "id": 1,
        "name": "生日",
        "photo_count": 12,
        "created_at": "2023-12-19T10:00:00Z"
      },
      {
        "id": 2,
        "name": "蛋糕",
        "photo_count": 8,
        "created_at": "2023-12-19T10:05:00Z"
      }
    ]
  }
}
```

#### 5.2.2 为照片添加标签
**接口路径**：`POST /api/v1/photos/{photo_id}/tags`
**功能描述**：为照片添加标签

**路径参数**：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| photo_id | integer | 照片ID |

**请求体**：
```json
{
  "tag_name": "生日"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "photo_id": 1,
    "tag_id": 1,
    "tag_name": "生日",
    "added": true
  }
}
```

## 六、搜索API

### 6.1 搜索接口

#### 6.1.1 综合搜索
**接口路径**：`GET /api/v1/search/photos`
**功能描述**：综合搜索照片，支持多种搜索条件组合

**请求参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| keyword | string | 否 | 关键词搜索 |
| camera_make | string | 否 | 相机品牌 |
| camera_model | string | 否 | 相机型号 |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |
| quality_min | float | 否 | 最低质量分数 (0-100) |
| quality_level | string | 否 | 质量等级 |
| tags | array | 否 | 标签列表 |
| categories | array | 否 | 分类列表 |
| location_lat | float | 否 | 纬度 |
| location_lng | float | 否 | 经度 |
| location_radius | float | 否 | 搜索半径(公里) |
| sort_by | string | 否 | 排序字段，默认taken_at |
| sort_order | string | 否 | 排序顺序，默认desc |
| limit | integer | 否 | 返回数量，默认50，最大200 |
| offset | integer | 否 | 偏移量，默认0 |

**响应示例**：
```json
{
  "success": true,
  "data": [
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

### 6.2 搜索辅助接口

#### 6.2.1 搜索建议
**接口路径**：`GET /api/v1/search/suggestions`
**功能描述**：获取搜索建议

**请求参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| prefix | string | 是 | 搜索前缀 |
| limit | integer | 否 | 建议数量限制，默认10 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "tags": ["生日", "家庭", "庆祝", "室内"],
    "categories": ["家庭", "庆祝", "聚会"],
    "camera_makes": ["Canon", "Nikon", "Sony"],
    "camera_models": ["EOS 80D", "D750", "A7R"]
  }
}
```

### 6.3 搜索统计
**接口路径**：`GET /api/v1/search/stats`
**功能描述**：获取搜索统计信息

**响应示例**：
```json
{
  "success": true,
  "data": {
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
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 8,
    "applied_filters": {
      "keywords": "生日",
      "date_range": "2023-01-01 to 2023-12-31",
      "quality_range": "70-100",
      "categories": ["家庭"],
      "tags": ["蛋糕", "蜡烛"]
    }
  }
}
```

### 6.2 搜索辅助接口

#### 6.2.1 搜索建议
**接口路径**：`GET /api/v1/search/suggestions`
**功能描述**：获取搜索建议

**请求参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| q | string | 是 | 输入关键词 |
| limit | integer | 否 | 建议数量，默认10 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "suggestions": [
      "生日",
      "生日蛋糕",
      "生日聚会",
      "家庭生日"
    ]
  }
}
```

## 七、存储管理API

### 7.1 存储信息接口

#### 7.1.1 获取存储信息
**接口路径**：`GET /api/v1/storage/info`
**功能描述**：获取存储使用情况

**响应示例**：
```json
{
  "success": true,
  "data": {
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
}
```

#### 7.1.2 清理存储空间
**接口路径**：`POST /api/v1/storage/cleanup`
**功能描述**：清理临时文件和缓存

**请求参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| cleanup_type | string | 否 | 清理类型 (temp/cache/all)，默认temp |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "cleanup_type": "temp",
    "cleaned_files": 15,
    "freed_space": 104857600,
    "cleanup_time": 2.5
  }
}
```

### 7.2 备份恢复接口

#### 7.2.1 创建备份
**接口路径**：`POST /api/v1/storage/backup`
**功能描述**：创建数据备份

**请求参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| backup_type | string | 否 | 备份类型 (full/incremental)，默认incremental |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "backup_type": "incremental",
    "backup_path": "backups/incremental_backup_20231219_143000.zip",
    "backup_size": 104857600,
    "backup_time": 45.2
  }
}
```

#### 7.2.2 恢复备份
**接口路径**：`POST /api/v1/storage/restore`
**功能描述**：从备份恢复数据

**请求参数**：
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| backup_file | string | 是 | 备份文件路径 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "backup_file": "backups/full_backup_20231219_140000.zip",
    "restore_time": 120.5,
    "restored_photos": 1250,
    "restored_size": 536870912
  }
}
```

## 八、系统管理API

### 8.1 系统状态接口

#### 8.1.1 获取系统状态
**接口路径**：`GET /api/v1/system/status`
**功能描述**：获取系统运行状态

**响应示例**：
```json
{
  "success": true,
  "data": {
    "version": "1.0.0",
    "uptime": 3600,
    "cpu_usage": 15.5,
    "memory_usage": 256,
    "disk_usage": {
      "total": 100000000000,
      "used": 30000000000,
      "free": 70000000000
    },
    "photo_stats": {
      "total_photos": 1250,
      "analyzed_photos": 1200,
      "total_size": 1073741824
    }
  }
}
```

#### 8.1.2 获取系统配置
**接口路径**：`GET /api/v1/system/config`
**功能描述**：获取系统配置信息

**响应示例**：
```json
{
  "success": true,
  "data": {
    "database": {
      "path": "./data/photos.db"
    },
    "storage": {
      "base_path": "./photos_storage",
      "max_file_size": 52428800
    },
    "analysis": {
      "max_concurrent": 2,
      "timeout": 10
    }
  }
}
```

## 九、错误码定义

### 9.1 通用错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|-----------|------|
| SUCCESS | 200 | 操作成功 |
| BAD_REQUEST | 400 | 请求参数错误 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 禁止访问 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| UNPROCESSABLE_ENTITY | 422 | 数据验证失败 |
| INTERNAL_SERVER_ERROR | 500 | 服务器内部错误 |

### 9.2 业务错误码

| 错误码 | 描述 |
|--------|------|
| PHOTO_NOT_FOUND | 照片不存在 |
| INVALID_FILE_FORMAT | 文件格式不支持 |
| FILE_TOO_LARGE | 文件过大 |
| STORAGE_FULL | 存储空间不足 |
| ANALYSIS_FAILED | 分析失败 |
| DUPLICATE_PHOTO | 重复照片 |
| INVALID_CATEGORY | 无效分类 |
| INVALID_TAG | 无效标签 |

### 9.3 错误响应示例

```json
{
  "success": false,
  "error": {
    "code": "PHOTO_NOT_FOUND",
    "message": "照片不存在",
    "details": {
      "photo_id": 999
    }
  },
  "meta": {
    "timestamp": "2025-01-01T00:00:00Z",
    "request_id": "uuid-string"
  }
}
```

## 十、API调用示例

### 10.1 JavaScript调用示例

#### 10.1.1 获取照片列表
```javascript
// 获取照片列表
async function getPhotos(page = 1, search = '') {
  try {
    const response = await fetch(`/api/v1/photos?page=${page}&q=${search}`);
    const result = await response.json();
    
    if (result.success) {
      console.log('获取成功:', result.data);
      return result.data;
    } else {
      console.error('获取失败:', result.error);
      return null;
    }
  } catch (error) {
    console.error('网络错误:', error);
    return null;
  }
}
```

#### 10.1.2 上传照片
```javascript
// 上传照片
async function uploadPhoto(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch('/api/v1/photos/upload', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('上传失败:', error);
    return null;
  }
}
```

### 10.2 Python调用示例

#### 10.2.1 使用requests库
```python
import requests

# 获取照片列表
def get_photos(page=1, search=''):
    try:
        response = requests.get(f'/api/v1/photos?page={page}&q={search}')
        result = response.json()
        
        if result['success']:
            return result['data']
        else:
            print(f"获取失败: {result['error']}")
            return None
    except Exception as e:
        print(f"网络错误: {e}")
        return None

# 上传照片
def upload_photo(file_path):
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post('/api/v1/photos/upload', files=files)
            return response.json()
    except Exception as e:
        print(f"上传失败: {e}")
        return None
```

## 十一、总结

本API接口详细文档定义了家庭单机版智能照片整理系统的完整API规范，包括：

**核心特性**：
- RESTful API设计，接口清晰易用
- 统一的请求响应格式，便于客户端处理
- 完善的错误处理机制，提升用户体验
- 详细的参数说明和示例，便于开发集成

**主要模块**：
- 照片管理API：照片的增删改查和批量操作
- 智能分析API：照片分析和重复检测
- 分类标签API：分类和标签的管理
- 搜索API：全局搜索和高级搜索
- 存储管理API：存储监控和备份恢复
- 系统管理API：系统状态和配置查询

**使用建议**：
- 客户端应正确处理各种错误响应
- 注意API的调用频率，避免过度请求
- 上传文件时注意文件大小限制
- 搜索接口支持分页，提高性能

通过遵循本API文档，开发团队可以快速集成和使用系统的各项功能，为用户提供稳定高效的服务。
