# OpenAI Agents SDK 深度梳理（基于 https://openai-agents-sdk.doczh.com/）

- 文档版本：v1.0
- 编写日期：2026-03-03
- 适用对象：准备基于 OpenAI Agents SDK 构建生产级 Agent 系统（如 Portex）的研发团队
- 阅读范围：Quickstart、Agents、Running、Results、Streaming、Tools、Handoffs、Guardrails、Context、Models、Config、MCP、Tracing、Multi-agent、Visualization、Voice，以及 API Reference（Runner/Result/Items/Tools/Handoffs/Guardrails/Exceptions/ModelSettings/MCP/Tracing）

---

## 1. 一句话架构理解

OpenAI Agents SDK 的核心是：

1. `Agent` 定义“能力边界”（指令、工具、交接、护栏、输出结构）。
2. `Runner` 驱动“执行循环”（LLM -> 工具/交接 -> 再次推理 -> 直到 final output）。
3. `RunResult`/`RunResultStreaming` 暴露“运行产物”（最终输出、增量项、原始响应、护栏结果）。
4. `Tracing`/`RunConfig`/`ModelSettings` 提供“可观测与可控性”。

这不是聊天 SDK，而是一个“工作流执行内核”。

---

## 2. 核心对象模型

### 2.1 Agent

`Agent` 是一组可组合能力的容器，关键字段：

1. `name`：Agent 名称。
2. `instructions`：系统提示，可为静态字符串或动态函数。
3. `model` + `model_settings`：模型与参数（温度、tool_choice、max_tokens 等）。
4. `tools`：函数工具/托管工具/Agent-as-tool。
5. `handoffs`：交接给其他 Agent。
6. `mcp_servers`：接入 MCP 工具源。
7. `input_guardrails` / `output_guardrails`：输入/输出护栏。
8. `output_type`：结构化输出（Pydantic/dataclass/TypedDict 等）。
9. `tool_use_behavior`：工具调用后是继续回到 LLM 还是停止。
10. `reset_tool_choice`：防止模型被固定在强制工具调用循环。

常用能力：

1. `clone(**kwargs)`：复制并覆盖配置。
2. `as_tool(...)`：把一个 Agent 包装成工具供上层 Agent 调用。
3. `get_all_tools()`：合并本地工具 + MCP 工具。

### 2.2 Runner

三种运行方式：

1. `Runner.run()`：异步，返回 `RunResult`。
2. `Runner.run_sync()`：同步封装。
3. `Runner.run_streamed()`：流式，返回 `RunResultStreaming`。

### 2.3 RunConfig（运行级总控）

`RunConfig` 覆盖“单次运行全局策略”，关键项：

1. `model` / `model_provider` / `model_settings`：全局模型覆盖。
2. `handoff_input_filter`：全局交接输入过滤器。
3. `input_guardrails` / `output_guardrails`：运行级护栏。
4. `tracing_disabled` / `trace_include_sensitive_data`：追踪策略。
5. `workflow_name` / `trace_id` / `group_id` / `trace_metadata`：追踪关联信息。

### 2.4 Result 与 Item

`RunResultBase`（`RunResult` 和 `RunResultStreaming` 共同基类）关键字段：

1. `final_output`：最终输出（可能是 `str`，也可能是结构化类型）。
2. `last_agent`：最后执行的 Agent。
3. `new_items`：本轮新增项（消息、工具调用、交接、推理项等）。
4. `raw_responses`：模型原始响应。
5. `input_guardrail_results` / `output_guardrail_results`：护栏检测结果。
6. `to_input_list()`：把本轮产物拼接为下一轮输入。
7. `last_response_id`：便于后续使用 `previous_response_id` 增量续跑。

---

## 3. 执行循环（最关键）

`Runner.run` 的逻辑本质：

1. 用当前 `agent + input` 调模型。
2. 若产出“最终输出”，结束。
3. 若产出 handoff 调用，切换 Agent 并继续。
4. 若产出 tool calls，执行工具，把工具输出注入上下文后继续。
5. 超过 `max_turns` 抛 `MaxTurnsExceeded`。
6. 护栏触发 `tripwire` 时抛异常并停止。

关键事实：

1. 输入护栏只在“起始 Agent”执行。
2. 输出护栏只在“最后 Agent”执行。
3. `previous_response_id` 可用于 OpenAI Responses API 场景下减少重复上下文传输。

---

## 4. 流式处理语义

流式不只 token 流，还包括语义事件流。

### 4.1 事件类型

`stream_events()` 会产出 `StreamEvent` 联合类型：

1. `RawResponsesStreamEvent`：底层模型原始事件（如文本 delta）。
2. `RunItemStreamEvent`：语义化项事件（消息完成、工具调用、工具输出、handoff 请求、推理项、MCP 列工具等）。
3. `AgentUpdatedStreamEvent`：当前执行 Agent 发生变化（handoff 场景）。

### 4.2 工程建议

1. 前端展示层建议优先消费 `RunItemStreamEvent`，而非直接拼接原始 token。
2. `raw_response_event` 适合做“极低延迟字粒度输出”；`run_item_stream_event` 适合做“状态机驱动 UI”。
3. 必须为“event 重放 + 断线恢复”设计幂等键（run_id + seq）。

---

## 5. 工具体系（Tools）

### 5.1 三类工具

1. 托管工具（Hosted）：如 Web/Search/File/Computer/MCP Hosted 等。
2. 函数工具（`@function_tool`）：Python 函数自动转工具。
3. Agent-as-tool：把子 Agent 当作工具调用，不转移控制权。

### 5.2 `@function_tool` 机制

SDK 自动完成：

1. 函数签名 -> JSON Schema。
2. docstring -> 工具描述与参数说明（支持 google/sphinx/numpy）。
3. 同步/异步函数统一调度。

关键参数：

1. `name_override` / `description_override`。
2. `docstring_style` / `use_docstring_info`。
3. `failure_error_function`：定义工具失败后如何反馈给 LLM。
4. `strict_mode`：建议开启，减少无效参数。

### 5.3 失败处理策略

1. 默认：将错误信息包装后反馈给模型。
2. 自定义：可输出更可控的错误格式。
3. 设为 `None`：直接抛异常，由业务方处理（更严格）。

---

## 6. Handoffs（交接/切换）

### 6.1 交接是“工具调用”语义

LLM 看见的是 `transfer_to_xxx` 工具，因此提示词必须明确何时交接。

### 6.2 配置方式

1. 直接在 `handoffs` 列表传 Agent。
2. 用 `handoff(...)` 构建自定义 Handoff：
- `tool_name_override`
- `tool_description_override`
- `on_handoff`
- `input_type`（handoff 输入结构校验）
- `input_filter`（重写传给下一个 Agent 的上下文）

### 6.3 输入过滤（关键）

默认下个 Agent 可看见完整历史。通过 `input_filter` 可做：

1. 去掉工具噪声。
2. 裁剪历史长度。
3. 清除敏感字段。

---

## 7. Guardrails（安全护栏）

### 7.1 数据结构

`GuardrailFunctionOutput`：

1. `output_info`：可记录检测细节。
2. `tripwire_triggered`：是否触发“熔断线”。

### 7.2 类型

1. `InputGuardrail`：检查用户输入。
2. `OutputGuardrail`：检查最终输出。

### 7.3 触发行为

1. 输入触发 -> `InputGuardrailTripwireTriggered`。
2. 输出触发 -> `OutputGuardrailTripwireTriggered`。
3. 触发后当前运行立即中断。

### 7.4 实践建议

1. 把高风险策略前置到输入护栏（降本）。
2. 把质量/合规策略后置到输出护栏（兜底）。
3. `output_info` 必须结构化，便于审计与回放。

---

## 8. 上下文管理（Context）

“上下文”分两类：

1. 本地上下文（`RunContextWrapper.context`）：仅 Python 侧可见，不发给模型。
2. 模型上下文（对话历史 + 指令 + 工具返回）：LLM 可见。

本地上下文适合注入：

1. 用户信息。
2. DB/API 客户端。
3. 权限与租户状态。
4. 请求级依赖（logger、trace context）。

模型上下文注入策略：

1. 放进 instructions（静态/动态）。
2. 放进 input。
3. 通过工具按需拉取。
4. 使用检索/WebSearch。

---

## 9. 模型与提供商

### 9.1 官方模型形态

1. `OpenAIResponsesModel`（推荐）。
2. `OpenAIChatCompletionsModel`（兼容形态）。

### 9.2 非 OpenAI 提供商

可通过 LiteLLM 或自定义 provider 接入，但要注意：

1. 不同提供商对 `Responses API` 支持不一致。
2. 结构化输出支持不一致。
3. 托管工具、多模态能力差异较大。

### 9.3 `ModelSettings` 关键字段

1. 采样：`temperature`、`top_p`。
2. 惩罚：`frequency_penalty`、`presence_penalty`。
3. 工具控制：`tool_choice`、`parallel_tool_calls`。
4. 截断与预算：`truncation`、`max_tokens`。
5. 推理与观测：`reasoning`、`metadata`、`include_usage`、`store`。
6. 扩展参数：`extra_query` / `extra_body` / `extra_headers`。

---

## 10. 配置与日志

### 10.1 全局配置函数

1. `set_default_openai_key(...)`
2. `set_default_openai_client(...)`
3. `set_default_openai_api("responses"|"chat_completions")`
4. `set_tracing_export_api_key(...)`
5. `set_tracing_disabled(True/False)`
6. `enable_verbose_stdout_logging()`

### 10.2 日志敏感信息控制

1. `OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1`
2. `OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1`

---

## 11. MCP 集成

### 11.1 服务器类型

1. `MCPServerStdio`（本地子进程）。
2. `MCPServerSse`（远程 SSE）。
3. `MCPServerStreamableHttp`（远程流式 HTTP）。

### 11.2 生命周期

1. `connect()` 建连。
2. `list_tools()` 列出工具。
3. `call_tool()` 调用工具。
4. `cleanup()` 释放资源。

### 11.3 性能优化

1. `cache_tools_list=True` 可显著减少远程 `list_tools` 延迟。
2. 工具变更后必须 `invalidate_tools_cache()`。

### 11.4 安全关注点

1. MCP 工具即远程执行能力，必须 RBAC + 审计。
2. 对 `mcp_approval_requested` 事件实现人工确认流。

---

## 12. Tracing（可观测性）

### 12.1 默认会追踪什么

默认包含：run、agent、generation、function tool、guardrail、handoff，以及语音相关 span。

### 12.2 Trace 关键维度

1. `workflow_name`：业务流程名。
2. `trace_id`：一次追踪唯一 ID。
3. `group_id`：会话级聚合键（适合 thread_id）。
4. `metadata`：租户、项目、环境等。

### 12.3 API

1. `trace(...)`：创建追踪。
2. `custom_span(...)`：自定义业务段。
3. `add_trace_processor(...)`：增加外部处理器。
4. `set_trace_processors(...)`：替换处理器链。

### 12.4 数据治理

1. `trace_include_sensitive_data=False` 可禁用模型/工具敏感数据上报。
2. 语音场景可单独控制敏感音频追踪。

---

## 13. 多 Agent 编排模式

### 13.1 LLM 编排

优势：灵活、适合开放式任务。风险：不可预测、成本波动。

### 13.2 代码编排

优势：可控、可测、稳定。模式包括：

1. 结构化输出后分支。
2. 串行流水线（research -> draft -> review）。
3. evaluator-optimizer 循环。
4. `asyncio.gather` 并行独立子任务。

### 13.3 推荐

生产系统应“LLM 决策 + 代码护栏”混合：

1. 决策留给 LLM。
2. 边界条件、超时、重试、预算由代码强约束。

---

## 14. Voice（语音 Agent）

`VoicePipeline` = STT -> Workflow -> TTS。

输入模式：

1. `AudioInput`：已成段音频。
2. `StreamedAudioInput`：流式输入并自动检测话轮。

输出是 `StreamedAudioResult`，可流式消费：

1. 音频事件。
2. 生命周期事件（turn_started / turn_ended 等）。
3. 错误事件。

注意：SDK 当前对流式中断不做强内建，需要应用层根据 lifecycle 事件处理打断和麦克风策略。

---

## 15. 异常体系（必须显式处理）

1. `AgentsException`：基类。
2. `MaxTurnsExceeded`：超过轮次。
3. `ModelBehaviorError`：模型行为异常（非法 JSON/无效工具）。
4. `UserError`：调用方式错误。
5. `InputGuardrailTripwireTriggered`。
6. `OutputGuardrailTripwireTriggered`。

工程上应把这几类异常映射到统一错误码与重试/告警策略。

---

## 16. 与 Portex 的落地映射（重点）

### 16.1 运行层（Runner Adapter）

1. 统一封装 `Runner.run` / `run_streamed`。
2. 强制注入 `RunConfig.workflow_name/group_id/trace_metadata`。
3. 把 `StreamEvent` 映射为 Portex 事件协议（前端解耦 SDK）。

### 16.2 会话与上下文

1. 每个 Flow 维护“对话输入链 + last_response_id”。
2. 默认通过 `to_input_list()` 拼接多轮。
3. 对长历史做服务端压缩与分段归档。

### 16.3 安全

1. 输入护栏做“越权、越界、敏感任务”前置阻断。
2. 输出护栏做“内容合规”后置兜底。
3. 工具权限按租户白名单分层（特别是 LocalShell/MCP）。

### 16.4 可观测

1. 每次运行附带 `trace_id + group_id + run_id` 三元关联。
2. 保存 `new_items` 的结构化镜像用于审计与回放。
3. 对 `ModelBehaviorError`、`tripwire`、`max_turns` 建立一级告警。

### 16.5 成本与性能

1. 使用轻量模型做分流/护栏，重模型做复杂推理。
2. 合理使用 `parallel_tool_calls`。
3. MCP 开启工具列表缓存并配置失效策略。
4. 对流式输出做“首 token 延迟”和“全量完成时延”双指标。

---

## 17. 实施检查清单（可直接用于开发）

1. 是否统一封装了 SDK 运行入口（避免业务代码散落调用）？
2. 是否为每次运行写入 `workflow_name/group_id`？
3. 是否建立了 StreamEvent -> 前端事件协议映射层？
4. 是否将工具错误、护栏触发、max_turns 做了统一异常映射？
5. 是否有工具权限矩阵（租户/角色/环境）？
6. 是否实现了对话历史压缩、归档、重放？
7. 是否为模型切换（Responses/ChatCompletions/LiteLLM）留了提供商抽象？
8. 是否对敏感日志和追踪数据做了治理开关？
9. 是否为 MCP 连接和缓存失效做了健康检查与重连策略？
10. 是否为关键路径建立端到端回归测试（含流式/中断/恢复）？

---

## 18. 参考链接

### 18.1 中文文档（本次主要依据）

1. 首页：https://openai-agents-sdk.doczh.com/
2. 快速开始：https://openai-agents-sdk.doczh.com/quickstart/
3. Agents：https://openai-agents-sdk.doczh.com/agents/
4. 运行：https://openai-agents-sdk.doczh.com/running_agents/
5. 结果：https://openai-agents-sdk.doczh.com/results/
6. 流式：https://openai-agents-sdk.doczh.com/streaming/
7. 工具：https://openai-agents-sdk.doczh.com/tools/
8. 交接：https://openai-agents-sdk.doczh.com/handoffs/
9. 护栏：https://openai-agents-sdk.doczh.com/guardrails/
10. 上下文：https://openai-agents-sdk.doczh.com/context/
11. 模型：https://openai-agents-sdk.doczh.com/models/
12. 配置：https://openai-agents-sdk.doczh.com/config/
13. MCP：https://openai-agents-sdk.doczh.com/mcp/
14. 追踪：https://openai-agents-sdk.doczh.com/tracing/
15. 多 Agent：https://openai-agents-sdk.doczh.com/multi_agent/
16. 可视化：https://openai-agents-sdk.doczh.com/visualization/
17. 语音快速入门：https://openai-agents-sdk.doczh.com/voice/quickstart/

### 18.2 API 参考（中文镜像）

1. Runner：https://openai-agents-sdk.doczh.com/ref/run/
2. Results：https://openai-agents-sdk.doczh.com/ref/result/
3. Streaming events：https://openai-agents-sdk.doczh.com/ref/stream_events/
4. Items：https://openai-agents-sdk.doczh.com/ref/items/
5. Tools：https://openai-agents-sdk.doczh.com/ref/tool/
6. Handoffs：https://openai-agents-sdk.doczh.com/ref/handoffs/
7. Guardrails：https://openai-agents-sdk.doczh.com/ref/guardrail/
8. Exceptions：https://openai-agents-sdk.doczh.com/ref/exceptions/
9. Model settings：https://openai-agents-sdk.doczh.com/ref/model_settings/
10. OpenAI Responses model：https://openai-agents-sdk.doczh.com/ref/models/openai_responses/
11. MCP servers：https://openai-agents-sdk.doczh.com/ref/mcp/server/
12. Tracing module：https://openai-agents-sdk.doczh.com/ref/tracing/
