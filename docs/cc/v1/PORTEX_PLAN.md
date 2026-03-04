# Portex 项目规划文档

## 项目概述

**项目名称**: Portex
**项目定位**: 基于 OpenAI Agents SDK 构建的、有 Web 界面的、支持容器隔离的远程 AI Agent 服务
**技术栈**: Python (FastAPI) + React + Docker
**参考项目**: HappyClaw (Node.js/TypeScript)
**核心原则**: 不重新实现 Agent 能力，直接复用 OpenAI Agents SDK

---

## 一、背景与目标

### 1.1 项目背景

HappyClaw 是一个基于 Claude Agent SDK 构建的自托管多用户 AI Agent 系统，通过飞书/Telegram/Web 三端接入完整的 Claude Code 能力。其核心设计原则是：

> **不重新实现 Agent 能力，直接复用 Claude Code/OpenAI Agents SDK。**

这意味着底层调用的是完整的 Agent SDK 运行时，而非 API Wrapper 或 Prompt Chain。Agent 的每一次升级——新工具、更强的推理、更多的 MCP 支持——Portex 零适配自动受益。

### 1.2 项目目标

Portex 旨在用 Python 重写 HappyClaw 的核心功能，主要目标包括：

1. **基于 OpenAI Agents SDK**: 使用 Python 版本的 Agents SDK，实现与原版相同的能力
2. **Web 界面**: 提供现代化的 React 前端，支持实时流式输出
3. **容器隔离**: 支持 Docker 容器隔离执行，确保安全性和多用户隔离
4. **多用户支持**: 支持多用户注册、权限管理和资源隔离
5. **持久记忆**: 实现跨会话的记忆系统

### 1.3 核心特性

| 特性 | 描述 |
|------|------|
| **多端消息接入** | Web 界面实时聊天（首选） |
| **Agent 执行引擎** | 基于 OpenAI Agents SDK，支持容器/宿主机模式 |
| **实时流式体验** | 实时推送 Agent 的思考过程、工具调用追踪 |
| **MCP 内置工具** | 消息发送、任务调度、记忆管理等 |
| **持久记忆系统** | 用户全局记忆、会话记忆、日期记忆 |
| **多用户隔离** | 独立工作区、权限控制、审计日志 |
| **移动端 PWA** | 支持 PWA 安装，原生 App 体验 |

---

## 二、技术架构

### 2.1 整体架构

Portex 由三个独立的 Python/Node.js 项目组成：

| 项目 | 目录 | 职责 |
|------|------|------|
| **主服务** | `/` (Python/FastAPI) | Web 服务器、消息处理、IPC 监听、容器生命周期管理 |
| **Web 前端** | `web/` (React + Vite) | React 19 + TypeScript SPA，Tailwind CSS，PWA |
| **Agent Runner** | `agent-runner/` (Python) | OpenAI Agents SDK 执行引擎，MCP Server |

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户端                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Web UI    │  │   PWA      │  │   (Future: Telegram)    │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Portex 主服务 (FastAPI)                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────┐   │
│  │  Web API │  │ WebSocket│  │  GroupQueue│  │ TaskScheduler│   │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  └──────┬───────┘   │
│       │             │              │               │            │
│  ┌────┴─────────────┴──────────────┴───────────────┴────────┐  │
│  │                    SQLite Database                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                                       ▼
┌─────────────────────┐               ┌─────────────────────────┐
│   Host Agent        │               │   Container Agent       │
│  (宿主机进程模式)    │               │   (Docker 容器模式)     │
│  runHostAgent()     │               │  runContainerAgent()    │
└─────────┬───────────┘               └───────────┬─────────────┘
          │                                       │
          ▼                                       ▼
┌─────────────────────┐               ┌─────────────────────────┐
│ OpenAI Agents SDK  │               │ OpenAI Agents SDK       │
│ (Python)           │               │ (Python)               │
└─────────────────────┘               └─────────────────────────┘
```

### 2.2 技术选型

| 层次 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **后端框架** | FastAPI | ≥0.115 | 现代 Python Web 框架，异步优先 |
| **数据库** | SQLite | - | 轻量级，使用 SQLAlchemy + Alembic |
| **Agent SDK** | openai-agents | latest | OpenAI Agents SDK Python 版 |
| **容器管理** | docker python SDK | latest | Docker 容器生命周期管理 |
| **WebSocket** | fastapi.WebSocket | - | 原生 WebSocket 支持 |
| **前端框架** | React | 19.x | 现代 React + TypeScript |
| **构建工具** | Vite | 6.x | 快速前端构建 |
| **状态管理** | Zustand | 5.x | 轻量级状态管理 |
| **样式** | Tailwind CSS | 4.x | 原子化 CSS |
| **终端模拟** | xterm.js | - | Web Terminal 支持 |

### 2.3 OpenAI Agents SDK 集成要点

```python
from agents import Agent, Runner, function_tool, RunConfig, ModelSettings

# 基本 Agent 定义
agent = Agent(
    name="portex-agent",
    instructions="你是一个有用的 AI 助手",
    model="gpt-4o",
    tools=[my_tool],           # MCP 工具
    handoffs=[sub_agent],     # 子 Agent
    output_type=str,           # 输出类型
)

# 使用流式执行
result = Runner.run_streamed(agent, input)
async for event in result.stream_events():
    # 处理流式事件
```

#### 核心特性

- **流式输出**: 使用 `Runner.run_streamed()` 实时获取事件
- **函数工具**: `@function_tool` 装饰器将 Python 函数转为工具
- **交接 (Handoffs)**: Agent 之间任务委派
- **安全护栏**: 输入/输出验证
- **MCP 支持**: 内置 MCP 服务器连接
- **追踪功能**: 内置可视化调试

### 2.3 数据流

```
用户消息 (Web) → WebSocket/API
     ↓
存储到 SQLite + 广播
     ↓
主进程轮询新消息 (2s 间隔)
     ↓
GroupQueue 判断状态
     ├── 空闲 → 启动容器/进程
     ├── 运行中 → IPC 文件注入消息
     └── 满载 → 排队等待
     ↓
Agent SDK 执行，流式事件输出
     ↓
主进程解析流式事件 → WebSocket 推送前端
     ↓
前端渲染实时输出
```

---

## 三、模块设计

### 3.1 主服务模块 (Python)

```
portex/
├── main.py                    # 应用入口
├── config.py                  # 配置管理
├── api/
│   ├── routes/
│   │   ├── auth.py            # 认证: 登录/登出/注册
│   │   ├── groups.py          # 群组 CRUD
│   │   ├── messages.py        # 消息管理
│   │   ├── files.py           # 文件上传/下载
│   │   ├── memory.py          # 记忆管理
│   │   ├── tasks.py           # 定时任务
│   │   ├── config.py          # 系统配置
│   │   ├── admin.py           # 管理后台
│   │   ├── skills.py          # Skills 管理
│   │   ├── mcp_servers.py     # MCP 服务器
│   │   └── monitor.py         # 系统监控
│   └── deps.py                # 依赖注入
├── core/
│   ├── database.py            # 数据库连接
│   ├── models.py              # SQLAlchemy 模型
│   ├── migrations/            # Alembic 迁移
│   └── security.py            # 密码哈希、会话管理
├── services/
│   ├── container_runner.py    # 容器/宿主机执行引擎
│   ├── group_queue.py         # 并发队列管理
│   ├── task_scheduler.py      # 定时任务调度
│   ├── im_manager.py          # IM 连接管理 (预留)
│   └── websocket_manager.py   # WebSocket 管理
└── utils/
    ├── ipc.py                 # IPC 通信
    ├── stream_parser.py       # 流式输出解析
    └── file_security.py       # 文件安全检查
```

### 3.2 Agent Runner 模块 (Python)

```
agent-runner/
├── src/
│   ├── __main__.py            # 入口点
│   ├── runner.py              # 会话循环
│   ├── types.py               # 类型定义
│   ├── mcp_tools.py           # MCP 工具实现
│   ├── stream_processor.py    # 流式事件处理
│   └── utils.py               # 工具函数
├── requirements.txt            # 依赖
└── pyproject.toml
```

### 3.3 前端模块 (React)

```
web/
├── src/
│   ├── components/
│   │   ├── chat/              # 聊天组件
│   │   ├── auth/              # 认证组件
│   │   ├── layout/            # 布局组件
│   │   └── ui/                # UI 组件
│   ├── stores/                # Zustand 状态
│   ├── hooks/                 # 自定义 Hooks
│   ├── api/                   # API 客户端
│   ├── ws.ts                  # WebSocket 管理
│   ├── types.ts               # 类型定义
│   └── stream-event.types.ts  # 流事件类型
├── package.json
└── vite.config.ts
```

---

## 四、核心功能实现

### 4.1 认证与权限系统

#### 4.1.1 认证机制

- **密码哈希**: bcrypt (12 轮)
- **会话管理**: JWT Token，30 天过期
- **Cookie 认证**: HttpOnly + SameSite=Lax

```python
# 认证流程
POST /api/auth/login
  → 验证密码
  → 生成 JWT Token
  → 设置 HttpOnly Cookie

POST /api/auth/register
  → 验证邀请码 (如启用)
  → 创建用户
  → 自动创建用户主容器 (home-{userId})
```

#### 4.1.2 RBAC 权限

| 权限 | 说明 |
|------|------|
| `manage_system_config` | 管理系统配置 |
| `manage_group_env` | 管理群组环境变量 |
| `manage_users` | 用户管理 |
| `manage_invites` | 邀请码管理 |
| `view_audit_log` | 查看审计日志 |

**角色**: admin, member

### 4.2 Agent 执行引擎

#### 4.2.1 执行模式

| 模式 | 行为 | 适用对象 |
|------|------|----------|
| `host` | Agent 作为宿主机进程运行 | admin 主容器 |
| `container` | Agent 在 Docker 容器中运行 | member 主容器及其他 |

#### 4.2.2 容器配置

```python
# 容器挂载策略
VOLUMES = {
    "/workspace/group": group_dir,        # 群组工作区
    "/workspace/global": user_global_dir, # 用户全局记忆
    "/workspace/memory": memory_dir,     # 日期记忆
    "/home/portex/.portex": sessions_dir, # Claude 会话
    "/workspace/ipc": ipc_dir,           # IPC 通信
    "/workspace/skills": skills_dir,     # Skills
    "/workspace/env": env_dir,           # 环境变量
}
```

#### 4.2.3 OpenAI Agents SDK 集成

```python
from agents import Agent, Runner

async def run_agent(input: ContainerInput):
    agent = Agent(
        name="portex-agent",
        instructions=get_agent_instructions(group),
        tools=get_mcp_tools(),  # MCP 工具
    )

    result = await Runner.run(
        agent,
        input.prompt,
        run_context=context,
    )

    return result.final_output
```

### 4.3 MCP 内置工具

| 工具 | 功能 |
|------|------|
| `send_message` | 运行期间即时发送消息给用户 |
| `schedule_task` | 创建定时/周期/一次性任务 |
| `list_tasks` / `pause_task` / `resume_task` / `cancel_task` | 任务生命周期管理 |
| `memory_append` | 追加时效记忆 |
| `memory_search` / `memory_get` | 全文检索和读取记忆 |

### 4.4 流式事件

| 事件类型 | 说明 |
|---------|------|
| `text_delta` | 文本增量 |
| `thinking_delta` | 推理过程 |
| `tool_use_start` / `tool_use_end` | 工具调用开始/结束 |
| `tool_progress` | 工具执行进度 |
| `hook_started` / `hook_progress` / `hook_response` | Hook 执行状态 |
| `status` | 系统状态 |

### 4.5 持久记忆系统

```
记忆结构:
├── CLAUDE.md           # 用户全局记忆 (per-user)
├── groups/{folder}/CLAUDE.md  # 会话私有记忆
└── memory/{folder}/
    └── YYYY-MM-DD.md   # 日期记忆
```

### 4.6 WebSocket 协议

**服务端 → 客户端**:

| 类型 | 用途 |
|------|------|
| `new_message` | 新消息到达 |
| `agent_reply` | Agent 最终回复 |
| `stream_event` | 流式事件 |
| `typing` | 输入指示 |
| `status_update` | 系统状态变更 |

**客户端 → 服务端**:

| 类型 | 用途 |
|------|------|
| `send_message` | 发送消息 |
| `terminal_start` | 启动终端 |
| `terminal_input` | 终端输入 |

---

## 五、数据库设计

### 5.1 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    status TEXT NOT NULL DEFAULT 'active',
    permissions TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 会话表
CREATE TABLE sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 群组表
CREATE TABLE groups (
    id TEXT PRIMARY KEY,
    jid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    folder TEXT NOT NULL,
    is_home BOOLEAN DEFAULT FALSE,
    created_by TEXT REFERENCES users(id),
    execution_mode TEXT DEFAULT 'container',
    container_config TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 消息表
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_jid TEXT NOT NULL,
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_from_me BOOLEAN DEFAULT FALSE,
    source TEXT DEFAULT 'web'
);

-- 任务表
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    group_folder TEXT NOT NULL,
    prompt TEXT NOT NULL,
    schedule_type TEXT NOT NULL,
    schedule_value TEXT,
    status TEXT DEFAULT 'pending',
    next_run TIMESTAMP,
    created_by TEXT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sub-Agent 表
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    group_folder TEXT NOT NULL,
    kind TEXT NOT NULL,
    status TEXT DEFAULT 'idle',
    info TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 审计日志表
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT REFERENCES users(id),
    action TEXT NOT NULL,
    target TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 六、API 设计

### 6.1 认证 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/auth/status` | 系统初始化状态 |
| POST | `/api/auth/setup` | 创建管理员 (仅首次) |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/me` | 当前用户信息 |
| POST | `/api/auth/register` | 注册 |
| PUT | `/api/auth/profile` | 更新个人资料 |

### 6.2 群组 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/groups` | 群组列表 |
| POST | `/api/groups` | 创建群组 |
| GET | `/api/groups/{jid}` | 群组详情 |
| PATCH | `/api/groups/{jid}` | 更新群组 |
| DELETE | `/api/groups/{jid}` | 删除群组 |
| GET | `/api/groups/{jid}/messages` | 消息历史 |
| POST | `/api/groups/{jid}/reset-session` | 重置会话 |

### 6.3 配置 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/PUT | `/api/config/openai` | OpenAI 配置 |
| GET/PUT | `/api/config/system` | 系统参数 |
| GET/PUT | `/api/config/appearance` | 外观配置 |

### 6.4 监控 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/status` | 系统状态 |
| GET | `/api/health` | 健康检查 |

---

## 七、实现计划

### 7.1 阶段一：基础架构 (第 1-2 周)

**目标**: 完成项目基础架构和核心功能

1. **项目初始化**
   - [ ] 创建 Python 项目结构 (FastAPI)
   - [ ] 配置 SQLite + SQLAlchemy
   - [ ] 设置 Alembic 数据库迁移
   - [ ] 配置日志系统

2. **认证系统**
   - [ ] 用户注册/登录 API
   - [ ] JWT 会话管理
   - [ ] 密码哈希验证

3. **数据库模型**
   - [ ] 定义所有 SQLAlchemy 模型
   - [ ] 实现基础 CRUD 操作
   - [ ] 编写数据库迁移脚本

### 7.2 阶段二：Agent 执行引擎 (第 3-4 周)

**目标**: 实现 Agent 核心执行能力

1. **Agent Runner**
   - [ ] 创建 Python Agent Runner
   - [ ] 集成 OpenAI Agents SDK
   - [ ] 实现会话循环
   - [ ] 流式输出处理

2. **容器管理**
   - [ ] Docker 容器生命周期管理
   - [ ] 容器卷挂载
   - [ ] 环境变量注入
   - [ ] 超时和资源限制

3. **IPC 通信**
   - [ ] 文件系统 IPC 实现
   - [ ] 消息队列
   - [ ] 流式事件解析

### 7.3 阶段三：Web API 和 WebSocket (第 5 周)

**目标**: 完成 Web 服务和实时通信

1. **REST API**
   - [ ] 群组管理 API
   - [ ] 消息管理 API
   - [ ] 文件上传/下载 API
   - [ ] 配置管理 API

2. **Socket**
   - [ ] WebSocket 连接管理
Web   - [ ] 实时消息推送
   - [ ] 流式事件广播

3. **任务调度**
   - [ ] Cron 任务调度
   - [ ] 任务队列管理

### 7.4 阶段四：前端开发 (第 6-7 周)

**目标**: 完成 React 前端开发

1. **基础界面**
   - [ ] 项目初始化 (React + Vite + TS)
   - [ ] 登录/注册页面
   - [ ] 主布局和路由

2. **聊天界面**
   - [ ] 消息列表组件
   - [ ] 消息输入框
   - [ ] Markdown 渲染

3. **实时功能**
   - [ ] WebSocket 连接
   - [ ] 流式事件处理
   - [ ] 工具调用追踪显示

4. **管理功能**
   - [ ] 用户管理页面
   - [ ] 群组管理页面
   - [ ] 系统设置页面

### 7.5 阶段五：完善与优化 (第 8 周)

**目标**: 完善功能，优化性能

1. **记忆系统**
   - [ ] CLAUDE.md 管理
   - [ ] 日期记忆
   - [ ] 记忆检索

2. **MCP 工具**
   - [ ] send_message
   - [ ] schedule_task
   - [ ] memory_append/search

3. **PWA 支持**
   - [ ] Service Worker
   - [ ] 离线缓存

4. **测试与文档**
   - [ ] 单元测试
   - [ ] 集成测试
   - [ ] 项目文档

---

## 八、安全考虑

### 8.1 用户隔离

- 每用户独立工作区 (`home-{userId}`)
- 独立 Claude 会话目录
- 独立 IPC 命名空间

### 8.2 权限控制

- RBAC 权限模型
- 会话级权限检查
- 文件访问白名单

### 8.3 敏感数据

- API Key 加密存储
- 密码 bcrypt 哈希
- Session Token 安全传输

### 8.4 审计日志

- 18 种事件类型
- 完整操作追踪

---

## 九、部署说明

### 9.1 前置要求

- Python >= 3.11
- Docker (容器模式)
- Node.js >= 20 (前端构建)
- OpenAI API Key

### 9.2 快速开始

```bash
# 克隆项目
git clone https://github.com/your-repo/portex.git
cd portex

# 安装后端依赖
pip install -r requirements.txt

# 初始化数据库
alembic upgrade head

# 构建前端
cd web && npm install && npm run build

# 启动服务
python main.py

# 访问 http://localhost:8000
```

### 9.3 Docker 镜像构建

```bash
# 构建 Agent 容器镜像
docker build -t portex-agent:latest -f agent-runner/Dockerfile agent-runner/
```

---

## 十、参考资源

- [HappyClaw GitHub](https://github.com/riba2534/happyclaw)
- [OpenAI Agents SDK](https://openai-agents-sdk.doczh.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)

---

## 十一、后续规划

1. **飞书集成**: 支持飞书消息接入
2. **Telegram 集成**: 支持 Telegram Bot 消息
3. **Web Terminal**: 基于 xterm.js 的浏览器终端
4. **MCP Server 管理**: 用户自定义 MCP 服务器
5. **多模型支持**: 支持多种 LLM 提供商

---

*文档版本: 1.0*
*创建日期: 2026-03-03*
