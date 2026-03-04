# OpenAI Agents SDK 中文文档

## 目录

- [简介](#简介)
- [安装](#安装)
- [快速开始](#快速开始)
- [Agent 类](#agent-类)
- [Runner 执行器](#runner-执行器)
- [Tools 工具](#tools-工具)
- [Handoffs 交接](#handoffs-交接)
- [Guardrails 安全护栏](#guardrails-安全护栏)
- [MCP 支持](#mcp-支持)
- [流式输出](#流式输出)
- [追踪功能](#追踪功能)
- [配置选项](#配置选项)

---

## 简介

OpenAI Agents SDK 是一个轻量级、易于使用的智能代理 AI 应用程序构建包。基于之前的 Swarm 实验项目升级而来。

### 核心组件

- **智能代理 (Agent)**：配备指令和工具的大语言模型（LLM）
- **交接/切换 (Handoffs)**：将任务委托给其他智能代理
- **安全护栏 (Guardrails)**：对输入数据进行验证

### 主要功能

- 智能体循环：自动调用工具、将结果发送给 LLM，直至任务完成
- Python 优先：利用 Python 内置特性编排智能体
- 函数工具：将任意 Python 函数转换为工具
- 追踪功能：内置可视化、调试和监控工作流程

---

## 安装

```bash
pip install openai-agents
```

### 环境变量

```bash
export OPENAI_API_KEY=sk-...
```

---

## 快速开始

### Hello World

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haika about recursion in programming.")
print(result.final_output)
```

---

## Agent 类

### 基本参数

```python
from agents import Agent

agent = Agent(
    name="Assistant",           # 智能体名称
    instructions="你是一个有用的助手",  # 指令（系统提示词）
    model="gpt-4o",            # 使用的模型
    tools=[],                   # 工具列表
    output_type=str,            # 输出类型
    handoffs=[],                # 可交接的子智能体
    input_guardrails=[],        # 输入安全护栏
    output_guardrails=[],       # 输出安全护栏
)
```

### 参数详解

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | str | 智能体名称 |
| `instructions` | str | 指令（开发者消息/系统提示词） |
| `model` | str | 使用的 LLM，默认 "gpt-4o" |
| `tools` | list | 智能体可用的工具列表 |
| `output_type` | type | 输出类型（Pydantic/数据类/列表/TypedDict） |
| `handoffs` | list | 可交接给的其他智能体 |
| `input_guardrails` | list | 输入安全护栏 |
| `output_guardrails` | list | 输出安全护栏 |

### 动态指令

可通过函数提供动态指令：

```python
def get_instructions(ctx, agent):
    return f"当前用户: {ctx.user_id}"

agent = Agent(
    name="Dynamic agent",
    instructions=get_instructions,
)
```

### 克隆智能体

```python
cloned_agent = agent.clone()
cloned_agent.name = "Cloned agent"
```

---

## Runner 执行器

### 同步执行

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="你是一个有用的助手")

# 同步执行
result = Runner.run_sync(agent, "你的问题")
print(result.final_output)
```

### 异步执行

```python
import asyncio
from agents import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="你是一个有用的助手")
    result = await Runner.run(agent, "你的问题")
    print(result.final_output)

asyncio.run(main())
```

### run() 方法参数

```python
Runner.run(
    agent,              # Agent 实例
    input,              # 用户输入
    context=None,       # 上下文对象
    run_config=None,    # 运行配置
)
```

### RunConfig 配置

```python
from agents import RunConfig

config = RunConfig(
    model="gpt-4o",
    model_settings=ModelSettings(
        temperature=0.5,
        top_p=0.9,
    ),
    tracing_disabled=False,
    trace_include_sensitive_data=True,
)
```

---

## Tools 工具

### 三种工具类型

1. **Managed Tools**: OpenAI 内置工具 (WebSearchTool, FileSearchTool, ComputerTool)
2. **Function Tools**: 任意 Python 函数转换为工具
3. **Agent as Tool**: 将智能体作为工具使用

### @function_tool 装饰器

将 Python 函数转换为工具：

```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """获取指定城市的天气。

    Args:
        city: 城市名称
    """
    return f"{city} 的天气是晴天"

agent = Agent(
    name="Weather agent",
    instructions="使用工具获取天气信息",
    tools=[get_weather],
)
```

### 工具特性

- 工具名称 = 函数名称（可通过 `name_override` 覆盖）
- 描述来自 docstring（可覆盖）
- 参数 schema 从函数签名自动生成
- 参数描述来自 docstring

### 异步工具

```python
@function_tool
async def fetch_data(url: str) -> str:
    response = await aiohttp.get(url)
    return await response.text()
```

### 错误处理

```python
@function_tool(failure_error_function=lambda e: str(e))
def risky_function():
    # 可能失败的函数
    pass
```

### Agent as Tool

将智能体作为工具使用（不进行交接）：

```python
spanish_agent = Agent(
    name="Spanish agent",
    instructions="Translate to Spanish"
)

orchestrator = Agent(
    name="orchestrator",
    tools=[spanish_agent.as_tool(
        tool_name="translate_to_spanish",
        tool_description="Translate text to Spanish",
    )]
)
```

### 手动创建 FunctionTool

```python
from agents import FunctionTool

tool = FunctionTool(
    name="处理用户数据",
    description="处理提取的用户数据",
    params_json_schema=MyArgs.model_json_schema(),
    on_invoke_tool=run_function,
)
```

---

## Handoffs 交接

### 基本用法

交接允许一个智能体将任务委托给另一个智能体：

```python
from agents import Agent, handoff

billing_agent = Agent(name="Billing agent")
refund_agent = Agent(name="Refund agent")

triage_agent = Agent(
    name="Triage agent",
    handoffs=[billing_agent, handoff(refund_agent)]
)
```

### handoff() 函数参数

```python
handoff(
    agent,                          # 交接目标智能体
    tool_name_override=None,         # 覆盖默认工具名称
    tool_description_override=None,  # 覆盖工具描述
    on_handoff=None,                 # 交接时执行的回调
    input_type=None,                 # 交接输入类型（Pydantic）
    input_filter=None,               # 输入过滤器
)
```

### 交接回调

```python
from pydantic import BaseModel
from agents import Agent, handoff, RunContextWrapper

class EscalationData(BaseModel):
    reason: str

async def on_handoff(ctx, input_data: EscalationData):
    print(f"Escalation: {input_data.reason}")

agent = Agent(name="Escalation agent")
handoff_obj = handoff(agent=agent, on_handoff=on_handoff, input_type=EscalationData)
```

### 输入过滤器

过滤新智能体看到的对话历史：

```python
from agents.extensions import handoff_filters

handoff_obj = handoff(
    agent=agent,
    input_filter=handoff_filters.remove_all_tools,
)
```

### 推荐提示词

```python
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

agent = Agent(
    name="Billing agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    <你的指令内容>""",
)
```

---

## Guardrails 安全护栏

### 输入安全护栏

```python
from agents import (
    Agent, GuardrailFunctionOutput, InputGuardrailTripwireTriggered,
    RunContextWrapper, Runner, input_guardrail
)

@input_guardrail
async def math_guardrail(ctx, agent, input) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_math_homework,
    )

agent = Agent(
    name="Customer support",
    input_guardrails=[math_guardrail],
)
```

### 工作流程

1. 接收输入
2. 运行检查函数
3. 检查 `tripwire_triggered`，若为真则抛出异常

### 输出安全护栏

```python
from agents import output_guardrail

@output_guardrail
async def output_check(ctx, agent, output) -> GuardrailFunctionOutput:
    # 检查输出
    return GuardrailFunctionOutput(
        output_info={"valid": True},
        tripwire_triggered=False,
    )
```

---

## MCP 支持

### MCP 简介

MCP (Model Context Protocol) 是一个开放协议，标准化应用程序如何向 LLM 提供上下文。

### 两种 MCP 服务器类型

1. **stdio 服务器**: 本地子进程运行
2. **SSE 服务器**: 远程 HTTP 服务器

### 连接 MCP 服务器

```python
from agents import MCPServerStdio, MCPServerSse

# stdio 服务器
async with MCPServerStdio(
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"],
    }
) as server:
    tools = await server.list_tools()

# SSE 服务器
server = MCPServerSse(
    url="http://localhost:3000/sse",
    headers={"Authorization": "Bearer token"},
)
```

### 集成到 Agent

```python
agent = Agent(
    name="Assistant",
    instructions="Use tools to complete task",
    mcp_servers=[server1, server2],
)
```

### 缓存工具列表

减少重复 `list_tools()` 调用延迟：

```python
server = MCPServerStdio(
    params={...},
    cache_tools_list=True,  # 启用缓存
)
```

---

## 流式输出

### 使用 run_streamed()

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="讲5个笑话")

result = Runner.run_streamed(agent, input="请讲5个笑话")

async for event in result.stream_events():
    # 处理事件
```

### 事件类型

1. **RawResponsesStreamEvent**: 原始 LLM 响应事件
2. **RunItemStreamEvent**: 高级别事件，工具调用、消息输出
3. **AgentUpdatedStreamEvent**: 智能体更新事件（交接时）

### 事件过滤

```python
async for event in result.stream_events():
    if event.type == "raw_response_event":
        continue
    elif event.type == "agent_updated_stream_event":
        print(f"智能体更新: {event.new_agent.name}")
    elif event.type == "run_item_stream_event":
        # 处理生成的项目
        pass
```

---

## 追踪功能

### 默认追踪内容

- `Runner.run()` 整体
- Agent 运行
- LLM 生成
- 函数工具调用
- 安全护栏
- 交接/切换

### 禁用追踪

```python
# 方法1: 环境变量
# OPENAI_AGENTS_DISABLE_TRACING=1

# 方法2: RunConfig
config = RunConfig(tracing_disabled=True)
```

### 合并多次运行为单一追踪

```python
from agents import Agent, Runner, trace

async def main():
    agent = Agent(name="Joke generator", instructions="讲有趣的笑话")

    with trace("笑话工作流程"):
        first = await Runner.run(agent, "给我讲个笑话")
        second = await Runner.run(agent, f"评分: {first.final_output}")
```

### 自定义跨度

```python
from agents import custom_span

with custom_span("自定义操作") as span:
    span.add_attribute("key", "value")
```

### 外部追踪集成

支持：Weights & Biases、Arize-Phoenix、LangSmith、MLflow、Braintrust、Langfuse

```python
from agents import set_trace_processors

set_trace_processors([langsmith_processor, your_processor])
```

---

## 配置选项

### ModelSettings

```python
from agents import ModelSettings

settings = ModelSettings(
    temperature=0.7,
    top_p=0.9,
    max_tokens=1000,
    tool_choice="auto",  # auto/required/none/具体工具名
)
```

### RunConfig

```python
from agents import RunConfig

config = RunConfig(
    model="gpt-4o",
    model_settings=settings,
    tracing_disabled=False,
    trace_include_sensitive_data=False,
)
```

---

## 示例代码

### 完整示例

```python
import asyncio
from agents import (
    Agent, Runner, function_tool, handoff,
    ModelSettings, RunConfig
)

# 定义工具
@function_tool
def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city} 天气晴朗"

# 创建子智能体
spanish_agent = Agent(
    name="Spanish translator",
    instructions="Translate to Spanish"
)

# 创建主智能体
assistant = Agent(
    name="Assistant",
    instructions="你是一个有帮助的助手",
    model="gpt-4o",
    tools=[get_weather, spanish_agent.as_tool(
        tool_name="translate_spanish",
        tool_description="翻译成西班牙语"
    )],
    handoffs=[spanish_agent],
)

# 运行
async def main():
    config = RunConfig(
        model_settings=ModelSettings(temperature=0.7)
    )

    result = await Runner.run(
        assistant,
        "北京天气怎么样？",
        run_config=config
    )

    print(result.final_output)

asyncio.run(main())
```

---

## 参考资料

- [OpenAI Agents SDK 官方文档](https://openai-agents-sdk.doczh.com/)
- [GitHub 仓库](https://github.com/openai/openai-agents-python)

---

*文档版本: 1.0*
*最后更新: 2026-03-03*
