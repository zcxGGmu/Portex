from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def service(tmp_path: Path):
    from services.skills import SkillsService

    return SkillsService(data_dir=tmp_path / "data")


@pytest.mark.asyncio
async def test_list_user_skills_returns_empty_when_user_has_no_skills(service) -> None:
    skills = await service.list_user_skills("user-1")

    assert skills == []


@pytest.mark.asyncio
async def test_upsert_user_skill_creates_enabled_skill_and_returns_detail(service, tmp_path: Path) -> None:
    entry = await service.upsert_user_skill(
        "user-1",
        "writer-guide",
        "# Writer Guide\nAlways clarify assumptions.",
    )
    detail = await service.get_user_skill("user-1", "writer-guide")

    assert entry.skill_id == "writer-guide"
    assert entry.enabled is True
    assert entry.size == len("# Writer Guide\nAlways clarify assumptions.".encode("utf-8"))
    assert detail.skill_id == "writer-guide"
    assert detail.enabled is True
    assert detail.content == "# Writer Guide\nAlways clarify assumptions."
    skill_file = (
        tmp_path
        / "data"
        / "skills"
        / "user-1"
        / "writer-guide"
        / "SKILL.md"
    )
    assert skill_file.exists()


@pytest.mark.asyncio
async def test_upsert_user_skill_preserves_disabled_state(service, tmp_path: Path) -> None:
    await service.upsert_user_skill("user-1", "ops-playbook", "v1")
    await service.set_user_skill_enabled("user-1", "ops-playbook", enabled=False)

    updated = await service.upsert_user_skill("user-1", "ops-playbook", "v2")
    detail = await service.get_user_skill("user-1", "ops-playbook")

    assert updated.enabled is False
    assert detail.enabled is False
    assert detail.content == "v2"
    disabled_file = (
        tmp_path
        / "data"
        / "skills"
        / "user-1"
        / "ops-playbook"
        / "SKILL.md.disabled"
    )
    enabled_file = (
        tmp_path / "data" / "skills" / "user-1" / "ops-playbook" / "SKILL.md"
    )
    assert disabled_file.exists()
    assert not enabled_file.exists()


@pytest.mark.asyncio
async def test_set_user_skill_enabled_toggles_skill_state_file(service, tmp_path: Path) -> None:
    await service.upsert_user_skill("user-1", "toggle-skill", "demo")

    disabled = await service.set_user_skill_enabled("user-1", "toggle-skill", enabled=False)
    enabled = await service.set_user_skill_enabled("user-1", "toggle-skill", enabled=True)

    assert disabled.enabled is False
    assert enabled.enabled is True
    skill_dir = tmp_path / "data" / "skills" / "user-1" / "toggle-skill"
    assert (skill_dir / "SKILL.md").exists()
    assert not (skill_dir / "SKILL.md.disabled").exists()


@pytest.mark.asyncio
async def test_delete_user_skill_removes_skill_directory(service, tmp_path: Path) -> None:
    await service.upsert_user_skill("user-1", "delete-me", "temporary")

    await service.delete_user_skill("user-1", "delete-me")

    skill_dir = tmp_path / "data" / "skills" / "user-1" / "delete-me"
    assert not skill_dir.exists()


@pytest.mark.asyncio
async def test_get_user_skill_raises_file_not_found_for_missing_skill(service) -> None:
    with pytest.raises(FileNotFoundError, match="skill not found"):
        await service.get_user_skill("user-1", "missing")


@pytest.mark.asyncio
async def test_skill_operations_reject_invalid_skill_id(service) -> None:
    with pytest.raises(ValueError, match="invalid skill id"):
        await service.upsert_user_skill("user-1", "../bad", "x")


@pytest.mark.asyncio
async def test_list_user_skills_rejects_symlink_escape(service, tmp_path: Path) -> None:
    user_root = tmp_path / "data" / "skills" / "user-1"
    outside = tmp_path / "outside-skill"
    outside.mkdir(parents=True, exist_ok=True)
    (outside / "SKILL.md").write_text("outside", encoding="utf-8")
    user_root.mkdir(parents=True, exist_ok=True)
    (user_root / "link-skill").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink traversal detected"):
        await service.list_user_skills("user-1")
