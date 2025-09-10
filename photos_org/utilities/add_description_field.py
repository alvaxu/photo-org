#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加description字段到Photo表
"""

from sqlalchemy import text
from app.db.session import get_db

def add_description_field():
    """添加description字段到Photo表"""
    print("开始添加description字段到Photo表...")
    
    db = next(get_db())
    
    try:
        # 添加description字段
        db.execute(text("ALTER TABLE photos ADD COLUMN description TEXT"))
        db.commit()
        print("✅ description字段添加成功")
        
    except Exception as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("✅ description字段已存在")
        else:
            print(f"❌ 添加description字段失败: {e}")
            db.rollback()
    
    finally:
        db.close()

if __name__ == '__main__':
    add_description_field()


