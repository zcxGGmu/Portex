# Portex 项目规划文档（OpenAI Agents SDK 增强版）

> 更新时间：2026-03-03
> 规划目标：基于 Python + OpenAI Agents SDK 构建具备 Web 界面与容器隔离能力的远程 AI Agent 服务

## 1. 背景与目标

## 1.1 背景
Portex 参考 happyclaw 的工程经验（Web 实时交互、任务编排、容器隔离、多租户），但在 Agent 运行时选型上，明确从 `Claude Agent SDK` 迁移为 `OpenAI Agents SDK`。

## 1.2 总体目标
1. 提供可远程访问的 Agent 服务（Web First）。
2. 通过容器隔离实现多租户安全执行。
3. 使用 OpenAI Agents SDK 提供标准化的 Agent/Tool/Handoff/Guardrail/Tracing 能力。
4. 从单机 MVP 平滑演进到多实例生产部署。

## 1.3 成功标准
1. 从消息发送到首个流式事件 P95 < 5s。
2. 非取消场景执行成功率 >= 99%。
3. 高危操作 100% 审计覆盖。
4. 多实例部署下无重复消费与跨租户数据泄露。

---

## 2. 关键输入结论

## 2.1 来自 happyclaw 的保留能力
1. 会话级串行 + 全局并发调度模式。
2. 流式事件驱动的 Web 交互模型。
3. 定时任务与即时对话共用执行框架。
4. 多租户边界（用户/工作区/凭据/审计）需一体化设计。

## 2.2 来自 OpenAI Agents SDK 的新增能力
1. `Agent` / `Runner` / `Tools` / `Handoffs` / `Guardrails` / `Tracing` 为一等能力。
2. `Runner.run_streamed()` 可直接承载 Portex 的实时事件链路。
3. `RunContextWrapper` 适合承载租户与权限上下文。
4. MCP 对接机制可复用现有工具生态。

---

## 3. 架构总览（Portex v1）

## 3.1 分层架构
1. **Gateway 层**：FastAPI（REST + WebSocket），处理鉴权、RBAC、租户识别。
2. **Orchestration 层**：会话调度、任务队列、run 状态机、幂等控制。
3. **Agent Runtime 层（OpenAI Agents SDK）**：
- AgentFactory
- RunnerExecutor
- ToolRegistry
- HandoffPolicy
- GuardrailEngine
- EventMapper
4. **Sandbox 层**：容器生命周期、挂载策略、网络与资源限制。
5. **State 层**：PostgreSQL + Redis + 对象存储（可选）。
6. **Observability 层**：Tracing、Metrics、Logs、Audit。

## 3.2 关键原则
1. 控制面与执行面解耦。
2. 平台事件协议与 SDK 原生对象解耦。
3. 默认容器隔离，宿主执行需审批。
4. 租户隔离、权限控制、审计留痕同步设计。

## 3.3 OpenAI Agents SDK 组件映射
1. Portex `agent_profile` -> SDK `Agent(name/instructions/model/tools/handoffs)`。
2. Portex `run_engine` -> SDK `Runner.run / run_streamed`。
3. Portex `tool_center` -> SDK Function Tools + MCP Tools + Hosted Tools。
4. Portex `delegation_policy` -> SDK Handoffs + input filter + enable switch。
5. Portex `safety_policy` -> SDK Input/Output Guardrails + tripwire。
6. Portex `trace_pipeline` -> SDK tracing + 平台 OTel 链路。

---

## 4. OpenAI Agents SDK 驱动的运行时设计

## 4.1 AgentFactory
职责：根据租户、角色、会话态动态组装 Agent。

输入：
1. tenant_id / user_id / workspace_id
2. 安全策略与可见工具列表
3. 会话历史摘要与系统策略

输出：
1. 主 Agent（Manager）
2. 可选专家 Agent 列表（handoffs）

## 4.2 RunnerExecutor
职责：封装 SDK 执行入口并统一错误处理。

执行模式：
1. `run_sync`：仅内部调试工具使用。
2. `run`：后台任务与非流式执行。
3. `run_streamed`：Web 交互主路径。

统一能力：
1. 超时控制
2. 取消控制
3. 重试策略
4. 幂等 run_id

## 4.3 EventMapper
职责：将 SDK 事件标准化为 Portex 事件。

映射建议：
1. `RawResponsesStreamEvent` -> `run.token.delta`
2. `RunItemStreamEvent` -> `run.item`
3. `AgentUpdatedStreamEvent` -> `run.agent.switched`
4. final_output -> `run.completed`
5. guardrail tripwire -> `run.blocked`

## 4.4 SessionManager
职责：管理跨轮会话上下文。

策略：
1. SDK Session（开发期可用 SQLiteSession）。
2. 生产期以平台 DB 为主存储，SDK Session 仅做适配层。
3. 长会话采用摘要压缩 + 最近窗口双层策略。

## 4.5 ToolRegistry
职责：统一注册和治理工具调用。

分类：
1. Function tools（内部业务函数）
2. MCP tools（外部工具生态）
3. Hosted tools（平台支持时按租户启用）

治理机制：
1. 工具白名单
2. 参数校验
3. 调用限流
4. 调用审计

## 4.6 GuardrailEngine
职责：统一输入/输出护栏。

规则：
1. 输入护栏：越权请求、命令注入、敏感数据请求。
2. 输出护栏：PII 泄露、违规内容、越权结果。
3. tripwire 触发后中断 run 并写入审计告警。

---

## 5. 数据模型（v2）

## 5.1 业务核心表
1. `tenants`
2. `users`
3. `memberships`
4. `workspaces`
5. `sessions`
6. `messages`
7. `agent_runs`
8. `run_events`
9. `scheduled_tasks`
10. `audit_logs`
11. `secrets`

## 5.2 新增 SDK 相关表
1. `agent_profiles`：Agent 模板（instructions/model/tools/handoffs 策略）。
2. `handoff_records`：多 Agent 委派轨迹。
3. `tool_invocations`：工具调用明细（入参摘要、耗时、结果摘要、是否失败）。
4. `guardrail_hits`：护栏命中记录。
5. `trace_spans`（可选）: SDK tracing 的结构化镜像。

## 5.3 关键约束
1. 所有业务数据强制 `tenant_id`。
2. `run_events` append-only。
3. `tool_invocations` 必须关联 `agent_run_id`。
4. `guardrail_hits` 必须可追溯到具体输入与策略版本。

---

## 6. API 与实时协议（v2）

## 6.1 REST API
1. `POST /api/v1/auth/login`
2. `POST /api/v1/auth/logout`
3. `GET /api/v1/me`
4. `GET /api/v1/workspaces`
5. `POST /api/v1/sessions`
6. `GET /api/v1/sessions/{id}/messages`
7. `POST /api/v1/sessions/{id}/messages`
8. `POST /api/v1/runs/{id}/cancel`
9. `GET /api/v1/tasks`
10. `POST /api/v1/tasks`
11. `PATCH /api/v1/tasks/{id}`
12. `GET /api/v1/audit-logs`
13. `GET /api/v1/agent-profiles`
14. `PUT /api/v1/agent-profiles/{id}`
15. `GET /api/v1/runs/{id}/trace`

## 6.2 WebSocket 事件（建议）
1. `message.created`
2. `run.started`
3. `run.token.delta`
4. `run.item`
5. `run.agent.switched`
6. `run.tool.started`
7. `run.tool.completed`
8. `run.guardrail.hit`
9. `run.completed`
10. `run.failed`
11. `run.cancelled`
12. `task.triggered`
13. `task.completed`
14. `system.alert`

## 6.3 协议治理
1. 事件 `type + version` 双键。
2. 向后兼容至少 1 个次版本周期。
3. 发布前通过契约测试（Consumer-Driven Contract）。

---

## 7. 容器隔离与安全

## 7.1 执行模式
1. `container`（默认）：普通用户与默认工作负载。
2. `host`（受控）：仅管理员+审批+短时授权。

## 7.2 容器基线
1. rootless 用户。
2. `cap-drop=ALL`。
3. `no-new-privileges`。
4. read-only rootfs + 独立可写工作目录。
5. CPU/内存/PID/磁盘限制。
6. 默认 deny egress，按域名/地址放行。
7. 挂载白名单与路径校验。

## 7.3 工具安全
1. 所有工具调用走 ToolRegistry。
2. 高危工具强制二次确认。
3. 工具执行日志与参数摘要落库。

## 7.4 秘钥管理
1. KMS 或主密钥分域加密。
2. 租户级 key scope。
3. 短时 token 注入，避免长期明文存在运行时。

---

## 8. 调度与并发

## 8.1 调度策略
1. 会话串行（同 session 同时仅 1 run）。
2. 租户并发配额。
3. 全局并发与队列长度限制。
4. 优先级：系统任务 > 交互任务 > 批处理。

## 8.2 故障处理
1. 超时自动取消。
2. 可恢复错误指数退避重试。
3. 死信队列 + 人工重放。
4. 幂等键防重复执行。

## 8.3 多实例一致性
1. Redis 分布式锁。
2. 数据库乐观锁/状态版本号。
3. 事件去重键（run_id + seq）。

---

## 9. Web 产品范围（MVP）

## 9.1 页面
1. 登录与租户切换。
2. 会话与消息页。
3. 实时执行面板（Token/Tool/Handoff/Guardrail）。
4. 任务中心。
5. 监控状态页。
6. 管理后台（用户/角色/配额/审计）。

## 9.2 关键体验
1. 流式输出稳定。
2. 断线重连与状态恢复。
3. 历史分页与增量加载。
4. 可追踪每次工具调用与 Agent 切换。

---

## 10. 里程碑（18-22 周）

### P0：技术冻结（1-2 周）
1. 冻结架构与协议（REST/WS/Event）。
2. 冻结 SDK 版本与模型策略。
3. 输出威胁模型。

验收：
1. RFC 评审通过。
2. 协议评审通过。

### P1：控制平面骨架（2-3 周）
1. FastAPI + 鉴权 + RBAC。
2. PostgreSQL/Alembic 初始化。
3. WS 通道与最小事件广播。

验收：
1. 登录与会话基础可用。
2. message.created 可实时下发。

### P2：OpenAI Agents SDK 最小闭环（3-4 周）
1. AgentFactory。
2. RunnerExecutor（run + run_streamed）。
3. EventMapper（SDK -> Portex）。
4. 基础 Session 管理。

验收：
1. 对话可流式完成。
2. run 生命周期可追踪。

### P3：Tools + MCP + Handoffs（3-4 周）
1. Function tools 接入。
2. MCP 连接器接入。
3. 多 Agent handoff 策略。

验收：
1. 工具调用成功且有审计。
2. 多 Agent 委派可稳定复现。

### P4：Guardrails + 安全强化（3 周）
1. 输入/输出护栏。
2. tripwire 拦截链路。
3. 容器安全参数全量接入。

验收：
1. 高风险输入被拦截。
2. 越权输出被阻断并记录。

### P5：生产化扩展（4-6 周）
1. Redis 队列/锁与多实例。
2. Tracing + Metrics + Logs。
3. 压测与故障演练。

验收：
1. 多实例一致性通过。
2. SLO 达标并有告警策略。

---

## 11. 质量保障

## 11.1 测试分层
1. 单元：权限、状态机、guardrail 规则、事件映射。
2. 集成：API + DB + Redis + SDK adapter。
3. E2E：Web -> API -> Runner -> WS。
4. 安全：注入、越权、路径遍历、容器逃逸模拟。

## 11.2 验收指标
1. 执行成功率 >= 99%。
2. 首事件 P95 < 5s。
3. 系统可用性 >= 99.9%。
4. 审计覆盖率 = 100%。

---

## 12. 风险与缓解（SDK 维度）

1. **SDK 升级破坏兼容**
- 缓解：固定版本 + 契约测试 + 灰度升级。

2. **事件类型变化影响前端**
- 缓解：EventMapper 隔离层 + 内部统一事件协议。

3. **工具权限扩散**
- 缓解：ToolRegistry 二次授权 + 审计 + 限流。

4. **Handoff 路由不可控**
- 缓解：handoff 白名单 + 输入过滤 + 动态开关。

5. **Tracing 数据膨胀**
- 缓解：采样、分级存储、保留策略。

---

## 13. 组织实施建议

1. 设立三条并行工作流：
- 控制平面（API/数据/调度）
- SDK Runtime（Agent/Runner/Tools/Handoff/Guardrails）
- 前端交互（WS/可观测）

2. 每周双评审：
- 架构评审（协议与安全边界）
- 可用性评审（演示 + 指标）

3. 完成定义（DoD）：
- 功能 + 测试 + 审计 + 监控 + 回滚。

---

## 14. 立即启动任务（两周内）

1. 固定 OpenAI Agents SDK 版本并完成 PoC。
2. 定义 `PortexRunEvent` 统一事件协议。
3. 实现 AgentFactory 与最小 run_streamed 链路。
4. 实现 Function Tool 审计闭环。
5. 接入首个 MCP server。
6. 实现 InputGuardrail + OutputGuardrail 样例。
7. 落地容器安全启动模板。

---

## 15. 结论

Portex 的核心不是重造 Agent，而是将 OpenAI Agents SDK 的能力稳定地产品化：
1. 用 SDK 提供标准化 Agent 运行语义。
2. 用平台补齐多租户、安全、审计、可观测、扩展性。
3. 用事件与协议层解耦保证长期演进。

该路线能够在工程复杂度可控的前提下，实现“可远程、可协作、可监管”的 Agent 服务平台。
