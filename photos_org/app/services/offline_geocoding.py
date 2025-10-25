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
'''

import sqlite3
import math
import os
from typing import Optional, Dict, Any, List

class OfflineGeocodingService:
    def __init__(self, db_path: str = "offline_geocoding.db"):
        """
        初始化离线地理编码服务
        :param db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """
        初始化地理数据库
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建城市表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                country TEXT NOT NULL,
                country_code TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                population INTEGER,
                region TEXT,
                timezone TEXT
            )
        ''')
        
        # 创建国家表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS countries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                continent TEXT,
                capital TEXT,
                latitude REAL,
                longitude REAL
            )
        ''')
        
        # 插入主要城市数据
        cities_data = [
            # 中国城市
            ('北京', '中国', 'CN', 39.9042, 116.4074, 21540000, '华北', 'Asia/Shanghai'),
            ('上海', '中国', 'CN', 31.2304, 121.4737, 24280000, '华东', 'Asia/Shanghai'),
            ('广州', '中国', 'CN', 23.1291, 113.2644, 15300000, '华南', 'Asia/Shanghai'),
            ('深圳', '中国', 'CN', 22.5431, 114.0579, 17560000, '华南', 'Asia/Shanghai'),
            ('成都', '中国', 'CN', 30.5728, 104.0668, 20930000, '西南', 'Asia/Shanghai'),
            ('杭州', '中国', 'CN', 30.2741, 120.1551, 11940000, '华东', 'Asia/Shanghai'),
            ('南京', '中国', 'CN', 32.0603, 118.7969, 9420000, '华东', 'Asia/Shanghai'),
            ('武汉', '中国', 'CN', 30.5928, 114.3055, 12320000, '华中', 'Asia/Shanghai'),
            ('西安', '中国', 'CN', 34.3416, 108.9398, 12950000, '西北', 'Asia/Shanghai'),
            ('重庆', '中国', 'CN', 29.4316, 106.9123, 32050000, '西南', 'Asia/Shanghai'),
            
            # 加拿大城市
            ('温哥华', '加拿大', 'CA', 49.2827, -123.1207, 675218, 'BC', 'America/Vancouver'),
            ('多伦多', '加拿大', 'CA', 43.6532, -79.3832, 2930000, 'ON', 'America/Toronto'),
            ('蒙特利尔', '加拿大', 'CA', 45.5017, -73.5673, 1780000, 'QC', 'America/Montreal'),
            ('卡尔加里', '加拿大', 'CA', 51.0447, -114.0719, 1300000, 'AB', 'America/Edmonton'),
            ('渥太华', '加拿大', 'CA', 45.4215, -75.6972, 1017449, 'ON', 'America/Toronto'),
            
            # 美国城市
            ('纽约', '美国', 'US', 40.7128, -74.0060, 8336817, 'NY', 'America/New_York'),
            ('洛杉矶', '美国', 'US', 34.0522, -118.2437, 3979576, 'CA', 'America/Los_Angeles'),
            ('芝加哥', '美国', 'US', 41.8781, -87.6298, 2693976, 'IL', 'America/Chicago'),
            ('休斯顿', '美国', 'US', 29.7604, -95.3698, 2320268, 'TX', 'America/Chicago'),
            ('费城', '美国', 'US', 39.9526, -75.1652, 1584064, 'PA', 'America/New_York'),
            
            # 欧洲城市
            ('伦敦', '英国', 'GB', 51.5074, -0.1278, 8982000, 'England', 'Europe/London'),
            ('巴黎', '法国', 'FR', 48.8566, 2.3522, 2161000, 'Île-de-France', 'Europe/Paris'),
            ('柏林', '德国', 'DE', 52.5200, 13.4050, 3669491, 'Berlin', 'Europe/Berlin'),
            ('罗马', '意大利', 'IT', 41.9028, 12.4964, 2873000, 'Lazio', 'Europe/Rome'),
            ('马德里', '西班牙', 'ES', 40.4168, -3.7038, 3223000, 'Madrid', 'Europe/Madrid'),
            
            # 亚洲城市
            ('东京', '日本', 'JP', 35.6762, 139.6503, 13960000, 'Tokyo', 'Asia/Tokyo'),
            ('首尔', '韩国', 'KR', 37.5665, 126.9780, 9720846, 'Seoul', 'Asia/Seoul'),
            ('新加坡', '新加坡', 'SG', 1.3521, 103.8198, 5453600, 'Singapore', 'Asia/Singapore'),
            ('曼谷', '泰国', 'TH', 13.7563, 100.5018, 10539000, 'Bangkok', 'Asia/Bangkok'),
            ('吉隆坡', '马来西亚', 'MY', 3.1390, 101.6869, 1588000, 'Kuala Lumpur', 'Asia/Kuala_Lumpur'),
            
            # 大洋洲城市
            ('悉尼', '澳大利亚', 'AU', -33.8688, 151.2093, 5312000, 'NSW', 'Australia/Sydney'),
            ('墨尔本', '澳大利亚', 'AU', -37.8136, 144.9631, 5078000, 'VIC', 'Australia/Melbourne'),
            ('奥克兰', '新西兰', 'NZ', -36.8485, 174.7633, 1657000, 'Auckland', 'Pacific/Auckland'),
        ]
        
        # 插入城市数据
        cursor.executemany('''
            INSERT OR REPLACE INTO cities (name, country, country_code, latitude, longitude, population, region, timezone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', cities_data)
        
        # 插入国家数据
        countries_data = [
            ('中国', 'CN', '亚洲', '北京', 39.9042, 116.4074),
            ('加拿大', 'CA', '北美洲', '渥太华', 45.4215, -75.6972),
            ('美国', 'US', '北美洲', '华盛顿', 38.9072, -77.0369),
            ('英国', 'GB', '欧洲', '伦敦', 51.5074, -0.1278),
            ('法国', 'FR', '欧洲', '巴黎', 48.8566, 2.3522),
            ('德国', 'DE', '欧洲', '柏林', 52.5200, 13.4050),
            ('日本', 'JP', '亚洲', '东京', 35.6762, 139.6503),
            ('韩国', 'KR', '亚洲', '首尔', 37.5665, 126.9780),
            ('澳大利亚', 'AU', '大洋洲', '堪培拉', -35.2809, 149.1300),
            ('新西兰', 'NZ', '大洋洲', '惠灵顿', -41.2924, 174.7787),
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO countries (name, code, continent, capital, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', countries_data)
        
        conn.commit()
        conn.close()
        print(f"✅ 离线地理数据库初始化完成: {self.db_path}")
    
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
