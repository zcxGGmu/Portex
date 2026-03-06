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
- 当前起点：`M3.4.1`（容器启动）。

---

## 2. 最近完成

- `M3.3.1`：在 `infra/exec/docker.py` 中新增 `build_volume()` / `build_readonly_volume()` / `build_volumes()`，固定 sessions、memory、ipc、group、skills 的 host→container 映射。
- `M3.3.2`：新增 `infra/exec/security.py`，实现 real-path 基础的 `validate_path()`，并在挂载构建时阻断路径逃逸。
- `M3.3.3`：为 skills 提供默认只读挂载，并允许通过 `readonly_mounts` 扩展到 memory / ipc / group / sessions。
- 新增 `tests/infra/exec/test_security.py`，并扩展 `tests/infra/exec/test_docker.py` 覆盖只读绑定、挂载构建与 traversal 拒绝路径。
- 最近阶段提交：
  - `fa96e35` `feat(exec): complete M3.1 docker sdk wrapper`
  - `d08e544` `feat(container): complete M3.2 agent runner scaffold`
  - `ca121b3` `feat(exec): complete M3.3 volume mount safety`

---

## 3. 最新验证证据

- M3.3 聚焦：`.venv/bin/pytest tests/infra/exec/test_docker.py tests/infra/exec/test_security.py` -> `17 passed`
- 全量后端回归：`.venv/bin/pytest` -> `91 passed, 1 warning`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3.2` 与 `M3.3` 均以静态/离线契约验证完成，尚未执行真实 `docker build` / 容器烟测。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`infra/exec/docker.py`、`infra/exec/security.py`、`container/agent-runner/src/runner.py`、`container/agent-runner/src/types.py`
2. 从 `M3.4.1` 开始：
   - 复用 `build_volumes()` 与 `DockerClient.run_container()` 串起容器启动
   - 明确容器名、工作目录、环境变量和 detach/remove 策略
   - 为停止、健康检查和优雅关闭保留可测接口
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M3.3` 卷挂载与安全已完成并通过回归，当前从 `M3.4.1` 容器生命周期继续。
