#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# 测试智能分析API
base_url = "http://127.0.0.1:8000/api/v1/analysis"

def test_analysis_status():
    """测试分析状态查询"""
    url = f"{base_url}/status/1"
    response = requests.get(url)
    print(f"分析状态查询: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"分析状态: {data}")
    else:
        print(f"错误: {response.json()}")

def test_queue_status():
    """测试队列状态查询"""
    url = f"{base_url}/queue/status"
    response = requests.get(url)
    print(f"\n队列状态查询: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"队列状态: {data}")
    else:
        print(f"错误: {response.json()}")

def test_caption_generation():
    """测试标题生成"""
    url = f"{base_url}/caption"
    data = {
        "photo_id": 1,
        "style": "natural"
    }

    response = requests.post(url, json=data)
    print(f"\n标题生成: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"标题生成结果: {result}")
    else:
        print(f"错误: {response.json()}")

def test_duplicate_detection():
    """测试重复检测"""
    url = f"{base_url}/duplicates/1"
    response = requests.get(url)
    print(f"\n重复检测: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"重复检测结果: {result}")
    else:
        print(f"错误: {response.json()}")

if __name__ == "__main__":
    print("=== 测试智能分析模块 ===")

    # 测试各个API
    test_analysis_status()
    test_queue_status()
    test_caption_generation()
    test_duplicate_detection()

    print("\n=== 测试完成 ===")
