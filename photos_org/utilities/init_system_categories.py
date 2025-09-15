"""
程序说明：

## 1. 功能
初始化5个系统分类到数据库中，用于新的分类标签系统

## 2. 特点
- 检查分类是否已存在，避免重复创建
- 支持更新现有分类的描述和排序
- 保持向后兼容性，不影响现有分类数据

## 3. 使用方法
python utilities/init_system_categories.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db
from app.models.photo import Category
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

# 使用应用配置的日志系统
from app.core.logging import get_logger
logger = get_logger(__name__)

def init_system_categories():
    """
    初始化5个系统分类
    
    :return: 初始化结果
    """
    # 定义5个系统分类
    system_categories = [
        {
            'name': '家庭照片',
            'description': '家庭聚会、孩子玩耍、亲子活动等家庭相关照片',
            'sort_order': 1
        },
        {
            'name': '旅行照片',
            'description': '旅行旅游、度假出游、景点观光等旅行相关照片',
            'sort_order': 2
        },
        {
            'name': '工作照片',
            'description': '工作办公、会议商务、出差培训等工作相关照片',
            'sort_order': 3
        },
        {
            'name': '社交活动',
            'description': '社交聚会、派对聚餐、庆祝生日、婚礼节日等社交活动照片',
            'sort_order': 4
        },
        {
            'name': '日常生活',
            'description': '日常购物、休闲娱乐、运动健身、学习读书等日常生活照片',
            'sort_order': 5
        }
    ]
    
    try:
        # 获取数据库会话
        db: Session = next(get_db())
        
        # 检查是否已有系统分类，如果有则跳过初始化
        existing_categories = db.query(Category).count()
        if existing_categories >= 5:  # 系统分类数量
            # 静默跳过，不输出日志
            return {
                "success": True,
                "message": "系统分类已存在，无需初始化",
                "created_count": 0,
                "updated_count": 0
            }
        
        logger.info("开始初始化系统分类...")
        
        created_count = 0
        updated_count = 0
        
        for category_data in system_categories:
            category_name = category_data['name']
            
            # 检查分类是否已存在
            existing_category = db.query(Category).filter(Category.name == category_name).first()
            
            if existing_category:
                # 更新现有分类的描述和排序
                logger.info(f"更新现有分类: {category_name}")
                existing_category.description = category_data['description']
                existing_category.sort_order = category_data['sort_order']
                updated_count += 1
            else:
                # 创建新分类
                logger.info(f"创建新分类: {category_name}")
                new_category = Category(
                    name=category_name,
                    description=category_data['description'],
                    sort_order=category_data['sort_order']
                )
                db.add(new_category)
                created_count += 1
        
        # 提交更改
        db.commit()
        
        logger.info(f"✅ 系统分类初始化完成！")
        logger.info(f"   - 创建新分类: {created_count} 个")
        logger.info(f"   - 更新现有分类: {updated_count} 个")
        
        # 验证结果
        logger.info("\n验证初始化结果:")
        for category_data in system_categories:
            category = db.query(Category).filter(Category.name == category_data['name']).first()
            if category:
                logger.info(f"✅ {category.name} (ID: {category.id}) - {category.description}")
            else:
                logger.error(f"❌ {category_data['name']} 未找到")
        
        return {
            'success': True,
            'created_count': created_count,
            'updated_count': updated_count,
            'total_categories': len(system_categories)
        }
        
    except IntegrityError as e:
        logger.error(f"数据库完整性错误: {e}")
        db.rollback()
        return {
            'success': False,
            'error': f"数据库完整性错误: {e}"
        }
    except Exception as e:
        logger.error(f"初始化系统分类失败: {e}")
        db.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()

def check_existing_categories():
    """
    检查现有分类情况
    
    :return: 分类统计信息
    """
    try:
        db: Session = next(get_db())
        
        # 获取所有分类
        all_categories = db.query(Category).all()
        
        # 按类型分组
        system_categories = []
        other_categories = []
        
        system_names = ['家庭照片', '旅行照片', '工作照片', '社交活动', '日常生活']
        
        for cat in all_categories:
            if cat.name in system_names:
                system_categories.append(cat)
            else:
                other_categories.append(cat)
        
        logger.info(f"数据库分类统计:")
        logger.info(f"  - 系统分类: {len(system_categories)} 个")
        logger.info(f"  - 其他分类: {len(other_categories)} 个")
        logger.info(f"  - 总计: {len(all_categories)} 个")
        
        if system_categories:
            logger.info(f"\n现有系统分类:")
            for cat in system_categories:
                logger.info(f"  - {cat.name} (ID: {cat.id}) - {cat.description}")
        
        return {
            'total_categories': len(all_categories),
            'system_categories': len(system_categories),
            'other_categories': len(other_categories)
        }
        
    except Exception as e:
        logger.error(f"检查现有分类失败: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("系统分类初始化脚本")
    print("=" * 60)
    
    # 检查现有分类
    logger.info("1. 检查现有分类情况...")
    stats = check_existing_categories()
    
    if stats:
        logger.info(f"\n2. 开始初始化系统分类...")
        result = init_system_categories()
        
        if result['success']:
            print(f"\n🎉 初始化成功！")
            print(f"   - 创建新分类: {result['created_count']} 个")
            print(f"   - 更新现有分类: {result['updated_count']} 个")
            print(f"   - 系统分类总数: {result['total_categories']} 个")
        else:
            print(f"\n❌ 初始化失败: {result['error']}")
            sys.exit(1)
    else:
        print("❌ 无法检查现有分类，退出")
        sys.exit(1)
    
    print("=" * 60)
