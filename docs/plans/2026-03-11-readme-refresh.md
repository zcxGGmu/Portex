# README Refresh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite the public English README into a product-facing project entrypoint and add a near-parity Chinese counterpart with truthful architecture/workflow diagrams and public support/todo framing.

**Architecture:** Keep the public entrypoint in two Markdown files only: `README.md` as the canonical English overview and `README.zh-CN.md` as the Chinese mirror. Derive all diagrams and claims from the current code paths, especially the WebSocket runtime flow and the current IM normalization boundary, while keeping session tracking in `tasks/todo.md` and `docs/progress.md`.

**Tech Stack:** Markdown, Mermaid, git, pytest, Ruff, npm

---

### Task 1: Rewrite the English README

**Files:**
- Modify: `README.md`
- Reference: `app/main.py`
- Reference: `app/routes/websocket.py`
- Reference: `services/agent_trigger.py`
- Reference: `infra/runtime/openai.py`
- Reference: `infra/im/feishu.py`
- Reference: `infra/im/telegram.py`
- Reference: `services/message_router.py`
- Reference: `app/routes/messages.py`

**Step 1: Capture the current public-doc gap**

Run: `rg -n "M[0-9]" README.md`

Expected: matches are found, proving the current README still exposes internal milestone identifiers.

**Step 2: Rewrite `README.md` with the approved structure**

Update `README.md` so it contains:

- top language switch linking to `README.zh-CN.md`
- a one-line pitch plus `Portex = Portal + Codex`
- `Why Portex`
- `What Works Today`
- `What's Next`
- `Architecture`
  - system overview Mermaid diagram
  - web run/stream/cancel Mermaid sequence
  - IM normalization/routing boundary Mermaid diagram
- `Quick Start`
- `Developer Workflow`
- `Repository Map`
- `Current Boundaries`
- `Documentation`

Keep the content honest:

- do not use any `M...` numbering
- do not present `/messages` as a complete delivery pipeline
- do not present Telegram outbound sending as already implemented
- do not place `container/agent-runner` on the current WebSocket happy path without labeling it as a separate slice

**Step 3: Verify the English README structure**

Run: `rg -n "Portal \\+ Codex|What Works Today|What's Next|```mermaid" README.md`

Expected: the naming story, public capability sections, and Mermaid diagrams are all present.

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs(readme): rewrite public english readme"
```

### Task 2: Add the Chinese counterpart README

**Files:**
- Create: `README.zh-CN.md`
- Reference: `README.md`

**Step 1: Confirm the counterpart file does not exist yet**

Run: `test -f README.zh-CN.md`

Expected: exit code `1`, confirming the file still needs to be created.

**Step 2: Write `README.zh-CN.md` as a near-parity mirror**

Create `README.zh-CN.md` with:

- top language switch linking back to `README.md`
- the same section order as the English README
- Chinese product positioning, feature framing, and boundaries
- the same Mermaid diagram topology, translated only where it improves readability without changing meaning

Keep the Chinese README aligned with the same public-doc rules:

- no internal `M...` numbering
- same current-support and next-step framing
- same honest caveats around IM, persistence, and Docker verification

**Step 3: Verify bilingual parity and public framing**

Run: `rg -n "Portal \\+ Codex|传送门|What Works Today|当前已支持|```mermaid" README.md README.zh-CN.md`

Expected: both files expose the naming story, bilingual public capability framing, and diagrams.

**Step 4: Commit**

```bash
git add README.zh-CN.md
git commit -m "docs(readme): add chinese counterpart"
```

### Task 3: Update session tracking and verify the documentation slice

**Files:**
- Modify: `tasks/todo.md`
- Modify: `docs/progress.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

**Step 1: Update task tracking**

Mark the README refresh checklist items complete in `tasks/todo.md` and add a short review section summarizing the public-doc improvements and verification evidence.

**Step 2: Update progress handoff**

Add a concise `docs/progress.md` entry describing:

- the README naming story refresh
- removal of public `M...` references
- the new Mermaid diagrams
- the addition of `README.zh-CN.md`
- the verification commands and outcomes

**Step 3: Run verification**

Run:

- `rg -n "M[0-9]" README.md README.zh-CN.md`
- `git diff --check`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

Expected:

- no internal milestone matches in the public READMEs
- clean diff formatting
- backend regression passes
- Ruff passes
- frontend lint passes
- frontend build passes

**Step 4: Commit**

```bash
git add README.md README.zh-CN.md tasks/todo.md docs/progress.md
git commit -m "docs(readme): refresh public project entrypoint"
```
