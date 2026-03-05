# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-05 (Asia/Shanghai)
仓库路径: `/home/zcxggmu/workspace/hello-projs/posp/Portex`
当前分支: `main`

---

## 1. 当前阶段

- `M0` 已完成。
- `M1` 已完成（`M1.1` ~ `M1.6`）。
- `M2.1` 已完成（WebSocket 基础设施）。
- `M2.2` 已完成（`M2.2.1` ~ `M2.2.3` Runtime 适配器）。
- 下一起点：`M2.3.1`（消息存储链路）。

---

## 2. 本轮完成内容（M2.2）

- 实现运行时抽象：`infra/runtime/adapter.py`
  - `RunRequest` / `RunEvent` / `RunResult`
  - `AgentRuntime` 协议（`run_streamed` / `cancel`）
- 实现 OpenAI Agents Runtime：`infra/runtime/openai.py`
  - `OpenAIAgentsRuntime`
  - `Runner.run_streamed()` 事件迭代
- 实现 SDK 事件映射：`infra/runtime/mapper.py`
  - `agent_updated_stream_event` -> `run.started`
  - `raw_response_event` -> `run.token.delta` / `run.completed` / `run.failed`
  - `run_item_stream_event` -> `run.tool.started` / `run.tool.completed`
- 运行时包导出更新：`infra/runtime/__init__.py`
- 新增测试：`tests/infra/runtime/test_adapter.py`、`tests/infra/runtime/test_openai.py`、`tests/infra/runtime/test_runtime_event_mapper.py`

---

## 3. 最新验证证据

- 特性测试：`.venv/bin/pytest tests/infra/runtime/ -q` -> `11 passed`
- 单元验收：`.venv/bin/pytest tests/unit/ -v` -> `1 passed`
- 全量回归：`.venv/bin/pytest -q` -> `53 passed`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass

备注：`passlib` 仍有 `DeprecationWarning: crypt`（Python 3.13 将移除）。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
2. 从 `M2.3.1` 开始：
   - `services/message_service.py`（消息持久化）
   - 后续衔接 `services/agent_trigger.py`（触发 Runtime 流式执行）
3. 子任务完成后固定流程：
   - 跑特性测试 + 全量回归；
   - 更新 `docs/TODO.md` 与 `docs/progress.md`；
   - 单任务单提交。

---

## 5. 一句话版

> 项目已完成 M2.2 Runtime 适配器，下一步进入 M2.3 消息处理链路。
