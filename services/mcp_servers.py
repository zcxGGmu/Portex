"""Filesystem-backed MCP server management service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Literal

from infra.exec.security import validate_path


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MCP_SERVERS_DIRNAME = "mcp-servers"
MCP_SERVERS_FILENAME = "servers.json"
MAX_MCP_SERVERS_FILE_SIZE_BYTES = 512 * 1024
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_MCP_TRANSPORTS = {"stdio", "http", "sse"}
McpTransport = Literal["stdio", "http", "sse"]


@dataclass(frozen=True, slots=True)
class McpServerEntry:
    server_id: str
    transport: McpTransport
    enabled: bool
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class McpServerDetail:
    server_id: str
    transport: McpTransport
    enabled: bool
    description: str | None
    created_at: datetime
    updated_at: datetime
    command: str | None
    args: list[str] | None
    env: dict[str, str] | None
    url: str | None
    headers: dict[str, str] | None


class McpServersService:
    """Manage user-owned MCP server entries under ``data/mcp-servers/{user_id}``."""

    def __init__(
        self,
        *,
        data_dir: str | Path | None = None,
        max_file_size_bytes: int = MAX_MCP_SERVERS_FILE_SIZE_BYTES,
    ) -> None:
        root = Path(data_dir or DATA_DIR).expanduser().resolve()
        self._mcp_servers_root = (root / MCP_SERVERS_DIRNAME).resolve()
        self._mcp_servers_root.mkdir(parents=True, exist_ok=True)
        self._max_file_size_bytes = max_file_size_bytes

    async def list_user_servers(self, user_id: str) -> list[McpServerEntry]:
        return await asyncio.to_thread(self._list_user_servers, user_id)

    async def get_user_server(self, user_id: str, server_id: str) -> McpServerDetail:
        return await asyncio.to_thread(self._get_user_server, user_id, server_id)

    async def upsert_user_server(
        self,
        user_id: str,
        server_id: str,
        *,
        transport: str,
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        description: str | None = None,
    ) -> McpServerDetail:
        return await asyncio.to_thread(
            self._upsert_user_server,
            user_id,
            server_id,
            transport,
            command,
            args,
            env,
            url,
            headers,
            description,
        )

    async def set_user_server_enabled(
        self,
        user_id: str,
        server_id: str,
        *,
        enabled: bool,
    ) -> McpServerDetail:
        return await asyncio.to_thread(self._set_user_server_enabled, user_id, server_id, enabled)

    async def delete_user_server(self, user_id: str, server_id: str) -> None:
        await asyncio.to_thread(self._delete_user_server, user_id, server_id)

    def _list_user_servers(self, user_id: str) -> list[McpServerEntry]:
        servers = self._read_user_servers(user_id)
        entries: list[McpServerEntry] = []

        for server_id in sorted(servers.keys(), key=lambda item: item.lower()):
            detail = self._detail_from_record(server_id, servers[server_id])
            entries.append(
                McpServerEntry(
                    server_id=detail.server_id,
                    transport=detail.transport,
                    enabled=detail.enabled,
                    updated_at=detail.updated_at,
                )
            )
        return entries

    def _get_user_server(self, user_id: str, server_id: str) -> McpServerDetail:
        safe_server_id = self._validate_segment(server_id, label="server id")
        servers = self._read_user_servers(user_id)
        record = servers.get(safe_server_id)
        if record is None:
            raise FileNotFoundError("mcp server not found")
        return self._detail_from_record(safe_server_id, record)

    def _upsert_user_server(
        self,
        user_id: str,
        server_id: str,
        transport: str,
        command: str | None,
        args: list[str] | None,
        env: dict[str, str] | None,
        url: str | None,
        headers: dict[str, str] | None,
        description: str | None,
    ) -> McpServerDetail:
        safe_server_id = self._validate_segment(server_id, label="server id")
        transport_payload = self._normalize_transport_payload(
            transport=transport,
            command=command,
            args=args,
            env=env,
            url=url,
            headers=headers,
        )
        normalized_description = self._normalize_optional_string(description)

        now = datetime.now(timezone.utc)
        servers = self._read_user_servers(user_id)

        existing_record = servers.get(safe_server_id)
        if existing_record is None:
            enabled = True
            created_at = now
        else:
            existing_detail = self._detail_from_record(safe_server_id, existing_record)
            enabled = existing_detail.enabled
            created_at = existing_detail.created_at

        record: dict[str, Any] = {
            "enabled": enabled,
            "transport": transport_payload["transport"],
            "description": normalized_description,
            "created_at": self._iso_datetime(created_at),
            "updated_at": self._iso_datetime(now),
        }

        if transport_payload["transport"] == "stdio":
            record["command"] = transport_payload["command"]
            record["args"] = transport_payload["args"]
            record["env"] = transport_payload["env"]
        else:
            record["url"] = transport_payload["url"]
            record["headers"] = transport_payload["headers"]

        servers[safe_server_id] = record
        self._write_user_servers(user_id, servers)

        return self._detail_from_record(safe_server_id, record)

    def _set_user_server_enabled(
        self,
        user_id: str,
        server_id: str,
        enabled: bool,
    ) -> McpServerDetail:
        safe_server_id = self._validate_segment(server_id, label="server id")
        servers = self._read_user_servers(user_id)
        record = servers.get(safe_server_id)
        if record is None:
            raise FileNotFoundError("mcp server not found")

        detail = self._detail_from_record(safe_server_id, record)
        if detail.enabled == enabled:
            return detail

        updated_record = dict(record)
        updated_record["enabled"] = enabled
        updated_record["updated_at"] = self._iso_datetime(datetime.now(timezone.utc))

        servers[safe_server_id] = updated_record
        self._write_user_servers(user_id, servers)
        return self._detail_from_record(safe_server_id, updated_record)

    def _delete_user_server(self, user_id: str, server_id: str) -> None:
        safe_server_id = self._validate_segment(server_id, label="server id")
        servers = self._read_user_servers(user_id)
        if safe_server_id not in servers:
            raise FileNotFoundError("mcp server not found")

        servers.pop(safe_server_id)
        self._write_user_servers(user_id, servers)

    def _detail_from_record(self, server_id: str, record: dict[str, Any]) -> McpServerDetail:
        if not isinstance(record, dict):
            raise ValueError("invalid mcp servers file")

        enabled = record.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError("invalid mcp servers file")

        transport_raw = record.get("transport")
        if not isinstance(transport_raw, str):
            raise ValueError("invalid mcp servers file")
        transport = transport_raw.strip().lower()
        if transport not in _MCP_TRANSPORTS:
            raise ValueError("invalid mcp servers file")

        description = record.get("description")
        if description is not None and not isinstance(description, str):
            raise ValueError("invalid mcp servers file")

        created_at = self._parse_datetime(record.get("created_at"))
        updated_at = self._parse_datetime(record.get("updated_at"))

        if transport == "stdio":
            command = self._normalize_required_string(record.get("command"), "command")
            args = self._normalize_string_list(record.get("args"), label="args")
            env = self._normalize_string_dict(record.get("env"), label="env")
            return McpServerDetail(
                server_id=server_id,
                transport="stdio",
                enabled=enabled,
                description=description,
                created_at=created_at,
                updated_at=updated_at,
                command=command,
                args=args,
                env=env,
                url=None,
                headers=None,
            )

        url = self._normalize_required_string(record.get("url"), "url")
        headers = self._normalize_string_dict(record.get("headers"), label="headers")
        return McpServerDetail(
            server_id=server_id,
            transport=transport,
            enabled=enabled,
            description=description,
            created_at=created_at,
            updated_at=updated_at,
            command=None,
            args=None,
            env=None,
            url=url,
            headers=headers,
        )

    def _normalize_transport_payload(
        self,
        *,
        transport: str,
        command: str | None,
        args: list[str] | None,
        env: dict[str, str] | None,
        url: str | None,
        headers: dict[str, str] | None,
    ) -> dict[str, Any]:
        normalized_transport = (transport or "").strip().lower()
        if normalized_transport not in _MCP_TRANSPORTS:
            raise ValueError("invalid transport")

        if normalized_transport == "stdio":
            normalized_command = self._normalize_optional_string(command)
            if not normalized_command:
                raise ValueError("command is required for stdio transport")
            normalized_args = self._normalize_string_list(args, label="args")
            normalized_env = self._normalize_string_dict(env, label="env")
            return {
                "transport": "stdio",
                "command": normalized_command,
                "args": normalized_args,
                "env": normalized_env,
            }

        normalized_url = self._normalize_optional_string(url)
        if not normalized_url:
            raise ValueError("url is required for http/sse transport")
        normalized_headers = self._normalize_string_dict(headers, label="headers")
        return {
            "transport": normalized_transport,
            "url": normalized_url,
            "headers": normalized_headers,
        }

    def _read_user_servers(self, user_id: str) -> dict[str, dict[str, Any]]:
        user_root = self._user_root(user_id)
        servers_path = self._servers_file(user_id)
        if not servers_path.exists():
            return {}

        self._ensure_safe_servers_file(servers_path, user_root)

        file_stats = servers_path.stat()
        if file_stats.st_size > self._max_file_size_bytes:
            raise ValueError("mcp servers file exceeds size limit")

        try:
            payload = json.loads(servers_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("invalid mcp servers file") from exc

        if not isinstance(payload, dict):
            raise ValueError("invalid mcp servers file")

        servers = payload.get("servers", {})
        if not isinstance(servers, dict):
            raise ValueError("invalid mcp servers file")

        normalized_servers: dict[str, dict[str, Any]] = {}
        for server_id, record in servers.items():
            if not isinstance(server_id, str):
                raise ValueError("invalid mcp servers file")
            safe_server_id = self._validate_segment(server_id, label="server id")
            if not isinstance(record, dict):
                raise ValueError("invalid mcp servers file")
            normalized_servers[safe_server_id] = dict(record)

        return normalized_servers

    def _write_user_servers(self, user_id: str, servers: dict[str, dict[str, Any]]) -> None:
        servers_path = self._servers_file(user_id)
        user_root = self._user_root(user_id)
        self._ensure_safe_servers_file(servers_path, user_root)

        payload = {
            "servers": {
                server_id: servers[server_id]
                for server_id in sorted(servers.keys(), key=lambda item: item.lower())
            }
        }
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if len(encoded.encode("utf-8")) > self._max_file_size_bytes:
            raise ValueError("mcp servers file exceeds size limit")

        servers_path.write_text(f"{encoded}\n", encoding="utf-8")

    def _user_root(self, user_id: str) -> Path:
        safe_user_id = self._validate_segment(user_id, label="user id")
        user_root = self._mcp_servers_root / safe_user_id
        if not validate_path(user_root.resolve(strict=False), [self._mcp_servers_root]):
            raise ValueError("symlink traversal detected")
        user_root.mkdir(parents=True, exist_ok=True)
        return user_root

    def _servers_file(self, user_id: str) -> Path:
        user_root = self._user_root(user_id)
        servers_path = user_root / MCP_SERVERS_FILENAME
        if not validate_path(servers_path.resolve(strict=False), [user_root]):
            raise ValueError("symlink traversal detected")
        return servers_path

    def _ensure_safe_servers_file(self, file_path: Path, user_root: Path) -> None:
        if not validate_path(file_path.resolve(strict=False), [user_root]):
            raise ValueError("symlink traversal detected")
        if file_path.name != MCP_SERVERS_FILENAME:
            raise ValueError("unexpected mcp servers file name")
        if file_path.exists() and file_path.is_dir():
            raise IsADirectoryError("mcp servers path is a directory")

    def _validate_segment(self, value: str, *, label: str) -> str:
        normalized = (value or "").strip()
        if not _SAFE_SEGMENT.fullmatch(normalized):
            raise ValueError(f"invalid {label}")
        return normalized

    def _normalize_optional_string(self, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("expected string value")
        normalized = value.strip()
        return normalized or None

    def _normalize_required_string(self, value: Any, label: str) -> str:
        if not isinstance(value, str):
            raise ValueError("invalid mcp servers file")
        normalized = value.strip()
        if not normalized:
            raise ValueError("invalid mcp servers file")
        return normalized

    def _normalize_string_list(self, value: Any, *, label: str) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError(f"{label} must be an array of strings")

        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError(f"{label} must be an array of strings")
            cleaned = item.strip()
            if not cleaned:
                raise ValueError(f"{label} must be an array of strings")
            normalized.append(cleaned)
        return normalized

    def _normalize_string_dict(self, value: Any, *, label: str) -> dict[str, str]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError(f"{label} must be an object with string values")

        normalized: dict[str, str] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"{label} must be an object with string values")
            if not isinstance(item, str):
                raise ValueError(f"{label} must be an object with string values")
            normalized[key.strip()] = item
        return normalized

    def _parse_datetime(self, value: Any) -> datetime:
        if not isinstance(value, str):
            raise ValueError("invalid mcp servers file")

        candidate = value.strip()
        if not candidate:
            raise ValueError("invalid mcp servers file")

        if candidate.endswith("Z"):
            candidate = f"{candidate[:-1]}+00:00"

        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError as exc:
            raise ValueError("invalid mcp servers file") from exc

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _iso_datetime(self, value: datetime) -> str:
        normalized = value.astimezone(timezone.utc).replace(microsecond=0)
        return normalized.isoformat()


mcp_servers_service = McpServersService()


__all__ = [
    "MAX_MCP_SERVERS_FILE_SIZE_BYTES",
    "MCP_SERVERS_FILENAME",
    "McpServerDetail",
    "McpServerEntry",
    "McpServersService",
    "mcp_servers_service",
]
