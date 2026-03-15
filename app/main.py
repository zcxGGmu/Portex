"""FastAPI application entrypoint for Portex."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import setup_logging
from app.middleware import SecurityHeadersMiddleware
from app.openapi import OPENAPI_DESCRIPTION, OPENAPI_TAGS
from app.routes import (
    auth,
    executions,
    files,
    groups,
    health,
    im,
    mcp_servers,
    memory,
    messages,
    monitor,
    settings,
    skills,
    tasks,
    users,
    websocket,
)


setup_logging()

app = FastAPI(
    title="Portex",
    version="0.1.0",
    description=OPENAPI_DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(health.router)
app.include_router(monitor.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(groups.router)
app.include_router(files.router)
app.include_router(memory.router)
app.include_router(skills.router)
app.include_router(mcp_servers.router)
app.include_router(settings.router)
app.include_router(im.router)
app.include_router(executions.router)
app.include_router(messages.router)
app.include_router(tasks.router)
app.include_router(websocket.router)
