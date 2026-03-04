# OpenAI Agents SDK 深度梳理（Python 方向）

> 文档来源：`https://openai-agents-sdk.doczh.com/`（按站点结构逐章学习）
> 目标：为 Portex 的 Python 重写提供可执行的 SDK 认知与落地参考

## 1. SDK 定位与整体设计

OpenAI Agents SDK 的定位是一个“**轻量、可组合、可生产化**”的 Agent 框架，核心围绕以下能力：
1. `Agent`：具备 instructions、tools、handoffs、guardrails 的智能体。
2. `Runner`：统一驱动 Agent 执行（同步/异步/流式）。
3. `Tools`：函数工具、Hosted tools、MCP server tools。
4. `Handoffs`：多 Agent 任务委派。
5. `Guardrails`：输入/输出护栏与拦截。
6. `Tracing`：内建追踪与可观测。

核心思想不是“把所有能力绑死在一个黑箱里”，而是把 Agent 运行拆成可替换模块，便于工程化接入。

---

## 2. 快速开始与基础运行模型

## 2.1 安装

```bash
pip install openai-agents
```

## 2.2 最小可运行示例

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")
result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)
```

说明：
1. `Runner.run_sync()` 是最直观的本地阻塞调用。
2. 非阻塞/服务端场景优先用 `await Runner.run(...)`。
3. 需要增量事件推送时使用 `Runner.run_streamed(...)`。

---

## 3. Agent 核心概念

## 3.1 Agent 的关键属性

一个 Agent 通常包含：
1. `name`：可读名称。
2. `instructions`：系统级行为约束（可为静态字符串，也可动态生成）。
3. `model`：模型标识或模型对象。
4. `tools`：该 Agent 可调用的工具集合。
5. `handoffs`：可委派的下游 Agent 列表。
6. `output_type`：结构化输出类型（可选）。
7. `hooks`：生命周期钩子（可选）。
8. `guardrails`：输入/输出护栏（可选）。

## 3.2 Instructions 最佳实践

文档强调两类方式：
1. 静态 instructions：简单稳定，便于审计。
2. 动态 instructions：可根据 `context` 生成，适合多租户、个性化策略。

对 Portex 的意义：可按租户、角色、安全级别动态拼装系统提示词。

## 3.3 结构化输出

`output_type` 能强制 Agent 返回结构化结果（通常结合 Pydantic）。
这对平台化尤其重要：
1. 易于存储/索引。
2. 易于前端渲染。
3. 易于自动化后处理。

---

## 4. Runner 与执行生命周期

## 4.1 三种执行入口

1. `Runner.run(agent, input, ...)`：异步执行。
2. `Runner.run_sync(agent, input, ...)`：同步包装。
3. `Runner.run_streamed(agent, input, ...)`：流式执行。

## 4.2 执行循环（重要）

官方描述的循环语义可以概括为：
1. 调用当前 Agent。
2. 若模型产出 `final_output`：结束。
3. 若模型请求 `handoff`：切换到目标 Agent。
4. 若模型请求 `tool call`：执行工具并把结果回注。
5. 重复直到结束或触发上限（如 `max_turns`）。

这与 happyclaw 的“消息 -> 执行 -> 事件回传”链路高度匹配，但 SDK 内部已封装了多数编排细节。

## 4.3 RunResult 关键结果对象

常用字段（按文档语义）：
1. `final_output`：最终输出（字符串或结构化对象）。
2. `last_agent`：结束时的 Agent。
3. `new_items`：本次 run 产生的新增条目。
4. `input_guardrail_results` / `output_guardrail_results`：护栏结果。
5. `raw_responses`：底层模型响应集合。
6. `to_input_list()`：把历史产物转为下一轮输入。

对 Portex 的意义：可以把 `new_items + raw_responses + guardrail_results` 统一落库，形成“可回放执行轨迹”。

---

## 5. Streaming 事件模型

`run_streamed` 允许在执行中持续消费事件。文档给出的常见类型包括：
1. `RawResponsesStreamEvent`：底层模型 token/响应增量。
2. `RunItemStreamEvent`：运行条目事件（消息、工具结果等）。
3. `AgentUpdatedStreamEvent`：当前活跃 Agent 变化（多 Agent 场景）。

平台落地建议：
1. SDK 事件 -> 平台内部标准事件（`run.event`）做一次映射。
2. 前端只依赖平台事件协议，不直接绑定 SDK 内部类型。

---

## 6. Tools 体系

## 6.1 Function tools

通过 Python 函数快速注册工具，SDK 会自动处理 schema 与调用流程。

价值：
1. 业务逻辑可直接复用服务内部函数。
2. 工具权限可由平台统一管理（白名单、审计、限流）。

## 6.2 Agent-as-tool

一个 Agent 可以 `as_tool()` 暴露给另一个 Agent。
适合“专家 Agent”模式：
1. Planner Agent 调度。
2. Domain Agent 作为工具被调用。

## 6.3 Hosted tools

文档列出了内置 Hosted 工具类别（如 WebSearch、FileSearch、ComputerUse 等）。
注意：
1. 需确认对应模型/账号能力是否开通。
2. 应在平台层做可用性开关和配额隔离。

## 6.4 MCP server tools

SDK 支持对接 MCP Server（stdio / SSE / streamable HTTP）。
这对 Portex 非常关键：
1. 可将现有内部工具服务化为 MCP。
2. 实现跨语言工具生态接入。

---

## 7. Handoffs（多 Agent 委派）

Handoff 是 SDK 的一等能力，不是“提示词模拟路由”。

可用能力（文档语义）：
1. 指定可委派 Agent 列表。
2. 为 handoff 定义工具名/描述覆写。
3. 支持 `on_handoff` 回调。
4. 支持输入过滤（handoff input filter）。
5. 支持动态启用/禁用 handoff。

对 Portex 的意义：
1. 可构建“总控 Agent + 专家 Agent”分层。
2. 可在租户维度动态装配可见 Agent 能力。

---

## 8. Guardrails（输入/输出护栏）

Guardrails 可在两个时机执行：
1. `InputGuardrail`：模型调用前拦截。
2. `OutputGuardrail`：输出返回前拦截。

关键机制：
1. Guardrail 函数返回校验结果。
2. 可触发“tripwire”中断执行。

Portex 落地建议：
1. 把敏感词/越权请求放输入护栏。
2. 把 PII 泄露/违规输出放输出护栏。
3. 护栏触发写入审计与告警事件。

---

## 9. Context 与 Sessions

## 9.1 Context

文档中的 `RunContextWrapper[T]` 用于在 Agent/工具中共享运行时上下文（如 user_id、tenant_id、权限范围）。

落地建议：
1. 将租户、用户、工作区、请求追踪 ID 注入 context。
2. 禁止工具直接读取全局状态，统一从 context 获取授权信息。

## 9.2 Sessions

SDK 提供 Session 概念（如 SQLiteSession），用于跨轮次保存会话历史。

平台化建议：
1. 小规模开发可先 SQLiteSession。
2. 生产环境建议将 session 与消息历史持久化到 PostgreSQL，并按租户隔离。

---

## 10. 模型与配置

## 10.1 模型配置

文档展示了 `ModelSettings` 可调项，常见包括：
1. `temperature`
2. `top_p`
3. `frequency_penalty`
4. `presence_penalty`
5. `tool_choice`
6. `parallel_tool_calls`
7. `max_tokens`
8. 推理相关参数（reasoning）
9. 文本输出控制（verbosity 等）
10. `metadata` / `store` / `include` 等

## 10.2 SDK 全局配置

文档给出 `set_default_openai_key`、`set_default_openai_client`、`set_tracing_disabled` 等配置入口。

平台建议：
1. 不在业务代码散落 API Key。
2. 统一从 Secret Manager 注入。
3. 运行时按租户选择模型策略（成本/时延/能力分层）。

## 10.3 非 OpenAI 模型

文档有 LiteLLM 集成章节，说明 SDK 支持通过适配层接入非 OpenAI 模型。

对 Portex 的价值：
1. 模型厂商解耦。
2. 可做混合路由与成本优化。

---

## 11. Tracing 与可观测

SDK 内建 tracing（默认启用），可观测执行路径包含：
1. Run/Trace 级别信息。
2. Agent 切换、工具调用、模型响应等 span。

文档也提供禁用追踪、导出/处理追踪数据的机制。

Portex 建议：
1. 保留 SDK tracing。
2. 同时映射到平台统一观测栈（OpenTelemetry/Prometheus/Loki）。
3. trace_id 贯穿 API -> 调度 -> Runner -> 前端事件。

---

## 12. 多 Agent 编排模式（官方建议可抽象）

文档中的典型模式可归纳为：
1. **Manager Pattern**：总控 Agent 委派专家 Agent。
2. **Decentralized Pattern**：Agent 之间可互相 handoff。

Portex 推荐先采用 Manager Pattern：
1. 行为稳定，便于审计。
2. 权限边界清晰。
3. 前端可更直观展示任务分派。

---

## 13. Realtime / Voice 能力

文档包含 Voice Agent 与 Realtime Agent 章节，适用于语音交互与实时会话。

对当前 Portex 的建议：
1. 第一阶段先做文本优先。
2. 预留 Realtime 网关接口（WebRTC/WS）与事件协议扩展位。
3. 第二阶段引入 Voice Agent。

---

## 14. 将 SDK 用于 Portex 的落地蓝图

## 14.1 运行时分层

1. **API 层**：FastAPI 提供 REST + WS。
2. **Orchestrator 层**：会话队列、任务调度、run 生命周期。
3. **SDK Adapter 层**：
- Agent Factory（动态 instructions/tools/handoffs）
- Runner Executor（run/run_streamed）
- Event Mapper（SDK 事件 -> 平台事件）
4. **Sandbox 层**：容器隔离 + 权限策略。
5. **Storage 层**：会话、消息、run_event、审计。

## 14.2 最小闭环

1. 用户发消息。
2. 创建/复用 Session。
3. 用 Agent Factory 组装 Agent（含 tools/guardrails）。
4. 调用 `run_streamed`。
5. 把事件推送前端并落库。
6. 完成后返回 `final_output` 与 run 摘要。

## 14.3 关键工程策略

1. 平台协议与 SDK 内部对象解耦。
2. 对 Guardrails、Tools、Handoffs 全量审计。
3. 将 SDK 升级视为“可控变更”，配套回归测试。

---

## 15. 风险与注意事项

1. SDK 升级导致事件字段变化：
- 需要版本锁定 + 合约测试。

2. 工具调用权限扩散：
- 必须在平台层二次授权，不能仅依赖 instructions。

3. 多 Agent 路由不可控：
- 通过 handoff 白名单和策略开关限制。

4. 流式事件量大：
- 需要事件采样、压缩与冷热分层存储。

5. 生产稳定性：
- 需建立超时、取消、重试、熔断和死信机制。

---

## 16. 推荐学习顺序（给团队）

1. Quickstart + Agents + Runner
2. Results + Streaming
3. Tools + MCP
4. Handoffs + Multi-agent
5. Guardrails + Context + Sessions
6. Tracing + Configuration + Models
7. Voice/Realtime（按需）

---

## 17. 参考链接

1. 首页/概览：https://openai-agents-sdk.doczh.com/
2. Agents：https://openai-agents-sdk.doczh.com/agents/
3. Running agents：https://openai-agents-sdk.doczh.com/running_agents/
4. Results：https://openai-agents-sdk.doczh.com/results/
5. Streaming：https://openai-agents-sdk.doczh.com/streaming/
6. Tools：https://openai-agents-sdk.doczh.com/tools/
7. MCP：https://openai-agents-sdk.doczh.com/mcp/
8. Handoffs：https://openai-agents-sdk.doczh.com/handoffs/
9. Guardrails：https://openai-agents-sdk.doczh.com/guardrails/
10. Context management：https://openai-agents-sdk.doczh.com/context_management/
11. Sessions：https://openai-agents-sdk.doczh.com/sessions/
12. Tracing：https://openai-agents-sdk.doczh.com/tracing/
13. Orchestrating multiple agents：https://openai-agents-sdk.doczh.com/multi_agent/
14. Models：https://openai-agents-sdk.doczh.com/models/
15. Configuration：https://openai-agents-sdk.doczh.com/config/
16. Voice agents：https://openai-agents-sdk.doczh.com/voice/quickstart/
17. Realtime agents：https://openai-agents-sdk.doczh.com/realtime/quickstart/
