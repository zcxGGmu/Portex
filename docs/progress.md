# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-05 (Asia/Shanghai)
仓库路径: `/home/zcxggmu/workspace/hello-projs/posp/Portex`
当前分支: `main`

---

## 1. 当前阶段

- `M0` 已完成。
- `M1` 已完成（`M1.1` ~ `M1.6`）。
- `M2.1` 已完成（WebSocket 基础设施）。
- `M2.2` 已完成（Runtime 适配器）。
- `M2.3` 已完成（`M2.3.1` ~ `M2.3.3` 消息处理链路基础）。
- 下一起点：`M2.4.1`（前端流式事件类型定义）。

---

## 2. 本轮完成内容（M2.3）

- 消息存储：`services/message_service.py`
  - `store_message(db, chat_jid, sender, content, is_from_me=False)`
- 消息触发执行：`services/agent_trigger.py`
  - 构建 `RunRequest`
  - 调用 `runtime.run_streamed()`
  - 将 `RunEvent` JSON 推送到 websocket 房间
- 前端消息展示状态：`web/src/stores/chat.ts`
  - 新增 `addMessage`
  - `sendDraft` 改为只追加用户消息（移除占位 Echo）
  - 初始消息改为空列表
- 服务导出更新：`services/__init__.py`
- 新增测试：
  - `tests/services/test_message_service.py`
  - `tests/services/test_agent_trigger.py`

---

## 3. 最新验证证据

- 特性测试：`.venv/bin/pytest tests/services/test_message_service.py tests/services/test_agent_trigger.py -q` -> `4 passed`
- 单元验收：`.venv/bin/pytest tests/unit/ -v` -> `1 passed`
- 全量回归：`.venv/bin/pytest -q` -> `57 passed`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass

备注：`passlib` 仍有 `DeprecationWarning: crypt`（Python 3.13 将移除）。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
2. 从 `M2.4.1` 开始：
   - 新增 `web/src/types/events.ts`
   - 将 runtime 事件类型接入前端渲染链路
3. 子任务完成后固定流程：
   - 跑特性测试 + 全量回归；
   - 更新 `docs/TODO.md` 与 `docs/progress.md`；
   - 单任务单提交。

---

## 5. 一句话版

> 项目已完成 M2.3 消息存储/触发/展示基础，下一步进入 M2.4 流式输出完善。
