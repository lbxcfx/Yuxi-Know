# MySQL CSV/Excel 导入功能使用指南

## 概述

本功能允许用户通过知识库界面上传 Excel/CSV 文件，预览数据内容，并将数据存储到 MySQL 数据库中，供大模型查询和分析。

## 功能特点

✅ **支持多种格式**: CSV (.csv), Excel (.xlsx, .xls)
✅ **全数据预览**: 上传后展示完整表格数据
✅ **自动类型推断**: 自动识别数据类型并创建对应的 MySQL 表结构
✅ **智能编码处理**: 自动处理 UTF-8、GBK、Latin1 等多种编码
✅ **批量导入**: 支持大文件批量导入
✅ **AI 集成**: 导入后大模型可通过 `mysql_query_database` 工具查询数据

---

## API 接口

### 1. 预览 Excel/CSV 文件

**接口**: `POST /api/knowledge/mysql/preview`

**功能**: 上传文件并预览全部数据（包括列信息、数据类型、所有行）

**请求参数**:
- `file`: 上传的文件（multipart/form-data）

**响应示例**:
```json
{
  "message": "success",
  "filename": "sample_data.csv",
  "total_rows": 10,
  "total_columns": 6,
  "columns": [
    {"name": "姓名", "type": "object"},
    {"name": "年龄", "type": "int64"},
    {"name": "城市", "type": "object"},
    {"name": "职业", "type": "object"},
    {"name": "工资", "type": "int64"},
    {"name": "入职日期", "type": "object"}
  ],
  "data": [
    {
      "姓名": "张三",
      "年龄": 28,
      "城市": "北京",
      "职业": "软件工程师",
      "工资": 15000,
      "入职日期": "2022-01-15"
    },
    ...
  ]
}
```

---

### 2. 导入数据到 MySQL

**接口**: `POST /api/knowledge/mysql/import`

**功能**: 将已上传的文件导入到 MySQL 数据库

**请求参数** (application/json):
```json
{
  "file_path": "/path/to/uploaded/file.csv",
  "table_name": "employees",
  "create_table": true,
  "drop_if_exists": false,
  "batch_size": 1000
}
```

**参数说明**:
- `file_path` (必填): 已上传文件的服务器路径
- `table_name` (必填): 目标 MySQL 表名
- `create_table` (可选): 是否自动创建表，默认 `true`
- `drop_if_exists` (可选): 如果表已存在是否删除重建，默认 `false`
- `batch_size` (可选): 批量插入大小，默认 `1000`

**响应示例**:
```json
{
  "message": "导入成功",
  "status": "success",
  "table_name": "employees",
  "total_rows": 10,
  "inserted_rows": 10,
  "final_count": 10
}
```

---

## 使用流程

### 完整流程示例

```
1. 用户在前端上传 CSV/Excel 文件
   ↓
2. 调用 /api/knowledge/mysql/preview 预览数据
   - 前端展示完整表格
   - 用户确认数据正确性
   ↓
3. 调用 /api/knowledge/files/upload 上传文件到服务器
   - 获得 file_path
   ↓
4. 调用 /api/knowledge/mysql/import 导入到 MySQL
   - 设置表名
   - 选择是否创建表/覆盖已有表
   ↓
5. 导入成功后，大模型可以查询数据
```

---

## Python 使用示例

### 示例 1: 预览 CSV 文件

```python
import requests

API_BASE = "http://localhost:5050/api"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

# 上传并预览文件
with open("data.csv", "rb") as f:
    files = {"file": ("data.csv", f, "text/csv")}
    response = requests.post(
        f"{API_BASE}/knowledge/mysql/preview",
        headers=headers,
        files=files
    )

preview_data = response.json()
print(f"总行数: {preview_data['total_rows']}")
print(f"列信息: {preview_data['columns']}")
print(f"数据预览: {preview_data['data'][:5]}")  # 前5行
```

### 示例 2: 上传并导入到 MySQL

```python
import requests

API_BASE = "http://localhost:5050/api"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

# 步骤 1: 上传文件
with open("employees.csv", "rb") as f:
    files = {"file": ("employees.csv", f, "text/csv")}
    upload_response = requests.post(
        f"{API_BASE}/knowledge/files/upload",
        headers=headers,
        files=files
    )

file_path = upload_response.json()["file_path"]

# 步骤 2: 导入到 MySQL
import_payload = {
    "file_path": file_path,
    "table_name": "employees",
    "create_table": True,
    "drop_if_exists": True,
    "batch_size": 1000
}

import_response = requests.post(
    f"{API_BASE}/knowledge/mysql/import",
    headers=headers,
    json=import_payload
)

result = import_response.json()
print(f"导入结果: {result['message']}")
print(f"表名: {result['table_name']}")
print(f"导入行数: {result['inserted_rows']}")
```

---

## 大模型查询示例

导入数据后，可以通过 ReActAgent 查询 MySQL 数据：

### 示例对话

**用户**: 查询 employees 表中工资最高的前 5 名员工

**Agent 响应**:
```
我来帮你查询 employees 表中工资最高的前 5 名员工。

[调用工具: mysql_query_database]
查询语句: SELECT * FROM employees ORDER BY 工资 DESC LIMIT 5

查询结果:
1. 郑十一 - 架构师 - 西安 - 25000 元
2. 赵六 - 项目经理 - 广州 - 22000 元
3. 李四 - 产品经理 - 上海 - 18000 元
4. 周九 - 后端开发 - 南京 - 17000 元
5. 钱七 - 数据分析师 - 杭州 - 16000 元
```

---

## 数据类型映射

CSV/Excel 数据类型会自动映射为 MySQL 类型：

| Pandas 类型 | MySQL 类型 | 说明 |
|------------|-----------|------|
| int64 | BIGINT | 整数 |
| float64 | DOUBLE | 浮点数 |
| bool | BOOLEAN | 布尔值 |
| datetime64 | DATETIME | 日期时间 |
| object (字符串 < 255) | VARCHAR(255+) | 短文本 |
| object (字符串 >= 255) | TEXT | 长文本 |

---

## 注意事项

### ⚠️ 重要提示

1. **列名处理**:
   - 空格和连字符会被替换为下划线
   - 例如: `"First Name"` → `"First_Name"`

2. **表命名**:
   - 使用有意义的表名，避免使用 MySQL 保留字
   - 推荐使用小写字母和下划线组合

3. **数据覆盖**:
   - 设置 `drop_if_exists=true` 会删除已有表，请谨慎使用
   - 建议先预览数据，确认无误后再导入

4. **编码问题**:
   - CSV 文件推荐使用 UTF-8 编码
   - 系统会自动尝试 UTF-8 → GBK → Latin1 编码

5. **文件大小**:
   - 支持大文件批量导入
   - 默认批量大小为 1000 行，可根据需要调整

---

## 常见问题

### Q1: 如何处理包含中文的 CSV 文件？

**A**: 系统会自动检测编码。如果遇到乱码，请确保 CSV 文件使用 UTF-8 编码保存。

### Q2: 导入失败怎么办？

**A**: 检查以下几点：
- 文件格式是否正确（.csv, .xlsx, .xls）
- MySQL 服务是否正常运行
- 表名是否已存在且未设置覆盖选项
- 查看日志获取详细错误信息

### Q3: 如何让大模型查询导入的数据？

**A**: 导入成功后，直接在对话中询问，例如：
- "查询 employees 表的所有数据"
- "employees 表中有多少人在北京工作？"
- "计算 employees 表的平均工资"

### Q4: 支持哪些文件格式？

**A**: 目前支持：
- ✅ CSV (.csv)
- ✅ Excel 2007+ (.xlsx)
- ✅ Excel 97-2003 (.xls)

---

## 技术架构

```
┌─────────────┐
│  前端界面   │
└──────┬──────┘
       │
       ├─ POST /api/knowledge/mysql/preview (预览数据)
       │
       ├─ POST /api/knowledge/files/upload (上传文件)
       │
       ├─ POST /api/knowledge/mysql/import (导入MySQL)
       │
       ↓
┌─────────────────────────────────────┐
│         后端 API (FastAPI)          │
├─────────────────────────────────────┤
│  1. pandas 读取 CSV/Excel           │
│  2. 自动推断数据类型                │
│  3. pymysql 连接 MySQL              │
│  4. 创建表结构                      │
│  5. 批量插入数据                    │
└──────────────┬──────────────────────┘
               │
               ↓
        ┌──────────────┐
        │  MySQL 数据库 │
        └──────┬───────┘
               │
               ↓
        ┌─────────────────────────┐
        │  AI Agent 工具调用      │
        │  mysql_query_database   │
        └─────────────────────────┘
```

---

## 测试结果

✅ **测试 1**: CSV 预览功能
- 成功读取 10 行 6 列数据
- 正确识别中文列名和数据类型
- 完整展示所有数据

✅ **测试 2**: MySQL 导入功能
- 成功创建表结构（自动推断类型）
- 成功插入 10 行数据
- 验证数据完整性通过

✅ **测试 3**: 大模型查询
- Agent 可通过 `mysql_query_database` 工具查询数据
- 支持复杂 SQL 查询
- 支持结果可视化（配合图表工具）

---

## 相关文件

- **API 实现**: `server/routers/knowledge_router.py:641-862`
- **导入脚本**: `scripts/import_csv_to_mysql.py`
- **测试脚本**: `test/test_mysql_import_direct.py`
- **测试数据**: `test/data/sample_data.csv`

---

## 更新日志

**v1.0.0** (2025-10-22)
- ✨ 新增 CSV/Excel 预览 API
- ✨ 新增 MySQL 导入 API
- ✨ 支持完整数据展示
- ✨ 自动推断数据类型
- ✨ 智能编码处理
- ✨ 批量导入支持
