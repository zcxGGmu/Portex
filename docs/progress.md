# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-27 (Asia/Shanghai)
当前分支: `main`
最新 planning-only 提交: `70cb8dd` (`docs(plans): add offline relevance convergence audit plan`)
最新功能提交: `0402678` (`feat(terminal): add M8.5.53 history detail metadata export`)
上一条 handoff 提交: `a14ca20` (`docs(handoff): sync M8.5.53 history detail metadata export context`)

---

## 1. 当前阶段

- `docs/TODO.md` 的正式路线仍停在 `M6.5.3`；`M0` ~ `M6` 全部完成，post-`M6` 的 `M7.1` ~ `M7.6.5` parity backlog 也已完成。
- terminal relevance 主线已完成到 `M8.5.51`，且 2026-03-26 的 convergence audit 已确认当前 `81`-case offline baseline 收敛；默认下一步不是继续扩样或继续加 tie-break。
- 2026-03-27 没有新的功能变更；最新可执行功能状态仍是 `M8.5.53`，本次更新仅同步 restart-oriented handoff 锚点，方便下一次重启直接续做。
- `M8.5.52` 已完成并保持原始 transcript 下载；`M8.5.53` 已在当前分支完成：同一路径 `GET /terminals/{group_id}/sessions/history/{session_id}/download` 现在支持 `format=text|json`，默认仍是原始 `text/plain` 下载，并新增 metadata-rich `application/json` 附件导出；`/terminals` 的 history detail 面板现在同时提供 `Download Output` 和 `Download JSON`。
- 本次 `M8.5.53` 明确保持不变的边界：
  - 不改 `services/terminal_sessions.py`
  - 不改 terminal relevance / offline baseline / search 排序语义
  - 不改 `latest.json`
  - 不改 `/sessions/current/history`
  - 不改 RBAC / workspace-access contract

## 2. 最新验证证据

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
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
- `docs/plans/2026-03-26-m8-5-52-terminal-history-detail-download-design.md`
- `docs/plans/2026-03-26-m8-5-52-terminal-history-detail-download.md`
- `docs/plans/2026-03-26-m8-5-53-terminal-history-detail-metadata-export-design.md`
- `docs/plans/2026-03-26-m8-5-53-terminal-history-detail-metadata-export.md`

当前 terminal 线额外注意点：

- M8.5.52 / M8.5.53 的下载路由复用现有 history detail 读取路径和 RBAC 边界；默认 `format=text` 仍生成 `.log`，`format=json` 生成 `.json`
- 前端下载动作继续复用 `Blob` + `URL.createObjectURL(...)` 模式；如果继续这条线，优先沿用现有 detail/action state，不要另外造一套下载状态机
- relevance baseline 仍是 source of truth；只有出现新的真实证据时才重新进入 post-`M8.5.51` 排序 refinement

## 4. 下一位 Codex 直接执行

1. 先读 `docs/TODO.md`、`docs/progress.md`、`AGENTS.md`、`tasks/lessons.md`。
2. 如继续 terminal 线，先区分两类工作：
   - relevance / offline baseline：默认暂停，除非有新证据
   - operator surface：当前可从 `M8.5.53` 的 format-aware detail export 继续做小的加法功能
3. 如果要继续 terminal operator surface，只在有明确需求时考虑：
   - bulk export
   - richer metadata export 的更大范围版本（当前单-snapshot JSON 已覆盖最小形态）
   - operator 报告的具体 detail/download UX 问题
4. 动手前先更新 `tasks/todo.md` 与对应 planning docs；保持 RED -> 最小实现 -> 验证 -> 提交。

常用命令：

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- `.venv/bin/ruff check .`
- `cd web && npm run lint && npm run build`
- `git diff --check`

## 5. 一句话版

> `M8.5.53` 已把 `/terminals` history detail download 扩展为 `text|json` 双导出；terminal relevance baseline 仍保持收敛暂停，除非出现新的真实证据。
