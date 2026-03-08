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
- 当前起点：`M4.3.1`（实现任务调度器）。

---

## 2. 最近完成

- `M4.2.3`：新增 `domain/models/group_member.py`，定义 `group_members` SQLAlchemy 契约（`group_jid` / `user_id` 复合主键，角色 `owner/admin/member`，`joined_at` 默认时间戳）。
- `M4.2.3`：新增 `services/group_member_service.py` 作为当前最小 in-memory 群成员服务；支持列举、添加、删除成员，以及按群查询成员角色。
- `M4.2.3`：扩展 `app/routes/groups.py` 与 `domain/schemas.py`，提供 `GET/POST/DELETE /groups/{group_id}/members` 最小 API，并补充模型 / 服务 / 路由测试覆盖成员可见性、owner-only 管理规则，以及 owner 角色转移/降级保护。
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

---

## 3. 最新验证证据

- M4.2.3 聚焦验证：`.venv/bin/pytest -o addopts='' tests/domain/models/test_models.py tests/services/test_group_member_service.py tests/app/routes/test_api_routes.py -q` -> `43 passed, 1 warning in 5.35s`
- 全量后端回归：`.venv/bin/pytest -o addopts='' -q` -> `173 passed, 1 warning in 7.61s`
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
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`domain/permissions.py`、`app/middleware/auth.py`、`app/routes/users.py`、`services/auth.py`
2. 从 `M4.3.1` 开始：
   - 优先围绕 `services/scheduler.py` 建立最小调度器循环与测试，再决定 API/执行触发如何串接
   - 建议先复用现有 `domain/models/task.py` 契约，补 scheduler 的内存态 / DB 交界设计，避免直接跨到完整任务 CRUD
   - 继续保留 `M4.2.2` / `M4.2.3` 的边界：不要顺手启用 `user.permissions` 自定义覆盖，也不要启动 DB-backed 用户/群组迁移
   - 继续把 `M3` 未完成的真实请求注入 / 混合模式烟测作为风险备注保留，不要在 `M4` 中意外遗失
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M4.2.3` 已完成，下一步进入 `M4.3.1` 任务调度器。
