# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-08 (Asia/Shanghai)
仓库路径: `/home/zcxggmu/workspace/hello-projs/posp/Portex`
当前分支: `main`

---

## 1. 当前阶段

- `M0` 已完成。
- `M1` 已完成（`M1.1` ~ `M1.6`）。
- `M2` 已完成（`M2.1` ~ `M2.6.1`）。
- `M3.1` 已完成（`M3.1.1` ~ `M3.1.3`）。
- `M3.2` 已完成（`M3.2.1` ~ `M3.2.3`）。
- `M3.3` 已完成（`M3.3.1` ~ `M3.3.3`）。
- `M3.4.1` 已完成（容器启动编排层）。
- `M3.4.2` 已完成（容器停止编排层）。
- `M3.4.3` 已完成（容器健康检查）。
- `M3.4.4` 已完成（优雅关闭）。
- `M3.5.1` 已完成（宿主机进程运行器）。
- `M3.5.2` 已完成（模式选择逻辑）。
- `M3.5.3` 已完成（宿主机模式安全限制）。
- `M3` 已完成（`M3.1` ~ `M3.6`）。
- `M4.1.1` 已完成（扩展用户模型）。
- `M4.1.2` 已完成（实现用户管理 API）。
- `M4.1.3` 已完成（实现邀请码系统）。
- `M4.2.1` 已完成（定义权限模板）。
- `M4.2.2` 已完成（实现权限检查装饰器）。
- `M4.2.3` 已完成（实现群组成员管理）。
- `M4.3.1` 已完成（实现任务调度器）。
- `M4.3.2` 已完成（实现任务 CRUD API）。
- `M4.3.3` 已完成（实现任务执行日志）。
- `M4.4.1` 已完成（实现 `AGENTS.md` 用户全局记忆管理）。
- `M4.4.2` 已完成（实现日期记忆）。
- `M4.4.3` 已完成（实现记忆搜索）。
- `M4.4.4` 已完成（实现 MCP 工具包装）。
- `M4.5` 已完成（M4 阶段验收）。
- `M4` 已完成（`M4.1` ~ `M4.5`）。
- `M5.1.1` 已完成（创建飞书客户端）。
- 当前起点：`M5.1.2`（实现 WebSocket 事件接收）。

---

## 2. 最近完成

- `M4.3.2`：补齐 `domain/schemas.py` 任务 DTO、新增薄层 `services/task_service.py`，将当前 in-memory `TaskScheduler` 暴露为最小 create/list/delete 服务边界。
- `M4.3.2`：实现并挂载 `/tasks` CRUD API：`POST /tasks`、`GET /tasks`、`DELETE /tasks/{task_id}`；继续沿用 `tasks` 资源权限模板，`owner/admin` 可写、`member` 只读。
- `M4.3.2`：补齐任务服务与任务路由测试，覆盖 create/list/delete、鉴权、权限差异与非法调度载荷校验。
- `M4.3.2`：根据代码评审补齐任务 API 的时间契约测试；对外请求/响应统一按 UTC 表达，服务内部继续维持 scheduler 现有的 naive UTC 运行态。
- `M4.3.3`：新增正式 `TaskRunLog` 模型契约与 in-memory `task_log_service`，为当前任务系统补齐最小执行日志存储/查询边界。
- `M4.3.3`：扩展 `TaskService`，在 scheduler executor 外层记录 success/error 日志，并新增 `GET /tasks/{task_id}/logs` 查询接口。
- `M4.3.3`：补齐模型、日志服务、任务执行与日志路由测试，覆盖 most-recent-first 排序、limit、缺失任务 `404` 与真实 `run_pending()` 执行日志记录。
- `M4.4.1`：用文件系统版 `MemoryService` 替换占位内存 KV，实现 `get_user_memory()` / `update_user_memory()`，并按用户要求使用 `AGENTS.md` 替代 `CLAUDE.md` 作为用户全局记忆文件名。
- `M4.4.1`：新增 `tests/services/test_memory_service.py`，覆盖缺失文件返回空字符串、`AGENTS.md` 路径创建、覆盖写入与多用户隔离。
- `M4.4.2`：扩展 `MemoryService.append_daily_memory()`，将群组日期记忆追加到 `data/memory/{group_folder}/YYYY-MM-DD.md`。
- `M4.4.2`：为 `MemoryService` 增加可注入的 `today_func`，并补齐日期记忆测试，覆盖建档、重复追加、群组隔离与不影响用户全局 `AGENTS.md`。
- `M4.4.3`：扩展 `MemoryService.search_memory()`，对 `data/memory/{group_folder}/**/*.md` 做最小大小写不敏感内容搜索，并返回命中文件路径列表。
- `M4.4.3`：补齐记忆搜索测试，覆盖大小写不敏感、空查询返回空列表、排除其他群组结果，以及不把用户全局 `AGENTS.md` 混入搜索结果。
- `M4.4.4`：用挂载的 `/workspace/memory` 目录替换 runner 内存工具占位，实现 `memory_append_tool()` / `memory_search_tool()`，并通过 `@function_tool` 暴露为默认工具。
- `M4.4.4`：新增 `tests/container/agent_runner/test_memory_tools.py`，覆盖日期追加、大小写不敏感搜索、空查询返回空列表，以及默认工具注册包含 memory tools。
- `M4.5`：完成 `M4.1` ~ `M4.4` 的阶段验收，围绕用户系统、RBAC、任务系统、记忆系统与多用户隔离证据执行 fresh 验证，未发现阻塞 `M5` 的缺口。
- `M4.5`：确认 `M4` 当前边界清晰：用户、权限、任务、记忆能力均可验证，但运行态仍以 in-memory / 文件型最小实现为主，真实产品化持久化与生命周期托管留待后续阶段。
- `M5.1.1`：用正式 `FeishuClient` 替换占位实现，补齐 `tenant_access_token` 获取、回调验签与加密事件解密三项基础能力。
- `M5.1.1`：新增 `tests/infra/im/test_feishu.py`，覆盖 token 成功/失败、签名校验、加密事件解密与缺少 `encrypt_key` 的错误路径。
- 最近阶段提交：
  - `fa96e35` `feat(exec): complete M3.1 docker sdk wrapper`
  - `d08e544` `feat(container): complete M3.2 agent runner scaffold`
  - `ca121b3` `feat(exec): complete M3.3 volume mount safety`
  - `7337f1d` `feat(exec): complete M3.4.1 container startup`
  - `066bdbf` `feat(exec): complete M3.4.2 container stop`
  - `3ca3b83` `feat(exec): complete M3.4.3 container health`
  - `399b99c` `docs(progress): refresh M3.4.3 verification evidence`
  - `9180756` `feat(exec): complete M3.4.4 graceful shutdown`
  - `9ddc7fe` `docs(progress): refresh M3.4.4 verification evidence`
  - `016efc3` `feat(exec): complete M3.5.1 host process runner`
  - `4aec343` `feat(services): complete M3.5.2 execution mode selection`
  - `fb62bed` `feat(exec): complete M3.5.3 host mode restrictions`
  - `cb83fcc` `feat(user): complete M4.1.1 user model extension`
  - `bd50272` `feat(user): complete M4.1.2 admin user management api`
  - `e9ca2e1` `feat(user): complete M4.1.3 invite code system`
  - `f7f20aa` `docs(progress): refresh M4.1.3 verification evidence`
  - `f2516ae` `feat(auth): complete M4.2.1 permission templates`
  - `999f163` `docs(progress): refresh M4.2.1 verification evidence`
  - `435fb6c` `feat(auth): complete M4.2.2 permission dependency`
  - `6203fa7` `feat(groups): complete M4.2.3 group member management`
  - `35d550c` `fix(groups): block owner role transfer via member api`
  - `90443f5` `feat(tasks): complete M4.3.1 scheduler core`
  - `0b0564d` `docs(progress): refresh M4.3.1 verification evidence`

---

## 3. 最新验证证据

- M5.1.1 聚焦验证：`.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py -q` -> `5 passed in 0.11s`
- 全量后端回归：`.venv/bin/pytest -o addopts='' -q` -> `228 passed, 1 warning in 5.76s`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3` 仍以静态/离线契约验证完成，尚未执行真实容器/宿主机混合模式烟测。
- `M3` 的容器生命周期、宿主机运行器、模式选择与 host mode 安全限制已就位；进入 `M4` 前仍应记住：真实请求注入策略与混合模式烟测尚未完成。
- `M4.1` 当前仍沿用 in-memory `AuthService` 作为用户真实来源；`last_login_at` 继续保持默认 `null`，DB-backed 用户服务迁移尚未开始。
- `M4.1.3` 当前提供的是“可选消费”的单次邀请码：管理员可创建 / 查看邀请码，注册时可选携带 `invite_code` 继承邀请角色；注册开关（开放注册 / 必须邀请码 / 关闭注册）仍未实现。
- `M4.2.2` 当前仍只基于静态 `role -> permissions` 模板做鉴权；尚未启用 `user.permissions` 自定义覆盖，也未启动 DB-backed 权限迁移。
- `M4.2.2` 当前将 `/admin/invites` 暂时映射到 `users` 资源的 `read/write` 权限，作为不扩展 RBAC 模型的最小桥接；更细粒度的 `invites` 资源需在后续阶段单独设计。
- `M4.2.3` 当前已建立正式 `GroupMember` 模型，但运行态成员真实来源仍是 in-memory `group_member_service`；后续若进入 DB-backed 群组/成员迁移，需要与用户/群组 source of truth 一并设计。
- `M4.2.3` 当前的群内 `admin` 角色仅作为数据契约保留，不额外赋予成员管理权限；成员增删仍限定为 group owner。
- `M4.2.3` 当前不支持通过成员管理接口进行 owner 角色转移或 owner 降级；若后续需要 owner transfer，需单独设计迁移规则与唯一 owner 约束。
- `M4.3.2` 当前的任务运行态仍是进程内 in-memory：`/tasks` 只管理单例 `task_service` / `TaskScheduler` 中的注册表，尚未接入 DB 轮询恢复、执行日志或真实 `agent_trigger` 执行链。
- `M4.3.2` 当前未把 scheduler `start()/stop()` 挂到 FastAPI 生命周期；现阶段完成的是任务 CRUD 与注册表装载/卸载边界，不是持续执行守护进程。
- `M4.3.2` 当前对外 API 的 `next_run` / `created_at` 已统一按 UTC 返回；服务内部仍为了兼容现有 scheduler 比较逻辑，保留 naive UTC datetime。
- `M4.3.3` 当前的任务执行日志同样仍是进程内 in-memory，只会反映当前进程里 `TaskScheduler.run_pending()` 的真实执行结果；重启后不会恢复历史日志。
- `M4.3.3` 当前日志状态仅覆盖 `success` / `error`；`timeout` 仍保留为后续真实执行链与超时控制接入后的预留状态。
- `M4.4.1` 当前只完成用户全局记忆文件管理，且文件名按本仓库当前决策使用 `AGENTS.md`；尚未实现 daily memory、memory search、API 暴露或 runner / MCP 集成。
- `M4.4.2` 当前已补齐群组日期记忆文件，但仍只停留在服务层文件读写；尚未实现搜索、API 暴露或 runner / MCP 集成。
- `M4.4.3` 当前搜索仍只停留在服务层：按 group folder 扫描 markdown 文件内容并返回路径列表，不提供片段、高亮、排序优化或 API / runner 集成。
- `M4.4.4` 当前 runner memory tools 直接操作挂载的 group-scoped `/workspace/memory`，不经过主服务 API，也不覆盖用户全局 `AGENTS.md`。
- `M4.5` 验收结论：`M4` 已达成当前 TODO 定义的用户 / RBAC / 任务 / 记忆 / 多用户隔离目标，但仍不是完整产品态；进入 `M5` 前需继续保留上述 in-memory / 文件型边界说明。
- `M5.1.1` 当前只完成飞书认证 / 验签 / 解密基础能力；尚未接入事件路由、消息发送、或真实 webhook/WebSocket 入口。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`infra/im/feishu.py`、`tests/infra/im/test_feishu.py`、`infra/im/base.py`
2. 从 `M5.1.2` 开始：
   - 在当前飞书认证 / 验签 / 解密基础之上补最小事件接收处理，不要顺手扩成完整通道产品化
   - 保留 `M4` 当前边界：用户、任务、日志、记忆仍有 in-memory / 文件型最小实现，不要在 `M5` 起步时顺手扩成 DB 迁移或后台守护
   - 飞书接入优先聚焦事件解析与最小消息入口，不要一次性扩到发送富文本卡片、Telegram 或完整多平台抽象细节
   - 继续保留 `M4.2.2` / `M4.2.3` 的边界：不要顺手启用 `user.permissions` 自定义覆盖，也不要启动 DB-backed 用户/群组迁移
   - 继续把 `M3` 未完成的真实请求注入 / 混合模式烟测作为风险备注保留，不要在 `M5` 中意外遗失
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M5.1.1` 已完成，下一步进入 `M5.1.2` 飞书事件接收。
