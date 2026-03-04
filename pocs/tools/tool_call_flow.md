# Tool Call Flow (M0.3.4)

## Scope

This document records the minimal tool registration and invocation flow validated in `pocs/tools/main.py`.

## Components

- Tool definition: `read_file` (`@function_tool`)
- Local implementation: `invoke_read_file_locally(path)`
- Agent registration: `build_agent()` with `tools=[read_file]`

## Flow

1. Startup loads `read_file` tool metadata (`name`, `params_json_schema`).
2. `build_agent()` registers the tool into `Agent.tools`.
3. Dry-run mode executes local file reading path:
   - command: `.venv/bin/python pocs/tools/main.py --dry-run --sample-file README.md`
   - output file: `pocs/tools/verification_output.json`
4. Validation checks:
   - tool name equals `read_file`
   - argument schema requires `path`
   - invocation result returns file content length (`chars > 0`)

## Verified Evidence

- Unit tests: `tests/pocs/tools/test_main.py`
- Verification payload: `pocs/tools/verification_output.json`

## Next Step

Replace dry-run local call with online `Runner.run(...)` execution under a valid `OPENAI_API_KEY` to verify end-to-end model-triggered tool calls.
