# Portex 项目整体规划（v3.0）

**项目名称**: Portex  
**文档版本**: 3.0  
**更新日期**: 2026-03-04  
**文档状态**: 可执行草案（建议作为当前唯一规划基线）

---

## 1. 项目目标与边界

### 1.1 项目定位

Portex 是一个基于 **OpenAI Agents SDK（Python）** 的多用户远程 AI Agent 平台，提供：

1. Web 实时会话界面（含流式事件）
2. 容器隔离执行（member 默认）
3. 宿主机执行（admin 可选）
4. 飞书 / Telegram / Web 三通道接入
5. 以 Codex CLI 为核心编码执行能力

### 1.2 v1 必须交付（Must Have）

1. 单机部署可用（Docker + SQLite + FastAPI + React）
2. 多用户登录与会话隔离可用（RBAC + 审计）
3. 基础聊天链路可用（Web -> Agent -> 流式回传）
4. 容器模式稳定可用（启动、超时、关闭、重试）
5. 至少 6 个 MCP/平台工具可用（`send_message`、`schedule_task`、`list/pause/resume/cancel_task`、`memory_search/get/append`）
6. 定时任务可用（cron / interval / once）
7. 飞书与 Telegram 至少打通其一（另一个可放 v1.1）

### 1.3 v1 非目标（Non-goals）

1. Kubernetes/多节点调度
2. 复杂计费系统
3. 企业 SSO（OIDC/SAML）
4. 全量插件市场
5. 强一致分布式队列

### 1.4 成功指标（v1）

1. P95 Web 首 token 延迟 < 3s（非冷启动）
2. 消息丢失率 < 0.1%
3. 24h 稳定运行无进程崩溃
4. 关键链路测试通过率 100%（消息、容器、任务、鉴权）
5. 最小回归测试集每次 CI 必跑并稳定

---

## 2. 核心设计原则

1. **运行时可替换**：通过 `AgentRuntimeAdapter` 隔离 SDK/CLI 变动。
2. **契约先行**：先定义 Run/Event 协议，再做前后端实现。
3. **默认隔离**：容器默认启用；宿主机模式需显式权限。
4. **最小可用优先**：先做可运行 MVP，再逐步增强。
5. **证据驱动完成**：阶段完成必须附带测试与验证输出。

---

## 3. 总体架构

### 3.1 逻辑架构

```
Client Layer
  Web UI / Feishu / Telegram
        |
Gateway Layer
  FastAPI REST + WebSocket
        |
Orchestration Layer
  GroupQueue + Scheduler + Session Router + IPC Watcher
        |
Runtime Layer
  AgentRuntimeAdapter
   |- OpenAIAgentsRuntime (主路径)
   |- DirectCodexRuntime (兜底/迁移路径)
        |
Execution Layer
  Host Process (admin only) / Docker Container (default)
        |
Storage Layer
  SQLite + Filesystem (ipc/sessions/memory/skills/config)
```

### 3.2 关键边界

1. **控制面**（Control Plane）
   - 用户认证、会话路由、群组管理、配置管理、审计管理
2. **执行面**（Execution Plane）
   - Agent 执行、工具调用、容器生命周期、流式事件回传
3. **适配层**（Adapter Boundary）
   - 屏蔽 OpenAI Agents SDK/Codex CLI 细节，向上暴露稳定接口

### 3.3 运行时接口（建议）

```python
class AgentRuntimeAdapter(Protocol):
    async def run_streamed(self, request: RunRequest, emit: Callable[[RunEvent], Awaitable[None]]) -> RunResult:
        ...
    async def cancel(self, run_id: str) -> None:
        ...
```

---

## 4. OpenAI Agents SDK 与 Codex CLI 集成策略

### 4.1 方案对比

1. **方案 A（推荐）**：OpenAI Agents SDK 主导 + Codex CLI 作为受控工具能力
   - 优点：统一 Runner/Tracing/Guardrails/Handoffs 语义
   - 风险：Codex 工具能力和权限边界需严格治理

2. **方案 B**：双运行时并存（普通会话走 SDK，编码任务直连 Codex CLI）
   - 优点：编码任务能力保真，迁移灵活
   - 风险：状态机与事件模型复杂度显著上升

### 4.2 v1 决策

采用 **方案 A 为主，方案 B 兜底**：

1. 主链路使用 OpenAI Agents SDK（满足项目定位）
2. 预留 `DirectCodexRuntime` 作为降级路径
3. 前端永远只接收 Portex 自定义事件，不直接依赖 SDK 原生事件

---

## 5. 平台契约（Run/Event）

### 5.1 RunRequest（v1）

```json
{
  "contract_version": "portex.run.v1",
  "request_id": "uuid",
  "tenant_id": "t_xxx",
  "user_id": "u_xxx",
  "session_id": "s_xxx",
  "channel": "web|feishu|telegram",
  "message": {"role": "user", "content": [{"type": "text", "text": "..."}]},
  "limits": {"max_turns": 12, "run_timeout_ms": 120000, "tool_timeout_ms": 30000},
  "tool_policy": {"allow": ["send_message", "memory_search"], "mcp_servers": ["srv_a"]}
}
```

### 5.2 RunResult（v1）

```json
{
  "contract_version": "portex.run.v1",
  "request_id": "uuid",
  "run_id": "run_xxx",
  "status": "completed|failed|blocked|cancelled|timeout",
  "final_output": {"type": "text", "text": "..."},
  "error": {"code": "", "message": "", "retryable": false},
  "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
  "timing": {"started_at": "ISO8601", "completed_at": "ISO8601", "latency_ms": 0},
  "trace": {"trace_id": "trace_xxx"}
}
```

### 5.3 RunEvent（v1）

```json
{
  "event_version": "1.0",
  "event_type": "run.started|run.token.delta|run.tool.started|run.tool.completed|run.agent.switched|run.guardrail.hit|run.completed|run.failed|run.cancelled",
  "run_id": "run_xxx",
  "request_id": "uuid",
  "seq": 1,
  "ts": "ISO8601",
  "payload": {}
}
```

---

## 6. 模块规划（目标结构）

### 6.1 后端（`portex/`）

1. `app/`：FastAPI 启动、路由注册、中间件
2. `domain/`：核心业务模型（user/group/message/task/session）
3. `infra/db/`：SQLite DAO、迁移、事务封装
4. `infra/runtime/`：`AgentRuntimeAdapter` + runtime 实现
5. `infra/exec/`：container/host 执行器、IPC 协议
6. `infra/im/`：飞书/Telegram 连接与路由
7. `services/`：group queue、scheduler、memory、skills
8. `ws/`：事件映射、连接管理、重放/重连
9. `security/`：auth、rbac、crypto、audit、rate limit

### 6.2 Runner（`container/agent-runner/`）

1. `runner.py`：stdin 读取、运行循环、stdout 分帧
2. `event_mapper.py`：SDK 事件 -> Portex 事件
3. `tools/`：平台工具（memory/task/message）
4. `ipc/`：输入消息、关闭/中断信号处理

### 6.3 前端（`web/`）

1. Auth（登录/注册/设置向导）
2. Chat（消息、流式、会话切换）
3. Monitor（队列/容器/系统状态）
4. Settings（模型、通道、权限可见配置）

---

## 7. 数据模型（核心表）

### 7.1 必需表

1. `users`
2. `user_sessions`
3. `invite_codes`
4. `auth_audit_log`
5. `registered_groups`
6. `group_members`
7. `chats`
8. `messages`
9. `sessions`（复合主键：`group_folder + agent_id`）
10. `scheduled_tasks`
11. `task_run_logs`
12. `agents`
13. `router_state`

### 7.2 存储策略

1. 对话与运行态状态使用 SQLite（WAL）
2. 大对象与运行时文件使用文件系统（`data/`）
3. 密钥与第三方凭据统一 AES-256-GCM 加密存储

---

## 8. 安全与多租户策略

1. 登录态使用 HttpOnly Session Cookie（Web）
2. RBAC + 组级访问控制（owner/member/admin）
3. 宿主机模式仅 admin 可用
4. 路径安全：realpath + traversal 防护 + symlink 防护
5. 挂载安全：allowlist + blocked patterns + non-main 只读策略
6. 审计：登录、权限变更、配置变更、任务变更、工具调用
7. 限流：登录与关键写接口必须限流

---

## 9. 可观测性与可靠性

1. 日志：结构化日志（`request_id/run_id/trace_id/user_id/group_folder`）
2. 指标：活跃运行数、队列长度、失败率、重试次数、平均延迟
3. 追踪：默认开启 tracing，trace_id 贯穿 WS 和日志
4. 可靠性：
   - 指数退避重试（可配置）
   - run/tool 超时分层控制
   - cancel/interrupt 语义可验证
   - 重启恢复（pending message/task recovery）

---

## 10. 里程碑与阶段门槛

| 里程碑 | 目标 | 退出标准 |
|---|---|---|
| M0 预研封板 | 集成路径与契约定稿 | 完成 3 个 PoC：SDK 流式、Codex 调用、事件映射 |
| M1 核心骨架 | 后端框架与基础表可用 | `/health`、auth、group/message CRUD、迁移脚本可运行 |
| M2 运行链路 | Web -> Runtime -> WS 流式 | 单用户端到端稳定，支持 cancel/timeout |
| M3 容器隔离 | container/host 双模式 | 容器启动、挂载安全、并发限制、优雅关闭通过测试 |
| M4 多用户与任务 | RBAC、scheduler、memory | 多用户隔离验证、定时任务可执行并可追踪 |
| M5 IM 接入 | 飞书/Telegram 通道 | 至少一条 IM 渠道全链路打通并稳定 |
| M6 发布 | v1 发布准备 | 回归测试通过、文档完整、镜像可发布 |

---

## 11. 关键风险与缓解

1. **SDK 版本变更导致事件破坏**
   - 缓解：事件映射层 + 契约回放测试
2. **Codex CLI 接入权限面过大**
   - 缓解：工具白名单 + 容器隔离 + 审计
3. **多通道路由串扰**
   - 缓解：严格 `group_folder + owner` 绑定策略
4. **消息丢失/重复**
   - 缓解：cursor 提交语义测试 + 幂等键
5. **宿主机模式安全边界薄弱**
   - 缓解：默认关闭，admin 显式启用，操作审计

---

## 12. 需确认决策（启动前）

1. v1 是否强制同时交付飞书和 Telegram（或先交付其一）
2. v1 是否启用宿主机模式（默认建议关闭）
3. 记忆文件命名是否保持 `CLAUDE.md` 兼容
4. 是否要求对 HappyClaw API 100% 兼容，还是仅行为兼容

---

## 13. 参考资料

1. HappyClaw 仓库与文档
2. OpenAI Agents SDK 文档（官方）
3. Codex CLI 文档（官方）
4. FastAPI / React / SQLite 官方文档

---

**结论**: 本规划将项目从“功能罗列”调整为“可交付路线图”。建议与 `PORTEX_TASKS.md` 绑定执行，任何新增范围需走里程碑变更评审。
