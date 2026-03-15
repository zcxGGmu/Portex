# M7.6.3 Slash-Command Scope Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M7.6.3` by explicitly excluding HappyClaw-style generic slash-command parity from the current Portex roadmap while documenting the narrow future-exception rule.

**Architecture:** Docs-first decision milestone. Reuse the current Portex product surface and HappyClaw slash-command reference behavior as evidence, then freeze a conservative scope choice: Portex keeps management flows in Web and does not create a generic IM slash-command control plane.

**Tech Stack:** Markdown docs, current roadmap/progress docs, HappyClaw README/source references, existing verification command set

---

### Task 1: Confirm Slash-Command Baseline

**Files (read):**
- `/home/zcxggmu/workspace/hello-projs/agents/happyclaw/README.md`
- `/home/zcxggmu/workspace/hello-projs/agents/happyclaw/src/index.ts`
- `tasks/todo.md`
- `docs/progress.md`

**Step 1: Capture reference behavior**

- note the HappyClaw command set and what kinds of state it mutates

**Step 2: Capture current Portex baseline**

- Portex has no generic slash-command layer
- Web/operator surfaces already cover the important management actions

### Task 2: Publish M7.6.3 Decision Docs

**Files:**
- Create: `docs/plans/2026-03-15-m7-6-3-slash-command-scope-decision-design.md`
- Create: `docs/plans/2026-03-15-m7-6-3-slash-command-scope-decision.md`

**Step 1: Write design doc**

- choose `exclude generic slash-command parity`
- document rationale
- define the narrow future-exception rule

**Step 2: Write implementation plan**

- keep this milestone docs-only
- define the exact handoff update and verification commands

### Task 3: Refresh Handoff And Entry Point

**Files:**
- Modify: `docs/progress.md`

**Step 1: Update progress context**

- mark `M7.6.3` complete
- move next entrypoint to `M7.6.4`
- note that no runtime code changed in this milestone

### Task 4: Verify And Commit

**Step 1: Run verification**

```bash
cd web && npm run lint
cd web && npm run build
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
git diff --check
```

**Step 2: Commit**

```bash
git add docs/plans/2026-03-15-m7-6-3-slash-command-scope-decision-design.md docs/plans/2026-03-15-m7-6-3-slash-command-scope-decision.md docs/progress.md
git commit -m "docs(parity): complete M7.6.3 slash command decision"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-6-3-slash-command-scope-decision.md`. Given you asked to continue in this session, I’m executing it directly now.
