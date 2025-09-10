#!/usr/bin/env python3
"""
检查分析结果中的关键词
"""

from app.db.session import get_db
from sqlalchemy import text

def check_analysis_results():
    """检查分析结果中的关键词"""
    db = next(get_db())
    
    try:
        # 检查包含"生日"关键词的分析结果
        result = db.execute(text("SELECT photo_id, analysis_result FROM photo_analysis WHERE analysis_result LIKE '%生日%'"))
        rows = result.fetchall()
        print("包含生日关键词的分析结果:")
        for row in rows:
            print(f"照片ID: {row[0]}")
            print(f"分析结果: {row[1]}")
            print("---")
        
        # 检查所有分析结果
        result = db.execute(text("SELECT photo_id, analysis_result FROM photo_analysis LIMIT 3"))
        rows = result.fetchall()
        print("\n前3个分析结果:")
        for row in rows:
            print(f"照片ID: {row[0]}")
            print(f"分析结果: {row[1]}")
            print("---")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_analysis_results()
