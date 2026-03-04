# Portex Task-by-Task Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 `Portex_Project_Plan.md` 落地为可执行工程计划，按阶段完成“Web + 多用户 + 容器隔离 + OpenAI Agents SDK 编排”的生产可用系统。

**Architecture:** 采用控制平面（API/Orchestrator/Scheduler）与执行平面（Runner/Container）分离架构；以 OpenAI Agents SDK 为运行内核，统一通过 `AgentRunService` 和标准事件协议接入前端与审计系统。

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL, Redis, Docker, OpenAI Agents SDK, React + Vite + TypeScript, Pytest, Playwright, Prometheus/Grafana, OpenTelemetry。

---

## 0. 目标仓库文件结构（实施目标）

```text
portex/
  pyproject.toml
  Makefile
  .env.example
  docker-compose.yml
  README.md

  api/
    app/
      main.py
      config.py
      deps.py
      middleware/
        auth.py
        request_id.py
      routers/
        auth.py
        flows.py
        chat.py
        files.py
        tasks.py
        admin.py
        ws.py
      schemas/
        auth.py
        flows.py
        chat.py
        tasks.py
      services/
        auth_service.py
        flow_service.py
        chat_service.py
        ws_service.py
      repositories/
        user_repo.py
        flow_repo.py
        message_repo.py
        run_repo.py
      security/
        crypto.py
        rbac.py

  orchestrator/
    app/
      main.py
      dispatcher.py
      retry.py
      idempotency.py
      queue/
        producer.py
        consumer.py
      policies/
        priority.py
        concurrency.py
      contracts/
        run_request.py
        run_result.py

  runner/
    app/
      main.py
      runtime/
        agent_run_service.py
        event_mapper.py
        exception_mapper.py
        context_builder.py
      sdk_adapter/
        agents_runner.py
        model_provider.py
        guardrail_adapter.py
      protocols/
        event_protocol.py
      host_runner/
        host_executor.py
      container_runner/
        container_executor.py
        sandbox_policy.py
      tools/
        file_tools.py
        memory_tools.py
        system_tools.py

  scheduler/
    app/
      main.py
      cron_runner.py
      interval_runner.py
      oneoff_runner.py

  web/
    package.json
    src/
      main.tsx
      app/
        router.tsx
        store.ts
      pages/
        Login.tsx
        Chat.tsx
        Files.tsx
        Tasks.tsx
        Monitor.tsx
        Settings.tsx
      components/
        ChatStream.tsx
        ToolTimeline.tsx
        RunStatusBar.tsx
      services/
        api.ts
        ws.ts
      types/
        events.ts
        models.ts

  shared/
    contracts/
      api_contracts.py
      ws_events.py
    event_types/
      stream_events.py
      audit_events.py

  infra/
    migrations/
      versions/
    docker/
      runner.Dockerfile
      api.Dockerfile
      web.Dockerfile
    compose/
      compose.dev.yml
      compose.prod.yml
    monitoring/
      prometheus.yml
      grafana/

  tests/
    unit/
      api/
      orchestrator/
      runner/
    integration/
      test_chat_flow.py
      test_runner_stream.py
      test_guardrails.py
      test_rbac.py
    e2e/
      test_chat_stream.spec.ts
      test_task_lifecycle.spec.ts

  docs/
    architecture/
      system-overview.md
      event-protocol.md
    runbooks/
      deploy.md
      rollback.md
      incident.md
    plans/
      2026-03-03-portex-task-by-task-implementation-plan.md
```

---

## 1. 阶段交付清单总览（M0-M5）

| 阶段 | 时间 | 核心目标 | 阶段交付物 |
|---|---|---|---|
| M0 | 第1-2周 | 工程基线 + 开发环境 | 代码骨架、CI、Compose 环境、基础迁移、健康检查 |
| M1 | 第3-5周 | 单用户最小闭环 | 登录、Flow、消息->Runner->流式回传、RunConfig基线 |
| M2 | 第6-8周 | 多用户与隔离 | RBAC、审计、并发配额、容器隔离策略 |
| M3 | 第9-11周 | 记忆与任务系统 | 记忆工具、任务调度、任务中心 UI |
| M4 | 第12-13周 | MCP与可观测性 | MCP注册与审批、Tracing 贯通、监控告警 |
| M5 | 第14-16周 | 灰度上线 | 压测、安全测试、发布/回滚、运行手册 |

---

## 2. Task-by-Task 实施计划

## M0：架构基线（第1-2周）

### Task M0-T01: 初始化仓库与工具链

**Files:**
- Create: `portex/pyproject.toml`
- Create: `portex/Makefile`
- Create: `portex/.editorconfig`
- Create: `portex/.env.example`
- Create: `portex/README.md`

**Steps:**
1. 创建 Python 项目基础依赖（FastAPI, SQLAlchemy, Redis, OpenAI Agents SDK, pytest）。
2. 定义 `make` 命令：`lint`, `test`, `run-api`, `run-orchestrator`, `run-runner`。
3. 写入环境变量模板（DB/Redis/OpenAI/Tracing/Runner 限额）。
4. 添加 README 的本地启动说明。

**Done when:**
1. `make -n` 可展示基础命令。
2. 新人按 README 能在 15 分钟内启动开发环境。

### Task M0-T02: 搭建服务目录骨架

**Files:**
- Create: `portex/api/app/main.py`
- Create: `portex/orchestrator/app/main.py`
- Create: `portex/runner/app/main.py`
- Create: `portex/scheduler/app/main.py`
- Create: `portex/shared/contracts/ws_events.py`

**Steps:**
1. 按目标结构创建目录与 `__init__.py`。
2. 各服务加入 `/healthz` 路由。
3. 共享层定义基础事件类型与错误码占位。

**Done when:**
1. 4 个服务均可本地启动并返回健康状态。

### Task M0-T03: 数据库与迁移基线

**Files:**
- Create: `portex/infra/migrations/env.py`
- Create: `portex/infra/migrations/versions/0001_init_core_tables.py`
- Create: `portex/api/app/models/base.py`
- Create: `portex/api/app/models/user.py`
- Create: `portex/api/app/models/flow.py`

**Steps:**
1. 初始化迁移框架。
2. 建立核心表：`users`, `flows`, `messages`, `agent_runs`, `audit_logs`。
3. 增加索引：`messages(flow_id, created_at)`、`agent_runs(flow_id, status)`。

**Done when:**
1. 全新数据库可一键迁移。
2. 回滚一版迁移可成功。

### Task M0-T04: 本地依赖编排（Compose）

**Files:**
- Create: `portex/docker-compose.yml`
- Create: `portex/infra/compose/compose.dev.yml`
- Create: `portex/infra/docker/api.Dockerfile`

**Steps:**
1. 配置 PostgreSQL、Redis、API 占位容器。
2. 定义健康检查和网络。
3. 统一日志与端口配置。

**Done when:**
1. `docker compose up -d` 后 DB/Redis healthy。

### Task M0-T05: CI 基线

**Files:**
- Create: `portex/.github/workflows/ci.yml`
- Create: `portex/tests/unit/test_smoke.py`

**Steps:**
1. CI 串联 `lint -> typecheck -> unit test`。
2. 增加 smoke test。
3. 配置失败阻断主分支合并。

**Done when:**
1. PR 中 CI 能完整跑通。

**M0 阶段交付清单：**
1. 可运行的 monorepo 骨架。
2. Compose 本地环境。
3. 初始数据库模型与迁移。
4. CI 可用。

---

## M1：最小闭环（第3-5周）

### Task M1-T01: 认证与会话

**Files:**
- Create: `portex/api/app/routers/auth.py`
- Create: `portex/api/app/services/auth_service.py`
- Create: `portex/api/app/middleware/auth.py`
- Create: `portex/api/app/schemas/auth.py`
- Test: `portex/tests/integration/test_auth_flow.py`

**Steps:**
1. 实现注册/登录/退出 API。
2. 建立 Cookie Session。
3. 中间件注入当前用户上下文。
4. 编写认证集成测试。

**Done when:**
1. 未登录访问受保护资源返回 401。
2. 登录后可访问 Flow API。

### Task M1-T02: Flow 与消息模型 API

**Files:**
- Create: `portex/api/app/routers/flows.py`
- Create: `portex/api/app/routers/chat.py`
- Create: `portex/api/app/services/flow_service.py`
- Create: `portex/api/app/services/chat_service.py`
- Test: `portex/tests/integration/test_flow_chat_crud.py`

**Steps:**
1. 实现 Flow 创建/查询。
2. 实现消息写入与历史拉取。
3. 关联消息与 Flow 权限校验。

**Done when:**
1. 单用户可创建多个 Flow 并独立存储消息。

### Task M1-T03: Runner SDK 执行基线

**Files:**
- Create: `portex/runner/app/runtime/agent_run_service.py`
- Create: `portex/runner/app/sdk_adapter/agents_runner.py`
- Create: `portex/runner/app/runtime/context_builder.py`
- Test: `portex/tests/unit/runner/test_agent_run_service.py`

**Steps:**
1. 封装 `Runner.run_streamed` 统一入口。
2. 注入 `RunConfig`（workflow_name/group_id/trace_metadata）。
3. 注入 `max_turns` 和默认异常处理。

**Done when:**
1. Runner 服务可执行简单 Agent 并返回最终输出。

### Task M1-T04: 事件映射与 WebSocket 通道

**Files:**
- Create: `portex/runner/app/runtime/event_mapper.py`
- Create: `portex/api/app/routers/ws.py`
- Create: `portex/api/app/services/ws_service.py`
- Create: `portex/shared/event_types/stream_events.py`
- Test: `portex/tests/integration/test_runner_stream.py`

**Steps:**
1. 映射 `raw_response_event/run_item_stream_event/agent_updated_stream_event`。
2. API 建立 WS 推送通道。
3. 实现 run_id 粒度订阅。

**Done when:**
1. 前端可实时收到 text/tool/status/error 事件。

### Task M1-T05: 标准异常映射

**Files:**
- Create: `portex/runner/app/runtime/exception_mapper.py`
- Modify: `portex/runner/app/runtime/agent_run_service.py`
- Modify: `portex/api/app/services/ws_service.py`
- Test: `portex/tests/integration/test_run_error_mapping.py`

**Steps:**
1. 映射 `MaxTurnsExceeded` -> `RUN_MAX_TURNS_EXCEEDED`。
2. 映射 `ModelBehaviorError` -> `RUN_MODEL_BEHAVIOR_ERROR`。
3. 映射 guardrail tripwire -> `RUN_GUARDRAIL_TRIPWIRE`。
4. WS 发送结构化错误事件。

**Done when:**
1. 前端可区分错误类型并显示可操作提示。

### Task M1-T06: Web Chat 最小 UI

**Files:**
- Create: `portex/web/src/pages/Chat.tsx`
- Create: `portex/web/src/components/ChatStream.tsx`
- Create: `portex/web/src/services/ws.ts`
- Test: `portex/tests/e2e/test_chat_stream.spec.ts`

**Steps:**
1. 实现消息发送与本地回显。
2. 实现流式增量渲染。
3. 支持 run 完成状态收敛。

**Done when:**
1. 单用户连续 20 轮对话无状态丢失。

**M1 阶段交付清单：**
1. 登录鉴权可用。
2. Flow/消息闭环。
3. Runner + WS 流式闭环。
4. 异常映射和前端可解释错误。

---

## M2：多用户与隔离（第6-8周）

### Task M2-T01: RBAC 权限模型

**Files:**
- Create: `portex/api/app/security/rbac.py`
- Create: `portex/api/app/models/role.py`
- Create: `portex/api/app/models/permission.py`
- Create: `portex/api/app/routers/admin.py`
- Test: `portex/tests/integration/test_rbac.py`

**Steps:**
1. 建立角色与权限模型。
2. API 路由加权限注解。
3. 增加权限拒绝审计日志。

**Done when:**
1. 不同角色访问控制符合预期。

### Task M2-T02: 多租户数据隔离

**Files:**
- Modify: `portex/api/app/repositories/*.py`
- Modify: `portex/api/app/services/*.py`
- Test: `portex/tests/integration/test_tenant_isolation.py`

**Steps:**
1. Repository 层强制 user_id 过滤。
2. Service 层新增越权访问拦截。
3. 补齐跨用户访问测试。

**Done when:**
1. 10 并发用户无消息/文件串扰。

### Task M2-T03: 调度并发与配额策略

**Files:**
- Create: `portex/orchestrator/app/policies/concurrency.py`
- Create: `portex/orchestrator/app/policies/priority.py`
- Create: `portex/orchestrator/app/dispatcher.py`
- Test: `portex/tests/unit/orchestrator/test_concurrency_policy.py`

**Steps:**
1. 实现会话串行、全局并发限流。
2. 实现优先级队列策略。
3. 为拒绝/排队状态定义统一返回码。

**Done when:**
1. 并发压力下任务执行顺序可预测。

### Task M2-T04: 幂等与重试

**Files:**
- Create: `portex/orchestrator/app/idempotency.py`
- Create: `portex/orchestrator/app/retry.py`
- Test: `portex/tests/integration/test_retry_idempotency.py`

**Steps:**
1. 设计 `flow_id + message_id` 幂等键。
2. 实现指数退避重试。
3. 区分可重试与不可重试错误。

**Done when:**
1. 重复请求不产生重复 run。

### Task M2-T05: 容器运行策略基线

**Files:**
- Create: `portex/runner/app/container_runner/container_executor.py`
- Create: `portex/runner/app/container_runner/sandbox_policy.py`
- Test: `portex/tests/integration/test_container_policy.py`

**Steps:**
1. 默认非 root 运行。
2. 配置最小挂载与禁用敏感路径。
3. 配置 CPU/内存/时长限制。

**Done when:**
1. 风险路径不可访问，资源限制生效。

**M2 阶段交付清单：**
1. 完整 RBAC。
2. 多租户隔离。
3. 调度/重试/幂等。
4. 容器策略与执行限制。

---

## M3：记忆与任务系统（第9-11周）

### Task M3-T01: 记忆目录与存储 API

**Files:**
- Create: `portex/api/app/routers/files.py`
- Create: `portex/runner/app/tools/memory_tools.py`
- Create: `portex/api/app/services/memory_service.py`
- Test: `portex/tests/integration/test_memory_files.py`

**Steps:**
1. 定义全局/Flow/日期记忆目录规范。
2. 提供写记忆与检索接口。
3. 添加路径归一化与越界防护。

**Done when:**
1. 跨会话可读写记忆并可检索。

### Task M3-T02: 记忆压缩与归档

**Files:**
- Create: `portex/runner/app/tools/memory_compaction.py`
- Create: `portex/api/app/services/archive_service.py`
- Test: `portex/tests/unit/runner/test_memory_compaction.py`

**Steps:**
1. 实现历史压缩策略。
2. 会话归档为 markdown。
3. 建立归档恢复机制。

**Done when:**
1. 长会话不会无限膨胀，恢复可用。

### Task M3-T03: 调度任务模型与 API

**Files:**
- Create: `portex/api/app/models/scheduled_task.py`
- Create: `portex/api/app/models/task_run_log.py`
- Create: `portex/api/app/routers/tasks.py`
- Test: `portex/tests/integration/test_task_crud.py`

**Steps:**
1. 建立 `cron/interval/once` 任务模型。
2. 实现任务增删改查。
3. 增加任务日志查询接口。

**Done when:**
1. 前端可创建并查询任务。

### Task M3-T04: Scheduler 执行器

**Files:**
- Create: `portex/scheduler/app/cron_runner.py`
- Create: `portex/scheduler/app/interval_runner.py`
- Create: `portex/scheduler/app/oneoff_runner.py`
- Test: `portex/tests/integration/test_scheduler_runtime.py`

**Steps:**
1. 扫描待执行任务。
2. 触发 orchestrator 下发 run。
3. 记录执行日志与重试次数。

**Done when:**
1. 重启后任务仍可恢复执行。

### Task M3-T05: 任务中心 UI

**Files:**
- Create: `portex/web/src/pages/Tasks.tsx`
- Create: `portex/web/src/components/RunStatusBar.tsx`
- Test: `portex/tests/e2e/test_task_lifecycle.spec.ts`

**Steps:**
1. 支持任务创建、暂停、恢复、取消。
2. 展示每次 run 状态和错误原因。

**Done when:**
1. 全任务生命周期可在 UI 完成。

**M3 阶段交付清单：**
1. 记忆系统与压缩归档。
2. 定时任务模型与执行器。
3. 任务中心可视化。

---

## M4：MCP 与可观测性（第12-13周）

### Task M4-T01: MCP 注册中心与配置

**Files:**
- Create: `portex/api/app/models/mcp_server.py`
- Create: `portex/api/app/routers/mcp.py`
- Create: `portex/runner/app/sdk_adapter/mcp_registry.py`
- Test: `portex/tests/integration/test_mcp_registry.py`

**Steps:**
1. 实现 MCP server 的租户级配置。
2. 支持 stdio/sse/streamable_http。
3. 提供启停与健康检查接口。

**Done when:**
1. MCP server 可按租户可控启用。

### Task M4-T02: MCP 审批与安全策略

**Files:**
- Create: `portex/runner/app/sdk_adapter/mcp_approval.py`
- Modify: `portex/runner/app/runtime/event_mapper.py`
- Test: `portex/tests/integration/test_mcp_approval.py`

**Steps:**
1. 处理 `mcp_approval_requested` 事件。
2. 实现人工审批回执流程。
3. 高风险工具默认拒绝。

**Done when:**
1. 未审批请求不会实际执行。

### Task M4-T03: Tracing 贯通

**Files:**
- Create: `portex/shared/contracts/tracing.py`
- Modify: `portex/runner/app/runtime/agent_run_service.py`
- Modify: `portex/api/app/services/chat_service.py`
- Test: `portex/tests/integration/test_trace_grouping.py`

**Steps:**
1. 每次运行写入 `workflow_name/trace_id/group_id`。
2. 将 run_id 与 trace_id 关联存储。
3. 增加 trace 查询 API。

**Done when:**
1. 同会话多轮运行可聚合查询。

### Task M4-T04: 监控与告警

**Files:**
- Create: `portex/infra/monitoring/prometheus.yml`
- Create: `portex/infra/monitoring/grafana/dashboards.json`
- Create: `portex/api/app/middleware/metrics.py`

**Steps:**
1. 上报 p95 latency、error rate、queue backlog。
2. 配置告警阈值与通知通道。

**Done when:**
1. 压测时仪表盘可实时反映系统状态。

### Task M4-T05: 监控页面 UI

**Files:**
- Create: `portex/web/src/pages/Monitor.tsx`
- Create: `portex/web/src/services/metrics.ts`

**Steps:**
1. 展示队列积压、并发占用、错误率。
2. 展示最近失败 run 列表与错误类型。

**Done when:**
1. 运维可在单页面定位热点问题。

**M4 阶段交付清单：**
1. MCP 注册 + 审批流程。
2. Trace 全链路关联。
3. 可观测指标与告警。
4. 监控 UI。

---

## M5：灰度上线（第14-16周）

### Task M5-T01: 压测基线

**Files:**
- Create: `portex/tests/perf/locustfile.py`
- Create: `portex/docs/runbooks/perf-baseline.md`

**Steps:**
1. 设计 10/50/100 并发场景。
2. 输出首 token、完成时延、错误率。

**Done when:**
1. 达到阶段目标或形成容量结论。

### Task M5-T02: 安全测试与修复

**Files:**
- Create: `portex/tests/security/test_path_traversal.py`
- Create: `portex/tests/security/test_permission_escalation.py`
- Modify: `portex/api/app/security/*.py`

**Steps:**
1. 路径穿越、越权、注入基线测试。
2. 修复并形成复测报告。

**Done when:**
1. 高风险漏洞清零，保留风险可接受。

### Task M5-T03: 发布与回滚脚本

**Files:**
- Create: `portex/infra/compose/compose.prod.yml`
- Create: `portex/scripts/deploy.sh`
- Create: `portex/scripts/rollback.sh`
- Create: `portex/docs/runbooks/deploy.md`
- Create: `portex/docs/runbooks/rollback.md`

**Steps:**
1. 固化灰度发布流程。
2. 固化一键回滚流程。
3. 编写故障演练手册。

**Done when:**
1. 演练可在 15 分钟内回滚。

### Task M5-T04: 运营交接与文档封板

**Files:**
- Create: `portex/docs/runbooks/incident.md`
- Create: `portex/docs/architecture/system-overview.md`
- Create: `portex/docs/architecture/event-protocol.md`

**Steps:**
1. 补齐架构文档与排障 runbook。
2. 形成上线前 checklist。
3. 组织一次交接 walkthrough。

**Done when:**
1. 开发、测试、运维三方签字确认上线。

**M5 阶段交付清单：**
1. 压测与容量报告。
2. 安全测试报告。
3. 可执行发布/回滚方案。
4. 运维与架构文档全集。

---

## 3. 并行实施编组（执行建议）

1. 小队 A（API + 数据）：M0/M1/M2 主导。
2. 小队 B（Runner + Orchestrator）：M1/M2/M4 主导。
3. 小队 C（Web）：M1/M3/M4 主导。
4. 小队 D（平台保障）：M0/M4/M5 主导。

每周固定节奏：

1. 周一拆任务与依赖确认。
2. 周三集成冒烟。
3. 周五阶段验收与风险清理。

---

## 4. 每阶段验收门禁（Go/No-Go）

1. M0 Gate: 环境启动成功率 100%，CI 通过率 100%。
2. M1 Gate: 单用户 20 轮稳定，流式链路无阻塞。
3. M2 Gate: 10 并发多租户隔离通过，越权测试通过。
4. M3 Gate: 任务调度重启恢复通过，记忆可检索。
5. M4 Gate: trace 全链路可追踪，告警可触发。
6. M5 Gate: 压测达标或容量边界明确，回滚演练成功。

---

## 5. 首周可执行任务包（马上开工）

1. 完成 M0-T01 到 M0-T03。
2. 建立首次 schema migration 并通过 CI。
3. 输出第一版 API/Runner 启动脚本。
4. 发起 M1-T01 认证接口开发。

