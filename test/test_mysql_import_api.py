#!/usr/bin/env python3
"""
测试 MySQL 数据导入 API

功能：
1. 测试 CSV 文件预览
2. 测试 CSV 导入到 MySQL
"""

import requests
import os

API_BASE = "http://localhost:5050/api"
TOKEN = "test"  # 请替换为真实的 JWT token

headers = {"Authorization": f"Bearer {TOKEN}"}


def test_preview_csv():
    """测试预览 CSV 文件"""
    print("=" * 60)
    print("测试 1: 预览 CSV 文件")
    print("=" * 60)

    csv_file = "test/data/sample_data.csv"

    if not os.path.exists(csv_file):
        print(f"❌ 文件不存在: {csv_file}")
        return None

    with open(csv_file, "rb") as f:
        files = {"file": (os.path.basename(csv_file), f, "text/csv")}
        response = requests.post(f"{API_BASE}/knowledge/mysql/preview", headers=headers, files=files)

    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 文件名: {data['filename']}")
        print(f"✓ 总行数: {data['total_rows']}")
        print(f"✓ 总列数: {data['total_columns']}")
        print(f"\n列信息:")
        for col in data["columns"]:
            print(f"  - {col['name']}: {col['type']}")
        print(f"\n前 5 行数据:")
        for i, row in enumerate(data["data"][:5], 1):
            print(f"  {i}. {row}")
        return data
    else:
        print(f"❌ 请求失败: {response.text}")
        return None


def test_import_to_mysql():
    """测试导入 CSV 到 MySQL"""
    print("\n" + "=" * 60)
    print("测试 2: 导入 CSV 到 MySQL")
    print("=" * 60)

    # 首先上传文件到服务器
    csv_file = "test/data/sample_data.csv"
    if not os.path.exists(csv_file):
        print(f"❌ 文件不存在: {csv_file}")
        return

    # 上传文件
    print("\n步骤 1: 上传文件...")
    with open(csv_file, "rb") as f:
        files = {"file": (os.path.basename(csv_file), f, "text/csv")}
        upload_response = requests.post(f"{API_BASE}/knowledge/files/upload", headers=headers, files=files)

    if upload_response.status_code != 200:
        print(f"❌ 文件上传失败: {upload_response.text}")
        return

    upload_data = upload_response.json()
    file_path = upload_data["file_path"]
    print(f"✓ 文件已上传到: {file_path}")

    # 导入到 MySQL
    print("\n步骤 2: 导入到 MySQL...")
    import_payload = {
        "file_path": file_path,
        "table_name": "test_employees",
        "create_table": True,
        "drop_if_exists": True,
        "batch_size": 1000,
    }

    import_response = requests.post(f"{API_BASE}/knowledge/mysql/import", headers=headers, json=import_payload)

    print(f"状态码: {import_response.status_code}")
    if import_response.status_code == 200:
        data = import_response.json()
        print(f"✓ {data['message']}")
        print(f"  - 表名: {data['table_name']}")
        print(f"  - 总行数: {data['total_rows']}")
        print(f"  - 已插入: {data['inserted_rows']}")
        print(f"  - 最终计数: {data['final_count']}")
    else:
        print(f"❌ 导入失败: {import_response.text}")


def test_query_mysql():
    """测试查询 MySQL 数据"""
    print("\n" + "=" * 60)
    print("测试 3: 查询 MySQL 数据（使用 mysql_query_database 工具）")
    print("=" * 60)

    # 通过 Agent 查询数据
    query_payload = {
        "messages": [{"role": "user", "content": "查询 test_employees 表的所有数据，并展示前 5 条"}],
        "agent_id": "ReActAgent",
        "stream": False,
    }

    response = requests.post(f"{API_BASE}/chat/agent/ReActAgent/chat", headers=headers, json=query_payload)

    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Agent 响应:")
        print(data.get("content", "无响应内容"))
    else:
        print(f"❌ 查询失败: {response.text}")


if __name__ == "__main__":
    # 测试 1: 预览 CSV 文件
    preview_data = test_preview_csv()

    # 测试 2: 导入到 MySQL
    if preview_data:
        test_import_to_mysql()

    # 测试 3: 查询 MySQL 数据
    # test_query_mysql()  # 需要真实的 JWT token

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
