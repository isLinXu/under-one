"""LLM 适配层单元测试（仅依赖 mock，不发真实网络请求）。"""

import os

import pytest

from under_one.adapters import (
    LLMError,
    LLMResponse,
    MockClient,
    available_providers,
    get_client,
)


def test_mock_complete_returns_response():
    c = MockClient(latency_ms=0)
    resp = c.complete("请给任务排个优先级")
    assert isinstance(resp, LLMResponse)
    assert resp.provider == "mock"
    assert "优先级" in resp.content
    assert resp.total_tokens == resp.prompt_tokens + resp.completion_tokens


def test_mock_deterministic():
    c = MockClient(latency_ms=0)
    r1 = c.complete("hello world")
    r2 = c.complete("hello world")
    assert r1.content == r2.content


def test_mock_chat_uses_last_user_message():
    c = MockClient(latency_ms=0)
    resp = c.chat(
        [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
            {"role": "user", "content": "帮我总结一下"},
        ]
    )
    assert "摘要" in resp.content or "[mock" in resp.content


def test_get_client_defaults_to_mock_when_no_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("UNDERONE_LLM_PROVIDER", raising=False)
    c = get_client()
    assert c.provider == "mock"


def test_get_client_respects_explicit_provider():
    c = get_client(provider="mock")
    assert c.provider == "mock"


def test_get_client_raises_on_unknown_provider():
    with pytest.raises(LLMError):
        get_client(provider="no-such-provider")


def test_available_providers_includes_mock():
    providers = available_providers()
    assert "mock" in providers
