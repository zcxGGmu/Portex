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
- 当前起点：`M3.2.1`（Agent Runner Dockerfile）。

---

## 2. 最近完成

- `M3.1.1`：确认 `pyproject.toml` 已纳入 `docker>=7.0.0` 依赖。
- `M3.1.2`：完成 `infra/exec/docker.py` Docker SDK 客户端封装，保留 container/host 清晰边界。
- `M3.1.3`：补齐 `run_container`、`stop_container`、`wait_container`、`get_logs`、`remove_container`，并统一 `DockerExecutionError` 错误出口。
- 新增 `tests/infra/exec/test_docker.py`，覆盖 lazy `docker.from_env()`、参数透传、生命周期委托与错误包装。

---

## 3. 最新验证证据

- 执行层聚焦：`.venv/bin/pytest tests/infra/exec/test_docker.py -q` -> pass（8 个用例）。
- 聚焦回归：`.venv/bin/pytest tests/infra/exec/test_docker.py tests/services/test_agent_trigger.py tests/app/routes/test_websocket_routes.py -q` -> `20 passed`。
- 全量后端回归：`.venv/bin/pytest -q` -> pass（含新增 Docker 执行层测试）。
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3.1` 以 fake Docker client 离线测试完成契约验证。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
2. 从 `M3.2.1` 开始：
   - 创建 `container/agent-runner/Dockerfile`
   - 明确 Runner 主入口与容器输入输出协议
   - 复用 `infra/exec/docker.py` 作为后续容器生命周期调用基础
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M3.1` Docker SDK 集成已完成并通过回归，当前从 `M3.2.1` Agent Runner 容器化继续。
