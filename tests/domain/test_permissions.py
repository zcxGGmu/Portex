from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from domain.permissions import (  # noqa: E402
    PERMISSION_TEMPLATES,
    get_permissions_for_role,
    has_permission,
)


def test_permission_templates_define_expected_roles() -> None:
    assert set(PERMISSION_TEMPLATES) == {"owner", "admin", "member"}


def test_owner_and_admin_templates_expose_expected_actions() -> None:
    assert PERMISSION_TEMPLATES["owner"]["users"] == ("read", "write", "delete", "admin")
    assert PERMISSION_TEMPLATES["owner"]["settings"] == ("read", "write")
    assert PERMISSION_TEMPLATES["admin"]["tasks"] == ("read", "write", "execute")
    assert PERMISSION_TEMPLATES["admin"]["settings"] == ("read",)


def test_member_template_is_restricted() -> None:
    assert PERMISSION_TEMPLATES["member"]["groups"] == ("read",)
    assert PERMISSION_TEMPLATES["member"]["messages"] == ("read", "write")
    assert PERMISSION_TEMPLATES["member"]["tasks"] == ("read",)


def test_get_permissions_for_role_returns_copy_and_empty_for_unknown_role() -> None:
    admin_permissions = get_permissions_for_role("admin")
    unknown_permissions = get_permissions_for_role("guest")

    assert admin_permissions["users"] == ("read", "write")
    assert unknown_permissions == {}

    admin_permissions["users"] = ("tampered",)
    assert PERMISSION_TEMPLATES["admin"]["users"] == ("read", "write")


def test_has_permission_allows_known_role_action_pairs() -> None:
    assert has_permission("owner", "users", "admin") is True
    assert has_permission("admin", "tasks", "execute") is True
    assert has_permission("member", "messages", "write") is True


def test_has_permission_denies_unknown_or_forbidden_pairs() -> None:
    assert has_permission("member", "users", "read") is False
    assert has_permission("admin", "settings", "write") is False
    assert has_permission("guest", "messages", "read") is False
    assert has_permission("owner", "unknown", "read") is False
    assert has_permission("owner", "users", "unknown") is False
