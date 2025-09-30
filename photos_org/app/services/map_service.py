"""
地图服务模块
负责GPS坐标转地址功能，使用高德地图API
"""
import time
import logging
from typing import Optional, Dict, Tuple, List
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)


class MapCacheService:
    """地图缓存服务"""

    def __init__(self):
        self.cache_enabled = settings.maps.cache_enabled
        self.cache_ttl = settings.maps.cache_ttl
        # 使用内存缓存，生产环境建议用Redis
        self.cache = {}  # 格式: {coord_key: (address, timestamp)}

    def get_cached_address(self, lat: float, lng: float) -> Optional[str]:
        """获取缓存的地址"""
        if not self.cache_enabled:
            return None

        coord_key = f"{lat:.6f}_{lng:.6f}"
        cached_item = self.cache.get(coord_key)

        if cached_item:
            address, timestamp = cached_item
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"缓存命中: {coord_key} -> {address}")
                return address
            else:
                # 缓存过期，删除
                logger.debug(f"缓存过期: {coord_key}")
                del self.cache[coord_key]

        return None

    def set_cached_address(self, lat: float, lng: float, address: str):
        """缓存地址"""
        if not self.cache_enabled:
            return

        coord_key = f"{lat:.6f}_{lng:.6f}"
        self.cache[coord_key] = (address, time.time())
        logger.debug(f"地址缓存: {coord_key} -> {address}")


class AMapService:
    """高德地图服务"""

    def __init__(self):
        self.api_key = settings.maps.api_key
        self.base_url = "https://restapi.amap.com"
        self.timeout = settings.maps.timeout

    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        GPS坐标转地址（逆地理编码）

        :param lat: 纬度
        :param lng: 经度
        :return: 格式化的地址字符串
        """
        if not self.api_key:
            raise ValueError("高德API Key未配置")

        url = f"{self.base_url}/v3/geocode/regeo"
        params = {
            "location": f"{lng},{lat}",  # 高德API：经度,纬度
            "key": self.api_key,
            "radius": 1000,  # 搜索半径(米)
            "extensions": "all",  # 返回详细信息
            "output": "json"
        }

        try:
            logger.debug(f"调用高德API: lat={lat}, lng={lng}")
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()

            if data.get("status") == "1" and data.get("info") == "OK":
                address = data["regeocode"]["formatted_address"]
                logger.debug(f"高德API调用成功: {address}")
                return address
            else:
                error_info = data.get('info', '未知错误')
                logger.warning(f"高德API调用失败: {error_info}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"高德API调用超时: {self.timeout}秒")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"高德API网络异常: {e}")
            return None
        except Exception as e:
            logger.error(f"高德API调用异常: {e}")
            return None

    def batch_reverse_geocode(self, locations: List[Tuple[float, float]]) -> Dict[str, str]:
        """
        批量GPS坐标转地址

        :param locations: [(lat, lng), ...] 坐标列表
        :return: {coord_key: address} 地址字典
        """
        results = {}

        # 控制并发和频率限制
        batch_size = settings.maps.batch_size
        rate_limit = settings.maps.rate_limit

        logger.info(f"开始批量转换 {len(locations)} 个坐标，批次大小: {batch_size}")

        for i in range(0, len(locations), batch_size):
            batch = locations[i:i + batch_size]
            logger.debug(f"处理批次 {i//batch_size + 1}: {len(batch)} 个坐标")

            # 逐个调用API（简化实现，后续可优化为并发）
            for lat, lng in batch:
                coord_key = f"{lat:.6f}_{lng:.6f}"
                address = self.reverse_geocode(lat, lng)
                if address:
                    results[coord_key] = address

            # 频率控制 - 避免超过每分钟调用限制
            if i + batch_size < len(locations):
                sleep_time = 60 / rate_limit * batch_size
                logger.debug(f"频率控制: 等待 {sleep_time:.2f} 秒")
                time.sleep(sleep_time)

        logger.info(f"批量转换完成: {len(results)}/{len(locations)} 个地址")
        return results
