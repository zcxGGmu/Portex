# Portex 实施计划 - Task-by-Task

**项目名称**: Portex
**版本**: v1.0.0
**创建日期**: 2026-03-04

---

## 阶段 0: 项目准备 (1 周)

### Task 0.1: 初始化项目结构

**目标**: 创建项目骨架和开发环境

**交付清单**:
- [ ] `portex/pyproject.toml` - Python 项目配置
- [ ] `portex/Makefile` - 开发命令
- [ ] `portex/.env.example` - 环境变量模板
- [ ] `portex/uv.lock` - 依赖锁定
- [ ] `portex/README.md` - 项目说明

**文件结构**:
```
portex/
├── pyproject.toml
├── Makefile
├── .env.example
├── uv.lock
├── README.md
└── portex/
    ├── __init__.py
    └── main.py
```

---

## 阶段 1: 基础设施 (2 周)

### Task 1.1: FastAPI 应用骨架

**目标**: 创建 FastAPI 应用基础结构

**交付清单**:
- [ ] `portex/portex/main.py` - 应用入口
- [ ] `portex/portex/config.py` - 配置管理
- [ ] `portex/portex/constants.py` - 常量定义
- [ ] `portex/portex/utils/logger.py` - 日志配置
- [ ] `portex/tests/unit/test_config.py` - 配置测试

**文件结构**:
```
portex/portex/
├── __init__.py
├── main.py
├── config.py
├── constants.py
└── utils/
    ├── __init__.py
    └── logger.py
```

### Task 1.2: 数据库层

**目标**: 建立数据库连接和模型

**交付清单**:
- [ ] `portex/portex/database/connection.py` - 数据库连接
- [ ] `portex/portex/models/user.py` - 用户模型
- [ ] `portex/portex/models/session.py` - 会话模型
- [ ] `portex/portex/models/message.py` - 消息模型
- [ ] `portex/portex/models/task.py` - 任务模型
- [ ] `portex/portex/database/repositories/user_repo.py` - 用户仓储
- [ ] `portex/portex/database/repositories/session_repo.py` - 会话仓储
- [ ] `portex/portex/database/repositories/message_repo.py` - 消息仓储
- [ ] `portex/portex/database/migrations/` - 迁移脚本

**文件结构**:
```
portex/portex/
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── session.py
│   ├── message.py
│   └── task.py
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repo.py
│   │   ├── session_repo.py
│   │   └── message_repo.py
│   └── migrations/
```

### Task 1.3: Pydantic Schemas

**目标**: 创建请求/响应验证模型

**交付清单**:
- [ ] `portex/portex/schemas/auth.py` - 认证 Schema
- [ ] `portex/portex/schemas/chat.py` - 聊天 Schema
- [ ] `portex/portex/schemas/session.py` - 会话 Schema
- [ ] `portex/portex/schemas/common.py` - 通用 Schema

### Task 1.4: 认证系统

**目标**: 实现用户认证功能

**交付清单**:
- [ ] `portex/portex/utils/crypto.py` - 加密工具
- [ ] `portex/portex/middleware/auth.py` - 认证中间件
- [ ] `portex/portex/api/auth.py` - 认证路由
- [ ] `portex/portex/services/auth_service.py` - 认证服务

---

## 阶段 2: 核心 Agent 功能 (3 周)

### Task 2.1: Agent 执行引擎

**目标**: 实现基于 OpenAI Agents SDK 的 Agent 执行

**交付清单**:
- [ ] `portex/portex/core/agent.py` - Agent 执行引擎
- [ ] `portex/portex/core/agent_tools.py` - 内置工具 (10 个)
- [ ] `portex/portex/core/agent_guardrails.py` - Guardrails
- [ ] `portex/portex/core/agent_handoffs.py` - Handoffs 配置

**文件结构**:
```
portex/portex/core/
├── __init__.py
├── agent.py              # AgentExecutor 类
├── agent_tools.py       # @function_tool 装饰的工具
├── agent_guardrails.py  # @input_guardrail/@output_guardrail
└── agent_handoffs.py    # 多智能体配置
```

### Task 2.2: WebSocket 实时通信

**目标**: 实现 WebSocket 实时消息推送

**交付清单**:
- [ ] `portex/portex/api/ws.py` - WebSocket 端点
- [ ] `portex/portex/core/stream_manager.py` - 流式管理器
- [ ] `portex/tests/integration/test_ws.py` - WebSocket 测试

### Task 2.3: 消息处理流程

**目标**: 实现消息接入到 Agent 执行的完整流程

**交付清单**:
- [ ] `portex/portex/services/chat_service.py` - 聊天服务
- [ ] `portex/portex/services/session_service.py` - 会话服务
- [ ] `portex/portex/api/chat.py` - 聊天路由
- [ ] `portex/portex/api/session.py` - 会话路由

**文件结构**:
```
portex/portex/
├── api/
│   ├── router.py         # 主路由
│   ├── auth.py          # 认证接口
│   ├── chat.py          # 聊天接口
│   ├── session.py        # 会话管理
│   ├── ws.py             # WebSocket
│   └── admin.py          # 管理接口
└── services/
    ├── __init__.py
    ├── auth_service.py
    ├── chat_service.py
    ├── session_service.py
    └── notification_service.py
```

### Task 2.4: 文件 IPC 通信

**目标**: 实现基于文件系统的进程间通信

**交付清单**:
- [ ] `portex/portex/core/ipc.py` - 文件 IPC 类
- [ ] `portex/portex/core/ipc_watcher.py` - 目录监视器
- [ ] `portex/tests/unit/test_ipc.py` - IPC 测试

---

## 阶段 3: 容器隔离 (2 周)

### Task 3.1: Docker 容器管理

**目标**: 实现 Docker 容器生命周期管理

**交付清单**:
- [ ] `portex/portex/core/container.py` - 容器管理类
- [ ] `portex/portex/core/container_config.py` - 容器配置
- [ ] `portex/tests/unit/test_container.py` - 容器测试

### Task 3.2: 容器镜像构建

**目标**: 构建包含 Codex CLI 的容器镜像

**交付清单**:
- [ ] `portex/container/Dockerfile` - 镜像定义
- [ ] `portex/container/build.sh` - 构建脚本
- [ ] `portex/container/agent-runner/main.py` - Agent Runner
- [ ] `portex/container/agent-runner/executor.py` - 执行器
- [ ] `portex/container/agent-runner/mcp_client.py` - MCP 客户端

**文件结构**:
```
portex/container/
├── Dockerfile
├── build.sh
├── agent-runner/
│   ├── __init__.py
│   ├── main.py
│   ├── executor.py
│   └── mcp_client.py
└── skills/           # Skills 目录
```

### Task 3.3: 并发调度器

**目标**: 实现会话级队列调度

**交付清单**:
- [ ] `portex/portex/core/queue.py` - GroupQueue 类
- [ ] `portex/portex/core/queue_scheduler.py` - 调度逻辑
- [ ] `portex/tests/unit/test_queue.py` - 队列测试

### Task 3.4: Web Terminal

**目标**: 实现浏览器内终端

**交付清单**:
- [ ] `portex/portex/core/terminal.py` - 终端管理
- [ ] `portex/portex/api/terminal.py` - 终端路由

---

## 阶段 4: IM 集成 (2 周)

### Task 4.1: IM 适配器基类

**目标**: 定义 IM 适配器接口

**交付清单**:
- [ ] `portex/portex/adapters/base.py` - 适配器基类
- [ ] `portex/portex/adapters/registry.py` - 适配器注册表

### Task 4.2: 飞书适配器

**目标**: 实现飞书消息接入

**交付清单**:
- [ ] `portex/portex/adapters/feishu.py` - 飞书适配器
- [ ] `portex/portex/api/feishu.py` - 飞书 Webhook
- [ ] `portex/tests/integration/test_feishu.py` - 飞书测试

### Task 4.3: Telegram 适配器

**目标**: 实现 Telegram 消息接入

**交付清单**:
- [ ] `portex/portex/adapters/telegram.py` - Telegram 适配器
- [ ] `portex/tests/integration/test_telegram.py` - Telegram 测试

---

## 阶段 5: 高级功能 (2 周)

### Task 5.1: MCP 工具

**目标**: 实现 MCP 服务器和工具

**交付清单**:
- [ ] `portex/portex/core/mcp.py` - MCP 管理器
- [ ] `portex/portex/api/mcp_tools.py` - MCP 工具路由

### Task 5.2: 记忆系统

**目标**: 实现持久记忆功能

**交付清单**:
- [ ] `portex/portex/core/memory.py` - 记忆管理
- [ ] `portex/portex/api/memory.py` - 记忆路由

**文件结构**:
```
portex/data/
├── db/                 # SQLite 数据库
├── ipc/               # IPC 文件目录
│   └── {session_id}/
│       ├── input/
│       ├── messages/
│       └── tasks/
├── memory/             # 记忆文件
│   └── YYYY-MM-DD.md
└── workspaces/        # 用户工作区
    └── home-{userId}/
```

### Task 5.3: 定时任务调度

**目标**: 实现任务调度功能

**交付清单**:
- [ ] `portex/portex/core/scheduler.py` - 调度器
- [ ] `portex/portex/api/task.py` - 任务路由

### Task 5.4: RBAC 权限系统

**目标**: 实现基于角色的访问控制

**交付清单**:
- [ ] `portex/portex/core/permissions.py` - 权限定义
- [ ] `portex/portex/middleware/rbac.py` - RBAC 中间件

---

## 阶段 6: 前端完善 (2 周)

### Task 6.1: React 项目骨架

**目标**: 创建 React 前端项目

**交付清单**:
- [ ] `portex/web/package.json`
- [ ] `portex/web/vite.config.ts`
- [ ] `portex/web/tsconfig.json`
- [ ] `portex/web/index.html`
- [ ] `portex/web/src/main.tsx`
- [ ] `portex/web/src/App.tsx`

**文件结构**:
```
portex/web/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts
│   │   └── ws.ts
│   ├── components/
│   ├── hooks/
│   ├── pages/
│   ├── stores/
│   └── types/
└── public/
```

### Task 6.2: 聊天界面

**目标**: 实现核心聊天界面

**交付清单**:
- [ ] `portex/web/src/components/chat/ChatWindow.tsx`
- [ ] `portex/web/src/components/chat/MessageList.tsx`
- [ ] `portex/web/src/components/chat/MessageItem.tsx`
- [ ] `portex/web/src/components/chat/InputArea.tsx`
- [ ] `portex/web/src/pages/Chat.tsx`

### Task 6.3: PWA 支持

**目标**: 实现渐进式 Web 应用

**交付清单**:
- [ ] `portex/web/vite.config.ts` - PWA 配置
- [ ] `portex/web/public/manifest.json`
- [ ] `portex/web/public/icons/`

### Task 6.4: 管理后台

**目标**: 实现系统管理界面

**交付清单**:
- [ ] `portex/web/src/pages/Admin.tsx`
- [ ] `portex/web/src/pages/Settings.tsx`
- [ ] `portex/web/src/pages/Monitor.tsx`

---

## 阶段 7: 测试与部署 (1 周)

### Task 7.1: 单元测试

**目标**: 编写单元测试

**交付清单**:
- [ ] `portex/tests/unit/` - 单元测试 (80% 覆盖率)

### Task 7.2: 集成测试

**目标**: 编写集成测试

**交付清单**:
- [ ] `portex/tests/integration/` - 集成测试

### Task 7.3: E2E 测试

**目标**: 编写端到端测试

**交付清单**:
- [ ] `portex/tests/e2e/` - E2E 测试

### Task 7.4: Docker Compose 部署

**目标**: 实现一键部署

**交付清单**:
- [ ] `portex/docker-compose.yml` - 部署配置
- [ ] `portex/Dockerfile` - 主服务镜像
- [ ] `portex/.dockerignore`

---

## 交付检查清单

### 阶段 1 交付 (基础设施)
- [ ] FastAPI 应用可启动
- [ ] SQLite 数据库可连接
- [ ] 用户可注册/登录
- [ ] 基础 API 可访问

### 阶段 2 交付 (核心功能)
- [ ] Agent 可执行消息
- [ ] WebSocket 实时推送正常
- [ ] 消息历史可查询

### 阶段 3 交付 (容器隔离)
- [ ] Docker 容器可启动
- [ ] 并发控制正常工作
- [ ] Web Terminal 可用

### 阶段 4 交付 (IM 集成)
- [ ] 飞书消息可接入
- [ ] Telegram 消息可接入

### 阶段 5 交付 (高级功能)
- [ ] MCP 工具可用
- [ ] 记忆系统可用
- [ ] 定时任务可执行

### 阶段 6 交付 (前端)
- [ ] 聊天界面完整
- [ ] PWA 可安装
- [ ] 管理后台可用

### 阶段 7 交付 (测试与部署)
- [ ] 测试覆盖率 > 80%
- [ ] Docker Compose 可部署

---

## 依赖关系图

```
阶段 0 ─────────────────────────────────────────────────>
  │                                                         │
  ▼                                                         ▼
阶段 1 ──────> 阶段 2 ──────> 阶段 3 ──────> 阶段 4 ──────> 阶段 5
  │              │              │              │              │
  ▼              ▼              ▼              ▼              ▼
  Task 1.1      Task 2.1      Task 3.1      Task 4.1       Task 5.1
  Task 1.2      Task 2.2      Task 3.2      Task 4.2       Task 5.2
  Task 1.3      Task 2.3      Task 3.3      Task 4.3       Task 5.3
  Task 1.4      Task 2.4      Task 3.4                     Task 5.4

阶段 6 (前端，可并行) ◄────────────────────────────────────┘
  │
  ▼
阶段 7 ─────────────────────────────────────────────────> 完成
```

---

*实施计划版本: v1.0.0*
*最后更新: 2026-03-04*
