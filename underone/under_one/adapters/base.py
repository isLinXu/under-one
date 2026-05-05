"""
LLM 适配层基类与数据结构。

所有 provider 实现都必须继承 LLMClient 并实现 `complete()`。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


class LLMError(Exception):
    """LLM 调用统一异常。skills 捕获此异常触发降级（对应拘灵遣将的 fallback）。"""


@dataclass
class LLMResponse:
    """LLM 响应的标准化封装。"""

    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.content


class LLMClient(Protocol):
    """所有 LLM 适配器的统一接口。

    子类应实现 `complete()`，可选实现 `chat()` 与 `embed()`。
    """

    provider: str
    model: str

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """同步调用 LLM 补全单次 prompt。

        Args:
            prompt: 用户输入。
            max_tokens: 响应最大 token 数。
            temperature: 采样温度 0~2。
            system: 可选的 system prompt。

        Returns:
            LLMResponse 对象，包含内容、token 统计与延迟。

        Raises:
            LLMError: 调用失败（网络/鉴权/配额）。
        """
        ...

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> LLMResponse:
        """多轮对话接口。messages = [{"role": "user|assistant|system", "content": "..."}, ...]"""
        ...
