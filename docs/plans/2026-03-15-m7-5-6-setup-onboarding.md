# M7.5.6 Setup/Onboarding Pages Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a minimal multi-step setup/onboarding page for first-run flow parity, without backend schema changes.

**Architecture:** Frontend-only extension. Add `/setup` route, setup page component, local completion marker, and login default redirect logic. Reuse existing settings APIs for provider/channel/system writes.

**Tech Stack:** React 19, TypeScript, existing `apiClient`, existing auth store and routing

---

### Task 1: Add Red-Stage Evidence For Setup Route

**Files:**
- Modify: `web/src/App.tsx`

**Step 1: Reference missing setup page**

- add import/route for `Setup` before creating `web/src/pages/Setup.tsx`

**Step 2: Run red-stage verification**

```bash
cd web && npm run build
```

Expected: FAIL because setup page module does not exist yet.

### Task 2: Implement Setup Page And First-Run Redirect

**Files:**
- Create: `web/src/pages/Setup.tsx`
- Modify: `web/src/pages/Login.tsx`
- Modify: `web/src/components/layout/AppLayout.tsx`
- Modify: `web/src/index.css`

**Step 1: Build minimal multi-step onboarding UI**

- provider step
- channels step
- system step (owner-writable, non-owner read-only hint)
- completion step

**Step 2: Add first-run marker flow**

- local storage key `portex.setup.completed`
- login default target: `/setup` when marker absent
- setup `Skip`/`Finish` sets marker and routes to `/chat`

**Step 3: Keep boundaries stable**

- no backend API/schema changes
- no websocket/chat protocol changes
- no terminal/mobile work

### Task 3: Verify, Handoff, Commit

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run verification**

```bash
cd web && npm run lint
cd web && npm run build
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
git diff --check
```

**Step 2: Update handoff**

- mark `M7.5.6` complete
- move next entrypoint to `M7.5.7`
- record red/green evidence and verification commands

**Step 3: Commit**

```bash
git add docs/plans/2026-03-15-m7-5-6-setup-onboarding-design.md docs/plans/2026-03-15-m7-5-6-setup-onboarding.md docs/progress.md web/src/App.tsx web/src/pages/Setup.tsx web/src/pages/Login.tsx web/src/components/layout/AppLayout.tsx web/src/index.css
git commit -m "feat(web): complete M7.5.6 setup onboarding pages"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-5-6-setup-onboarding.md`. Given you asked to continue in this session, I’m executing it directly now.
