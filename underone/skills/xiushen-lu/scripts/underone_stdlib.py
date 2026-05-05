#!/usr/bin/env python3
"""
under-one.skills V10 Standard Library
所有skill脚本共享的标准化基础设施

Usage:
    from under_one_stdlib import HachiCLI, HachiConfig, export_metrics

Features:
- 统一CLI参数解析（input, config, verbose, output）
- 统一错误处理和日志输出
- 统一metrics导出（自动写入runtime_data/）
- 配置驱动（从under-one.yaml读取参数，不硬编码）
- 统一JSON报告输出
"""

import argparse
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


# ── Global Paths ──
RUNTIME_DIR = Path("runtime_data")
RUNTIME_DIR.mkdir(exist_ok=True)


class HachiConfig:
    """配置管理器：从under-one.yaml或默认值读取"""

    DEFAULTS = {
        "quality_threshold": 75,
        "entropy_warning": 3.0,
        "entropy_critical": 7.0,
        "sla_timeout_ms": 30000,
        "max_retries": 3,
        "log_level": "info",
        "curse_keywords_high": ["删除", "覆盖", "资金", "医疗", "法律", "销毁"],
        "curse_keywords_medium": ["发布", "发送", "配置", "权限", "变更"],
        "digestion_thresholds": {"S": 0.95, "A": 0.85, "B": 0.70, "C": 0.50},
    }

    def __init__(self, config_path: Optional[str] = None):
        self._config = dict(self.DEFAULTS)
        # Try loading from under-one.yaml
        if config_path:
            self._load_yaml(config_path)
        else:
            # Search in common locations（覆盖仓库内多层调用）
            for p in ["under-one.yaml", "../under-one.yaml", "../../under-one.yaml",
                      "../../../under-one.yaml"]:
                if Path(p).exists():
                    self._load_yaml(p)
                    break

    def _load_yaml(self, path: str):
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data:
                self._config.update(data)
        except ImportError:
            # Fallback: try JSON
            try:
                with open(path.replace(".yaml", ".json"), "r", encoding="utf-8") as f:
                    self._config.update(json.load(f))
            except FileNotFoundError:
                pass

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def __getitem__(self, key: str):
        return self._config[key]


class HachiCLI:
    """标准化CLI接口：统一参数解析和错误处理"""

    def __init__(self, skill_name: str, description: str):
        self.skill_name = skill_name
        self.parser = argparse.ArgumentParser(
            prog=f"{skill_name}.py",
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self._add_common_args()
        self.args = None
        self.config = None

    def _add_common_args(self):
        self.parser.add_argument("input", nargs="?", default=None,
                                help="Input file path (or '-' for stdin)")
        self.parser.add_argument("-c", "--config", default=None,
                                help="Path to under-one.yaml config file")
        self.parser.add_argument("-v", "--verbose", action="store_true",
                                help="Enable verbose output")
        self.parser.add_argument("-o", "--output", default=None,
                                help="Output file path (default: auto-generated)")
        self.parser.add_argument("--version", action="version",
                                version=f"%(prog)s V10.0 (under-one.skills)")

    def parse(self) -> "HachiCLI":
        self.args = self.parser.parse_args()
        self.config = HachiConfig(self.args.config)
        return self

    def read_input(self) -> str:
        """读取输入：支持文件路径或stdin"""
        if self.args.input is None or self.args.input == "-":
            return sys.stdin.read()
        path = Path(self.args.input)
        if not path.exists():
            self.error(f"Input file not found: {path}")
            sys.exit(1)
        return path.read_text(encoding="utf-8")

    def read_input_json(self) -> Any:
        """读取JSON输入"""
        raw = self.read_input()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            self.error(f"Invalid JSON input: {e}")
            sys.exit(1)

    def write_output(self, data: Dict, path: Optional[str] = None) -> Path:
        """写入JSON输出"""
        out_path = Path(path or self.args.output or f"{self.skill_name}_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return out_path

    def log(self, msg: str):
        if self.args and self.args.verbose:
            print(f"[{self.skill_name}] {msg}", file=sys.stderr)

    def info(self, msg: str):
        print(f"  {msg}")

    def error(self, msg: str):
        print(f"  ERROR: {msg}", file=sys.stderr)

    def success(self, msg: str):
        print(f"  OK: {msg}")

    def run(self, main_fn):
        """统一执行入口，带错误处理"""
        try:
            self.parse()
            result = main_fn(self)
            # Auto-export metrics
            if isinstance(result, dict):
                export_metrics(self.skill_name, result)
            return result
        except KeyboardInterrupt:
            self.error("Interrupted by user")
            sys.exit(130)
        except Exception as e:
            self.error(f"{type(e).__name__}: {e}")
            if self.args and self.args.verbose:
                traceback.print_exc()
            sys.exit(1)


def export_metrics(skill_name: str, result: Dict):
    """统一metrics导出：自动写入runtime_data/"""
    metrics = {
        "skill_name": skill_name,
        "timestamp": datetime.now().isoformat(),
        "success": result.get("success", result.get("passed", True)),
        "quality_score": result.get("quality_score", result.get("score", 80)),
        "error_count": result.get("error_count", 0),
        "human_intervention": result.get("human_intervention", 0),
        "output_completeness": result.get("output_completeness", 100),
        "consistency_score": result.get("consistency_score", 90),
        "duration_ms": result.get("duration_ms", 0),
    }
    file_path = RUNTIME_DIR / f"{skill_name}_metrics.jsonl"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(metrics, ensure_ascii=False) + "\n")


def load_jsonl(name: str, n: int = 100) -> list:
    """加载最近n条metrics记录"""
    file_path = RUNTIME_DIR / f"{name}_metrics.jsonl"
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    records = [json.loads(l) for l in lines if l.strip()]
    return records[-n:]


if __name__ == "__main__":
    # Self-test
    cli = HachiCLI("test", "Test the standard library")
    cli.parse()
    print("under-one.skills V10 Standard Library loaded successfully")
    print(f"Config quality_threshold: {cli.config.get('quality_threshold')}")
    print(f"Verbose: {cli.args.verbose}")
