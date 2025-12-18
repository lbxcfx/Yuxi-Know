#!/usr/bin/env python3
"""
测试 MySQL 表管理 API

测试以下功能:
1. 获取表列表
2. 获取表详细信息
3. 获取表数据（分页）
4. 删除表（可选）
"""

import requests
import json

API_BASE = "http://localhost:5050/api"
TOKEN = "test"  # 测试 token

headers = {"Authorization": f"Bearer {TOKEN}"}


def test_get_tables():
    """测试获取表列表"""
    print("=" * 60)
    print("测试 1: 获取 MySQL 表列表")
    print("=" * 60)

    response = requests.get(f"{API_BASE}/knowledge/mysql/tables", headers=headers)

    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 共有 {data['total']} 个表")
        print(f"\n表列表:")
        for table in data["tables"]:
            print(f"  - {table['name']}")
            print(f"    行数: {table['row_count']}")
            print(f"    列数: {table['column_count']}")
            print(f"    列名: {', '.join(table['columns'])}")
            print(f"    创建时间: {table['create_time']}")
        return data["tables"]
    else:
        print(f"❌ 请求失败: {response.text}")
        return []


def test_get_table_info(table_name):
    """测试获取表详细信息"""
    print("\n" + "=" * 60)
    print(f"测试 2: 获取表 {table_name} 的详细信息")
    print("=" * 60)

    response = requests.get(f"{API_BASE}/knowledge/mysql/tables/{table_name}", headers=headers)

    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 表名: {data['table_name']}")
        print(f"✓ 行数: {data['row_count']}")
        print(f"✓ 列数: {data['column_count']}")
        print(f"✓ 引擎: {data['engine']}")
        print(f"✓ 字符集: {data['collation']}")
        print(f"\n表结构:")
        for col in data["columns"]:
            key_info = f" [{col['key']}]" if col["key"] else ""
            extra_info = f" {col['extra']}" if col["extra"] else ""
            null_info = "NULL" if col["null"] else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {null_info}{key_info}{extra_info}")
    else:
        print(f"❌ 请求失败: {response.text}")


def test_get_table_data(table_name, limit=10):
    """测试获取表数据"""
    print("\n" + "=" * 60)
    print(f"测试 3: 获取表 {table_name} 的数据（前 {limit} 行）")
    print("=" * 60)

    response = requests.get(
        f"{API_BASE}/knowledge/mysql/tables/{table_name}/data", headers=headers, params={"offset": 0, "limit": limit}
    )

    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 总行数: {data['total']}")
        print(f"✓ 当前页: {data['offset']} - {data['offset'] + len(data['data'])}")
        print(f"\n列名: {', '.join(data['columns'])}")
        print(f"\n数据（前 {limit} 行）:")
        for i, row in enumerate(data["data"], 1):
            print(f"  {i}. {json.dumps(row, ensure_ascii=False, indent=None)}")
    else:
        print(f"❌ 请求失败: {response.text}")


def test_delete_table(table_name):
    """测试删除表（谨慎使用）"""
    print("\n" + "=" * 60)
    print(f"测试 4: 删除表 {table_name}")
    print("=" * 60)

    confirm = input(f"确认删除表 {table_name}? (yes/no): ")
    if confirm.lower() != "yes":
        print("已取消删除操作")
        return

    response = requests.delete(f"{API_BASE}/knowledge/mysql/tables/{table_name}", headers=headers)

    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ {data['message']}")
    else:
        print(f"❌ 请求失败: {response.text}")


if __name__ == "__main__":
    # 测试 1: 获取表列表
    tables = test_get_tables()

    if tables:
        # 选择第一个表进行测试
        test_table = tables[0]["name"]

        # 测试 2: 获取表详细信息
        test_get_table_info(test_table)

        # 测试 3: 获取表数据
        test_get_table_data(test_table, limit=5)

        # 测试 4: 删除表（可选，需要确认）
        # test_delete_table(test_table)

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
