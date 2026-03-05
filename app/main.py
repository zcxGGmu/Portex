"""FastAPI application entrypoint for Portex."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import setup_logging

setup_logging()

app = FastAPI(title="Portex", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health endpoint used by probes and local checks."""
    return {"status": "ok"}
