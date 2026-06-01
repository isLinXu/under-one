"""Shared validation helpers for SDK and skill scripts."""

from __future__ import annotations

from typing import Any, Dict, Sequence, Tuple

from .exceptions import InputValidationError


def validate_json_input(
    data: Dict[str, Any],
    required_fields: Sequence[str],
    skill_name: str = "skill",
) -> Tuple[bool, list[str]]:
    """Validate that a JSON object contains all required fields."""

    if not isinstance(data, dict):
        return False, ["<root> must be an object"]
    missing = [field for field in required_fields if field not in data or data[field] is None]
    return len(missing) == 0, missing


def validate_json_list(data: list, item_schema: Dict[str, Any], skill_name: str = "skill") -> Tuple[bool, list[str]]:
    """Validate a list of JSON objects against a simple field/type schema."""

    if not isinstance(data, list):
        return False, ["<root> must be a list"]

    errors: list[str] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"item[{index}] must be an object")
            continue
        for field, expected_type in item_schema.items():
            if field not in item:
                errors.append(f"item[{index}] missing field: {field}")
                continue
            value = item[field]
            if not isinstance(value, expected_type):
                errors.append(f"item[{index}].{field} type error: expected {expected_type}, got {type(value)}")
    return len(errors) == 0, errors


def require_json_input(data: Dict[str, Any], required_fields: Sequence[str], skill_name: str = "skill") -> None:
    """Raise a typed UnderOne error when required fields are missing."""

    ok, missing = validate_json_input(data, required_fields, skill_name)
    if not ok:
        raise InputValidationError(skill_name, missing)
