# M7.6.1 QQ Scope Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M7.6.1` by explicitly excluding QQ from the current Portex parity roadmap and documenting the milestone consequences of that decision.

**Architecture:** Docs-first decision milestone. Reuse the current Portex roadmap, Portex project plan, and HappyClaw reference material as evidence, then freeze a conservative scope decision: QQ remains reference-only and does not enter the active Portex parity track.

**Tech Stack:** Markdown docs, current roadmap/progress docs, HappyClaw reference README/CLAUDE material, existing verification command set

---

### Task 1: Confirm QQ Scope Baseline

**Files (read):**
- `tasks/todo.md`
- `docs/PORTEX_PLAN.md`
- `/home/zcxggmu/workspace/hello-projs/agents/happyclaw/README.md`
- `/home/zcxggmu/workspace/hello-projs/agents/happyclaw/CLAUDE.md` (QQ and slash-command slices as needed)

**Step 1: Capture current Portex baseline**

- Portex stable channels are Web, Feishu, Telegram
- there is no QQ implementation, config surface, or test baseline in the current repo

**Step 2: Capture reference scope**

- HappyClaw QQ support includes runtime connection, pairing, group/private semantics, and settings/config surfaces
- this confirms QQ is a large integration commitment, not a tiny adapter add-on

### Task 2: Publish M7.6.1 Decision Docs

**Files:**
- Create: `docs/plans/2026-03-15-m7-6-1-qq-scope-decision-design.md`
- Create: `docs/plans/2026-03-15-m7-6-1-qq-scope-decision.md`

**Step 1: Write design doc**

- choose `QQ excluded from current Portex parity scope`
- document rationale
- document downstream effect on `M7.6.2`

**Step 2: Write implementation plan**

- keep this milestone docs-only
- define the exact handoff update and verification commands

### Task 3: Refresh Handoff And Entry Point

**Files:**
- Modify: `docs/progress.md`

**Step 1: Update progress context**

- mark `M7.6.1` complete
- note that `M7.6.2` is not applicable under the current decision
- move next entrypoint to `M7.6.3`

**Step 2: Record evidence**

- note the HappyClaw reference scope that was considered
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
git add docs/plans/2026-03-15-m7-6-1-qq-scope-decision-design.md docs/plans/2026-03-15-m7-6-1-qq-scope-decision.md docs/progress.md
git commit -m "docs(parity): complete M7.6.1 qq scope decision"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-6-1-qq-scope-decision.md`. Given you asked to continue in this session, I’m executing it directly now.
