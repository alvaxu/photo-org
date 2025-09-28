#!/usr/bin/env python3
"""
节假日标签补充工具

为数据库中缺少节假日标签的照片补充节假日标签。
处理所有在chinese_calendar有效范围内（2004-2025年）的照片。
"""

import sqlite3
import json
import time
from datetime import datetime, date
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

class HolidayTagUpdater:
    """节假日标签补充工具"""

    def __init__(self, db_path: str, batch_size: int = 500):
        self.db_path = db_path
        self.batch_size = batch_size
        self.conn = None
        self.cursor = None

        # 节假日映射表 - 直接使用chinese_calendar库的原生中文名称
        self.holiday_map = {}
        try:
            import chinese_calendar as cc
            # 构建英文到中文的映射
            for holiday in cc.constants.Holiday:
                if holiday.name == 'new_years_day':
                    self.holiday_map["New Year's Day"] = holiday.chinese
                elif holiday.name == 'spring_festival':
                    self.holiday_map['Spring Festival'] = holiday.chinese
                elif holiday.name == 'tomb_sweeping_day':
                    self.holiday_map['Tomb-sweeping Day'] = holiday.chinese
                elif holiday.name == 'labour_day':
                    self.holiday_map['Labour Day'] = holiday.chinese
                elif holiday.name == 'dragon_boat_festival':
                    self.holiday_map['Dragon Boat Festival'] = holiday.chinese
                elif holiday.name == 'mid_autumn_festival':
                    self.holiday_map['Mid-autumn Festival'] = holiday.chinese
                elif holiday.name == 'national_day':
                    self.holiday_map['National Day'] = holiday.chinese
                elif holiday.name == 'anti_fascist_70th_day':
                    self.holiday_map['Anti-Fascist 70th Day'] = holiday.chinese
        except ImportError:
            print("❌ chinese_calendar库未安装，无法获取节假日映射")
            # 备用映射表
            self.holiday_map = {
                'New Year\'s Day': '元旦',
                'Spring Festival': '春节',
                'Tomb-sweeping Day': '清明',
                'Labour Day': '劳动节',
                'Dragon Boat Festival': '端午',
                'Mid-autumn Festival': '中秋',
                'National Day': '国庆节',
                'Anti-Fascist 70th Day': '中国人民抗日战争暨世界反法西斯战争胜利70周年纪念日'
            }

        # 统计信息
        self.stats = {
            'total_processed': 0,
            'tags_added': 0,
            'skipped_out_of_range': 0,
            'skipped_already_have': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    def connect_db(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"✅ 已连接数据库: {self.db_path}")

    def close_db(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("✅ 已关闭数据库连接")

    def is_date_in_range(self, taken_at_str: str) -> bool:
        """检查日期是否在chinese_calendar支持范围内"""
        try:
            # 解析日期字符串
            if taken_at_str.endswith('Z'):
                taken_at_str = taken_at_str[:-1] + '+00:00'
            taken_at = datetime.fromisoformat(taken_at_str.replace('Z', '+00:00'))
            return 2004 <= taken_at.year <= 2025
        except Exception:
            return False

    def detect_holiday(self, taken_at_str: str) -> Optional[str]:
        """检测节假日"""
        try:
            import chinese_calendar as cc

            # 解析日期
            if taken_at_str.endswith('Z'):
                taken_at_str = taken_at_str[:-1] + '+00:00'
            taken_at = datetime.fromisoformat(taken_at_str.replace('Z', '+00:00'))
            photo_date = taken_at.date()

            # 检查是否为节假日
            if cc.is_holiday(photo_date):
                holiday_detail = cc.get_holiday_detail(photo_date)
                if len(holiday_detail) >= 2:
                    holiday_name_en = holiday_detail[1]
                    return self.holiday_map.get(holiday_name_en)

        except ImportError:
            print("❌ chinese_calendar库未安装")
        except Exception as e:
            print(f"❌ 节假日检测出错: {e}")

        return None

    def get_or_create_tag(self, tag_name: str) -> int:
        """获取或创建标签，返回标签ID"""
        # 检查标签是否已存在
        self.cursor.execute("""
            SELECT id FROM tags
            WHERE name = ? AND category = 'time'
        """, (tag_name,))

        result = self.cursor.fetchone()
        if result:
            return result[0]

        # 创建新标签
        self.cursor.execute("""
            INSERT INTO tags (name, category, usage_count, created_at, updated_at)
            VALUES (?, 'time', 0, ?, ?)
        """, (tag_name, datetime.now().isoformat(), datetime.now().isoformat()))

        return self.cursor.lastrowid

    def tag_exists_for_photo(self, photo_id: int, tag_id: int) -> bool:
        """检查照片是否已有该标签"""
        self.cursor.execute("""
            SELECT id FROM photo_tags
            WHERE photo_id = ? AND tag_id = ?
        """, (photo_id, tag_id))

        return self.cursor.fetchone() is not None

    def add_holiday_tag_to_photo(self, photo_id: int, holiday_name: str):
        """为照片添加节假日标签"""
        try:
            # 获取或创建标签
            tag_id = self.get_or_create_tag(holiday_name)

            # 检查是否已存在关联
            if self.tag_exists_for_photo(photo_id, tag_id):
                return False

            # 添加关联
            self.cursor.execute("""
                INSERT INTO photo_tags (photo_id, tag_id, source, created_at, updated_at)
                VALUES (?, ?, 'holiday_update', ?, ?)
            """, (photo_id, tag_id, datetime.now().isoformat(), datetime.now().isoformat()))

            # 更新标签使用计数
            self.cursor.execute("""
                UPDATE tags SET usage_count = usage_count + 1, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), tag_id))

            return True

        except Exception as e:
            print(f"❌ 添加标签失败 photo_id={photo_id}, holiday={holiday_name}: {e}")
            return False

    def get_photos_to_process(self, offset: int = 0) -> List[Tuple]:
        """获取需要处理的照片"""
        self.cursor.execute("""
            SELECT id, taken_at, filename
            FROM photos
            WHERE taken_at IS NOT NULL
              AND status != 'analyzing'  -- 排除正在分析的照片
            ORDER BY taken_at DESC
            LIMIT ? OFFSET ?
        """, (self.batch_size, offset))

        return self.cursor.fetchall()

    def process_batch(self, photos: List[Tuple]) -> Dict[str, int]:
        """处理一批照片"""
        batch_stats = {
            'processed': 0,
            'tags_added': 0,
            'skipped_out_of_range': 0,
            'skipped_already_have': 0,
            'errors': 0
        }

        for photo_id, taken_at, filename in photos:
            batch_stats['processed'] += 1
            self.stats['total_processed'] += 1

            try:
                # 检查日期范围
                if not self.is_date_in_range(taken_at):
                    batch_stats['skipped_out_of_range'] += 1
                    self.stats['skipped_out_of_range'] += 1
                    continue

                # 检测节假日
                holiday_name = self.detect_holiday(taken_at)
                if not holiday_name:
                    # 不是节假日，跳过
                    continue

                # 检查是否已有任何节假日标签
                self.cursor.execute("""
                    SELECT COUNT(*) FROM photo_tags pt
                    JOIN tags t ON pt.tag_id = t.id
                    WHERE pt.photo_id = ? AND t.category = 'time'
                      AND (t.name LIKE '%节%' OR t.name LIKE '%旦%' OR
                           t.name IN ('情人节', '愚人节', '圣诞节', '妇女节', '儿童节'))
                """, (photo_id,))

                if self.cursor.fetchone()[0] > 0:
                    batch_stats['skipped_already_have'] += 1
                    self.stats['skipped_already_have'] += 1
                    continue

                # 添加节假日标签
                if self.add_holiday_tag_to_photo(photo_id, holiday_name):
                    batch_stats['tags_added'] += 1
                    self.stats['tags_added'] += 1
                    print(f"✅ 为照片 {filename[:30]}... 添加节假日标签: {holiday_name}")
                else:
                    batch_stats['errors'] += 1
                    self.stats['errors'] += 1

            except Exception as e:
                print(f"❌ 处理照片失败 {filename[:30]}...: {e}")
                batch_stats['errors'] += 1
                self.stats['errors'] += 1

        return batch_stats

    def get_total_count(self) -> int:
        """获取需要处理的照片总数"""
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM photos
            WHERE taken_at IS NOT NULL
              AND status != 'analyzing'
        """)
        return self.cursor.fetchone()[0]

    def scan_and_report(self) -> Dict[str, Any]:
        """扫描并生成报告"""
        print("\n=== 节假日标签补充工具 - 扫描模式 ===\n")

        total_count = self.get_total_count()
        print(f"需要处理的照片总数: {total_count}")

        # 统计各年份分布
        self.cursor.execute("""
            SELECT strftime('%Y', taken_at) as year, COUNT(*) as count
            FROM photos
            WHERE taken_at IS NOT NULL AND status != 'analyzing'
            GROUP BY year
            ORDER BY year
        """)

        year_dist = self.cursor.fetchall()
        print("\n各年份照片分布:")
        in_range_count = 0
        for year, count in year_dist:
            year_int = int(year)
            if 2004 <= year_int <= 2025:
                status = "✅ 在范围内"
                in_range_count += count
            else:
                status = "❌ 超出范围"
            print(f"  {year}年: {count}张照片 {status}")

        print(f"\n在chinese_calendar有效范围内的照片: {in_range_count}")

        # 估算节假日照片数量（粗略估计）
        holiday_estimate = int(in_range_count * 0.05)  # 假设5%的照片是节假日照片
        print(f"预估需要补充节假日标签的照片: {holiday_estimate}")

        return {
            'total_photos': total_count,
            'in_range_photos': in_range_count,
            'estimated_holidays': holiday_estimate,
            'year_distribution': year_dist
        }

    def run_update(self) -> Dict[str, Any]:
        """执行节假日标签补充"""
        print("\n=== 节假日标签补充工具 - 更新模式 ===\n")

        self.stats['start_time'] = time.time()

        try:
            total_count = self.get_total_count()
            processed_count = 0
            batch_num = 0

            print(f"开始处理 {total_count} 张照片...")
            print(f"批量大小: {self.batch_size}")
            print("-" * 60)

            while processed_count < total_count:
                batch_num += 1
                photos = self.get_photos_to_process(processed_count)

                if not photos:
                    break

                print(f"\n处理第 {batch_num} 批 ({len(photos)} 张照片)...")

                batch_stats = self.process_batch(photos)
                processed_count += len(photos)

                # 显示批次统计
                progress = (processed_count / total_count) * 100
                print(f"进度: {progress:.1f}% - "
                      f"添加标签: {batch_stats['tags_added']}, "
                      f"超出范围: {batch_stats['skipped_out_of_range']}, "
                      f"已有标签: {batch_stats['skipped_already_have']}, "
                      f"错误: {batch_stats['errors']}")

                # 提交事务
                self.conn.commit()

                # 检查是否真的处理完了所有照片
                if processed_count >= total_count:
                    print("已处理完所有照片")
                    break

            self.stats['end_time'] = time.time()
            duration = self.stats['end_time'] - self.stats['start_time']

            print("\n" + "="*60)
            print("处理完成！")
            print(f"总处理照片: {self.stats['total_processed']}")
            print(f"添加节假日标签: {self.stats['tags_added']}")
            print(f"超出日期范围: {self.stats['skipped_out_of_range']}")
            print(f"已有节假日标签: {self.stats['skipped_already_have']}")
            print(f"处理错误: {self.stats['errors']}")
            print(f"总耗时: {duration:.1f}秒")
            return self.stats

        except Exception as e:
            print(f"❌ 处理过程中出错: {e}")
            self.conn.rollback()
            raise

    def run(self, mode: str = 'scan'):
        """运行工具"""
        try:
            self.connect_db()

            if mode == 'scan':
                return self.scan_and_report()
            elif mode == 'update':
                return self.run_update()
            else:
                print("❌ 无效模式，请使用 'scan' 或 'update'")

        finally:
            self.close_db()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='节假日标签补充工具')
    parser.add_argument('--mode', choices=['scan', 'update'],
                       default='scan', help='运行模式：scan(扫描) 或 update(更新)')
    parser.add_argument('--db-path', help='数据库路径（可选，默认从config.json读取）')
    parser.add_argument('--batch-size', type=int, default=500,
                       help='批量处理大小（默认500）')

    args = parser.parse_args()

    # 获取数据库路径
    if args.db_path:
        db_path = args.db_path
    else:
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            db_path = config['database']['path']
        except Exception as e:
            print(f"❌ 无法读取数据库路径: {e}")
            return

    # 检查数据库文件
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return

    # 运行工具
    updater = HolidayTagUpdater(db_path, args.batch_size)
    result = updater.run(args.mode)

    if args.mode == 'scan':
        print("\n扫描完成！建议运行更新命令补充节假日标签。")
    elif args.mode == 'update':
        print("\n更新完成！节假日标签已补充。")

if __name__ == "__main__":
    main()
