"""
LLM 适配器注册表 + 自动选择逻辑。
"""

from __future__ import annotations

import os
from typing import Callable, Dict, List, Optional

from .base import LLMClient, LLMError
from .mock import MockClient


_REGISTRY: Dict[str, Callable[..., LLMClient]] = {
    "mock": MockClient,
}


def register_client(name: str, factory: Callable[..., LLMClient]) -> None:
    """注册自定义 provider。"""
    _REGISTRY[name] = factory


def available_providers() -> List[str]:
    """返回当前可用的 provider 列表（已能 import 的）。"""
    out = ["mock"]
    try:
        import openai  # noqa: F401

        out.append("openai")
    except ImportError:
        pass
    try:
        import anthropic  # noqa: F401

        out.append("anthropic")
    except ImportError:
        pass
    return out


def _lazy_openai() -> LLMClient:
    from .openai import OpenAIClient

    return OpenAIClient()


def _lazy_anthropic() -> LLMClient:
    from .anthropic import AnthropicClient

    return AnthropicClient()


_REGISTRY.setdefault("openai", _lazy_openai)
_REGISTRY.setdefault("anthropic", _lazy_anthropic)


def get_client(provider: Optional[str] = None, **kwargs) -> LLMClient:
    """获取 LLM client。

    选择顺序：
      1. 显式参数 `provider`
      2. 环境变量 `UNDERONE_LLM_PROVIDER`
      3. 环境变量自动探测（OPENAI_API_KEY → openai；ANTHROPIC_API_KEY → anthropic）
      4. 回退到 `mock`
    """
    name = provider or os.environ.get("UNDERONE_LLM_PROVIDER")
    if not name:
        if os.environ.get("OPENAI_API_KEY"):
            name = "openai"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            name = "anthropic"
        else:
            name = "mock"

    factory = _REGISTRY.get(name)
    if factory is None:
        raise LLMError(f"未知的 LLM provider: {name}。可用: {list(_REGISTRY)}")

    # 带参数的显式构造 vs 懒加载的默认构造
    try:
        return factory(**kwargs) if kwargs else factory()
    except TypeError:
        # 懒加载闭包不接受 kwargs
        return factory()
