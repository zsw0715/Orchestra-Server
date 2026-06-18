"""
FastAPI application entry point — lifecycle, middleware, routes.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import setup_langsmith_tracing
from server import graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.

    Initialises global resources once, yields to hold the app running.
    Resources include:
      - AI Agent graph
      - Database / Redis connections (future: Human-in-the-Loop approval state,
        distributed locks for multi-agent file editing)
      - Persistent checkpointer
      - Global logging / tracing (LangSmith)
    """
    setup_langsmith_tracing()
    yield


app = FastAPI(title="The Orchestra", lifespan=lifespan)

# Allow all origins during development; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    if graph is None:
        return {"status": "error", "message": "Graph not initialized"}
    return {"status": "ok", "graph_ready": graph is not None}
