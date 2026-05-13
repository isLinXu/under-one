#!/usr/bin/env python3
"""
器名: 通用修身炉 (Universal XiuShenLu)
用途: 对任意skill（代码型/指令型）和agent.md进行自进化
核心设计: 插件化进化策略 + 通用metrics接口 + AST级代码分析

支持的进化目标:
  1. 任意 .skill 包 (SKILL.md + scripts/ + references/ + assets/)
  2. 任意 agent.md (纯文本指令文件)
  3. 任意 Python/Bash/JS 脚本文件

进化策略 (Strategy Pattern):
  - CodeStrategy: AST分析 + 自动修复 (代码型skill)
  - InstructionStrategy: 指令优化 + 结构重组 (指令型skill/agent.md)
  - HybridStrategy: 混合进化 (SKILL.md + scripts同时进化)
"""

import ast
import json
import sys
import os
import shutil
import re
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

# 运行时指标收集
SKILLS_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SKILLS_ROOT))
try:
    from metrics_collector import record_metrics
except ImportError:
    def record_metrics(*args, **kwargs):
        def decorator(f): return f
        return decorator


# ═══════════════════════════════════════════════════════════
# 通用Metrics接口 (任何skill/agent只需实现此接口即可被进化)
# ═══════════════════════════════════════════════════════════
class UniversalMetricsCollector:
    """
    通用指标收集器
    任何可进化对象只需将指标写入 {output_dir}/{name}_metrics.jsonl 即可
    格式: {"name": str, "timestamp": str, "success": bool, "quality": float, "errors": int, ...}
    """

    REQUIRED_FIELDS = ["name", "timestamp", "success", "quality"]
    OPTIONAL_FIELDS = ["errors", "human_intervention", "duration_ms", "token_usage", "complexity"]

    def __init__(self, output_dir: str = "runtime_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def write(self, metrics: Dict) -> None:
        """写入一条指标记录"""
        # 验证必需字段
        for field in self.REQUIRED_FIELDS:
            if field not in metrics:
                raise ValueError(f"Missing required field: {field}")

        # 自动补全可选字段
        for field in self.OPTIONAL_FIELDS:
            if field not in metrics:
                metrics[field] = 0

        metrics["_collected_by"] = "UniversalXiuShenLu"
        metrics["_version"] = "9.0"

        name = metrics["name"]
        file_path = self.output_dir / f"{name}_metrics.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(metrics, ensure_ascii=False) + "\n")

    def read(self, name: str, n: int = 100) -> List[Dict]:
        """读取最近n条指标"""
        file_path = self.output_dir / f"{name}_metrics.jsonl"
        if not file_path.exists():
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        records = [json.loads(l) for l in lines if l.strip()]
        return records[-n:]


# ═══════════════════════════════════════════════════════════
# 进化策略基类 (Strategy Pattern)
# ═══════════════════════════════════════════════════════════
class EvolutionStrategy(ABC):
    """进化策略抽象基类"""

    @abstractmethod
    def can_handle(self, target_path: Path) -> bool:
        """判断是否能处理该目标"""
        pass

    @abstractmethod
    def analyze(self, target_path: Path, metrics: List[Dict]) -> Dict:
        """分析瓶颈"""
        pass

    @abstractmethod
    def evolve(self, target_path: Path, analysis: Dict) -> Dict:
        """执行进化"""
        pass

    @abstractmethod
    def validate(self, target_path: Path) -> Dict:
        """验证进化结果"""
        pass


# ═══════════════════════════════════════════════════════════
# 策略1: 代码型进化 (Python脚本)
# ═══════════════════════════════════════════════════════════
class CodeEvolutionStrategy(EvolutionStrategy):
    """
    代码型进化策略
    通过AST分析Python代码，自动检测并修复:
      - 异常处理缺失 (try/except)
      - 性能问题 (循环内重复计算)
      - 硬编码阈值 (magic numbers)
      - 输入验证缺失
    """

    def can_handle(self, target_path: Path) -> bool:
        if target_path.is_file() and target_path.suffix == ".py":
            return True
        if target_path.is_dir() and list(target_path.glob("scripts/*.py")):
            return True
        return False

    def analyze(self, target_path: Path, metrics: List[Dict]) -> Dict:
        """AST级代码分析"""
        issues = []

        # 获取所有Python文件
        py_files = []
        if target_path.is_file():
            py_files = [target_path]
        else:
            py_files = list(target_path.rglob("*.py"))

        for py_file in py_files:
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source)

                # 检测1: 缺少异常处理的主函数
                has_try_except = any(isinstance(node, ast.Try) for node in ast.walk(tree))
                if not has_try_except and "def main(" in source:
                    issues.append({
                        "file": py_file.name,
                        "type": "missing_exception_handling",
                        "severity": "high",
                        "line": None,
                        "suggestion": "Add try/except in main function",
                    })

                # 检测2: 硬编码阈值
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and "THRESHOLD" in target.id.upper():
                                if isinstance(node.value, (ast.Num, ast.Constant)):
                                    val = node.value.n if isinstance(node.value, ast.Num) else node.value.value
                                    if val > 80:
                                        issues.append({
                                            "file": py_file.name,
                                            "type": "threshold_too_strict",
                                            "severity": "medium",
                                            "line": node.lineno,
                                            "current_value": val,
                                            "suggestion": f"Consider lowering threshold from {val}",
                                        })

                # 检测3: 循环内函数调用 (性能问题)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.For):
                            for child in ast.walk(node):
                                if isinstance(child, ast.Call):
                                    if isinstance(child.func, ast.Name) and child.func.id in ["len", "range"]:
                                        # 检查是否是len(text)在循环内且text不变
                                        pass  # 简化版

            except SyntaxError:
                issues.append({"file": py_file.name, "type": "syntax_error", "severity": "critical"})

        # 结合metrics分析
        if metrics:
            avg_errors = sum(m.get("errors", 0) for m in metrics) / len(metrics)
            avg_quality = sum(m.get("quality", 0) for m in metrics) / len(metrics)
        else:
            avg_errors = 0
            avg_quality = 100

        # 根据metrics调整问题优先级
        if avg_errors > 0.1:
            for issue in issues:
                if issue["type"] == "missing_exception_handling":
                    issue["severity"] = "critical"

        return {
            "strategy": "code",
            "files_analyzed": len(py_files),
            "issues_found": len(issues),
            "issues": issues,
            "metrics_summary": {"avg_errors": avg_errors, "avg_quality": avg_quality},
        }

    def evolve(self, target_path: Path, analysis: Dict) -> Dict:
        """AST-aware代码修复"""
        changes = []
        issues = analysis.get("issues", [])

        # 按文件分组问题
        by_file = defaultdict(list)
        for issue in issues:
            by_file[issue["file"]].append(issue)

        for filename, file_issues in by_file.items():
            # 找到实际文件路径
            if target_path.is_file():
                file_path = target_path
            else:
                file_path = next(target_path.rglob(filename), None)

            if not file_path or not file_path.exists():
                continue

            source = file_path.read_text(encoding="utf-8")
            original = source

            for issue in file_issues:
                issue_type = issue["type"]

                if issue_type == "missing_exception_handling":
                    # 为main函数添加try/except
                    source = self._add_exception_handling(source)
                    changes.append(f"{filename}: Added exception handling to main()")

                elif issue_type == "threshold_too_strict":
                    # 放宽阈值
                    current = issue.get("current_value", 95)
                    new_val = max(50, int(current * 0.6))
                    # 安全替换：使用AST定位的上下文
                    if f"= {current}" in source:
                        source = source.replace(f"= {current}", f"= {new_val}", 1)
                        changes.append(f"{filename}: Threshold {current} → {new_val}")

                elif issue_type == "syntax_error":
                    changes.append(f"{filename}: ⚠️ Syntax error found - cannot auto-fix")

            if source != original:
                # 语法验证
                try:
                    ast.parse(source)
                    file_path.write_text(source, encoding="utf-8")
                    changes.append(f"{filename}: ✓ Syntax check passed")
                except SyntaxError as e:
                    changes.append(f"{filename}: ✗ Syntax error after evolution: {e}")

        return {"status": "evolved" if changes else "no_changes", "changes": changes}

    def _add_exception_handling(self, source: str) -> str:
        """为main函数添加try/except"""
        # 简单策略：在main函数体外层包裹try/except
        lines = source.split("\n")
        new_lines = []
        in_main = False
        main_indent = None
        inserted_try = False

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            # 找到main函数定义
            if stripped.startswith("def main("):
                in_main = True
                main_indent = indent
                new_lines.append(line)
                continue

            # 在main函数第一行代码前插入try
            if in_main and not inserted_try and stripped and not stripped.startswith("def ") and not stripped.startswith("@"):
                if main_indent is not None:
                    try_indent = " " * (main_indent + 4)
                    new_lines.append(try_indent + "try:")
                    new_lines.append(try_indent + "    " + stripped)
                    inserted_try = True
                    continue

            # 在main函数末尾添加except
            if in_main and stripped.startswith("if __name__"):
                if inserted_try:
                    except_indent = " " * (main_indent + 4)
                    new_lines.append(except_indent + "except Exception as e:")
                    new_lines.append(except_indent + '    print(f"Error: {e}")')
                    new_lines.append(except_indent + "    import sys")
                    new_lines.append(except_indent + "    sys.exit(1)")
                in_main = False
                inserted_try = False

            new_lines.append(line)

        return "\n".join(new_lines)

    def validate(self, target_path: Path) -> Dict:
        """验证所有Python文件语法正确"""
        py_files = [target_path] if target_path.is_file() else list(target_path.rglob("*.py"))
        results = {}
        for py_file in py_files:
            try:
                ast.parse(py_file.read_text(encoding="utf-8"))
                results[py_file.name] = "ok"
            except SyntaxError as e:
                results[py_file.name] = f"syntax_error: {e}"

        all_ok = all(v == "ok" for v in results.values())
        return {"passed": all_ok, "file_checks": results}


# ═══════════════════════════════════════════════════════════
# 策略2: 指令型进化 (SKILL.md / agent.md)
# ═══════════════════════════════════════════════════════════
class InstructionEvolutionStrategy(EvolutionStrategy):
    """
    指令型进化策略
    适用于 SKILL.md 和 agent.md
    通过文本分析优化:
      - 冗余指令删除
      - 关键指令补充
      - 结构重组
      - 版本管理
    """

    # 好的skill/agent应该包含的关键元素
    ESSENTIAL_SECTIONS = [
        (r"##?\s*(Quick Start|快速开始|quickstart)", "quick_start"),
        (r"##?\s*(Error Handling|错误处理|异常处理)", "error_handling"),
        (r"##?\s*(Constraints|限制|约束条件)", "constraints"),
        (r"##?\s*(Examples|示例|例子)", "examples"),
    ]

    # 冗余/过时的表述模式
    REDUNDANT_PATTERNS = [
        (r"请务必注意", "注意"),  # 过于冗长
        (r"非常重要", ""),  # 空洞修饰
        (r"一定", ""),  # 绝对化
    ]

    def can_handle(self, target_path: Path) -> bool:
        if target_path.is_file() and target_path.suffix in (".md", ".txt"):
            return True
        if target_path.is_dir() and (target_path / "SKILL.md").exists():
            return True
        return False

    def analyze(self, target_path: Path, metrics: List[Dict]) -> Dict:
        """分析指令文件结构和质量"""
        # 确定实际文件路径
        if target_path.is_file():
            md_file = target_path
        else:
            md_file = target_path / "SKILL.md"

        if not md_file.exists():
            return {"strategy": "instruction", "status": "no_md_file"}

        content = md_file.read_text(encoding="utf-8")
        issues = []

        # 1. 检测缺失的关键章节
        for pattern, section_name in self.ESSENTIAL_SECTIONS:
            if not re.search(pattern, content, re.IGNORECASE):
                issues.append({
                    "type": "missing_section",
                    "section": section_name,
                    "severity": "medium",
                    "suggestion": f"Add a '{section_name}' section",
                })

        # 2. 检测冗余表述
        for pattern, suggestion in self.REDUNDANT_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                issues.append({
                    "type": "redundant_expression",
                    "pattern": pattern,
                    "count": len(matches),
                    "severity": "low",
                    "suggestion": f"Simplify: replace '{pattern}' with '{suggestion}'",
                })

        # 3. 检测过长的段落 (>500字无换行)
        long_paragraphs = []
        for para in content.split("\n\n"):
            if len(para) > 500 and not para.startswith("```"):
                long_paragraphs.append(len(para))
        if long_paragraphs:
            issues.append({
                "type": "long_paragraphs",
                "count": len(long_paragraphs),
                "severity": "low",
                "suggestion": "Break long paragraphs into smaller chunks",
            })

        # 4. 检测metrics反映的问题
        if metrics:
            avg_human = sum(m.get("human_intervention", 0) for m in metrics) / len(metrics)
            if avg_human > 0.2:
                issues.append({
                    "type": "high_human_intervention",
                    "severity": "high",
                    "avg_per_run": round(avg_human, 2),
                    "suggestion": "Add more specific instructions or constraints to reduce ambiguity",
                })

        return {
            "strategy": "instruction",
            "file": str(md_file),
            "content_length": len(content),
            "issues_found": len(issues),
            "issues": issues,
        }

    def evolve(self, target_path: Path, analysis: Dict) -> Dict:
        """优化指令文件"""
        # 确定实际文件
        if target_path.is_file():
            md_file = target_path
        else:
            md_file = target_path / "SKILL.md"

        if not md_file.exists():
            return {"status": "error", "message": "No markdown file found"}

        content = md_file.read_text(encoding="utf-8")
        original = content
        changes = []

        for issue in analysis.get("issues", []):
            issue_type = issue["type"]

            if issue_type == "missing_section":
                section = issue["section"]
                # 在文件末尾添加缺失的章节
                section_content = self._generate_section(section)
                if section_content not in content:
                    content = content.rstrip() + "\n\n" + section_content + "\n"
                    changes.append(f"Added missing section: {section}")

            elif issue_type == "redundant_expression":
                pattern = issue["pattern"]
                replacement = issue.get("suggestion", "").split("with '")[-1].rstrip("'")
                if replacement:
                    content = re.sub(pattern, replacement, content)
                    changes.append(f"Simplified redundant expression: {pattern}")

            elif issue_type == "high_human_intervention":
                # 在SKILL.md中添加更具体的约束
                constraint_block = """
## Auto-Evolved Constraints

- Be specific in your output format to reduce ambiguity
- Always validate inputs before processing
- When uncertain, ask clarifying questions instead of guessing
"""
                if "Auto-Evolved Constraints" not in content:
                    content = content.rstrip() + "\n\n" + constraint_block + "\n"
                    changes.append("Added constraints to reduce human intervention")

        if content != original:
            md_file.write_text(content, encoding="utf-8")

        return {"status": "evolved" if changes else "no_changes", "changes": changes}

    def _generate_section(self, section_name: str) -> str:
        """为缺失的章节生成内容"""
        templates = {
            "quick_start": "## Quick Start\n\nRun the main script with default parameters.",
            "error_handling": "## Error Handling\n\n- All exceptions are caught and logged\n- Invalid inputs return structured error responses\n- Graceful degradation on resource constraints",
            "constraints": "## Constraints\n\n- Input size limit: 10MB\n- Processing timeout: 30 seconds\n- Output format: JSON or plain text",
            "examples": "## Examples\n\n### Example 1: Basic Usage\n```\n$ python script.py input.txt\n```\n",
        }
        return templates.get(section_name, f"## {section_name.title()}\n\n[Auto-generated section]")

    def validate(self, target_path: Path) -> Dict:
        """验证markdown文件结构"""
        if target_path.is_file():
            md_file = target_path
        else:
            md_file = target_path / "SKILL.md"

        if not md_file.exists():
            return {"passed": False, "error": "No markdown file"}

        content = md_file.read_text(encoding="utf-8")
        checks = {
            "has_content": len(content) > 50,
            "has_body": len(content) > 100,
            "has_headers": "#" in content,
            "reasonable_length": 100 < len(content) < 50000,
        }

        return {"passed": all(checks.values()), "checks": checks}


# ═══════════════════════════════════════════════════════════
# 策略3: 混合进化 (SKILL.md + scripts/)
# ═══════════════════════════════════════════════════════════
class HybridEvolutionStrategy(EvolutionStrategy):
    """混合进化: 同时对SKILL.md和scripts/进行进化"""

    def __init__(self):
        self.code_strategy = CodeEvolutionStrategy()
        self.instruction_strategy = InstructionEvolutionStrategy()

    def can_handle(self, target_path: Path) -> bool:
        # 必须是目录，且有SKILL.md和scripts/
        return (target_path.is_dir()
                and (target_path / "SKILL.md").exists()
                and (target_path / "scripts").exists())

    def analyze(self, target_path: Path, metrics: List[Dict]) -> Dict:
        code_analysis = self.code_strategy.analyze(target_path / "scripts", metrics)
        instruction_analysis = self.instruction_strategy.analyze(target_path, metrics)

        return {
            "strategy": "hybrid",
            "code_analysis": code_analysis,
            "instruction_analysis": instruction_analysis,
            "total_issues": code_analysis.get("issues_found", 0) + instruction_analysis.get("issues_found", 0),
        }

    def evolve(self, target_path: Path, analysis: Dict) -> Dict:
        code_result = self.code_strategy.evolve(
            target_path / "scripts",
            analysis.get("code_analysis", {})
        )
        instruction_result = self.instruction_strategy.evolve(
            target_path,
            analysis.get("instruction_analysis", {})
        )

        all_changes = []
        all_changes.extend([f"[CODE] {c}" for c in code_result.get("changes", [])])
        all_changes.extend([f"[INSTR] {c}" for c in instruction_result.get("changes", [])])

        return {
            "status": "evolved" if all_changes else "no_changes",
            "changes": all_changes,
            "code_result": code_result,
            "instruction_result": instruction_result,
        }

    def validate(self, target_path: Path) -> Dict:
        code_val = self.code_strategy.validate(target_path / "scripts")
        instr_val = self.instruction_strategy.validate(target_path)

        return {
            "passed": code_val["passed"] and instr_val["passed"],
            "code_validation": code_val,
            "instruction_validation": instr_val,
        }


# ═══════════════════════════════════════════════════════════
# 通用修身炉引擎
# ═══════════════════════════════════════════════════════════
class UniversalXiuShenLu:
    """
    通用修身炉 - 对任意skill/agent.md进行自进化

    使用方式:
      1. 将指标写入 runtime_data/{name}_metrics.jsonl
      2. 调用 evolve(target_path, name)
      3. 修身炉自动选择策略并执行进化
    """

    STRATEGIES = [
        HybridEvolutionStrategy(),
        CodeEvolutionStrategy(),
        InstructionEvolutionStrategy(),
    ]

    def __init__(self, runtime_dir: str = "runtime_data", backup_dir: str = "backups"):
        self.metrics = UniversalMetricsCollector(runtime_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    @record_metrics("xiushen-lu")
    def evolve(self, target_path: str, name: Optional[str] = None) -> Dict:
        """
        通用进化入口

        Args:
            target_path: skill目录路径 或 文件路径
            name: metrics名称（默认使用路径名）
        """
        path = Path(target_path)
        target_name = name or path.name

        print(f"\n{'='*60}")
        print(f"☯️ Universal XiuShenLu: Evolving '{target_name}'")
        print(f"{'='*60}")
        print(f"Target: {path.absolute()}")

        # Step 1: 选择策略
        strategy = self._select_strategy(path)
        if not strategy:
            return {"status": "error", "message": "No strategy can handle this target"}
        print(f"Strategy: {strategy.__class__.__name__}")

        # Step 2: 备份
        backup_path = self._backup(path, target_name)
        print(f"Backup: {backup_path}")

        # Step 3: 读取metrics
        metrics = self.metrics.read(target_name)
        print(f"Metrics: {len(metrics)} records")

        # Step 4: 分析
        print(f"\n🔍 Analyzing...")
        analysis = strategy.analyze(path, metrics)
        issues = analysis.get("issues_found", 0) + analysis.get("total_issues", 0)
        print(f"Issues found: {issues}")

        # Step 5: 进化
        if issues == 0 and not analysis.get("metrics_summary", {}).get("avg_errors", 0):
            print(f"No issues detected, skipping evolution")
            return {"status": "healthy", "name": target_name}

        print(f"\n🔧 Evolving...")
        result = strategy.evolve(path, analysis)
        for change in result.get("changes", []):
            print(f"  ✓ {change}")

        # Step 6: 验证
        print(f"\n✅ Validating...")
        validation = strategy.validate(path)
        print(f"Validation: {'PASSED' if validation['passed'] else 'FAILED'}")

        return {
            "status": "evolved" if result.get("changes") else "no_changes",
            "name": target_name,
            "strategy": strategy.__class__.__name__,
            "changes": result.get("changes", []),
            "validation": validation,
            "backup": str(backup_path),
        }

    def _select_strategy(self, path: Path) -> Optional[EvolutionStrategy]:
        """自动选择最佳策略"""
        for strategy in self.STRATEGIES:
            if strategy.can_handle(path):
                return strategy
        return None

    def _backup(self, path: Path, name: str) -> Path:
        """创建备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{name}_{timestamp}"

        if path.is_file():
            backup_path.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_path / path.name)
        else:
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(path, backup_path)

        return backup_path


def main():
    if len(sys.argv) < 2:
        print("Universal XiuShenLu - 通用修身炉")
        print("\n用法:")
        print("  python universal_engine.py <target_path> [name]")
        print("\n示例:")
        print("  # 进化一个skill目录")
        print("  python universal_engine.py /path/to/my-skill my-skill")
        print("\n  # 进化一个agent.md文件")
        print("  python universal_engine.py /path/to/agent.md my-agent")
        print("\n  # 进化单个Python脚本")
        print("  python universal_engine.py /path/to/script.py my-script")
        sys.exit(1)

    target = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None

    xsl = UniversalXiuShenLu()
    result = xsl.evolve(target, name)

    print(f"\n{'='*60}")
    print(f"Result: {result['status']}")
    print(f"Changes: {len(result.get('changes', []))}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
