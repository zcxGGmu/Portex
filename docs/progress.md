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
- `M2.6.1` 已完成（M2 阶段验收）。
- 下一起点：`M3.1.1`（Docker SDK 集成）。

---

## 2. 本轮完成内容（M2.6.1）

- 启动了真实后端/前端验收环境：
  - 后端：临时 acceptance harness 驱动 `app.main.app`
  - 前端：`cd web && npm run dev -- --host 127.0.0.1 --port 5173`
- 通过 live HTTP 流程验证认证链：
  - `POST /auth/register`
  - `POST /auth/login`
  - token 返回正常
- 通过 live WebSocket 流程验证聊天链：
  - `WS /ws/group-demo` 发送普通文本
  - 收到 `run.started`、多条 `run.token.delta`、`run.completed`
- 通过 live WebSocket 流程验证取消链：
  - 发送长运行消息
  - 收到 `run.started`
  - 发送 `{"type":"cancel","run_id":"..."}` 控制帧
  - 收到终态 `run.failed(status=cancelled)`
- 新增验收计划文档：
  - `docs/plans/2026-03-06-m2-6-1-acceptance-flow.md`

---

## 3. 最新验证证据

- 端到端验收脚本：`.venv/bin/python /tmp/portex_m26_acceptance_check.py` -> `/tmp/portex_m26_acceptance_result.json`
- 验收结果要点：
  - 登录用户：`m26-dd4e3115`
  - 流式 run：`128ea8bed7c942a5a322922e6ca454e5`
  - 取消 run：`c829dce18609404aa0b258e05e9304b1`
- 聚焦路由验证：`.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q` -> `4 passed`
- 单元验收：`.venv/bin/pytest tests/unit/ -v` -> `1 passed`
- 全量回归：`.venv/bin/pytest -q` -> `65 passed`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass

备注：
- 当前环境未设置 `OPENAI_API_KEY`，所以 live 验收使用了临时 fake runtime harness 来验证 HTTP/WS 全链路协议，而非真实 OpenAI 模型调用。
- `M2.5.2` 的 timeout 语义仍由自动化测试覆盖；live harness 本轮重点验证了 send/stream/cancel 链。
- `passlib` 仍有 `DeprecationWarning: crypt`（Python 3.13 将移除）。
- `services/message_service.py` 仍有 `datetime.utcnow()` 的弃用告警，后续可单独处理。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
2. 从 `M3.1.1` 开始：
   - 在依赖中确认并启用 Docker SDK
   - 建立 `infra/exec/docker.py` 客户端
   - 保持 host/container 双模式边界清晰
3. 若要提升 M2 体验，可先考虑：
   - 把 `run.failed(status=cancelled)` 升级为正式 `run.cancelled`
   - 把前端注册页接到真实 `/auth/register`

---

## 5. 一句话版

> 项目已完成 `M2` 阶段验收，HTTP 登录链、WS 流式链、WS 取消链都已跑通，下一步进入 `M3.1.1` Docker SDK 集成。
