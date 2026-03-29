# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-29 (Asia/Shanghai)
当前分支: `main`
最新 planning-only 提交: `70cb8dd` (`docs(plans): add offline relevance convergence audit plan`)
最新功能提交: `60656f7` (`feat(terminal): add M8.5.57 history search archive export`)
上一条 handoff 提交: `4b40a7a` (`docs(handoff): sync M8.5.56 history archive export context`)

---

## 1. 当前阶段

- `docs/TODO.md` 的正式路线仍停在 `M6.5.3`；`M0` ~ `M6` 全部完成，post-`M6` 的 `M7.1` ~ `M7.6.5` parity backlog 也已完成。
- terminal relevance 主线已完成到 `M8.5.51`，且 2026-03-26 的 convergence audit 已确认当前 `81`-case offline baseline 收敛；默认下一步不是继续扩样或继续加 tie-break。
- 最新可执行功能状态已推进到 `M8.5.57`：在保留 `M8.5.56` timeline all-pages archive、`M8.5.54` timeline current-page export、`M8.5.55` search current-page export、以及 `M8.5.52` / `M8.5.53` detail 下载链路不变的前提下，新增 `GET /terminals/{group_id}/sessions/history/search/archive`，按当前 search 的 `q` / `sort` / `status` / `owner_user_id` / `session_id_prefix` / `snapshot_from` / `snapshot_to` 过滤条件导出当前 workspace 的 all-pages search-result JSON archive；`/terminals` search panel 新增 `Export Search Archive JSON`。
- 本次 `M8.5.57` 明确保持不变的边界：
  - 不改 terminal relevance / offline baseline / search 排序语义
  - 不改 `latest.json`
  - 不改 `/sessions/current/history`
  - 不改已有 timeline all-pages archive 合约
  - 不改已有 search current-page export 合约
  - 不改已有 timeline current-page bulk export 合约
  - 不改已有 detail 下载 `format=text|json` 合约
  - 不改 RBAC / workspace-access contract

## 2. 最新验证证据

- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`
- `git diff --check`

## 3. 当前起点

关键文件：

- `app/routes/terminals.py`
- `web/src/api/client.ts`
- `web/src/pages/Terminals.tsx`
- `tests/app/routes/test_terminal_routes.py`
- `tests/app/routes/test_api_routes.py`
- `docs/plans/2026-03-29-m8-5-57-terminal-history-search-archive-export-design.md`
- `docs/plans/2026-03-29-m8-5-57-terminal-history-search-archive-export.md`

当前 terminal 线额外注意点：

- `M8.5.56` 的 timeline archive 和 `M8.5.57` 的 search archive 都跨过了 current-page 边界，但仍只针对单个 workspace 和当前 filter slice，不是跨 workspace 归档
- search archive JSON 顶层包含 `group_id`、`query`、`sort`、`total`、当前 filters，以及现有 `TerminalSessionHistorySearchResponse` 形状的 `items`
- timeline archive、timeline current-page export、search archive、search current-page export、detail 下载继续复用 `Blob` + `URL.createObjectURL(...)` 模式；如果继续这条线，优先沿用现有 timeline/search/detail action state，不要另外造一套下载状态机
- relevance baseline 仍是 source of truth；只有出现新的真实证据时才重新进入 post-`M8.5.51` 排序 refinement

## 4. 下一位 Codex 直接执行

1. 先读 `docs/TODO.md`、`docs/progress.md`、`AGENTS.md`、`tasks/lessons.md`。
2. 如继续 terminal 线，先区分两类工作：
   - relevance / offline baseline：默认暂停，除非有新证据
   - operator surface：当前已经具备单快照 detail 导出、timeline current-page bulk JSON 导出、search current-page JSON 导出、timeline all-pages archive JSON 导出、search all-pages archive JSON 导出
3. 如果要继续 terminal operator surface，只在有明确需求时考虑：
   - timeline/search/detail/archive 五类导出之间的 UX 一致性问题
   - 更大范围的跨 surface / 跨 workspace 归档需求
   - operator 报告的具体 detail/download/export UX 问题
4. 动手前先更新 `tasks/todo.md` 与对应 planning docs；保持 RED -> 最小实现 -> 验证 -> 提交。

常用命令：

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- `.venv/bin/ruff check .`
- `cd web && npm run lint && npm run build`
- `git diff --check`

## 5. 一句话版

> `M8.5.57` 已把 `/terminals` terminal-history operator surface 扩展到“单快照 detail 导出 + timeline/search current-page 导出 + timeline/search all-pages archive 导出”；terminal relevance baseline 仍保持收敛暂停，除非出现新的真实证据。
