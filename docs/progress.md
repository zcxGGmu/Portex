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
- 当前起点：`M4.2.2`（实现权限检查装饰器）。

---

## 2. 最近完成

- `M4.2.1`：新增 `domain/permissions.py`，定义 `owner` / `admin` / `member` 三套静态权限模板，覆盖 `users`、`groups`、`messages`、`tasks`、`settings` 五类资源。
- `M4.2.1`：补充 `get_permissions_for_role()` 与 `has_permission()` 两个纯函数 helper，为下一步 `require_permission` 依赖提供直接复用的最小契约。
- `M4.2.1`：新增 `tests/domain/test_permissions.py`，覆盖模板结构、角色权限正反例、未知 role/resource/action 的默认拒绝，以及 helper 的防篡改返回行为。
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

---

## 3. 最新验证证据

- M4.2.1 聚焦验证：`.venv/bin/pytest -o addopts='' tests/domain/test_permissions.py -q` -> `6 passed in 0.03s`
- 全量后端回归：`.venv/bin/pytest -o addopts='' -q` -> `149 passed, 1 warning in 4.87s`
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
- `M4.2.1` 当前只完成“静态角色模板 + 纯函数 helper”，尚未启用 `user.permissions` 自定义覆盖，也未把现有路由迁移到 `require_permission`。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`domain/permissions.py`、`app/middleware/auth.py`、`services/auth.py`、`app/routes/users.py`
2. 从 `M4.2.2` 开始：
   - 在 `app/middleware/auth.py` 新增 `require_permission(resource, action)`，先基于当前用户 `role` 与 `domain/permissions.py` 的静态模板进行判断
   - 保持边界最小：暂不启用 `user.permissions` 自定义覆盖，也不要顺手启动 DB-backed 权限迁移
   - 继续把 `M3` 未完成的真实请求注入 / 混合模式烟测作为风险备注保留，不要在 `M4` 中意外遗失
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M4.2.1` 已完成，下一步进入 `M4.2.2` 权限检查依赖。
