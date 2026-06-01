"""UnderOne exception hierarchy."""

from __future__ import annotations

from typing import Sequence


class UnderOneError(Exception):
    """Base exception for all UnderOne errors."""


class SkillExecutionError(UnderOneError):
    """A skill failed while executing."""

    def __init__(self, skill_name: str, message: str, *, recoverable: bool = False) -> None:
        self.skill_name = skill_name
        self.recoverable = recoverable
        super().__init__(f"[{skill_name}] {message}")


class InputValidationError(UnderOneError):
    """Input payload failed validation before a skill could run."""

    def __init__(self, skill_name: str, missing_fields: Sequence[str]) -> None:
        self.skill_name = skill_name
        self.missing_fields = list(missing_fields)
        super().__init__(f"[{skill_name}] 缺少必需字段: {self.missing_fields}")


class ConfigurationError(UnderOneError):
    """Configuration could not be loaded or validated."""


class LLMProviderError(UnderOneError):
    """LLM provider failed because of network, auth, quota, or provider errors."""
