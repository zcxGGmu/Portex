# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-04-06 (Asia/Shanghai)
当前分支: `main`
最新 planning-only 提交: `9a3d2ad` (`docs(plans): add M8.5.61 terminal export UX consistency plan`)
最新功能提交: `b870f70` (`feat(web): add M8.5.61 terminal export UX consistency`)
上一条 handoff 提交: `5129a4a` (`docs(handoff): sync M8.5.60 cross-workspace history archive export context`)

---

## 1. 当前阶段

- `docs/TODO.md` 的正式路线仍停在 `M6.5.3`；`M0` ~ `M6` 全部完成，post-`M6` 的 `M7.1` ~ `M7.6.5` parity backlog 也已完成。
- terminal relevance 主线已完成到 `M8.5.51`，且 2026-03-26 的 convergence audit 已确认当前 `81`-case offline baseline 收敛；默认下一步不是继续扩样或继续加 tie-break。
- 最新可执行功能状态已推进到 `M8.5.61`：`M8.5.60` 已完成 cross-workspace history archive 导出；本次 `M8.5.61` 在不改任何 backend contract 的前提下，仅整理 `/terminals` 既有导出/下载 UX，一致化顶层、timeline、search、detail 四个区域的按钮顺序、成功/失败提示语气，并把重复的 `Blob` 下载流程收敛到 `web/src/pages/Terminals.tsx` 内的共享 helper。
- 本次 `M8.5.61` 明确保持不变的边界：
  - 不改 terminal relevance / offline baseline / search 排序语义
  - 不改 `latest.json`
  - 不改 `/sessions/current/history`
  - 不改任何 FastAPI route / response schema / attachment filename
  - 不改已有 latest-history bundle 合约
  - 不改已有 overview 导出合约
  - 不改已有 overview 读取合约
  - 不改已有 timeline all-pages archive 合约
  - 不改已有 search current-page export 合约
  - 不改已有 timeline current-page bulk export 合约
  - 不改已有 detail 下载 `format=text|json` 合约
  - 不改 page-level `actionKey` / `actionError` / `actionNotice` 模型
  - 不改 RBAC / workspace-access contract

## 2. 最新验证证据

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`
- `git diff --check`

## 3. 当前起点

关键文件：

- `web/src/pages/Terminals.tsx`
- `tests/app/routes/test_terminal_routes.py`
- `tests/app/routes/test_api_routes.py`
- `docs/plans/2026-04-06-m8-5-61-terminal-export-ux-consistency-design.md`
- `docs/plans/2026-04-06-m8-5-61-terminal-export-ux-consistency.md`

当前 terminal 线额外注意点：

- `M8.5.60` 在 latest-history bundle 之上增加了 full grouped archive，但仍保持 JSON-first，不引入 ZIP/CSV/text bundle
- `M8.5.61` 未新增任何导出能力，只把既有八类动作的顺序、提示语气和前端下载实现做了一次收敛整理
- cross-workspace history archive 顶层包含 `total_workspaces`、`total_snapshots` 和 grouped `items`；每个 workspace item 带 `group_id` / `group_name` / `chat_accessible` / `total` / `items`
- overview 导出、latest-history bundle、cross-workspace history archive、timeline archive、timeline current-page export、search archive、search current-page export、detail 下载继续复用 `Blob` + `URL.createObjectURL(...)` 模式；`M8.5.61` 已将这套流程在 `web/src/pages/Terminals.tsx` 内收敛成共享 helper，如果继续这条线，优先沿用现有 page-level action state，不要另外造一套下载状态机
- relevance baseline 仍是 source of truth；只有出现新的真实证据时才重新进入 post-`M8.5.51` 排序 refinement

## 4. 下一位 Codex 直接执行

1. 先读 `docs/TODO.md`、`docs/progress.md`、`AGENTS.md`、`tasks/lessons.md`。
2. 如继续 terminal 线，先区分两类工作：
   - relevance / offline baseline：默认暂停，除非有新证据
   - operator surface：当前已经具备 overview 导出、latest-history bundle、cross-workspace history archive、detail 导出、timeline current-page bulk JSON 导出、search current-page JSON 导出、timeline all-pages archive JSON 导出、search all-pages archive JSON 导出
3. 如果要继续 terminal operator surface，只在有明确需求时考虑：
   - 需要过滤器或更细粒度边界的 cross-workspace archive 需求
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

> `M8.5.61` 已在不改任何 terminal backend / API contract 的前提下，把 `/terminals` 既有八类 export/download 动作整理成一致的顺序、提示文案和共享前端下载流程；terminal relevance baseline 仍保持收敛暂停，除非出现新的真实证据。
