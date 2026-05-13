"""
under-one.skills — 八奇技Agent运维框架

Usage:
    from under_one import ContextGuard, PriorityEngine, ToolOrchestrator
    
    guard = ContextGuard()
    result = guard.run(conversation_history)
"""

__version__ = "10.0.0"
__all__ = [
    "ContextGuard",
    "CommandFactory",
    "InsightRadar",
    "ToolForge",
    "PriorityEngine",
    "KnowledgeDigest",
    "PersonaGuard",
    "ToolOrchestrator",
    "EcosystemHub",
    "EvolutionEngine",
    "load_config",
    "get_logger",
]

import json
import importlib.util
import copy
import logging
import os
import io
import sys
import tempfile
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

# ── 配置加载 ──
CONFIG_PATHS = [
    "under-one.yaml",
    "../under-one.yaml",
    "~/.under-one/under-one.yaml",
    "/etc/under-one/under-one.yaml",
]


def load_config() -> Dict[str, Any]:
    """加载全局配置，按优先级搜索配置文件"""
    for p in CONFIG_PATHS:
        path = Path(p).expanduser()
        if path.exists():
            try:
                import yaml
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except ImportError:
                pass
    return {}


def get_logger(name: str = "under-one") -> logging.Logger:
    """获取统一日志记录器"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def _find_skill_dir() -> Path:
    """自动查找 skill 目录。返回指向 underone/skills/ 的 Path，或兼容旧布局返回 repo 根。"""
    candidates = [
        # Python 包位于 underone/under_one/，skills 位于同级 underone/skills/
        Path(__file__).parent.parent / "skills",
        # 兼容：从 repo 根运行
        Path.cwd() / "underone" / "skills",
        Path.cwd() / "skills",
        Path.cwd(),
        # 全局安装
        Path.home() / ".under-one/skills",
    ]
    for c in candidates:
        if (c / "qiti-yuanliu").exists():
            return c
    raise RuntimeError("找不到 skill 目录。请确保在正确的工作目录中运行，或 pip install -e underone/")


def _run_script(skill_dir_name: str, script_name: str, *args, input_data=None) -> Dict[str, Any]:
    """统一执行skill脚本的辅助函数"""
    import subprocess
    skill_dir = _find_skill_dir() / skill_dir_name / "scripts"
    script = skill_dir / script_name
    if not script.exists():
        return {"success": False, "error": f"脚本不存在: {script}"}
    cmd = [sys.executable, str(script)] + list(args)
    stdin = json.dumps(input_data) if input_data is not None else None
    result = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=60)
    output = result.stdout.strip()
    # 尝试解析JSON输出
    try:
        parsed = json.loads(output) if output else {}
    except json.JSONDecodeError:
        parsed = {"raw_output": output}
    parsed["success"] = result.returncode == 0
    if result.stderr:
        parsed["stderr"] = result.stderr[:500]
    return parsed


@lru_cache(maxsize=None)
def _load_skill_module(skill_dir_name: str, script_name: str):
    """按文件路径加载 skill 脚本模块，避免依赖 CLI 文本输出。"""
    skill_dir = _find_skill_dir() / skill_dir_name / "scripts"
    script = skill_dir / script_name
    if not script.exists():
        raise FileNotFoundError(f"脚本不存在: {script}")

    module_name = f"under_one_runtime_{skill_dir_name}_{script_name}".replace("-", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块: {script}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _call_silently(fn, *args, **kwargs):
    """执行会打印进度的函数时，静默收集输出。"""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = fn(*args, **kwargs)
    return result


# ── Skill基类 ──
class BaseSkill:
    """所有skill的基类，提供统一接口"""
    skill_name: str = "base"
    skill_version: str = "v0.1.0"

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or load_config()
        self.logger = get_logger(self.skill_name)

    def run(self, input_data: Any) -> Dict[str, Any]:
        """执行skill核心逻辑，子类必须实现"""
        raise NotImplementedError

    def export_metrics(self, result: Dict[str, Any]):
        """导出运行时指标到 runtime_data/"""
        metrics_dir = Path("runtime_data")
        metrics_dir.mkdir(exist_ok=True)
        entry = {
            "skill_name": self.skill_name,
            "timestamp": datetime.now().isoformat(),
            "success": result.get("success", True),
            "quality_score": result.get("quality_score", result.get("score", 80)),
            "error_count": result.get("error_count", 0),
        }
        with open(metrics_dir / f"{self.skill_name}_metrics.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── 十技完整实现 ──
class ContextGuard(BaseSkill):
    """炁体源流 — 本源自省与稳态自愈。检测漂移、提炼规则、生成修正路径。"""
    skill_name = "qiti-yuanliu"

    def run(self, context: list) -> Dict[str, Any]:
        """
        扫描上下文健康状态。
        Args:
            context: 对话轮次列表 [{"role": "user", "content": "..."}, ...]
        Returns:
            {"health_score": float, "entropy": float, "alerts": list, "success": bool}
        """
        self.logger.info(f"扫描{len(context)}轮对话并提炼炁体规则")
        mod = _load_skill_module("qiti-yuanliu", "entropy_scanner.py")
        normalized_context = self._normalize_context(context)
        result = mod.QiTiScanner(normalized_context).scan()
        result["success"] = True
        self_evolution = result.get("self_evolution", {})
        result.setdefault("origin_anchor", self_evolution.get("origin_core", {}).get("goal_anchor"))
        result.setdefault("rule_candidates", self_evolution.get("rule_candidates", []))

        repair_handoff = result.get("repair_handoff")
        if repair_handoff:
            result["repair_handoff_execution"] = self._execute_repair_handoff(
                normalized_context, result, repair_handoff
            )

        result["stability_execution"] = self._build_stability_execution(
            result, result.get("repair_handoff_execution")
        )

        return result

    def _normalize_context(self, context: list) -> list:
        normalized = []
        for idx, msg in enumerate(context, start=1):
            if isinstance(msg, str):
                normalized.append({"role": "unknown", "content": msg, "round": idx})
                continue
            item = dict(msg)
            if "content" not in item and "text" in item:
                item["content"] = item["text"]
            item.setdefault("role", "unknown")
            item.setdefault("round", idx)
            normalized.append(item)
        return normalized

    def _execute_repair_handoff(
        self, context: list, scan_result: Dict[str, Any], repair_handoff: Dict[str, Any]
    ) -> Dict[str, Any]:
        target_skill = repair_handoff.get("target_skill")
        if target_skill != "dalu-dongguan":
            return {
                "status": "skipped",
                "target_skill": target_skill,
                "reason": "unsupported_target_skill",
            }

        segments = self._build_repair_segments(context, scan_result, repair_handoff)
        trace = InsightRadar(self.config).run(segments)
        return {
            "status": "completed" if trace.get("success") else "failed",
            "target_skill": target_skill,
            "input_segments": segments,
            "trace": trace,
        }

    def _build_repair_segments(
        self, context: list, scan_result: Dict[str, Any], repair_handoff: Dict[str, Any]
    ) -> list:
        round_lookup = {msg.get("round"): msg for msg in context}
        evidence_by_round: Dict[Any, list] = {}
        for item in repair_handoff.get("evidence", []):
            evidence_by_round.setdefault(item.get("round"), []).append(item)

        segments = []
        goal_text = ""
        if context:
            goal_text = context[0].get("content", "")
            if goal_text:
                segments.append({"source": "goal-anchor", "content": f"原始目标: {goal_text}"})

        for round_num in repair_handoff.get("contradiction_rounds", []):
            msg = round_lookup.get(round_num)
            if not msg:
                continue
            signals = []
            for evidence in evidence_by_round.get(round_num, []):
                signal = evidence.get("keyword") or evidence.get("pattern") or evidence.get("type")
                if signal:
                    signals.append(str(signal))
            signal_text = " ".join(signals)
            content = msg.get("content", "")
            segments.append(
                {
                    "source": f"round-{round_num}",
                    "content": f"第{round_num}轮 {msg.get('role', 'unknown')}: {content} 诊断信号: {signal_text}".strip(),
                }
            )

        alert_digest = " | ".join(alert.get("message", "") for alert in scan_result.get("alerts", [])[:3])
        recommendation_digest = " | ".join(scan_result.get("recommendations", [])[:2])
        round_digest = " | ".join(
            msg.get("content", "")
            for round_num in repair_handoff.get("contradiction_rounds", [])
            for msg in [round_lookup.get(round_num)]
            if msg and msg.get("content", "")
        )
        bridge = " | ".join(
            bit
            for bit in [
                f"原始目标: {goal_text}" if goal_text else "",
                f"矛盾摘录: {round_digest}" if round_digest else "",
                repair_handoff.get("summary", ""),
                alert_digest,
                recommendation_digest,
            ]
            if bit
        )
        segments.append({"source": "repair-bridge", "content": bridge})
        segments.append({"source": "repair-handoff", "content": repair_handoff.get("summary", "")})
        return segments

    def _build_stability_execution(
        self, scan_result: Dict[str, Any], repair_execution: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        contract = scan_result.get("stability_contract") or {}
        escalation = scan_result.get("escalation_contract") or {}
        targets = contract.get("verification_targets") or {}
        metrics = scan_result.get("metrics") or {}
        repair_handoff = scan_result.get("repair_handoff")
        repair_status = (repair_execution or {}).get(
            "status", "not_needed" if not repair_handoff else "pending"
        )
        handoff_completed = repair_status == "completed"

        pending_blockers = []
        if targets.get("requires_handoff_completion") and not handoff_completed:
            pending_blockers.append("repair_handoff 尚未完成")
        if metrics.get("health_score", 0) < targets.get("health_score_min", 0):
            pending_blockers.append("health_score 未达到恢复阈值")
        if metrics.get("consistency", 0) < targets.get("consistency_min", 0):
            pending_blockers.append("consistency 未达到恢复阈值")
        if metrics.get("alignment", 0) < targets.get("alignment_min", 0):
            pending_blockers.append("alignment 未达到恢复阈值")
        if metrics.get("entropy_level") not in set(targets.get("allowed_entropy_levels", [])):
            pending_blockers.append("entropy_level 超出允许范围")
        if escalation.get("manual_review_required"):
            pending_blockers.append("需要人工确认")

        resume_ready = not pending_blockers
        if resume_ready:
            next_action = "恢复受控自演化并继续下一轮炁循环"
        elif repair_handoff and not handoff_completed:
            next_action = f"等待 {repair_handoff.get('target_skill')} 修复结果后再校验恢复门"
        else:
            next_action = "继续执行 repair_plan，暂不恢复自演化"

        return {
            "freeze_applied": contract.get("freeze_self_evolution", False),
            "mutation_mode": contract.get("mutation_budget", {}).get("mode"),
            "repair_handoff_status": repair_status,
            "manual_review_required": escalation.get("manual_review_required", False),
            "resume_ready": resume_ready,
            "pending_blockers": pending_blockers,
            "next_action": next_action,
            "verification_snapshot": {
                "health_score": metrics.get("health_score"),
                "consistency": metrics.get("consistency"),
                "alignment": metrics.get("alignment"),
                "entropy_level": metrics.get("entropy_level"),
                "repair_handoff_completed": handoff_completed,
            },
        }


class CommandFactory(BaseSkill):
    """通天箓 — 瞬发指令工厂。将复杂任务拆解为可执行步骤链。"""
    skill_name = "tongtian-lu"

    def run(self, task: str) -> Dict[str, Any]:
        """
        拆解任务为可执行符箓链。
        Args:
            task: 自然语言描述的任务，如"分析竞品数据并生成报告"
        Returns:
            {"dimensions": list, "conflicts": list, "curse_level": str, "success": bool}
        """
        self.logger.info(f"拆解任务: {task[:50]}")
        try:
            mod = _load_skill_module("tongtian-lu", "fu_generator.py")
            result = mod.FuGenerator(task).generate()
            result["success"] = True
        except Exception:
            result = _run_script("tongtian-lu", "fu_generator.py", task)

        talisman_list = result.get("talisman_list", [])
        result.setdefault("dimensions", len(talisman_list) if isinstance(talisman_list, list) else 1)
        result.setdefault("curse_level", result.get("curse_level", "low"))
        return result


class InsightRadar(BaseSkill):
    """大罗洞观 — 全局洞察雷达。跨文档/跨轮次发现隐藏关联。"""
    skill_name = "dalu-dongguan"

    def run(self, segments: list) -> Dict[str, Any]:
        """
        分析多段文本间的关联。
        Args:
            segments: 文本段落列表 [{"id": "s1", "text": "..."}, ...]
        Returns:
            {"links": list, "mermaid": str, "success": bool}
        """
        self.logger.info(f"分析{len(segments)}段文本的关联")
        mod = _load_skill_module("dalu-dongguan", "link_detector.py")
        normalized_segments = self._normalize_segments(segments)
        result = mod.LinkDetector(normalized_segments).detect()
        result["success"] = True
        return result

    def _normalize_segments(self, segments: list) -> list:
        normalized = []
        for idx, segment in enumerate(segments, start=1):
            if isinstance(segment, str):
                normalized.append({"source": f"段{idx}", "content": segment})
                continue

            item = dict(segment)
            source = item.get("source") or item.get("id") or f"段{idx}"
            content = item.get("content")
            if content is None:
                content = item.get("text")
            if content is None:
                content = json.dumps(item, ensure_ascii=False)
            normalized.append({"source": source, "content": content})
        return normalized


class ToolForge(BaseSkill):
    """神机百炼 — 自主工具锻造。需求描述→可运行Python脚本+测试+契约。"""
    skill_name = "shenji-bailian"

    def run(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据需求生成工具脚本。
        Args:
            requirement: {"name": "工具名", "inputs": [...], "outputs": [...], "description": "..."}
        Returns:
            {"tool_code": str, "test_code": str, "contract": str, "success": bool}
        """
        self.logger.info(f"锻造工具: {requirement.get('name', 'unnamed')}")
        try:
            mod = _load_skill_module("shenji-bailian", "tool_factory.py")
            result = mod.ToolFactory(requirement).forge()
            result["success"] = True
            return result
        except Exception:
            return _run_script("shenji-bailian", "tool_factory.py", input_data=requirement)


class PriorityEngine(BaseSkill):
    """风后奇门 — 任务优先级引擎。九维度评分+八门映射+蒙特卡洛验证。"""
    skill_name = "fenghou-qimen"

    def run(self, tasks: list) -> Dict[str, Any]:
        """
        对任务列表进行优先级排序。
        Args:
            tasks: [{"name": "任务名", "urgency": 1-5, "importance": 1-5, ...}, ...]
        Returns:
            {"execution_plan": list, "top_gate": str, "success": bool}
        """
        self.logger.info(f"排序{len(tasks)}个任务")
        try:
            mod = _load_skill_module("fenghou-qimen", "priority_engine.py")
            result = mod.PriorityEngine(tasks).run()
            result["success"] = True
            return result
        except Exception:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(tasks, f)
                tmp = f.name
            try:
                return _run_script("fenghou-qimen", "priority_engine.py", tmp)
            finally:
                Path(tmp).unlink(missing_ok=True)


class KnowledgeDigest(BaseSkill):
    """六库仙贼 — 知识消化器。可信度分级+消化率评估+保鲜期追踪。"""
    skill_name = "liuku-xianzei"

    def run(self, items: list) -> Dict[str, Any]:
        """
        评估知识条目的消化质量。
        Args:
            items: [{"source": "来源", "content": "内容", "credibility": "S/A/B/C"}, ...]
        Returns:
            {"avg_digestion_rate": float, "distribution": dict, "success": bool}
        """
        self.logger.info(f"消化{len(items)}条知识")
        try:
            mod = _load_skill_module("liuku-xianzei", "knowledge_digest.py")
            result = mod.KnowledgeDigest(items).digest()
            result["success"] = True
            return result
        except Exception:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(items, f)
                tmp = f.name
            try:
                return _run_script("liuku-xianzei", "knowledge_digest.py", tmp)
            finally:
                Path(tmp).unlink(missing_ok=True)


class PersonaGuard(BaseSkill):
    """双全手 — 记忆/人格手术台。DNA护栏 + 改写方案 + 污染风险控制。"""
    skill_name = "shuangquanshou"

    STYLE_DIMENSIONS = ("tone", "formality", "detail_level", "structure")

    def run(self, profile: Any) -> Dict[str, Any]:
        """
        校验会话是否符合人格DNA。
        Args:
            profile: 人格档案 dict，或兼容旧版的 session_log list
        Returns:
            {"allow": bool, "violation_count": int, "consistency": float, "success": bool}
        """
        normalized_profile = self._normalize_profile(profile)
        self.logger.info(
            f"校验{len(normalized_profile.get('history', []))}轮会话的人格一致性"
        )
        try:
            mod = _load_skill_module("shuangquanshou", "dna_validator.py")
            result = mod.DNAValidator(normalized_profile).validate()
            result["success"] = True
        except Exception:
            result = self._run_cli_fallback(normalized_profile)

        result["allow"] = result.get("can_switch", False)
        result["violation_count"] = len(result.get("dna_violations", []))
        deviation = result.get("deviation_score", 0.0) or 0.0
        result["consistency"] = round(max(0.0, 1.0 - float(deviation)), 3)
        result.setdefault("primary_domain", (result.get("surgery_plan") or [{}])[0].get("domain"))
        patch_simulation = self._simulate_rewrite_patch(normalized_profile, result.get("rewrite_patch", {}))
        result["patch_simulation"] = patch_simulation
        result["applied_profile_preview"] = patch_simulation.get("profile_preview")
        result["rollback_profile_preview"] = patch_simulation.get("rollback_preview")
        return result

    def _normalize_profile(self, profile: Any) -> Dict[str, Any]:
        if isinstance(profile, list):
            return self._profile_from_legacy_session(profile)
        if not isinstance(profile, dict):
            raise TypeError("PersonaGuard expects a profile dict or legacy session_log list")

        normalized = dict(profile)
        normalized["current_style"] = self._coerce_style_map(normalized.get("current_style"))
        dna_expectation = normalized.get("dna_expectation", normalized.get("dna"))
        normalized["dna_expectation"] = self._coerce_style_map(dna_expectation)
        normalized["dna_core"] = self._coerce_dict(normalized.get("dna_core"))
        normalized["requested_change"] = self._coerce_dict(normalized.get("requested_change"))
        normalized["history"] = self._coerce_history(normalized.get("history"))
        return normalized

    def _profile_from_legacy_session(self, session_log: list) -> Dict[str, Any]:
        style_snapshots = [
            snapshot
            for snapshot in (self._coerce_style_map(item) for item in session_log if isinstance(item, dict))
            if snapshot
        ]
        current_style = style_snapshots[-1] if style_snapshots else {}
        dna_expectation = style_snapshots[0] if style_snapshots else dict(current_style)
        history = []
        for idx, item in enumerate(session_log, start=1):
            if isinstance(item, dict):
                style_label = item.get("style") or item.get("mode") or item.get("persona")
                if not style_label:
                    snapshot = self._coerce_style_map(item)
                    if snapshot:
                        style_label = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
                history.append({"style": str(style_label or f"round-{idx}"), "round": idx})
            else:
                history.append({"style": str(item), "round": idx})
        return {
            "current_style": current_style,
            "dna_expectation": dna_expectation,
            "dna_core": {},
            "requested_change": {},
            "history": history,
        }

    def _coerce_style_map(self, value: Any) -> Dict[str, float]:
        if not isinstance(value, dict):
            return {}
        snapshot: Dict[str, float] = {}
        for key in self.STYLE_DIMENSIONS:
            raw = value.get(key)
            if isinstance(raw, bool):
                continue
            if isinstance(raw, (int, float)):
                snapshot[key] = raw
                continue
            if isinstance(raw, str):
                try:
                    snapshot[key] = float(raw) if "." in raw else int(raw)
                except ValueError:
                    continue
        return snapshot

    def _coerce_dict(self, value: Any) -> Dict[str, Any]:
        return dict(value) if isinstance(value, dict) else {}

    def _coerce_history(self, value: Any) -> list:
        if not isinstance(value, list):
            return []
        history = []
        for idx, item in enumerate(value, start=1):
            if isinstance(item, dict):
                entry = dict(item)
                entry.setdefault("round", idx)
                if "style" not in entry and "mode" in entry:
                    entry["style"] = entry["mode"]
                if "style" in entry and entry["style"] is not None:
                    entry["style"] = str(entry["style"])
                history.append(entry)
            else:
                history.append({"style": str(item), "round": idx})
        return history

    def _simulate_rewrite_patch(self, profile: Dict[str, Any], rewrite_patch: Dict[str, Any]) -> Dict[str, Any]:
        base_profile = copy.deepcopy(profile)
        preview_profile = copy.deepcopy(profile)
        applied_patch_items = []
        simulation = {
            "mode": rewrite_patch.get("mode"),
            "apply_ready": bool(rewrite_patch.get("apply_ready")),
            "applied": False,
            "applied_items": [],
            "skipped_items": [],
            "profile_preview": preview_profile,
            "rollback_preview": copy.deepcopy(preview_profile),
        }

        for item in rewrite_patch.get("items", []):
            target_path = item.get("target_path")
            status = item.get("status")
            if status != "planned":
                if status == "review":
                    reason = "requires_confirmation"
                elif status == "blocked":
                    reason = "blocked_by_guardrail"
                else:
                    reason = "not_planned"
                simulation["skipped_items"].append(
                    {
                        "domain": item.get("domain"),
                        "target_path": target_path,
                        "status": status,
                        "reason": reason,
                    }
                )
                continue

            operations = item.get("operations", [])
            if not target_path:
                simulation["skipped_items"].append(
                    {
                        "domain": item.get("domain"),
                        "target_path": target_path,
                        "status": status,
                        "reason": "missing_target_path",
                    }
                )
                continue

            target_state = preview_profile.get(target_path)
            if not isinstance(target_state, dict):
                target_state = {}
            else:
                target_state = dict(target_state)

            before_state = copy.deepcopy(target_state)
            for op in operations:
                key = str(op.get("path"))
                if op.get("op") == "remove":
                    target_state.pop(key, None)
                else:
                    target_state[key] = op.get("after")

            preview_profile[target_path] = target_state
            applied_patch_items.append(item)
            simulation["applied_items"].append(
                {
                    "domain": item.get("domain"),
                    "target_path": target_path,
                    "rollback_token": item.get("rollback_token"),
                    "operation_count": len(operations),
                    "before_state": before_state,
                    "after_state": copy.deepcopy(target_state),
                }
            )

        rollback_profile = copy.deepcopy(preview_profile)
        for item in reversed(applied_patch_items):
            target_path = item.get("target_path")
            operations = item.get("operations", [])
            target_state = rollback_profile.get(target_path)
            if not isinstance(target_state, dict):
                target_state = {}
            else:
                target_state = dict(target_state)

            for op in reversed(operations):
                key = str(op.get("path"))
                before = op.get("before")
                original_op = op.get("op")
                if original_op == "add":
                    target_state.pop(key, None)
                elif original_op == "remove":
                    target_state[key] = before
                elif before is None:
                    target_state.pop(key, None)
                else:
                    target_state[key] = before
            rollback_profile[target_path] = target_state

        simulation["rollback_preview"] = rollback_profile
        simulation["applied"] = bool(simulation["applied_items"])
        simulation["partial"] = bool(simulation["applied_items"]) and bool(simulation["skipped_items"])
        simulation["restored"] = rollback_profile == base_profile
        return simulation

    def _run_cli_fallback(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        import subprocess

        script = _find_skill_dir() / "shuangquanshou" / "scripts" / "dna_validator.py"
        if not script.exists():
            return {"success": False, "error": f"脚本不存在: {script}"}

        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script), str(profile_path)],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=60,
            )
            report_path = Path(tmpdir) / "dna_report.json"
            if report_path.exists():
                try:
                    parsed = json.loads(report_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    parsed = {"raw_output": result.stdout.strip()}
            else:
                parsed = {"raw_output": result.stdout.strip()}
            parsed["success"] = result.returncode == 0
            if result.stderr:
                parsed["stderr"] = result.stderr[:500]
            return parsed


class ToolOrchestrator(BaseSkill):
    """拘灵遣将 — 灵体统御中枢。主副灵调度、边界控制与反叛风险监控。"""
    skill_name = "juling-qianjiang"

    def __init__(self, config=None):
        super().__init__(config)
        jg = self.config.get("julingqianjiang", {})
        self.strategy = jg.get("strategy", "protect")

    def run(self, tasks: list, spirits: list) -> Dict[str, Any]:
        """
        调度多个工具执行任务。
        Args:
            tasks: [{"type": "search", "desc": "..."}, ...]
            spirits: [{"id": "api1", "capabilities": ["search"], "available": true}, ...]
        Returns:
            {"plan": list, "fallback_count": int, "avg_quality": float, "success": bool}
        """
        self.logger.info(f"调度{len(tasks)}个任务到{len(spirits)}个工具 (策略={self.strategy})")
        try:
            mod = _load_skill_module("juling-qianjiang", "dispatcher.py")
            result = mod.dispatch(tasks, spirits, strategy=self.strategy, formation=self.config.get("julingqianjiang", {}).get("formation"))
            result["success"] = True
            return result
        except Exception:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
                json.dump(tasks, tf)
                task_path = tf.name
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as sf:
                json.dump(spirits, sf)
                spirit_path = sf.name
            try:
                return _run_script("juling-qianjiang", "dispatcher.py", task_path, spirit_path, self.strategy)
            finally:
                Path(task_path).unlink(missing_ok=True)
                Path(spirit_path).unlink(missing_ok=True)


class EcosystemHub(BaseSkill):
    """八卦阵 — 中央协调器。十技状态监控+互斥仲裁+协同增益。"""
    skill_name = "bagua-zhen"

    def run(self) -> Dict[str, Any]:
        """
        扫描十技生态全景。
        Returns:
            {"ecosystem_level": str, "average_quality": float, "skill_states": dict, "success": bool}
        """
        self.logger.info("扫描十技生态全景")
        try:
            mod = _load_skill_module("bagua-zhen", "coordinator.py")
            result = _call_silently(mod.coordinate, str(_find_skill_dir()))
            result["success"] = True
            return result
        except Exception:
            return _run_script("bagua-zhen", "coordinator.py")


class EvolutionEngine(BaseSkill):
    """修身炉 — 自进化引擎。运行时指标分析+自动参数优化。"""
    skill_name = "xiushen-lu"

    def run(self, target_skill: Optional[str] = None) -> Dict[str, Any]:
        """
        启动自进化周期。
        Args:
            target_skill: 指定进化的skill名称 (None=全部)
        Returns:
            {"evolved": int, "failed": int, "unchanged": int, "success": bool}
        """
        self.logger.info(f"启动修身炉进化 (目标={target_skill or '全部'})")
        skill_dir = str(_find_skill_dir())
        try:
            mod = _load_skill_module("xiushen-lu", "core_engine.py")
            core = mod.XiuShenLuCoreV7(skill_dir, apply_changes=False, persist_adaptive=False)
            result = _call_silently(core.run_evolution_cycle, target_skill)
            result["success"] = True
            return result
        except Exception:
            args = [skill_dir]
            if target_skill:
                args.append(target_skill)
            return _run_script("xiushen-lu", "core_engine.py", *args)
