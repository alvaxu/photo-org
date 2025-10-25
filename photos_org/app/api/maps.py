"""
地图服务API接口
处理高德地图API Key配置和GPS转地址功能
"""

import httpx
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
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

        # 重新加载配置，使更改立即生效
        from app.api.config import reload_config
        await reload_config()

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
    request: Request,
    db: Session = Depends(get_db)
):
    """转换单张照片的GPS为地址"""
    
    # 获取请求体参数
    try:
        body = await request.json()
        service = body.get("service", "amap")
        force = body.get("force", False)
    except:
        service = "amap"
        force = False
    
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    if not photo.location_lat or not photo.location_lng:
        raise HTTPException(status_code=400, detail="照片没有GPS信息")

    # 根据选择的服务进行地址解析
    if service == "amap":
        result = await convert_with_amap(photo.location_lat, photo.location_lng, force)
    elif service == "offline":
        result = await convert_with_offline(photo.location_lat, photo.location_lng)
    elif service == "nominatim":
        result = await convert_with_nominatim(photo.location_lat, photo.location_lng)
    else:
        raise HTTPException(status_code=400, detail="不支持的服务类型")

    if result["success"]:
        # 更新数据库
        photo.location_name = result["address"]
        db.commit()
        
        return {
            "address": result["address"],
            "service": service,
            "success": True,
            "cached": result.get("cached", False),
            "message": result.get("message", "地址解析成功")
        }
    else:
        return {
            "address": None,
            "service": service,
            "success": False,
            "message": result.get("message", "地址解析失败")
        }

async def convert_with_amap(lat: float, lng: float, force: bool = False):
    """使用高德地图API解析地址"""
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    from app.core.config import settings
    
    start_time = time.time()
    logger.info(f"🌐 开始高德API地址解析: 坐标({lat}, {lng}), 强制更新={force}")
    
    if not settings.maps.api_key:
        logger.warning("❌ 高德地图API密钥未配置")
        return {
            "success": False,
            "message": "高德地图API密钥未配置"
        }
    
    # 检查缓存
    cache_service = MapCacheService()
    if not force:
        cached_address = cache_service.get_cached_address(lat, lng)
        if cached_address:
            elapsed = time.time() - start_time
            logger.info(f"✅ 使用缓存地址: {cached_address[:50]}... (耗时: {elapsed:.2f}s)")
            return {
                "success": True,
                "address": cached_address,
                "cached": True,
                "message": "使用缓存地址"
            }
    
    # 调用高德API
    logger.info("🔄 调用高德API进行地址解析...")
    map_service = AMapService()
    address = map_service.reverse_geocode(lat, lng)
    
    elapsed = time.time() - start_time
    
    if address:
        # 缓存结果
        cache_service.set_cached_address(lat, lng, address)
        logger.info(f"✅ 高德API解析成功: {address[:50]}... (耗时: {elapsed:.2f}s)")
        return {
            "success": True,
            "address": address,
            "cached": False,
            "message": "高德API解析成功"
        }
    else:
        logger.error(f"❌ 高德API调用失败 (耗时: {elapsed:.2f}s)")
        return {
            "success": False,
            "message": "高德API调用失败"
        }

async def convert_with_offline(lat: float, lng: float):
    """使用离线数据库解析地址"""
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    logger.info(f"🏠 开始离线数据库地址解析: 坐标({lat}, {lng})")
    
    try:
        import sys
        import os
        from pathlib import Path
        
        logger.info("🔄 查询离线数据库...")
        from app.services.offline_geocoding import offline_geocoding
        
        result = offline_geocoding.get_address_info(lat, lng)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ 离线数据库解析成功: {result['display_name'][:50]}... (耗时: {elapsed:.2f}s)")
        
        return {
            "success": True,
            "address": result["display_name"],
            "service": "offline",
            "message": "离线数据库解析成功"
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ 离线服务失败: {str(e)} (耗时: {elapsed:.2f}s)", exc_info=True)
        return {
            "success": False,
            "service": "offline",
            "message": f"离线服务失败: {str(e)}"
        }

async def convert_with_nominatim(lat: float, lng: float):
    """使用Nominatim API解析地址"""
    import logging
    import time
    import requests
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    logger.info(f"🌍 开始Nominatim API地址解析: 坐标({lat}, {lng})")
    
    try:
        # Nominatim API URL
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "addressdetails": 1,
            "accept-language": "zh-CN,en"
        }
        
        # 设置User-Agent（Nominatim要求）
        headers = {
            "User-Agent": "PhotoSystem/1.0 (contact@example.com)"
        }
        
        logger.info("🔄 调用Nominatim API进行地址解析...")
        # 发送请求，设置超时
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data and "display_name" in data:
                logger.info(f"✅ Nominatim API解析成功: {data['display_name'][:50]}... (耗时: {elapsed:.2f}s)")
                return {
                    "success": True,
                    "address": data["display_name"],
                    "service": "nominatim",
                    "message": "Nominatim API解析成功"
                }
            else:
                logger.warning(f"⚠️ Nominatim API返回空结果 (耗时: {elapsed:.2f}s)")
                return {
                    "success": False,
                    "service": "nominatim",
                    "message": "Nominatim API返回空结果"
                }
        else:
            logger.error(f"❌ Nominatim API请求失败: HTTP {response.status_code} (耗时: {elapsed:.2f}s)")
            return {
                "success": False,
                "service": "nominatim",
                "message": f"Nominatim API请求失败: HTTP {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        logger.error(f"❌ Nominatim API请求超时 (耗时: {elapsed:.2f}s)")
        return {
            "success": False,
            "service": "nominatim",
            "message": "Nominatim API请求超时，请检查网络连接或使用科学上网"
        }
    except requests.exceptions.ConnectionError:
        elapsed = time.time() - start_time
        logger.error(f"❌ Nominatim API连接失败 (耗时: {elapsed:.2f}s)")
        return {
            "success": False,
            "service": "nominatim",
            "message": "无法连接到Nominatim API，可能需要科学上网"
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Nominatim服务失败: {str(e)} (耗时: {elapsed:.2f}s)", exc_info=True)
        return {
            "success": False,
            "service": "nominatim",
            "message": f"Nominatim服务失败: {str(e)}"
        }


@router.get("/service-status")
async def get_service_status():
    """获取各服务状态"""
    status = {
        "amap": {
            "available": False,
            "reason": None
        },
        "offline": {
            "available": True,
            "reason": None
        },
        "nominatim": {
            "available": False,
            "reason": None
        }
    }
    
    # 检查高德API状态
    from app.core.config import settings
    if settings.maps.api_key:
        try:
            # 简单测试API
            map_service = AMapService()
            test_result = map_service.reverse_geocode(39.9042, 116.4074)
            status["amap"]["available"] = test_result is not None
            if not test_result:
                status["amap"]["reason"] = "API调用失败"
        except Exception as e:
            status["amap"]["reason"] = f"连接失败: {str(e)}"
    else:
        status["amap"]["reason"] = "API密钥未配置"
    
    # 检查Nominatim API状态
    try:
        import requests
        test_response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": 39.9042, "lon": 116.4074, "format": "json"},
            headers={"User-Agent": "PhotoSystem/1.0"},
            timeout=5
        )
        status["nominatim"]["available"] = test_response.status_code == 200
        if test_response.status_code != 200:
            status["nominatim"]["reason"] = f"HTTP {test_response.status_code}"
    except requests.exceptions.Timeout:
        status["nominatim"]["reason"] = "请求超时，可能需要科学上网"
    except requests.exceptions.ConnectionError:
        status["nominatim"]["reason"] = "连接失败，可能需要科学上网"
    except Exception as e:
        status["nominatim"]["reason"] = f"测试失败: {str(e)}"
    
    return status

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
    request: Request,
    db: Session = Depends(get_db)
):
    """批量转换GPS为地址"""
    
    # 从请求体中获取参数
    body = await request.json()
    service = body.get("service", "amap")
    limit = body.get("limit")

    # 🔥 如果没有传入limit，使用配置的batch_size
    from app.core.config import settings as current_settings
    if limit is None:
        limit = current_settings.maps.batch_size
        print(f"使用配置的批次大小: {limit}")
    
    print(f"批量转换使用服务: {service}")

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

    # 使用选择的服务进行批量转换
    success_count = 0
    error_count = 0
    
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    logger.info(f"🚀 开始批量地址解析: 服务={service}, 照片数量={len(photos_to_convert)}")
    
    for i, photo in enumerate(photos_to_convert, 1):
        try:
            logger.info(f"📸 处理照片 {i}/{len(photos_to_convert)}: ID={photo.id}, 坐标=({photo.location_lat}, {photo.location_lng})")
            
            if service == "amap":
                result = await convert_with_amap(photo.location_lat, photo.location_lng, False)
            elif service == "offline":
                result = await convert_with_offline(photo.location_lat, photo.location_lng)
            elif service == "nominatim":
                # Nominatim API有请求频率限制，添加延迟
                if i > 1:  # 第一张照片不需要延迟
                    logger.info("⏳ Nominatim API请求间隔控制: 等待1秒...")
                    time.sleep(1)
                result = await convert_with_nominatim(photo.location_lat, photo.location_lng)
            else:
                result = {"success": False, "message": "不支持的服务类型"}
            
            if result["success"]:
                photo.location_name = result["address"]
                success_count += 1
                logger.info(f"✅ 照片 {i} 地址解析成功: {result['address'][:50]}...")
            else:
                error_count += 1
                logger.error(f"❌ 照片 {i} 地址解析失败: {result.get('message', '未知错误')}")
        except Exception as e:
            error_count += 1
            logger.error(f"❌ 照片 {i} 处理异常: {str(e)}", exc_info=True)
    
    # 提交数据库更改
    db.commit()
    
    logger.info(f"🎉 批量地址解析完成: 成功 {success_count}, 失败 {error_count}, 服务={service}")

    return {
        "message": f"批量转换完成: 成功 {success_count}, 失败 {error_count}",
        "count": len(photos_to_convert),
        "success_count": success_count,
        "error_count": error_count,
        "service": service
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
