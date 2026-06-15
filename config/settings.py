"""
从 env 读配置、做类型校验
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    """应用配置类：从 .env 或环境变量加载配置"""
    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 默认路由模型 
    default_provider: str = "deepseek"

    # 工作区 -- 之后做外挂知识库用的
    workspace_dir: str = ""

    # 数据库
    database_url: str = ""
    chroma_path: str = ".chroma"  # Chroma 数据库路径，以后做外挂知识库用的

    # DeepSeek
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_basic_model: str = "deepseek-chat"
    deepseek_advanced_model: str = "deepseek-reasoner"

    # Kimi (Moonshot)
    moonshot_api_key: str
    moonshot_base_url: str = "https://api.moonshot.cn/v1"
    moonshot_basic_model: str = "kimi-k2.5"
    moonshot_advanced_model: str = "kimi-k2.6"

    # 智谱 GLM (ZhipuAI)
    zhipuai_api_key: str
    zhipuai_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    zhipuai_basic_model: str = "glm-5-turbo"
    zhipuai_advanced_model: str = "glm-5.1"

    # 通义千问 (DashScope)
    dashscope_api_key: str
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_basic_model: str = "qwen3.6-35b-a3b"
    dashscope_advanced_model: str = "qwen3.6-plus"

    # === Tavily ===
    tavily_api_key: str

    # === 其他 ===
    # 用于长网页提炼的轻量模型 配置
    web_fetch_summarize_model : str = "deepseek-chat"
    web_fetch_summarize_model_api_key: str | None = None
    web_fetch_summarize_model_base_url: str | None = None

    # LangSmith 配置
    langsmith_tracing: bool = True
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str | None = None
    langsmith_project: str = "my_code_agent"


_langsmith_initialized = False


def setup_langsmith_tracing():
    """
    设置 LangSmith 自动追踪，幂等，只执行一次
    """
    global _langsmith_initialized
    if _langsmith_initialized:
        return

    if settings.langsmith_api_key and settings.langsmith_tracing:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
        os.environ["LANGSMITH_TRACING"] = "true"
        print(f"LangSmith Auto Tracing Enabled: {settings.langsmith_project}")
    else:
        print("LangSmith Auto Tracing Disabled")

    _langsmith_initialized = True


settings = Settings()


if __name__ == "__main__":
    """
    打印所有配置项，隐藏 API 密钥
    """
    for k, v in settings.model_dump().items():
        if "api_key" in k and v:
            v = v[:10] + "..."
        print(f"{k}: {v}")
