#!/usr/bin/env python3
"""
检查FTS表是否存在
"""

from app.db.session import get_db
from sqlalchemy import text

def check_fts_tables():
    """检查FTS表是否存在"""
    db = next(get_db())
    
    try:
        # 检查所有表
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = result.fetchall()
        print("所有表:")
        for table in tables:
            print(f"  {table[0]}")
        
        # 检查FTS表
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%'"))
        fts_tables = result.fetchall()
        print(f"\nFTS表: {[t[0] for t in fts_tables]}")
        
        # 检查photos_fts表是否存在
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='photos_fts'"))
        photos_fts = result.fetchall()
        print(f"photos_fts表存在: {len(photos_fts) > 0}")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_fts_tables()
