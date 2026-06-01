#!/usr/bin/env python3
"""Runtime prompt fragment tests."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from under_one import ContextGuard, PersonaGuard, PriorityEngine
from under_one.runtime_prompt import (
    RuntimePromptCompiler,
    RuntimePromptFragment,
    append_runtime_directives_to_messages,
    compile_runtime_prompt_messages,
)


def test_runtime_prompt_compiler_orders_dedupes_and_decays():
    compiler = RuntimePromptCompiler(max_fragments=2, max_chars=240)
    compiler.ingest(
        [
            RuntimePromptFragment(
                source_skill="qiti-yuanliu",
                priority=2,
                condition="entropy=4",
                directive="[ENTROPY-WARN] 先对齐目标。",
                ttl_rounds=2,
            ),
            RuntimePromptFragment(
                source_skill="shuangquanshou",
                priority=1,
                condition="dna_violation",
                directive="[PERSONA-GUARD] 保持核心人格边界。",
                ttl_rounds=3,
            ),
            RuntimePromptFragment(
                source_skill="qiti-yuanliu",
                priority=3,
                condition="alignment=80",
                directive="[DRIFT] 回归主线。",
                ttl_rounds=3,
            ),
        ]
    )

    compiled = compiler.compile(current_round=5)

    assert compiled.startswith("\n\n[Runtime Directives]")
    assert compiled.index("[PERSONA-GUARD]") < compiled.index("[ENTROPY-WARN]")
    assert "[DRIFT]" not in compiled
    active = compiler.active_fragments()
    assert any(item["source_skill"] == "shuangquanshou" for item in active)
    assert all(item["ttl_rounds"] >= 1 for item in active)


def test_append_runtime_directives_to_messages_extends_system_message():
    messages = [
        {"role": "system", "content": "Base system."},
        {"role": "user", "content": "Hello"},
    ]
    updated = append_runtime_directives_to_messages(messages, "\n\n[Runtime Directives]\n[DRIFT] 回归主线。")

    assert updated[0]["role"] == "system"
    assert "Base system." in updated[0]["content"]
    assert "[DRIFT]" in updated[0]["content"]
    assert messages[0]["content"] == "Base system."


def test_compile_runtime_prompt_messages_creates_system_message_when_missing():
    updated = compile_runtime_prompt_messages(
        [{"role": "user", "content": "Hello"}],
        [
            {
                "source_skill": "qiti-yuanliu",
                "priority": 1,
                "condition": "entropy=9",
                "directive": "[ENTROPY-CRITICAL] 先梳理共识。",
                "ttl_rounds": 3,
            }
        ],
        current_round=1,
    )

    assert updated[0]["role"] == "system"
    assert "[ENTROPY-CRITICAL]" in updated[0]["content"]
    assert updated[1]["role"] == "user"


def test_context_guard_emits_runtime_prompt_fragments():
    result = ContextGuard().run(
        [
            {"role": "user", "content": "我们先用 React。", "round": 1},
            {"role": "assistant", "content": "好的，前端采用 React。", "round": 2},
            {"role": "user", "content": "不对，改成 Vue。", "round": 3},
            {"role": "assistant", "content": "已切换为 Vue。", "round": 4},
        ]
    )

    fragments = result["runtime_prompt_fragments"]
    assert fragments
    assert any(item["source_skill"] == "qiti-yuanliu" for item in fragments)
    assert any("[HANDOFF]" in item["directive"] or "[CONTEXT-ALERT]" in item["directive"] for item in fragments)

    compiler = RuntimePromptCompiler()
    compiler.ingest(fragments)
    assert "[Runtime Directives]" in compiler.compile(current_round=4)


def test_persona_guard_emits_guard_fragment_on_violation():
    result = PersonaGuard().run(
        [
            {"style": "formal", "tone": 3, "formality": 4, "detail_level": 3, "structure": 4},
            {"style": "casual", "tone": 2, "formality": 2, "detail_level": 2, "structure": 2},
            {"style": "technical", "tone": 5, "formality": 5, "detail_level": 4, "structure": 5},
        ]
    )

    fragments = result["runtime_prompt_fragments"]
    assert any(item["source_skill"] == "shuangquanshou" for item in fragments)
    assert any("[PERSONA-GUARD]" in item["directive"] for item in fragments)


def test_priority_engine_emits_robustness_or_dead_gate_fragment():
    result = PriorityEngine().run(
        [
            {"name": "修复生产故障", "urgency": 5, "importance": 5, "dependency": 4, "resource_match": 4},
            {"name": "整理文档", "urgency": 1, "importance": 1, "dependency": 1, "resource_match": 1},
        ]
    )

    fragments = result["runtime_prompt_fragments"]
    assert any(item["source_skill"] == "fenghou-qimen" for item in fragments)
