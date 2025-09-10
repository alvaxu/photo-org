#!/usr/bin/env python3
"""
检查数据库结构和数据
"""

from app.db.session import get_db
from app.models.photo import Photo, PhotoQuality, PhotoAnalysis

def check_database_structure():
    """检查数据库结构和数据"""
    db = next(get_db())
    
    try:
        # 检查照片数据
        photo = db.query(Photo).first()
        if photo:
            print(f"照片ID: {photo.id}")
            print(f"照片状态: {photo.status}")
            print(f"照片文件名: {photo.filename}")
            
            # 检查质量评估数据
            quality = db.query(PhotoQuality).filter(PhotoQuality.photo_id == photo.id).first()
            print(f"质量评估存在: {quality is not None}")
            if quality:
                print("质量评估字段:")
                for attr in dir(quality):
                    if not attr.startswith('_') and not callable(getattr(quality, attr)):
                        value = getattr(quality, attr)
                        print(f"  {attr}: {value}")
            
            # 检查分析结果数据
            analysis = db.query(PhotoAnalysis).filter(PhotoAnalysis.photo_id == photo.id).first()
            print(f"分析结果存在: {analysis is not None}")
            if analysis:
                print(f"分析类型: {analysis.analysis_type}")
                print(f"分析结果: {analysis.analysis_result}")
                print(f"置信度: {analysis.confidence_score}")
                
    except Exception as e:
        print(f"错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database_structure()
