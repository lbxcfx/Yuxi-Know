from dataclasses import dataclass, field
from typing import Annotated

from src.agents.common.context import BaseContext
from src.agents.common.mcp import MCP_SERVERS


@dataclass(kw_only=True)
class Context(BaseContext):
    """ReAct Agent 的上下文配置，支持 MCP 服务"""

    mcps: list[str] = field(
        default_factory=list,
        metadata={"name": "MCP服务器", "options": list(MCP_SERVERS.keys()), "description": "MCP服务器列表"},
    )
