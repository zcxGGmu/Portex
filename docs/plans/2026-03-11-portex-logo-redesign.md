# Portex Logo Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the README logo into a reference-inspired crab mascot plus `PORTEX` wordmark and wire it into both README entrypoints.

**Architecture:** Keep the feature scoped to documentation assets. Rework the existing shared SVG into a horizontal lockup, preserve the same asset path used by both README files, and update the static repository contract test so the README/logo slice stays protected without introducing any build pipeline.

**Tech Stack:** SVG, Markdown, Python `pytest`, Ruff

---

### Task 1: Lock the new horizontal logo contract in tests

**Files:**
- Modify: `tests/container/agent_runner/test_container_files.py`
- Reference: `README.md`
- Reference: `README.zh-CN.md`
- Reference: `assets/portex-crab-logo.svg`

**Step 1: Write the failing test change**

Update the README/logo assertions so they still require the shared SVG path and alt text, but now expect the horizontal SVG `viewBox` and the wider README image width.

```python
assert 'src="assets/portex-crab-logo.svg"' in content
assert 'alt="Portex project logo"' in content
assert 'width="560"' in content
assert root.attrib["viewBox"] == "0 0 1800 420"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/container/agent_runner/test_container_files.py -v`
Expected: FAIL because the current README width and current square SVG contract do not match the new design.

**Step 3: Write the minimal implementation**

Change the test file only.

**Step 4: Run test to verify the intended failure surface**

Run: `.venv/bin/pytest tests/container/agent_runner/test_container_files.py -v`
Expected: FAIL only on the README/logo contract assertions.

**Step 5: Commit**

```bash
git add tests/container/agent_runner/test_container_files.py
git commit -m "test(readme): lock horizontal Portex logo contract"
```

### Task 2: Redesign the shared SVG asset and rewire the README image block

**Files:**
- Modify: `assets/portex-crab-logo.svg`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Test: `tests/container/agent_runner/test_container_files.py`

**Step 1: Replace the SVG**

Redraw `assets/portex-crab-logo.svg` as a horizontal lockup with:

- left-side crab mascot in a dynamic 3/4 pose
- dark outline plus light outline for mascot readability
- deep navy body with teal/cyan highlights
- right-side all-caps `PORTEX` display wordmark
- transparent background
- horizontal `viewBox` sized for README use

**Step 2: Update the README blocks**

Keep the existing top placement in both README files, but widen the image block:

```html
<p align="center">
  <img src="assets/portex-crab-logo.svg" alt="Portex project logo" width="560" />
</p>
```

**Step 3: Run focused verification**

Run: `.venv/bin/pytest tests/container/agent_runner/test_container_files.py -v`
Expected: PASS

**Step 4: Run formatting hygiene**

Run: `git diff --check`
Expected: PASS

**Step 5: Commit**

```bash
git add assets/portex-crab-logo.svg README.md README.zh-CN.md tests/container/agent_runner/test_container_files.py
git commit -m "docs(readme): redesign Portex logo lockup"
```

### Task 3: Record the change and run the repo slice verification

**Files:**
- Modify: `docs/progress.md`
- Test: `tests/container/agent_runner/test_container_files.py`

**Step 1: Update progress handoff**

Add a concise entry describing:

- the logo redesign now follows the reference composition more closely
- the mascot changed from a geometric icon to a reference-inspired crab
- both README files still share the same SVG asset
- the focused verification evidence

**Step 2: Run verification**

Run:

```bash
.venv/bin/pytest tests/container/agent_runner/test_container_files.py -v
.venv/bin/ruff check tests/container/agent_runner/test_container_files.py
git diff --check
```

Expected: all commands succeed.

**Step 3: Commit**

```bash
git add docs/progress.md
git commit -m "docs(handoff): record Portex logo redesign"
```
