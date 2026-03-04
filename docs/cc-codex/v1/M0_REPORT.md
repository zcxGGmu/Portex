# Portex M0 阶段报告 (2026-03-04)

## 总结

M0 阶段目标（集成路径与契约定稿、3 个 PoC）已完成：

- M0.1 环境搭建完成（Python 3.11 `.venv` + editable 安装）
- M0.2 流式输出 PoC 完成（含事件类型记录与映射示例）
- M0.3 工具调用 PoC 完成（`read_file` 工具定义、注册和本地调用验证）
- M0.4 事件契约与映射完成（`PortexEvent` + SDK 映射器 + 测试）

## 关键产物

- 环境与工程基线
  - `pyproject.toml`
  - `.venv` (Python 3.11.14)
- PoC 1: Streaming
  - `pocs/streaming/main.py`
  - `pocs/streaming/event_types.md`
  - `pocs/streaming/event_mapper.py`
- PoC 2: Tools
  - `pocs/tools/main.py`
  - `pocs/tools/verification_output.json`
  - `pocs/tools/tool_call_flow.md`
- PoC 3: Contract + Mapper
  - `portex/contracts/events.py`
  - `pocs/events/mapper.py`
  - `tests/portex/contracts/test_events.py`
  - `tests/pocs/events/test_mapper.py`

## 验证结果

- Streaming/Tools/Contract 相关测试共 14 条通过。
- 事件映射覆盖最小闭环：
  - `run.started`
  - `run.token.delta`
  - `run.tool.started`
  - `run.tool.completed`
  - `run.completed`
  - `run.failed`

## 风险与后续

- 在线 E2E（真实模型触发工具）仍依赖 `OPENAI_API_KEY` 与可用模型。
- 下一阶段 M1 重点：FastAPI + SQLite 核心骨架、基础路由、队列与 WebSocket 流转。
