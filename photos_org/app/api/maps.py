"""
地图服务API接口
处理高德地图API Key配置和GPS转地址功能
"""

import httpx
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import json
import os
from pathlib import Path
from typing import List, Tuple

from app.core.config import settings
from app.db.session import get_db
from app.models.photo import Photo
from app.services.map_service import AMapService, MapCacheService

router = APIRouter()

class ApiKeyConfig(BaseModel):
    api_key: str

class GeocodeTest(BaseModel):
    lat: float
    lng: float
    api_key: str

@router.get("/config")
async def get_maps_config():
    """获取地图API配置"""
    try:
        # 从配置文件读取高德API Key
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            maps_config = config.get('maps', {})
            # 不返回API Key，只返回配置状态
            return {
                "configured": bool(maps_config.get('api_key')),
                "provider": maps_config.get('provider', 'amap')
            }
        else:
            return {
                "configured": False,
                "provider": "amap"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取配置失败: {str(e)}")

@router.post("/config")
async def update_maps_config(config: ApiKeyConfig):
    """更新地图API配置"""
    try:
        # 验证API Key格式
        if not config.api_key or len(config.api_key) != 32:
            raise HTTPException(status_code=400, detail="API Key格式不正确，应为32位字符串")

        # 读取现有配置
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
        else:
            existing_config = {}

        # 更新地图配置
        if 'maps' not in existing_config:
            existing_config['maps'] = {}

        existing_config['maps'].update({
            'api_key': config.api_key,
            'provider': 'amap',
            'configured': True
        })

        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)

        return {"message": "高德API Key配置成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")

@router.post("/test-geocode")
async def test_geocode_api(test_data: GeocodeTest):
    """测试高德地图API Key是否有效"""
    try:
        # 验证API Key格式
        if not test_data.api_key or len(test_data.api_key) != 32:
            raise HTTPException(status_code=400, detail="API Key格式不正确，应为32位字符串")

        # 调用高德地图逆地理编码API
        url = "https://restapi.amap.com/v3/geocode/regeo"
        params = {
            'key': test_data.api_key,
            'location': f"{test_data.lng},{test_data.lat}",
            'extensions': 'base',
            'output': 'json'
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="API调用失败，请检查网络")

        result = response.json()

        # 检查API响应
        if result.get('status') != '1':
            error_msg = result.get('info', '未知错误')
            if 'INVALID_USER_KEY' in error_msg:
                raise HTTPException(status_code=400, detail="API Key无效或不存在")
            elif 'INSUFFICIENT_PRIVILEGES' in error_msg:
                raise HTTPException(status_code=400, detail="API Key权限不足")
            else:
                raise HTTPException(status_code=400, detail=f"API调用失败: {error_msg}")

        # 提取地址信息
        regeocode = result.get('regeocode', {})
        formatted_address = regeocode.get('formatted_address', '')

        if not formatted_address:
            raise HTTPException(status_code=400, detail="无法获取地址信息")

        return {
            "address": formatted_address,
            "message": "API Key测试成功"
        }

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="API调用超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")

@router.get("/stats")
async def get_maps_stats():
    """获取地图API使用统计"""
    # 暂时返回默认统计，后续可以实现真正的统计
    return {
        "total_calls": 0,
        "success_rate": 0.0,
        "cache_hit_rate": 0.0,
        "remaining_quota": 6000  # 高德每月免费额度
    }


# GPS转地址相关接口

@router.post("/photos/{photo_id}/convert-gps-address")
async def convert_single_photo_address(
    photo_id: int,
    force: bool = False,
    db: Session = Depends(get_db)
):
    """转换单张照片的GPS为地址"""

    # 检查API Key
    if not settings.maps.api_key:
        raise HTTPException(
            status_code=400,
            detail="请先配置高德地图API Key",
            headers={"X-Help-Page": "/help-gaode-api-key"}
        )

    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    if not photo.location_lat or not photo.location_lng:
        raise HTTPException(status_code=400, detail="照片没有GPS信息")

    # 检查缓存
    cache_service = MapCacheService()
    cached_address = cache_service.get_cached_address(
        photo.location_lat, photo.location_lng
    )

    if cached_address and not force:
        # 更新数据库但不重新调用API
        photo.location_name = cached_address
        db.commit()
        return {
            "address": cached_address,
            "cached": True,
            "message": "使用缓存地址"
        }

    # 调用高德API
    map_service = AMapService()
    address = map_service.reverse_geocode(
        photo.location_lat,
        photo.location_lng
    )

    if not address:
        raise HTTPException(status_code=500, detail="地址解析失败，请检查网络或API Key")

    # 缓存结果
    cache_service.set_cached_address(
        photo.location_lat,
        photo.location_lng,
        address
    )

    # 更新数据库
    photo.location_name = address
    db.commit()

    return {
        "address": address,
        "cached": False,
        "message": "地址转换成功"
    }


@router.get("/photos/gps-stats")
async def get_gps_photo_stats(db: Session = Depends(get_db)):
    """获取GPS照片统计信息"""
    total_photos = db.query(func.count(Photo.id)).scalar()
    photos_with_gps = db.query(func.count(Photo.id)).filter(
        Photo.location_lat.isnot(None),
        Photo.location_lng.isnot(None)
    ).scalar()

    photos_with_address = db.query(func.count(Photo.id)).filter(
        Photo.location_name.isnot(None)
    ).scalar()

    photos_gps_without_address = db.query(func.count(Photo.id)).filter(
        Photo.location_lat.isnot(None),
        Photo.location_lng.isnot(None),
        Photo.location_name.is_(None)
    ).scalar()

    return {
        "total_photos": total_photos,
        "photos_with_gps": photos_with_gps,
        "photos_with_address": photos_with_address,
        "has_gps_without_address": photos_gps_without_address,
        "gps_coverage": round(photos_with_gps / total_photos * 100, 1) if total_photos > 0 else 0
    }


@router.post("/photos/batch-convert-gps-address")
async def batch_convert_gps_address(
    limit: int = 50,  # 最多处理多少张照片
    db: Session = Depends(get_db)
):
    """批量转换GPS为地址"""

    # 检查API Key
    if not settings.maps.api_key:
        raise HTTPException(
            status_code=400,
            detail="请先配置高德地图API Key",
            headers={"X-Help-Page": "/help-gaode-api-key"}
        )

    # 获取需要转换的照片（有GPS但没有地址的照片）
    photos_to_convert = db.query(Photo).filter(
        Photo.location_lat.isnot(None),
        Photo.location_lng.isnot(None),
        Photo.location_name.is_(None)
    ).limit(limit).all()

    if not photos_to_convert:
        return {
            "message": "没有需要转换的照片",
            "count": 0
        }

    # 直接执行批量转换（改为同步执行）
    success_count, error_count = await process_batch_gps_conversion_sync(
        [photo.id for photo in photos_to_convert]
    )

    return {
        "message": f"批量转换完成: 成功 {success_count}, 失败 {error_count}",
        "count": len(photos_to_convert),
        "success_count": success_count,
        "error_count": error_count
    }


async def process_batch_gps_conversion_sync(photo_ids: List[int]) -> Tuple[int, int]:
    """同步处理批量GPS转换"""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        map_service = AMapService()
        cache_service = MapCacheService()

        success_count = 0
        error_count = 0

        for photo_id in photo_ids:
            try:
                photo = db.query(Photo).filter(Photo.id == photo_id).first()
                if not photo or not photo.location_lat or not photo.location_lng:
                    continue

                # 检查缓存
                cached_address = cache_service.get_cached_address(
                    photo.location_lat, photo.location_lng
                )

                if cached_address:
                    photo.location_name = cached_address
                    success_count += 1
                    continue

                # 调用API
                address = map_service.reverse_geocode(
                    photo.location_lat, photo.location_lng
                )

                if address:
                    # 缓存结果
                    cache_service.set_cached_address(
                        photo.location_lat, photo.location_lng,
                        address
                    )
                    photo.location_name = address
                    success_count += 1
                else:
                    error_count += 1

                # 提交每张照片的变更
                db.commit()

            except Exception as e:
                error_count += 1
                print(f"转换照片 {photo_id} 失败: {e}")
                continue

        print(f"批量转换完成: 成功 {success_count}, 失败 {error_count}")
        return success_count, error_count

    except Exception as e:
        print(f"批量转换任务异常: {e}")
        return 0, len(photo_ids)
    finally:
        db.close()


async def process_batch_gps_conversion(photo_ids: List[int]):
    """后台处理批量GPS转换（保留兼容性）"""
    await process_batch_gps_conversion_sync(photo_ids)
