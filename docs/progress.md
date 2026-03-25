# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-25 (Asia/Shanghai)
当前分支: `main`
最新 planning 提交: `88c3e59` (`docs(plans): add offline relevance early whole-word positive expansion plan`)
最新功能提交: `c4e55a7` (`feat(terminal): expand offline relevance early whole-word positive fixtures`)
最新 handoff 提交: `ea93fc8` (`docs(handoff): sync offline relevance early fallback and delimiter quality context`)

---

## 1. 当前阶段

- `docs/TODO.md` 的正式路线仍停在 `M6.5.3`；`M0` ~ `M6` 全部完成，post-`M6` 的 `M7.1` ~ `M7.6.5` parity backlog 也已完成。
- terminal 搜索排序逻辑主线已完成到 `M8.5.51`；2026-03-25 的最新工作仍然没有继续改 `services/terminal_sessions.py` 排序逻辑，而是继续扩 terminal relevance 的离线基准。
- 当前活跃工作是 offline relevance baseline expansion：`tests/fixtures/terminal_relevance_baseline.json` 已扩到 `48` 个固定 case，`scripts/evaluate_terminal_relevance.py` 与 `tests/scripts/test_evaluate_terminal_relevance.py` 是当前离线评估入口。
- 当前 48-case 基线已覆盖：`raw > wrapper > plain` ladders、`M8.5.18` / `M8.5.19` 早期正向与 fallback 分支、whole-word / line-start-whole-word offset tie-break、marker/plain-wrapper pagination 与 offset tie-break、non-square marker families、brace/angle branch/fallback/pairwise、raw-marker 与 exact-tag wrapper delimiter quality、separator quality、payloadless/tab/multi-space/mixed-whitespace/other-leading whitespace families、punctuation-noise cleanliness。
- `pyproject.toml` 中的 `greenlet>=3.0.0` 不能回退；这是 fresh `pip install -e '.[dev]'` 后 async SQLAlchemy 测试可运行的依赖修复。
- 当前策略仍是 baseline-first：只有当离线样本或指标暴露稳定缺口时，才考虑继续 post-`M8.5.51` 的新 tie-break。

## 2. 最新验证证据

最新 early whole-word positive 扩样批次已通过以下验证：
- `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q`
- `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` -> `case_count=48`, `pass_count=48`, `pass_rate/top1_accuracy/mrr = 1.000`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest -o addopts='' -q` -> `740 passed`
- `.venv/bin/ruff check .`
- `cd web && npm run lint && npm run build`
- `git diff --check`

## 3. 当前起点

关键文件：
- `scripts/evaluate_terminal_relevance.py`
- `tests/fixtures/terminal_relevance_baseline.json`
- `tests/scripts/test_evaluate_terminal_relevance.py`
- `services/terminal_sessions.py`
- `tests/services/test_terminal_sessions.py`
- `pyproject.toml`
- `services/auth.py`
- `services/message_service.py`
当前 terminal 线必须保持的边界：
- 不改 `latest.json`
- 不改 `/sessions/current/history`
- 不改 API/DTO/UI/RBAC/search contract
- 不回退 `greenlet` 依赖修复
2026-03-24 ~ 2026-03-25 的离线扩样提交链：
- `7c1c4c7` / `ab90bbc` realistic-edge
- `6226cea` / `eeb388e` whitespace family
- `e64f835` / `841e3e2` marker/plain-wrapper
- `ca0be06` / `150a412` offset tie-break
- `c9c6ef1` / `76cecc3` non-square marker
- `c7fc16e` / `bd16927` brace/angle branch
- `38f9385` / `1171501` brace/angle fallback
- `84f6e4c` / `04553e8` brace/angle pairwise
- `d926bbb` / `d0f2b42` early fallback + delimiter quality
- `88c3e59` / `c4e55a7` early whole-word positive

## 4. 下一位 Codex 直接执行

1. 先读 `docs/TODO.md`、`docs/progress.md`、`AGENTS.md`、`tasks/lessons.md`。
2. 如继续 terminal 搜索线，先检查 `tests/services/test_terminal_sessions.py` 中仍未进入离线基准的 additive fallback / pagination 分支。
3. 当前最值得补的空位已转为 non-duplicate additive fallback 与 early pagination 样本，例如 `no exact-tag wrapper` fallback、`word-boundary` pagination、`line-boundary` pagination、`line-start quality` pagination；`no delimited log marker` fallback 不必单列，因为当前 `exact-tag-wrapper-delimiter-quality` 已覆盖同语义排序证据。
4. 动手前先更新 `tasks/todo.md` 与对应 planning docs；实现时遵循 RED -> 只扩 fixture/test -> 全量验证 -> planning/feature/handoff 三步提交。
常用命令：
- `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint && npm run build`
- `git diff --check`

## 5. 一句话版

> 当前主线不是继续加 terminal ranking tie-break，而是站在 `M8.5.51` 之上继续扩 terminal relevance 的 `48`-case 离线基准；最新功能批次为 `c4e55a7`，下一步仍是 baseline-first 地补 non-duplicate additive fallback 与 early pagination 空位。
