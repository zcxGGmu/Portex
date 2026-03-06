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
- 当前起点：`M3.3.1`（卷挂载构建器）。

---

## 2. 最近完成

- `M3.2.1`：升级 `container/agent-runner/Dockerfile`，补齐系统依赖、非 root 用户和 `src.runner` 入口。
- `M3.2.2`：完成 `container/agent-runner/src/runner.py`，支持 stdin JSON 解析、`Runner.run_sync()` 调用和结构化 JSON 输出。
- `M3.2.3`：新增 `container/agent-runner/src/types.py` 与默认工具注册，固化容器输入输出协议。
- 新增 `tests/container/agent_runner/`，覆盖 Dockerfile 静态断言、协议模型默认值、runner 成功/失败路径。

---

## 3. 最新验证证据

- Agent Runner 聚焦：`.venv/bin/pytest tests/container/agent_runner` -> `9 passed`
- 全量后端回归：`.venv/bin/pytest` -> `82 passed, 1 warning`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- Docker CLI 环境：`docker version --format '{{.Client.Version}}|{{.Server.Version}}'` -> `docker: command not found`
- Docker SDK 直连：`.venv/bin/python -c 'import docker; docker.from_env().ping()'` -> `DockerException: ... FileNotFoundError(2, 'No such file or directory')`

备注：
- 当前环境没有可用的 Docker CLI / daemon，`M3.2` 以静态 Dockerfile 断言 + 离线 runner 单元测试完成契约验证，尚未执行真实 `docker build` / 容器烟测。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
2. 从 `M3.3.1` 开始：
   - 基于 `group_folder` / `user_id` 设计卷挂载构建器
   - 明确 session / memory / skills / IPC 的宿主机到容器映射
   - 为额外挂载和只读选项预留可扩展结构
3. 如果要做真实容器烟测，再确认本机 Docker daemon 可用，且不要把任何凭据写入仓库。

---

## 5. 一句话版

> `M3.2` Agent Runner 容器化已完成并通过回归，当前从 `M3.3.1` 卷挂载与安全继续。
