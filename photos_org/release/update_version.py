#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本号更新脚本

在打包时自动更新 config.json 和 config_default.json 中的 app_version 字段
格式：YYYYMMDD_HH（例如：20251113_01）
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def update_version():
    """更新配置文件中的版本号"""
    # 获取当前日期时间，格式：YYYYMMDD_HH
    current_version = datetime.now().strftime('%Y%m%d_%H')
    
    # 获取项目根目录（脚本在 release/ 目录下，需要回到上一级）
    project_root = Path(__file__).parent.parent
    
    # 更新 config.json
    config_path = project_root / 'config.json'
    if config_path.exists():
        print(f'Updating {config_path}...')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['app_version'] = current_version
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f'✓ {config_path} version updated to {current_version}')
    else:
        print(f'⚠ Warning: {config_path} not found')
        return False
    
    # 更新 config_default.json
    config_default_path = project_root / 'config_default.json'
    if config_default_path.exists():
        print(f'Updating {config_default_path}...')
        with open(config_default_path, 'r', encoding='utf-8') as f:
            config_default = json.load(f)
        config_default['app_version'] = current_version
        with open(config_default_path, 'w', encoding='utf-8') as f:
            json.dump(config_default, f, ensure_ascii=False, indent=2)
        print(f'✓ {config_default_path} version updated to {current_version}')
    else:
        print(f'⚠ Warning: {config_default_path} not found')
        return False
    
    print(f'\n✓ All version numbers updated to {current_version}')
    return True

if __name__ == '__main__':
    try:
        success = update_version()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f'✗ Error: {e}')
        sys.exit(1)

