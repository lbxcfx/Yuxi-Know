# ReActAgent 工具使用指南

ReActAgent 配备了 11 个工具，可以帮助您完成各种任务。以下是详细的使用说明和示例。

---

## 📚 工具分类

### 1. 知识库检索工具（6个）
### 2. 静态工具（2个）
### 3. MySQL 数据库工具（3个）

---

## 1️⃣ 知识库检索工具

这些工具用于从已创建的知识库中检索相关信息。

### 工具格式
- **工具名**: `query_{db_id前8位}` （例如：`query_ef30b`）
- **参数**: `query_text` (字符串) - 查询关键词

### 使用示例

#### 示例 1: 查询知识库中的技术文档
```
用户提问: "请帮我查找关于 Docker 容器部署的最佳实践"

Agent 思考过程:
1. 我需要在知识库中搜索 "Docker 容器部署最佳实践"
2. 调用工具: query_ef30b
   - query_text: "Docker 容器部署 最佳实践"

工具返回结果:
[
  {
    "content": "Docker 部署最佳实践包括: 1. 使用多阶段构建...",
    "score": 0.85
  },
  ...
]

Agent 回复: 根据知识库中的信息，Docker 容器部署的最佳实践包括...
```

#### 示例 2: 查询项目文档
```
用户提问: "这个项目使用了什么 AI 模型？"

Agent 调用:
- 工具: query_ef30b
- 参数:
  {
    "query_text": "AI 模型 LLM 配置"
  }

返回: 项目使用了 qwen-max、DeepSeek 等模型...
```

### 💡 使用技巧
- **关键词优化**: 使用简洁的关键词而不是完整问题
  - ✅ 好: "Python 异步编程 asyncio"
  - ❌ 差: "请告诉我如何在Python中使用异步编程？"
- **多关键词**: 可以使用多个相关关键词提高检索准确度

---

## 2️⃣ 静态工具

### 2.1 query_knowledge_graph - 知识图谱查询

查询知识图谱中的食品领域知识。

**参数**: `query` (字符串) - 查询关键词

#### 使用示例

```
用户提问: "苹果有什么营养价值？"

Agent 调用:
- 工具: query_knowledge_graph
- 参数: "苹果"

返回结果:
{
  "triples": [
    {"subject": "苹果", "predicate": "包含", "object": "维生素C"},
    {"subject": "苹果", "predicate": "富含", "object": "膳食纤维"},
    ...
  ]
}

Agent 回复: 根据知识图谱，苹果富含维生素C、膳食纤维...
```

### 2.2 tavily_search_results_json - Web 搜索

使用 Tavily 搜索引擎获取实时网络信息。

**参数**: `query` (字符串) - 搜索查询

#### 使用示例

```
用户提问: "请搜索英伟达最新的股价和市场动态"

Agent 调用:
- 工具: tavily_search_results_json
- 参数: "NVIDIA stock price market trends 2025"

返回结果:
[
  {
    "title": "NVIDIA Stock Surges on AI Chip Demand",
    "url": "https://...",
    "content": "NVIDIA股价今日上涨5%，AI芯片需求强劲...",
    "score": 0.95
  },
  ...
]

Agent 回复: 根据最新搜索结果，英伟达股价...
```

#### 典型使用场景
- ✅ 实时信息查询（股票、新闻、天气）
- ✅ 最新技术动态
- ✅ 市场趋势分析
- ✅ 事实核查

---

## 3️⃣ MySQL 数据库工具

这三个工具提供完整的数据库查询功能。

### 3.1 mysql_list_tables - 列出所有表

获取数据库中所有表名及行数。

**参数**: 无

#### 使用示例

```
用户提问: "数据库里有哪些表？"

Agent 调用:
- 工具: mysql_list_tables
- 参数: {}

返回结果:
数据库中的表:
- users (约 1500 行)
- orders (约 3200 行)
- products (约 450 行)
- reviews (约 5600 行)

Agent 回复: 数据库包含 4 个表: users、orders、products、reviews
```

### 3.2 mysql_describe_table - 查看表结构

获取指定表的详细结构信息（字段、类型、索引等）。

**参数**:
- `table_name` (字符串) - 表名

#### 使用示例

```
用户提问: "users 表的结构是什么？"

Agent 调用:
- 工具: mysql_describe_table
- 参数: {"table_name": "users"}

返回结果:
表 `users` 的结构:

字段名          类型            NULL    键    默认值          额外
--------------------------------------------------------------------------------
id              int(11)         NO      PRI                   auto_increment
username        varchar(50)     NO      UNI
email           varchar(100)    NO
created_at      timestamp       NO            CURRENT_TIMESTAMP
is_active       tinyint(1)      YES           1

索引信息:
- PRIMARY: id
- username_idx: username
- email_idx: email

Agent 回复: users 表包含 5 个字段: id (主键)、username (唯一索引)、email、created_at、is_active...
```

### 3.3 mysql_query - 执行 SQL 查询

执行只读的 SELECT 查询语句。

**参数**:
- `sql` (字符串) - SQL 查询语句（仅支持 SELECT）
- `limit` (整数, 可选) - 最大返回行数，默认 100，最大 1000
- `timeout` (整数, 可选) - 查询超时秒数，默认 10，最大 60

#### 使用示例

#### 示例 1: 简单查询
```
用户提问: "查询所有活跃用户"

Agent 调用:
- 工具: mysql_query
- 参数:
  {
    "sql": "SELECT id, username, email FROM users WHERE is_active = 1",
    "limit": 100
  }

返回结果:
查询成功，返回 45 行:
id  | username  | email
----|-----------|------------------
1   | alice     | alice@example.com
2   | bob       | bob@example.com
...

Agent 回复: 找到 45 个活跃用户，包括 alice、bob...
```

#### 示例 2: 复杂聚合查询
```
用户提问: "每个用户的订单总金额是多少？只显示前10名"

Agent 调用:
- 工具: mysql_query
- 参数:
  {
    "sql": "SELECT u.username, COUNT(o.id) as order_count, SUM(o.amount) as total_amount FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.username ORDER BY total_amount DESC",
    "limit": 10
  }

返回结果:
username  | order_count | total_amount
----------|-------------|-------------
alice     | 25          | 5680.50
bob       | 18          | 3420.00
charlie   | 15          | 2890.75
...

Agent 回复: 订单金额排名前10的用户中，alice 以 $5,680.50 排名第一...
```

#### 示例 3: JOIN 查询
```
用户提问: "查找最近 7 天内购买了产品的用户及其购买详情"

Agent 调用:
- 工具: mysql_query
- 参数:
  {
    "sql": "SELECT u.username, p.product_name, o.amount, o.created_at FROM orders o JOIN users u ON o.user_id = u.id JOIN products p ON o.product_id = p.id WHERE o.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) ORDER BY o.created_at DESC",
    "limit": 50
  }
```

### 🔒 安全限制

MySQL 工具有以下安全限制：

1. **只读操作**: 仅支持 SELECT 查询，不允许 INSERT、UPDATE、DELETE、DROP 等修改操作
2. **SQL 注入防护**: 自动检测并拒绝可疑的 SQL 语句
3. **结果大小限制**: 最多返回 1000 行数据
4. **超时保护**: 查询最长运行 60 秒
5. **表名验证**: 表名只允许字母、数字、下划线

---

## 🎯 完整工作流示例

### 场景: 数据分析任务

```
用户提问: "分析一下我们的用户活跃度，并与行业标准对比"

Agent 工作流:

步骤 1: 查看数据库表结构
- 工具: mysql_list_tables
- 获取可用表: users, orders, user_activity

步骤 2: 查询用户活跃数据
- 工具: mysql_query
- SQL: SELECT COUNT(*) as active_users FROM users WHERE last_login >= DATE_SUB(NOW(), INTERVAL 30 DAY)
- 结果: 1250 活跃用户

步骤 3: 计算活跃率
- 工具: mysql_query
- SQL: SELECT COUNT(*) as total_users FROM users
- 结果: 2000 总用户

步骤 4: 搜索行业标准
- 工具: tavily_search_results_json
- 查询: "SaaS user engagement industry benchmark 2025"
- 结果: 行业平均活跃率 55-65%

步骤 5: 综合分析
- 计算: 1250/2000 = 62.5%
- 对比: 62.5% 处于行业标准范围内 (55-65%)

Agent 回复:
"根据分析，我们的用户活跃度为 62.5% (1250/2000)，处于行业标准的中上水平。
根据最新行业数据，SaaS 产品的平均活跃率在 55-65% 之间，我们的表现良好。"
```

---

## 📝 最佳实践

### 1. 知识库检索
- 使用精确的关键词，避免自然语言问句
- 可以组合多个关键词提高准确度

### 2. Web 搜索
- 对于需要最新信息的问题，明确告诉 Agent 使用搜索
- 使用英文关键词通常效果更好

### 3. MySQL 查询
- 先使用 `mysql_list_tables` 了解表结构
- 再使用 `mysql_describe_table` 查看字段详情
- 最后编写 `mysql_query` 执行查询
- 使用 `LIMIT` 控制结果数量

### 4. 组合使用
- 多个工具可以组合使用完成复杂任务
- 例如: 数据库查询 + Web 搜索 + 知识库检索

---

## ❓ 常见问题

### Q: 为什么 Agent 不使用工具？
A: 可能原因：
1. 问题太简单，模型认为可以直接回答
2. 提示不够明确，可以在问题中明确要求使用工具
3. 例如："请使用搜索工具查找..."

### Q: MySQL 工具报错怎么办？
A: 检查：
1. 环境变量中的 MySQL 配置是否正确
2. SQL 语句是否是 SELECT 查询
3. 表名和字段名是否正确

### Q: 如何让 Agent 优先使用搜索？
A: 在问题中明确指示：
- "请搜索最新的..."
- "用 web search 查找..."
- "在网上搜索..."

---

生成时间: 2025-10-19
