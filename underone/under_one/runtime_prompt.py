"""Runtime System Prompt fragments and compiler.

Skills diagnose runtime state; this module turns those diagnoses into short,
bounded system-prompt directives that an agent runtime can inject before an LLM
call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union


@dataclass
class RuntimePromptFragment:
    """A short runtime directive produced by a skill."""

    source_skill: str
    priority: int
    condition: str
    directive: str
    ttl_rounds: int = 3
    expires_at: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.priority = max(1, min(5, int(self.priority)))
        self.ttl_rounds = max(1, int(self.ttl_rounds))
        self.directive = str(self.directive).strip()
        self.condition = str(self.condition).strip()
        self.source_skill = str(self.source_skill).strip()

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            "source_skill": self.source_skill,
            "priority": self.priority,
            "condition": self.condition,
            "directive": self.directive,
            "ttl_rounds": self.ttl_rounds,
            "expires_at": self.expires_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RuntimePromptFragment":
        """Build a fragment from a dict payload."""

        return cls(
            source_skill=str(payload.get("source_skill", "unknown")),
            priority=int(payload.get("priority", 5)),
            condition=str(payload.get("condition", "")),
            directive=str(payload.get("directive", "")),
            ttl_rounds=int(payload.get("ttl_rounds", 3)),
            expires_at=payload.get("expires_at"),
            metadata=dict(payload.get("metadata") or {}),
        )


FragmentLike = Union[RuntimePromptFragment, Dict[str, Any]]


def coerce_fragment(fragment: FragmentLike) -> RuntimePromptFragment:
    """Normalize a dict/dataclass fragment into a RuntimePromptFragment."""

    if isinstance(fragment, RuntimePromptFragment):
        return fragment
    if isinstance(fragment, dict):
        return RuntimePromptFragment.from_dict(fragment)
    raise TypeError(f"Unsupported runtime prompt fragment: {type(fragment)!r}")


def fragments_to_dicts(fragments: Iterable[FragmentLike]) -> List[Dict[str, Any]]:
    """Convert fragments to JSON-friendly dicts, dropping empty directives."""

    out: List[Dict[str, Any]] = []
    for fragment in fragments:
        normalized = coerce_fragment(fragment)
        if normalized.directive:
            out.append(normalized.to_dict())
    return out


class FragmentConflictResolver:
    """Resolve duplicate or conflicting runtime prompt fragments conservatively."""

    def resolve(self, fragments: Sequence[FragmentLike]) -> List[RuntimePromptFragment]:
        normalized = [coerce_fragment(fragment) for fragment in fragments]

        by_source: Dict[str, RuntimePromptFragment] = {}
        for fragment in normalized:
            existing = by_source.get(fragment.source_skill)
            if existing is None or self._is_stronger(fragment, existing):
                by_source[fragment.source_skill] = fragment

        deduped: Dict[str, RuntimePromptFragment] = {}
        for fragment in by_source.values():
            key = fragment.directive.strip()
            existing = deduped.get(key)
            if existing is None or self._is_stronger(fragment, existing):
                deduped[key] = fragment

        return sorted(deduped.values(), key=lambda item: (item.priority, item.source_skill))

    @staticmethod
    def _is_stronger(candidate: RuntimePromptFragment, existing: RuntimePromptFragment) -> bool:
        if candidate.priority != existing.priority:
            return candidate.priority < existing.priority
        return candidate.ttl_rounds > existing.ttl_rounds


class FragmentLifecycleManager:
    """Apply TTL expiry and non-critical priority decay after each turn."""

    def tick(
        self,
        fragments: Sequence[FragmentLike],
        *,
        current_round: int,
        decay_priority: bool = True,
    ) -> List[RuntimePromptFragment]:
        alive: List[RuntimePromptFragment] = []
        for fragment_like in fragments:
            fragment = coerce_fragment(fragment_like)
            if fragment.expires_at is not None and current_round >= fragment.expires_at:
                continue
            remaining_ttl = fragment.ttl_rounds - 1
            if remaining_ttl <= 0:
                continue
            next_priority = fragment.priority
            if decay_priority and next_priority > 1:
                next_priority = min(5, next_priority + 1)
            alive.append(
                RuntimePromptFragment(
                    source_skill=fragment.source_skill,
                    priority=next_priority,
                    condition=fragment.condition,
                    directive=fragment.directive,
                    ttl_rounds=remaining_ttl,
                    expires_at=fragment.expires_at,
                    metadata=fragment.metadata,
                )
            )
        return alive


class RuntimePromptCompiler:
    """Compile active fragments into a bounded system prompt directive block."""

    def __init__(
        self,
        max_fragments: int = 5,
        max_chars: int = 800,
        *,
        resolver: Optional[FragmentConflictResolver] = None,
        lifecycle: Optional[FragmentLifecycleManager] = None,
    ) -> None:
        self.max_fragments = max(1, int(max_fragments))
        self.max_chars = max(1, int(max_chars))
        self.fragments: List[RuntimePromptFragment] = []
        self.resolver = resolver or FragmentConflictResolver()
        self.lifecycle = lifecycle or FragmentLifecycleManager()

    def ingest(self, fragment: Union[FragmentLike, Iterable[FragmentLike]]) -> None:
        """Ingest one fragment or an iterable of fragments."""

        if isinstance(fragment, (RuntimePromptFragment, dict)):
            self.fragments.append(coerce_fragment(fragment))
            return
        for item in fragment:
            self.fragments.append(coerce_fragment(item))

    def compile(self, current_round: int, *, decay: bool = True) -> str:
        """Compile the current active fragments into a prompt block."""

        active = [
            fragment
            for fragment in self.fragments
            if fragment.directive
            and (fragment.expires_at is None or current_round < fragment.expires_at)
            and fragment.ttl_rounds > 0
        ]
        resolved = self.resolver.resolve(active)
        selected = resolved[: self.max_fragments]

        parts: List[str] = []
        total_chars = 0
        for fragment in selected:
            line = fragment.directive.strip()
            if not line:
                continue
            line_len = len(line)
            separator_len = 1 if parts else 0
            if parts and total_chars + separator_len + line_len > self.max_chars:
                break
            if not parts and line_len > self.max_chars:
                line = line[: self.max_chars].rstrip()
                line_len = len(line)
            parts.append(line)
            total_chars += separator_len + line_len

        if decay:
            self.fragments = self.lifecycle.tick(active, current_round=current_round)

        if not parts:
            return ""
        return "\n\n[Runtime Directives]\n" + "\n".join(parts)

    def active_fragments(self) -> List[Dict[str, Any]]:
        """Return active fragments as dicts for inspection/debugging."""

        return fragments_to_dicts(self.fragments)


def append_runtime_directives_to_messages(
    messages: Sequence[Dict[str, str]],
    runtime_prompt: str,
) -> List[Dict[str, str]]:
    """Append runtime directives to the first system message, or create one."""

    copied = [dict(message) for message in messages]
    if not runtime_prompt:
        return copied

    for message in copied:
        if message.get("role") == "system":
            base = message.get("content", "")
            message["content"] = base + runtime_prompt
            return copied

    return [{"role": "system", "content": runtime_prompt.lstrip()}, *copied]


def compile_runtime_prompt_messages(
    messages: Sequence[Dict[str, str]],
    fragments: Iterable[FragmentLike],
    *,
    current_round: int,
    max_fragments: int = 5,
    max_chars: int = 800,
) -> List[Dict[str, str]]:
    """Compile fragments and return messages with runtime directives injected."""

    compiler = RuntimePromptCompiler(max_fragments=max_fragments, max_chars=max_chars)
    compiler.ingest(fragments)
    runtime_prompt = compiler.compile(current_round=current_round, decay=False)
    return append_runtime_directives_to_messages(messages, runtime_prompt)
