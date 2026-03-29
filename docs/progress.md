# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-29 (Asia/Shanghai)
当前分支: `main`
最新 planning-only 提交: `70cb8dd` (`docs(plans): add offline relevance convergence audit plan`)
最新功能提交: `c710a74` (`feat(terminal): add M8.5.58 overview export`)
上一条 handoff 提交: `2a7ae65` (`docs(handoff): sync M8.5.57 history search archive export context`)

---

## 1. 当前阶段

- `docs/TODO.md` 的正式路线仍停在 `M6.5.3`；`M0` ~ `M6` 全部完成，post-`M6` 的 `M7.1` ~ `M7.6.5` parity backlog 也已完成。
- terminal relevance 主线已完成到 `M8.5.51`，且 2026-03-26 的 convergence audit 已确认当前 `81`-case offline baseline 收敛；默认下一步不是继续扩样或继续加 tie-break。
- 最新可执行功能状态已推进到 `M8.5.58`：在保留 detail、timeline current-page、search current-page、timeline archive、search archive 五类 workspace-scoped 导出链路不变的前提下，新增 `GET /terminals/export`，导出当前 `/terminals` overview 的跨 workspace session/history inventory JSON；`/terminals` 顶层 summary 区域新增 `Export Overview JSON`。
- 本次 `M8.5.58` 明确保持不变的边界：
  - 不改 terminal relevance / offline baseline / search 排序语义
  - 不改 `latest.json`
  - 不改 `/sessions/current/history`
  - 不改已有 overview 读取合约
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
- `docs/plans/2026-03-29-m8-5-58-terminal-overview-export-design.md`
- `docs/plans/2026-03-29-m8-5-58-terminal-overview-export.md`

当前 terminal 线额外注意点：

- `M8.5.58` 把 overview 层也补上了导出；当前 `/terminals` 已覆盖 overview / timeline / search / detail 四层导出读面
- overview export 仅导出现有 `TerminalWorkspaceListResponse` 形状，不包含 timeline/search/detail payload 展开
- overview 导出、timeline archive、timeline current-page export、search archive、search current-page export、detail 下载继续复用 `Blob` + `URL.createObjectURL(...)` 模式；如果继续这条线，优先沿用现有 page-level action state，不要另外造一套下载状态机
- relevance baseline 仍是 source of truth；只有出现新的真实证据时才重新进入 post-`M8.5.51` 排序 refinement

## 4. 下一位 Codex 直接执行

1. 先读 `docs/TODO.md`、`docs/progress.md`、`AGENTS.md`、`tasks/lessons.md`。
2. 如继续 terminal 线，先区分两类工作：
   - relevance / offline baseline：默认暂停，除非有新证据
   - operator surface：当前已经具备 overview 导出、detail 导出、timeline current-page bulk JSON 导出、search current-page JSON 导出、timeline all-pages archive JSON 导出、search all-pages archive JSON 导出
3. 如果要继续 terminal operator surface，只在有明确需求时考虑：
   - overview/timeline/search/detail/archive 六类导出之间的 UX 一致性问题
   - 更大范围的跨 workspace transcript archive / bundle 需求
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

> `M8.5.58` 已把 `/terminals` terminal-history operator surface 扩展到“overview 导出 + detail 导出 + timeline/search current-page 导出 + timeline/search all-pages archive 导出”；terminal relevance baseline 仍保持收敛暂停，除非出现新的真实证据。
