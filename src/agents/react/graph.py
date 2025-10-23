from pathlib import Path

from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.runtime import get_runtime

from src import config as sys_config
from src.agents.common.base import BaseAgent
from src.agents.common.mcp import get_mcp_tools
from src.agents.common.models import load_chat_model
from src.agents.common.tools import get_buildin_tools
from src.utils import logger

from .context import Context

model = load_chat_model("dashscope/qwen-max")


def prompt(state) -> list[AnyMessage]:
    runtime = get_runtime(Context)
    enhanced_prompt = f"""{runtime.context.system_prompt}

IMPORTANT TOOL USAGE RULES:
- For EVERY new user question, you MUST call the relevant tools again, even if similar information was retrieved in previous messages.
- Do NOT rely on tool results from previous questions in the conversation history.
- Always make fresh tool calls to ensure the most accurate and up-to-date information.
- When the user asks about knowledge graph, knowledge base, or web search, ALWAYS call the corresponding tools.
"""
    system_msg = SystemMessage(content=enhanced_prompt)
    return [system_msg] + state["messages"]


class ReActAgent(BaseAgent):
    name = "ReAct (all tools)"
    description = "A react agent that can answer questions and help with tasks."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.graph = None
        self.workdir = Path(sys_config.save_dir) / "agents" / self.module_name
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.context_schema = Context

    async def get_graph(self, input_context=None, **kwargs):
        # Load configuration to get MCP servers
        context = Context.from_file(module_name=self.module_name, input_context=input_context)

        # Check if we need to rebuild the graph based on mcps configuration
        current_mcps = tuple(sorted(context.mcps)) if context.mcps else ()
        cached_mcps = getattr(self, '_cached_mcps', None)

        # Return cached graph only if mcps configuration hasn't changed
        if self.graph and cached_mcps == current_mcps:
            return self.graph

        # Get builtin tools
        available_tools = get_buildin_tools()

        # Load MCP tools if configured
        if context.mcps and isinstance(context.mcps, list) and len(context.mcps) > 0:
            for mcp in context.mcps:
                mcp_tools = await get_mcp_tools(mcp)
                available_tools.extend(mcp_tools)
                logger.info(f"Loaded {len(mcp_tools)} tools from MCP server '{mcp}'")

        logger.info(f"ReActAgent initialized with {len(available_tools)} total tools")

        self.checkpointer = await self._get_checkpointer()

        # 创建 ReActAgent
        graph = create_react_agent(model, tools=available_tools, prompt=prompt, checkpointer=self.checkpointer)
        self.graph = graph
        self._cached_mcps = current_mcps
        logger.info(f"ReActAgent built with mcps={current_mcps}")
        return graph
