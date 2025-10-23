#!/usr/bin/env python3
"""
CSV/Excel 数据导入 MySQL 脚本

功能：
- 支持导入 CSV 和 Excel (.xlsx, .xls) 文件
- 自动推断数据类型
- 自动创建表结构（可选）
- 批量导入数据

使用示例：
    python scripts/import_csv_to_mysql.py --file data.csv --table my_table
    python scripts/import_csv_to_mysql.py --file data.xlsx --table my_table --create-table
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import pymysql
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import logger

# 加载环境变量
load_dotenv()


def get_mysql_connection():
    """获取 MySQL 连接"""
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "testdb"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
    }

    logger.info(f"连接到 MySQL: {config['user']}@{config['host']}:{config['port']}/{config['database']}")

    try:
        connection = pymysql.connect(**config)
        logger.info("✓ MySQL 连接成功")
        return connection
    except Exception as e:
        logger.error(f"✗ MySQL 连接失败: {e}")
        raise


def infer_mysql_type(dtype, max_length=None):
    """根据 pandas dtype 推断 MySQL 数据类型"""
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
        # 字符串类型
        if max_length and max_length < 255:
            return f"VARCHAR({max(255, max_length + 50)})"
        else:
            return "TEXT"


def create_table_from_dataframe(connection, table_name, df, drop_if_exists=False):
    """根据 DataFrame 创建表"""
    cursor = connection.cursor()

    try:
        # 检查表是否存在
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        table_exists = cursor.fetchone() is not None

        if table_exists:
            if drop_if_exists:
                logger.warning(f"删除已存在的表: {table_name}")
                cursor.execute(f"DROP TABLE `{table_name}`")
            else:
                logger.info(f"表 {table_name} 已存在，跳过创建")
                return

        # 分析每列的数据类型和最大长度
        columns = []
        for col in df.columns:
            dtype = df[col].dtype
            max_length = None

            if dtype == "object":
                # 计算字符串最大长度
                max_length = df[col].astype(str).str.len().max()

            mysql_type = infer_mysql_type(dtype, max_length)
            # 处理列名中的特殊字符
            safe_col_name = col.replace(" ", "_").replace("-", "_")
            columns.append(f"`{safe_col_name}` {mysql_type}")

        # 添加自增主键
        columns.insert(0, "`id` BIGINT AUTO_INCREMENT PRIMARY KEY")

        # 创建表
        create_sql = f"""
        CREATE TABLE `{table_name}` (
            {', '.join(columns)}
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        cursor.execute(create_sql)
        connection.commit()
        logger.info(f"✓ 表 {table_name} 创建成功")
        logger.debug(f"表结构: {create_sql}")

    except Exception as e:
        connection.rollback()
        logger.error(f"✗ 创建表失败: {e}")
        raise
    finally:
        cursor.close()


def import_data_to_mysql(connection, table_name, df, batch_size=1000):
    """导入数据到 MySQL"""
    cursor = connection.cursor()

    try:
        # 处理列名
        df.columns = [col.replace(" ", "_").replace("-", "_") for col in df.columns]

        # 替换 NaN 为 None
        df = df.where(pd.notnull(df), None)

        # 生成 INSERT 语句
        columns = ", ".join([f"`{col}`" for col in df.columns])
        placeholders = ", ".join(["%s"] * len(df.columns))
        insert_sql = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"

        # 批量插入
        total_rows = len(df)
        inserted = 0

        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i : i + batch_size]
            data = [tuple(row) for row in batch.values]

            cursor.executemany(insert_sql, data)
            connection.commit()

            inserted += len(batch)
            logger.info(f"已导入 {inserted}/{total_rows} 行 ({inserted/total_rows*100:.1f}%)")

        logger.info(f"✓ 数据导入完成，共 {total_rows} 行")

    except Exception as e:
        connection.rollback()
        logger.error(f"✗ 数据导入失败: {e}")
        raise
    finally:
        cursor.close()


def load_file(file_path):
    """加载 CSV 或 Excel 文件"""
    file_ext = Path(file_path).suffix.lower()

    logger.info(f"加载文件: {file_path}")

    try:
        if file_ext == ".csv":
            # 尝试自动检测编码
            df = pd.read_csv(file_path, encoding="utf-8")
        elif file_ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}，支持 .csv, .xlsx, .xls")

        logger.info(f"✓ 文件加载成功，共 {len(df)} 行 {len(df.columns)} 列")
        logger.info(f"列名: {', '.join(df.columns.tolist())}")

        # 显示前几行预览
        logger.debug(f"数据预览:\n{df.head()}")

        return df

    except Exception as e:
        logger.error(f"✗ 文件加载失败: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="CSV/Excel 数据导入 MySQL")
    parser.add_argument("--file", "-f", required=True, help="数据文件路径 (.csv, .xlsx, .xls)")
    parser.add_argument("--table", "-t", required=True, help="目标表名")
    parser.add_argument("--create-table", action="store_true", help="自动创建表")
    parser.add_argument("--drop-if-exists", action="store_true", help="如果表存在则删除重建")
    parser.add_argument("--batch-size", type=int, default=1000, help="批量插入大小（默认 1000）")

    args = parser.parse_args()

    # 检查文件是否存在
    if not os.path.exists(args.file):
        logger.error(f"文件不存在: {args.file}")
        sys.exit(1)

    try:
        # 1. 加载文件
        df = load_file(args.file)

        # 2. 连接数据库
        connection = get_mysql_connection()

        # 3. 创建表（如果需要）
        if args.create_table:
            create_table_from_dataframe(connection, args.table, df, args.drop_if_exists)

        # 4. 导入数据
        import_data_to_mysql(connection, args.table, df, args.batch_size)

        # 5. 验证导入结果
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM `{args.table}`")
        count = cursor.fetchone()[0]
        logger.info(f"✓ 验证成功：表 {args.table} 中有 {count} 行数据")
        cursor.close()

        connection.close()
        logger.info("✓ 导入任务完成")

    except Exception as e:
        logger.error(f"✗ 导入失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
