#!/usr/bin/env python3
"""
测试 MySQL 查询功能
"""

import sys

sys.path.insert(0, ".")

from src.agents.common.toolkits.mysql.tools import mysql_list_tables, mysql_describe_table, mysql_query

print("=" * 60)
print("测试 MySQL 工具")
print("=" * 60)

# 1. 列出所有表
print("\n1. 列出所有表:")
print("-" * 60)
result = mysql_list_tables.invoke({})
print(result)

# 2. 查看 employees 表结构
print("\n2. 查看 employees 表结构:")
print("-" * 60)
result = mysql_describe_table.invoke({"table_name": "employees"})
print(result)

# 3. 查询员工数据
print("\n3. 查询工资最高的5名员工:")
print("-" * 60)
result = mysql_query.invoke({"sql": "SELECT 姓名, 职业, 工资, 城市 FROM employees ORDER BY 工资 DESC LIMIT 5"})
print(result)

# 4. 统计查询
print("\n4. 统计各城市的平均工资:")
print("-" * 60)
result = mysql_query.invoke({"sql": "SELECT 城市, AVG(工资) as 平均工资, COUNT(*) as 人数 FROM employees GROUP BY 城市 ORDER BY 平均工资 DESC"})
print(result)

print("\n" + "=" * 60)
print("✓ 所有测试完成！")
print("=" * 60)
