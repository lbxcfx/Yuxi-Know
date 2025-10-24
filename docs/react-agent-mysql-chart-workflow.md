# React Agent MySQL 数据查询与图表展示完整指南

## 问题描述

用户希望通过自然语言提问："从 MySQL 数据库中查询疾病类型分布，并用饼状图展示"，React Agent 能够自动执行以下流程：

1. 查找 MySQL 中存在哪些表
2. 根据表名和字段确定要查询哪个表
3. 编写并执行相应的 SQL 语句
4. 获取查询结果后，调用 chart 工具生成饼状图

## 系统架构

### 1. 已有的工具能力

您的系统**已经完全支持**这个工作流，包含以下工具：

#### MySQL 工具 (内置)
位于 `src/agents/common/toolkits/mysql/tools.py`

- **`mysql_list_tables`**: 列出数据库中所有表名及行数
- **`mysql_describe_table`**: 查看指定表的详细结构（字段、类型、索引等）
- **`mysql_query`**: 执行只读 SQL 查询（自动安全检查、限制行数、超时控制）

#### Chart 工具 (MCP 服务)
位于 `src/agents/common/mcp.py` 配置的 `mcp-server-chart`

- **`generate_pie_chart`**: 生成饼状图
- 其他 24 种图表类型（柱状图、折线图、散点图等）

### 2. React Agent 工作原理

React Agent 的实现位于 `src/agents/react/graph.py`，它：

1. 使用 LangGraph 的 `create_react_agent` 创建
2. 自动加载所有内置工具（包括 MySQL 工具）
3. 根据配置动态加载 MCP 工具（包括 chart 工具）
4. 采用 ReAct (Reason + Act) 模式：
   - **Reason**: 分析用户问题，制定计划
   - **Act**: 调用相应工具执行任务
   - **Observe**: 观察工具返回结果
   - **循环**: 重复上述过程直到完成任务

## 配置步骤

### 步骤 1: 启用 Chart MCP 服务

在前端 Agent 配置界面中：

1. 打开 React Agent 配置侧边栏
2. 找到 "MCP 服务器" 配置项（mcps）
3. 在多选卡片中选择 `mcp-server-chart`
4. 保存配置

配置位置：
- 后端配置文件: `saves/config/agents/ReActAgent/context.json`
- 配置结构:
```json
{
  "mcps": ["mcp-server-chart"]
}
```

### 步骤 2: 确保 MySQL 连接正确

检查 Docker 环境变量（在 `docker-compose.yml` 或 `.env` 文件中）：

```env
MYSQL_HOST=mysql-dev
MYSQL_USER=testuser
MYSQL_PASSWORD=testpassword
MYSQL_DATABASE=testdb
MYSQL_PORT=3306
```

### 步骤 3: 准备测试数据

确保 MySQL 中有测试数据。例如，使用现有的导入功能：

```bash
# 使用前端的 MySQL 导入功能
# 或通过 API 导入：
POST http://localhost:5050/api/knowledge/mysql/import
{
  "file_path": "/path/to/patient_data.xlsx",
  "table_name": "patients",
  "create_table": true
}
```

## 使用示例

### 示例 1: 疾病类型分布饼状图

**用户提问**:
```
从 MySQL 数据库中查询疾病类型分布，并用饼状图展示
```

**React Agent 执行流程**:

1. **调用 `mysql_list_tables`**
   ```
   工具返回：
   数据库中的表:
   - patients (约 50 行)
   - employees (约 100 行)
   ```

2. **调用 `mysql_describe_table(table_name="patients")`**
   ```
   工具返回：
   表 `patients` 的结构:
   字段名          类型            NULL    键    默认值
   --------------------------------------------------------------------------------
   id              BIGINT          NO      PRI
   patient_name    VARCHAR(255)    YES
   disease_type    VARCHAR(255)    YES
   diagnosis_date  DATE            YES
   ```

3. **调用 `mysql_query`**
   ```sql
   SELECT disease_type, COUNT(*) as count
   FROM patients
   GROUP BY disease_type
   ```

   工具返回：
   ```
   | disease_type | count |
   |--------------|-------|
   | 糖尿病        | 15    |
   | 高血压        | 20    |
   | 冠心病        | 10    |
   | 其他          | 5     |
   ```

4. **调用 `generate_pie_chart`**
   ```json
   {
     "title": "疾病类型分布",
     "data": [
       {"category": "糖尿病", "value": 15},
       {"category": "高血压", "value": 20},
       {"category": "冠心病", "value": 10},
       {"category": "其他", "value": 5}
     ]
   }
   ```

5. **返回图表 URL 给用户**

### 示例 2: 其他查询场景

**场景：月度就诊趋势折线图**
```
查询最近 6 个月的就诊人数趋势，用折线图展示
```

Agent 会：
1. 列出表
2. 查看表结构（找到日期字段）
3. 执行 SQL: `SELECT DATE_FORMAT(diagnosis_date, '%Y-%m') as month, COUNT(*) FROM patients GROUP BY month`
4. 调用 `generate_line_chart`

**场景：年龄分布直方图**
```
查询患者年龄分布情况
```

Agent 会：
1. 查看表结构（找到年龄字段）
2. 执行 SQL 获取年龄数据
3. 调用 `generate_histogram_chart`

## 优化建议

### 1. 增强 System Prompt

如果发现 Agent 不能很好地理解任务，可以在 React Agent 的配置中添加更详细的系统提示：

编辑 `saves/config/agents/ReActAgent/context.json`:

```json
{
  "system_prompt": "你是一个数据分析助手，擅长查询 MySQL 数据库并生成可视化图表。\n\n工作流程：\n1. 当用户询问数据库相关问题时，首先使用 mysql_list_tables 查看所有表\n2. 使用 mysql_describe_table 查看相关表的结构\n3. 根据表结构编写并执行 SQL 查询\n4. 如果用户要求可视化，根据数据类型选择合适的图表工具（饼图、柱状图、折线图等）\n5. 生成图表并返回给用户\n\n重要提示：\n- 每次用户提问时都要重新调用工具，不要依赖之前的查询结果\n- SQL 查询要根据具体需求灵活调整（GROUP BY、聚合函数等）\n- 选择合适的图表类型来展示数据",
  "mcps": ["mcp-server-chart"]
}
```

### 2. 添加示例对话

可以在前端展示一些示例问题，帮助用户更好地使用：

```markdown
📊 MySQL 数据分析示例：

1. "查询疾病类型分布，用饼状图展示"
2. "统计各科室的就诊人数，用柱状图对比"
3. "分析最近 3 个月的就诊趋势"
4. "查看患者年龄分布情况"
5. "展示不同治疗方式的效果对比"
```

### 3. 测试工具可用性

可以通过以下命令测试工具是否正常加载：

```bash
# 测试 MySQL 工具
docker exec api-dev python -c "
from src.agents.common.tools import get_mysql_tools
tools = get_mysql_tools()
print(f'MySQL Tools: {len(tools)}')
for t in tools:
    print(f'  - {t.name}: {t.description[:50]}...')
"

# 测试 Chart MCP 工具
docker exec api-dev python -c "
import asyncio
from src.agents.common.mcp import get_mcp_tools
tools = asyncio.run(get_mcp_tools('mcp-server-chart'))
print(f'Chart Tools: {len(tools)}')
for t in tools:
    if 'pie' in t.name or 'bar' in t.name:
        print(f'  - {t.name}')
"
```

### 4. 监控执行过程

在前端聊天界面中，可以看到 Agent 的思考过程和工具调用：

```
思考中...
📋 正在查询数据库表列表
✅ 找到 2 个表

📋 正在查看 patients 表结构
✅ 表包含 4 个字段

📋 正在执行 SQL 查询
✅ 查询返回 4 行结果

📊 正在生成饼状图
✅ 图表生成完成
```

## 常见问题

### Q1: Agent 不调用工具怎么办？

**可能原因**:
- MCP 服务未启用
- System prompt 不够明确
- 模型能力不足

**解决方案**:
1. 确认 `mcp-server-chart` 已在配置中启用
2. 增强 system prompt，明确工作流程
3. 使用更强的模型（如 qwen-max、gpt-4 等）

### Q2: Chart 工具调用失败

**可能原因**:
- MCP 服务器连接问题
- 数据格式不正确

**解决方案**:
1. 检查 MCP 服务器状态
2. 查看 Agent 日志: `docker logs api-dev | grep mcp-server-chart`
3. 确保传递给 chart 工具的数据格式正确

### Q3: SQL 查询返回结果过大

**内置保护机制**:
- 默认限制返回 100 行
- 最大显示 10000 字符
- 自动截断并提示

**解决方案**:
在用户问题中加入更多过滤条件，例如：
- "查询最近一个月的数据"
- "只展示前 10 个疾病类型"

### Q4: Agent 找不到正确的表或字段

**可能原因**:
- 表名或字段名不符合预期
- 数据库中没有相关数据

**解决方案**:
1. 让用户先询问："数据库中有哪些表？"
2. 然后询问："patients 表的结构是什么？"
3. 最后再进行具体查询

## 技术细节

### React Agent 的工具选择逻辑

React Agent 使用 LLM 的 function calling 能力来选择工具：

1. **输入**: 用户问题 + 可用工具列表（含描述）
2. **LLM 推理**: 分析问题，决定需要调用哪个工具
3. **工具执行**: 调用选定的工具，获取结果
4. **结果评估**: 判断是否需要调用更多工具
5. **循环**: 重复 2-4 直到任务完成

### 工具描述的重要性

工具的 `description` 字段对 Agent 的工具选择至关重要：

```python
@tool(args_schema=TableListModel)
def mysql_list_tables() -> str:
    """获取数据库中的所有表名

    这个工具用来列出当前数据库中所有的表名，帮助你了解数据库的结构。
    """
    # ...
```

清晰的描述能帮助 LLM 更准确地选择工具。

### 安全机制

MySQL 工具内置了多层安全保护：

1. **SQL 注入防护** (`src/agents/common/toolkits/mysql/security.py`)
   - 只允许 SELECT 语句
   - 阻止 DROP、DELETE、UPDATE 等危险操作
   - 验证表名和字段名

2. **资源限制**
   - 默认限制 100 行
   - 最大 1000 行
   - 查询超时（默认 10 秒，最大 60 秒）

3. **连接管理**
   - 使用连接池
   - 自动重连
   - 错误处理

## 总结

您的系统已经具备完整的能力来执行 "查询 MySQL → 生成图表" 的工作流。只需要：

1. ✅ 在前端配置中启用 `mcp-server-chart`
2. ✅ 确保 MySQL 连接配置正确
3. ✅ 准备测试数据
4. ✅ 使用清晰的自然语言提问

React Agent 会自动：
- 🔍 探索数据库结构
- 📝 编写合适的 SQL 查询
- 📊 选择合适的图表类型
- 🎨 生成可视化结果

无需任何额外开发！整个流程由 Agent 的推理能力自动完成。

## 下一步

1. 测试基本功能是否正常
2. 根据实际使用情况优化 system prompt
3. 考虑添加更多 MCP 工具（如数据处理、统计分析等）
4. 收集用户反馈，持续改进
