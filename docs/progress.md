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
- 当前起点：`M3.6`（阶段验收）。

---

## 2. 最近完成

- `M3.5.3`：在 `infra/exec/process.py` 新增 `HostModeRestrictions`、`HOST_MODE_RESTRICTIONS` 与 `is_command_forbidden()`，为 host mode 定义允许目录、危险命令前缀与最大执行时长。
- `M3.5.3`：`ProcessExecutor.run_agent()` 现会在启动前校验允许目录与危险命令，并通过 `asyncio.wait_for(..., timeout=...)` 强制执行时长上限；超时会 `kill()` 子进程并抛出 `ProcessExecutionError`。
- `M3.5.3`：扩展 `tests/infra/exec/test_process.py`，覆盖允许目录拒绝、危险命令匹配、超时 kill，以及默认 host mode 限制常量。
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

---

## 3. 最新验证证据

- M3.5.3 聚焦：`.venv/bin/pytest tests/services/test_execution_mode.py tests/infra/exec/test_process.py tests/infra/exec/test_container_manager.py tests/infra/exec/test_docker.py tests/infra/exec/test_security.py tests/container/agent_runner` -> `52 passed in 3.62s`
- 全量后端回归：`.venv/bin/pytest` -> `117 passed, 1 warning in 7.29s`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3.5.3` 仍以静态/离线契约验证完成，尚未执行真实容器/宿主机混合模式烟测。
- `M3.4` 生命周期与 `M3.5` 三项宿主机模式基础能力已就位；下一步进入 `M3.6` 阶段验收，并继续明确真实请求注入策略。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`infra/exec/container_manager.py`、`infra/exec/docker.py`、`container/agent-runner/src/runner.py`、`container/agent-runner/src/types.py`
2. 从 `M3.6` 开始：
   - 按阶段验收清单回看 `M3.1` ~ `M3.5` 的交付、测试和文档，确认边界一致
   - 重点确认 host/container 两条运行路径的共同协议边界，以及仍缺的真实请求注入策略
   - 若准备进入 `M4`，先把 `M3` 收尾结论与风险点写进 `docs/progress.md`
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M3.5.3` 宿主机模式安全限制已完成，下一步从 `M3.6` 阶段验收继续。
