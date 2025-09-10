#!/usr/bin/env python3
"""
家庭单机版智能照片整理系统 - 数据库结构分析工具
"""
from app.db.session import get_db
from sqlalchemy import text

def analyze_database():
    print("=== 数据库结构分析 ===")

    db = next(get_db())

    # 查询所有表
    tables_query = text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = db.execute(tables_query).fetchall()

    print("数据库中的表:")
    for table in tables:
        print(f"  📋 {table[0]}")

    print("\n=== 详细表结构分析 ===")

    for table in tables:
        table_name = table[0]
        print(f"\n📋 表: {table_name}")

        # 查询表结构
        schema_query = text(f"PRAGMA table_info({table_name})")
        columns = db.execute(schema_query).fetchall()

        print("  字段:")
        for col in columns:
            pk = " (PK)" if col[5] else ""
            nullable = "" if col[3] else " NOT NULL"
            print(f"    - {col[1]}: {col[2]}{nullable}{pk}")

        # 查询索引
        index_query = text(f"PRAGMA index_list({table_name})")
        indexes = db.execute(index_query).fetchall()

        if indexes:
            print("  索引:")
            for idx in indexes:
                unique = "UNIQUE" if idx[2] else "普通"
                print(f"    - {idx[1]} ({unique})")
        else:
            print("  索引: 无")

    # 分析外键关系
    print("\n=== 外键关系分析 ===")
    for table in tables:
        table_name = table[0]
        fk_query = text(f"PRAGMA foreign_key_list({table_name})")
        fks = db.execute(fk_query).fetchall()

        if fks:
            print(f"\n🔗 {table_name} 的外键:")
            for fk in fks:
                print(f"    - {fk[3]} -> {fk[2]}.{fk[4]}")

    # 数据量统计
    print("\n=== 数据量统计 ===")
    for table in tables:
        table_name = table[0]
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        count = db.execute(count_query).scalar()
        print(f"  {table_name}: {count} 条记录")

    db.close()

if __name__ == "__main__":
    analyze_database()
