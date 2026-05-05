"""
Anthropic (Claude) 适配器。

使用：
    export ANTHROPIC_API_KEY=sk-ant-...
    export UNDERONE_LLM_PROVIDER=anthropic           # 可选，显式选择
    export UNDERONE_ANTHROPIC_MODEL=claude-sonnet-4  # 可选

依赖（按需）：
    pip install anthropic
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from .base import LLMClient, LLMError, LLMResponse

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class AnthropicClient(LLMClient):
    provider = "anthropic"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or os.environ.get("UNDERONE_ANTHROPIC_MODEL", DEFAULT_MODEL)
        self.timeout = timeout
        if not self.api_key:
            raise LLMError("ANTHROPIC_API_KEY 未设置")
        self._client = self._build_client()

    def _build_client(self):
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise LLMError(
                "缺少 anthropic 依赖。请执行: pip install anthropic"
            ) from e
        return Anthropic(api_key=self.api_key, timeout=self.timeout)

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        start = time.time()
        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
        except Exception as e:
            raise LLMError(f"Anthropic 调用失败: {e}") from e
        elapsed = (time.time() - start) * 1000
        content = "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
        usage = getattr(resp, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        return LLMResponse(
            content=content,
            provider=self.provider,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=elapsed,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else {},
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> LLMResponse:
        system = next(
            (m["content"] for m in messages if m.get("role") == "system"), None
        )
        conv = [m for m in messages if m.get("role") != "system"]
        start = time.time()
        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system or "",
                messages=conv,
                **kwargs,
            )
        except Exception as e:
            raise LLMError(f"Anthropic 调用失败: {e}") from e
        elapsed = (time.time() - start) * 1000
        content = "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
        usage = getattr(resp, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        return LLMResponse(
            content=content,
            provider=self.provider,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=elapsed,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else {},
        )
