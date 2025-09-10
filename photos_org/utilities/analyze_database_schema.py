#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库结构分析脚本
分析所有表的字段、类型、关系和含义
"""

from sqlalchemy import text, inspect
from app.db.session import get_db
from app.models import base
from app.models.photo import *

def analyze_database_schema():
    """分析数据库结构"""
    print("=== 家庭单机版智能照片整理系统 - 数据库结构分析 ===\n")
    
    db = next(get_db())
    inspector = inspect(db.bind)
    
    # 获取所有表名
    tables = inspector.get_table_names()
    print(f"📊 数据库中共有 {len(tables)} 个表:")
    for table in tables:
        print(f"  - {table}")
    print()
    
    # 分析每个表
    for table_name in tables:
        print(f"🔍 分析表: {table_name}")
        print("-" * 50)
        
        # 获取列信息
        columns = inspector.get_columns(table_name)
        print(f"字段数量: {len(columns)}")
        
        for col in columns:
            nullable = "可空" if col['nullable'] else "非空"
            default = f"默认值: {col['default']}" if col['default'] is not None else "无默认值"
            print(f"  📝 {col['name']:<20} {str(col['type']):<15} {nullable:<4} {default}")
        
        # 获取外键信息
        foreign_keys = inspector.get_foreign_keys(table_name)
        if foreign_keys:
            print(f"\n🔗 外键关系:")
            for fk in foreign_keys:
                print(f"  {fk['constrained_columns'][0]} -> {fk['referred_table']}.{fk['referred_columns'][0]}")
        
        # 获取索引信息
        indexes = inspector.get_indexes(table_name)
        if indexes:
            print(f"\n📇 索引:")
            for idx in indexes:
                unique = "唯一" if idx['unique'] else "普通"
                print(f"  {idx['name']} ({unique}): {', '.join(idx['column_names'])}")
        
        print("\n" + "="*60 + "\n")
    
    # 分析模型关系
    print("🔗 模型关系分析:")
    print("-" * 30)
    
    # Photo表的关系
    print("📸 Photo表关系:")
    print("  - analysis_results -> PhotoAnalysis (一对多)")
    print("  - quality_assessments -> PhotoQuality (一对多)")
    print("  - tags -> PhotoTag -> Tag (多对多)")
    print("  - categories -> PhotoCategory -> Category (多对多)")
    
    print("\n🏷️ Tag表关系:")
    print("  - photos -> PhotoTag -> Photo (多对多)")
    
    print("\n📂 Category表关系:")
    print("  - photos -> PhotoCategory -> Photo (多对多)")
    
    print("\n🤖 PhotoAnalysis表关系:")
    print("  - photo -> Photo (多对一)")
    
    print("\n⭐ PhotoQuality表关系:")
    print("  - photo -> Photo (多对一)")
    
    # 检查数据
    print("\n📊 数据统计:")
    print("-" * 20)
    
    for table_name in tables:
        try:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            print(f"  {table_name}: {count} 条记录")
        except Exception as e:
            print(f"  {table_name}: 查询失败 - {e}")
    
    db.close()
    print("\n=== 分析完成 ===")

if __name__ == '__main__':
    analyze_database_schema()


