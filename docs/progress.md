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
- 当前起点：`M3.5.1`（宿主机进程运行器）。

---

## 2. 最近完成

- `M3.4.4`：在 `infra/exec/container_manager.py` 新增 `graceful_shutdown()`，默认执行 `stop(timeout=30)` → `wait()` → `remove(force=False)`，并在 graceful 路径失败时回退到 `remove(force=True)`。
- `M3.4.4`：扩展 `tests/infra/exec/test_container_manager.py`，覆盖正常 stop/wait/remove 顺序、stop 失败 fallback、wait 失败 fallback、force remove 失败异常透传。
- `M3.4`：容器生命周期四个子任务已完成，`ContainerManager` 当前已具备启动、停止、健康检查和最小优雅关闭能力。
- 最近阶段提交：
  - `fa96e35` `feat(exec): complete M3.1 docker sdk wrapper`
  - `d08e544` `feat(container): complete M3.2 agent runner scaffold`
  - `ca121b3` `feat(exec): complete M3.3 volume mount safety`
  - `7337f1d` `feat(exec): complete M3.4.1 container startup`
  - `066bdbf` `feat(exec): complete M3.4.2 container stop`
  - `3ca3b83` `feat(exec): complete M3.4.3 container health`
  - `399b99c` `docs(progress): refresh M3.4.3 verification evidence`

---

## 3. 最新验证证据

- M3.4.4 聚焦：`.venv/bin/pytest tests/infra/exec/test_container_manager.py tests/infra/exec/test_docker.py tests/infra/exec/test_security.py tests/container/agent_runner` -> `39 passed in 2.10s`
- 全量后端回归：`.venv/bin/pytest` -> `104 passed, 1 warning in 2.52s`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3.4.4` 仍以静态/离线契约验证完成，尚未执行真实容器生命周期烟测。
- `M3.4` 当前已完成最小生命周期编排；`agent-runner` 仍以 stdin JSON 作为执行入口，后续需要在 `M3.5+` / IPC 链路中补齐真实请求注入、宿主机模式与更稳健的长期运行策略。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`infra/exec/container_manager.py`、`infra/exec/docker.py`、`container/agent-runner/src/runner.py`、`container/agent-runner/src/types.py`
2. 从 `M3.5.1` 开始：
   - 在 `infra/exec/process.py` 上实现宿主机进程运行器，明确命令启动、stdout/stderr 收集和返回码处理
   - 为 host mode 增加最小单测，优先覆盖成功执行、异常退出和参数透传
   - 继续明确 detached 容器 / host mode 的真实请求注入方案（stdin attach、IPC 文件监听或 runner 读取文件/环境变量）
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M3.4` 容器生命周期已完成，下一步从 `M3.5.1` 宿主机进程运行器继续。
