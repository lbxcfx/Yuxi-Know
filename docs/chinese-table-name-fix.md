# 中文表名支持修复说明

## 问题描述

在使用 React Agent 查询 MySQL 数据库时，当表名包含中文字符（如 `患者医疗数据_50条_含就诊日期`）时，`mysql_describe_table` 工具会报错：

```
表名包含非法字符，请检查表名
```

## 原因分析

原始的表名验证逻辑（`src/agents/common/toolkits/mysql/security.py:77`）使用了严格的正则表达式：

```python
# 旧代码
return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name))
```

这个正则表达式只允许：
- 首字符：ASCII 字母或下划线
- 后续字符：ASCII 字母、数字、下划线

因此，任何包含中文、连字符或其他 Unicode 字符的表名都会被拒绝。

## 解决方案

### 修改内容

修改了 `MySQLSecurityChecker.validate_table_name()` 方法，采用**黑名单机制**而非白名单：

```python
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
```

### 安全性考虑

新的验证逻辑仍然保持了安全性：

1. **长度限制**: 不超过 64 字符（MySQL 限制）
2. **危险字符检测**: 阻止可能导致 SQL 注入的特殊字符：
   - `;` - 语句分隔符
   - `'`, `"`, `` ` `` - 字符串引号
   - `(`, `)` - 函数调用
   - 空白字符 - 可能的语法操作
   - `\`, `/` - 转义和注释
   - `*`, `=`, `<`, `>` - SQL 操作符

3. **反引号包围**: 在实际执行 SQL 时，表名仍然使用反引号包围（`` `table_name` ``），这是 MySQL 的最佳实践

### 测试验证

```bash
✅ 患者医疗数据_50条_含就诊日期  → True (允许)
✅ 患者医疗数据                → True (允许)
✅ patients                   → True (允许)
✅ test_table                 → True (允许)
✅ table;DROP TABLE users     → False (阻止 - 包含分号)
✅ table'name                 → False (阻止 - 包含引号)
✅ table name                 → False (阻止 - 包含空格)
✅ table(123)                 → False (阻止 - 包含括号)
```

## 使用示例

现在 Agent 可以正常处理中文表名了：

```python
# 调用工具
mysql_describe_table.invoke({'table_name': '患者医疗数据_50条_含就诊日期'})

# 输出
表 `患者医疗数据_50条_含就诊日期` 的结构:

字段名          类型            NULL    键    默认值
--------------------------------------------------------------------------------
id              bigint          NO      PRI                     auto_increment
姓名            varchar(255)    YES
年龄            bigint          YES
性别            varchar(255)    YES
疾病类型        varchar(255)    YES
就诊日期        varchar(255)    YES
...
```

## 完整工作流程示例

现在用户可以这样提问：

```
用户: "查询患者医疗数据_50条_含就诊日期表中的疾病类型分布，用饼状图展示"

Agent 执行流程:
1. ✅ mysql_list_tables
   → 找到表 "患者医疗数据_50条_含就诊日期"

2. ✅ mysql_describe_table(table_name="患者医疗数据_50条_含就诊日期")
   → 查看表结构，找到 "疾病类型" 字段

3. ✅ mysql_query(
     sql="SELECT `疾病类型`, COUNT(*) as count
          FROM `患者医疗数据_50条_含就诊日期`
          GROUP BY `疾病类型`"
   )
   → 获取疾病分布数据

4. ✅ generate_pie_chart(...)
   → 生成饼状图
```

## 注意事项

### 1. 表名在 SQL 中的使用

所有工具都使用反引号包围表名，确保中文和特殊字符的正确处理：

```sql
-- ✅ 正确
SELECT * FROM `患者医疗数据_50条_含就诊日期`

-- ❌ 错误（可能导致语法错误）
SELECT * FROM 患者医疗数据_50条_含就诊日期
```

### 2. 字段名也支持中文

同样的逻辑也适用于字段名（虽然字段名验证不在 `validate_table_name` 中）：

```sql
SELECT `姓名`, `疾病类型`, `就诊日期`
FROM `患者医疗数据_50条_含就诊日期`
```

### 3. 最佳实践建议

虽然现在支持中文表名和字段名，但在生产环境中，建议：

**表名规范**：
- ✅ 推荐：使用英文和下划线，如 `patient_medical_data`
- ⚠️ 可用：使用中文，如 `患者医疗数据`
- ❌ 避免：混用中英文，如 `patient患者_data数据`

**原因**：
1. 英文表名在跨平台、跨数据库时兼容性更好
2. 更容易编写和维护 SQL 查询
3. 减少编码问题的风险

但对于**已有的中文表名数据**，现在完全可以正常使用！

## 相关文件

修改的文件：
- `src/agents/common/toolkits/mysql/security.py` - 表名验证逻辑

相关工具：
- `mysql_list_tables` - 列出所有表（包括中文表名）
- `mysql_describe_table` - 查看表结构（支持中文表名）
- `mysql_query` - 执行查询（SQL 中使用反引号包围表名）

## 版本历史

- **v1.0** (2025-10-24): 支持中文表名和字段名
  - 修改表名验证逻辑从白名单改为黑名单
  - 保持安全性的同时支持 Unicode 字符
  - 添加完整的测试用例

## 总结

✅ **现在完全支持中文表名！**

您的 React Agent 可以无缝处理包含中文字符的 MySQL 表，执行完整的"查询数据库 → 生成图表"工作流程。
