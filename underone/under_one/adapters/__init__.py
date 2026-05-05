"""
LLM 适配层 — 统一不同 LLM 提供商的调用接口

使用方法：
    from under_one.adapters import get_client
    client = get_client()  # 自动按环境变量选择
    response = client.complete("你好")

支持的 provider：
    - openai    (需要 OPENAI_API_KEY)
    - anthropic (需要 ANTHROPIC_API_KEY)
    - mock      (无需 API key，用于测试与本地开发)

环境变量优先级：
    UNDERONE_LLM_PROVIDER > OPENAI_API_KEY/ANTHROPIC_API_KEY 自动探测 > mock
"""

from .base import LLMClient, LLMResponse, LLMError
from .mock import MockClient
from .registry import get_client, register_client, available_providers

__all__ = [
    "LLMClient",
    "LLMResponse",
    "LLMError",
    "MockClient",
    "get_client",
    "register_client",
    "available_providers",
]
