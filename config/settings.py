"""
Load and validate configuration from .env / environment variables.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    """
    Application settings loaded from .env or environment.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Default model provider when not specified
    default_provider: str = "deepseek"

    # Workspace directory for external knowledge base (future)
    workspace_dir: str = ""

    # Database
    database_url: str = ""
    chroma_path: str = ".chroma"

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

    # ZhipuAI (GLM)
    zhipuai_api_key: str
    zhipuai_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    zhipuai_basic_model: str = "glm-5-turbo"
    zhipuai_advanced_model: str = "glm-5.1"

    # Qwen (DashScope)
    dashscope_api_key: str
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_basic_model: str = "qwen3.6-35b-a3b"
    dashscope_advanced_model: str = "qwen3.6-plus"

    # Tavily
    tavily_api_key: str

    # Lightweight model for web fetch summarization
    web_fetch_summarize_model: str = "deepseek-chat"
    web_fetch_summarize_model_api_key: str | None = None
    web_fetch_summarize_model_base_url: str | None = None

    # LangSmith
    langsmith_tracing: bool = True
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str | None = None
    langsmith_project: str = "my_code_agent"


_langsmith_initialized = False


def setup_langsmith_tracing():
    """
    Enable LangSmith auto-tracing (idempotent).
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
    Print all settings, masking API keys.
    """
    for k, v in settings.model_dump().items():
        if "api_key" in k and v:
            v = v[:10] + "..."
        print(f"{k}: {v}")
