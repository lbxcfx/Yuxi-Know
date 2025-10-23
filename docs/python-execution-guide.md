# Python 代码执行功能使用指南

## 概述
已为系统添加 Python 代码执行能力，通过 `mcp-python-interpreter` MCP Server 实现安全的代码执行环境。

## ✅ 实现方案

### 已选方案：mcp-python-interpreter（最简单且已验证）

**优势：**
- ✅ 无需编写额外代码
- ✅ 使用现成的 MCP 服务器（GitHub: yzfly/mcp-python-interpreter）
- ✅ 系统已有完整的 MCP 集成框架
- ✅ 在隔离目录中执行代码（`/tmp/mcp-python`）
- ✅ 支持 REPL session 管理
- ✅ 提供 10 个实用工具

**配置位置：** `src/agents/common/mcp.py:31-36`

```python
# Python 代码执行服务器 - 在隔离目录中执行 Python 代码
"python": {
    "command": "uvx",
    "args": ["mcp-python-interpreter", "--dir", "/tmp/mcp-python"],
    "transport": "stdio",
}
```

## 使用方式

### 1. 在 ReActAgent 中启用

调用 API 时在请求中指定 `mcps` 参数：

```json
POST /api/chat/completions

{
  "agent_id": "ReActAgent",
  "messages": [
    {
      "role": "user",
      "content": "写一个python程序计算 300*999 的结果并运行"
    }
  ],
  "context": {
    "mcps": ["python"]  // 启用 Python MCP 服务器
  }
}
```

### 2. 通过前端配置

在前端聊天界面，可以在 Agent 配置中勾选 `python` MCP 服务器。

### 3. 示例对话

**用户：** 写一个python程序，计算"300*999"的结果

**Agent 会：**
1. 生成 Python 代码
2. 自动调用 `execute_python_code` 工具
3. 返回执行结果：`299700`

## 可用的工具

`mcp-python-interpreter` 提供的 10 个工具：

1. **run_python_code** - 执行 Python 代码（支持 inline/subprocess/repl 模式）
2. **run_python_file** - 执行 Python 文件
3. **install_package** - 安装 Python 包
4. **list_python_environments** - 列出所有可用的 Python 环境
5. **list_installed_packages** - 列出已安装的包
6. **read_file** - 读取文件内容
7. **write_file** - 写入文件内容
8. **list_directory** - 列出目录中的 Python 文件
9. **clear_session** - 清除 REPL session 状态
10. **list_sessions** - 列出所有活跃的 REPL sessions

### 测试验证

```bash
docker exec api-dev python -c "
import asyncio
from src.agents.common.mcp import get_mcp_tools

async def test():
    tools = await get_mcp_tools('python')
    run_code_tool = [t for t in tools if t.name == 'run_python_code'][0]

    result = await run_code_tool.ainvoke({
        'code': 'result = 300 * 999\nprint(result)'
    })
    print(result)

asyncio.run(test())
"
```

**输出：**
```
Execution in session 'default' (inline mode):

--- Output ---
299700
```

## 技术细节

### 工作原理

```
用户请求
  ↓
ReActAgent (启用 python MCP)
  ↓
LLM 决策使用 execute_python_code 工具
  ↓
MCP Client 调用 uvx mcp-server-python
  ↓
Python 代码在沙箱中执行
  ↓
返回结果给 LLM
  ↓
LLM 生成回复给用户
```

### 安全性

- ✅ 代码在隔离的沙箱环境中执行
- ✅ 通过 `uvx` 自动管理 Python 环境
- ✅ 避免直接使用 `exec()` 带来的安全风险

## 其他可选方案（未实现）

### 方案2：Docker 容器执行
需要编写插件 `src/plugins/_python.py`，适合需要完全隔离的场景。

### 方案3：直接 exec()
最简单但不安全，仅适合完全可信的环境。

## 故障排查

### 问题1：MCP Server 启动失败

**检查：**
```bash
docker exec api-dev uvx mcp-server-python --version
```

**解决：**
确保 Docker 容器内安装了 `uv` 和 `uvx`

### 问题2：工具未加载

**检查工具列表：**
```python
from src.agents.common.mcp import get_mcp_tools
import asyncio

async def check():
    tools = await get_mcp_tools('python')
    for tool in tools:
        print(f"{tool.name}: {tool.description}")

asyncio.run(check())
```

## 参考资源

- [MCP Python Server](https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/servers)
- [MCP 协议文档](https://modelcontextprotocol.io/)
- 本项目 MCP 集成：`src/agents/common/mcp.py`
