# Portex 实施计划（v2.0）

**项目**: Portex  
**文档版本**: 2.0  
**更新日期**: 2026-03-04  
**执行基线**: 对齐 `PORTEX_PLAN.md v3.0`

---

## 0. 执行规则（必须遵守）

1. 每个阶段必须先完成“退出标准”，再进入下一阶段。
2. 所有关键任务都要有可重复的验证命令（本地或 CI）。
3. 先做 MVP 主链路，再做增强能力；禁止前置过度工程。
4. 任何新增范围（功能/模块）都要记录到本文件并评审。
5. 任务完成声明必须附带证据（测试输出/日志/截图）。

---

## 1. 里程碑总览

| 里程碑 | 时间建议 | 目标 |
|---|---|---|
| M0 | Week 0-1 | 预研封板：确认运行时方案与事件契约 |
| M1 | Week 1-2 | 后端骨架：auth + db + health + 基础 API |
| M2 | Week 3-4 | 端到端链路：Web 消息 -> Agent -> 流式回传 |
| M3 | Week 5-7 | 执行隔离：容器/宿主机、队列、IPC、并发 |
| M4 | Week 8-10 | 多用户：RBAC、任务调度、记忆系统 |
| M5 | Week 11-12 | 通道扩展：飞书/Telegram（至少一条） |
| M6 | Week 13-14 | 安全加固、测试补齐、发布准备 |

---

## 2. 阶段任务清单

## 阶段 M0：预研与封板（Week 0-1）

| ID | 任务 | 主要文件 | 依赖 | 验证 |
|---|---|---|---|---|
| T0-01 | 定义 `RunRequest/RunResult/RunEvent` v1 | `docs/contracts/run-v1.md` | - | 契约评审通过 |
| T0-02 | 定义 WS 消息协议 v1 | `docs/contracts/ws-v1.md` | T0-01 | 前后端字段对齐检查 |
| T0-03 | OpenAI Agents SDK 流式 PoC | `sandbox/poc_agents_stream.py` | - | 可输出 token/tool 事件 |
| T0-04 | Codex CLI 调用 PoC（子进程） | `sandbox/poc_codex_cli.py` | - | 可请求并解析结果 |
| T0-05 | EventMapper PoC（SDK -> Portex） | `sandbox/poc_event_mapper.py` | T0-03 | 事件映射单测通过 |
| T0-06 | 运行时方案决策（A 主 B 兜底） | `docs/decisions/ADR-001-runtime.md` | T0-03~05 | ADR 评审通过 |
| T0-07 | 数据模型最小集合确认 | `docs/decisions/ADR-002-schema.md` | - | 表清单冻结 |
| T0-08 | 安全基线确认（auth/rbac/mount/audit） | `docs/security/baseline.md` | - | 安全项清单冻结 |

**M0 退出标准**
1. PoC 脚本可运行。
2. 契约文档与 ADR 完成并评审通过。
3. 进入 M1 前无未决“主链路技术路径”问题。

---

## 阶段 M1：平台骨架（Week 1-2）

| ID | 任务 | 主要文件 | 依赖 | 验证 |
|---|---|---|---|---|
| T1-01 | 初始化后端项目结构（FastAPI） | `portex/app/*` | T0-06 | `uvicorn` 可启动 |
| T1-02 | 配置管理与环境加载 | `portex/app/config.py` | T1-01 | 配置单测 |
| T1-03 | 结构化日志与请求 ID | `portex/app/logging.py` | T1-01 | 日志字段检查 |
| T1-04 | SQLite 初始化与 WAL | `portex/infra/db/engine.py` | T0-07 | 启动后 DB 可写 |
| T1-05 | 数据迁移机制（schema_version） | `portex/infra/db/migrate.py` | T1-04 | 迁移回归通过 |
| T1-06 | users/user_sessions DAO | `portex/infra/db/users.py` | T1-04 | DAO 单测 |
| T1-07 | auth 登录/登出/会话校验 | `portex/security/auth.py` | T1-06 | API 集成测试 |
| T1-08 | 基础中间件（auth/cors/rate-limit） | `portex/app/middleware/*` | T1-07 | 中间件测试 |
| T1-09 | health/ready/status 基础端点 | `portex/app/routes/monitor.py` | T1-01 | `/health` 200 |
| T1-10 | groups/chats/messages 最小 CRUD | `portex/app/routes/groups.py` | T1-04 | CRUD 测试 |
| T1-11 | 审计日志落库（auth 事件） | `portex/security/audit.py` | T1-06 | 审计写入测试 |

**M1 退出标准**
1. 登录态可用（Cookie 会话）。
2. 基础 CRUD 可用。
3. DB 迁移可重复执行且不破坏数据。

---

## 阶段 M2：运行时主链路（Week 3-4）

| ID | 任务 | 主要文件 | 依赖 | 验证 |
|---|---|---|---|---|
| T2-01 | 定义 `AgentRuntimeAdapter` 接口 | `portex/infra/runtime/base.py` | T0-06 | 接口单测 |
| T2-02 | 实现 `OpenAIAgentsRuntime` | `portex/infra/runtime/agents_runtime.py` | T2-01 | run_streamed PoC |
| T2-03 | 实现 `DirectCodexRuntime` 兜底 | `portex/infra/runtime/codex_runtime.py` | T2-01 | 子进程调用测试 |
| T2-04 | RuntimeFactory + 特性开关 | `portex/infra/runtime/factory.py` | T2-02/03 | 切换测试 |
| T2-05 | 实现 EventMapper（统一事件） | `portex/ws/event_mapper.py` | T0-01 | 映射单测 |
| T2-06 | 实现 RunService（request->result） | `portex/services/run_service.py` | T2-02 | 集成测试 |
| T2-07 | 实现 WS 连接管理与广播 | `portex/ws/manager.py` | T2-05 | WS 通信测试 |
| T2-08 | 实现 `/ws` 协议处理 | `portex/app/routes/ws.py` | T2-07 | websocket e2e |
| T2-09 | 实现消息入站 API（Web） | `portex/app/routes/messages.py` | T2-06 | API + WS e2e |
| T2-10 | 支持 cancel/timeout 语义 | `portex/services/run_control.py` | T2-06 | cancel 集成测试 |
| T2-11 | 流式事件持久化（最小） | `portex/infra/db/run_events.py` | T2-05 | 重放测试 |
| T2-12 | 端到端 Demo（单用户） | `docs/e2e/m2-checklist.md` | T2-01~11 | 手工验收通过 |

**M2 退出标准**
1. Web 端可流式看到 token/tool 事件。
2. 取消与超时生效。
3. 失败路径可返回结构化错误。

---

## 阶段 M3：执行隔离与编排（Week 5-7）

| ID | 任务 | 主要文件 | 依赖 | 验证 |
|---|---|---|---|---|
| T3-01 | Docker 镜像与 runner 入口 | `container/Dockerfile`, `container/entrypoint.sh` | M2 | 镜像构建成功 |
| T3-02 | Host 执行器（admin only） | `portex/infra/exec/host_runner.py` | T2-06 | host 执行测试 |
| T3-03 | Container 执行器 | `portex/infra/exec/container_runner.py` | T3-01 | container 执行测试 |
| T3-04 | 执行模式选择器（group 级） | `portex/infra/exec/factory.py` | T3-02/03 | 模式路由测试 |
| T3-05 | 文件 IPC 协议实现（input/messages/tasks） | `portex/infra/ipc/*` | T3-03 | IPC 集成测试 |
| T3-06 | sentinel 协议（_close/_interrupt） | `portex/infra/ipc/signals.py` | T3-05 | 中断/关闭测试 |
| T3-07 | GroupQueue（并发、串行键） | `portex/services/group_queue.py` | T3-04 | 队列单测 |
| T3-08 | 指数退避重试策略 | `portex/services/retry.py` | T3-07 | 重试单测 |
| T3-09 | scheduler 基础循环 | `portex/services/scheduler/loop.py` | T1-04 | 调度器测试 |
| T3-10 | run/task 游标提交语义 | `portex/services/cursor.py` | T3-07 | 消息不丢不重测 |
| T3-11 | mount allowlist 与路径安全 | `portex/security/mount_security.py` | T0-08 | 安全测试 |
| T3-12 | 运行恢复（重启后恢复 pending） | `portex/services/recovery.py` | T3-07 | 恢复测试 |

**M3 退出标准**
1. 容器/宿主机双模式可跑通。
2. 并发上限与重试机制生效。
3. `_close/_interrupt` 语义通过回归测试。

---

## 阶段 M4：多用户、任务与记忆（Week 8-10）

| ID | 任务 | 主要文件 | 依赖 | 验证 |
|---|---|---|---|---|
| T4-01 | RBAC 权限模型实现 | `portex/security/rbac.py` | M1 | 权限单测 |
| T4-02 | admin 用户管理 API | `portex/app/routes/admin_users.py` | T4-01 | API 测试 |
| T4-03 | invite codes API | `portex/app/routes/admin_invites.py` | T4-01 | API 测试 |
| T4-04 | group_members 与共享策略 | `portex/infra/db/group_members.py` | T1-04 | 权限场景测试 |
| T4-05 | scheduled_tasks DAO/API | `portex/infra/db/tasks.py`, `portex/app/routes/tasks.py` | T3-09 | CRUD 测试 |
| T4-06 | cron/interval/once 执行 | `portex/services/scheduler/*` | T4-05 | 调度集成测试 |
| T4-07 | task_run_logs 与查询 | `portex/infra/db/task_logs.py` | T4-05 | 日志 API 测试 |
| T4-08 | memory 服务（global/daily/search/get/append） | `portex/services/memory/*` | M3 | memory 单测 |
| T4-09 | memory API | `portex/app/routes/memory.py` | T4-08 | API 测试 |
| T4-10 | 工具授权策略中心（tool policy） | `portex/services/tool_policy.py` | T2-02 | 工具权限测试 |
| T4-11 | 审计扩展（配置/任务/工具） | `portex/security/audit.py` | T4-10 | 审计校验 |

**M4 退出标准**
1. 多用户隔离可验证（数据、执行、权限）。
2. 任务调度完整可用并可追踪。
3. 记忆工具可用并受权限控制。

---

## 阶段 M5：前端与通道接入（Week 11-12）

| ID | 任务 | 主要文件 | 依赖 | 验证 |
|---|---|---|---|---|
| T5-01 | 前端项目骨架与路由 | `web/src/*` | M2 | 前端可启动 |
| T5-02 | 登录/注册/会话管理页面 | `web/src/pages/auth/*` | M1 | auth e2e |
| T5-03 | 聊天主界面（消息列表+输入） | `web/src/pages/chat/*` | T5-01 | 聊天 e2e |
| T5-04 | 流式事件渲染面板 | `web/src/components/stream/*` | T2-05 | 流式 e2e |
| T5-05 | 系统监控页 | `web/src/pages/monitor/*` | M3 | 监控展示 |
| T5-06 | 飞书接入（优先） | `portex/infra/im/feishu.py` | M4 | 飞书链路 e2e |
| T5-07 | Telegram 接入（次优） | `portex/infra/im/telegram.py` | M4 | Telegram e2e |
| T5-08 | IM 路由与 owner 解析 | `portex/infra/im/manager.py` | T5-06/07 | 多通道路由测试 |
| T5-09 | 配置页（模型/通道/系统参数） | `web/src/pages/settings/*` | M4 | 设置 e2e |

**M5 退出标准**
1. Web 端核心功能可用。
2. 至少一个 IM 通道全链路通过。
3. 前后端契约无未解决字段差异。

---

## 阶段 M6：加固、测试与发布（Week 13-14）

| ID | 任务 | 主要文件 | 依赖 | 验证 |
|---|---|---|---|---|
| T6-01 | 安全回归（路径、挂载、权限） | `tests/security/*` | M5 | 安全测试通过 |
| T6-02 | 登录限流与异常防护 | `portex/security/rate_limit.py` | M1 | 压测/单测 |
| T6-03 | 配置加密与脱敏回归 | `portex/security/crypto.py` | M4 | 加密测试 |
| T6-04 | WebSocket 断线重连与事件重放 | `portex/ws/replay.py` | M2 | 重连测试 |
| T6-05 | E2E 用例（登录/聊天/任务/通道） | `tests/e2e/*` | M5 | e2e 通过 |
| T6-06 | 单元+集成覆盖率达标 | `tests/**` | M5 | 覆盖率报告 |
| T6-07 | 性能基线（并发/延迟） | `scripts/bench/*` | M3 | benchmark 报告 |
| T6-08 | 部署文档与运维手册 | `docs/deployment.md` | M5 | 文档评审 |
| T6-09 | Release Checklist 与版本发布 | `docs/release-checklist.md` | T6-01~08 | checklist 全绿 |
| T6-10 | v1.0 标签与镜像发布 | `CHANGELOG.md`, `VERSION` | T6-09 | 发布完成 |

**M6 退出标准**
1. 测试（unit/integration/e2e）通过。
2. 安全与性能基线达标。
3. 文档完整，可独立部署。

---

## 3. 测试与验收矩阵

| 领域 | 最低要求 |
|---|---|
| 单元测试 | 核心模块覆盖率 >= 80% |
| 集成测试 | auth、message、runtime、queue、scheduler 必测 |
| E2E | 登录、聊天流式、任务调度、至少 1 个 IM 通道 |
| 安全测试 | 路径遍历、越权访问、挂载绕过、会话过期 |
| 稳定性 | 24h soak test 无致命错误 |

---

## 4. 关键依赖与并行建议

1. 可并行
   - 前端页面开发（M5）与 IM 接入（M5）
   - memory 服务（M4）与调度日志（M4）
2. 不可并行（需先后）
   - 契约冻结（M0） -> 运行链路（M2）
   - 执行隔离（M3） -> 多用户与任务（M4）
   - 核心链路稳定（M2~M4） -> 发布准备（M6）

---

## 5. 文档维护规则

1. 新增任务必须写明：目标、依赖、验证方式。
2. 已完成任务需标注完成日期和证据链接。
3. 每个里程碑完成后更新“风险状态”和“剩余问题”。

---

**结论**: 该版本将原先“大而全任务列表”改为“可执行里程碑 + 强验证门槛”的实施计划，可直接用于实际开发排期与执行。
