#!/usr/bin/env python3
"""
直接测试 MySQL 表管理功能（绕过 API 认证）
"""

import sys
import os
import pymysql

# 添加项目路径
sys.path.insert(0, "/app")

from src.utils import logger


def test_get_tables():
    """测试获取表列表"""
    print("=" * 60)
    print("测试 1: 获取 MySQL 表列表")
    print("=" * 60)

    try:
        # 连接 MySQL
        connection = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "mysql"),
            user=os.getenv("MYSQL_USER", "testuser"),
            password=os.getenv("MYSQL_PASSWORD", "testpassword"),
            database=os.getenv("MYSQL_DATABASE", "testdb"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            charset="utf8mb4",
        )
        cursor = connection.cursor()

        # 获取所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"✓ 共有 {len(tables)} 个表\n")

        # 获取每个表的详细信息
        for (table_name,) in tables:
            # 获取行数
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]

            # 获取列信息
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            columns = cursor.fetchall()
            column_count = len(columns)
            column_names = [col[0] for col in columns]

            print(f"表名: {table_name}")
            print(f"  行数: {row_count}")
            print(f"  列数: {column_count}")
            print(f"  列名: {', '.join(column_names)}\n")

        cursor.close()
        connection.close()

        return [table[0] for table in tables]

    except Exception as e:
        logger.error(f"获取表列表失败: {e}")
        import traceback

        traceback.print_exc()
        return []


def test_get_table_data(table_name, limit=10):
    """测试获取表数据"""
    print("=" * 60)
    print(f"测试 2: 获取表 {table_name} 的数据（前 {limit} 行）")
    print("=" * 60)

    try:
        connection = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "mysql"),
            user=os.getenv("MYSQL_USER", "testuser"),
            password=os.getenv("MYSQL_PASSWORD", "testpassword"),
            database=os.getenv("MYSQL_DATABASE", "testdb"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            charset="utf8mb4",
        )
        cursor = connection.cursor()

        # 获取列信息
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns_info = cursor.fetchall()
        column_names = [col[0] for col in columns_info]

        print(f"列名: {', '.join(column_names)}\n")

        # 获取数据
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {limit}")
        rows = cursor.fetchall()

        print(f"数据（前 {limit} 行）:")
        for i, row in enumerate(rows, 1):
            row_dict = dict(zip(column_names, row))
            print(f"  {i}. {row_dict}")

        cursor.close()
        connection.close()

    except Exception as e:
        logger.error(f"获取表数据失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # 测试 1: 获取表列表
    tables = test_get_tables()

    if tables:
        # 测试 2: 获取第一个表的数据
        test_get_table_data(tables[0], limit=5)

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
