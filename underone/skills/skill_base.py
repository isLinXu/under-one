#!/usr/bin/env python3
"""
SkillBase — 所有Skill脚本的基类

提供：
1. 自动配置加载（从 under-one.yaml）
2. 标准化的指标收集装饰器
3. 输入验证辅助函数
4. 默认值回退机制

使用方式：
    from skill_base import SkillBase

    class MySkill(SkillBase):
        SKILL_NAME = "my-skill"
        DEFAULT_CONFIG = {...}

        def execute(self, data):
            # 使用 self.config 访问配置
            # 使用 self.validate_input() 验证输入
            pass
"""

import json
import sys
from pathlib import Path
from functools import wraps

# ═══════════════════════════════════════════════════════════════════════════
# 路径设置
# ═══════════════════════════════════════════════════════════════════════════

# 从当前文件位置向上追溯到 skills/ 目录
_SKILL_BASE_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _SKILL_BASE_DIR.parent  # underone/skills/


# ═══════════════════════════════════════════════════════════════════════════
# 配置加载（延迟导入，避免循环依赖）
# ═══════════════════════════════════════════════════════════════════════════

_config_cache = None


def _load_global_config():
    """延迟加载 under-one.yaml 配置（全局缓存）"""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    try:
        # 尝试从 _skill_config 导入
        sys.path.insert(0, str(_SKILLS_ROOT))
        from _skill_config import load_skill_config
        _config_cache = load_skill_config()
    except ImportError:
        # 降级：手动解析 YAML
        config_path = _SKILLS_ROOT.parent / "under-one.yaml"
        if config_path.exists():
            _config_cache = _minimal_yaml_parse(config_path.read_text(encoding="utf-8"))
        else:
            _config_cache = {}
    return _config_cache


def get_skill_config(skill_name: str, key: str = None, default=None):
    """获取指定skill的配置项。

    Args:
        skill_name: skill名称（如 "fenghouqimen", "daludongguan"）
        key: 配置键名，None返回整节
        default: 未找到时的默认值
    """
    cfg = _load_global_config()
    section = cfg.get(skill_name, {})
    if key is None:
        return section if section else default
    return section.get(key, default)


def _minimal_yaml_parse(text: str) -> dict:
    """极简 YAML 解析器"""
    result = {}
    current_section = None
    current_sub = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
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
        elif current_section is not None and stripped.startswith("-"):
            val = stripped[1:].strip()
            # 修复：确保列表存在
            if current_sub and current_sub in result.get(current_section, {}):
                if isinstance(result[current_section][current_sub], list):
                    result[current_section][current_sub].append(_parse_yaml_value(val))
                else:
                    # 已经是dict，转为列表
                    result[current_section][current_sub] = [result[current_section][current_sub], _parse_yaml_value(val)]
            elif current_section in result and isinstance(result[current_section], list):
                result[current_section].append(_parse_yaml_value(val))
            else:
                # 新的顶级列表项
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
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1]
        if not inner.strip():
            return []
        return [_parse_yaml_value(v.strip()) for v in inner.split(",")]
    return val


# ═══════════════════════════════════════════════════════════════════════════
# 指标收集（延迟导入）
# ═══════════════════════════════════════════════════════════════════════════

def record_metrics(skill_name: str):
    """指标记录装饰器工厂。

    用法:
        @record_metrics("my-skill")
        def execute(self, data):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                sys.path.insert(0, str(_SKILLS_ROOT))
                from metrics_collector import record as _record
                return _record(skill_name)(func)(*args, **kwargs)
            except ImportError:
                return func(*args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════
# 输入验证
# ═══════════════════════════════════════════════════════════════════════════

def validate_json_input(data: dict, required_fields: list, skill_name: str = "skill") -> tuple:
    """验证JSON输入数据是否包含所有必需字段。

    Returns:
        (is_valid: bool, missing_fields: list)
    """
    if not isinstance(data, dict):
        return False, ["<root> must be an object"]
    missing = [f for f in required_fields if f not in data or data[f] is None]
    return len(missing) == 0, missing


def validate_json_list(data: list, item_schema: dict, skill_name: str = "skill") -> tuple:
    """验证JSON列表输入，检查每项是否符合schema。

    Args:
        data: 输入列表
        item_schema: {字段名: 类型} 的schema字典

    Returns:
        (is_valid: bool, errors: list)
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


# ═══════════════════════════════════════════════════════════════════════════
# SkillBase 基类
# ═══════════════════════════════════════════════════════════════════════════

class SkillBase:
    """所有Skill的基类，提供通用基础设施。

    子类应该：
    1. 定义 SKILL_NAME 属性
    2. 定义 DEFAULT_CONFIG 类属性
    3. 实现 execute() 方法

    示例:
        class MySkill(SkillBase):
            SKILL_NAME = "my-skill"
            DEFAULT_CONFIG = {
                "threshold": 0.5,
                "keywords": ["a", "b"],
            }

            def __init__(self, data):
                super().__init__(data)
                # 自定义初始化

            def execute(self):
                threshold = self.config.get("threshold", 0.5)
                # ...
    """

    SKILL_NAME = "base-skill"
    DEFAULT_CONFIG = {}

    def __init__(self, input_data=None):
        """初始化SkillBase。

        Args:
            input_data: 输入数据（dict 或 list）
        """
        self.input_data = input_data
        self.config = self._load_config()
        self.errors = []
        self.warnings = []

    def _load_config(self) -> dict:
        """从 under-one.yaml 加载配置，未找到时回退到 DEFAULT_CONFIG"""
        cfg = get_skill_config(self.SKILL_NAME, default=None)
        if cfg is None:
            return self.DEFAULT_CONFIG.copy()
        # 合并：配置优先，默认值兜底
        merged = self.DEFAULT_CONFIG.copy()
        for key, value in cfg.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key].update(value)
            else:
                merged[key] = value
        return merged

    def get_config(self, key: str, default=None):
        """获取配置值，兼容嵌套结构。

        用法:
            threshold = self.get_config("thresholds.semantic_similarity", 0.3)
            # 等价于 self.config.get("thresholds", {}).get("semantic_similarity", 0.3)
        """
        if "." in key:
            keys = key.split(".")
            value = self.config
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default
            return value if value is not None else default
        return self.config.get(key, default)

    def validate(self, required_fields: list = None) -> bool:
        """验证输入数据。

        Args:
            required_fields: 必需的顶层字段列表

        Returns:
            True if valid, False otherwise
        """
        if required_fields is None:
            return True
        if self.input_data is None:
            self.errors.append("输入数据为空")
            return False
        is_valid, missing = validate_json_input(
            self.input_data if isinstance(self.input_data, dict) else {},
            required_fields,
            self.SKILL_NAME
        )
        if not is_valid:
            self.errors.extend(missing)
        return is_valid

    def add_warning(self, message: str):
        """添加警告信息"""
        self.warnings.append(message)

    def add_error(self, message: str):
        """添加错误信息"""
        self.errors.append(message)

    def execute(self):
        """执行Skill逻辑，子类必须实现"""
        raise NotImplementedError("子类必须实现 execute() 方法")

    def get_result(self) -> dict:
        """获取执行结果，包含元数据"""
        result = {
            "skill": self.SKILL_NAME,
            "success": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
        }
        if hasattr(self, 'output'):
            result["data"] = self.output
        return result


# ═══════════════════════════════════════════════════════════════════════════
# CLI 入口辅助
# ═══════════════════════════════════════════════════════════════════════════

def create_cli_entry(skill_class, required_fields=None):
    """创建标准化的CLI入口。

    用法:
        if __name__ == "__main__":
            main = create_cli_entry(MySkill, required_fields=["content"])
            main()
    """
    def main():
        if len(sys.argv) < 2:
            print(f"用法: python {skill_class.SKILL_NAME}.py <input.json>")
            sys.exit(1)

        # 读取输入
        try:
            with open(sys.argv[1], "r", encoding="utf-8") as f:
                input_data = json.load(f)
        except FileNotFoundError:
            print(f"错误: 文件不存在 {sys.argv[1]}")
            sys.exit(2)
        except json.JSONDecodeError as e:
            print(f"错误: JSON解析失败 {e}")
            sys.exit(2)

        # 执行
        skill = skill_class(input_data)
        if required_fields and not skill.validate(required_fields):
            print(f"错误: 缺少必需字段 {skill.errors}")
            sys.exit(3)

        try:
            output = skill.execute()
        except Exception as e:
            print(f"错误: 执行失败 {e}")
            sys.exit(4)

        # 输出
        output_path = Path(f"{skill_class.SKILL_NAME}_report.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"✅ 输出已保存到 {output_path}")

    return main