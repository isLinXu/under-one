"""Configuration loading for UnderOne."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import ConfigurationError

CONFIG_ENV = "UNDER_ONE_CONFIG"
CONFIG_HOT_RELOAD_ENV = "UNDER_ONE_CONFIG_RELOAD"
ENV_OVERRIDE_PREFIX = "UNDER_ONE__"
SUPPORTED_CONFIG_VERSIONS = {1}
CONFIG_PATHS = [
    "under-one.yaml",
    "../under-one.yaml",
    "~/.under-one/under-one.yaml",
    "/etc/under-one/under-one.yaml",
]
SENSITIVE_KEY_FRAGMENTS = ("api_key", "apikey", "token", "secret", "password", "credential")

_CONFIG_CACHE: Dict[Optional[str], Dict[str, Any]] = {}
_CONFIG_CACHE_META: Dict[Optional[str], tuple[Optional[int], tuple[tuple[str, str], ...]]] = {}


def _candidate_paths() -> list[Path]:
    env_path = os.getenv(CONFIG_ENV)
    paths: list[Path] = []
    if env_path:
        paths.append(Path(env_path).expanduser())
    paths.extend(Path(path).expanduser() for path in CONFIG_PATHS)

    package_dir = Path(__file__).resolve().parent
    for candidate_dir in (Path.cwd(), package_dir, *package_dir.parents):
        paths.append(candidate_dir / "under-one.yaml")
    return paths


def find_config_path(explicit_path: Optional[Any] = None) -> Optional[Path]:
    """Return the first readable under-one config path."""

    if explicit_path is not None:
        path = Path(explicit_path).expanduser()
        return path if path.exists() else None

    seen: set[Path] = set()
    for path in _candidate_paths():
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved
    return None


def clear_config_cache() -> None:
    """Clear cached config content."""

    _CONFIG_CACHE.clear()
    _CONFIG_CACHE_META.clear()


def _path_mtime_ns(path: Optional[Path]) -> Optional[int]:
    if path is None:
        return None
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None


def _env_override_signature() -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (key, value)
            for key, value in os.environ.items()
            if key.startswith(ENV_OVERRIDE_PREFIX)
        )
    )


def _parse_env_value(raw: str) -> Any:
    lowered = raw.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _set_nested_value(target: Dict[str, Any], path: list[str], value: Any) -> None:
    current = target
    for key in path[:-1]:
        if not isinstance(current.get(key), dict):
            current[key] = {}
        current = current[key]
    current[path[-1]] = value


def _apply_env_overrides(payload: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(payload)
    for key, raw_value in os.environ.items():
        if not key.startswith(ENV_OVERRIDE_PREFIX):
            continue
        path = [part.lower() for part in key[len(ENV_OVERRIDE_PREFIX):].split("__") if part]
        if not path:
            continue
        _set_nested_value(merged, path, _parse_env_value(raw_value))
    return merged


def validate_config(payload: Dict[str, Any], *, path: Optional[Path] = None) -> None:
    """Validate the config envelope without requiring a version in old files."""

    if not isinstance(payload, dict):
        raise ConfigurationError(f"配置文件必须是 YAML mapping: {path or '<memory>'}")

    raw_version = payload.get("config_version")
    if raw_version is None:
        return
    try:
        version = int(raw_version)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"config_version 必须是整数: {raw_version!r}") from exc
    if version not in SUPPORTED_CONFIG_VERSIONS:
        supported = ", ".join(str(item) for item in sorted(SUPPORTED_CONFIG_VERSIONS))
        raise ConfigurationError(f"不支持的 config_version={version}，当前支持: {supported}")


def redact_config(payload: Any) -> Any:
    """Return a copy of config data with secrets masked for logs and diagnostics."""

    if isinstance(payload, dict):
        redacted = {}
        for key, value in payload.items():
            key_l = str(key).lower()
            if any(fragment in key_l for fragment in SENSITIVE_KEY_FRAGMENTS):
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = redact_config(value)
        return redacted
    if isinstance(payload, list):
        return [redact_config(item) for item in payload]
    return payload


def load_config(config_path: Optional[Any] = None, *, force_reload: bool = False) -> Dict[str, Any]:
    """Load global UnderOne config as a dictionary."""

    path = find_config_path(config_path)
    cache_key = str(path) if path is not None else None
    current_meta = (_path_mtime_ns(path), _env_override_signature())
    cached_meta = _CONFIG_CACHE_META.get(cache_key)
    hot_reload = os.getenv(CONFIG_HOT_RELOAD_ENV, "").lower() in {"1", "true", "yes"}
    if hot_reload:
        cache_valid = cached_meta == current_meta
    else:
        cached_env_signature = (cached_meta or (None, ()))[1]
        cache_valid = cached_env_signature == current_meta[1]
    if cache_key in _CONFIG_CACHE and not force_reload and cache_valid:
        return _CONFIG_CACHE[cache_key]
    if path is None:
        _CONFIG_CACHE[cache_key] = _apply_env_overrides({})
        _CONFIG_CACHE_META[cache_key] = current_meta
        return _CONFIG_CACHE[cache_key]

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - PyYAML is a package dependency.
        raise ConfigurationError("PyYAML is required to load under-one.yaml") from exc

    with open(path, "r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    validate_config(payload, path=path)
    payload = _apply_env_overrides(payload)
    _CONFIG_CACHE[cache_key] = payload
    _CONFIG_CACHE_META[cache_key] = current_meta
    return payload


def reload_config(config_path: Optional[Any] = None) -> Dict[str, Any]:
    """Force reload config from disk and environment overrides."""

    return load_config(config_path, force_reload=True)


def get_config(section: str, key: Optional[str] = None, default: Any = None) -> Any:
    """Read a config value from a section."""

    cfg = load_config()
    sec = cfg.get(section, {})
    if key is None:
        return sec if sec else default
    if not isinstance(sec, dict):
        return default
    value = sec.get(key, default)
    return value if value is not None else default


def get_threshold(key: str, default: Any = None) -> Any:
    """Read a value from the global thresholds section."""

    return get_config("thresholds", key, default)


def get_skill_config(skill_name: str, key: Optional[str] = None, default: Any = None) -> Any:
    """Read a skill-specific config section."""

    return get_config(skill_name, key, default)


def get_script_timeout(skill_name: Optional[str] = None, default: int = 60) -> int:
    """Return subprocess timeout seconds from runtime or per-skill config."""

    raw = get_config("runtime", "script_timeout_seconds", default)
    if skill_name:
        section = skill_name.replace("-", "")
        raw = get_config(section, "script_timeout_seconds", raw)
    try:
        timeout = int(raw)
    except (TypeError, ValueError):
        timeout = default
    return max(1, timeout)
