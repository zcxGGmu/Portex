# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-05 (Asia/Shanghai)  
仓库路径: `/home/zq/work-space/repo/ai-projs/posp/Portex`  
当前分支: `main`（本地相对远端 `ahead 8`）

---

## 1. 当前结论（先看这里）

- `M0` 已完成。
- `M1` 已完成（`M1.1` ~ `M1.6` 全勾选）。
- 当前起点：`M2.1.1`（`app/websocket.py`，ConnectionManager）。
- 当前可用状态：后端 API、认证中间件、前端骨架均可运行/构建。

---

## 2. 最近一次可复现验证（通过）

- `.venv/bin/pytest tests/unit/ -v` -> `1 passed`
- `.venv/bin/pytest -q` -> `39 passed`
- `.venv/bin/ruff check .` -> `All checks passed!`
- `curl http://127.0.0.1:8000/health` -> `200` + `{"status":"ok","version":"0.1.0"}`
- `cd web && npm run lint` -> pass
- `cd web && npm run build` -> pass（Vite 构建成功）

备注：`passlib` 仍有 `DeprecationWarning: crypt`（Python 3.13 将移除）。

---

## 3. M1 收尾说明（本轮刚完成）

- `M1.6.1`：新增 `tests/unit/test_auth_unit.py` 使 `tests/unit/` 验收命令可执行。
- `M1.6.2`：健康检查端点验证通过（`/health`）。
- `M1.6.3`：前端构建验证通过（`web`）。

---

## 4. 下一位 Codex 直接执行

1. 先读：
   - `docs/TODO.md`
   - `docs/progress.md`（本文件）
   - `docs/PORTEX_PLAN.md`
2. 从 `M2.1.1` 开始实现：
   - `app/websocket.py`（ConnectionManager）
   - `app/routes/websocket.py`
   - `web/src/api/ws.ts`
3. 每个子任务完成后固定流程：
   - 跑相关测试/验证
   - 更新 `docs/TODO.md` 与 `docs/progress.md`
   - 单任务单提交

---

## 5. 一句话版

> 项目已完成 M1 全阶段，下一步从 M2.1.1 的 WebSocket 基础设施开发继续。
