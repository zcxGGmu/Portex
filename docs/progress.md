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
- 当前起点：`M3.5.3`（宿主机模式安全限制）。

---

## 2. 最近完成

- `M3.5.2`：新增 `services/execution_mode.py`，实现 `get_execution_mode()`，仅在 `admin + host_mode=true` 时选择 host，其余情况统一回落到 container。
- `M3.5.2`：扩展 `services/__init__.py` 导出 `execution_mode`，让后续编排层可以直接接入模式判定。
- `M3.5.2`：新增 `tests/services/test_execution_mode.py`，覆盖 admin/member 与 `host_mode` 开关组合的最小判定矩阵。
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

---

## 3. 最新验证证据

- M3.5.2 聚焦：`.venv/bin/pytest tests/services/test_execution_mode.py tests/infra/exec/test_process.py tests/infra/exec/test_container_manager.py tests/infra/exec/test_docker.py tests/infra/exec/test_security.py tests/container/agent_runner` -> `47 passed in 3.67s`
- 全量后端回归：`.venv/bin/pytest` -> `112 passed, 1 warning in 7.49s`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3.5.2` 仍以静态/离线契约验证完成，尚未执行真实容器/宿主机混合模式烟测。
- `M3.4` 生命周期与 `M3.5.1~M3.5.2` 基础运行切换已就位；后续需要在 `M3.5.3` 补齐 host mode 安全限制以及真实请求注入策略。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`infra/exec/container_manager.py`、`infra/exec/docker.py`、`container/agent-runner/src/runner.py`、`container/agent-runner/src/types.py`
2. 从 `M3.5.3` 开始：
   - 为 host mode 增加最小安全限制配置，至少覆盖允许目录、危险命令黑名单、执行时长上限
   - 明确这些限制如何与 `ProcessExecutor` 结合，是在启动前校验还是在命令层统一拦截
   - 继续明确 detached 容器 / host mode 的真实请求注入方案（stdin attach、IPC 文件监听或 runner 读取文件/环境变量）
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M3.5.2` 模式选择逻辑已完成，下一步从 `M3.5.3` 宿主机模式安全限制继续。
