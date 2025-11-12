#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线地理编码数据库初始化脚本

此脚本用于创建和初始化离线地理编码数据库。
数据库包含全球主要城市和国家信息，用于GPS坐标转地址功能。

使用方法：
    python utilities/init_offline_geocoding_db.py

作者：AI助手
创建日期：2025年1月20日
"""

import sys
import os
import sqlite3
import re
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.path_utils import resolve_resource_path


# 国家代码到国家名称的映射（ISO 3166-1 alpha-2）
COUNTRY_CODE_MAP = {
    'AD': '安道尔', 'AE': '阿联酋', 'AF': '阿富汗', 'AG': '安提瓜和巴布达', 'AI': '安圭拉',
    'AL': '阿尔巴尼亚', 'AM': '亚美尼亚', 'AO': '安哥拉', 'AQ': '南极洲', 'AR': '阿根廷',
    'AS': '美属萨摩亚', 'AT': '奥地利', 'AU': '澳大利亚', 'AW': '阿鲁巴', 'AX': '奥兰群岛',
    'AZ': '阿塞拜疆', 'BA': '波黑', 'BB': '巴巴多斯', 'BD': '孟加拉国', 'BE': '比利时',
    'BF': '布基纳法索', 'BG': '保加利亚', 'BH': '巴林', 'BI': '布隆迪', 'BJ': '贝宁',
    'BL': '圣巴泰勒米', 'BM': '百慕大', 'BN': '文莱', 'BO': '玻利维亚', 'BQ': '荷属加勒比',
    'BR': '巴西', 'BS': '巴哈马', 'BT': '不丹', 'BV': '布韦岛', 'BW': '博茨瓦纳',
    'BY': '白俄罗斯', 'BZ': '伯利兹', 'CA': '加拿大', 'CC': '科科斯群岛', 'CD': '刚果(金)',
    'CF': '中非', 'CG': '刚果(布)', 'CH': '瑞士', 'CI': '科特迪瓦', 'CK': '库克群岛',
    'CL': '智利', 'CM': '喀麦隆', 'CN': '中国', 'CO': '哥伦比亚', 'CR': '哥斯达黎加',
    'CU': '古巴', 'CV': '佛得角', 'CW': '库拉索', 'CX': '圣诞岛', 'CY': '塞浦路斯',
    'CZ': '捷克', 'DE': '德国', 'DJ': '吉布提', 'DK': '丹麦', 'DM': '多米尼克',
    'DO': '多米尼加', 'DZ': '阿尔及利亚', 'EC': '厄瓜多尔', 'EE': '爱沙尼亚', 'EG': '埃及',
    'EH': '西撒哈拉', 'ER': '厄立特里亚', 'ES': '西班牙', 'ET': '埃塞俄比亚', 'FI': '芬兰',
    'FJ': '斐济', 'FK': '福克兰群岛', 'FM': '密克罗尼西亚', 'FO': '法罗群岛', 'FR': '法国',
    'GA': '加蓬', 'GB': '英国', 'GD': '格林纳达', 'GE': '格鲁吉亚', 'GF': '法属圭亚那',
    'GG': '根西岛', 'GH': '加纳', 'GI': '直布罗陀', 'GL': '格陵兰', 'GM': '冈比亚',
    'GN': '几内亚', 'GP': '瓜德罗普', 'GQ': '赤道几内亚', 'GR': '希腊', 'GS': '南乔治亚',
    'GT': '危地马拉', 'GU': '关岛', 'GW': '几内亚比绍', 'GY': '圭亚那', 'HK': '香港',
    'HM': '赫德岛', 'HN': '洪都拉斯', 'HR': '克罗地亚', 'HT': '海地', 'HU': '匈牙利',
    'ID': '印度尼西亚', 'IE': '爱尔兰', 'IL': '以色列', 'IM': '马恩岛', 'IN': '印度',
    'IO': '英属印度洋领地', 'IQ': '伊拉克', 'IR': '伊朗', 'IS': '冰岛', 'IT': '意大利',
    'JE': '泽西岛', 'JM': '牙买加', 'JO': '约旦', 'JP': '日本', 'KE': '肯尼亚',
    'KG': '吉尔吉斯斯坦', 'KH': '柬埔寨', 'KI': '基里巴斯', 'KM': '科摩罗', 'KN': '圣基茨和尼维斯',
    'KP': '朝鲜', 'KR': '韩国', 'KW': '科威特', 'KY': '开曼群岛', 'KZ': '哈萨克斯坦',
    'LA': '老挝', 'LB': '黎巴嫩', 'LC': '圣卢西亚', 'LI': '列支敦士登', 'LK': '斯里兰卡',
    'LR': '利比里亚', 'LS': '莱索托', 'LT': '立陶宛', 'LU': '卢森堡', 'LV': '拉脱维亚',
    'LY': '利比亚', 'MA': '摩洛哥', 'MC': '摩纳哥', 'MD': '摩尔多瓦', 'ME': '黑山',
    'MF': '法属圣马丁', 'MG': '马达加斯加', 'MH': '马绍尔群岛', 'MK': '北马其顿', 'ML': '马里',
    'MM': '缅甸', 'MN': '蒙古', 'MO': '澳门', 'MP': '北马里亚纳群岛', 'MQ': '马提尼克',
    'MR': '毛里塔尼亚', 'MS': '蒙特塞拉特', 'MT': '马耳他', 'MU': '毛里求斯', 'MV': '马尔代夫',
    'MW': '马拉维', 'MX': '墨西哥', 'MY': '马来西亚', 'MZ': '莫桑比克', 'NA': '纳米比亚',
    'NC': '新喀里多尼亚', 'NE': '尼日尔', 'NF': '诺福克岛', 'NG': '尼日利亚', 'NI': '尼加拉瓜',
    'NL': '荷兰', 'NO': '挪威', 'NP': '尼泊尔', 'NR': '瑙鲁', 'NU': '纽埃',
    'NZ': '新西兰', 'OM': '阿曼', 'PA': '巴拿马', 'PE': '秘鲁', 'PF': '法属波利尼西亚',
    'PG': '巴布亚新几内亚', 'PH': '菲律宾', 'PK': '巴基斯坦', 'PL': '波兰', 'PM': '圣皮埃尔和密克隆',
    'PN': '皮特凯恩', 'PR': '波多黎各', 'PS': '巴勒斯坦', 'PT': '葡萄牙', 'PW': '帕劳',
    'PY': '巴拉圭', 'QA': '卡塔尔', 'RE': '留尼汪', 'RO': '罗马尼亚', 'RS': '塞尔维亚',
    'RU': '俄罗斯', 'RW': '卢旺达', 'SA': '沙特阿拉伯', 'SB': '所罗门群岛', 'SC': '塞舌尔',
    'SD': '苏丹', 'SE': '瑞典', 'SG': '新加坡', 'SH': '圣赫勒拿', 'SI': '斯洛文尼亚',
    'SJ': '斯瓦尔巴和扬马延', 'SK': '斯洛伐克', 'SL': '塞拉利昂', 'SM': '圣马力诺', 'SN': '塞内加尔',
    'SO': '索马里', 'SR': '苏里南', 'SS': '南苏丹', 'ST': '圣多美和普林西比', 'SV': '萨尔瓦多',
    'SX': '荷属圣马丁', 'SY': '叙利亚', 'SZ': '斯威士兰', 'TC': '特克斯和凯科斯群岛', 'TD': '乍得',
    'TF': '法属南部领地', 'TG': '多哥', 'TH': '泰国', 'TJ': '塔吉克斯坦', 'TK': '托克劳',
    'TL': '东帝汶', 'TM': '土库曼斯坦', 'TN': '突尼斯', 'TO': '汤加', 'TR': '土耳其',
    'TT': '特立尼达和多巴哥', 'TV': '图瓦卢', 'TW': '台湾', 'TZ': '坦桑尼亚', 'UA': '乌克兰',
    'UG': '乌干达', 'UM': '美国本土外小岛屿', 'US': '美国', 'UY': '乌拉圭', 'UZ': '乌兹别克斯坦',
    'VA': '梵蒂冈', 'VC': '圣文森特和格林纳丁斯', 'VE': '委内瑞拉', 'VG': '英属维尔京群岛', 'VI': '美属维尔京群岛',
    'VN': '越南', 'VU': '瓦努阿图', 'WF': '瓦利斯和富图纳', 'WS': '萨摩亚', 'YE': '也门',
    'YT': '马约特', 'ZA': '南非', 'ZM': '赞比亚', 'ZW': '津巴布韦',
}


def import_from_geonames(geonames_file: str, cursor, batch_size: int = 1000):
    """
    从GeoNames文件导入城市数据
    
    :param geonames_file: GeoNames文件路径
    :param cursor: 数据库游标
    :param batch_size: 批量插入大小
    :return: 导入的城市数量
    """
    geonames_path = Path(geonames_file)
    if not geonames_path.exists():
        raise FileNotFoundError(f"GeoNames文件不存在: {geonames_file}")
    
    print(f"📂 读取GeoNames文件: {geonames_file}")
    
    cities_data = []
    imported_count = 0
    skipped_count = 0
    
    with open(geonames_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 5000 == 0:
                print(f"   处理进度: {line_num} 行...")
            
            # 跳过空行
            line = line.strip()
            if not line:
                continue
            
            # 解析制表符分隔的数据
            fields = line.split('\t')
            if len(fields) < 19:
                skipped_count += 1
                continue
            
            try:
                # GeoNames格式字段：
                # 0: geonameid, 1: name, 2: asciiname, 3: alternatenames
                # 4: latitude, 5: longitude, 6: feature class, 7: feature code
                # 8: country code, 14: population, 17: timezone
                
                geonameid = fields[0]
                name = fields[1].strip()
                alternatenames_str = fields[3].strip() if len(fields) > 3 else ''
                latitude = float(fields[4])
                longitude = float(fields[5])
                country_code = fields[8].strip()
                population_str = fields[14].strip() if len(fields) > 14 else ''
                timezone = fields[17].strip() if len(fields) > 17 else ''
                
                # 跳过无效数据
                if not name or not country_code or country_code not in COUNTRY_CODE_MAP:
                    skipped_count += 1
                    continue
                
                # 优先使用中文名称（从alternatenames中提取）
                # 中文城市名通常是纯中文，不包含英文字母
                chinese_name = None
                if alternatenames_str:
                    alternatenames = alternatenames_str.split(',')
                    # 查找中文名称（包含中文字符且不包含英文字母的名称）
                    chinese_pattern = re.compile(r'^[\u4e00-\u9fff]+.*[\u4e00-\u9fff]*$')
                    for alt_name in alternatenames:
                        alt_name = alt_name.strip()
                        # 检查是否包含中文字符且不包含英文字母
                        if chinese_pattern.match(alt_name) and not re.search(r'[a-zA-Z]', alt_name):
                            chinese_name = alt_name
                            break
                
                # 如果找到中文名称，使用中文名称；否则使用原始名称
                final_name = chinese_name if chinese_name else name
                
                # 解析人口（可能为空）
                population = int(population_str) if population_str else 0
                
                # 获取国家名称
                country = COUNTRY_CODE_MAP.get(country_code, country_code)
                
                # 使用admin1 code作为region（如果有）
                region = fields[10].strip() if len(fields) > 10 and fields[10] else ''
                
                # 准备数据：name, country, country_code, latitude, longitude, population, region, timezone
                cities_data.append((
                    final_name, country, country_code, latitude, longitude, 
                    population, region, timezone
                ))
                
                # 批量插入
                if len(cities_data) >= batch_size:
                    cursor.executemany('''
                        INSERT OR REPLACE INTO cities 
                        (name, country, country_code, latitude, longitude, population, region, timezone)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', cities_data)
                    imported_count += len(cities_data)
                    cities_data = []
                    
            except (ValueError, IndexError) as e:
                skipped_count += 1
                continue
    
    # 插入剩余数据
    if cities_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO cities 
            (name, country, country_code, latitude, longitude, population, region, timezone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', cities_data)
        imported_count += len(cities_data)
    
    print(f"✅ GeoNames数据导入完成: 导入 {imported_count} 个城市, 跳过 {skipped_count} 条记录")
    return imported_count


def init_offline_geocoding_database(db_path: str = None, force: bool = False, from_geonames: bool = False):
    """
    初始化离线地理编码数据库
    
    :param db_path: 数据库文件路径（可选，如果为None则从配置读取）
    :param force: 是否强制重新初始化（删除现有数据）
    :return: 是否成功
    """
    if db_path is None:
        db_path = settings.maps.offline_geocoding_db_path
    
    # 解析路径
    # 对于工具脚本，直接使用项目根目录作为基准
    if Path(db_path).is_absolute():
        db_path_obj = Path(db_path)
    else:
        # 相对路径：工具脚本在 utilities/ 目录，项目根目录是父目录
        db_path_obj = (project_root / db_path).resolve()
    db_path_str = str(db_path_obj)
    
    print(f"📦 开始初始化离线地理编码数据库...")
    print(f"   数据库路径: {db_path_str}")
    
    # 检查数据库是否已存在
    db_exists = db_path_obj.exists()
    if db_exists and not force:
        # 检查数据库中是否已有数据
        try:
            conn = sqlite3.connect(db_path_str)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cities")
            city_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM countries")
            country_count = cursor.fetchone()[0]
            conn.close()
            
            if city_count > 0 and country_count > 0:
                # 如果使用了 --from-geonames，检查数据量是否匹配
                if from_geonames:
                    # GeoNames 数据应该有约3万个城市，如果当前数据量很少，提示更新
                    if city_count < 10000:
                        print(f"⚠️  数据库已存在，但城市数量较少（当前: {city_count}）")
                        print(f"   GeoNames 数据包含约3.2万个城市")
                        print(f"   如需导入 GeoNames 数据，请使用 --force 参数重新初始化：")
                        print(f"   python utilities/init_offline_geocoding_db.py --from-geonames --force")
                        return False
                    else:
                        print(f"✅ 数据库已存在且包含 GeoNames 数据（城市: {city_count}, 国家: {country_count}）")
                        print(f"   如需重新导入，请使用 --force 参数")
                        return True
                else:
                    # 使用内置数据模式
                    print(f"✅ 数据库已存在且包含数据（城市: {city_count}, 国家: {country_count}）")
                    print(f"   如需重新初始化，请使用 --force 参数")
                    return True
        except sqlite3.OperationalError:
            # 表不存在，需要初始化
            pass
    
    try:
        conn = sqlite3.connect(db_path_str)
        cursor = conn.cursor()
        
        # 创建城市表
        print("📋 创建城市表...")
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
        print("📋 创建国家表...")
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
        
        # 如果强制重新初始化，先清空数据
        if force:
            print("🗑️  清空现有数据...")
            cursor.execute("DELETE FROM cities")
            cursor.execute("DELETE FROM countries")
        
        # 根据模式选择数据源
        if from_geonames:
            # 从GeoNames文件导入
            geonames_file = project_root / "utilities" / "cities15000.txt"
            if not geonames_file.exists():
                print(f"❌ GeoNames文件不存在: {geonames_file}")
                print(f"   请确保 cities15000.txt 文件在 utilities 目录中")
                conn.close()
                return False
            
            print("📥 从GeoNames文件导入城市数据...")
            try:
                imported_count = import_from_geonames(str(geonames_file), cursor)
                print(f"   成功导入 {imported_count} 个城市")
            except Exception as e:
                print(f"❌ GeoNames导入失败: {str(e)}")
                import traceback
                traceback.print_exc()
                conn.close()
                return False
        else:
            # 使用内置数据
            print("📥 插入内置城市数据...")
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
            
            cursor.executemany('''
                INSERT OR REPLACE INTO cities (name, country, country_code, latitude, longitude, population, region, timezone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', cities_data)
        
        # 插入国家数据（无论使用哪种模式都插入）
        print("📥 插入国家数据...")
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
        
        # 创建索引以提高查询性能
        print("📊 创建索引...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cities_lat_lng ON cities(latitude, longitude)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cities_country ON cities(country_code)")
            print("   ✅ 索引创建成功")
        except Exception as e:
            print(f"   ⚠️  索引创建失败（可能已存在）: {e}")
        
        conn.commit()
        
        # 验证数据
        cursor.execute("SELECT COUNT(*) FROM cities")
        city_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM countries")
        country_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ 离线地理编码数据库初始化完成！")
        print(f"   城市数量: {city_count}")
        print(f"   国家数量: {country_count}")
        print(f"   数据库路径: {db_path_str}")
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='初始化离线地理编码数据库',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 使用内置数据初始化（约30个城市）
  python utilities/init_offline_geocoding_db.py
  
  # 从GeoNames文件导入（约3.2万个城市）
  python utilities/init_offline_geocoding_db.py --from-geonames
  
  # 强制重新初始化
  python utilities/init_offline_geocoding_db.py --from-geonames --force
        '''
    )
    parser.add_argument('--db-path', type=str, help='数据库文件路径（可选）')
    parser.add_argument('--force', action='store_true', help='强制重新初始化（删除现有数据）')
    parser.add_argument('--from-geonames', action='store_true', 
                       help='从GeoNames文件(cities15000.txt)导入数据（约3.2万个城市）')
    
    args = parser.parse_args()
    
    success = init_offline_geocoding_database(
        db_path=args.db_path, 
        force=args.force,
        from_geonames=args.from_geonames
    )
    
    if success:
        print("\n🎉 初始化成功！现在可以使用离线地理编码服务了。")
        sys.exit(0)
    else:
        print("\n❌ 初始化失败，请检查错误信息。")
        sys.exit(1)


if __name__ == "__main__":
    main()

