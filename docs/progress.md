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
- `M2.5.3` 已完成（前端取消按钮 + WS 取消入口）。
- 下一起点：`M2.6.1`（M2 阶段验收）。

---

## 2. 本轮完成内容（M2.5.3）

- `app/routes/websocket.py`
  - WebSocket 路由从 echo 改为真实执行入口
  - 普通文本仍为发送消息；取消走 JSON 控制帧 `{"type":"cancel","run_id":"..."}`
  - 每个连接维护独立 runtime、`active_run_id`、`active_task`
  - `run.started` 只直送发起页，避免同房间其他页被错误锁定为 running
  - 手动取消后等待旧任务真正收尾，再回发 `run.failed(status=cancelled)` 给发起页
  - 断开连接时会清理 active run 和后台 task
- `web/src/stores/chat.ts`
  - 新增 `isRunning`、`activeRunId`、`clearRunState`
  - 仅对当前 `activeRunId` 的终态事件收口运行态，避免被同房间其他页的终态事件污染
- `web/src/components/chat/ChatPanel.tsx`
  - 发送时阻止并发重复提交
  - 新增取消按钮并通过同一 WebSocket 发送取消控制帧
  - 新增 `run.timeout` / `cancelled` 的 assistant 可见提示
  - 运行中禁用 `Send` 与 `Clear`
- `tests/app/routes/test_websocket_routes.py`
  - 用真实 send/cancel 路由测试替换旧 echo 测试
- 新增文档：
  - `docs/plans/2026-03-06-m2-5-3-cancel-ui-design.md`
  - `docs/plans/2026-03-06-m2-5-3-cancel-ui-flow.md`

---

## 3. 最新验证证据

- 聚焦测试：`.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q` -> `4 passed`
- 单元验收：`.venv/bin/pytest tests/unit/ -v` -> `1 passed`
- 全量回归：`.venv/bin/pytest -q` -> `65 passed`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass

备注：
- `passlib` 仍有 `DeprecationWarning: crypt`（Python 3.13 将移除）。
- `services/message_service.py` 仍有 `datetime.utcnow()` 的弃用告警，后续可单独处理。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
2. 从 `M2.6.1` 开始，做 M2 阶段验收：
   - 启动后端与前端
   - 走登录、发消息、流式展示、取消、超时路径
   - 记录端到端结果与遗留问题
3. 如要继续完善取消体验，优先考虑补一个正式 `run.cancelled` 事件，替代当前临时复用的 `run.failed(status=cancelled)`。

---

## 5. 一句话版

> 项目已完成 `M2.5.3` 前端取消按钮与 WebSocket 取消入口，下一步进入 `M2.6.1` M2 阶段验收。
