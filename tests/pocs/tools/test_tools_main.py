from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from pocs.tools.main import build_agent, invoke_read_file_locally, read_file


def test_read_file_tool_schema_contains_path() -> None:
    assert read_file.name == "read_file"
    assert "path" in read_file.params_json_schema["properties"]
    assert "path" in read_file.params_json_schema["required"]


def test_invoke_read_file_locally_reads_file(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hello tool", encoding="utf-8")
    assert invoke_read_file_locally(str(sample)) == "hello tool"


def test_build_agent_registers_read_file_tool() -> None:
    agent = build_agent()
    tool_names = [tool.name for tool in agent.tools]
    assert "read_file" in tool_names
