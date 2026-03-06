# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-06 (Asia/Shanghai)
仓库路径: `/home/zq/work-space/repo/ai-projs/posp/Portex`
当前分支: `main`

---

## 1. 当前阶段

- `M0` 已完成。
- `M1` 已完成（`M1.1` ~ `M1.6`）。
- `M2.1` 已完成（WebSocket 基础设施）。
- `M2.2` 已完成（Runtime 适配器）。
- `M2.3` 已完成（消息存储 + 触发 + 展示基础）。
- `M2.4` 已完成（`M2.4.1` ~ `M2.4.4` 流式输出前端展示）。
- `M2.5.1` 已完成（取消功能基线）。
- `M2.5.2` 已完成（超时控制）。
- 下一起点：`M2.5.3`（前端取消按钮）。

---

## 2. 本轮完成内容（M2.5.2）

- `services/agent_trigger.py`
  - 新增 `timeout_ms: int = 300_000`，沿用 HappyClaw 毫秒语义
  - 超时控制改为独立消费任务 + `asyncio.wait(...)`，避免把内部 `TimeoutError` 误判为整体超时
  - 超时后先调用 `runtime.cancel(request.request_id)`，再取消消费任务并广播 `run.timeout`
  - 外层调用被取消时，会兜底清理后台消费任务，避免 runtime 流泄漏
- 契约对齐：
  - `portex/contracts/events.py` 新增 `RUN_TIMEOUT`
  - `web/src/types/events.ts` 新增 `run.timeout` 联合类型
- 新增/增强测试：
  - `tests/services/test_agent_trigger.py`
    - 超时会返回原 `run_id`
    - 超时会广播 `run.timeout`
    - 超时会触发真实 OpenAI runtime active stream 取消
    - 内部 `TimeoutError` 不会被误判为整体超时
    - 外层任务取消时后台消费任务会被回收
  - `tests/portex/contracts/test_events.py`
    - 新增 `RUN_TIMEOUT` 枚举断言
- 新增文档：
  - `docs/plans/2026-03-06-m2-5-2-timeout-design.md`
  - `docs/plans/2026-03-06-m2-5-2-timeout-flow.md`

---

## 3. 最新验证证据

- 聚焦测试：`.venv/bin/pytest tests/services/test_agent_trigger.py tests/portex/contracts/test_events.py -q` -> `10 passed`
- 单元验收：`.venv/bin/pytest tests/unit/ -v` -> `1 passed`
- 全量回归：`.venv/bin/pytest -q` -> `64 passed`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass

备注：
- `passlib` 仍有 `DeprecationWarning: crypt`（Python 3.13 将移除）。
- `services/message_service.py` 仍有 `datetime.utcnow()` 的弃用告警，后续可单独处理。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
2. 从 `M2.5.3` 开始：
   - 在 `web/src/stores/chat.ts` 中加入运行态和当前 `run_id`
   - 在 `web/src/components/chat/ChatPanel.tsx` 中接 `run.started` / `run.completed` / `run.failed` / `run.timeout`
   - 增加取消按钮，并连接到后端取消入口
3. 注意：当前生产 WebSocket 路由仍是 echo，`M2.5.3` 需要一并补齐服务端入口，否则前端取消按钮只能停留在 UI 状态层。

---

## 5. 一句话版

> 项目已完成 `M2.5.2` 服务层超时控制与 `run.timeout` 契约，下一步进入 `M2.5.3` 前端取消按钮。
