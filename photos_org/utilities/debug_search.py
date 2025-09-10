#!/usr/bin/env python3
"""
调试搜索功能
"""

from app.db.session import get_db
from app.services.search_service import SearchService
from sqlalchemy import text

def debug_search():
    """调试搜索功能"""
    db = next(get_db())
    search_service = SearchService()
    
    try:
        print("=== 调试搜索功能 ===")
        
        # 测试关键词搜索
        print("\n1. 测试关键词搜索...")
        results, total = search_service.search_photos(
            db=db,
            keyword="生日",
            limit=10,
            offset=0
        )
        print(f"搜索结果数量: {total}")
        print(f"返回照片数: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"照片 {i+1}:")
            print(f"  ID: {result['id']}")
            print(f"  文件名: {result['filename']}")
            print(f"  描述: {result.get('analysis', {}).get('description', '无')}")
            print("---")
        
        # 测试直接SQL查询
        print("\n2. 测试直接SQL查询...")
        result = db.execute(text("""
            SELECT p.id, p.filename, pa.analysis_result
            FROM photos p
            LEFT JOIN photo_analysis pa ON p.id = pa.photo_id
            WHERE p.status = 'completed'
            AND pa.analysis_result LIKE '%生日%'
        """))
        rows = result.fetchall()
        print(f"直接SQL查询结果: {len(rows)} 条")
        for row in rows:
            print(f"  ID: {row[0]}, 文件名: {row[1]}")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_search()
