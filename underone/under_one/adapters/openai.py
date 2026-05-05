"""
OpenAI 适配器。

使用：
    export OPENAI_API_KEY=sk-...
    export UNDERONE_LLM_PROVIDER=openai          # 可选，显式选择
    export UNDERONE_OPENAI_MODEL=gpt-4o-mini     # 可选，默认 gpt-4o-mini
    export UNDERONE_OPENAI_BASE_URL=https://...  # 可选，兼容 OpenAI 协议的自建/代理

依赖（按需）：
    pip install openai
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from .base import LLMClient, LLMError, LLMResponse

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIClient(LLMClient):
    provider = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("UNDERONE_OPENAI_MODEL", DEFAULT_MODEL)
        self.base_url = base_url or os.environ.get("UNDERONE_OPENAI_BASE_URL")
        self.timeout = timeout
        if not self.api_key:
            raise LLMError("OPENAI_API_KEY 未设置")
        self._client = self._build_client()

    def _build_client(self):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise LLMError(
                "缺少 openai 依赖。请执行: pip install openai"
            ) from e
        kwargs: Dict[str, Any] = {"api_key": self.api_key, "timeout": self.timeout}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return OpenAI(**kwargs)

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, max_tokens=max_tokens, temperature=temperature, **kwargs)

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> LLMResponse:
        start = time.time()
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )
        except Exception as e:
            raise LLMError(f"OpenAI 调用失败: {e}") from e
        elapsed = (time.time() - start) * 1000
        choice = resp.choices[0]
        usage = getattr(resp, "usage", None)
        return LLMResponse(
            content=choice.message.content or "",
            provider=self.provider,
            model=self.model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            total_tokens=getattr(usage, "total_tokens", 0) if usage else 0,
            latency_ms=elapsed,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else {},
        )
