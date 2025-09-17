#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统诊断脚本
用于诊断家庭版智能照片系统的运行状态
"""

import requests
import json

def diagnose_system():
    """诊断系统运行状态"""
    print('=== 家庭版智能照片系统 - 运行诊断 ===\n')

    issues = []

    # 1. 检查基础健康状态
    print('1. 检查服务器健康状态...')
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print('✅ 基础健康检查: 正常')
        else:
            print(f'❌ 基础健康检查: 状态码 {response.status_code}')
            issues.append('基础健康检查失败')
    except Exception as e:
        print(f'❌ 基础健康检查失败: {e}')
        issues.append('无法连接到服务器')

    # 2. 检查API健康状态
    print('\n2. 检查API健康状态...')
    try:
        response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
        if response.status_code == 200:
            print('✅ API健康检查: 正常')
        else:
            print(f'❌ API健康检查: 状态码 {response.status_code}')
            issues.append('API健康检查失败')
    except Exception as e:
        print(f'❌ API健康检查失败: {e}')
        issues.append('API连接失败')

    # 3. 检查搜索统计API
    print('\n3. 检查搜索统计API...')
    try:
        response = requests.get('http://localhost:8000/api/v1/search/stats', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data['data']
                total_photos = stats.get('total_photos', 0)
                total_tags = stats.get('total_tags', 0)
                total_categories = stats.get('total_categories', 0)
                print(f'✅ 搜索统计API正常: {total_photos}张照片, {total_tags}个标签, {total_categories}个分类')
            else:
                print(f'❌ 搜索统计API返回错误: {data}')
                issues.append('搜索统计API数据错误')
        else:
            print(f'❌ 搜索统计API状态码: {response.status_code}')
            issues.append('搜索统计API不可用')
    except Exception as e:
        print(f'❌ 搜索统计API失败: {e}')
        issues.append('搜索统计API连接失败')

    # 4. 检查搜索照片API
    print('\n4. 检查搜索照片API...')
    try:
        response = requests.get('http://localhost:8000/api/v1/search/photos?limit=5', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                photos = data.get('data', [])
                total = data.get('total', 0)
                print(f'✅ 搜索照片API正常: 返回{len(photos)}/{total}张照片')
            else:
                print(f'❌ 搜索照片API返回错误: {data}')
                issues.append('搜索照片API数据错误')
        else:
            print(f'❌ 搜索照片API状态码: {response.status_code}')
            issues.append('搜索照片API不可用')
    except Exception as e:
        print(f'❌ 搜索照片API失败: {e}')
        issues.append('搜索照片API连接失败')

    # 5. 检查静态文件
    print('\n5. 检查静态文件访问...')
    static_files = [
        ('HTML', '/index.html'),
        ('CSS', '/css/style.css'),
        ('JS', '/js/app.js'),
        ('JS', '/js/photo-manager.js'),
        ('JS', '/js/ui-components.js'),
        ('Favicon', '/images/favicon.ico')
    ]

    for name, path in static_files:
        try:
            response = requests.get(f'http://localhost:8000{path}', timeout=5)
            if response.status_code in [200, 304]:
                print(f'✅ {name}文件正常: {path}')
            else:
                print(f'❌ {name}文件错误: {path} (状态码: {response.status_code})')
                issues.append(f'{name}文件访问失败')
        except Exception as e:
            print(f'❌ {name}文件访问失败: {path} ({e})')
            issues.append(f'{name}文件访问失败')

    # 6. 总结诊断结果
    print('\n' + '='*50)
    if issues:
        print(f'❌ 发现 {len(issues)} 个问题:')
        for i, issue in enumerate(issues, 1):
            print(f'   {i}. {issue}')
        print('\n🔧 请根据上述问题进行修复')
    else:
        print('🎉 所有诊断项目正常通过！')
        print('🌐 您可以访问以下地址:')
        print('   - 前端界面: http://localhost:8000/index.html')
        print('   - API文档: http://localhost:8000/docs')

    print('='*50)

if __name__ == '__main__':
    diagnose_system()


