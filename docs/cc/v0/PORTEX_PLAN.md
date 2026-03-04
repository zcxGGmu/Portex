# Portex 项目规划文档

**项目名称**: Portex
**项目类型**: 基于 Codex CLI 的远程 AI Agent 服务
**技术栈**: Python (FastAPI) + React + Docker
**版本**: v1.0.0
**创建日期**: 2026-03-03

---

## 1. 项目概述

### 1.1 项目背景

Portex 是一个自托管多用户 AI Agent 系统，旨在将 Codex CLI 的强大能力从终端解放出来，使其可以通过 Web 界面、移动端 PWA 以及即时通讯工具（飞书/Telegram）访问。

本项目基于 HappyClaw 设计思路进行 Python 重写，利用 Python 生态的成熟工具（FastAPI、SQLAlchemy、asyncio）提供更现代化的实现。

### 1.2 核心特性

| 特性 | 描述 |
|------|------|
| **多端接入** | Web (PWA)、飞书、Telegram 三端消息接入 |
| **容器隔离** | Docker 容器隔离执行，支持 40+ 预装工具 |
| **实时流式** | Agent 思考过程、工具调用实时推送 |
| **多用户隔离** | RBAC 权限体系，独立工作区 |
| **持久记忆** | 用户全局记忆、会话记忆、日期记忆 |
| **MCP 工具** | 10 个内置 MCP 工具（消息、任务、记忆等） |
| **定时任务** | Cron/Interval/一次性任务调度 |
| **Web Terminal** | 浏览器内完整终端 |

### 1.3 设计原则

> **不重新实现 Agent 能力，直接复用 Codex CLI。**

这意味着 Codex CLI 的每一次升级——新工具、更强的推理、更多的 MCP 支持——Portex 零适配自动受益。

---

## 2. 需求分析

### 2.1 功能需求

#### 2.1.1 消息接入

| 渠道 | 接入方式 | 消息格式 | 特色功能 |
|------|---------|---------|---------|
| Web | WebSocket | 流式 Markdown | 图片拖拽、虚拟滚动 |
| 飞书 | WebSocket 长连接 | 富文本卡片 | 图片消息、Reaction 反馈 |
| Telegram | Bot API Long Polling | Markdown → HTML | 长消息分片（3800 字符） |

#### 2.1.2 Agent 执行引擎

基于 **OpenAI Agents SDK** 构建：

- **框架**: OpenAI Agents SDK (Python)
- **宿主机模式**: Agent 直接在服务器运行，admin 用户默认使用
- **容器模式**: Docker 隔离执行，member 用户默认使用
- **并发控制**: 最多 20 容器 + 5 宿主机进程同时运行
- **重试机制**: 指数退避（5s → 80s，最多 5 次）
- **内置工具**: ShellTool, FileSearchTool, WebSearchTool, CodeInterpreterTool
- **多智能体**: 通过 Handoffs 实现多智能体协作
- **安全护栏**: Input/Output Guardrails 验证

#### 2.1.3 实时流式事件（11 种）

- 思考过程（thinking_delta）
- 工具调用追踪（tool_use_start/end/progress）
- Hook 执行状态（hook_started/progress/response）
- 任务通知（task_start/notification）

#### 2.1.4 MCP 内置工具（10 个）

| 工具 | 功能 |
|------|------|
| `send_message` | 运行期间即时发送消息 |
| `schedule_task` | 创建定时/周期/一次性任务 |
| `list_tasks` / `pause/resume/cancel_task` | 任务生命周期管理 |
| `register_group` | 注册新群组（仅 admin） |
| `memory_append` / `memory_search` / `memory_get` | 记忆管理 |

#### 2.1.5 记忆系统

- **用户全局记忆**: `CLAUDE.md`，所有会话共享
- **会话记忆**: 每个会话私有的 `CLAUDE.md`
- **日期记忆**: `memory/YYYY-MM-DD.md`
- **对话归档**: 上下文压缩前自动归档

#### 2.1.6 权限控制

- **RBAC**: 5 种权限 × 4 种角色模板
- **注册管理**: 开放注册 / 邀请码 / 关闭注册
- **审计日志**: 18 种事件类型

### 2.2 非功能需求

| 需求 | 指标 |
|------|------|
| **可用性** | 7×24 小时运行，优雅关闭 |
| **性能** | 消息延迟 < 100ms，流式推送延迟 < 50ms |
| **并发** | 支持 20 容器 + 5 进程并发 |
| **安全** | API Key AES-256-GCM 加密，路径遍历防护 |
| **可维护性** | 模块化架构，完善日志，配置驱动 |

---

## 3. 技术架构

### 3.1 整体架构图

```
                           ┌─────────────────────────────────────────────────────┐
                           │                     Portex                          │
                           │              (FastAPI + SQLite)                     │
                           └──────────────────────┬──────────────────────────────┘
                                                    │
    ┌───────────────────────┬──────────────────────┼───────────────────────┐
    │                       │                      │                       │
    ▼                       ▼                      ▼                       ▼
┌─────────┐           ┌─────────┐           ┌─────────┐           ┌─────────┐
│  飞书    │           │Telegram │           │  Web    │           │ WebSocket│
│WebSocket │           │Bot API  │           │  PWA    │           │  推送   │
└────┬────┘           └────┬────┘           └────┬────┘           └────┬────┘
     │                    │                      │                      │
     └────────────────────┼──────────────────────┘                      │
                          │                                             │
                          ▼                                             │
                  ┌────────────────┐                                    │
                  │   消息队列      │◄───────────────────────────────────┘
                  │  (GroupQueue)  │
                  └────────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
     ┌──────────┐    ┌──────────┐    ┌──────────┐
     │ 认证模块  │    │ 容器管理  │    │ 定时任务  │
     └────┬─────┘    └────┬─────┘    │ Scheduler│
          │               │          └────┬─────┘
          ▼               ▼               │
    ┌──────────┐    ┌──────────┐          │
    │ SQLite   │    │ Docker   │◄─────────┘
    │  (WAL)   │    │ 容器集群  │
    └──────────┘    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ 用户工作区 │   │ 会话工作区 │   │ MCP工具  │
    │ CLAUDE.md│   │ CLAUDE.md│   │ 10个内置 │
    └──────────┘   └──────────┘   └──────────┘
```

### 3.2 技术栈

| 层次 | 技术 | 版本 |
|------|------|------|
| **后端 Web** | FastAPI | >= 0.115 |
| **ASGI 服务器** | Uvicorn | >= 0.27 |
| **数据库** | SQLite (aiosqlite) + SQLAlchemy | 2.0+ |
| **异步运行时** | asyncio | 标准库 |
| **WebSocket** | FastAPI 内置 + websockets | >= 14.0 |
| **Docker SDK** | docker (官方) | >= 7.0 |
| **任务调度** | APScheduler | >= 3.10 |
| **数据验证** | Pydantic | >= 2.6 |
| **HTTP 客户端** | httpx | >= 0.27 |
| **加密** | cryptography | >= 41.0 |
| **日志** | structlog | >= 24.0 |
| **飞书 SDK** | feishu-sdk-python | >= 2.0 |
| **Telegram Bot** | python-telegram-bot | >= 21.0 |
| **AI Agent 框架** | OpenAI Agents SDK | >= 0.10 |

| 层次 | 技术 | 版本 |
|------|------|------|
| **前端框架** | React | 19.x |
| **构建工具** | Vite | 6.x |
| **语言** | TypeScript | 5.x |
| **样式** | Tailwind CSS | 3.x |
| **状态管理** | Zustand | 5.x |
| **HTTP 客户端** | Axios | - |
| **Markdown** | react-markdown | - |
| **终端** | xterm.js | - |
| **PWA** | vite-plugin-pwa | - |

### 3.3 目录结构

```
portex/
├── portex/                          # 主包
│   ├── __init__.py
│   ├── main.py                      # 应用入口
│   ├── config.py                    # 配置管理
│   ├── constants.py                 # 常量定义
│   │
│   ├── api/                         # API 层
│   │   ├── router.py                # 主路由
│   │   ├── auth.py                  # 认证接口
│   │   ├── chat.py                  # 聊天接口
│   │   ├── session.py               # 会话管理
│   │   ├── container.py             # 容器管理
│   │   ├── task.py                  # 任务调度
│   │   ├── ws.py                    # WebSocket 端点
│   │   └── admin.py                 # 管理接口
│   │
│   ├── core/                        # 核心业务逻辑
│   │   ├── agent.py                 # Agent 执行引擎
│   │   ├── container.py             # Docker 容器管理
│   │   ├── queue.py                 # 并发调度器
│   │   ├── mcp.py                   # MCP Server 实现
│   │   ├── memory.py                # 记忆系统
│   │   ├── scheduler.py             # 定时任务调度器
│   │   ├── ipc.py                   # 文件 IPC 通信
│   │   └── security.py              # 安全检查
│   │
│   ├── adapters/                    # 外部适配器
│   │   ├── base.py                  # 适配器基类
│   │   ├── feishu.py                # 飞书适配器
│   │   ├── telegram.py              # Telegram 适配器
│   │   └── registry.py              # 适配器注册表
│   │
│   ├── models/                      # 数据模型
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── message.py
│   │   └── task.py
│   │
│   ├── database/                    # 数据库层
│   │   ├── connection.py            # 数据库连接
│   │   ├── repositories/           # 仓储模式
│   │   │   ├── user_repo.py
│   │   │   ├── session_repo.py
│   │   │   └── message_repo.py
│   │   └── migrations/              # 迁移脚本
│   │
│   ├── services/                   # 服务层
│   │   ├── auth_service.py
│   │   ├── chat_service.py
│   │   ├── session_service.py
│   │   └── notification_service.py
│   │
│   ├── schemas/                     # Pydantic 模型
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── session.py
│   │   └── common.py
│   │
│   ├── utils/                       # 工具函数
│   │   ├── logger.py
│   │   ├── crypto.py               # AES-256-GCM
│   │   └── file_utils.py
│   │
│   └── middleware/                  # 中间件
│       ├── auth.py
│       └── rate_limit.py
│
├── web/                            # 前端 (React + Vite)
│   ├── src/
│   │   ├── api/                    # API 客户端
│   │   ├── components/              # 组件
│   │   ├── hooks/                  # 自定义 Hooks
│   │   ├── pages/                  # 页面
│   │   ├── stores/                 # 状态管理
│   │   └── types/                  # 类型定义
│   ├── package.json
│   └── vite.config.ts
│
├── container/                       # 容器镜像
│   ├── Dockerfile                   # 镜像定义
│   ├── agent-runner/               # Agent Runner (Python)
│   │   ├── main.py
│   │   ├── executor.py
│   │   └── mcp_client.py
│   ├── build.sh
│   └── skills/                     # Skills 目录
│
├── data/                            # 运行时数据
│   ├── db/
│   ├── ipc/
│   │   └── {session_id}/
│   │       ├── input/
│   │       ├── messages/
│   │       └── tasks/
│   ├── memory/
│   └── workspaces/
│
├── tests/                           # 测试
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── pyproject.toml
├── Makefile
└── README.md
```

---

## 4. 模块设计

### 4.1 API 模块 (`portex/api/`)

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/auth/*` | POST | 登录/注册/登出/密码修改 |
| `/api/chat/*` | GET/POST | 消息发送/历史查询 |
| `/api/sessions/*` | GET/POST/DELETE | 会话 CRUD |
| `/api/containers/*` | GET/POST | 容器状态/管理 |
| `/api/tasks/*` | GET/POST/PUT/DELETE | 定时任务 CRUD |
| `/api/memory/*` | GET/POST | 记忆读写与搜索 |
| `/api/mcp-tools/*` | GET | MCP 工具列表 |
| `/api/admin/*` | GET/POST/PUT | 用户管理/邀请码 |
| `/api/status` | GET | 系统状态/健康检查 |
| `/ws` | WebSocket | 实时消息推送 |

### 4.2 核心模块 (`portex/core/`)

#### 4.2.1 Agent 执行引擎 (`agent.py`)

基于 OpenAI Agents SDK 构建：

```python
from agents import Agent, Runner, function_tool, handoff, SQLiteSession

# 定义自定义工具
@function_tool
def send_message(user_id: str, message: str) -> str:
    """Send a message to user."""
    return "Message sent"

# 创建 Agent
agent = Agent(
    name="Portex Agent",
    instructions="You are a helpful AI assistant.",
    tools=[send_message],
    handoffs=[],
    input_guardrails=[],
    output_guardrails=[],
)

# 使用 SQLite 持久化会话
session = SQLiteSession(
    session_id="session-123",
    db_path="./data/sessions.db"
)

# 执行
result = await Runner.run(agent, "Hello!", session=session)
print(result.final_output)

# 流式执行
result = await Runner.run_streamed(agent, "Hello!")
async for event in result.stream_events():
    print(event)
```

**核心特性**：
- `@function_tool` 装饰器创建自定义工具
- `@handoff` 实现多智能体协作
- `@input_guardrail` / `@output_guardrail` 安全验证
- `Runner.run()` / `Runner.run_streamed()` 执行
- `SQLiteSession` 会话持久化

#### 4.2.2 容器管理 (`container.py`)

```python
class ContainerManager:
    """Docker 容器生命周期管理"""

    async def create_workspace(self, user_id: str) -> Path:
        """创建用户工作区"""

    async def start_container(
        self,
        session_id: str,
        user_id: str,
        mode: ExecutionMode
    ) -> str:
        """启动容器/进程"""

    async def stop_container(self, session_id: str):
        """停止容器"""

    async def get_container_status(self, session_id: str) -> ContainerStatus:
        """获取容器状态"""

    async def exec_terminal(
        self,
        session_id: str,
        command: str
    ) -> AsyncIterator[str]:
        """执行终端命令"""
```

#### 4.2.3 并发调度器 (`queue.py`)

```python
class GroupQueue:
    """会话级队列调度"""

    MAX_CONTAINERS = 20
    MAX_HOST_PROCESSES = 5

    async def enqueue_message(
        self,
        session_id: str,
        message: dict
入    ):
        """队消息"""

    async def start_session(
        self,
        session_id: str,
        mode: ExecutionMode
    ) -> bool:
        """启动会话"""

    async def send_message(
        self,
        session_id: str,
        message: dict
    ):
        """发送消息到运行中的会话"""

    async def close_session(self, session_id: str):
        """关闭会话"""
```

#### 4.2.4 文件 IPC (`ipc.py`)

```python
class FileIPC:
    """基于文件系统的 IPC 通信"""

    IPC_MARKER_START = "---PORTEX_OUTPUT_START---"
    IPC_MARKER_END = "---PORTEX_OUTPUT_END---"

    async def write_input(self, session_id: str, data: dict):
        """写入输入消息"""

    async def watch_input(self, session_id: str) -> AsyncIterator[dict]:
        """监视输入目录"""

    async def write_message(self, session_id: str, data: dict):
        """写入输出消息"""

    async def watch_messages(self, session_id: str) -> AsyncIterator[dict]:
        """监视消息目录"""
```

#### 4.2.5 MCP Server (`mcp.py`)

使用 OpenAI Agents SDK 内置的 MCP 支持：

```python
from agents import Agent
from agents.mcp import MCPServerStdio, MCPServerSse

# STDIO 模式（本地进程）
mcp_stdio = MCPServerStdio(
    params=MCPServerStdioParams(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "./data"],
    )
)

# SSE 模式（远程服务器）
mcp_sse = MCPServerSse(
    params=MCPServerSseParams(
        url="http://localhost:3000/sse",
    )
)

# 在 Agent 中使用
agent = Agent(
    name="Portex Agent",
    instructions="You are a helpful AI assistant.",
    mcp_servers=[mcp_stdio, mcp_sse],
)
```

**MCP 服务器类型**：
- `MCPServerStdio`: STDIO 协议（本地进程）
- `MCPServerSse`: Server-Sent Events
- `MCPServerStreamableHttp`: HTTP 流式

### 4.3 IM 适配器 (`portex/adapters/`)

```python
class IMAdapter(ABC):
    """IM 适配器基类"""

    @abstractmethod
    async def connect(self):
        """建立连接"""

    @abstractmethod
    async def disconnect(self):
        """断开连接"""

    @abstractmethod
    async def send_message(self, chat_id: str, message: Message):
        """发送消息"""

    @abstractmethod
    async def on_message(self, handler: Callable[[Message], Awaitable]):
        """消息回调"""
```

### 4.4 数据模型

#### 4.4.1 用户表 (`users`)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| username | VARCHAR(50) | 用户名（唯一） |
| password_hash | VARCHAR(255) | bcrypt 哈希 |
| role | ENUM | admin/member |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| is_active | BOOLEAN | 是否激活 |

#### 4.4.2 会话表 (`sessions`)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| folder | VARCHAR(100) | 会话目录名 |
| name | VARCHAR(255) | 会话名称 |
| user_id | UUID | 所属用户 |
| execution_mode | ENUM | host/container |
| status | ENUM | idle/running/paused |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 4.4.3 消息表 (`messages`)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| session_id | UUID | 所属会话 |
| role | ENUM | user/assistant |
| content | TEXT | 消息内容 |
| channel | ENUM | web/feishu/telegram |
| created_at | DATETIME | 创建时间 |

#### 4.4.4 定时任务表 (`scheduled_tasks`)

| 字段 |类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| session_id | UUID | 关联会话 |
| user_id | UUID | 所属用户 |
| trigger_type | ENUM | cron/interval/once |
| cron_expr | VARCHAR(100) | Cron 表达式 |
| interval_seconds | INTEGER | 间隔秒数 |
| run_date | DATETIME | 一次性执行时间 |
| command | TEXT | 执行命令 |
| status | ENUM | active/paused/completed |
| created_at | DATETIME | 创建时间 |

---

## 5. API 设计

### 5.1 认证接口

| 路径 | 方法 | 描述 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/logout` | POST | 用户登出 |
| `/api/auth/me` | GET | 获取当前用户 |
| `/api/auth/password` | PUT | 修改密码 |

### 5.2 聊天接口

| 路径 | 方法 | 描述 |
|------|------|------|
| `/api/chat/sessions` | GET | 获取会话列表 |
| `/api/chat/sessions` | POST | 创建会话 |
| `/api/chat/sessions/{id}` | GET | 获取会话详情 |
| `/api/chat/sessions/{id}/messages` | GET | 获取消息历史 |
| `/api/chat/sessions/{id}/send` | POST | 发送消息 |
| `/api/chat/sessions/{id}/close` | POST | 关闭会话 |

### 5.3 管理接口

| 路径 | 方法 | 描述 |
|------|------|------|
| `/api/admin/users` | GET | 用户列表 |
| `/api/admin/users` | POST | 创建用户 |
| `/api/admin/users/{id}` | PUT | 更新用户 |
| `/api/admin/users/{id}` | DELETE | 删除用户 |
| `/api/admin/invite-codes` | GET | 邀请码列表 |
| `/api/admin/invite-codes` | POST | 创建邀请码 |
| `/api/admin/audit-logs` | GET | 审计日志 |

### 5.4 WebSocket 协议

#### 5.4.1 服务端 → 客户端

| 事件 | 数据 | 描述 |
|------|------|------|
| `new_message` | Message | 新消息通知 |
| `agent_reply` | Message | Agent 回复 |
| `stream_event` | StreamEvent | 流式事件 |
| `agent_status` | Status | Agent 状态变更 |
| `typing` | None | 正在输入 |
| `terminal_data` | string | 终端数据 |

#### 5.4.2 客户端 → 服务端

| 事件 | 数据 | 描述 |
|------|------|------|
| `send_message` | {session_id, content} | 发送消息 |
| `terminal_start` | {session_id} | 启动终端 |
| `terminal_input` | {session_id, data} | 终端输入 |
| `terminal_resize` | {session_id, cols, rows} | 终端调整 |
| `terminal_stop` | {session_id} | 停止终端 |

---

## 6. 容器隔离设计

### 6.1 容器镜像

基于 `node:22-slim`，预装 Codex CLI 及常用工具：

| 类别 | 工具 |
|------|------|
| **运行时** | Node.js 22, Python 3, Go |
| **Agent** | Codex CLI (npm install -g @opencode-ai/codex) |
| **浏览器** | Chromium (Playwright) |
| **开发工具** | git, curl, wget, vim, nano |
| **媒体处理** | ffmpeg, imagemagick |
| **数据库** | sqlite3, postgresql-client |
| **网络** | openssh-client, netcat |
| **实用工具** | tar, gzip, unzip, jq, yq |
| **本地模型** | Ollama (可选，用于 --oss 模式) |

### 6.2 容器挂载策略

| 资源 | 容器路径 | admin 容器 | member 容器 |
|------|---------|----------|------------|
| 工作目录 | `/workspace` | 读写 | 读写（仅自己） |
| 用户全局记忆 | `/workspace/global` | 读写 | 读写（仅自己） |
| IPC 通道 | `/workspace/ipc` | 读写 | 读写（仅自己） |
| Skills | `/skills` | 只读 | 只读 |

### 6.3 容器生命周期

```
1. 用户发送消息
   ↓
2. GroupQueue 判断:
   - 空闲 → 启动容器
   - 运行中 → IPC 注入
   - 满载 → 排队等待
   ↓
3. 启动容器:
   - 创建工作区 (home-{userId})
   - 挂载 volumes
   - 设置环境变量
   - 启动 Agent Runner
   ↓
4. 执行消息:
   - 写入 IPC input/
   - 监视 IPC messages/
   - 解析 stdout 流式事件
   - WebSocket 推送
   ↓
5. 关闭容器:
   - 写入 _close sentinel
   - docker stop (10s)
   - docker kill (5s)
   - 清理资源
```

---

## 7. 安全设计

### 7.1 认证与授权

- **密码哈希**: bcrypt 12 轮
- **会话**: 30 天有效期，HMAC 签名 Cookie
- **登录限流**: 5 次失败后锁定 15 分钟

### 7.2 数据加密

- **API Key**: AES-256-GCM 加密存储
- **会话密钥**: 持久化到独立文件（0600 权限）

### 7.3 文件安全

- **路径遍历防护**: realpath 校验
- **敏感路径黑名单**: `.ssh`, `.gnupg`, `.aws` 等
- **系统路径保护**: `logs/`, `CLAUDE.md`, `.claude/` 等

### 7.4 Agent 安全（Guardrails）

使用 OpenAI Agents SDK 内置的 Guardrails：

```python
from agents import input_guardrail, output_guardrail

@input_guardrail
def check_sensitive_input(context, agent) -> dict:
    """验证用户输入不包含敏感信息"""
    text = context.messages[-1].content
    # 实现检查逻辑
    return {"is_safe": True}

@output_guardrail
def check_output_safety(context, agent, output: str) -> None:
    """验证 Agent 输出安全"""
    # 实现检查逻辑
    pass

agent = Agent(
    name="Portex Agent",
    instructions="You are a helpful assistant.",
    input_guardrails=[check_sensitive_input],
    output_guardrails=[check_output_safety],
)
```

### 7.5 审计日志

18 种事件类型：
- 认证: `login_success`, `login_failed`, `logout`, `password_changed`
- 用户: `user_created`, `user_updated`, `user_deleted`
- 会话: `session_created`, `session_closed`
- 文件: `file_uploaded`, `file_downloaded`, `file_deleted`

---

## 8. 实施计划

### Phase 1: 基础设施（2 周）

| 任务 | 描述 |
|------|------|
| P1 | 项目骨架搭建 (FastAPI + React) |
| P1 | 数据库模型定义与迁移 |
| P1 | 用户认证系统 |
| P2 | 基础配置管理 |

### Phase 2: 核心功能（3 周）

| 任务 | 描述 |
|------|------|
| P1 | 会话管理 |
| P1 | Agent 执行引擎 |
| P1 | WebSocket 实时通信 |
| P1 | 消息处理流程 |
| P2 | 文件 IPC 通信 |

### Phase 3: 容器隔离（2 周）

| 任务 | 描述 |
|------|------|
| P1 | Docker 容器管理 |
| P1 | 容器镜像构建 |
| P1 | 并发调度器 |
| P2 | Web Terminal |

### Phase 4: IM 集成（2 周）

| 任务 | 描述 |
|------|------|
| P1 | 飞书适配器 |
| P1 | Telegram 适配器 |
| P2 | IM 连接池管理 |

### Phase 5: 高级功能（2 周）

| 任务 | 描述 |
|------|------|
| P1 | MCP 工具实现 |
| P1 | 记忆系统 |
| P2 | 定时任务调度 |
| P2 | RBAC 权限系统 |

### Phase 6: 前端完善（2 周）

| 任务 | 描述 |
|------|------|
| P1 | 聊天界面优化 |
| P1 | PWA 支持 |
| P2 | 系统监控页面 |
| P2 | 管理后台 |

### Phase 7: 测试与部署（1 周）

| 任务 | 描述 |
|------|------|
| P1 | 单元测试 (80% 覆盖率) |
| P1 | 集成测试 |
| P2 | E2E 测试 |
| P1 | Docker Compose 部署 |

---

## 9. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Codex CLI 变更 | 高 | 紧跟官方版本，及时适配 |
| 本地模型集成 | 中 | 支持 Ollama / LM Studio 多种后端 |
| Docker 资源耗尽 | 高 | 严格限制并发数，设置资源配额 |
| 安全漏洞 | 高 | 定期安全审计，依赖更新 |
| 消息丢失 | 中 | 消息持久化 + 重试机制 |
| 容器启动失败 | 中 | 健康检查 + 自动重试 |
| 前端维护成本 | 中 | 保持技术栈简洁，减少依赖 |

---

## 10. 参考资料

- [HappyClaw GitHub](https://github.com/riba2534/happyclaw)
- [OpenCode / Codex CLI GitHub](https://github.com/opencode-ai/codex)
- [Codex CLI 官方文档](https://docs.opencode.ai)
- [OpenAI Agents SDK Python](https://github.com/openai/openai-agents-python)
- [OpenAI Agents SDK 文档](https://openai.github.io/openai-agents-python/)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [Docker SDK for Python](https://docker-py.readthedocs.io)

---

## 11. 附录

### A. 流式事件类型

| 事件 | 字段 | 描述 |
|------|------|------|
| `text_delta` | content | 文本增量 |
| `thinking_delta` | content | 思考过程增量 |
| `tool_use_start` | tool_name, input | 工具调用开始 |
| `tool_use_end` | tool_name, output | 工具调用结束 |
| `tool_progress` | tool_name, progress | 工具执行进度 |
| `hook_started` | hook_name | Hook 开始 |
| `hook_progress` | hook_name, progress | Hook 进度 |
| `hook_response` | hook_name, response | Hook 响应 |
| `task_start` | task_id | 任务开始 |
| `task_notification` | task_id, notification | 任务通知 |
| `status` | status | 状态更新 |
| `init` | config | 初始化配置 |

### B. IPC 消息格式

```json
// 输入消息 (主进程 → Agent)
{
  "type": "message",
  "content": "帮我写一个 Hello World",
  "timestamp": 1706800000
}

// 输出消息 (Agent → 主进程)
{
  "type": "reply",
  "content": "好的，我来帮你...",
  "timestamp": 1706800001
}
```

### C. 环境变量

| 变量 | 必填 | 描述 |
|------|------|------|
| `ANTHROPIC_API_KEY` | 是 | Claude API 密钥（或 OpenAI 兼容 API） |
| `OPENAI_API_KEY` | 否 | OpenAI 兼容 API 密钥（用于 --oss 模式） |
| `DATABASE_URL` | 是 | SQLite 数据库路径 |
| `SECRET_KEY` | 是 | 会话签名密钥 |
| `ENCRYPTION_KEY` | 是 | API Key 加密密钥 |
| `FEISHU_APP_ID` | 否 | 飞书 App ID |
| `FEISHU_APP_SECRET` | 否 | 飞书 App Secret |
| `TELEGRAM_BOT_TOKEN` | 否 | Telegram Bot Token |
| `CONTAINER_IMAGE` | 否 | Agent 容器镜像 |

### D. Codex CLI 集成

#### D.1 核心命令

```bash
# 非交互式执行
codex exec "帮我写一个 Hello World"

# 使用 JSON 输出模式（流式事件）
codex exec --json "任务描述"

# 使用沙箱模式
codex exec --sandbox read-only "任务描述"
codex exec --sandbox workspace-write "任务描述"
codex exec --sandbox danger-full-access "任务描述"

# 使用开放源码模型（--oss）
codex exec --oss --local-provider ollama "任务描述"

# 指定模型
codex exec -m o3 "任务描述"

# 跳过 Git 仓库检查
codex exec --skip-git-repo-check "任务描述"
```

#### D.2 Sandbox 模式

| 模式 | 说明 |
|------|------|
| `read-only` | 只读模式，禁止写入 |
| `workspace-write` | 允许写入工作区 |
| `danger-full-access` | 完全访问（危险） |

#### D.3 MCP Server 模式

```bash
# 作为 MCP 服务器运行（stdio 协议）
codex mcp-server
```

#### D.4 与 HappyClaw 的区别

| 特性 | HappyClaw (Claude Code) | Portex (Codex CLI) |
|------|------------------------|-------------------|
| API 提供商 | Anthropic 官方 | Anthropic / OpenAI 兼容 / 本地模型 |
| 沙箱模式 | 无 | 内置 sandbox 支持 |
| 开源 | 否 | 是 |
| MCP 协议 | 自定义 | 标准 STDIO |

---

*本文档将根据项目进展持续更新*
