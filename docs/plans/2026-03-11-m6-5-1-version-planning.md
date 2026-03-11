# M6.5.1 Version Planning Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M6.5.1` by documenting the first release-version strategy and updating the repository handoff/docs without creating tags, changing package versions, or building release artifacts.

**Architecture:** Treat this milestone as a documentation-and-handoff decision point. Record the target release tag `v1.0.0`, keep runtime/package versions unchanged for now, and update repo-facing docs so `M6.5.2` can execute the tag/release step from a clear starting point.

**Tech Stack:** Markdown, repository docs, git

---

### Task 1: Record the planning decision in repo docs

**Files:**
- Modify: `README.md`
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`

**Step 1: Write the planning updates**

Record:
- planned first release tag `v1.0.0`
- current package/runtime version remains `0.1.0` until later release execution
- next starting point is `M6.5.2`

**Step 2: Sanity-check consistency**

Run:
- `rg -n "M6\\.5\\.1|M6\\.5\\.2|v1\\.0\\.0|0\\.1\\.0" README.md AGENTS.md docs/progress.md`

Expected: the docs consistently describe the planning-vs-execution split.

### Task 2: Update session tracking

**Files:**
- Modify: `tasks/todo.md`

**Step 1: Record checklist and review**

Add the current `M6.5.1` session plan and final review notes.

### Task 3: Run milestone verification

**Files:**
- Verify repository state only; no product code changes expected

**Step 1: Run verification**

Run:
- `git diff --check`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

Expected: PASS

### Task 4: Commit the milestone

**Files:**
- Commit all approved `M6.5.1` changes

**Step 1: Commit**

Prepare a focused commit such as:
- `docs(release): complete M6.5.1 version planning`
