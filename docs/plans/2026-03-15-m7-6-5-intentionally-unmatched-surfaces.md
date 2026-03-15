# M7.6.5 Intentionally Unmatched Surfaces Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M7.6.5` by consolidating which HappyClaw-specific surfaces are intentionally unmatched in Portex and separating them from surfaces that are only deferred.

**Architecture:** Docs-first consolidation milestone. Reuse the prior `M7.5.5`, `M7.6.1`, `M7.6.3`, and `M7.6.4` decisions as evidence, then publish one restart-oriented summary that future work can trust without re-deriving scope intent from several different milestone docs.

**Tech Stack:** Markdown docs, current progress/handoff docs, prior parity decision docs, existing verification command set

---

### Task 1: Gather Prior Decisions

**Files (read):**
- `docs/plans/2026-03-15-m7-5-5-terminal-panel-decision-design.md`
- `docs/plans/2026-03-15-m7-6-1-qq-scope-decision-design.md`
- `docs/plans/2026-03-15-m7-6-3-slash-command-scope-decision-design.md`
- `docs/plans/2026-03-15-m7-6-4-richer-im-artifacts-scope-decision-design.md`
- `tasks/todo.md`

**Step 1: Capture explicit exclusions**

- QQ
- generic slash commands
- richer IM artifacts

**Step 2: Capture deferred-but-reopenable surfaces**

- terminal panel remains deferred, not rejected

### Task 2: Publish M7.6.5 Consolidation Docs

**Files:**
- Create: `docs/plans/2026-03-15-m7-6-5-intentionally-unmatched-surfaces-design.md`
- Create: `docs/plans/2026-03-15-m7-6-5-intentionally-unmatched-surfaces.md`

**Step 1: Write design doc**

- list intentionally unmatched surfaces
- distinguish deferred surfaces
- describe reopen rule for excluded items

**Step 2: Write implementation plan**

- keep this milestone docs-only
- define the exact handoff update and verification commands

### Task 3: Refresh Handoff And Close The Current Decision Track

**Files:**
- Modify: `docs/progress.md`

**Step 1: Update progress context**

- mark `M7.6.5` complete
- state that the current `M7` parity-decision track is exhausted
- record the intentionally unmatched list in restart-friendly wording

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
git add docs/plans/2026-03-15-m7-6-5-intentionally-unmatched-surfaces-design.md docs/plans/2026-03-15-m7-6-5-intentionally-unmatched-surfaces.md docs/progress.md
git commit -m "docs(parity): complete M7.6.5 unmatched surfaces decision"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-6-5-intentionally-unmatched-surfaces.md`. Given you asked to continue in this session, I’m executing it directly now.
