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
- 当前起点：`M3.4.4`（优雅关闭）。

---

## 2. 最近完成

- `M3.4.3`：在 `infra/exec/container_manager.py` 新增 `is_container_healthy()`，复用 `DockerClient.get_container()` 并以 `container.status == "running"` 作为最小健康判断。
- `M3.4.3`：扩展 `tests/infra/exec/test_container_manager.py`，覆盖 running / exited 分支与容器查询异常透传。
- `M3.4.x`：`ContainerManager` 继续保持薄编排层；当前健康判断仍是离线契约级，真实 daemon 下是否需要 `reload()` 留待 `M3.4.4+` 结合长期运行策略再收敛。
- 最近阶段提交：
  - `fa96e35` `feat(exec): complete M3.1 docker sdk wrapper`
  - `d08e544` `feat(container): complete M3.2 agent runner scaffold`
  - `ca121b3` `feat(exec): complete M3.3 volume mount safety`
  - `7337f1d` `feat(exec): complete M3.4.1 container startup`
  - `066bdbf` `feat(exec): complete M3.4.2 container stop`

---

## 3. 最新验证证据

- M3.4.3 聚焦：`.venv/bin/pytest tests/infra/exec/test_container_manager.py tests/infra/exec/test_docker.py tests/infra/exec/test_security.py tests/container/agent_runner` -> `35 passed in 3.73s`
- 全量后端回归：`.venv/bin/pytest` -> `100 passed, 1 warning in 9.08s`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3.4.3` 仍以静态/离线契约验证完成，尚未执行真实容器生命周期烟测。
- `M3.4.1~M3.4.3` 当前只完成启动/停止/最小健康判断编排；`agent-runner` 仍以 stdin JSON 作为执行入口，后续需要在 `M3.4.4+` / IPC 链路中补齐真实请求注入、长期运行策略与更稳健的健康状态来源。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`infra/exec/container_manager.py`、`infra/exec/docker.py`、`container/agent-runner/src/runner.py`、`container/agent-runner/src/types.py`
2. 从 `M3.4.4` 开始：
   - 在 `ContainerManager` 上补优雅关闭，明确 stop / wait / force remove 的顺序和超时策略
   - 继续扩展 `test_container_manager.py` 的 fake client/container 夹具，为 `graceful_shutdown()` 增加 wait / logs / fallback 分支断言
   - 继续明确 detached 容器的真实请求注入方案（stdin attach、IPC 文件监听或 runner 读取文件/环境变量）
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M3.4.3` 容器健康检查已完成，下一步从 `M3.4.4` 优雅关闭继续。
