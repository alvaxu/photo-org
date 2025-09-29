#!/usr/bin/env python3
"""
程序说明：

## 1. 相似照片搜索性能测试工具
## 2. 验证第一层优化效果
## 3. 对比优化前后的性能差异
"""

import time
from datetime import datetime
from app.db.session import get_db
from app.services.enhanced_similarity_service import EnhancedSimilarityService
from app.models.photo import Photo


def test_similarity_performance():
    """测试相似照片搜索性能"""
    print("🔍 相似照片搜索性能测试")
    print("=" * 60)

    db = next(get_db())
    service = EnhancedSimilarityService()

    try:
        # 1. 获取测试照片
        print("📸 获取测试照片...")
        test_photos = db.query(Photo).filter(
            Photo.perceptual_hash.isnot(None),
            Photo.status.in_(['imported', 'quality_completed', 'content_completed', 'completed'])
        ).limit(10).all()  # 测试前10张照片

        if not test_photos:
            print("❌ 没有找到合适的测试照片")
            return

        print(f"✅ 找到 {len(test_photos)} 张测试照片")

        # 2. 测试单张照片的相似搜索性能
        print("\n⚡ 测试单张照片相似搜索性能...")

        total_time = 0
        results_count = 0

        for i, photo in enumerate(test_photos):
            print(f"\n  测试照片 {i+1}/{len(test_photos)}: {photo.filename}")

            start_time = time.time()
            try:
                # 调用第一层相似搜索
                similar_photos = service.find_first_layer_similar_photos(
                    db_session=db,
                    reference_photo_id=photo.id,
                    threshold=0.5,
                    limit=8
                )

                end_time = time.time()
                duration = end_time - start_time

                print(".4f"                print(f"    📊 返回相似照片: {len(similar_photos)} 张")

                total_time += duration
                results_count += 1

                # 显示前3个结果的相似度
                if similar_photos:
                    print("    🏆 Top相似度:")
                    for j, result in enumerate(similar_photos[:3]):
                        print(".3f")

            except Exception as e:
                print(f"    ❌ 测试失败: {str(e)}")

        # 3. 计算平均性能
        if results_count > 0:
            avg_time = total_time / results_count
            print("
📊 性能统计:"            print(".4f"            print(".1f"            print(".4f"
        # 4. 测试预筛选效果
        print("\n🎯 测试预筛选效果...")
        test_pre_screening(db, service, test_photos[0])

        # 5. 对比不同阈值的性能
        print("\n⚖️ 测试不同相似度阈值的影响...")
        test_threshold_performance(db, service, test_photos[0])

    except Exception as e:
        print(f"❌ 性能测试失败: {str(e)}")
    finally:
        db.close()


def test_pre_screening(db, service, reference_photo):
    """测试预筛选的效果"""
    try:
        # 获取预筛选前的总数
        total_photos = db.query(Photo).filter(
            Photo.id != reference_photo.id,
            Photo.perceptual_hash.isnot(None)
        ).count()

        # 获取预筛选后的数量
        pre_screened = service._pre_screen_candidates(db, reference_photo)

        reduction_ratio = (1 - len(pre_screened) / total_photos) * 100 if total_photos > 0 else 0

        print(f"  📊 预筛选统计:")
        print(f"    总数: {total_photos} 张")
        print(f"    预筛选后: {len(pre_screened)} 张")
        print(".1f"
        # 显示预筛选条件
        conditions = []
        if reference_photo.taken_at:
            conditions.append(f"时间范围: ±30天")
        if reference_photo.location_lat and reference_photo.location_lng:
            conditions.append(f"位置范围: ±0.1度")
        if not conditions:
            conditions.append("感知哈希存在")

        print(f"    🎛️ 筛选条件: {' + '.join(conditions)}")

    except Exception as e:
        print(f"  ❌ 预筛选测试失败: {str(e)}")


def test_threshold_performance(db, service, reference_photo):
    """测试不同相似度阈值对性能的影响"""
    thresholds = [0.3, 0.5, 0.7, 0.8]

    print("  📊 阈值性能对比:")

    for threshold in thresholds:
        try:
            start_time = time.time()
            results = service.find_first_layer_similar_photos(
                db_session=db,
                reference_photo_id=reference_photo.id,
                threshold=threshold,
                limit=20
            )
            end_time = time.time()

            duration = end_time - start_time
            print(".4f"
        except Exception as e:
            print(f"    ❌ 阈值 {threshold} 测试失败: {str(e)}")


def benchmark_against_old_method(db, service, reference_photo):
    """对比新旧方法的性能"""
    print("\n🔄 对比新旧方法性能...")

    try:
        # 模拟旧方法：直接遍历所有照片
        print("  📊 旧方法测试...")

        all_photos = db.query(Photo).filter(
            Photo.id != reference_photo.id,
            Photo.perceptual_hash.isnot(None)
        ).all()

        start_time = time.time()
        old_method_count = 0

        for photo in all_photos[:100]:  # 限制测试数量
            try:
                # 只计算感知哈希相似度（模拟旧方法的核心逻辑）
                if reference_photo.perceptual_hash and photo.perceptual_hash:
                    service.calculate_perceptual_hash_similarity(reference_photo, photo)
                    old_method_count += 1
            except:
                pass

        old_time = time.time() - start_time

        # 新方法测试
        print("  📊 新方法测试...")

        start_time = time.time()
        new_results = service.find_first_layer_similar_photos(
            db_session=db,
            reference_photo_id=reference_photo.id,
            threshold=0.5,
            limit=20
        )
        new_time = time.time() - start_time

        # 计算性能提升
        if old_time > 0 and new_time > 0:
            speedup = old_time / new_time
            print("
🎯 性能对比:"            print(".4f"            print(".4f"            print(".2f"
    except Exception as e:
        print(f"  ❌ 方法对比失败: {str(e)}")


if __name__ == "__main__":
    print("家庭版智能照片系统 - 相似照片搜索性能测试")
    print("=" * 60)

    test_similarity_performance()

    print("\n🎯 性能测试完成！")
    print("基于测试结果可以评估相似照片搜索的优化效果。")
