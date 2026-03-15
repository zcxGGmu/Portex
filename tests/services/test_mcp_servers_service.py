from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def service(tmp_path: Path):
    from services.mcp_servers import McpServersService

    return McpServersService(data_dir=tmp_path / "data")


@pytest.mark.asyncio
async def test_list_user_servers_returns_empty_when_user_has_no_servers(service) -> None:
    servers = await service.list_user_servers("user-1")

    assert servers == []


@pytest.mark.asyncio
async def test_upsert_user_server_creates_stdio_server_and_returns_detail(service) -> None:
    entry = await service.upsert_user_server(
        "user-1",
        "local-cli",
        transport="stdio",
        command="uvx",
        args=["mcp-server-sqlite"],
        env={"MCP_ROOT": "/workspace"},
        description="Local stdio MCP",
    )
    detail = await service.get_user_server("user-1", "local-cli")

    assert entry.server_id == "local-cli"
    assert entry.transport == "stdio"
    assert entry.enabled is True
    assert detail.server_id == "local-cli"
    assert detail.transport == "stdio"
    assert detail.command == "uvx"
    assert detail.args == ["mcp-server-sqlite"]
    assert detail.env == {"MCP_ROOT": "/workspace"}
    assert detail.description == "Local stdio MCP"


@pytest.mark.asyncio
async def test_upsert_user_server_creates_http_server(service) -> None:
    detail = await service.upsert_user_server(
        "user-1",
        "remote-docs",
        transport="http",
        url="https://example.com/mcp",
        headers={"Authorization": "Bearer token"},
    )

    assert detail.transport == "http"
    assert detail.url == "https://example.com/mcp"
    assert detail.headers == {"Authorization": "Bearer token"}
    assert detail.command is None


@pytest.mark.asyncio
async def test_upsert_user_server_preserves_disabled_state(service) -> None:
    await service.upsert_user_server(
        "user-1",
        "persist-state",
        transport="stdio",
        command="node",
    )
    await service.set_user_server_enabled("user-1", "persist-state", enabled=False)

    updated = await service.upsert_user_server(
        "user-1",
        "persist-state",
        transport="sse",
        url="https://example.com/sse",
    )
    detail = await service.get_user_server("user-1", "persist-state")

    assert updated.enabled is False
    assert detail.enabled is False
    assert detail.transport == "sse"
    assert detail.url == "https://example.com/sse"


@pytest.mark.asyncio
async def test_set_user_server_enabled_toggles_state(service) -> None:
    await service.upsert_user_server(
        "user-1",
        "toggle-me",
        transport="stdio",
        command="python",
    )

    disabled = await service.set_user_server_enabled("user-1", "toggle-me", enabled=False)
    enabled = await service.set_user_server_enabled("user-1", "toggle-me", enabled=True)

    assert disabled.enabled is False
    assert enabled.enabled is True


@pytest.mark.asyncio
async def test_delete_user_server_removes_entry(service) -> None:
    await service.upsert_user_server(
        "user-1",
        "delete-me",
        transport="stdio",
        command="python",
    )

    await service.delete_user_server("user-1", "delete-me")

    with pytest.raises(FileNotFoundError, match="mcp server not found"):
        await service.get_user_server("user-1", "delete-me")


@pytest.mark.asyncio
async def test_upsert_user_server_rejects_invalid_server_id(service) -> None:
    with pytest.raises(ValueError, match="invalid server id"):
        await service.upsert_user_server(
            "user-1",
            "../bad",
            transport="stdio",
            command="python",
        )


@pytest.mark.asyncio
async def test_upsert_user_server_rejects_invalid_transport_payload(service) -> None:
    with pytest.raises(ValueError, match="command is required for stdio transport"):
        await service.upsert_user_server(
            "user-1",
            "bad-stdio",
            transport="stdio",
        )

    with pytest.raises(ValueError, match="url is required for http/sse transport"):
        await service.upsert_user_server(
            "user-1",
            "bad-http",
            transport="http",
        )


@pytest.mark.asyncio
async def test_list_user_servers_rejects_symlink_escape(service, tmp_path: Path) -> None:
    user_root = tmp_path / "data" / "mcp-servers" / "user-1"
    outside = tmp_path / "outside-user"
    outside.mkdir(parents=True, exist_ok=True)
    (outside / "servers.json").write_text('{"servers": {}}', encoding="utf-8")
    user_root.parent.mkdir(parents=True, exist_ok=True)
    user_root.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink traversal detected"):
        await service.list_user_servers("user-1")
