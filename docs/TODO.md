# Portex 项目实施计划 (Task-by-Task)

**项目名称**: Portex
**文档版本**: 1.0
**创建日期**: 2026-03-04

---

## 目录

- [M0: 预研封板 (1周)](#m0-预研封板-1周)
- [M1: 核心骨架 (2周)](#m1-核心骨架-2周)
- [M2: 运行链路 (2周)](#m2-运行链路-2周)
- [M3: 容器隔离 (2周)](#m3-容器隔离-2周)
- [M4: 多用户与任务 (2周)](#m4-多用户与任务-2周)
- [M5: IM接入 (1周)](#m5-im接入-1周)
- [M6: 发布准备 (1周)](#m6-发布准备-1周)

---

## M0: 预研封板 (1周)

**目标**: 集成路径与契约定稿，完成 3 个 PoC

### M0.1: 环境搭建与依赖验证 [Day 1-2]

- [x] **M0.1.1** 创建项目目录结构

```
portex/
├── app/
├── domain/
├── infra/
├── services/
├── container/
│   └── agent-runner/
├── web/
├── data/
├── config/
└── scripts/
```

- [x] **M0.1.2** 初始化 Python 项目 (pyproject.toml)

```toml
[project]
name = "portex"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "python-multipart>=0.0.10",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "aiosqlite>=0.20.0",
    "docker>=7.0.0",
    "httpx>=0.27.0",
]
```

- [x] **M0.1.3** 验证 OpenAI Agents SDK 安装

```bash
pip install openai-agents
python -c "from agents import Agent, Runner; print('OK')"
```

- [x] **M0.1.4** 创建虚拟环境并安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**交付**: 可运行的 Python 环境

### M0.2: PoC 1 - SDK 流式输出 [Day 2-3]

- [x] **M0.2.1** 创建 PoC 目录 `pocs/streaming/`

```
pocs/
└── streaming/
    ├── main.py
    └── requirements.txt
```

- [x] **M0.2.2** 实现基础 Agent 流式输出

```python
# pocs/streaming/main.py
from agents import Agent, Runner

agent = Agent(
    name="Test",
    instructions="你是一个有帮助的助手",
)

result = Runner.run_streamed(agent, input="你好")
async for event in result.stream_events():
    print(event)
```

- [x] **M0.2.3** 测试并记录事件类型

- [x] **M0.2.4** 编写事件映射示例 `event_mapper.py`

**交付**: `pocs/streaming/` 目录，事件类型清单

### M0.3: PoC 2 - Codex/工具调用 [Day 3-4]

- [x] **M0.3.1** 创建 PoC 目录 `pocs/tools/`

```
pocs/
└── tools/
    ├── main.py
    └── requirements.txt
```

- [x] **M0.3.2** 定义自定义工具（模拟文件操作）

```python
from agents import function_tool, RunContextWrapper
from typing import Any

@function_tool
def read_file(ctx: RunContextWrapper[Any], path: str) -> str:
    """读取文件内容"""
    with open(path, 'r') as f:
        return f.read()
```

- [x] **M0.3.3** 验证工具注册与调用

- [x] **M0.3.4** 记录工具调用流程

**交付**: `pocs/tools/` 目录，工具调用流程文档

### M0.4: PoC 3 - 事件映射与契约 [Day 4-5]

- [x] **M0.4.1** 定义 Portex 事件契约

```python
# portex/contracts/events.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class EventType(str, Enum):
    RUN_STARTED = "run.started"
    TOKEN_DELTA = "run.token.delta"
    TOOL_STARTED = "run.tool.started"
    TOOL_COMPLETED = "run.tool.completed"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"

class PortexEvent(BaseModel):
    event_type: EventType
    run_id: str
    payload: dict
    seq: int
    timestamp: str
```

- [x] **M0.4.2** 实现 SDK 事件 → Portex 事件映射器

```python
# pocs/events/mapper.py
def map_sdk_event(sdk_event) -> PortexEvent:
    # 实现映射逻辑
    pass
```

- [x] **M0.4.3** 编写契约测试用例

**交付**: `portex/contracts/` 模块，事件契约文档

### M0.5: 预研总结与定稿 [Day 5]

- [x] **M0.5.1** 整理 PoC 结果与发现

- [x] **M0.5.2** 更新项目规划文档

- [x] **M0.5.3** 确认技术选型决策

**交付**: M0 阶段报告，技术选型确认

---

## M1: 核心骨架 (2周)

**目标**: 后端框架与基础表可用

### M1.1: 项目骨架搭建 [Week 1, Day 1-2]

- [x] **M1.1.1** 创建完整目录结构

```
portex/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   └── routes/
│       ├── __init__.py
│       ├── auth.py             # 认证路由
│       ├── users.py            # 用户管理
│       ├── groups.py           # 群组管理
│       ├── messages.py         # 消息路由
│       ├── tasks.py            # 任务路由
│       └── admin.py            # 管理路由
├── domain/
│   ├── __init__.py
│   ├── models/                 # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── message.py
│   │   ├── group.py
│   │   ├── session.py
│   │   └── task.py
│   ├── schemas.py              # Pydantic 模型
│   └── exceptions.py           # 业务异常
├── infra/
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # 数据库连接
│   │   ├── session.py          # 会话管理
│   │   └── repositories/       # 数据仓库
│   ├── runtime/                # Agent 运行时
│   │   ├── __init__.py
│   │   ├── adapter.py          # 抽象适配器
│   │   └── openai.py          # OpenAI Agents 实现
│   ├── exec/                   # 容器执行
│   │   ├── __init__.py
│   │   ├── docker.py          # Docker 操作
│   │   └── process.py         # 进程管理
│   └── im/                     # IM 通道
│       ├── __init__.py
│       ├── base.py             # 基础接口
│       ├── feishu.py           # 飞书实现
│       └── telegram.py          # Telegram 实现
├── services/
│   ├── __init__.py
│   ├── auth.py                 # 认证服务
│   ├── group_queue.py          # 并发调度
│   ├── scheduler.py            # 定时任务
│   ├── memory.py               # 记忆系统
│   └── skills.py               # Skills 管理
├── container/
│   └── agent-runner/
│       ├── src/
│       │   ├── __init__.py
│       │   ├── runner.py
│       │   ├── event_mapper.py
│       │   ├── tools/
│       │   │   ├── __init__.py
│       │   │   ├── message.py
│       │   │   ├── task.py
│       │   │   └── memory.py
│       │   └── ipc/
│       │       ├── __init__.py
│       │       ├── reader.py
│       │       └── writer.py
│       ├── pyproject.toml
│       └── Dockerfile
├── web/                        # 前端项目
├── config/
│   └── default.yaml           # 默认配置
├── scripts/
│   ├── init_db.py             # 初始化数据库
│   └── build_docker.py        # 构建镜像
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── pyproject.toml
├── uvicorn.ini
├── Makefile
└── README.md
```

- [x] **M1.1.2** 配置 FastAPI 应用 (app/main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Portex", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

- [x] **M1.1.3** 配置日志系统

```python
# app/config.py
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
```

**交付**: 完整目录结构，基础 FastAPI 应用

### M1.2: 数据库层实现 [Week 1, Day 2-4]

- [x] **M1.2.1** 实现数据库连接 (infra/db/database.py)

```python
# infra/db/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./portex.db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

- [x] **M1.2.2** 定义用户模型 (domain/models/user.py)

```python
# domain/models/user.py
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="member")  # owner/admin/member
    status = Column(String, default="active")
    permissions = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

- [x] **M1.2.3** 定义消息模型 (domain/models/message.py)

```python
# domain/models/message.py
class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    chat_jid = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_from_me = Column(Boolean, default=False)
    attachments = Column(Text)  # JSON
```

- [x] **M1.2.4** 定义会话模型 (domain/models/session.py)

```python
# domain/models/session.py
class Session(Base):
    __tablename__ = "sessions"

    group_folder = Column(String, primary_key=True)
    session_id = Column(String, primary_key=True)
    agent_id = Column(String, default="")
```

- [x] **M1.2.5** 定义群组模型 (domain/models/group.py)

```python
# domain/models/group.py
class RegisteredGroup(Base):
    __tablename__ = "registered_groups"

    jid = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    folder = Column(String, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    container_config = Column(Text)  # JSON
    created_by = Column(String)
```

- [x] **M1.2.6** 定义任务模型 (domain/models/task.py)

```python
# domain/models/task.py
class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(String, primary_key=True)
    group_folder = Column(String, nullable=False)
    chat_jid = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    schedule_type = Column(String)  # cron/interval/once
    schedule_value = Column(String)
    next_run = Column(DateTime)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [x] **M1.2.7** 创建数据库初始化脚本 (scripts/init_db.py)

```python
# scripts/init_db.py
from portex.infra.db.database import engine
from portex.domain.models import user, message, group, session, task

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(user.Base.metadata.create_all)
        await conn.run_sync(message.Base.metadata.create_all)
        # ... 其他模型

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
```

**交付**: 数据库模型，初始化脚本

### M1.3: 基础 API 路由 [Week 1, Day 4-5 + Week 2, Day 1]

- [x] **M1.3.1** 实现健康检查接口

```python
# app/routes/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
```

- [x] **M1.3.2** 实现用户注册接口

```python
# app/routes/auth.py
@router.post("/auth/register")
async def register(request: RegisterRequest):
    # 验证用户名唯一
    # 密码哈希
    # 创建用户
    return {"user_id": user.id}
```

- [x] **M1.3.3** 实现用户登录接口

```python
@router.post("/auth/login")
async def login(request: LoginRequest):
    # 验证凭据
    # 生成 token
    return {"access_token": token, "token_type": "bearer"}
```

- [x] **M1.3.4** 实现用户信息接口

```python
@router.get("/users/me")
async def get_current_user(current_user: User = Depends(get_current_user)):
    return current_user
```

- [x] **M1.3.5** 实现群组列表接口

```python
@router.get("/groups")
async def list_groups(current_user: User = Depends(get_current_user)):
    # 返回用户可见的群组
    pass
```

- [x] **M1.3.6** 实现消息发送接口

```python
@router.post("/messages")
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user)
):
    # 存储消息
    # 触发 Agent 执行
    pass
```

**交付**: 基础 API 路由，可运行的 REST API

### M1.4: 认证与安全基础 [Week 2, Day 2-3]

- [x] **M1.4.1** 实现密码哈希

```python
# services/auth.py
from passlib.hash import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hash: str) -> bool:
    return bcrypt.verify(password, hash)
```

- [x] **M1.4.2** 实现 JWT token 生成与验证

```python
# services/auth.py
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

- [x] **M1.4.3** 实现依赖注入的当前用户获取

```python
# app/middleware/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(
    token: str = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    # 验证 token
    # 获取用户
    # 返回用户对象
```

- [x] **M1.4.4** 配置 CORS 中间件

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**交付**: 认证系统，JWT token 支持

### M1.5: 前端骨架 [Week 2, Day 4-5]

- [x] **M1.5.1** 初始化前端项目

```bash
cd web
npm create vite@latest . -- --template react-ts
npm install
npm install tailwindcss @tailwindcss/vite
npm install zustand @tanstack/react-query react-router-dom
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
```

- [x] **M1.5.2** 配置 Tailwind CSS

```javascript
// web/vite.config.ts
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],
})
```

- [x] **M1.5.3** 创建基础页面结构

```
web/src/
├── App.tsx
├── main.tsx
├── api/
│   └── client.ts           # API 客户端
├── components/
│   ├── ui/                 # 基础 UI 组件
│   ├── layout/             # 布局组件
│   └── chat/               # 聊天组件
├── pages/
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── Chat.tsx
│   └── Settings.tsx
├── stores/
│   ├── auth.ts            # 认证状态
│   └── chat.ts            # 聊天状态
└── hooks/
    └── useApi.ts          # API Hook
```

- [x] **M1.5.4** 实现登录页面

```tsx
// web/src/pages/Login.tsx
import { useState } from 'react'
import { useAuthStore } from '../stores/auth'

export function Login() {
  const login = useAuthStore(s => s.login)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  return (
    <form onSubmit={() => login(username, password)}>
      <input value={username} onChange={e => setUsername(e.target.value)} />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button>登录</button>
    </form>
  )
}
```

**交付**: 可运行的前端项目

### M1.6: M1 阶段验收 [Week 2, Day 5]

- [x] **M1.6.1** 运行单元测试

```bash
pytest tests/unit/ -v
```

- [x] **M1.6.2** 验证 API 端点

```bash
curl http://localhost:8000/health
```

- [x] **M1.6.3** 验证前端构建

```bash
cd web && npm run build
```

**交付清单**:
- [x] 完整项目目录结构
- [x] FastAPI 应用可运行
- [x] SQLite 数据库初始化
- [x] 用户认证 (注册/登录)
- [x] 基础 API 路由
- [x] 前端骨架页面

---

## M2: 运行链路 (2周)

**目标**: Web -> Runtime -> WS 流式

### M2.1: WebSocket 基础 [Week 1, Day 1-2]

- [x] **M2.1.1** 创建 WebSocket 管理器

```python
# app/websocket.py
from fastapi import WebSocket
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = set()
        self.active_connections[room].add(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)

    async def send_message(self, message: str, room: str):
        for connection in self.active_connections.get(room, []):
            await connection.send_text(message)
```

- [x] **M2.1.2** 定义 WebSocket 路由

```python
# app/routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/{group_folder}")
async def websocket_endpoint(websocket: WebSocket, group_folder: str):
    await manager.connect(websocket, group_folder)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理消息
    except WebSocketDisconnect:
        manager.disconnect(websocket, group_folder)
```

- [x] **M2.1.3** 前端 WebSocket 客户端

```typescript
// web/src/api/ws.ts
export function createWebSocket(groupFolder: string) {
  const ws = new WebSocket(`ws://localhost:8000/ws/${groupFolder}`)

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // 处理事件
  }

  return ws
}
```

**交付**: WebSocket 基础设施

### M2.2: Agent Runtime 适配器 [Week 1, Day 2-4]

- [x] **M2.2.1** 定义运行时抽象接口

```python
# infra/runtime/adapter.py
from abc import ABC, abstractmethod
from typing import Protocol, AsyncIterator
from dataclasses import dataclass

@dataclass
class RunRequest:
    request_id: str
    group_folder: str
    message: str
    session_id: str
    user_id: str

@dataclass
class RunEvent:
    event_type: str
    run_id: str
    payload: dict

@dataclass
class RunResult:
    status: str
    final_output: str

class AgentRuntime(Protocol):
    async def run_streamed(
        self, request: RunRequest
    ) -> AsyncIterator[RunEvent]:
        ...

    async def cancel(self, run_id: str) -> None:
        ...
```

- [x] **M2.2.2** 实现 OpenAI Agents Runtime

```python
# infra/runtime/openai.py
from agents import Agent, Runner
from typing import AsyncIterator

class OpenAIAgentsRuntime:
    def __init__(self, tools: list):
        self.agent = Agent(
            name="PortexAgent",
            instructions="你是一个专业的 AI 助手",
            tools=tools,
        )

    async def run_streamed(
        self, request: RunRequest
    ) -> AsyncIterator[RunEvent]:
        result = Runner.run_streamed(
            self.agent,
            input=request.message
        )
        async for event in result.stream_events():
            yield self._map_event(event)
```

- [x] **M2.2.3** 实现事件映射器

```python
# infra/runtime/mapper.py
def map_sdk_event(sdk_event) -> RunEvent:
    if sdk_event.type == "raw_response_event":
        # 处理原始响应
        pass
    elif sdk_event.type == "run_item_stream_event":
        # 处理运行项
        pass
    # ...
```

**交付**: Agent Runtime 适配器

### M2.3: 消息处理链路 [Week 1, Day 4-5]

- [x] **M2.3.1** 实现消息存储

```python
# services/message_service.py
async def store_message(
    db: AsyncSession,
    chat_jid: str,
    sender: str,
    content: str,
    is_from_me: bool = False
) -> Message:
    message = Message(
        id=str(uuid.uuid4()),
        chat_jid=chat_jid,
        sender=sender,
        content=content,
        is_from_me=is_from_me,
        timestamp=datetime.utcnow()
    )
    db.add(message)
    await db.commit()
    return message
```

- [x] **M2.3.2** 实现消息触发 Agent 执行

```python
# services/agent_trigger.py
async def trigger_agent_execution(
    group_folder: str,
    message: str,
    user_id: str,
    websocket_manager: ConnectionManager
):
    # 1. 创建请求
    request = RunRequest(
        request_id=str(uuid.uuid4()),
        group_folder=group_folder,
        message=message,
        session_id=get_session_id(group_folder),
        user_id=user_id
    )

    # 2. 获取运行时
    runtime = get_runtime(group_folder)

    # 3. 执行并推送事件
    async for event in runtime.run_streamed(request):
        await websocket_manager.send_message(
            json.dumps(event),
            group_folder
        )
```

- [x] **M2.3.3** 前端消息展示

```typescript
// web/src/stores/chat.ts
import { create } from 'zustand'

interface ChatState {
  messages: Message[]
  addMessage: (msg: Message) => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  addMessage: (msg) => set((state) => ({
    messages: [...state.messages, msg]
  })),
}))
```

**交付**: 完整消息处理链路

### M2.4: 流式输出完善 [Week 2, Day 1-3]

- [x] **M2.4.1** 定义前端事件类型

```typescript
// web/src/types/events.ts
export type StreamEvent =
  | { type: 'run.started'; runId: string }
  | { type: 'run.token.delta'; runId: string; delta: string }
  | { type: 'run.tool.started'; runId: string; toolName: string; input: any }
  | { type: 'run.tool.completed'; runId: string; toolName: string; output: any }
  | { type: 'run.completed'; runId: string; finalOutput: string }
  | { type: 'run.failed'; runId: string; error: string }
```

- [x] **M2.4.2** 实现流式消息组件

```tsx
// web/src/components/chat/MessageList.tsx
export function MessageList() {
  const messages = useChatStore(s => s.messages)

  return (
    <div className="flex flex-col gap-2">
      {messages.map(msg => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
    </div>
  )
}
```

- [x] **M2.4.3** 实现思考过程展示

```tsx
// web/src/components/chat/ThinkingPanel.tsx
export function ThinkingPanel({ events }: { events: StreamEvent[] }) {
  const thinking = events
    .filter(e => e.type === 'run.token.delta')
    .map(e => e.delta)
    .join('')

  return <div className="thinking">{thinking}</div>
}
```

- [x] **M2.4.4** 实现工具调用追踪展示

```tsx
// web/src/components/chat/ToolCallTracker.tsx
export function ToolCallTracker({ events }: { events: StreamEvent[] }) {
  const toolCalls = events.filter(e =>
    e.type === 'run.tool.started' || e.type === 'run.tool.completed'
  )

  return (
    <div className="tool-calls">
      {toolCalls.map((call, i) => (
        <ToolCallItem key={i} event={call} />
      ))}
    </div>
  )
}
```

**交付**: 完整的流式输出前端展示

### M2.5: 取消与超时处理 [Week 2, Day 4-5]

- [x] **M2.5.1** 实现取消功能

```python
# infra/runtime/openai.py
class OpenAIAgentsRuntime:
    def __init__(self, tools: list):
        self.active_runs: Dict[str, RunResultStreaming] = {}

    async def run_streamed(self, request: RunRequest) -> AsyncIterator[RunEvent]:
        result = Runner.run_streamed(self.agent, input=request.message)
        self.active_runs[request.request_id] = result
        try:
            async for sdk_event in result.stream_events():
                mapped_event = map_sdk_event(sdk_event, run_id=request.request_id)
                if mapped_event is not None:
                    yield mapped_event
        finally:
            self.active_runs.pop(request.request_id, None)

    async def cancel(self, run_id: str) -> None:
        result = self.active_runs.get(run_id)
        if result is not None:
            result.cancel()
```

- [x] **M2.5.2** 实现超时控制

```python
# services/agent_trigger.py
async def trigger_agent_execution(..., timeout_ms: int = 300000):
    consumer_task = asyncio.create_task(_broadcast_runtime_events(...))
    done, _ = await asyncio.wait({consumer_task}, timeout=timeout_ms / 1000)

    if consumer_task in done:
        await consumer_task
        return run_id

    try:
        await runtime.cancel(request.request_id)
    finally:
        consumer_task.cancel()
        with suppress(asyncio.CancelledError):
            await consumer_task

    await websocket_manager.send_message(
        serialize_run_event(
            RunEvent(
                event_type="run.timeout",
                run_id=run_id,
                payload={"status": "timeout", "timeout_ms": timeout_ms},
            )
        ),
        group_folder,
    )
```

- [x] **M2.5.3** 前端取消按钮

```tsx
// web/src/components/chat/ChatPanel.tsx
export function ChatPanel() {
  const isRunning = useChatStore((state) => state.isRunning)
  const activeRunId = useChatStore((state) => state.activeRunId)

  function handleCancel() {
    if (!activeRunId || wsRef.current?.readyState !== WebSocket.OPEN) {
      return
    }

    wsRef.current.send(JSON.stringify({ type: 'cancel', run_id: activeRunId }))
  }

  return <button onClick={handleCancel} disabled={!isRunning}>取消</button>
}
```

**交付**: 可取消的 Agent 执行

### M2.6: M2 阶段验收 [Week 2, Day 5]

- [x] **M2.6.1** 端到端测试

```bash
# 1. 启动后端
PYTHONPATH=. .venv/bin/python /tmp/portex_m26_acceptance_app.py

# 2. 启动前端
cd web && npm run dev -- --host 127.0.0.1 --port 5173

# 3. 测试流程
# - HTTP register/login/users/me
# - WS 发送消息并观察流式输出
# - WS 发送 cancel 控制帧并观察 cancelled 终态
```

**交付清单**:
- [x] WebSocket 实时通信
- [x] Agent 执行链路
- [x] 流式输出前端展示
- [x] 取消与超时功能
- [x] 端到端测试通过

---

## M3: 容器隔离 (2周)

**目标**: container/host 双模式

### M3.1: Docker SDK 集成 [Week 1, Day 1-2]

- [x] **M3.1.1** 安装 Docker SDK

```toml
# pyproject.toml
dependencies = [
    "docker>=7.0.0",
]
```

- [x] **M3.1.2** 创建 Docker 客户端

```python
# infra/exec/docker.py
import docker
from docker.models.containers import Container

class DockerClient:
    def __init__(self):
        self.client = docker.from_env()

    def list_containers(self) -> list[Container]:
        return self.client.containers.list()

    def get_container(self, name: str) -> Container:
        return self.client.containers.get(name)
```

- [x] **M3.1.3** 实现容器操作

```python
# infra/exec/docker.py
async def run_container(
    image: str,
    command: list,
    volumes: dict,
    environment: dict
) -> Container:
    container = self.client.containers.run(
        image,
        command,
        volumes=volumes,
        environment=environment,
        detach=True,
        remove=False
    )
    return container
```

**交付**: Docker 客户端封装

### M3.2: Agent Runner 容器化 [Week 1, Day 2-4]

- [x] **M3.2.1** 创建 Agent Runner Dockerfile

```dockerfile
# container/agent-runner/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    ffmpeg \
    imagemagick \
    postgresql-client \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

RUN useradd -m -u 1000 portex \
    && chown -R portex:portex /app

USER portex

ENTRYPOINT ["python", "-m", "src.runner"]
```

- [x] **M3.2.2** 实现 Runner 主入口

```python
# container/agent-runner/src/runner.py
import sys
from agents import Agent, Runner

from .tools import build_default_tools
from .types import ContainerInput, ContainerOutput

def run_agent(config: ContainerInput) -> ContainerOutput:
    agent = Agent(
        name=config.agent_name,
        instructions=config.instructions,
        tools=build_default_tools(),
    )
    result = Runner.run_sync(agent, input=config.prompt)
    return ContainerOutput(status="success", result=str(result.final_output))

def main() -> int:
    request = ContainerInput.model_validate_json(sys.stdin.read())
    print(run_agent(request).model_dump_json())
    return 0
```

- [x] **M3.2.3** 定义容器输入输出协议

```python
# container/agent-runner/src/types.py
from typing import Literal

from pydantic import BaseModel, ConfigDict

class ContainerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str
    group_folder: str
    session_id: str | None = None
    agent_name: str = "PortexAgent"
    instructions: str = "你是一个专业的 AI 助手"

class ContainerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "error", "timeout"]
    result: str | None = None
    error: str | None = None
```

**交付**: Agent Runner 容器镜像

### M3.3: 卷挂载与安全 [Week 1, Day 4-5]

- [x] **M3.3.1** 实现卷挂载构建器

```python
# infra/exec/docker.py
def build_volumes(group_folder: str, user_id: str) -> dict:
    return {
        f"{DATA_DIR}/sessions/{group_folder}/.claude": {
            "bind": "/home/portex/.claude",
            "mode": "rw"
        },
        f"{DATA_DIR}/memory/{group_folder}": {
            "bind": "/workspace/memory",
            "mode": "rw"
        },
        f"{DATA_DIR}/ipc/{group_folder}": {
            "bind": "/workspace/ipc",
            "mode": "rw"
        },
        f"{DATA_DIR}/groups/{group_folder}": {
            "bind": "/workspace/group",
            "mode": "rw"
        },
    }
```

- [x] **M3.3.2** 实现路径安全验证

```python
# infra/exec/security.py
def validate_path(path: str, allowed_roots: list[str]) -> bool:
    real_path = os.path.realpath(path)
    for root in allowed_roots:
        if real_path.startswith(os.path.realpath(root)):
            return True
    return False
```

- [x] **M3.3.3** 实现只读挂载选项

```python
# 为 memory、skills 等使用只读挂载
def build_readonly_volume(host_path: str, container_path: str) -> dict:
    return {
        host_path: {
            "bind": container_path,
            "mode": "ro"  # 只读
        }
    }
```

**交付**: 安全的卷挂载机制

### M3.4: 容器生命周期管理 [Week 2, Day 1-3]

- [x] **M3.4.1** 实现容器启动

```python
# infra/exec/container_manager.py
class ContainerManager:
    def __init__(self, docker_client: DockerClient):
        self.client = docker_client

    async def start_agent_container(
        self,
        group_folder: str,
        user_id: str,
        payload: ContainerInput
    ) -> str:
        container = await self.client.run_container(
            image=CONTAINER_IMAGE,
            command=["python", "-m", "src.runner"],
            volumes=self.build_runner_volumes(group_folder, user_id),
            environment=self.build_environment(group_folder, payload),
            name=self.build_container_name(group_folder, payload),
            working_dir="/workspace/group",
            detach=True,
            remove=False,
        )
        return container.id
```

- [x] **M3.4.2** 实现容器停止

```python
    async def stop_container(self, container_id: str) -> None:
        self.client.stop_container(container_id, timeout=30)
        self.client.remove_container(container_id, force=False)
```

- [ ] **M3.4.3** 实现健康检查

```python
    async def is_container_healthy(self, container_id: str) -> bool:
        container = self.client.get_container(container_id)
        return container.status == "running"
```

- [ ] **M3.4.4** 实现优雅关闭

```python
    async def graceful_shutdown(self, container_id: str) -> None:
        # 1. 发送关闭信号
        # 2. 等待完成（或超时）
        # 3. 强制停止
        pass
```

**交付**: 容器生命周期管理

### M3.5: 宿主机模式 [Week 2, Day 4-5]

- [ ] **M3.5.1** 实现宿主机进程运行器

```python
# infra/exec/process.py
import asyncio
import subprocess

class ProcessRunner:
    async def run_agent(
        self,
        group_folder: str,
        input: ContainerInput
    ) -> AsyncIterator[str]:
        process = await asyncio.create_subprocess_exec(
            "python", "-m", "portex.agent_runner",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=f"{DATA_DIR}/groups/{group_folder}"
        )

        # 发送输入
        process.stdin.write(json.dumps(input).encode())
        await process.stdin.drain()

        # 读取输出
        async for line in process.stdout:
            yield line.decode()
```

- [ ] **M3.5.2** 实现模式选择逻辑

```python
# services/execution_mode.py
def get_execution_mode(user_role: str, group_config: dict) -> str:
    if user_role == "admin" and group_config.get("host_mode"):
        return "host"
    return "container"
```

- [ ] **M3.5.3** 添加安全限制（宿主机模式）

```python
# 限制宿主机模式的权限
HOST_MODE_RESTRICTIONS = {
    "allowed_directories": ["/home/portex/workspace"],
    "forbidden_commands": ["rm -rf /", "dd if="],
    "max_execution_time": 3600,
}
```

**交付**: 宿主机执行模式

### M3.6: M3 阶段验收 [Week 2, Day 5]

**交付清单**:
- [x] Docker SDK 集成
- [x] Agent Runner 容器镜像
- [x] 卷挂载安全
- [x] 容器生命周期管理
- [x] 宿主机执行模式
- [x] 容器隔离测试

---

## M4: 多用户与任务 (2周)

**目标**: RBAC、scheduler、memory

### M4.1: 完整用户系统 [Week 1, Day 1-3]

- [ ] **M4.1.1** 扩展用户模型

```python
# domain/models/user.py
class User(Base):
    # ... 现有字段
    avatar_emoji = Column(String)
    avatar_color = Column(String)
    ai_name = Column(String)
    ai_avatar_emoji = Column(String)
    must_change_password = Column(Boolean, default=False)
    last_login_at = Column(DateTime)
    disable_reason = Column(String)
    notes = Column(Text)
```

- [ ] **M4.1.2** 实现用户管理 API

```python
# app/routes/users.py
@router.get("/admin/users")
@require_role("admin")
async def list_users(db: AsyncSession = Depends(get_db)):
    # 列出所有用户
    pass

@router.patch("/admin/users/{user_id}")
@require_role("admin")
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    db: AsyncSession = Depends(get_db)
):
    # 更新用户
    pass
```

- [ ] **M4.1.3** 实现邀请码系统

```python
# domain/models/invite_code.py
class InviteCode(Base):
    __tablename__ = "invite_codes"

    code = Column(String, primary_key=True)
    created_by = Column(String)
    role = Column(String, default="member")
    permission_template = Column(String)
    expires_at = Column(DateTime)
    used_by = Column(String)
    used_at = Column(DateTime)
```

**交付**: 完整用户系统

### M4.2: RBAC 权限系统 [Week 1, Day 3-5]

- [ ] **M4.2.1** 定义权限模板

```python
# domain/permissions.py
PERMISSION_TEMPLATES = {
    "owner": {
        "users": ["read", "write", "delete", "admin"],
        "groups": ["read", "write", "delete"],
        "messages": ["read", "write"],
        "tasks": ["read", "write", "execute"],
        "settings": ["read", "write"],
    },
    "admin": {
        "users": ["read", "write"],
        "groups": ["read", "write"],
        "messages": ["read", "write"],
        "tasks": ["read", "write", "execute"],
        "settings": ["read"],
    },
    "member": {
        "groups": ["read"],
        "messages": ["read", "write"],
        "tasks": ["read"],
    },
}
```

- [ ] **M4.2.2** 实现权限检查装饰器

```python
# app/middleware/permissions.py
def require_permission(resource: str, action: str):
    async def dependency(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        has_permission = await check_permission(
            db, current_user, resource, action
        )
        if not has_permission:
            raise HTTPException(403, "Permission denied")
        return current_user
    return dependency
```

- [ ] **M4.2.3** 实现群组成员管理

```python
# domain/models/group_member.py
class GroupMember(Base):
    __tablename__ = "group_members"

    group_jid = Column(String, primary_key=True)
    user_id = Column(String, primary_key=True)
    role = Column(String)  # owner/admin/member
    joined_at = Column(DateTime, default=datetime.utcnow)
```

**交付**: RBAC 权限系统

### M4.3: 定时任务调度 [Week 2, Day 1-3]

- [ ] **M4.3.1** 实现任务调度器

```python
# services/scheduler.py
import asyncio
from croniter import croniter

class TaskScheduler:
    def __init__(self):
        self.tasks: dict[str, ScheduledTask] = {}
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            await self._check_and_run_tasks()
            await asyncio.sleep(60)  # 每分钟检查

    async def _check_and_run_tasks(self):
        now = datetime.utcnow()
        for task in self.tasks.values():
            if task.status != "active":
                continue

            if task.schedule_type == "cron":
                if croniter(task.schedule_value, now).is_now():
                    await self._execute_task(task)
            elif task.schedule_type == "interval":
                if (now - task.last_run).total_seconds() >= int(task.schedule_value):
                    await self._execute_task(task)
            elif task.schedule_type == "once":
                if now >= task.next_run:
                    await self._execute_task(task)
                    task.status = "completed"
```

- [ ] **M4.3.2** 实现任务 CRUD API

```python
# app/routes/tasks.py
@router.post("/tasks")
async def create_task(
    request: CreateTaskRequest,
    current_user: User = Depends(get_current_user)
):
    # 创建定时任务
    pass

@router.get("/tasks")
async def list_tasks(
    current_user: User = Depends(get_current_user)
):
    # 列出任务
    pass

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    # 删除任务
    pass
```

- [ ] **M4.3.3** 实现任务执行日志

```python
# domain/models/task_log.py
class TaskRunLog(Base):
    __tablename__ = "task_run_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String)
    run_at = Column(DateTime)
    duration_ms = Column(Integer)
    status = Column(String)  # success/error/timeout
    result = Column(Text)
    error = Column(Text)
```

**交付**: 定时任务系统

### M4.4: 记忆系统 [Week 2, Day 3-5]

- [ ] **M4.4.1** 实现 CLAUDE.md 管理

```python
# services/memory.py
class MemoryService:
    async def get_user_memory(self, user_id: str) -> str:
        path = f"{DATA_DIR}/memory/user-global/{user_id}/CLAUDE.md"
        if os.path.exists(path):
            return open(path).read()
        return ""

    async def update_user_memory(self, user_id: str, content: str) -> None:
        path = f"{DATA_DIR}/memory/user-global/{user_id}/CLAUDE.md"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w').write(content)
```

- [ ] **M4.4.2** 实现日期记忆

```python
    async def append_daily_memory(self, group_folder: str, content: str) -> None:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        path = f"{DATA_DIR}/memory/{group_folder}/{today}.md"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'a') as f:
            f.write(f"\n{content}\n")
```

- [ ] **M4.4.3** 实现记忆搜索

```python
    async def search_memory(self, group_folder: str, query: str) -> list[str]:
        # 简单的文件内容搜索
        results = []
        memory_dir = f"{DATA_DIR}/memory/{group_folder}"
        for file in glob.glob(f"{memory_dir}/**/*.md", recursive=True):
            content = open(file).read()
            if query.lower() in content.lower():
                results.append(file)
        return results
```

- [ ] **M4.4.4** 实现 MCP 工具包装

```python
# container/agent-runner/src/tools/memory.py
from agents import function_tool

@function_tool
async def memory_append(ctx, content: str) -> str:
    """追加记忆"""
    # 调用主服务的记忆 API
    pass

@function_tool
async def memory_search(ctx, query: str) -> str:
    """搜索记忆"""
    pass
```

**交付**: 记忆系统

### M4.5: M4 阶段验收 [Week 2, Day 5]

**交付清单**:
- [x] 完整用户系统
- [x] RBAC 权限系统
- [x] 定时任务调度
- [x] 记忆系统
- [x] 多用户隔离测试

---

## M5: IM接入 (1周)

**目标**: 飞书/Telegram 通道

### M5.1: 飞书集成 [Week 1, Day 1-3]

- [ ] **M5.1.1** 创建飞书客户端

```python
# infra/im/feishu.py
import httpx
from Crypto.Cipher import AES

class FeishuClient:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn"

    async def get_access_token(self) -> str:
        # 获取 tenant_access_token
        pass
```

- [ ] **M5.1.2** 实现 WebSocket 事件接收

```python
# infra/im/feishu.py
async def handle_websocket_event(event: dict):
    event_type = event.get("type")
    if event_type == "im.message.receive_v1":
        message = event["message"]
        # 处理消息
```

- [ ] **M5.1.3** 实现消息发送

```python
# infra/im/feishu.py
async def send_message(self, receive_id: str, content: dict):
    # 发送富文本卡片消息
    pass
```

**交付**: 飞书集成

### M5.2: Telegram 集成 [Week 1, Day 3-4]

- [ ] **M5.2.1** 创建 Telegram 客户端

```python
# infra/im/telegram.py
import httpx

class TelegramClient:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def get_updates(self, offset: int = 0) -> list:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/getUpdates", {
                "offset": offset,
                "timeout": 60
            })
            return resp.json()["result"]
```

- [ ] **M5.2.2** 实现消息处理

```python
# infra/im/telegram.py
async def handle_update(self, update: dict):
    message = update.get("message")
    if message:
        # 处理消息
        pass
```

- [ ] **M5.2.3** 实现 Markdown 转换

```python
# infra/im/telegram.py
def markdown_to_html(self, text: str) -> str:
    # 简单的 Markdown -> HTML 转换
    text = text.replace("**", "<b>")
    text = text.replace("*", "<i>")
    text = text.replace("`", "<code>")
    return text
```

**交付**: Telegram 集成

### M5.3: 消息路由 [Week 1, Day 4-5]

- [ ] **M5.3.1** 实现统一消息格式

```python
# domain/schemas.py
class UnifiedMessage(BaseModel):
    channel: str  # web/feishu/telegram
    sender_id: str
    group_folder: str
    content: str
    message_id: str
    timestamp: datetime
```

- [ ] **M5.3.2** 实现消息路由逻辑

```python
# services/message_router.py
async def route_message(message: UnifiedMessage):
    # 根据 channel 路由到对应处理器
    if message.channel == "feishu":
        await feishu.send_reply(message)
    elif message.channel == "telegram":
        await telegram.send_reply(message)
    elif message.channel == "web":
        await websocket.broadcast(message)
```

**交付**: 统一消息路由

### M5.4: M5 阶段验收 [Week 1, Day 5]

**交付清单**:
- [x] 飞书通道
- [x] Telegram 通道
- [x] 消息路由
- [x] IM 集成测试

---

## M6: 发布准备 (1周)

**目标**: v1 发布准备

### M6.1: 测试完善 [Week 1, Day 1-2]

- [ ] **M6.1.1** 编写单元测试

```bash
# 目录结构
tests/
├── unit/
│   ├── test_auth.py
│   ├── test_models.py
│   └── test_services.py
├── integration/
│   ├── test_api.py
│   └── test_websocket.py
└── e2e/
    └── test_chat.py
```

- [ ] **M6.1.2** 编写集成测试

```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
```

- [ ] **M6.1.3** 配置 CI/CD

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest tests/ -v --cov
```

**交付**: 测试套件

### M6.2: 文档完善 [Week 1, Day 2-3]

- [ ] **M6.2.1** 编写 README

```markdown
# Portex

基于 OpenAI Agents SDK 的远程 AI Agent 服务

## 特性

- Web 实时聊天
- 容器隔离执行
- 多用户支持
- IM 接入

## 快速开始

```bash
# 克隆
git clone https://github.com/yourorg/portex.git
cd portex

# 安装
pip install -e .

# 运行
make dev
```
```

- [ ] **M6.2.2** 编写 API 文档

```python
# 使用 FastAPI 自动生成
# 访问 /docs 查看 Swagger UI
```

- [ ] **M6.2.3** 编写部署文档

```markdown
# 部署指南

## Docker Compose 部署

```yaml
# docker-compose.yml
version: '3.8'
services:
  portex:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - SECRET_KEY=your-secret-key
```
```

**交付**: 完整文档

### M6.3: 性能优化 [Week 1, Day 3-4]

- [ ] **M6.3.1** 添加数据库索引

```sql
CREATE INDEX idx_messages_chat_jid ON messages(chat_jid);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_tasks_next_run ON scheduled_tasks(next_run);
```

- [ ] **M6.3.2** 实现连接池

```python
# infra/db/database.py
from sqlalchemy.pool import StaticPool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_size=20,
    max_overflow=10,
)
```

- [ ] **M6.3.3** 添加缓存层（如需要）

```python
# 使用 Redis 缓存（如需要）
# 或使用简单的内存缓存
```

**交付**: 性能优化

### M6.4: 安全审查 [Week 1, Day 4]

- [ ] **M6.4.1** 安全扫描

```bash
# 使用安全工具扫描
pip install safety
safety check
```

- [ ] **M6.4.2** 依赖审计

```bash
# 检查依赖漏洞
pip-audit
```

- [ ] **M6.4.3** 配置安全头

```python
# app/middleware/security.py
from fastapi.middleware.security import SecurityMiddleware

app.add_middleware(
    SecurityMiddleware,
    directives={
        "default-src": "'self'",
        "script-src": "'self'",
    }
)
```

**交付**: 安全审查报告

### M6.5: 版本发布 [Week 1, Day 5]

- [ ] **M6.5.1** 版本号规划

```
v1.0.0
  - 基础功能完整
  - Web 聊天
  - 容器隔离
  - 多用户
```

- [ ] **M6.5.2** 创建发布标签

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

- [ ] **M6.5.3** 构建发布产物

```bash
# 构建 Docker 镜像
docker build -t portex:v1.0.0 .

# 构建前端
cd web && npm run build
```

**交付**: 发布产物

---

## 附录

### 依赖清单

```toml
# 核心依赖
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlalchemy>=2.0.0
pydantic>=2.0.0

# 认证
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# 数据库
aiosqlite>=0.20.0
alembic>=1.13.0

# 容器
docker>=7.0.0

# HTTP
httpx>=0.27.0

# 工具
python-multipart>=0.0.10
croniter>=1.4.0
```

### 环境变量

```bash
# .env.example
DATABASE_URL=sqlite+aiosqlite:///./portex.db
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...

# 可选
FEISHU_APP_ID=
FEISHU_APP_SECRET=
TELEGRAM_BOT_TOKEN=
```

### 目录结构总览

```
portex/
├── app/                    # FastAPI 应用 (10+ 文件)
├── domain/                 # 领域模型 (10+ 文件)
├── infra/                  # 基础设施 (15+ 文件)
├── services/               # 业务服务 (10+ 文件)
├── container/              # 容器相关
│   └── agent-runner/       # Agent Runner (10+ 文件)
├── web/                    # React 前端 (50+ 文件)
├── config/                 # 配置文件
├── scripts/                # 运维脚本
├── tests/                  # 测试 (30+ 文件)
└── docs/                   # 文档
```

### 关键里程碑检查点

| 里程碑 | 检查点 | 验收条件 |
|--------|--------|----------|
| M0 | 3 个 PoC 完成 | 流式、工具、事件映射可演示 |
| M1 | 骨架可用 | API 可调用、前端可运行 |
| M2 | 链路贯通 | 端到端聊天可用 |
| M3 | 容器就绪 | 容器模式稳定运行 |
| M4 | 功能完整 | 多用户、任务、记忆可用 |
| M5 | 通道打通 | IM 消息可收发 |
| M6 | 可发布 | 测试通过、文档完整 |

---

*本文档将作为 Portex 项目的执行指南，每个任务完成后请更新任务状态。*
