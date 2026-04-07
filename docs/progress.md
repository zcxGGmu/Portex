# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-04-07 (Asia/Shanghai)
当前分支: `main`
最新 planning-only 提交: `9a3d2ad` (`docs(plans): add M8.5.61 terminal export UX consistency plan`)
最新功能状态: 当前工作树已完成 `M8.5.62` terminal cross-workspace history archive filters
上一条 handoff 提交: `5129a4a` (`docs(handoff): sync M8.5.60 cross-workspace history archive export context`)

---

## 1. 当前阶段

- `docs/TODO.md` 的正式路线仍停在 `M6.5.3`；`M0` ~ `M6` 全部完成，post-`M6` 的 `M7.1` ~ `M7.6.5` parity backlog 也已完成。
- terminal relevance 主线已完成到 `M8.5.51`，且 2026-03-26 的 convergence audit 已确认当前 `81`-case offline baseline 收敛；默认下一步不是继续扩样或继续加 tie-break。
- 最新可执行功能状态已推进到 `M8.5.62`：在 `M8.5.60` 顶层 grouped cross-workspace history archive 与 `M8.5.61` 顶层导出 UX 收敛之上，`GET /terminals/history/archive` 现已支持 `owner_user_id`、`session_id_prefix`、`snapshot_from`、`snapshot_to` 四个可选过滤器，并在返回体顶层追加 `filters` 回显对象。
- `M8.5.62` 继续保持 additive 边界：
  - 不改 `GET /terminals/export`
  - 不改 `GET /terminals/history/export`
  - 不改 workspace-scoped timeline/search/detail/export/archive routes
  - 不改 grouped archive item payload、attachment filename、RBAC、`404` 空结果语义
  - 不改 `latest.json`、`/sessions/current/history`、relevance/ranking/offline baseline
  - 不改 `M8.5.61` 的 page-level `actionKey` / `actionError` / `actionNotice` 模型，只在 `/terminals` summary 区增加 archive-only filter state 和输入框

## 2. 最新验证证据

- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`
- `git diff --check`

## 3. 当前起点

关键文件：

- `services/terminal_sessions.py`
- `app/routes/terminals.py`
- `web/src/api/client.ts`
- `web/src/pages/Terminals.tsx`
- `tests/services/test_terminal_sessions.py`
- `tests/app/routes/test_terminal_routes.py`
- `tests/app/routes/test_api_routes.py`
- `docs/plans/2026-04-06-m8-5-62-terminal-cross-workspace-history-archive-filters-design.md`
- `docs/plans/2026-04-06-m8-5-62-terminal-cross-workspace-history-archive-filters.md`

当前 terminal 线额外注意点：

- `M8.5.62` 只给顶层 cross-workspace history archive 增加最小 owner/session/time 过滤，不扩散到 overview 或 latest-history bundle
- 顶层 grouped archive 现在额外回显 `filters.owner_user_id` / `filters.session_id_prefix` / `filters.snapshot_from` / `filters.snapshot_to`
- `/terminals` summary 区新增 archive-only 过滤输入；只有 `Export History Archive JSON` 使用它们，overview 和 latest-history 继续保持无过滤语义
- workspace-scoped timeline/search/export/archive 既有过滤契约和前端 preset/range 逻辑保持不变；顶层 archive 仅复用相同的 local-datetime -> UTC ISO 转换语义
- relevance baseline 仍是 source of truth；只有出现新的真实证据时才重新进入 post-`M8.5.51` 排序 refinement

## 4. 下一位 Codex 直接执行

1. 先读 `docs/TODO.md`、`docs/progress.md`、`AGENTS.md`、`tasks/lessons.md`。
2. 如继续 terminal 线，先区分两类工作：
   - relevance / offline baseline：默认暂停，除非有新证据
   - operator surface：当前已经具备 overview 导出、latest-history bundle、带 owner/session/time 过滤的 cross-workspace history archive、detail 导出、timeline current-page bulk JSON 导出、search current-page JSON 导出、timeline all-pages archive JSON 导出、search all-pages archive JSON 导出
3. 如果要继续 terminal operator surface，只在有明确需求时考虑：
   - operator 报告需要 `status` 或其它新增边界的 top-level archive 过滤
   - operator 报告的具体 detail/download/export UX 问题
   - 明确要求将现有 page-local download helper 进一步抽成复用组件时，再评估是否值得扩散到其他页面
4. 动手前先更新 `tasks/todo.md` 与对应 planning docs；保持 RED -> 最小实现 -> 验证 -> 提交。

常用命令：

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- `.venv/bin/ruff check .`
- `cd web && npm run lint && npm run build`
- `git diff --check`

## 5. 一句话版

> `M8.5.62` 已在保持 grouped archive、RBAC、filename 和 workspace-scoped history contract 不变的前提下，为 `/terminals` 顶层 cross-workspace history archive 增加 owner/session/time 过滤与最小配套 UI；terminal relevance baseline 仍保持收敛暂停，除非出现新的真实证据。
