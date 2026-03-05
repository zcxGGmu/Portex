# Session Plan (2026-03-05) - M1.4

## Goal
- Continue from latest progress by implementing `M1.4.1` ~ `M1.4.4` (password hashing/JWT security/current-user DI/CORS hardening).

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, and `docs/TODO.md`
- [x] Define M1.4 implementation split and interface contracts
- [x] Use multi-agent workers for parallel implementation
- [x] Add/adjust security and API tests (TDD)
- [x] Verify with `.venv/bin/pytest -q` and `.venv/bin/ruff check .`
- [x] Update `docs/TODO.md` and `docs/progress.md`
- [x] Commit changes with a detailed message

## Review
- M1.4 已完成：密码哈希、JWT 过期、鉴权依赖注入、CORS 限制。
- 验证结果：`.venv/bin/pytest -q` => `38 passed`；`.venv/bin/ruff check .` => `All checks passed!`
