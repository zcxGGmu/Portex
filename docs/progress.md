# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-05 (Asia/Shanghai)
仓库路径: `/home/zcxggmu/workspace/hello-projs/posp/Portex`
当前分支: `main`

---

## 1. 当前阶段

- `M0` 已完成。
- `M1` 已完成（`M1.1` ~ `M1.6`）。
- `M2.1` 已完成（`M2.1.1` ~ `M2.1.3`）。
- 下一起点：`M2.2.1`（定义 `infra/runtime/adapter.py` 运行时抽象接口）。

---

## 2. 本轮完成内容（M2.1）

- 新增后端连接管理：`app/websocket.py`（`ConnectionManager`）。
- 新增后端 WebSocket 路由：`app/routes/websocket.py`（`/ws/{group_folder}`，房间内广播）。
- 主应用接入：`app/main.py` 注册 websocket router。
- 路由导出更新：`app/routes/__init__.py`。
- 新增测试：`tests/app/routes/test_websocket_routes.py`（连接、断开、房间广播、多房间状态）。
- 新增前端 WebSocket 客户端：`web/src/api/ws.ts`（URL 解析、消息解析、订阅辅助）。

---

## 3. 最新验证证据

- TDD 红灯（实现前）：
  - `.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q` -> `FFF`
  - 失败原因：`ModuleNotFoundError: No module named 'app.routes.websocket'` / websocket 路由未接入。
- TDD 绿灯（实现后）：
  - `.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q` -> `3 passed`
- 功能与回归：
  - `.venv/bin/pytest tests/unit/ -v` -> `1 passed`
  - `.venv/bin/pytest -q` -> `42 passed`
  - `.venv/bin/ruff check .` -> `All checks passed!`
  - `cd web && npm run lint` -> pass
  - `cd web && npm run build` -> pass（Vite 构建成功）

备注：`passlib` 仍有 `DeprecationWarning: crypt`（Python 3.13 将移除）。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
2. 从 `M2.2.1` 开始：
   - `infra/runtime/adapter.py`（`RunRequest` / `RunEvent` / `RunResult` / `AgentRuntime`）。
3. 子任务完成后固定流程：
   - 跑特性测试 + 全量回归；
   - 更新 `docs/TODO.md` 与 `docs/progress.md`；
   - 单任务单提交。

---

## 5. 一句话版

> 项目已完成 M2.1 WebSocket 基础设施，下一步进入 M2.2 Runtime 适配器。
