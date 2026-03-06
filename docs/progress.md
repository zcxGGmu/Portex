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
- 当前起点：`M3.5.2`（模式选择逻辑）。

---

## 2. 最近完成

- `M3.5.1`：重写 `infra/exec/process.py`，新增 `ProcessExecutor.run_agent()` / `ProcessRunResult`，通过 host subprocess 启动 `python -m src.runner`，向 stdin 写入 JSON，并收集 stdout/stderr/returncode。
- `M3.5.1`：宿主机运行器会自动创建 `data/groups/{group_folder}` 工作目录，并通过 `PYTHONPATH` 注入 `container/agent-runner`，让 host mode 可以复用现有 runner 包。
- `M3.5.1`：新增 `tests/infra/exec/test_process.py`，覆盖命令参数、stdin 序列化、PYTHONPATH 合并、非零退出码保留与创建失败透传。
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

---

## 3. 最新验证证据

- M3.5.1 聚焦：`.venv/bin/pytest tests/infra/exec/test_process.py tests/infra/exec/test_container_manager.py tests/infra/exec/test_docker.py tests/infra/exec/test_security.py tests/container/agent_runner` -> `43 passed in 4.84s`
- 全量后端回归：`.venv/bin/pytest` -> `108 passed, 1 warning in 6.74s`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3.5.1` 的 host mode 仍以 fake subprocess / 离线契约验证完成，尚未执行真实宿主机 runner 烟测。
- `M3.4` 生命周期与 `M3.5.1` 宿主机运行器已就位；后续需要在 `M3.5.2+` 补齐模式选择、host mode 安全限制以及真实请求注入策略。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
   - 建议顺手再看：`infra/exec/container_manager.py`、`infra/exec/docker.py`、`container/agent-runner/src/runner.py`、`container/agent-runner/src/types.py`
2. 从 `M3.5.2` 开始：
   - 新增执行模式选择逻辑，明确 `admin + host_mode` 的判定边界及默认回落到 container 的规则
   - 让 mode selection 与 `ProcessExecutor` / `ContainerManager` 的现有接口对齐，避免后面再改运行器签名
   - 继续明确 detached 容器 / host mode 的真实请求注入方案（stdin attach、IPC 文件监听或 runner 读取文件/环境变量）
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M3.5.1` 宿主机进程运行器已完成，下一步从 `M3.5.2` 模式选择逻辑继续。
