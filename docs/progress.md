# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-26 (Asia/Shanghai)
当前分支: `main`
最新 planning 提交: `70cb8dd` (`docs(plans): add offline relevance convergence audit plan`)
最新功能提交: `cdf21cb` (`feat(terminal): expand offline relevance foundational ranking fixtures`)
上一条 handoff 提交: `2ee97f9` (`docs(handoff): sync offline relevance convergence audit context`)

---

## 1. 当前阶段

- `docs/TODO.md` 的正式路线仍停在 `M6.5.3`；`M0` ~ `M6` 全部完成，post-`M6` 的 `M7.1` ~ `M7.6.5` parity backlog 也已完成。
- terminal 搜索排序逻辑主线已完成到 `M8.5.51`；2026-03-26 的最新功能相关工作仍然是 convergence audit，之后只有 docs-only handoff sync，没有新的 `services/terminal_sessions.py`、fixture、API 或 UI 变化。
- 当前离线评估入口仍是 `tests/fixtures/terminal_relevance_baseline.json`、`scripts/evaluate_terminal_relevance.py` 与 `tests/scripts/test_evaluate_terminal_relevance.py`；当前固定基线仍为 `81` 个 case。
- 2026-03-26 的收敛审计已确认：当前 81-case 基线已经覆盖 `M8.5.17` foundational ranking chain、whole-word / line-start / wrapper / marker / whitespace-family 主干，以及 `M8.5.50` / `M8.5.51` mixed-other tail 的 direct count、direct offset、pagination 与 no-single-space fallback 语义；本轮没有再发现值得补进离线 fixture 的非重复 service-test 缺口。
- 当前结论因此从“继续扩样”切换为“暂停扩样”：只有当新增 service test 暴露新的非重复语义、离线指标退化、或真实 operator/production 排序问题无法由现有 81-case 基线表达时，才继续扩 baseline 或进入 post-`M8.5.51` 新 tie-break 设计。
- `pyproject.toml` 中的 `greenlet>=3.0.0` 不能回退；这是 fresh `pip install -e '.[dev]'` 后 async SQLAlchemy 测试可运行的依赖修复。
- 当前策略仍是 baseline-first，但默认动作已更新为“保持现状”，而不是“继续补洞”。

## 2. 最新验证证据

最新功能相关验证证据仍来自 convergence audit：
- `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q`
- `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` -> `case_count=81`, `pass_count=81`, `pass_rate/top1_accuracy/mrr = 1.000`
- `git diff --check`

## 3. 当前起点

关键文件：
- `scripts/evaluate_terminal_relevance.py`
- `tests/fixtures/terminal_relevance_baseline.json`
- `tests/scripts/test_evaluate_terminal_relevance.py`
- `docs/plans/2026-03-26-terminal-relevance-offline-baseline-convergence-audit-design.md`
- `docs/plans/2026-03-26-terminal-relevance-offline-baseline-convergence-audit.md`
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
- `17b1fc1` / `cdf21cb` foundational ranking
- `70cb8dd` planning-only convergence audit
- `2ee97f9` handoff-only convergence audit sync

当前收敛审计结论：
- `M8.5.50` direct count 与 pagination 已分别由 `m8-5-50-mixed-other-count`、`m8-5-50-mixed-other-count-pagination` 固化。
- `M8.5.51` direct offset 与 pagination 已分别由 `m8-5-51-mixed-other-offset`、`m8-5-51-mixed-other-offset-pagination` 固化。
- mixed-other no-single-space fallback 已由 `no-single-space-fallback` 与 `m8-5-51-no-single-space-fallback-pagination` 固化。
- `M8.5.49` 相邻 fallback/offset 依赖链仍由 `other-leading-whitespace-no-single-space-fallback`、`other-leading-whitespace-offset-tie-break` 与 `m8-5-49-other-leading-whitespace-offset-pagination` 固化。
- 结论：当前没有额外的非重复 service-test 语义需要继续补进离线 fixture。

## 4. 下一位 Codex 直接执行

1. 先读 `docs/TODO.md`、`docs/progress.md`、`AGENTS.md`、`tasks/lessons.md`。
2. 如继续 terminal 搜索线，默认前提已变为“当前 81-case 基线已收敛”；不要重复补已经覆盖的 foundational ranking / pagination / direct count / direct offset / fallback 样本，尤其不要重复 `M8.5.50` / `M8.5.51` mixed-other tail。
3. 只有当你能指出一个当前 81-case 基线无法表达的真实新语义、离线指标问题，或明确的 operator/production 排序失败时，才继续扩 baseline 或提出 post-`M8.5.51` 新 tie-break。
4. 如果要进入新的 ranking refinement，先写 design，明确失败样本、为什么现有基线不足以表示它、以及为何不能只靠 fixture 扩样解决。
5. 动手前先更新 `tasks/todo.md` 与对应 planning docs；实现时遵循 RED -> 只扩 fixture/test 或最小排序逻辑改动 -> 对应验证 -> planning/feature/handoff 提交。
常用命令：
- `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint && npm run build`
- `git diff --check`

## 5. 一句话版

> 当前 `81`-case terminal relevance baseline 已完成收敛审计；默认下一步不是继续扩样，而是只有在出现新的真实证据时才考虑新的 ranking refinement。
