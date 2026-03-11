# M6.4.2 Dependency Audit Design

## Goal

Complete `M6.4.2` by adding the smallest repository-local Python dependency-audit workflow that is executable in the current environment and fits the existing backend verification chain.

## Scope

- add a repository-local `pip-audit` entrypoint under `scripts/`
- audit the repository's Python project dependency set rather than scanning the whole machine
- reuse the existing backend workflow and local command style established in `M6.4.1`
- add focused script tests for the new entrypoint
- expose the command in operator-facing docs and restart handoff notes

## Out of Scope

- do not replace or rework `scripts/security_scan.py`
- do not implement `M6.4.3` security headers or `app/middleware/security.py`
- do not add `npm audit`, frontend dependency auditing, CodeQL, Dependabot, secret scanning, or a broader security program
- do not introduce Python lockfiles, constraints files, or a dependency-management overhaul
- do not proactively upgrade large parts of the dependency graph unless the fresh `pip-audit` result forces a narrow fix

## Design Constraints

- `docs/TODO.md` names `pip-audit` explicitly for `M6.4.2`, so this milestone should stay aligned with that tool
- `docs/progress.md` requires that the work remain repository-local and reuse the current backend workflow rather than replacing the `M6.4.1` scan chain
- the current repository has no Python lockfile, so the audit must be honest about auditing the resolved dependency set available through the project definition and current installer behavior
- the milestone should stay Python-only because there is no TODO requirement yet for frontend dependency auditing

## Options Considered

### Option A: Repository-local wrapper around `python -m pip_audit .`

Pros:
- executable from the repo like `scripts/security_scan.py`
- keeps CI and local usage aligned
- audits the current Python project instead of arbitrary environment packages

Cons:
- still depends on the currently resolvable dependency set because there is no lockfile

### Option B: Wrapper around `python -m pip_audit --local`

Pros:
- audits the exact installed environment in CI and local development

Cons:
- more sensitive to incidental local environment drift
- weaker repo-local reproducibility story

### Option C: CI-only `pip-audit` command without a local script

Pros:
- smallest YAML-only change

Cons:
- does not meet the established repository-local toolchain pattern
- weaker local reproducibility

## Recommended Design

Choose **Option A**.

## Proposed Changes

### Repository-local audit entrypoint

- add `scripts/dependency_audit.py`
- make it run `sys.executable -m pip_audit .` from the repository root
- keep the command fixed and repo-owned, mirroring the `security_scan.py` pattern

### Dependencies

- add `pip-audit` to the `dev` extra in `pyproject.toml`
- continue relying on `pip install -e ".[dev]"` for local and CI setup

### CI integration

- add one backend workflow step in `.github/workflows/test.yml` for `python scripts/dependency_audit.py`
- keep the existing `security_scan.py`, tests, and lint steps unchanged

### Testing

- add `tests/scripts/test_dependency_audit.py`
- verify command construction and exit-code passthrough
- use the real `scripts/dependency_audit.py` run as the focused milestone verification

### Documentation and handoff

- add the new command to `README.md` and `AGENTS.md`
- record verification evidence and remaining boundaries in `docs/progress.md`
- append the current session plan and review notes to `tasks/todo.md`

## Risks and Boundaries

- without a lockfile, the audit result is only as stable as the currently resolved dependency graph
- if `pip-audit` reports real vulnerabilities, this milestone may require a narrow dependency-bound adjustment or a documented exception; that must be decided from fresh evidence, not assumed upfront
- this milestone still will not cover frontend packages

## Expected Deliverables

- a repository-local `scripts/dependency_audit.py` entrypoint
- focused tests for that script
- backend CI integration for the audit command
- updated restart-oriented docs moving the next step to `M6.4.3`
