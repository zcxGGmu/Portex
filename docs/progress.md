# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-07 (Asia/Shanghai)
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
- 当前起点：`M4.2.1`（定义权限模板）。

---

## 2. 最近完成

- `M4.1.3`：新增 `domain/models/invite_code.py` 并接入 `domain/models/__init__.py`，把邀请码纳入统一 SQLAlchemy metadata，支持单次消费的 `used_by` / `used_at` 状态。
- `M4.1.3`：扩展 `services/auth.py` 的 in-memory `AuthService`，新增邀请码创建、查询、消费能力，并在 `register_user()` 中支持可选 `invite_code` 赋予邀请角色、阻止过期/已使用邀请码，以及保证用户名冲突不会消耗邀请码。
- `M4.1.3`：在 `app/routes/users.py` 与 `app/routes/auth.py` 补齐 `GET /admin/invites`、`POST /admin/invites` 和注册消费逻辑，并扩展模型/API 测试覆盖邀请码管理与消费路径。
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

---

## 3. 最新验证证据

- M4.1.3 聚焦验证：`.venv/bin/pytest -o addopts='' tests/domain/models/test_models.py tests/services/test_auth_service.py tests/app/routes/test_api_routes.py -q` -> `37 passed, 1 warning in 4.48s`
- 全量后端回归：`.venv/bin/pytest -o addopts='' -q` -> `143 passed, 1 warning in 4.41s`
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
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`domain/models/user.py`、`domain/models/invite_code.py`、`domain/schemas.py`、`services/auth.py`、`app/routes/users.py`
2. 从 `M4.2.1` 开始：
   - 在新建 `domain/permissions.py` 中定义角色权限模板，并与当前 `role` / 邀请码赋权结果保持命名一致
   - 明确 `M4.1` 当前 in-memory 用户 / 邀请码体系如何为后续 `require_permission` 与 `group_members` 提供最小兼容接口
   - 继续把 `M3` 未完成的真实请求注入 / 混合模式烟测作为风险备注保留，不要在 `M4` 中意外遗失
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M4.1.3` 已完成，下一步进入 `M4.2.1` 权限模板。
