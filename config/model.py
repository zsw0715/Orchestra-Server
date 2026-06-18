"""
Model configuration — create ChatOpenAI instances by provider detection.
"""
from langchain_openai import ChatOpenAI
from config.settings import settings

_default_model = None


# ============================================================
# Internal
# ============================================================
def detect_provider(model: str) -> str:
    """
    Infer provider from model name string.
    """
    m = model.lower()
    if "deepseek" in m:
        return "deepseek"
    if "kimi" in m or "moonshot" in m:
        return "kimi"
    if "glm" in m or "zhipu" in m:
        return "glm"
    if "qwen" in m or "dashscope" in m:
        return "qwen"
    return settings.default_provider.lower()


def _get_default_model() -> ChatOpenAI:
    """
    Lazy singleton — reuse across graph invocations.
    """
    global _default_model
    if _default_model is None:
        _default_model = init_chat_model()
    return _default_model


# ============================================================
# Public
# ============================================================
def init_model(
    model: str = "",
    temperature: float = 0.2,
    max_tokens: int = 4096,
    streaming: bool = True,
) -> ChatOpenAI:
    """
    Create a ChatOpenAI instance by inferring the provider from the model name.

    Nodes call this with state.orchestrator.model / state.sub_agents[i].model.
    Falls back to the default provider when model is empty.
    """
    if not model:
        provider = settings.default_provider.lower()
        selected = ""
    else:
        provider = detect_provider(model)
        selected = model

    match provider:
        case "deepseek":
            return ChatOpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=selected or settings.deepseek_basic_model,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
            )
        case "kimi":
            return ChatOpenAI(
                api_key=settings.moonshot_api_key,
                base_url=settings.moonshot_base_url,
                model=selected or settings.moonshot_basic_model,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
            )
        case "glm":
            return ChatOpenAI(
                api_key=settings.zhipuai_api_key,
                base_url=settings.zhipuai_base_url,
                model=selected or settings.zhipuai_basic_model,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
            )
        case "qwen":
            return ChatOpenAI(
                api_key=settings.dashscope_api_key,
                base_url=settings.dashscope_base_url,
                model=selected or settings.dashscope_basic_model,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
            )
        case _:
            raise ValueError(f"Unknown provider: {provider}")


def build_autogen_llm_config(model: str = "", temperature: float = 0.3) -> dict:
    """
    Build an autogen-compatible llm_config dict from our settings.

    Used by plan.py (and later write.py) to create AssistantAgent instances.
    """
    provider = detect_provider(model)
    match provider:
        case "deepseek":
            return {
                "config_list": [{
                    "model": model or settings.deepseek_basic_model,
                    "api_key": settings.deepseek_api_key,
                    "base_url": settings.deepseek_base_url,
                }],
                "temperature": temperature,
            }
        case "kimi":
            return {
                "config_list": [{
                    "model": model or settings.moonshot_basic_model,
                    "api_key": settings.moonshot_api_key,
                    "base_url": settings.moonshot_base_url,
                }],
                "temperature": temperature,
            }
        case "glm":
            return {
                "config_list": [{
                    "model": model or settings.zhipuai_basic_model,
                    "api_key": settings.zhipuai_api_key,
                    "base_url": settings.zhipuai_base_url,
                }],
                "temperature": temperature,
            }
        case "qwen":
            return {
                "config_list": [{
                    "model": model or settings.dashscope_basic_model,
                    "api_key": settings.dashscope_api_key,
                    "base_url": settings.dashscope_base_url,
                }],
                "temperature": temperature,
            }
        case _:
            raise ValueError(f"Unknown provider: {provider}")
