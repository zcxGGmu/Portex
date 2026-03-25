# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-25 (Asia/Shanghai)
当前分支: `main`
最新 planning 提交: `9a35949` (`docs(plans): add offline relevance direct whitespace-family plan`)
最新功能提交: `272b487` (`feat(terminal): expand offline relevance direct whitespace-family fixtures`)
上一条 handoff 提交: `12b74a6` (`docs(handoff): refresh restart context sync`)

---

## 1. 当前阶段

- `docs/TODO.md` 的正式路线仍停在 `M6.5.3`；`M0` ~ `M6` 全部完成，post-`M6` 的 `M7.1` ~ `M7.6.5` parity backlog 也已完成。
- terminal 搜索排序逻辑主线已完成到 `M8.5.51`；2026-03-25 的最新工作仍然没有继续改 `services/terminal_sessions.py` 排序逻辑，而是继续扩 terminal relevance 的离线基准。
- 当前活跃工作仍是 offline relevance baseline expansion：`tests/fixtures/terminal_relevance_baseline.json` 已扩到 `77` 个固定 case，`scripts/evaluate_terminal_relevance.py` 与 `tests/scripts/test_evaluate_terminal_relevance.py` 是当前离线评估入口。
- 当前 77-case 基线已覆盖：`raw > wrapper > plain` ladders、`M8.5.18` / `M8.5.19` 早期正向与 fallback 分支、whole-word / line-start-whole-word offset tie-break、`M8.5.22` no-exact-tag-wrapper fallback、`M8.5.18` / `M8.5.19` / `M8.5.20` 早期 pagination、`M8.5.21` / `M8.5.22` / `M8.5.23` / `M8.5.24` / `M8.5.25` 中段 pagination、later quality-family pagination through punctuation-noise / single-space / separator-noise、payload-family pagination through payloadless / payloadless-offset / tab-prefixed / multi-space / space-prefixed mixed-whitespace plus square-bracket plain-offset pagination、marker/plain-wrapper pagination 与 offset tie-break、non-square marker families、brace/angle branch/fallback/pairwise、raw-marker 与 exact-tag wrapper delimiter quality、separator quality、whitespace-family no-single-space fallback branches through tab-prefixed / multi-space / space-prefixed mixed-whitespace / other-leading whitespace plus the existing mixed-other fallback coverage，以及剩余 direct whitespace-family separator-quality / offset tie-break evidence through `M8.5.49`。这意味着白空白家族在 service 测试里已经没有已知但尚未固化进离线 fixture 的 direct gap。
- `pyproject.toml` 中的 `greenlet>=3.0.0` 不能回退；这是 fresh `pip install -e '.[dev]'` 后 async SQLAlchemy 测试可运行的依赖修复。
- 当前策略仍是 baseline-first：只有当离线样本、service 语义缺口或指标暴露稳定缺口时，才继续扩 baseline；否则应基于现有 77-case 证据决定是否需要 post-`M8.5.51` 的新 tie-break。

## 2. 最新验证证据

最新 direct whitespace-family 扩样批次已通过以下验证：
- `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q`
- `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` -> `case_count=77`, `pass_count=77`, `pass_rate/top1_accuracy/mrr = 1.000`
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
- `570aff0` / `4769d84` additive fallback + early pagination
- `afff472` / `69d39f9` mid-chain pagination
- `5b1bb1e` / `597f25d` late quality pagination
- `85a449b` / `4276c59` payload + offset pagination
- `946f202` / `91cdb9c` final payload pagination
- `913a6b1` / `f4ff3fa` whitespace fallback
- `9a35949` / `272b487` direct whitespace-family

## 4. 下一位 Codex 直接执行

1. 先读 `docs/TODO.md`、`docs/progress.md`、`AGENTS.md`、`tasks/lessons.md`。
2. 如继续 terminal 搜索线，先检查 `tests/services/test_terminal_sessions.py` 与 `tests/fixtures/terminal_relevance_baseline.json`，确认是否还存在未进入 `77`-case 基线的非重复 service-test 语义；不要重复当前已覆盖的 pagination / direct count / direct offset / fallback 样本。
3. 当前 `77`-case 基线已经覆盖最近一轮 whitespace-family direct gap；如果确认没有新的非重复 fixture 空位，就停止扩 baseline，并基于现有离线证据决定是否需要 post-`M8.5.51` 新 tie-break。只有在发现真实语义缺口或指标问题时才继续扩样。
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

> 当前主线仍然不是直接继续加 terminal ranking tie-break，而是先用 `77`-case 离线基线确认 service 语义是否还有真实覆盖空位；最新功能批次为 `272b487`，下一步应先判断 baseline expansion 是否已经到头，再决定是否进入新的 ranking refinement。
