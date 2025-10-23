#!/usr/bin/env python3
"""
直接测试 MySQL 数据导入功能（绕过 API 认证）
"""

import sys
import os
import pandas as pd
from io import BytesIO

# 添加项目路径
sys.path.insert(0, "/app")

from src.utils import logger


def test_preview_csv():
    """测试预览 CSV 文件"""
    print("=" * 60)
    print("测试 1: 预览 CSV 文件")
    print("=" * 60)

    csv_file = "/app/test/data/sample_data.csv"

    if not os.path.exists(csv_file):
        print(f"❌ 文件不存在: {csv_file}")
        return None

    try:
        # 读取 CSV 文件
        df = pd.read_csv(csv_file, encoding="utf-8")

        # 替换 NaN 为 None
        df = df.where(pd.notnull(df), None)

        # 获取列信息
        columns_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            columns_info.append({"name": col, "type": dtype})

        # 转换为字典列表
        data = df.to_dict(orient="records")

        print(f"✓ 文件名: {os.path.basename(csv_file)}")
        print(f"✓ 总行数: {len(df)}")
        print(f"✓ 总列数: {len(df.columns)}")
        print(f"\n列信息:")
        for col in columns_info:
            print(f"  - {col['name']}: {col['type']}")
        print(f"\n全部数据:")
        for i, row in enumerate(data, 1):
            print(f"  {i}. {row}")

        return csv_file

    except Exception as e:
        logger.error(f"预览失败: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_import_to_mysql(csv_file):
    """测试导入 CSV 到 MySQL"""
    print("\n" + "=" * 60)
    print("测试 2: 导入 CSV 到 MySQL")
    print("=" * 60)

    import pymysql

    try:
        # 读取 CSV
        df = pd.read_csv(csv_file, encoding="utf-8")

        # 处理列名
        df.columns = [col.replace(" ", "_").replace("-", "_") for col in df.columns]

        # 替换 NaN
        df = df.where(pd.notnull(df), None)

        print(f"✓ CSV 加载成功，共 {len(df)} 行 {len(df.columns)} 列")

        # 连接 MySQL
        mysql_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "testdb"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "charset": "utf8mb4",
        }

        connection = pymysql.connect(**mysql_config)
        cursor = connection.cursor()
        print(f"✓ MySQL 连接成功: {mysql_config['user']}@{mysql_config['host']}:{mysql_config['port']}")

        # 表名
        table_name = "test_csv_import"

        # 删除已存在的表
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        print(f"✓ 已删除旧表（如果存在）")

        # 创建表
        def infer_mysql_type(dtype, max_length=None):
            dtype_str = str(dtype)
            if "int" in dtype_str:
                return "BIGINT"
            elif "float" in dtype_str:
                return "DOUBLE"
            elif "bool" in dtype_str:
                return "BOOLEAN"
            elif "datetime" in dtype_str:
                return "DATETIME"
            elif "date" in dtype_str:
                return "DATE"
            else:
                if max_length and max_length < 255:
                    return f"VARCHAR({max(255, max_length + 50)})"
                else:
                    return "TEXT"

        columns = []
        for col in df.columns:
            dtype = df[col].dtype
            max_length = None
            if dtype == "object":
                max_length = df[col].astype(str).str.len().max()
            mysql_type = infer_mysql_type(dtype, max_length)
            columns.append(f"`{col}` {mysql_type}")

        columns.insert(0, "`id` BIGINT AUTO_INCREMENT PRIMARY KEY")

        create_sql = f"""
        CREATE TABLE `{table_name}` (
            {', '.join(columns)}
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        cursor.execute(create_sql)
        connection.commit()
        print(f"✓ 表 {table_name} 创建成功")
        print(f"  表结构: {columns}")

        # 导入数据
        columns_str = ", ".join([f"`{col}`" for col in df.columns])
        placeholders = ", ".join(["%s"] * len(df.columns))
        insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"

        data = [tuple(row) for row in df.values]
        cursor.executemany(insert_sql, data)
        connection.commit()
        print(f"✓ 数据导入成功，共 {len(data)} 行")

        # 验证导入结果
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        count = cursor.fetchone()[0]
        print(f"✓ 验证成功: 表中有 {count} 行数据")

        # 查询前 5 行
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 5")
        rows = cursor.fetchall()
        print(f"\n前 5 行数据:")
        for row in rows:
            print(f"  {row}")

        cursor.close()
        connection.close()

        return table_name

    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 测试 1: 预览 CSV
    csv_file = test_preview_csv()

    # 测试 2: 导入到 MySQL
    if csv_file:
        test_import_to_mysql(csv_file)

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
