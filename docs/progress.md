# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-06 (Asia/Shanghai)
仓库路径: `/home/zq/work-space/repo/ai-projs/posp/Portex`
当前分支: `main`

---

## 1. 当前阶段

- `M0` 已完成。
- `M1` 已完成（`M1.1` ~ `M1.6`）。
- `M2` 已完成（`M2.1` ~ `M2.6.1`）。
- 当前起点：`M3.1.1`（Docker SDK 集成）。

---

## 2. 最近完成

- `M2.5.1`：runtime 活跃 run 跟踪与取消基线
- `M2.5.2`：服务层超时控制与 `run.timeout` 契约
- `M2.5.3`：前端取消按钮 + WebSocket 取消入口
- `M2.6.1`：M2 阶段验收
  - live HTTP 链：`/auth/register` → `/auth/login`
  - live WS 链：普通消息 → `run.started` / `run.token.delta` / `run.completed`
  - live cancel 链：取消控制帧 → `run.failed(status=cancelled)`

---

## 3. 最新验证证据

- 聚焦路由：`.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q` -> `4 passed`
- 单元验收：`.venv/bin/pytest tests/unit/ -v` -> `1 passed`
- 全量回归：`.venv/bin/pytest -q` -> `65 passed`
- Lint：`.venv/bin/ruff check .` -> `All checks passed!`
- 前端：`cd web && npm run lint` -> pass
- 前端：`cd web && npm run build` -> pass
- M2 live acceptance：`.venv/bin/python /tmp/portex_m26_acceptance_check.py` -> `/tmp/portex_m26_acceptance_result.json`
- OpenAI 兼容 provider 连通性：
  - `OPENAI_API_KEY=... OPENAI_BASE_URL=https://api.hanbbq.top/v1 .venv/bin/python -c 'from openai import OpenAI; print(len(list(OpenAI().models.list().data)))'` -> 成功列出模型
  - `OPENAI_API_KEY=... OPENAI_BASE_URL=https://api.hanbbq.top/v1 OPENAI_DEFAULT_MODEL=gpt-5.1 OPENAI_AGENTS_DISABLE_TRACING=1 .venv/bin/python pocs/streaming/main.py --input '请只回复：测试通过'` -> 成功输出流式事件

备注：
- 当前环境默认没有 `OPENAI_API_KEY`；`M2.6.1` 的 live 验收使用了临时 fake runtime harness 来覆盖 HTTP/WS 全链路协议。
- 兼容 provider 下，Agents SDK 默认模型 `gpt-4.1` 不可用；若走真实在线验证，需显式设置 `OPENAI_DEFAULT_MODEL=gpt-5.1`。
- `passlib` 仍有 `DeprecationWarning: crypt`。
- `services/message_service.py` 仍有 `datetime.utcnow()` 弃用告警。

---

## 4. 下一位 Codex 直接执行

1. 先读：`docs/TODO.md`、`docs/progress.md`、`docs/PORTEX_PLAN.md`。
2. 从 `M3.1.1` 开始：
   - 确认 `docker` 依赖与本地环境
   - 建立 `infra/exec/docker.py` 客户端
   - 为 container/host 双模式保留清晰边界
3. 如需真实在线验证 OpenAI 兼容 provider：
   - 设置 `OPENAI_API_KEY`
   - 设置 `OPENAI_BASE_URL`
   - 设置 `OPENAI_DEFAULT_MODEL=gpt-5.1`
   - 避免把密钥写入仓库文件

---

## 5. 一句话版

> `M2` 已全部完成并验收通过，当前从 `M3.1.1` Docker SDK 集成继续。
