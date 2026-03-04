# Portex 项目规划文档

**项目名称**: Portex
**文档版本**: 1.1
**创建日期**: 2026-03-04
**最近更新**: 2026-03-04
**项目类型**: 基于 OpenAI Agents SDK 的远程 AI Agent 服务

---

## 0. 进度快照 (M0 完成)

- M0.1 环境搭建：已完成（Python 3.11、`pyproject.toml`、`.venv`）
- M0.2 流式 PoC：已完成（`pocs/streaming/` + 事件类型记录）
- M0.3 工具 PoC：已完成（`read_file` 工具定义/注册/调用验证）
- M0.4 契约与映射：已完成（`portex/contracts/events.py` + `pocs/events/mapper.py` + 测试）
- M1 准备状态：可以进入 FastAPI + SQLite 核心骨架搭建

---

## 1. 项目概述

### 1.1 项目定位

Portex 是一个基于 **OpenAI Agents SDK（Python）** 构建的自托管多用户远程 AI Agent 平台，旨在将 Codex CLI 的能力通过 Web 界面和容器隔离技术提供给多用户使用。

Portex 是 HappyClaw 的 Python 重写版：
- **HappyClaw**：基于 Claude Agent SDK（Node.js）+ Claude Code CLI
- **Portex**：基于 OpenAI Agents SDK（Python）+ Codex CLI

### 1.2 核心设计原则

> **不重新实现 Agent 能力，直接复用 Codex CLI。**

这意味着 Codex 的每一次升级——新工具、更强的推理、更多的 MCP 支持——Portex 零适配自动受益。

### 1.3 目标用户

1. 希望自托管 AI 编程助手的技术团队
2. 希望在企业内部提供共享 AI Agent 能力的组织
3. 希望让 AI Agent 能力触达更多场景（Web、移动端、IM 群组）的个人开发者

---

## 2. 技术架构

### 2.1 整体架构

Portex 由三个独立的 Python/TypeScript 项目组成：

| 项目 | 目录 | 职责 |
|------|------|------|
| 主服务 | `/` | FastAPI Web 服务器、消息处理、IPC 监听、容器生命周期管理 |
| Web 前端 | `web/` | React 19 + Vite SPA，Tailwind CSS，PWA |
| Agent Runner | `container/agent-runner/` | OpenAI Agents SDK 执行引擎，MCP 工具 |

```
Client Layer
  Web UI / Feishu / Telegram
        |
Gateway Layer
  FastAPI REST + WebSocket
        |
Orchestration Layer
  GroupQueue + Scheduler + Session Router + IPC Watcher
        |
Runtime Layer
  AgentRuntimeAdapter
   |- OpenAIAgentsRuntime (主路径)
   |- DirectCodexRuntime (兜底/迁移路径)
        |
Execution Layer
  Host Process (admin only) / Docker Container (default)
        |
Storage Layer
  SQLite + Filesystem (ipc/sessions/memory/skills/config)
```

### 2.2 技术栈选型

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| Web 框架 | FastAPI | 高性能异步 Python 框架，原生支持 OpenAI Agents SDK |
| 数据库 | SQLite (WAL 模式) | 轻量级，无需额外依赖，与 HappyClaw 保持一致 |
| ORM | SQLAlchemy 2.0 | Python 生态最成熟的 ORM |
| WebSocket | FastAPI 原生 WebSocket | 支持流式事件推送 |
| 容器管理 | Docker SDK for Python | 与 HappyClaw 相同的 Docker 隔离方案 |
| 前端框架 | React 19 + Vite 6 | 与 HappyClaw Web 保持一致 |
| 状态管理 | Zustand | 轻量级 React 状态管理 |
| UI 组件 | Radix UI + Tailwind CSS | 与 HappyClaw 保持一致 |

### 2.3 IPC 通信机制

与 HappyClaw 类似，采用基于文件系统的 IPC 通信：

1. **主进程 → Agent Runner**：通过文件 IPC 注入消息
   - 路径：`data/ipc/{folder}/input/`
   - 格式：JSON 文件（原子写入：先写 `.tmp` 再 `rename`）

2. **Agent Runner → 主进程**：通过文件 IPC 回传结果
   - 路径：`data/ipc/{folder}/messages/`, `data/ipc/{folder}/tasks/`
   - 读取后立即删除

3. **流式输出**：通过 stdout 的哨兵标记分隔事件
   - 格式：`---PORTEX_OUTPUT_START---` / `---PORTEX_OUTPUT_END---`

### 2.4 目录结构

```
portex/
├── app/                      # FastAPI 应用入口
│   ├── __init__.py
│   ├── main.py              # ASGI 应用
│   ├── routes/              # API 路由
│   ├── middleware/          # 中间件
│   └── websocket.py        # WebSocket 处理
├── domain/                  # 核心业务模型
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas.py           # Pydantic 请求/响应模型
│   └── exceptions.py        # 业务异常
├── infra/                   # 基础设施层
│   ├── db/                  # 数据库操作
│   ├── runtime/            # Agent 运行时适配器
│   ├── exec/                # 容器/进程执行器
│   └── im/                  # IM 通道（飞书/Telegram）
├── services/                # 业务服务
│   ├── auth.py              # 认证服务
│   ├── group_queue.py       # 并发调度
│   ├── scheduler.py         # 定时任务
│   ├── memory.py            # 记忆系统
│   └── skills.py            # Skills 管理
├── container/               # 容器相关
│   ├── agent-runner/        # Agent Runner (Python)
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── runner.py    # 主入口
│   │   │   ├── event_mapper.py
│   │   │   ├── tools/       # 平台工具
│   │   │   └── ipc/        # IPC 处理
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── skills/              # 项目级 Skills
├── web/                     # React 前端
│   ├── src/
│   │   ├── api/             # API 客户端
│   │   ├── components/      # UI 组件
│   │   ├── hooks/           # React Hooks
│   │   ├── stores/          # Zustand 状态
│   │   └── pages/           # 页面组件
│   ├── package.json
│   └── vite.config.ts
├── data/                    # 数据目录（运行时生成）
│   ├── db/                  # SQLite 数据库
│   ├── sessions/            # 用户会话
│   ├── memory/              # 记忆文件
│   ├── ipc/                 # IPC 文件
│   ├── skills/              # 用户级 Skills
│   └── env/                 # 环境变量文件
├── config/                  # 配置文件
├── scripts/                 # 运维脚本
├── Makefile
├── pyproject.toml
└── README.md
```

---

## 3. 核心功能

### 3.1 Agent 执行引擎

#### 3.1.1 两种执行模式

| 模式 | 说明 | 适用用户 |
|------|------|----------|
| **宿主机模式** | Agent 直接在服务器上运行，访问本地文件系统 | admin 用户（可选） |
| **容器模式** | Docker 隔离执行，非 root 用户 | member 用户（默认） |

#### 3.1.2 容器配置

容器基于 `python:3.11-slim`，预装常用工具：
- Python 3.11 + pip
- Git、curl、wget
- Chromium（浏览器自动化）
- ffmpeg（多媒体处理）
- ImageMagick（图像处理）
- 数据库客户端（PostgreSQL、MySQL、MongoDB）

#### 3.1.3 卷挂载

| 宿主机路径 | 容器路径 | 说明 |
|-----------|----------|------|
| `data/sessions/{group}/.claude` | `/home/portex/.claude` | 用户会话配置 |
| `data/memory/{group}` | `/workspace/memory` | 记忆文件 |
| `data/ipc/{group}` | `/workspace/ipc` | IPC 通信目录 |
| `data/skills/{userId}` | `/workspace/user-skills` | 用户级 Skills |
| `container/skills` | `/workspace/project-skills` | 项目级 Skills |
| `{group}/` | `/workspace/group` | 用户工作区 |

### 3.2 实时流式输出

通过 OpenAI Agents SDK 的 `Runner.run_streamed()` 实现实时流式输出：

```python
from agents import Agent, Runner

result = Runner.run_streamed(agent, input="请写一个程序")
async for event in result.stream_events():
    if event.type == "run_item_stream_event":
        # 处理流式事件
        pass
```

**事件类型**：
- `run.started`：运行开始
- `run.token.delta`：Token 增量输出
- `run.tool.started`：工具调用开始
- `run.tool.completed`：工具调用完成
- `run.agent.switched`：Agent 切换
- `run.guardrail.hit`：Guardrail 触发
- `run.completed`：运行完成
- `run.failed`：运行失败

### 3.3 MCP 工具

Portex 内置以下 MCP 工具（在 Agent Runner 中实现）：

| 工具 | 说明 |
|------|------|
| `send_message` | 运行期间即时发送消息给用户/群组 |
| `schedule_task` | 创建定时/周期/一次性任务 |
| `list_tasks` / `pause_task` / `resume_task` / `cancel_task` | 任务生命周期管理 |
| `register_group` | 注册新群组 |
| `memory_append` | 追加时效性记忆 |
| `memory_search` / `memory_get` | 全文检索和读取记忆 |

### 3.4 记忆系统

| 记忆类型 | 路径 | 说明 |
|---------|------|------|
| 用户全局记忆 | `CLAUDE.md` | 每个用户独立，所有会话共享 |
| 会话记忆 | `{session}/CLAUDE.md` | 每个会话私有 |
| 日期记忆 | `memory/YYYY-MM-DD.md` | 适合存储时效性信息 |
| 对话归档 | `memory/archives/` | 上下文压缩前自动归档 |

### 3.5 多用户隔离

| 隔离维度 | 实现方式 |
|---------|----------|
| 执行环境 | 每用户独立工作区 `home-{userId}` |
| IM 通道 | per-user 飞书/Telegram 连接池 |
| 权限控制 | RBAC：owner / admin / member |
| 注册管理 | 开放注册 / 邀请码 / 关闭注册 |
| 配置安全 | API Key 加密存储 |
| 审计追踪 | 完整事件日志 |

### 3.6 IM 接入

| 渠道 | 连接方式 | 消息格式 | 特色 |
|------|----------|----------|------|
| **飞书** | WebSocket 长连接 | 富文本卡片 | 图片消息、Reaction 反馈 |
| **Telegram** | Bot API Long Polling | Markdown → HTML | 长消息自动分片 |
| **Web** | WebSocket 实时通信 | 流式 Markdown | 图片粘贴/拖拽上传 |

---

## 4. OpenAI Agents SDK 集成

### 4.1 Agent 定义

```python
from agents import Agent, function_tool

agent = Agent(
    name="CodexAssistant",
    instructions="你是一个专业的 AI 编程助手...",
    tools=[
        send_message,
        schedule_task,
        memory_search,
        # ... 更多工具
    ],
    model="gpt-4o",
)
```

### 4.2 工具注册

```python
from typing import TypedDict
from agents import function_tool, RunContextWrapper
from pydantic import Field

class Location(TypedDict):
    lat: float
    long: float

@function_tool
async def fetch_weather(location: Location) -> str:
    """获取指定位置的天气"""
    return "sunny"

@function_tool(name_override="custom_tool_name")
def read_file(ctx: RunContextWrapper[Any], path: str) -> str:
    """读取文件内容"""
    return "<file contents>"
```

### 4.3 流式输出处理

```python
result = Runner.run_streamed(agent, input="请写一个程序")
async for event in result.stream_events():
    if event.type == "run_item_stream_event":
        if event.item.type == "tool_call_item":
            print(f"-- Tool called: {event.item.name}")
        elif event.item.type == "message_output_item":
            print(f"-- Message: {event.item.content}")
```

---

## 5. 数据模型

### 5.1 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    status TEXT NOT NULL DEFAULT 'active',
    permissions TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 会话表
CREATE TABLE sessions (
    group_folder TEXT NOT NULL,
    session_id TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (group_folder, agent_id)
);

-- 消息表
CREATE TABLE messages (
    id TEXT,
    chat_jid TEXT,
    sender TEXT,
    content TEXT,
    timestamp TEXT,
    is_from_me INTEGER,
    attachments TEXT,
    PRIMARY KEY (id, chat_jid)
);

-- 定时任务表
CREATE TABLE scheduled_tasks (
    id TEXT PRIMARY KEY,
    group_folder TEXT NOT NULL,
    chat_jid TEXT NOT NULL,
    prompt TEXT NOT NULL,
    schedule_type TEXT NOT NULL,
    schedule_value TEXT NOT NULL,
    next_run TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
);

-- 群组表
CREATE TABLE registered_groups (
    jid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    folder TEXT NOT NULL,
    added_at TEXT NOT NULL,
    container_config TEXT,
    created_by TEXT
);
```

---

## 6. 实施计划

### 6.1 里程碑

| 里程碑 | 目标 | 周期 |
|--------|------|------|
| M0 预研封板 | 集成路径与契约定稿 | 1 周 |
| M1 核心骨架 | 后端框架与基础表可用 | 2 周 |
| M2 运行链路 | Web -> Runtime -> WS 流式 | 2 周 |
| M3 容器隔离 | container/host 双模式 | 2 周 |
| M4 多用户与任务 | RBAC、scheduler、memory | 2 周 |
| M5 IM 接入 | 飞书/Telegram 通道 | 1 周 |
| M6 发布 | v1 发布准备 | 1 周 |

### 6.2 v1 必须交付

1. ✅ 单机部署可用（Docker + SQLite + FastAPI + React）
2. ✅ 多用户登录与会话隔离（RBAC + 审计）
3. ✅ 基础聊天链路（Web -> Agent -> 流式回传）
4. ✅ 容器模式稳定（启动、超时、关闭、重试）
5. ✅ 6 个 MCP/平台工具
6. ✅ 定时任务（cron / interval / once）
7. ✅ 飞书或 Telegram 至少打通其一

---

## 7. 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| SDK 版本变更导致事件破坏 | 事件映射层 + 契约测试 |
| Codex CLI 接入权限面过大 | 工具白名单 + 容器隔离 + 审计 |
| 多通道路由串扰 | 严格 `group_folder + owner` 绑定策略 |
| 消息丢失/重复 | cursor 提交语义 + 幂等键 |
| 宿主机模式安全边界薄弱 | 默认关闭，admin 显式启用 |

---

## 8. 参考资料

1. [HappyClaw GitHub](https://github.com/riba2534/happyclaw)
2. [OpenAI Agents SDK 文档](https://openai.github.io/openai-agents-python/)
3. [OpenAI Agents SDK (中文)](https://openai-agents-sdk.doczh.com/)
4. [FastAPI 文档](https://fastapi.tiangolo.com/)
5. [React 文档](https://react.dev/)
6. [Codex CLI 文档](https://docs.anthropic.com/en/docs/claude-code)

---

*本文档将作为 Portex 项目的规划基线，与项目任务清单绑定执行。*
