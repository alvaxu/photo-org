#!/usr/bin/env python3
"""
家庭版智能照片系统 - 完整系统测试脚本
测试Python包导入、数据库连接、API服务、前端界面等所有组件
"""
import sys
import os
import subprocess
import requests
import time
from pathlib import Path
import webbrowser

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def test_python_package():
    """测试Python包导入"""
    print_header("测试Python包导入")

    test_imports = [
        ("app", "from app.core.config import settings"),
        ("app.models", "from app.models.photo import Photo"),
        ("app.services", "from app.services.search_service import SearchService"),
        ("app.api", "from app.api.search import router"),
        ("app.db", "from app.db.session import get_db")
    ]

    success_count = 0
    for module_name, import_statement in test_imports:
        try:
            exec(import_statement)
            print(f"✅ {module_name}: 导入成功")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}: 导入失败 - {e}")

    print(f"\n📊 Python包导入测试: {success_count}/{len(test_imports)} 成功")

    return success_count == len(test_imports)

def test_database_connection():
    """测试数据库连接"""
    print_header("测试数据库连接")

    try:
        from app.db.session import get_db
        from app.models.photo import Photo
        from app.core.config import settings

        db = next(get_db())

        # 测试基本查询
        photo_count = db.query(Photo).count()
        print(f"✅ 数据库连接成功")
        print(f"📸 当前照片数量: {photo_count}")

        # 显示数据库信息
        print(f"🔧 数据库路径: {settings.database.path}")
        print(f"🖼️ 存储路径: {settings.storage.base_path}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点"""
    print_header("测试API端点")

    # API端点测试列表
    endpoints = [
        ("GET", "/search/stats", "搜索统计"),
        ("GET", "/search/photos?limit=1", "照片列表"),
        ("GET", "/search/suggestions?prefix=测试", "搜索建议")
    ]

    success_count = 0

    for method, endpoint, description in endpoints:
        try:
            url = f"http://localhost:8000{endpoint}"
            response = requests.request(method, url, timeout=5)

            if response.status_code == 200:
                print(f"✅ {description}: {response.status_code}")
                success_count += 1
            else:
                print(f"⚠️ {description}: {response.status_code} - {response.text[:100]}")

        except requests.exceptions.ConnectionError:
            print(f"❌ {description}: API服务未启动")
            break
        except Exception as e:
            print(f"❌ {description}: 错误 - {e}")

    if success_count == 0:
        print("\n💡 提示: 请先启动FastAPI服务")
        print("   运行: python main.py")
        return False

    print(f"\n📊 API端点测试: {success_count}/{len(endpoints)} 成功")
    return success_count > 0

def test_frontend_files():
    """测试前端文件是否存在"""
    print_header("测试前端文件")

    frontend_files = [
        "static/index.html",
        "static/css/style.css",
        "static/js/app.js",
        "static/js/photo-manager.js",
        "static/js/ui-components.js"
    ]

    success_count = 0
    for file_path in frontend_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ {file_path}: 存在 ({file_size} bytes)")
            success_count += 1
        else:
            print(f"❌ {file_path}: 文件不存在")

    print(f"\n📊 前端文件测试: {success_count}/{len(frontend_files)} 存在")
    return success_count == len(frontend_files)

def test_search_functionality():
    """测试搜索功能"""
    print_header("测试搜索功能")

    try:
        from app.db.session import get_db
        from app.services.search_service import SearchService

        db = next(get_db())
        search_service = SearchService()

        # 测试统计功能
        stats = search_service.get_search_stats(db)
        print("✅ 搜索统计功能正常")
        print(f"   📊 数据统计: 照片{stats.get('total_photos', 0)}张, 标签{stats.get('total_tags', 0)}个")

        # 测试搜索建议
        suggestions = search_service.get_search_suggestions(db, "测试")
        print("✅ 搜索建议功能正常")
        print(f"   💡 建议数量: {sum(len(items) for items in suggestions.values())}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ 搜索功能测试失败: {e}")
        return False

def start_api_server():
    """启动API服务器（用于测试）"""
    print_header("启动API服务器")

    try:
        print("🚀 正在启动FastAPI服务器...")

        # 在后台启动服务器
        server_process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 等待服务器启动
        time.sleep(3)

        # 检查服务器是否启动成功
        try:
            response = requests.get("http://localhost:8000/docs", timeout=5)
            if response.status_code == 200:
                print("✅ API服务器启动成功")
                print("📖 Swagger文档: http://localhost:8000/docs")
                return server_process
        except:
            pass

        print("❌ API服务器启动失败")
        server_process.terminate()
        return None

    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        return None

def open_frontend():
    """打开前端界面"""
    print_header("打开前端界面")

    frontend_path = "static/index.html"
    if os.path.exists(frontend_path):
        try:
            # 转换为绝对路径并用file://协议
            abs_path = os.path.abspath(frontend_path)
            url = f"file://{abs_path}"

            print(f"🌐 正在打开前端界面: {url}")
            webbrowser.open(url)
            print("✅ 前端界面已打开")
            return True
        except Exception as e:
            print(f"❌ 打开前端界面失败: {e}")
            return False
    else:
        print("❌ 前端文件不存在")
        return False

def run_integration_test():
    """运行集成测试"""
    print_header("集成测试")

    # 测试完整的数据流
    try:
        from app.db.session import get_db
        from app.models.photo import Photo, PhotoAnalysis, PhotoQuality
        from app.services.search_service import SearchService

        db = next(get_db())

        # 1. 检查数据完整性
        photo_count = db.query(Photo).count()
        analysis_count = db.query(PhotoAnalysis).count()
        quality_count = db.query(PhotoQuality).count()

        print("📊 数据完整性检查:")
        print(f"   📸 照片: {photo_count}")
        print(f"   🤖 AI分析: {analysis_count}")
        print(f"   ⭐ 质量评估: {quality_count}")

        # 2. 测试搜索服务
        search_service = SearchService()
        results, total = search_service.search_photos(db, limit=5)

        print(f"🔍 搜索服务测试: 找到 {total} 张照片")

        # 3. 检查关联数据
        if photo_count > 0:
            sample_photo = db.query(Photo).first()
            analysis = db.query(PhotoAnalysis).filter(
                PhotoAnalysis.photo_id == sample_photo.id
            ).first()

            quality = db.query(PhotoQuality).filter(
                PhotoQuality.photo_id == sample_photo.id
            ).first()

            print("🔗 数据关联检查:")
            print(f"   📝 分析结果: {'✅' if analysis else '❌'}")
            print(f"   ⭐ 质量评估: {'✅' if quality else '❌'}")

        db.close()

        print("✅ 集成测试通过")
        return True

    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🏠 家庭版智能照片系统 - 系统测试")
    print("="*80)

    # 测试结果统计
    test_results = {}

    # 1. 测试Python包导入
    test_results['python_package'] = test_python_package()

    # 2. 测试数据库连接
    test_results['database'] = test_database_connection()

    # 3. 测试前端文件
    test_results['frontend'] = test_frontend_files()

    # 4. 测试搜索功能
    test_results['search'] = test_search_functionality()

    # 5. 运行集成测试
    test_results['integration'] = run_integration_test()

    # 6. 测试API端点
    test_results['api'] = test_api_endpoints()

    # 汇总测试结果
    print_header("测试结果汇总")

    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)

    print(f"📊 总体测试结果: {passed_tests}/{total_tests} 通过")

    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        test_display_name = {
            'python_package': 'Python包导入',
            'database': '数据库连接',
            'frontend': '前端文件',
            'search': '搜索功能',
            'integration': '集成测试',
            'api': 'API端点'
        }.get(test_name, test_name)

        print(f"   {status} {test_display_name}")

    # 根据测试结果给出建议
    print("\n" + "="*60)
    if passed_tests == total_tests:
        print("🎉 所有测试都通过了！系统运行正常")
        print("\n💡 建议操作:")
        print("   1. 启动API服务器: python main.py")
        print("   2. 打开前端界面: static/index.html")
        print("   3. 开始使用照片功能")

        # 自动启动服务器和打开前端
        server_process = start_api_server()
        if server_process:
            time.sleep(2)  # 等待服务器完全启动
            open_frontend()

    else:
        failed_tests = [name for name, result in test_results.items() if not result]
        print(f"⚠️ 有 {len(failed_tests)} 个测试失败: {', '.join(failed_tests)}")

        print("\n🔧 故障排除建议:")
        if not test_results['python_package']:
            print("   • 检查Python包是否正确安装: pip install -e .")
        if not test_results['database']:
            print("   • 检查数据库文件是否存在")
        if not test_results['frontend']:
            print("   • 检查前端文件是否完整")
        if not test_results['api']:
            print("   • 启动API服务器: python main.py")

if __name__ == "__main__":
    main()
