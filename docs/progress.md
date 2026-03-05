# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-05 (Asia/Shanghai)
仓库路径: `/home/zq/work-space/repo/ai-projs/posp/Portex`
当前分支: `main`

---

## 1. 当前状态（结论先看）

- `M0` 已全部完成（`M0.1` ~ `M0.5` 全勾选）。
- `M1` 已全部完成（`M1.1` ~ `M1.6` 全勾选）。
- 当前应从 `M2.1.1` 开始继续开发（WebSocket 管理器）。
- 最近一次验证结果：
  - 命令: `.venv/bin/pytest tests/unit/ -v`
  - 结果: `1 passed`
  - 命令: `curl http://127.0.0.1:8000/health`（通过 uvicorn 临时启动验证）
  - 结果: `200` + `{"status":"ok","version":"0.1.0"}`
  - 命令: `cd web && npm run build`
  - 结果: `vite build` 通过
  - 命令: `.venv/bin/pytest -q`
  - 结果: `39 passed`
  - 命令: `.venv/bin/ruff check .`
  - 结果: `All checks passed!`
  - 备注: 测试输出仍有 `passlib` 的 `DeprecationWarning`（`crypt` 在 Python 3.13 移除）。

---

## 2. 本轮新增（M1.6）

### M1.6.1 运行单元测试
- 为满足验收命令 `pytest tests/unit/ -v`，补充最小单测：
  - `tests/unit/test_auth_unit.py`
  - 覆盖密码 hash/verify 基础行为

### M1.6.2 验证 API 端点
- 临时启动 `uvicorn app.main:app`，通过 `curl` 验证：
  - `GET /health` 返回 `200` 和 `{"status":"ok","version":"0.1.0"}`

### M1.6.3 验证前端构建
- 在 `web/` 执行 `npm run build`，`tsc -b && vite build` 通过。

---

## 3. 关键产物索引（重启后优先读）

1. `docs/TODO.md`（主任务清单，真源）
2. `docs/PORTEX_PLAN.md`（总体架构与阶段规划）
3. `app/main.py`、`app/middleware/auth.py`（后端 API 与鉴权入口）
4. `web/src/App.tsx`、`web/src/pages/Login.tsx`（前端入口与登录页）
5. `tests/unit/test_auth_unit.py`（M1.6 单测验收入口）

---

## 4. 下一步建议（直接执行）

1. `M2.1.1` 创建 `ConnectionManager`（`app/websocket.py`）
2. `M2.1.2` 增加 WebSocket 路由（`app/routes/websocket.py`）
3. `M2.1.3` 前端新增 ws 客户端（`web/src/api/ws.ts`）
4. 每个子任务完成后继续执行：测试 + 文档回填 + 单任务提交

---

## 5. 一句话版

> Portex 已完成 M1 全阶段验收，当前进入 M2.1 WebSocket 基础设施开发，起点是 `M2.1.1`。
