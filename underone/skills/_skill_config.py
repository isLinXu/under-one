"""
Skill 配置加载辅助模块
提供统一接口让 skill 脚本读取 under-one.yaml 中的配置，不依赖外部依赖。
"""

import copy
import json
import os
from pathlib import Path
from typing import Optional

try:
    from _yaml_fallback import minimal_yaml_parse
except ImportError:
    from ._yaml_fallback import minimal_yaml_parse


# 缓存配置内容，避免重复读取
_CONFIG_CACHE = None
_CONFIG_PATH_CANDIDATES = [
    "under-one.yaml",
    "../under-one.yaml",
    "../../under-one.yaml",
    "~/.under-one/under-one.yaml",
]
ENV_OVERRIDE_PREFIX = "UNDER_ONE__"
SUPPORTED_CONFIG_VERSIONS = {1}


def _parse_env_value(raw: str):
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


def _set_nested_value(target: dict, path: list, value):
    current = target
    for key in path[:-1]:
        if not isinstance(current.get(key), dict):
            current[key] = {}
        current = current[key]
    current[path[-1]] = value


def _apply_env_overrides(payload: dict) -> dict:
    merged = copy.deepcopy(payload)
    for key, raw_value in os.environ.items():
        if not key.startswith(ENV_OVERRIDE_PREFIX):
            continue
        path = [part.lower() for part in key[len(ENV_OVERRIDE_PREFIX):].split("__") if part]
        if not path:
            continue
        _set_nested_value(merged, path, _parse_env_value(raw_value))
    return merged


def _validate_config(payload: dict, config_path: Optional[Path] = None):
    if not isinstance(payload, dict):
        raise ValueError(f"配置文件必须是 YAML mapping: {config_path or '<memory>'}")
    raw_version = payload.get("config_version")
    if raw_version is None:
        return
    try:
        version = int(raw_version)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"config_version 必须是整数: {raw_version!r}") from exc
    if version not in SUPPORTED_CONFIG_VERSIONS:
        supported = ", ".join(str(item) for item in sorted(SUPPORTED_CONFIG_VERSIONS))
        raise ValueError(f"不支持的 config_version={version}，当前支持: {supported}")


def _find_config() -> Optional[Path]:
    """按优先级搜索配置文件"""
    for p in _CONFIG_PATH_CANDIDATES:
        path = Path(p).expanduser().resolve()
        if path.exists():
            return path
    # 尝试从 skill 脚本位置向上回溯，避免依赖固定父级深度
    script_dir = Path(__file__).resolve().parent
    for candidate_dir in (script_dir, *script_dir.parents):
        candidate = candidate_dir / "under-one.yaml"
        if candidate.exists():
            return candidate
    return None


def load_skill_config() -> dict:
    """加载 under-one.yaml 全局配置，返回字典。无文件时返回空字典。"""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    config_path = _find_config()
    if config_path is None:
        _CONFIG_CACHE = _apply_env_overrides({})
        return _CONFIG_CACHE

    try:
        # 优先用 yaml，不可用则做极简解析
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                _CONFIG_CACHE = yaml.safe_load(f) or {}
                _validate_config(_CONFIG_CACHE, config_path)
                _CONFIG_CACHE = _apply_env_overrides(_CONFIG_CACHE)
                return _CONFIG_CACHE
        except ImportError:
            pass

        # 极简 YAML 子集解析（仅处理本项目用到的简单格式）
        with open(config_path, "r", encoding="utf-8") as f:
            raw = f.read()
        _CONFIG_CACHE = minimal_yaml_parse(raw)
        _validate_config(_CONFIG_CACHE, config_path)
        _CONFIG_CACHE = _apply_env_overrides(_CONFIG_CACHE)
        return _CONFIG_CACHE
    except Exception:
        _CONFIG_CACHE = {}
        return _CONFIG_CACHE


def get_config(section: str, key: str = None, default=None):
    """获取配置值。

    Args:
        section: 配置节名，如 "thresholds", "fenghouqimen"
        key: 节内的键名，如 "entropy_warning"
        default: 未找到时的默认值

    Returns:
        配置值或 default
    """
    cfg = load_skill_config()
    sec = cfg.get(section, {})
    if key is None:
        return sec if sec else default
    val = sec.get(key, default)
    return val if val is not None else default


# ---------------------------------------------------------------------------
# 便捷函数：供各 skill 直接导入使用
# ---------------------------------------------------------------------------

def get_threshold(key: str, default):
    """读取 thresholds 节下的阈值"""
    return get_config("thresholds", key, default)


def get_skill_config(skill_name: str, key: str = None, default=None):
    """读取特定 skill 的配置节"""
    return get_config(skill_name, key, default)


# ---------------------------------------------------------------------------
# 通用输入验证辅助函数
# ---------------------------------------------------------------------------

def validate_json_input(data: dict, required_fields: list, skill_name: str = "skill") -> tuple:
    """验证JSON输入数据是否包含所有必需字段。

    Args:
        data: 输入字典
        required_fields: 必需字段列表
        skill_name: skill名称（用于错误信息）

    Returns:
        (is_valid: bool, missing_fields: list)

    Example:
        ok, missing = validate_json_input(payload, ["name", "content"], "my-skill")
        if not ok:
            print(f"缺少字段: {missing}")
            sys.exit(1)
    """
    if not isinstance(data, dict):
        return False, ["<root> must be an object"]
    missing = [f for f in required_fields if f not in data or data[f] is None]
    return len(missing) == 0, missing


def validate_json_list(data: list, item_schema: dict, skill_name: str = "skill") -> tuple:
    """验证JSON列表输入，检查每项是否符合简单schema。

    Args:
        data: 输入列表
        item_schema: {字段名: 类型} 的schema字典
        skill_name: skill名称

    Returns:
        (is_valid: bool, errors: list)

    Example:
        ok, errs = validate_json_list(items, {"name": str, "score": (int, float)})
    """
    if not isinstance(data, list):
        return False, ["<root> must be a list"]
    errors = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"item[{i}] must be an object")
            continue
        for field, expected_type in item_schema.items():
            if field not in item:
                errors.append(f"item[{i}] missing field: {field}")
                continue
            val = item[field]
            if not isinstance(val, expected_type):
                errors.append(f"item[{i}].{field} type error: expected {expected_type}, got {type(val)}")
    return len(errors) == 0, errors
