'''
程序说明：

## 1. 功能特点
- 完全离线运行，无需API调用
- 基于预定义的地理数据库
- 支持全球主要城市和地区
- 快速响应，无网络依赖

## 2. 与其他版本的不同点
- 不依赖外部API服务
- 使用本地数据库和算法
- 支持自定义地理数据

## 3. 数据库初始化
- 数据库需要通过 utilities/init_offline_geocoding_db.py 脚本初始化
- 服务类只负责查询，不负责数据初始化
- 如果数据库不存在或为空，会记录警告信息
'''

import sqlite3
import math
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

class OfflineGeocodingService:
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化离线地理编码服务
        
        :param db_path: 数据库文件路径（可选，如果为None则从配置读取）
        
        注意：数据库需要先通过 utilities/init_offline_geocoding_db.py 脚本初始化
        """
        if db_path is None:
            # 从配置读取路径
            from app.core.config import settings
            db_path = settings.maps.offline_geocoding_db_path
        
        # 解析路径（使用统一的路径解析函数）
        from app.core.path_utils import resolve_resource_path
        db_path_obj = resolve_resource_path(db_path)
        self.db_path = str(db_path_obj)
        
        # 检查数据库是否存在
        self._check_database()
    
    def _check_database(self):
        """
        检查数据库是否存在且包含数据
        
        如果数据库不存在或为空，会记录警告信息
        """
        from pathlib import Path
        import logging
        logger = logging.getLogger(__name__)
        
        db_file = Path(self.db_path)
        if not db_file.exists():
            logger.warning(
                f"离线地理编码数据库不存在: {self.db_path}\n"
                f"请运行以下命令初始化数据库:\n"
                f"  python utilities/init_offline_geocoding_db.py"
            )
            return
        
        # 检查数据库中是否有数据
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('cities', 'countries')
            """)
            tables = cursor.fetchall()
            
            if len(tables) < 2:
                logger.warning(
                    f"离线地理编码数据库表结构不完整: {self.db_path}\n"
                    f"请运行以下命令初始化数据库:\n"
                    f"  python utilities/init_offline_geocoding_db.py"
                )
                conn.close()
                return
            
            # 检查是否有数据
            cursor.execute("SELECT COUNT(*) FROM cities")
            city_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM countries")
            country_count = cursor.fetchone()[0]
            
            conn.close()
            
            if city_count == 0 or country_count == 0:
                logger.warning(
                    f"离线地理编码数据库为空: {self.db_path}\n"
                    f"请运行以下命令初始化数据库:\n"
                    f"  python utilities/init_offline_geocoding_db.py"
                )
            else:
                logger.debug(f"离线地理编码数据库就绪: {self.db_path} (城市: {city_count}, 国家: {country_count})")
                
        except sqlite3.Error as e:
            logger.error(f"检查离线地理编码数据库时出错: {e}")
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两点间的距离（公里）
        :param lat1: 第一个点的纬度
        :param lon1: 第一个点的经度
        :param lat2: 第二个点的纬度
        :param lon2: 第二个点的经度
        :return: 距离（公里）
        """
        # 使用Haversine公式计算球面距离
        R = 6371  # 地球半径（公里）
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def find_nearest_city(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        查找最近的城市
        :param lat: 纬度
        :param lon: 经度
        :return: 最近城市信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有城市
        cursor.execute('SELECT name, country, country_code, latitude, longitude, population, region, timezone FROM cities')
        cities = cursor.fetchall()
        
        min_distance = float('inf')
        nearest_city = None
        
        for city in cities:
            city_lat, city_lon = city[3], city[4]
            distance = self.calculate_distance(lat, lon, city_lat, city_lon)
            
            if distance < min_distance:
                min_distance = distance
                nearest_city = {
                    'name': city[0],
                    'country': city[1],
                    'country_code': city[2],
                    'latitude': city[3],
                    'longitude': city[4],
                    'population': city[5],
                    'region': city[6],
                    'timezone': city[7],
                    'distance_km': distance
                }
        
        conn.close()
        return nearest_city
    
    def get_address_info(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        获取地址信息
        :param lat: 纬度
        :param lon: 经度
        :return: 地址信息
        """
        nearest_city = self.find_nearest_city(lat, lon)
        
        if nearest_city:
            return {
                'service': 'offline',
                'display_name': f"{nearest_city['name']}, {nearest_city['country']}",
                'city': nearest_city['name'],
                'country': nearest_city['country'],
                'country_code': nearest_city['country_code'],
                'region': nearest_city['region'],
                'timezone': nearest_city['timezone'],
                'population': nearest_city['population'],
                'distance_km': nearest_city['distance_km'],
                'coordinates': f"{lat:.6f}, {lon:.6f}",
                'lat': lat,
                'lon': lon
            }
        else:
            return {
                'service': 'offline',
                'display_name': f"坐标位置: {lat:.6f}, {lon:.6f}",
                'city': '未知',
                'country': '未知',
                'country_code': '',
                'region': '未知',
                'timezone': '未知',
                'population': 0,
                'distance_km': 0,
                'coordinates': f"{lat:.6f}, {lon:.6f}",
                'lat': lat,
                'lon': lon
            }
    
    def batch_geocode(self, coordinates: List[tuple]) -> List[Dict[str, Any]]:
        """
        批量地理编码
        :param coordinates: 坐标列表 [(lat, lon), ...]
        :return: 地址信息列表
        """
        results = []
        for lat, lon in coordinates:
            result = self.get_address_info(lat, lon)
            results.append(result)
        return results

# 全局实例
offline_geocoding = OfflineGeocodingService()

def test_offline_geocoding():
    """
    测试离线地理编码服务
    """
    test_coords = [
        (39.9042, 116.4074),  # 北京
        (48.9288, -123.7179),  # 加拿大
        (40.7128, -74.0060),  # 纽约
        (51.5074, -0.1278),   # 伦敦
        (35.6762, 139.6503),  # 东京
    ]
    
    print("测试离线地理编码服务...")
    print("=" * 60)
    
    for lat, lon in test_coords:
        print(f"\n坐标: {lat}, {lon}")
        result = offline_geocoding.get_address_info(lat, lon)
        
        print(f"服务: {result['service']}")
        print(f"地址: {result['display_name']}")
        print(f"城市: {result['city']}")
        print(f"国家: {result['country']}")
        print(f"地区: {result['region']}")
        print(f"时区: {result['timezone']}")
        print(f"距离: {result['distance_km']:.2f} 公里")
        print("-" * 40)

if __name__ == "__main__":
    test_offline_geocoding()
