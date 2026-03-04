# OpenAI Agents SDK 文档

**版本**: 0.10.3 (Python)
**文档地址**: https://openai.github.io/openai-agents-python/
**GitHub**: https://github.com/openai/openai-agents-python

---

## 1. 概述

OpenAI Agents SDK 是一个轻量但强大的多智能体（Multi-Agent）工作流框架，使用 Python 或 JavaScript/TypeScript 构建。它与提供商无关，支持 OpenAI APIs 及更多。

### 1.1 核心特性

| 特性 | 描述 |
|------|------|
| **多智能体工作流** | 在单个工作流中组合和编排多个智能体 |
| **工具集成** | 从智能体响应中无缝调用工具/函数 |
| **Handoffs** | 在运行期间动态在智能体之间转移控制权 |
| **结构化输出** | 支持纯文本和 Schema 验证的结构化输出 |
| **流式响应** | 实时流式传输智能体输出和事件 |
| **Tracing & 调试** | 内置追踪功能，可视化和调试智能体运行 |
| **Guardrails** | 输入和输出的安全验证 |
| **并行化** | 并行运行智能体或工具调用并聚合结果 |
| **Human-in-the-Loop** | 将人工批准或干预集成到工作流中 |
| **实时语音智能体** | 使用 WebRTC 或 WebSockets 构建实时语音智能体 |
| **MCP 服务器支持** | 让智能体访问本地运行的 MCP 服务器提供工具 |
| **广泛模型支持** | 通过 Vercel AI SDK 适配器使用非 OpenAI 模型 |

### 1.2 支持的环境

- **Node.js** 22+
- **Deno**
- **Bun**
- **Cloudflare Workers** (实验性)

### 1.3 安装

```bash
# Python
pip install openai-agents

# JavaScript/TypeScript
npm install @openai/agents zod
```

---

## 2. 核心概念

### 2.1 Agent（智能体）

Agent 是配置了指令、工具、Guardrails 和 Handoffs 的 LLM。

```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
)

result = await Runner.run(
    agent,
    "Write a haiku about recursion in programming.",
)
print(result.finalOutput)
```

#### Agent 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `name` | str | 智能体名称 |
| `handoff_description` | str | 人类可读的描述，用于 handoffs |
| `tools` | list[Tool] | 智能体可用的工具列表 |
| `mcp_servers` | list[MCPServer] | MCP 服务器列表 |
| `instructions` | str / Callable | 系统提示词 |
| `handoffs` | list[Handoff] | 可转交的智能体列表 |
| `model` | str / Model | 使用的模型 |
| `model_settings` | ModelSettings | 模型设置 |
| `input_guardrails` | list[InputGuardrail] | 输入 Guardrails |
| `output_guardrails` | list[OutputGuardrail] | 输出 Guardrails |
| `output_type` | type | 输出类型（结构化输出） |
| `hooks` | AgentHooks | 生命周期钩子 |
| `tool_use_behavior` | str | 工具使用行为 |

### 2.2 Runner（运行器）

Runner 负责执行智能体工作流。

```python
# 同步运行
result = await Runner.run(starting_agent, input)

# 流式运行
result = await Runner.run_streamed(starting_agent, input)
async for event in result.stream_events():
    print(event)
```

#### Runner.run() 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `starting_agent` | Agent | 起始智能体 |
| `input` | str / list / RunState | 输入内容 |
| `context` | TContext | 上下文对象 |
| `max_turns` | int | 最大轮次（默认 10） |
| `hooks` | RunHooks | 运行时钩子 |
| `run_config` | RunConfig | 运行时配置 |
| `conversation_id` | str | 对话 ID |
| `session` | Session | 会话用于历史管理 |

---

## 3. Tools（工具）

### 3.1 function_tool 装饰器

使用 `@function_tool` 装饰器创建自定义工具。

```python
from agents import function_tool

@function_tool
def get_weather(location: str) -> str:
    """Get the weather for a location.

    Args:
        location: The location to get weather for.
    """
    # 实现逻辑
    return f"The weather in {location} is sunny."

# 或使用异步
@function_tool
async def get_weather_async(location: str) -> str:
    """Get the weather for a location (async)."""
    # 异步实现逻辑
    return f"The weather in {location} is sunny."
```

#### function_tool 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `name_override` | str | 工具名称覆盖 |
| `description_override` | str | 工具描述覆盖 |
| `docstring_style` | str | 文档字符串风格 |
| `use_docstring_info` | bool | 使用文档填充描述 |
| `failure_error_function` | Callable | 工具失败时的错误处理 |
| `strict_mode` | bool | 严格模式（默认 True） |
| `is_enabled` | bool / Callable | 工具是否启用 |
| `needs_approval` | bool / Callable | 是否需要人工批准 |
| `tool_input_guardrails` | list | 工具输入 Guardrails |
| `tool_output_guardrails` | list | 工具输出 Guardrails |
| `timeout` | float | 超时时间（秒） |

### 3.2 内置工具

#### ShellTool

```python
from agents import ShellTool

shell = ShellTool()

agent = Agent(
    name="Shell Assistant",
    tools=[shell],
)
```

#### FileSearchTool

```python
from agents import FileSearchTool

file_search = FileSearchTool(
    directory="./my-project",
)

agent = Agent(
    name="File Assistant",
    tools=[file_search],
)
```

#### WebSearchTool

```python
from agents import WebSearchTool

web_search = WebSearchTool()

agent = Agent(
    name="Web Search Assistant",
    tools=[web_search],
)
```

#### CodeInterpreterTool

```python
from agents import CodeInterpreterTool

code_interpreter = CodeInterpreterTool()

agent = Agent(
    name="Code Assistant",
    tools=[code_interpreter],
)
```

### 3.3 工具作为智能体

将智能体转换为工具，供其他智能体调用。

```python
# 创建智能体
research_agent = Agent(
    name="Researcher",
    instructions="You research topics thoroughly.",
)

# 转换为工具
research_tool = research_agent.as_tool(
    tool_name="research",
    tool_description="Research a topic thoroughly.",
)

# 在另一个智能体中使用
main_agent = Agent(
    name="Main Agent",
    tools=[research_tool],
)
```

---

## 4. Handoffs（智能体转交）

Handoffs 允许智能体在运行期间动态将控制权转交给其他智能体。

### 4.1 创建 Handoff

```python
from agents import Agent, handoff

# 创建两个智能体
agent_a = Agent(name="Agent A", instructions="You are agent A.")
agent_b = Agent(name="Agent B", instructions="You are agent B.")

# 将 agent_b 添加为 agent_a 的 handoff
agent_a.handoffs = [
    handoff(agent_b, tool_name_override="transfer_to_b")
]
```

### 4.2 Handoff 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `agent` | Agent | 目标智能体 |
| `tool_name_override` | str | 工具名称覆盖 |
| `tool_description_override` | str | 工具描述覆盖 |
| `on_handoff` | Callable | 转交时执行的回调 |
| `input_type` | type | 输入类型验证 |
| `input_filter` | Callable | 输入过滤器 |
| `nest_handoff_history` | bool | 是否嵌套转交历史 |
| `is_enabled` | bool / Callable | 是否启用 |

### 4.3 示例：多智能体协作

```python
from agents import Agent, handoff, Runner

# 创建专业智能体
research_agent = Agent(
    name="Researcher",
    instructions="You research topics thoroughly and provide detailed reports.",
)

writing_agent = Agent(
    name="Writer",
    instructions="You write clear, engaging content based on research.",
)

# 配置转交
research_agent.handoffs = [
    handoff(writing_agent, tool_name_override="hand_off_to_writer")
]

# 运行
result = await Runner.run(research_agent, "Research AI and write an article.")
```

---

## 5. Guardrails（安全护栏）

Guardrails 用于验证输入和输出的安全性。

### 5.1 Input Guardrail

```python
from agents import input_guardrail, RunContextWrapper
from pydantic import BaseModel

class SensitiveInfo(BaseModel):
    has_sensitive_data: bool
    sensitive_type: str | None = None

@input_guardrail
def check_sensitive_info(context: RunContextWrapper, agent: Agent) -> SensitiveInfo:
    """Check if the input contains sensitive information."""
    user_input = context.messages[-1].content

    sensitive_patterns = ["password", "secret", "api_key"]
    for pattern in sensitive_patterns:
        if pattern in user_input.lower():
            return SensitiveInfo(has_sensitive_data=True, sensitive_type=pattern)

    return SensitiveInfo(has_sensitive_data=False)

# 在智能体中使用
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    input_guardrails=[check_sensitive_info],
)
```

### 5.2 Output Guardrail

```python
from agents import output_guardrail, RunContextWrapper

@output_guardrail
def validate_output(context: RunContextWrapper, agent: Agent, output: str) -> None:
    """Validate the output doesn't contain sensitive data."""
    if "password" in output.lower():
        raise ValueError("Output contains sensitive information")
```

### 5.3 Guardrail 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `name` | str | Guardrail 名称 |
| `run_in_parallel` | bool | 是否与智能体并行运行 |

---

## 6. 会话与存储

### 6.1 SQLiteSession

使用 SQLite 持久化会话历史。

```python
from agents import Agent, Runner, SQLiteSession

# 创建持久化会话
session = SQLiteSession(
    session_id="my-session",
    db_path="./data/sessions.db",
)

# 运行智能体
agent = Agent(name="Assistant", instructions="You are helpful.")
result = await Runner.run(agent, "Hello!", session=session)

# 获取历史
history = await session.get_items()
```

#### SQLiteSession 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `session_id` | str | 会话唯一标识 |
| `db_path` | str / Path | 数据库文件路径 |
| `sessions_table` | str | 会话表名 |
| `messages_table` | str | 消息表名 |
| `session_settings` | SessionSettings | 会话设置 |

### 6.2 Session 方法

```python
# 添加消息
await session.add_items([message_item])

# 获取历史
items = await session.get_items(limit=10)

# 弹出最后一条
item = await session.pop_item()

# 清空会话
await session.clear_session()

# 关闭连接
session.close()
```

---

## 7. 流式响应

### 7.1 基本使用

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are helpful.")

result = await Runner.run_streamed(agent, "Tell me a story.")

async for event in result.stream_events():
    if event.type == "agent_update":
        print(event.data.delta)
    elif event.type == "tool_call":
        print(f"Tool: {event.tool_name}")
```

### 7.2 事件类型

| 事件类型 | 描述 |
|----------|------|
| `agent_update` | 智能体更新 |
| `tool_call` | 工具调用 |
| `tool_call_started` | 工具调用开始 |
| `tool_call_completed` | 工具调用完成 |
| `handoff` | 智能体转交 |
| `guardrail` | Guardrail 检查 |

---

## 8. Tracing（追踪）

### 8.1 基本配置

```python
from agents import set_trace_provider, TracingProcessor
from openai import OpenAI

# 设置追踪
set_trace_provider(
    TracingProcessor(
        client=OpenAI(api_key="your-api-key"),
        project_name="my-project",
    )
)
```

### 8.2 内置追踪

SDK 自动追踪：
- 智能体运行
- 工具调用
- Handoffs
- Guardrail 检查

---

## 9. MCP（Model Context Protocol）

### 9.1 MCP 服务器

```python
from agents import Agent
from agents.mcp import MCPServerStdio

# 创建 MCP 服务器
mcp_server = MCPServerStdio(
    params=MCPServerStdioParams(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "./data"],
    )
)

# 在智能体中使用
agent = Agent(
    name="Assistant",
    mcp_servers=[mcp_server],
)
```

### 9.2 MCP 服务器类型

| 类型 | 描述 |
|------|------|
| `MCPServerStdio` | STDIO 协议（本地进程） |
| `MCPServerSse` | SSE（Server-Sent Events） |
| `MCPServerStreamableHttp` | HTTP 流式 |

---

## 10. 完整示例

### 10.1 多智能体客服系统

```python
from agents import Agent, Runner, function_tool, handoff, SQLiteSession

# 1. 定义工具
@function_tool
def get_order_status(order_id: str) -> str:
    """Get the status of an order."""
    return f"Order {order_id} is shipped."

@function_tool
def refund_order(order_id: str) -> str:
    """Process a refund for an order."""
    return f"Refund processed for order {order_id}."

# 2. 创建智能体
triage_agent = Agent(
    name="Triage",
    instructions="""You are a customer service triage agent.
    Determine if the user wants to check order status or request a refund.""",
)

order_agent = Agent(
    name="Order Support",
    instructions="You help users with order-related questions.",
    tools=[get_order_status],
)

refund_agent = Agent(
    name="Refund Agent",
    instructions="You help users process refunds.",
    tools=[refund_order],
)

# 3. 配置 Handoffs
order_agent.handoffs = [handoff(refund_agent)]
triage_agent.handoffs = [handoff(order_agent), handoff(refund_agent)]

# 4. 运行
session = SQLiteSession(session_id="customer-123", db_path="./support.db")

result = await Runner.run(
    triage_agent,
    "I want to check my order #12345",
    session=session,
)

print(result.final_output)
```

### 10.2 带 Guardrail 的智能体

```python
from agents import Agent, Runner, input_guardrail, output_guardrail
from pydantic import BaseModel

class ToxicContent(BaseModel):
    is_toxic: bool
    reason: str | None = None

@input_guardrail
def check_toxic_input(context, agent) -> ToxicContent:
    """Check for toxic content in input."""
    text = context.messages[-1].content
    toxic_words = ["hate", "violence"]

    for word in toxic_words:
        if word in text.lower():
            return ToxicContent(is_toxic=True, reason=f"Contains '{word}'")

    return ToxicContent(is_toxic=False)

agent = Agent(
    name="Safe Assistant",
    instructions="You are a helpful assistant.",
    input_guardrails=[check_toxic_input],
)

result = await Runner.run(agent, "Hello, how are you?")
```

---

## 11. 最佳实践

### 11.1 智能体设计

1. **单一职责**: 每个智能体只负责一个特定任务
2. **清晰指令**: 使用详细的 `instructions` 描述智能体角色
3. **适当工具**: 只给智能体必要的工具
4. **Handoffs**: 使用 Handoffs 连接相关智能体

### 11.2 工具开发

1. **文档字符串**: 为每个工具编写清晰的文档字符串
2. **错误处理**: 使用 `failure_error_function` 处理工具错误
3. **类型提示**: 使用类型提示让 LLM 更好理解参数
4. **批准机制**: 对敏感操作使用 `needs_approval`

### 11.3 安全

1. **Input Guardrails**: 验证用户输入
2. **Output Guardrails**: 验证输出内容
3. **工具超时**: 为长时间运行的工具设置超时
4. **敏感数据**: 避免在日志中暴露敏感信息

### 11.4 性能

1. **会话复用**: 复用 Session 减少开销
2. **流式处理**: 对长时间运行使用流式响应
3. **并行工具**: 使用并行工具调用
4. **适当轮次**: 设置合理的 `max_turns`

---

## 12. API 参考

### 12.1 核心类

| 类 | 描述 |
|---|------|
| `Agent` | 智能体配置 |
| `Runner` | 智能体运行器 |
| `Session` | 会话基类 |
| `SQLiteSession` | SQLite 会话实现 |
| `RunResult` | 运行结果 |
| `RunResultStreaming` | 流式运行结果 |

### 12.2 装饰器

| 装饰器 | 描述 |
|--------|------|
| `@function_tool` | 创建工具 |
| `@handoff` | 创建智能体转交 |
| `@input_guardrail` | 创建输入 Guardrail |
| `@output_guardrail` | 创建输出 Guardrail |

### 12.3 工具

| 工具 | 描述 |
|------|------|
| `ShellTool` | Shell 命令执行 |
| `FileSearchTool` | 文件搜索 |
| `WebSearchTool` | 网页搜索 |
| `CodeInterpreterTool` | 代码解释器 |

---

## 13. 参考资料

- [官方文档](https://openai.github.io/openai-agents-python/)
- [GitHub 仓库](https://github.com/openai/openai-agents-python)
- [JavaScript/TypeScript SDK](https://github.com/openai/openai-agents-js)
- [示例代码](https://github.com/openai/openai-agents-python/tree/main/examples)
