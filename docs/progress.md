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
- 当前起点：`M3.4.2`（容器停止）。

---

## 2. 最近完成

- `M3.4.1`：新增 `infra/exec/container_manager.py`，实现 `ContainerManager.start_agent_container()`，统一容器镜像、命令、工作目录、挂载、环境变量与 `detach=True/remove=False` 启动策略。
- `M3.4.1`：容器名固定为 `portex-agent-{group}-{session}` 风格，并对 session 片段做 Docker name 兼容清洗，为后续 stop / health / graceful shutdown 保留稳定标识。
- `M3.4.1`：新增 `tests/infra/exec/test_container_manager.py`，覆盖容器启动默认参数、挂载/环境拼装、group mismatch 防御和 Docker 异常透传。
- 最近阶段提交：
  - `fa96e35` `feat(exec): complete M3.1 docker sdk wrapper`
  - `d08e544` `feat(container): complete M3.2 agent runner scaffold`
  - `ca121b3` `feat(exec): complete M3.3 volume mount safety`

---

## 3. 最新验证证据

- M3.4.1 聚焦：`.venv/bin/pytest tests/infra/exec/test_container_manager.py tests/infra/exec/test_docker.py tests/infra/exec/test_security.py tests/container/agent_runner` -> `29 passed in 4.62s`
- 全量后端回归：`.venv/bin/pytest` -> `94 passed, 1 warning in 7.92s`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3.4.1` 仍以静态/离线契约验证完成，尚未执行真实容器启动烟测。
- `M3.4.1` 当前只完成“容器启动编排层”；`agent-runner` 仍以 stdin JSON 作为执行入口，后续需要在 `M3.4.2+` / IPC 链路中补齐真实请求注入与长期运行策略。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`infra/exec/container_manager.py`、`infra/exec/docker.py`、`container/agent-runner/src/runner.py`、`container/agent-runner/src/types.py`
2. 从 `M3.4.2` 开始：
   - 在 `ContainerManager` 上补 `stop_container()`，优先复用 `DockerClient.stop_container()` / `remove_container()`
   - 补 `health` / `graceful shutdown` 所需的容器检索与状态判断接口，尽量沿用 `test_container_manager.py` 的 fake client 夹具
   - 决定 detached 容器的真实请求注入方案（stdin attach、IPC 文件监听或 runner 读取文件/环境变量）
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M3.4.1` 容器启动编排层已完成并通过回归，当前从 `M3.4.2` 容器停止继续。
