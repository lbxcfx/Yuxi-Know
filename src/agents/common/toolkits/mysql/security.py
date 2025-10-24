import re


class MySQLSecurityChecker:
    """MySQL 安全检查器"""

    # 允许的SQL操作
    ALLOWED_OPERATIONS = {"SELECT", "SHOW", "DESCRIBE", "EXPLAIN"}

    # 危险的关键词
    DANGEROUS_KEYWORDS = {
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "REPLACE",
        "LOAD",
        "GRANT",
        "REVOKE",
        "SET",
        "COMMIT",
        "ROLLBACK",
        "UNLOCK",
        "KILL",
        "SHUTDOWN",
    }

    @classmethod
    def validate_sql(cls, sql: str) -> bool:
        """验证SQL语句的安全性"""
        if not sql:
            return False

        # 标准化SQL
        sql_upper = sql.strip().upper()

        # 检查是否是允许的操作
        if not any(sql_upper.startswith(op) for op in cls.ALLOWED_OPERATIONS):
            return False

        # 检查危险关键词
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in sql_upper:
                return False

        # 检查SQL注入模式
        sql_injection_patterns = [
            r"\bor\s+1\s*=\s*1\b",
            r"\bunion\s+select\b",
            r"\bexec\s*\(",
            r"\bxp_cmdshell\b",
            r"\bsleep\s*\(",
            r"\bbenchmark\s*\(",
            r"\bwaitfor\s+delay\b",
            r"\b;\s*drop\b",
            r"\b;\s*delete\b",
            r"\b;\s*update\b",
            r"\b;\s*insert\b",
        ]

        for pattern in sql_injection_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return False

        return True

    @classmethod
    def validate_table_name(cls, table_name: str) -> bool:
        """验证表名的安全性"""
        if not table_name:
            return False

        # 检查表名长度（MySQL 表名最大 64 字符）
        if len(table_name) > 64:
            return False

        # 检查是否包含危险字符（只需排除可能导致 SQL 注入的特殊字符）
        # 允许：字母、数字、下划线、中文字符、连字符
        # 不允许：分号、引号、反引号、括号、空格等可能导致注入的字符
        dangerous_chars = [";", "'", '"', "`", "(", ")", " ", "\t", "\n", "\r", "\\", "/", "*", "=", "<", ">"]
        for char in dangerous_chars:
            if char in table_name:
                return False

        return True

    @classmethod
    def validate_limit(cls, limit: int) -> bool:
        """验证limit参数"""
        return isinstance(limit, int) and 0 < limit <= 1000

    @classmethod
    def validate_timeout(cls, timeout: int) -> bool:
        """验证timeout参数"""
        return isinstance(timeout, int) and 1 <= timeout <= 60
