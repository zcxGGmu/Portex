# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-04-16 (Asia/Shanghai)
当前分支: `main`
最新 planning-only 提交: `fad5e0f` (`docs(plans): add M8.5.74 terminal search-input normalization plan`)
最新功能状态: 当前工作树已完成 `M8.5.74` terminal effective search query input normalization
上一条 handoff 提交: `757c192` (`docs(handoff): refresh latest main progress context`)

---

## 1. 当前阶段

- `docs/TODO.md` 的正式路线仍停在 `M6.5.3`；`M0` ~ `M6` 全部完成，post-`M6` 的 `M7.1` ~ `M7.6.5` parity backlog 也已完成。
- terminal relevance 主线已完成到 `M8.5.51`，且 2026-03-26 的 convergence audit 已确认当前 `81`-case offline baseline 收敛；默认下一步不是继续扩样或继续加 tie-break。
- 最新可执行功能状态已推进到 `M8.5.74`：在保持 `M8.5.73` owner/session effective-filter normalization、`M8.5.72` overview 空态去重和既有 backend search contracts 不变的前提下，`/terminals` 现在会在提交搜索时把受控搜索输入框同步收敛到 trimmed 的 effective query，并且只在 effective query 非空时才继续 arm first-match 跳转。这样提交 `  error  ` 后，输入框、`Query:` 文案、搜索请求、detail 高亮和 search export 都统一落在同一个 `error` 值上；纯空白提交也不再在输入框里保留一个只存在于视觉层的空白查询。这个增量仍然只影响前端搜索提交派生逻辑，不改变任何 backend contract。
- `M8.5.74` 继续保持 additive 边界：
  - 不改 `GET /terminals/export`
  - 不改 `GET /terminals/history/export`
  - 不改 `GET /terminals/history/archive`
  - 不改 `services/terminal_sessions.py` 的 snapshot-level filter 语义；archive-only filters 仍保持当前 route-owned + service-owned 分层
  - 不改 workspace-scoped timeline/search/detail/export/archive routes
  - 不改 grouped archive item payload、attachment filename、RBAC、`404` 空结果语义
  - 不改 `latest.json`、`/sessions/current/history`、relevance/ranking/offline baseline
  - 不改 `M8.5.61` 的 page-level `actionKey` / `actionError` / `actionNotice` 模型，只修正 `/terminals` 现有搜索输入在 submit 边界上的 effective-value 对齐

## 2. 最新验证证据

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`
- `git diff --check`

## 3. 当前起点

关键文件：

- `app/routes/terminals.py`
- `web/src/pages/Terminals.tsx`
- `tests/app/routes/test_terminal_routes.py`
- `tests/app/routes/test_api_routes.py`
- `docs/plans/2026-04-16-m8-5-74-terminal-effective-search-query-input-normalization-design.md`
- `docs/plans/2026-04-16-m8-5-74-terminal-effective-search-query-input-normalization.md`

当前 terminal 线额外注意点：

- `M8.5.74` 不新增任何顶层 archive 或 workspace-scoped search 参数，也不改 overview/timeline/search payload；只是让搜索输入框在 submit 后收敛到已经生效的 trimmed query
- 顶层 grouped archive 仍回显 `filters.group_name_prefix` / `filters.group_id_prefix` / `filters.chat_accessible` / `filters.status` / `filters.owner_user_id` / `filters.session_id_prefix` / `filters.snapshot_from` / `filters.snapshot_to`
- `/terminals` summary 区的 archive-only 过滤输入现在包含 `Workspace Name Prefix`、`Workspace Prefix`、`Chat Access`、五态 `Status` 和既有 owner/session/time 输入，并额外提供过滤态提示、逐项可清除 chips、`Clear Archive Filters`、以及与 timeline/search 对齐的 `1h` / `6h` / `24h` / `7d` / `30d` 时间快捷范围；只有 `Export History Archive JSON` 使用它们，overview 和 latest-history 继续保持无过滤语义
- `/terminals` 现在会把 archive/timeline/search 三条路径上的 `owner_user_id` / `session_id_prefix` 文本过滤先 trim 成 effective 值，再用于请求参数和 archive chips；因此纯空白 owner/session 输入不再产生假的 active archive filter 提示
- `/terminals` 搜索框现在会在 submit 时把输入值同步成 effective trimmed query；因此提交带前后空白的查询后，输入框、`Query:` 文案、detail 高亮和 search export 使用的是同一个值，纯空白提交也不会继续留下视觉层空白查询
- `/terminals` overview table 里的 `History Session` 现在展示 `history.session.session_id`，与列名和 typed payload 对齐；不再误显示 `history.session.status`
- `/terminals` overview 的 “无 workspace” 场景现在只保留表内空态行 `Terminal overview is empty.`，不再在表外额外重复渲染一条提示
- `/terminals` workspace timeline table 的空态行现在跨满 8 列（含 `Actions`），与当前表头结构保持一致
- reset 只重置 archive-only state，不触碰 timeline/search/detail state，也不会触发任何网络请求
- chips 只清除对应的 archive-only 字段，不触碰其它 archive filters，也不会触发任何网络请求
- workspace-scoped timeline/search/export/archive 既有过滤契约和前端 preset/range 逻辑保持不变；顶层 archive 继续复用相同的 local-datetime -> UTC ISO 转换语义，并且 archive-only active preset 只在 preset 点击时高亮，手动时间编辑、时间类 chip 清除和 bulk reset 都会清掉它
- relevance baseline 仍是 source of truth；只有出现新的真实证据时才重新进入 post-`M8.5.51` 排序 refinement
- 顶层 archive 这条线当前更适合只响应明确的 operator 反馈；如果没有新的真实使用痛点，默认不要继续堆新的 archive 参数或细碎 UX。

## 4. 下一位 Codex 直接执行

1. 先读 `docs/TODO.md`、`docs/progress.md`、`AGENTS.md`、`tasks/lessons.md`。
2. 如继续 terminal 线，先区分两类工作：
   - relevance / offline baseline：默认暂停，除非有新证据
   - operator surface：当前已经具备 overview 导出、latest-history bundle、带 `group_name_prefix`/`group_id_prefix`/`chat_accessible`/`status`/owner/session/time 过滤、逐项清除 chips、一键 reset、archive-only 时间快捷范围、前端对 owner/session effective filter 的 whitespace normalization、submit-time search input normalization、正确的 overview `History Session` 列、去重后的 overview 空态、以及正确的 timeline 空态列宽的 cross-workspace history archive、detail 导出、timeline current-page bulk JSON 导出、search current-page JSON 导出、timeline all-pages archive JSON 导出、search all-pages archive JSON 导出
3. 如果要继续 terminal operator surface，只在有明确需求时考虑：
   - operator 报告需要 `backend` 或其它新增边界的 top-level archive 过滤
   - operator 报告的具体 detail/download/export UX 问题，尤其是当前 archive-only chips/reset/preset shortcuts、effective-filter 展示和 search submit 对齐之外的交互摩擦
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

> `M8.5.74` 已在保持 grouped archive、RBAC、filename、backend/API contracts 和 workspace-scoped history contract 不变的前提下，把 `/terminals` 搜索框在 submit 边界上统一收敛到 effective trimmed query，让输入框、`Query:` 文案、detail 高亮和 search export 对齐到同一个查询值，同时保留 `M8.5.73` 的 owner/session effective-filter normalization、`M8.5.72` 的 overview 空态去重、`M8.5.71` 的 timeline 空态列宽修正和 `M8.5.69` 的 archive-only 时间快捷范围；terminal relevance baseline 仍保持收敛暂停，除非出现新的真实证据。
