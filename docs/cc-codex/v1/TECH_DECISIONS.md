# Portex 技术选型确认 (M0.5.3)

## 决策清单

| 决策项 | 结论 | 状态 | 依据 |
|---|---|---|---|
| Agent 框架 | OpenAI Agents SDK (Python) | 已确认 | M0.1/M0.2 PoC 通过，`Agent/Runner` 可用 |
| 执行能力来源 | Codex CLI（复用，不重造） | 已确认 | 与 Portex 核心原则一致，利于后续能力继承 |
| Web 后端 | FastAPI | 已确认 | 与异步流式输出和 WebSocket 兼容 |
| 数据存储 | SQLite + SQLAlchemy 2.0 | 已确认 | 与 HappyClaw 轻量部署模式一致 |
| 隔离执行 | Docker 默认 + Host 可选 | 已确认 | 满足多用户隔离和管理员直连两种场景 |
| IPC 机制 | 文件 IPC + 原子写入 | 已确认 | 兼容 HappyClaw 通信模型，便于迁移 |
| 流式事件契约 | `PortexEvent` + `EventType` 六类最小集 | 已确认 | M0.4 映射与测试已完成 |
| 工具 PoC | `read_file` function_tool | 已确认 | M0.3 注册/调用闭环验证通过 |

## M1 前置结论

- 进入 M1 时无需再进行框架级选型讨论。
- M1 直接聚焦于：
  1. FastAPI 应用骨架
  2. SQLite 核心模型与仓储
  3. 基础路由与鉴权
  4. WebSocket 流式消息转发

