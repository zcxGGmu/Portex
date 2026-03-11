# M6.4.1 Security Scanning Design

## Goal

Complete `M6.4.1` by adding the smallest repository-local security scanning workflow that is executable in the current development and CI environment.

## Scope

- add one repository-local security scan entrypoint under `scripts/`
- reuse the existing Python dev toolchain instead of adding a new external SaaS or authenticated service
- scan runtime-oriented Python code with Ruff's Bandit-derived `S` rules
- exclude `tests/` from the security scan entrypoint so pytest `assert` usage does not dominate the signal
- make the current runtime scan pass by replacing or narrowly suppressing the existing findings
- wire the new entrypoint into the current backend CI job
- document the command in repository-facing docs and record verification evidence

## Out of Scope

- do not implement `M6.4.2` dependency auditing with `pip-audit`
- do not implement `M6.4.3` security headers or add `app/middleware/security.py`
- do not add CodeQL, Dependabot, Semgrep, Gitleaks, Trivy, or a broader security program
- do not introduce a Python lockfile, constraints file, or dependency pinning overhaul
- do not scan frontend dependencies or add `npm audit` in this milestone
- do not scan `tests/` because the immediate milestone goal is a useful runtime-code signal, not zero findings across all repository paths

## Design Constraints

- `docs/TODO.md` names the milestone "安全扫描", but `docs/progress.md` further constrains it to a minimal toolchain that is executable and verifiable inside this repository
- the current repository already depends on `ruff`, so reusing it keeps installation, CI, and local commands aligned
- the current `ruff check --select S` result on runtime code exposes only three findings, which makes a minimal pass realistic without broad refactoring
- `M6.4.2` remains the correct place for dependency vulnerability auditing, so `M6.4.1` should stay focused on code scanning

## Options Considered

### Option A: Implement `safety check` exactly as written in `docs/TODO.md`

Pros:
- closest to the original TODO snippet

Cons:
- current Safety CLI behavior and service model are a moving target
- adds a second security tool before the repository has a stable dependency-audit phase
- conflicts with the `docs/progress.md` requirement to keep this milestone executable and minimal in the current repo

### Option B: Freeze an older `safety` workflow

Pros:
- preserves the old command shape

Cons:
- ties the repository to dated tool behavior
- creates maintenance debt immediately
- still overlaps conceptually with the upcoming dependency-audit milestone

### Option C: Add a repository-local Ruff security-scan entrypoint

Pros:
- fully executable with the current dev environment
- no extra third-party service or credentials
- small enough to fit the milestone boundary
- clean separation from `M6.4.2` dependency auditing

Cons:
- not identical to the original TODO snippet
- only covers Python static security rules, not dependency vulnerabilities

## Recommended Design

Choose **Option C**.

## Proposed Changes

### Repository-local entrypoint

- add `scripts/security_scan.py`
- make it run `python -m ruff check --select S` against the runtime-oriented Python directories:
  - `app`
  - `domain`
  - `infra`
  - `services`
  - `scripts`
  - `pocs`
  - `portex`
  - `container/agent-runner/src`

### Current finding cleanup

- replace the two `assert normalized is not None` statements in `domain/schemas.py` with explicit defensive checks
- keep the `EventType.TOKEN_DELTA = "run.token.delta"` contract intact and add a narrow inline Ruff suppression for the false-positive `S105` hit in `portex/contracts/events.py`

### CI integration

- add one backend workflow step in `.github/workflows/test.yml` that runs `python scripts/security_scan.py`
- keep it inside the existing backend job rather than creating a new workflow

### Documentation and handoff

- add the new command to the command lists in `README.md` and `AGENTS.md`
- record milestone completion, verification evidence, and remaining boundaries in `docs/progress.md`
- track the current session plan and review notes in `tasks/todo.md`

## Testing Strategy

- add tests first for the new scan script in `tests/scripts/test_security_scan.py`
- verify the script builds the intended Ruff command and returns the subprocess exit status
- run the script itself as the focused milestone verification
- run full backend regression, backend lint, and frontend lint/build after the scan passes

## Risks and Boundaries

- this milestone will not prove dependency vulnerability status; that remains explicitly deferred to `M6.4.2`
- scanning only runtime-oriented Python directories means repository-wide false positives from tests are intentionally left out of this milestone
- Ruff `S` rules are useful but still heuristic; any inline suppression added here must stay narrow and justified

## Expected Deliverables

- a repository-local `scripts/security_scan.py` entrypoint
- passing script tests plus a passing real security-scan command
- backend CI integration for the new command
- restart-oriented milestone notes in `docs/progress.md` and `tasks/todo.md`
