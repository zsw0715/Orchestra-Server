"""
FastAPI 应用入口，配置应用生命周期管理器、路由、中间件等。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import setup_langsmith_tracing
from server import shared

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器，初始化和关闭全局资源。
    全局资源只需要一次初始化, yield 卡住应用运行，避免重复创建。
    全局资源有：
        - 创建 AI Agent 图
        - 数据库连接, Redis 连接 (future phase: 记录 Human-in-the-Loop 审批状态, 记录工具执行结果) // 对于 multi-agent 来说，redis 可以有分布式锁，确保不会有两个 agent 同时编辑处理同一个文件
        - 初始化持久化存储 (checkpointer)
        - 配置全局日志、追踪 (LangSmith)
    """
    setup_langsmith_tracing()
    yield


app = FastAPI(title="The Orchestra", lifespan=lifespan)


# 开发环境允许所有来源的 CORS 请求，之后切换生产环境后限制为指定的来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 路由配置
# app.include_router(__rooter__, prefix="__path__")


@app.get("/api/health")
async def health():
    """
    健康检查接口，返回当前应用状态。
    """
    if shared.graph is None:
        return {"status": "error", "message": "Graph not initialized"}
    return {"status": "ok", "graph_ready": shared.graph is not None}
