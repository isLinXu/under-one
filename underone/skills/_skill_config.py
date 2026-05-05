"""
Skill 配置加载辅助模块
提供统一接口让 skill 脚本读取 under-one.yaml 中的配置，不依赖外部依赖。
"""

import json
from pathlib import Path


# 缓存配置内容，避免重复读取
_CONFIG_CACHE = None
_CONFIG_PATH_CANDIDATES = [
    "under-one.yaml",
    "../under-one.yaml",
    "../../under-one.yaml",
    "~/.under-one/under-one.yaml",
]


def _find_config() -> Path | None:
    """按优先级搜索配置文件"""
    for p in _CONFIG_PATH_CANDIDATES:
        path = Path(p).expanduser().resolve()
        if path.exists():
            return path
    # 尝试从 skill 脚本位置向上回溯
    script_dir = Path(__file__).resolve().parent
    for depth in range(5):
        candidate = script_dir.parents[depth] / "under-one.yaml"
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
        _CONFIG_CACHE = {}
        return _CONFIG_CACHE

    try:
        # 优先用 yaml，不可用则做极简解析
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                _CONFIG_CACHE = yaml.safe_load(f) or {}
                return _CONFIG_CACHE
        except ImportError:
            pass

        # 极简 YAML 子集解析（仅处理本项目用到的简单格式）
        with open(config_path, "r", encoding="utf-8") as f:
            raw = f.read()
        _CONFIG_CACHE = _minimal_yaml_parse(raw)
        return _CONFIG_CACHE
    except Exception:
        _CONFIG_CACHE = {}
        return _CONFIG_CACHE


def _minimal_yaml_parse(text: str) -> dict:
    """极简 YAML 解析器，仅支持本项目用到的格式：
    - 顶级键
    - 缩进子键
    - 列表（- 开头）
    - 基本数值、字符串
    """
    result = {}
    current_section = None
    current_sub = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # 顶级键: value
        if not line.startswith(" ") and not line.startswith("\t"):
            if ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip()
                if val == "":
                    result[key] = {}
                    current_section = key
                    current_sub = None
                else:
                    result[key] = _parse_yaml_value(val)
                    current_section = None
        # 子键
        elif current_section is not None and stripped.startswith("-"):
            # 列表项
            val = stripped[1:].strip()
            if isinstance(result.get(current_section), dict) and current_sub is not None:
                if current_sub not in result[current_section]:
                    result[current_section][current_sub] = []
                result[current_section][current_sub].append(_parse_yaml_value(val))
            else:
                if current_section not in result:
                    result[current_section] = []
                result[current_section].append(_parse_yaml_value(val))
        elif current_section is not None and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "":
                if current_section not in result:
                    result[current_section] = {}
                result[current_section][key] = {}
                current_sub = key
            else:
                if current_section not in result:
                    result[current_section] = {}
                result[current_section][key] = _parse_yaml_value(val)
    return result


def _parse_yaml_value(val: str):
    """解析 YAML 标量值"""
    val = val.strip()
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    if val == "true":
        return True
    if val == "false":
        return False
    if val == "null" or val == "~":
        return None
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        pass
    # 列表解析 [a, b]
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1]
        if not inner.strip():
            return []
        return [_parse_yaml_value(v.strip()) for v in inner.split(",")]
    return val


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
