# M7.6.4 Richer IM Artifacts Scope Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M7.6.4` by explicitly excluding provider-specific rich IM artifact parity from the current Portex roadmap while documenting the narrow future-exception rule.

**Architecture:** Docs-first decision milestone. Reuse the current Portex IM adapter boundaries and HappyClaw's richer channel behaviors as evidence, then freeze a conservative scope choice: Portex keeps IM adapters minimal and does not commit to cards, reactions, or long-message chunking parity.

**Tech Stack:** Markdown docs, current roadmap/progress docs, HappyClaw README/source references, existing verification command set

---

### Task 1: Confirm Richer IM Artifact Baseline

**Files (read):**
- `infra/im/feishu.py`
- `infra/im/telegram.py`
- `/home/zcxggmu/workspace/hello-projs/agents/happyclaw/README.md`
- `/home/zcxggmu/workspace/hello-projs/agents/happyclaw/src/feishu.ts`
- `/home/zcxggmu/workspace/hello-projs/agents/happyclaw/src/telegram.ts`

**Step 1: Capture current Portex baseline**

- Feishu send path is minimal
- Telegram send path is minimal HTML-converted text
- no cards, reactions, or long-message chunking are implemented

**Step 2: Capture reference behavior**

- HappyClaw includes provider-specific richer artifact behaviors
- these are separate, platform-coupled feature slices rather than one generic abstraction

### Task 2: Publish M7.6.4 Decision Docs

**Files:**
- Create: `docs/plans/2026-03-15-m7-6-4-richer-im-artifacts-scope-decision-design.md`
- Create: `docs/plans/2026-03-15-m7-6-4-richer-im-artifacts-scope-decision.md`

**Step 1: Write design doc**

- choose `exclude richer IM artifact parity`
- document rationale
- define the narrow future-exception rule

**Step 2: Write implementation plan**

- keep this milestone docs-only
- define the exact handoff update and verification commands

### Task 3: Refresh Handoff And Entry Point

**Files:**
- Modify: `docs/progress.md`

**Step 1: Update progress context**

- mark `M7.6.4` complete
- move next entrypoint to `M7.6.5`
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
git add docs/plans/2026-03-15-m7-6-4-richer-im-artifacts-scope-decision-design.md docs/plans/2026-03-15-m7-6-4-richer-im-artifacts-scope-decision.md docs/progress.md
git commit -m "docs(parity): complete M7.6.4 richer im artifacts decision"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-6-4-richer-im-artifacts-scope-decision.md`. Given you asked to continue in this session, I’m executing it directly now.
