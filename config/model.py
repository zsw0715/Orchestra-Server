"""
模型配置，提供初始化模型的函数
"""
from langchain_openai import ChatOpenAI
from config.settings import settings


def init_chat_model(provider: str | None = None) -> ChatOpenAI:
    """初始化模型"""
    if provider is None:
        provider = settings.default_provider.lower()

    match provider:
        case "deepseek":
            return ChatOpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_basic_model,
                streaming=True,
                temperature=0.2,
            )
        case "moonshot", "kimi":
            return ChatOpenAI(
                api_key=settings.moonshot_api_key,
                base_url=settings.moonshot_base_url,
                model=settings.moonshot_basic_model,
                streaming=True,
                temperature=0.2,
            )
        case "zhipuai", "glm":
            return ChatOpenAI(
                api_key=settings.zhipuai_api_key,
                base_url=settings.zhipuai_base_url,
                model=settings.zhipuai_basic_model,
                streaming=True,
                temperature=0.2,
            )
        case "dashscope", "qwen", "qwen3":
            return ChatOpenAI(
                api_key=settings.dashscope_api_key,
                base_url=settings.dashscope_base_url,
                model=settings.dashscope_basic_model,
                streaming=True,
                temperature=0.2,
            )
        case "chatgpt", "openai", "claude", "gemini", "grok":
            raise ValueError(f"Provider {provider} is not supported")
        case _:
            raise ValueError(f"Unknown provider: {provider}")


_default_model = None             # 全局单例（图内复用，不要每次节点调用都 new）

def get_default_model() -> ChatOpenAI:
    """懒加载全局默认模型"""
    global _default_model
    if _default_model is None:
        _default_model = init_chat_model()
    return _default_model
