# Portex Project Icon Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a single SVG Portex crab logo and surface it at the top of both README entrypoints.

**Architecture:** The implementation stays intentionally small: add one repository asset, lock the README/logo contract with a focused static test, then wire the existing English and Chinese README files to the shared SVG. The icon itself should be self-contained in plain SVG so GitHub can render it directly without any build step.

**Tech Stack:** Python `pytest`, Markdown, SVG

---

### Task 1: Lock the README/logo contract with a failing test

**Files:**
- Create: `tests/scripts/test_readme_logo_assets.py`
- Read: `README.md`
- Read: `README.zh-CN.md`

**Step 1: Write the failing test**

```python
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
LOGO_PATH = ROOT / "assets" / "portex-crab-logo.svg"


def test_readmes_reference_shared_portex_logo_asset() -> None:
    for relative_path in ("README.md", "README.zh-CN.md"):
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "assets/portex-crab-logo.svg" in content
        assert 'alt="Portex project logo"' in content


def test_portex_logo_asset_exists_and_is_valid_svg() -> None:
    assert LOGO_PATH.exists()
    root = ET.fromstring(LOGO_PATH.read_text(encoding="utf-8"))
    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 512 512"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/scripts/test_readme_logo_assets.py -q`
Expected: FAIL because the shared README logo reference and SVG asset do not exist yet.

**Step 3: Write minimal implementation**

Add the shared README icon block and create the SVG asset at `assets/portex-crab-logo.svg`.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/scripts/test_readme_logo_assets.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/scripts/test_readme_logo_assets.py README.md README.zh-CN.md assets/portex-crab-logo.svg
git commit -m "docs(readme): add Portex crab project logo"
```

### Task 2: Build the SVG and wire both README files

**Files:**
- Create: `assets/portex-crab-logo.svg`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Test: `tests/scripts/test_readme_logo_assets.py`

**Step 1: Write the SVG**

Implement a self-contained SVG with:

- geometric front-facing crab
- navy + teal palette
- portal-like enclosing ring
- transparent background

**Step 2: Add the shared README icon block**

Insert a centered HTML image block directly below `# Portex` in both README files:

```html
<p align="center">
  <img src="assets/portex-crab-logo.svg" alt="Portex project logo" width="200" />
</p>
```

**Step 3: Run focused verification**

Run: `.venv/bin/pytest tests/scripts/test_readme_logo_assets.py -q`
Expected: PASS

**Step 4: Run repository documentation hygiene checks**

Run: `git diff --check`
Expected: PASS

**Step 5: Commit**

```bash
git add assets/portex-crab-logo.svg README.md README.zh-CN.md tests/scripts/test_readme_logo_assets.py
git commit -m "docs(readme): add Portex crab project logo"
```

### Task 3: Record the session and verify the repo slice

**Files:**
- Modify: `tasks/todo.md`
- Modify: `docs/progress.md`
- Test: `tests/scripts/test_readme_logo_assets.py`

**Step 1: Update session tracking**

Append this feature to `tasks/todo.md` and add a concise handoff note to `docs/progress.md`.

**Step 2: Run the verification commands**

Run:

```bash
.venv/bin/pytest tests/scripts/test_readme_logo_assets.py -q
.venv/bin/ruff check tests/scripts/test_readme_logo_assets.py
git diff --check
```

Expected: all commands succeed.

**Step 3: Commit**

```bash
git add tasks/todo.md docs/progress.md
git commit -m "docs(handoff): record README logo update"
```
