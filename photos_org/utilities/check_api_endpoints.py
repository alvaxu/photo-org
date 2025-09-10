#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API端点检查脚本
"""

import requests
import json

def check_api_endpoints():
    """检查所有API端点"""
    print('=== 检查API端点 ===\n')

    endpoints = [
        ('API根路径', 'http://localhost:8000/api/v1/'),
        ('健康检查', 'http://localhost:8000/api/v1/health/'),
        ('照片API', 'http://localhost:8000/api/v1/photos/'),
        ('搜索API根', 'http://localhost:8000/api/v1/search/'),
        ('搜索统计', 'http://localhost:8000/api/v1/search/stats'),
        ('搜索照片', 'http://localhost:8000/api/v1/search/photos?limit=1'),
        ('导入API', 'http://localhost:8000/api/v1/import/'),
        ('分析API', 'http://localhost:8000/api/v1/analysis/'),
        ('标签API', 'http://localhost:8000/api/v1/tags/'),
        ('分类API', 'http://localhost:8000/api/v1/categories/'),
    ]

    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            
            if status == 200:
                print(f'✅ {name}: {status}')
                if 'photos' in url and 'search' not in url:
                    try:
                        data = response.json()
                        total = data.get('total', 0)
                        print(f'   📊 照片数量: {total}')
                    except:
                        pass
            elif status == 404:
                print(f'❌ {name}: {status} (未找到)')
            elif status == 307:
                print(f'🔄 {name}: {status} (重定向)')
            else:
                print(f'⚠️  {name}: {status}')
                
        except Exception as e:
            print(f'❌ {name}: 连接失败 - {e}')

    print('\n=== 检查静态文件 ===\n')
    
    static_files = [
        ('HTML文件', 'http://localhost:8000/static/index.html'),
        ('CSS文件', 'http://localhost:8000/static/css/style.css'),
        ('JS文件1', 'http://localhost:8000/static/js/app.js'),
        ('JS文件2', 'http://localhost:8000/static/js/photo-manager.js'),
        ('JS文件3', 'http://localhost:8000/static/js/ui-components.js'),
        ('Favicon', 'http://localhost:8000/static/images/favicon.ico'),
    ]

    for name, url in static_files:
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            
            if status == 200:
                print(f'✅ {name}: {status}')
            elif status == 304:
                print(f'✅ {name}: {status} (缓存)')
            else:
                print(f'❌ {name}: {status}')
                
        except Exception as e:
            print(f'❌ {name}: 连接失败 - {e}')

    print('\n=== 检查完成 ===')

if __name__ == '__main__':
    check_api_endpoints()


