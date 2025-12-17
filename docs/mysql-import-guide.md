# MySQL 数据导入指南

本指南介绍如何将 Excel 或 CSV 数据导入到 MySQL 数据库，并在 Yuxi-Know 项目中使用。

## 目录
- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [数据导入](#数据导入)
- [使用示例](#使用示例)
- [常见问题](#常见问题)

---

## 快速开始

### 1. 启动 MySQL 容器

项目已配置好 MySQL 8.0 容器，直接启动即可：

```bash
docker compose up -d mysql
```

等待容器启动完成（约 30 秒），查看状态：

```bash
docker ps --filter name=mysql-dev
```

### 2. 准备数据文件

支持的文件格式：
- CSV 文件 (`.csv`)
- Excel 文件 (`.xlsx`, `.xls`)

示例 CSV 文件（`test/data/sample_data.csv`）：
```csv
姓名,年龄,城市,职业,工资,入职日期
张三,28,北京,软件工程师,15000,2022-01-15
李四,32,上海,产品经理,18000,2021-06-20
```

### 3. 导入数据

使用导入脚本：

```bash
# 在容器中运行
docker exec api-dev python scripts/import_csv_to_mysql.py \
  --file test/data/sample_data.csv \
  --table employees \
  --create-table \
  --drop-if-exists
```

参数说明：
- `--file`: 数据文件路径
- `--table`: 目标表名
- `--create-table`: 自动创建表（可选）
- `--drop-if-exists`: 如果表存在则删除重建（可选）
- `--batch-size`: 批量插入大小，默认 1000（可选）

---

## 环境配置

### MySQL 连接配置

在 `.env` 文件中配置 MySQL 连接信息：

```bash
# MySQL 配置
MYSQL_HOST=mysql                    # 容器内使用 mysql，本地使用 localhost
MYSQL_USER=testuser                 # 数据库用户名
MYSQL_PASSWORD=testpassword         # 数据库密码
MYSQL_DATABASE=testdb               # 数据库名
MYSQL_PORT=3306                     # 端口号
MYSQL_CHARSET=utf8mb4               # 字符集
MYSQL_ROOT_PASSWORD=rootpassword    # root 密码
```

### Docker Compose 配置

MySQL 服务已在 `docker-compose.yml` 中配置：

```yaml
mysql:
  image: mysql:8.0
  container_name: mysql-dev
  ports:
    - "3306:3306"
  volumes:
    - ./docker/volumes/mysql/data:/var/lib/mysql
  environment:
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-rootpassword}
    MYSQL_DATABASE: ${MYSQL_DATABASE:-testdb}
    MYSQL_USER: ${MYSQL_USER:-testuser}
    MYSQL_PASSWORD: ${MYSQL_PASSWORD:-testpassword}
```

---

## 数据导入

### 方法一：使用导入脚本（推荐）

导入脚本位于 `scripts/import_csv_to_mysql.py`，功能特性：
- 自动检测数据类型
- 自动创建表结构
- 批量导入数据
- 支持中文字段名
- 详细的日志输出

#### 导入 CSV 文件

```bash
docker exec api-dev python scripts/import_csv_to_mysql.py \
  --file test/data/sample_data.csv \
  --table employees \
  --create-table
```

#### 导入 Excel 文件

```bash
docker exec api-dev python scripts/import_csv_to_mysql.py \
  --file /path/to/your/data.xlsx \
  --table your_table_name \
  --create-table
```

#### 重新导入（删除旧表）

```bash
docker exec api-dev python scripts/import_csv_to_mysql.py \
  --file test/data/sample_data.csv \
  --table employees \
  --create-table \
  --drop-if-exists
```

### 方法二：使用 MySQL 命令行

如果你熟悉 SQL，可以直接使用 MySQL 命令：

```bash
# 进入 MySQL 容器
docker exec -it mysql-dev mysql -utestuser -ptestpassword testdb

# 手动创建表
CREATE TABLE employees (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  age INT,
  city VARCHAR(50),
  salary DECIMAL(10,2)
);

# 导入 CSV（需要将文件复制到容器）
LOAD DATA INFILE '/path/to/data.csv'
INTO TABLE employees
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
```

---

## 使用示例

### 1. 查看所有表

```python
from src.agents.common.toolkits.mysql.tools import mysql_list_tables

result = mysql_list_tables.invoke({})
print(result)
```

### 2. 查看表结构

```python
from src.agents.common.toolkits.mysql.tools import mysql_describe_table

result = mysql_describe_table.invoke({"table_name": "employees"})
print(result)
```

### 3. 查询数据

```python
from src.agents.common.toolkits.mysql.tools import mysql_query

# 查询工资最高的员工
result = mysql_query.invoke({
    "sql": "SELECT 姓名, 职业, 工资 FROM employees ORDER BY 工资 DESC LIMIT 5"
})
print(result)
```

### 4. 统计查询

```python
# 按城市统计平均工资
result = mysql_query.invoke({
    "sql": """
        SELECT 城市, AVG(工资) as 平均工资, COUNT(*) as 人数
        FROM employees
        GROUP BY 城市
        ORDER BY 平均工资 DESC
    """
})
print(result)
```

### 5. 在 Agent 中使用

项目的 MySQL 工具已集成到智能体系统中，可以通过聊天界面使用：

**用户问题示例：**
- "帮我查询工资最高的5名员工"
- "统计各城市的平均工资"
- "有多少员工在北京工作？"
- "列出所有软件工程师的信息"

Agent 会自动使用 MySQL 工具执行查询并返回结果。

---

## 常见问题

### Q1: 导入时出现编码错误怎么办？

**A:** 确保 CSV 文件使用 UTF-8 编码保存。如果是 Excel 文件，建议另存为 CSV (UTF-8) 格式。

### Q2: 如何导入大文件？

**A:** 使用 `--batch-size` 参数调整批量插入大小：

```bash
docker exec api-dev python scripts/import_csv_to_mysql.py \
  --file large_data.csv \
  --table large_table \
  --batch-size 5000
```

### Q3: 如何连接外部 MySQL 数据库？

**A:** 修改 `.env` 文件中的 MySQL 配置：

```bash
MYSQL_HOST=your_external_host      # 外部数据库地址
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
```

### Q4: 数据导入后在终端显示乱码？

**A:** 这是终端编码问题，数据库中的数据是正常的。使用 Python 工具查询可以正常显示中文。

### Q5: 如何查看 MySQL 容器日志？

**A:** 使用以下命令：

```bash
docker logs mysql-dev --tail=50
```

### Q6: 如何备份和恢复数据？

**A:** 备份数据库：

```bash
# 备份单个表
docker exec mysql-dev mysqldump -utestuser -ptestpassword testdb employees > employees_backup.sql

# 备份整个数据库
docker exec mysql-dev mysqldump -utestuser -ptestpassword testdb > testdb_backup.sql
```

恢复数据库：

```bash
docker exec -i mysql-dev mysql -utestuser -ptestpassword testdb < testdb_backup.sql
```

### Q7: 如何清空表数据但保留表结构？

**A:** 使用 TRUNCATE 命令：

```bash
docker exec mysql-dev mysql -utestuser -ptestpassword testdb -e "TRUNCATE TABLE employees;"
```

---

## 测试文件

项目提供了测试文件和脚本：

1. **示例数据**: `test/data/sample_data.csv` - 包含 10 条员工数据
2. **导入脚本**: `scripts/import_csv_to_mysql.py` - CSV/Excel 导入工具
3. **查询测试**: `test/test_mysql_query.py` - MySQL 工具测试脚本

运行完整测试：

```bash
# 测试连接
docker exec api-dev python test/test_mysql_connection.py

# 测试查询
docker exec api-dev python test/test_mysql_query.py
```

---

## 更多信息

- [MySQL 官方文档](https://dev.mysql.com/doc/)
- [pymysql 文档](https://pymysql.readthedocs.io/)
- [pandas 文档](https://pandas.pydata.org/docs/)

如有问题，请查看项目的 GitHub Issues 或联系项目维护者。
