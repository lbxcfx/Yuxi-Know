# LLM 工具调用规划示例

## 用户问题
"数据库中，用饼状图画一个年龄的分布图"

## LLM 的推理过程

### 第1轮：分析问题

**Thought (内部推理):**
```
我需要完成这个任务：
1. 从数据库获取年龄数据
2. 对年龄进行分组统计
3. 用饼图展示分布

可用工具：
- mysql_list_tables: 列出所有表
- mysql_describe_table: 查看表结构
- mysql_query: 执行SQL查询 ✓ (需要这个!)
- generate_pie_chart: 生成饼图 ✓ (需要这个!)

首先，我需要查询数据库中的年龄数据。
但是我不知道表名，让我先列出所有表。
```

**Action:**
```json
{
  "tool": "mysql_list_tables",
  "arguments": {}
}
```

**Observation:**
```
数据库中的表:
- employees (约 10 行)
```

---

### 第2轮：查看表结构

**Thought:**
```
好的，有一个 employees 表，看起来应该包含员工信息。
让我查看这个表的结构，确认有年龄字段。
```

**Action:**
```json
{
  "tool": "mysql_describe_table",
  "arguments": {
    "table_name": "employees"
  }
}
```

**Observation:**
```
表 employees 的结构:
- id (bigint, 主键)
- 姓名 (varchar)
- 年龄 (bigint) ✓
- 城市 (varchar)
- 职业 (varchar)
- 工资 (bigint)
- 入职日期 (varchar)
```

---

### 第3轮：查询年龄数据

**Thought:**
```
完美！表中有"年龄"字段。
现在我需要：
1. 将年龄分组（例如：20-25岁，26-30岁等）
2. 统计每个年龄段的人数
3. 返回适合饼图的数据格式

让我编写一个 GROUP BY 查询。
```

**Action:**
```json
{
  "tool": "mysql_query",
  "arguments": {
    "sql": "SELECT CASE WHEN 年龄 < 26 THEN '25岁及以下' WHEN 年龄 BETWEEN 26 AND 30 THEN '26-30岁' WHEN 年龄 BETWEEN 31 AND 35 THEN '31-35岁' ELSE '35岁以上' END AS age_group, COUNT(*) as count FROM employees GROUP BY age_group ORDER BY age_group"
  }
}
```

**Observation:**
```
查询结果:
[
  {"age_group": "25岁及以下", "count": 2},
  {"age_group": "26-30岁", "count": 4},
  {"age_group": "31-35岁", "count": 4}
]
```

---

### 第4轮：生成饼图

**Thought:**
```
太好了！我现在有了年龄分布数据。
接下来需要调用 generate_pie_chart 工具。

根据工具文档，参数格式应该是：
data: [{category: string, value: number}, ...]

让我转换数据格式并调用工具。
```

**Action:**
```json
{
  "tool": "generate_pie_chart",
  "arguments": {
    "data": [
      {"category": "25岁及以下", "value": 2},
      {"category": "26-30岁", "value": 4},
      {"category": "31-35岁", "value": 4}
    ],
    "title": "员工年龄分布图",
    "width": 600,
    "height": 400
  }
}
```

**Observation:**
```
成功生成饼图！
返回: <chart_url> 或 <chart_image>
```

---

### 第5轮：返回结果

**Thought:**
```
任务完成！我已经：
1. ✓ 从数据库查询了年龄数据
2. ✓ 对年龄进行了分组统计
3. ✓ 生成了饼图

现在可以回复用户了。
```

**Final Answer:**
```
我已经为您生成了员工年龄分布饼图：

数据统计：
- 25岁及以下：2人 (20%)
- 26-30岁：4人 (40%)
- 31-35岁：4人 (40%)

[显示饼图]
```

---

## 关键点

### 1. LLM 的"工具调用决策"基于：

- **工具描述**: 每个工具的 `description` 字段
- **参数定义**: 每个工具的 `args` schema
- **用户意图**: 分析用户问题的关键词（"数据库"、"饼图"、"年龄分布"）
- **上下文信息**: 之前工具调用的结果

### 2. ReAct 的优势：

- **逐步推理**: 不是一次性规划所有步骤，而是根据观察结果动态调整
- **错误恢复**: 如果某个工具调用失败，LLM 可以尝试其他方法
- **灵活性**: 可以根据中间结果调整后续步骤

### 3. 没有显式的"规划"步骤：

LLM **不会**提前生成一个完整的计划（如"步骤1、步骤2、步骤3"），
而是**在每次观察后即时决定**下一步该做什么。

这就像人类解决问题一样：
- 先做第一步
- 看看结果
- 根据结果决定下一步
- 循环往复，直到问题解决

### 4. 提升规划质量的方法：

#### A. **优化工具描述**
```python
# 不好的描述
"查询数据库"

# 好的描述
"执行只读的SQL查询语句。用来执行SQL查询并返回结果。支持复杂的SELECT查询，包括JOIN、GROUP BY等。注意：只能执行查询操作，不能修改数据。"
```

#### B. **添加 System Prompt 指导**
```python
# 在 ReAct Agent 中已经有了：
"""
IMPORTANT TOOL USAGE RULES:
- For EVERY new user question, you MUST call the relevant tools again
- Always make fresh tool calls to ensure the most accurate information
- When the user asks about database, ALWAYS call mysql tools first
"""
```

#### C. **提供示例**
可以在 prompt 中添加 few-shot 示例，展示如何组合使用工具。

### 5. 实际执行流程

```
用户输入
  ↓
LLM 分析 → 决定调用 mysql_list_tables
  ↓
执行工具 → 返回表列表
  ↓
LLM 分析 → 决定调用 mysql_describe_table
  ↓
执行工具 → 返回表结构
  ↓
LLM 分析 → 决定调用 mysql_query
  ↓
执行工具 → 返回查询结果
  ↓
LLM 分析 → 决定调用 generate_pie_chart
  ↓
执行工具 → 返回饼图
  ↓
LLM 生成最终回复
```

每一步都是**即时决策**，不是预先计划！
