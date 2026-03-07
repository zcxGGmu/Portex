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
- 当前起点：`M4.1.2`（实现用户管理 API）。

---

## 2. 最近完成

- `M4.1.1`：在 `domain/models/user.py` 增加 `avatar_emoji`、`avatar_color`、`ai_name`、`ai_avatar_emoji`、`must_change_password`、`last_login_at`、`disable_reason`、`notes`，补齐用户资料与账户状态字段。
- `M4.1.1`：在 `services/auth.py` 扩展 `AuthUser` 公共形状和注册默认值，让当前内存版注册 / 登录 / `/users/me` 链路与新用户字段保持一致。
- `M4.1.1`：扩展 `domain/schemas.py` 与三组测试，覆盖 SQLAlchemy 列暴露、AuthService 默认字段，以及 `/users/me` 的返回契约。
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
  - `b367c70` `feat(user): complete M4.1.1 user model extension`

---

## 3. 最新验证证据

- M4.1.1 聚焦验证：`.venv/bin/pytest -o addopts='' tests/domain/models/test_models.py tests/services/test_auth_service.py tests/app/routes/test_api_routes.py -q` -> `15 passed, 1 warning in 3.77s`
- 全量后端回归：`.venv/bin/pytest -o addopts='' -q` -> `119 passed, 1 warning in 5.55s`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3` 仍以静态/离线契约验证完成，尚未执行真实容器/宿主机混合模式烟测。
- `M3` 的容器生命周期、宿主机运行器、模式选择与 host mode 安全限制已就位；进入 `M4` 前仍应记住：真实请求注入策略与混合模式烟测尚未完成。
- `M4.1.1` 当前只扩展了模型 / schema / 现有 auth 公共用户形状，`last_login_at` 暂保持默认 `null`，尚未引入 DB 持久化用户服务，也未开始管理员用户管理 API。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`domain/models/user.py`、`domain/schemas.py`、`services/auth.py`、`app/routes/users.py`
2. 从 `M4.1.2` 开始：
   - 新增管理员用户列表 / 更新 API，并明确沿用当前 in-memory auth 还是开始切到 DB-backed user service
   - 在 `app/routes/users.py`、`domain/schemas.py`、`services/auth.py` 之间补齐 admin 视角下的用户读写契约
   - 继续把 `M3` 未完成的真实请求注入 / 混合模式烟测作为风险备注保留，不要在 `M4` 中意外遗失
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M4.1.1` 已完成，下一步进入 `M4.1.2` 用户管理 API。
