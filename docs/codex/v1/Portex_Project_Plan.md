# Portex 项目规划文档（Python 重写 HappyClaw，基于 Codex + OpenAI Agents SDK）

- 文档版本：v1.1
- 编写日期：2026-03-03
- 项目名称：Portex
- 文档目标：给出可执行、可验收、可拆解的端到端落地规划

---

## 1. 项目目标与边界

### 1.1 项目愿景
Portex 是一个**远程、多用户、Web 可视化、容器隔离**的 AI Agent 服务，核心定位：

1. 把终端里的 Agent（尤其是 Codex 工作流）迁移到可协作的 Web 平台。
2. 保留“强执行能力”而不是只做聊天 UI。
3. 在多用户场景下保证安全隔离、可审计、可运维。

### 1.2 本次重写目标（以 Python 为主）

1. 以 Python 技术栈重构 HappyClaw 的核心能力。
2. Agent 执行层采用 OpenAI Agents SDK（并兼容 Codex 任务执行能力）。
3. 首期优先 Web 端闭环，IM（飞书/Telegram）作为二期扩展。
4. 形成可持续演进架构，而不是 1:1 翻译 Node 代码。

### 1.3 首期不做（明确范围）

1. 不做全量 IM 生态适配（首期仅保留接口设计与插件位）。
2. 不做跨地域多活。
3. 不做企业 SSO（先用本地账号体系 + RBAC）。
4. 不做移动端原生 App（保留 PWA）。

---

## 2. 并行分析结论（多 Agent 视角）

本规划先执行了并行分析（文章 / 仓库 / SDK 文档）：

- Agent-A（产品与架构）：拆解 HappyClaw 的产品能力、用户路径与部署模型。
- Agent-B（代码与运行时）：分析 `happyclaw` 后端、队列、容器 runner、IPC、DB schema、WebSocket 流协议。
- Agent-C（SDK 与能力映射）：梳理 OpenAI Agents SDK 在 `Agent/Runner/RunConfig/Items/Tools/Guardrails/Streaming/MCP/Tracing` 的可用能力。

结论：

1. HappyClaw 的关键不是“聊天”，而是“执行系统”：队列调度 + runner 生命周期 + 流式事件协议 + 多租户隔离。
2. Python 重写应保持“控制平面（编排）”与“数据平面（执行）”分离。
3. OpenAI Agents SDK 已覆盖大部分核心抽象；Portex 重点在工程化封装（隔离、安全、观测、权限、存储）。

---

## 3. HappyClaw 能力拆解（重写输入）

### 3.1 必须继承的能力

1. 多用户隔离：每用户独立工作区/会话/配置。
2. 双执行模式：宿主机模式 + 容器模式（默认容器）。
3. 流式事件：思考、文本、工具调用、任务、状态等结构化推送。
4. 调度与并发控制：会话级队列 + 全局并发上限 + 退避重试。
5. 记忆系统：全局记忆 + 会话记忆 + 日期记忆 + 归档。
6. 定时任务：cron / interval / once。
7. 安全能力：RBAC、审计、敏感配置加密、路径与挂载防护。

### 3.2 建议升级点（Python 重写时实现）

1. DB 从 SQLite 单机优先升级为 PostgreSQL（保留 SQLite dev 模式）。
2. IPC 从“文件轮询为主”升级为“事件总线 + 文件回退”（Redis Stream/NATS 可选）。
3. 统一 Runner 协议（host/container 同一抽象）。
4. 明确 Domain 分层，降低后续 IM、MCP、模型提供商扩展成本。

---

## 4. OpenAI Agents SDK 适配策略

### 4.1 SDK 能力映射

| Portex 需求 | SDK 能力 | Portex 落地方式 |
|---|---|---|
| Agent 主循环 | `Runner.run / run_streamed` | 统一封装 `AgentRunService` |
| 多轮上下文 | `to_input_list` / `last_response_id` / `previous_response_id` | 持久化输入链与 `last_response_id`，按策略裁剪历史 |
| 结构化输出 | `output_type` | 用于任务结果、审计结构化记录 |
| 工具调用 | `@function_tool` / Hosted tools | 平台工具统一注册为 function tools |
| 多 Agent | handoffs / agents-as-tools | 管理型编排优先，handoff 用于专家流转 |
| 安全护栏 | input/output/tool guardrails | 高风险任务前置阻断 + 工具级策略 |
| 流式事件 | `raw_response_event` / `run_item_stream_event` / `agent_updated_stream_event` | 转换为 Portex 统一事件协议 |
| MCP 生态 | `MCPServerStdio/Sse/StreamableHttp` + `HostedMCPTool` | 统一 MCP 注册中心 |
| 追踪 | SDK tracing + OpenAI traces | 对接平台日志/指标/告警 |
| 运行级策略 | `RunConfig` | 强制注入 `workflow_name/group_id/trace_metadata` |
| 异常语义 | `MaxTurnsExceeded`/`ModelBehaviorError`/`Input|OutputGuardrailTripwireTriggered` | 映射平台错误码与告警等级 |

### 4.2 Codex 能力接入策略

1. 主路径：使用 Agents SDK 的实验 `codex_tool` 承载工作区任务。
2. 兼容路径：保留 runner 侧“直接调用 codex CLI”的降级通道。
3. 策略：首期默认兼容路径更稳，逐步切到 `codex_tool` 主路径（实验能力变更风险更高）。

### 4.3 SDK 运行规范（Portex 强约束）

1. 所有执行入口统一走 `AgentRunService`，禁止业务层直接调用 SDK。
2. 默认使用 `Runner.run_streamed`，并将 `StreamEvent` 转换为平台事件。
3. 每次运行强制设置 `RunConfig.workflow_name/group_id/trace_metadata`。
4. 每轮运行后持久化 `to_input_list()` 和 `last_response_id`，用于恢复与续跑。
5. 默认 `max_turns` 由平台配置统一控制（按租户/环境可覆盖）。
6. 所有 SDK 异常映射为平台标准错误码，保证重试与告警一致。
7. 工具统一定义 `failure_error_function` 策略，避免模型收到不可解释错误。
8. 对非 OpenAI 提供商启用兼容策略（必要时切换 `chat_completions`）。

---

## 5. 技术架构总览

### 5.1 逻辑分层

1. **接入层**：Web API / WebSocket / Auth。
2. **控制平面**：Flow 管理、队列调度、任务编排、权限与审计。
3. **执行平面**：HostRunner / ContainerRunner、Agent SDK 执行、工具执行。
4. **状态层**：PostgreSQL、Redis、对象存储（可选）。
5. **观测层**：日志、指标、追踪、审计。

### 5.2 服务拆分（建议）

1. `portex-api`（FastAPI）：REST + WebSocket + Auth + RBAC。
2. `portex-orchestrator`：队列调度、重试、任务分发、生命周期控制。
3. `portex-runner`：实际执行（host/container），内置 Agents SDK runtime。
4. `portex-web`（React + Vite）：管理台 + 聊天台 + 监控台。
5. `portex-worker-scheduler`：定时任务扫描与触发。
6. 依赖：PostgreSQL、Redis、Docker Daemon。

### 5.3 关键数据流（首期）

1. 用户发送消息（Web） -> `portex-api` 持久化消息。
2. `orchestrator` 拉取待处理消息 -> 选择执行环境 -> 下发 runner。
3. runner 启动 Agent SDK，按流式事件回传。
4. `api` 通过 WebSocket 推送事件到前端。
5. 执行结果写回消息表与审计表，更新会话状态。

---

## 6. 领域模型与数据设计

### 6.1 核心实体

1. `users`：用户、角色、状态、偏好。
2. `sessions`：登录会话。
3. `flows`：工作区/会话容器（对应 happyclaw 的 group）。
4. `messages`：消息与附件引用。
5. `agent_runs`：一次运行实例（状态、耗时、错误码）。
6. `stream_events`（可选落库）：关键事件审计。
7. `scheduled_tasks` + `task_run_logs`：定时任务体系。
8. `mcp_servers`：每用户/每流配置。
9. `audit_logs`：安全与管理操作审计。

### 6.2 存储策略

1. 事务数据：PostgreSQL。
2. 临时队列与分布式锁：Redis。
3. 工作区文件：本地磁盘（后续可扩 S3/OSS）。
4. 会话记忆：
- SDK Session（SQLite/Redis/SQLAlchemy） + 业务侧记忆文件（`CLAUDE.md`、`memory/YYYY-MM-DD.md`）。

---

## 7. 关键模块设计

### 7.1 Runner 抽象

统一接口：

- `prepare(flow, run_request)`
- `start()`
- `send_input()`（支持中断/纠错）
- `stream_events()`
- `stop(graceful=True)`

实现：

1. `HostRunner`：用于 admin 或可信流。
2. `ContainerRunner`：默认执行路径，Docker 隔离。

### 7.2 队列调度（Orchestrator）

1. 会话串行，同会话同一时刻只允许一个 active run。
2. 全局配额：`max_container_runs`、`max_host_runs`。
3. 优先级：用户即时消息 > 已排队补偿 > 定时任务。
4. 重试：指数退避（5s -> 10s -> 20s -> ...，上限配置化）。
5. 幂等键：`flow_id + message_id`。

### 7.3 流式事件协议

建议统一事件模型（兼容 HappyClaw 视觉体验）：

1. `text_delta`
2. `thinking_delta`
3. `tool_use_start`
4. `tool_use_progress`
5. `tool_use_end`
6. `task_start`
7. `task_notification`
8. `status`
9. `error`

前后端仅依赖该协议，底层 SDK 事件可替换。

事件映射建议：

1. `raw_response_event` -> `text_delta` / `thinking_delta`（极低延迟显示）。
2. `run_item_stream_event.tool_called` -> `tool_use_start`。
3. `run_item_stream_event.tool_output` -> `tool_use_end`。
4. `run_item_stream_event.handoff_requested` -> `task_notification`。
5. `agent_updated_stream_event` -> `status`（当前 Agent 变更）。

### 7.4 会话与上下文策略

1. 本地上下文（`RunContextWrapper.context`）用于依赖注入，不进入 LLM 上下文。
2. LLM 上下文按“系统指令 + 输入链 + 工具输出”构建。
3. 长对话采用“窗口裁剪 + 归档摘要 + last_response_id 续跑”组合策略。
4. 对敏感上下文采用“本地注入优先，最小化透传给模型”的默认策略。

### 7.5 记忆系统

1. 用户全局记忆：`/data/users/{user_id}/global/CLAUDE.md`
2. Flow 记忆：`/data/flows/{flow_id}/CLAUDE.md`
3. 日期记忆：`/data/flows/{flow_id}/memory/YYYY-MM-DD.md`
4. 归档：`/data/flows/{flow_id}/conversations/*.md`

策略：

- 自动压缩前归档。
- 支持显式“写记忆”工具。
- 提供 memory 搜索与读取 API。

---

## 8. 安全与隔离设计

### 8.1 身份与权限

1. 认证：Cookie Session（HttpOnly + SameSite），后续可增 JWT。
2. 授权：RBAC + 细粒度 Permission。
3. 审计：用户管理、配置修改、任务调度、权限变更全量记录。

### 8.2 机密管理

1. API Key/OAuth 凭证加密存储（AES-256-GCM）。
2. 密钥轮换策略（季度）。
3. 日志脱敏（token、cookie、authorization 头）。

### 8.3 容器安全

1. 非 root 用户执行。
2. 最小挂载：按 flow 目录和白名单挂载。
3. 默认禁网（按任务策略启用 allowlist）。
4. CPU/内存/执行时长限制。
5. 明确禁止敏感路径挂载（`.ssh`, `.gnupg`, `.aws` 等）。

### 8.4 文件安全

1. 全路径归一化 + `realpath` 校验，防 path traversal。
2. 符号链接逃逸防护。
3. 上传大小限制 + MIME 检测。

### 8.5 MCP 与工具调用安全

1. MCP server 按租户白名单注册，默认禁用。
2. 高风险 MCP/本地 shell 工具接入审批机制（先审后调）。
3. `cache_tools_list` 仅在工具集合稳定时开启，并提供主动失效入口。
4. 关键工具调用写入审计日志（调用人、参数摘要、结果摘要、trace_id）。

---

## 9. Web 产品设计范围

### 9.1 首期页面

1. 登录/初始化向导
2. Chat 工作区（流式消息 + 工具轨迹 + 中断）
3. 文件管理器（上传/下载/编辑/预览）
4. 任务中心（创建/暂停/恢复/取消）
5. 监控页（并发、队列、runner 状态）
6. 设置页（模型、工具、权限、用户偏好）

### 9.2 交互关键点

1. 消息发送后立即本地回显。
2. 流式状态与最终消息自动收敛（避免“永久思考中”）。
3. 工具调用时间线可折叠、可回放最近 N 条。
4. 支持手动中断并安全恢复。

---

## 10. 里程碑计划（建议 16 周）

### M0：架构基线（第 1-2 周）

- 输出：
1. Monorepo 结构（`api/`, `orchestrator/`, `runner/`, `web/`, `infra/`）
2. 基础 CI（lint/test/typecheck）
3. PostgreSQL + Redis + Docker Compose 开发环境

- 验收：
1. 一键启动开发环境
2. 健康检查通过

### M1：最小闭环（第 3-5 周）

- 输出：
1. 用户登录 + Flow 创建
2. Web 消息发送 -> Runner 执行 -> 流式回传 -> 结果落库
3. HostRunner 与 ContainerRunner 基础实现
4. `RunConfig` 基线注入 + 标准异常映射

- 验收：
1. 单用户可连续 20 轮对话无状态丢失
2. 中断后可恢复下一轮执行
3. `MaxTurnsExceeded/ModelBehaviorError/Tripwire` 可正确返回前端并记录审计

### M2：多用户与隔离（第 6-8 周）

- 输出：
1. RBAC + 审计日志
2. 每用户独立工作区与配置
3. 并发调度与配额控制

- 验收：
1. 10 并发用户下无跨用户消息/文件串扰
2. 队列和重试符合预期

### M3：记忆与任务系统（第 9-11 周）

- 输出：
1. 记忆文件体系 + memory 工具
2. 定时任务（cron/interval/once）
3. Task 执行日志与页面

- 验收：
1. 定时任务可稳定触发与记录
2. 记忆跨会话可检索可生效

### M4：MCP 与可观测性（第 12-13 周）

- 输出：
1. MCP server 注册与权限控制
2. SDK tracing + 平台日志关联
3. 关键指标（p95 延迟、失败率、队列积压）

- 验收：
1. 单次 run 可追踪到 agent/tool/guardrail 全链路
2. 告警规则可触发
3. 同一会话多次 run 能通过 `group_id` 在追踪中聚合

### M5：灰度上线（第 14-16 周）

- 输出：
1. 压测与安全测试报告
2. 备份恢复与应急预案
3. 灰度发布与回滚脚本

- 验收：
1. p95 首 token < 3s（容器冷启动除外）
2. 关键路径成功率 >= 99%

---

## 11. 并行开发编组（建议）

### Agent-Dev-1：控制平面

1. API、鉴权、RBAC、审计。
2. Flow/Message/Task 数据模型。

### Agent-Dev-2：执行平面

1. Runner 抽象与容器生命周期。
2. Agents SDK 运行封装与事件转换。

### Agent-Dev-3：前端

1. Chat 流式 UI 与状态机。
2. 文件、任务、监控页面。

### Agent-Dev-4：平台保障

1. CI/CD、测试基建、压测、可观测性。
2. 安全策略与发布治理。

---

## 12. 测试与验收策略

### 12.1 测试分层

1. 单元测试：领域服务、调度算法、权限校验。
2. 集成测试：API + DB + Redis + runner mock。
3. 端到端测试：WebSocket 流式、任务调度、文件操作。
4. 安全测试：路径穿越、越权、注入、容器逃逸基线。

### 12.2 核心验收用例

1. 多用户并发对话，隔离正确。
2. agent 工具异常、超时、中断与恢复。
3. session/记忆在重启后可恢复。
4. 定时任务在时区切换和重启后行为正确。
5. 护栏触发 tripwire 时立即终止并返回可解释错误。
6. `last_response_id` 续跑链路可用，历史压缩后不破坏语义一致性。

---

## 13. 风险清单与缓解

1. **风险：Agents SDK 能力迭代快，接口变化**
- 缓解：在 `runner/sdk_adapter` 做隔离层，固定内部协议。

2. **风险：`codex_tool` 为实验能力**
- 缓解：保持 CLI 兼容路径；灰度切换。

3. **风险：容器冷启动延迟影响体验**
- 缓解：预热池 + 空闲保活 + 快照缓存。

4. **风险：长会话上下文膨胀**
- 缓解：session 限长、自动压缩、手动 compaction API。

5. **风险：多租户安全事件**
- 缓解：最小权限 + 审计 + 强制隔离 + 定期安全扫描。

6. **风险：非 OpenAI 模型兼容差异（Responses/结构化输出/工具能力）**
- 缓解：模型能力矩阵 + 运行时降级策略 + 兼容性回归测试集。

---

## 14. 交付物清单

1. `Portex` Python 后端服务（API/Orchestrator/Runner）。
2. `Portex` Web 管理台。
3. 部署脚本（Docker Compose + 生产 Helm/Ansible 二选一）。
4. 运维手册（监控、备份、回滚、故障处理）。
5. 安全基线文档（权限、密钥、挂载、网络）。
6. 开发者文档（模块图、事件协议、扩展点）。

---

## 15. 推荐目录结构（首版）

```text
portex/
  api/
    app/
      routers/
      services/
      models/
      schemas/
      middleware/
  orchestrator/
    scheduler/
    queue/
    dispatcher/
  runner/
    sdk_adapter/
    host_runner/
    container_runner/
    tools/
    protocols/
  web/
    src/
  shared/
    contracts/
    event_types/
  infra/
    docker/
    compose/
    migrations/
  tests/
    unit/
    integration/
    e2e/
  docs/
```

---

## 16. 立即执行建议（下一步）

1. 先落地 M0：建仓、基础骨架、CI、开发环境。
2. 用 1 周做“消息->runner->流式回传”最小 PoC（只支持 Web + 单用户）。
3. PoC 稳定后再扩多用户与容器配额，避免过早复杂化。

---

## 17. 参考资料

### HappyClaw 参考

1. 文章：`/home/zcxggmu/workspace/hello-projs/AGI-Research/posp/portex/happclaw.md`
2. 代码：`/home/zcxggmu/workspace/hello-projs/agents/happyclaw`

### OpenAI Agents SDK（本规划主要依据）

1. Quickstart：https://openai.github.io/openai-agents-python/quickstart/
2. Running agents：https://openai.github.io/openai-agents-python/running_agents/
3. Agents：https://openai.github.io/openai-agents-python/agents/
4. Tools：https://openai.github.io/openai-agents-python/tools/
5. Guardrails：https://openai.github.io/openai-agents-python/guardrails/
6. Streaming：https://openai.github.io/openai-agents-python/streaming/
7. Results：https://openai.github.io/openai-agents-python/results/
8. API Reference（Runner/Result/Items/Tools/Handoffs/Guardrails）：https://openai-agents-sdk.doczh.com/ref/
9. MCP：https://openai.github.io/openai-agents-python/mcp/
10. Tracing：https://openai.github.io/openai-agents-python/tracing/

### 中文站（用于中文术语对照）

1. https://openai-agents-sdk.doczh.com/
2. 当前目录深度梳理：`openai_agents_sdk.md`
