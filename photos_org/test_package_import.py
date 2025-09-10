#!/usr/bin/env python3
"""
测试Python包导入功能
"""
import os
import sys
import subprocess

def test_import_in_directory(test_dir, description):
    """在指定目录测试导入"""
    print(f"\n[*] 测试{description}:")

    if not os.path.exists(test_dir):
        print(f"[!] 目录 {test_dir} 不存在")
        return

    try:
        # 切换到测试目录
        original_cwd = os.getcwd()
        os.chdir(test_dir)

        # 测试导入
        result = subprocess.run([
            sys.executable, '-c',
            'from app.services.search_service import SearchService; print("SUCCESS: import ok")'
        ], capture_output=True, text=True, timeout=10, encoding='utf-8')

        os.chdir(original_cwd)  # 恢复原始目录

        if result.returncode == 0:
            print(f"[OK] {test_dir}: 导入成功")
        else:
            print(f"[FAIL] {test_dir}: 导入失败")
            if result.stderr:
                print(f"   错误: {result.stderr.strip()}")

    except Exception as e:
        os.chdir(original_cwd) if 'original_cwd' in locals() else None
        print(f"[ERROR] {test_dir}: 测试异常 - {e}")

def main():
    """主测试函数"""
    print(">>> Python包导入测试")
    print("=" * 50)

    # 测试根目录
    test_import_in_directory('.', '根目录')

    # 测试各个子目录
    test_dirs = [
        ('app', 'app目录'),
        ('app/services', 'services目录'),
        ('app/models', 'models目录'),
        ('app/api', 'api目录'),
    ]

    for test_dir, description in test_dirs:
        test_import_in_directory(test_dir, description)

    print("\n>>> Python包导入测试完成！")

if __name__ == "__main__":
    main()
