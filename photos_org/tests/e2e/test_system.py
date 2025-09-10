'''
程序说明：
系统测试脚本

## 1. 测试照片上传和分析功能
## 2. 验证AI服务集成
## 3. 测试重复检测功能
'''

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from database import init_db, get_db
from photo_service import PhotoService
from models import Photo
from sqlalchemy.orm import Session

async def test_photo_analysis():
    """测试照片分析功能"""
    print("开始测试照片分析功能...")
    
    # 初始化数据库
    init_db()
    
    # 获取数据库会话
    db = next(get_db())
    photo_service = PhotoService(db)
    
    try:
        # 创建测试图片（如果不存在）
        test_image_path = "test_image.jpg"
        if not os.path.exists(test_image_path):
            print("创建测试图片...")
            from PIL import Image
            import numpy as np
            
            # 创建一个简单的测试图片
            img_array = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            img.save(test_image_path)
            print(f"测试图片已创建: {test_image_path}")
        
        # 测试照片上传
        print("测试照片上传...")
        photo = photo_service.add_photo(test_image_path, move_file=False)
        if photo:
            print(f"照片上传成功: ID={photo.id}, 文件名={photo.filename}")
            
            # 测试照片分析
            print("测试照片分析...")
            success = await photo_service.analyze_photo(photo.id)
            if success:
                print("照片分析成功")
                
                # 查询分析结果
                updated_photo = db.query(Photo).filter(Photo.id == photo.id).first()
                if updated_photo:
                    print(f"分析结果: {updated_photo.ai_analysis}")
                    print(f"质量评分: {updated_photo.quality_score}")
                    print(f"分类: {updated_photo.category}")
                    print(f"子分类: {updated_photo.subcategory}")
            else:
                print("照片分析失败")
        else:
            print("照片上传失败")
        
        # 测试重复检测
        print("测试重复检测...")
        duplicate_groups = photo_service.detect_duplicates()
        print(f"检测到 {len(duplicate_groups)} 个重复组")
        
        # 测试统计信息
        print("测试统计信息...")
        stats = photo_service.get_statistics()
        print(f"统计信息: {stats}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def test_database_connection():
    """测试数据库连接"""
    print("测试数据库连接...")
    try:
        init_db()
        db = next(get_db())
        
        # 测试查询
        photos = db.query(Photo).all()
        print(f"数据库连接成功，当前有 {len(photos)} 张照片")
        
        db.close()
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

def test_ai_service():
    """测试AI服务"""
    print("测试AI服务...")
    try:
        from ai_service import ai_service
        
        # 创建测试图片
        test_image_path = "test_ai_image.jpg"
        if not os.path.exists(test_image_path):
            from PIL import Image
            import numpy as np
            
            # 创建一个简单的测试图片
            img_array = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            img.save(test_image_path)
        
        # 测试内容分析
        print("测试内容分析...")
        content_result = asyncio.run(ai_service.analyze_photo_content(test_image_path))
        print(f"内容分析结果: {content_result}")
        
        # 测试质量分析
        print("测试质量分析...")
        quality_result = asyncio.run(ai_service.analyze_photo_quality(test_image_path))
        print(f"质量分析结果: {quality_result}")
        
        # 测试标签生成
        print("测试标签生成...")
        tags_result = asyncio.run(ai_service.generate_photo_tags(test_image_path))
        print(f"标签生成结果: {tags_result}")
        
        # 测试分类
        print("测试照片分类...")
        classify_result = asyncio.run(ai_service.classify_photo(test_image_path))
        print(f"分类结果: {classify_result}")
        
        return True
    except Exception as e:
        print(f"AI服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=" * 50)
    print("智能照片整理系统测试")
    print("=" * 50)
    
    # 测试数据库连接
    if not test_database_connection():
        print("数据库连接测试失败，退出测试")
        return
    
    # 测试AI服务
    if not test_ai_service():
        print("AI服务测试失败，但继续其他测试")
    
    # 测试照片分析
    await test_photo_analysis()
    
    print("=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
