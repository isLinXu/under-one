#!/usr/bin/env python3
"""
skill_showcase.py — 全量 10-skill 可运行展示脚本

默认行为：
- 从源码 checkout 直接运行，无需先 pip install -e
- 依次执行 10 个 under-one 包装层 API
- 为每个 skill 分配独立沙箱目录，避免互相污染
- 生成结构化 JSON 报告，方便回归、安装验证与宿主集成前检查

用法：
    python underone/examples/skill_showcase.py
    python underone/examples/skill_showcase.py --skills priority-engine persona-guard
    python underone/examples/skill_showcase.py --workspace /tmp/underone-showcase
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

# 允许从仓库根目录直接运行，无需先安装 editable package。
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from under_one import (  # noqa: E402
    CommandFactory,
    ContextGuard,
    EcosystemHub,
    EvolutionEngine,
    InsightRadar,
    KnowledgeDigest,
    PersonaGuard,
    PriorityEngine,
    ToolForge,
    ToolOrchestrator,
)


@dataclass(frozen=True)
class SkillSpec:
    skill_id: str
    internal_id: str
    class_name: str
    title: str
    runner: Callable[[], Dict[str, Any]]
    summarizer: Callable[[Dict[str, Any]], Dict[str, Any]]


def _safe_number(value: Any, digits: int = 2) -> Optional[float]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), digits)
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, set):
        return sorted(_jsonable(item) for item in value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _priority_actions(result: Dict[str, Any]) -> List[str]:
    actions = []
    for item in result.get("priority_actions", [])[:3]:
        if isinstance(item, dict):
            label = item.get("id") or item.get("title") or item.get("action")
            if label:
                actions.append(str(label))
        elif item:
            actions.append(str(item))
    return actions


def _generated_files(workspace: Path) -> List[str]:
    files = []
    for path in sorted(workspace.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.name == ".DS_Store":
            continue
        files.append(str(path.relative_to(workspace)))
    return files


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    path.mkdir(parents=True, exist_ok=True)
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(previous)


def _run_context_guard() -> Dict[str, Any]:
    context = [
        {"role": "user", "content": "本轮先以 React 方案推进多端控制台。"},
        {"role": "assistant", "content": "收到，已记录 React 作为当前前端基线。"},
        {"role": "user", "content": "如果赶工不顺，也可以临时切回 Vue 进行试验。"},
        {"role": "assistant", "content": "我会保留 React 目标，同时标记 Vue 作为备选。"},
        {"role": "user", "content": "最终目标仍然是 React，只是希望先把风险列出来。"},
    ]
    return ContextGuard().run(context)


def _run_command_factory() -> Dict[str, Any]:
    return CommandFactory().run("分析竞品客服 Agent 的多宿主安装方案，并产出验证步骤与回滚清单")


def _run_insight_radar() -> Dict[str, Any]:
    segments = [
        {
            "id": "support-logs",
            "text": "客服 Agent 在高峰期会频繁调用搜索、表单填写与知识库检索，失败集中出现在浏览器回退环节。",
        },
        {
            "id": "ops-notes",
            "text": "近期事故复盘显示，浏览器任务失败后缺少统一降级策略，导致搜索和摘要子任务也一起中断。",
        },
        {
            "id": "design-brief",
            "text": "新方案要求把浏览器能力与摘要能力解耦，并在失败时自动切到只读搜索模式。",
        },
    ]
    return InsightRadar().run(segments)


def _run_tool_forge() -> Dict[str, Any]:
    requirement = {
        "name": "host-readiness-checker",
        "description": "生成一个检查多个宿主安装前置条件的分析型工具",
        "inputs": ["host profile", "install target", "skill selection"],
        "outputs": ["markdown checklist", "json readiness report"],
        "specialization": "analysis-skill",
    }
    return ToolForge().run(requirement)


def _run_priority_engine() -> Dict[str, Any]:
    tasks = [
        {
            "name": "修复多宿主安装中的 P0 路径错误",
            "urgency": 5,
            "importance": 5,
            "impact": 5,
            "dependency": 2,
            "resource_match": 5,
            "deadline_risk": 5,
            "reversibility": 4,
            "stakeholder": 5,
        },
        {
            "name": "补全每个 skill 的独立验证文档",
            "urgency": 4,
            "importance": 4,
            "impact": 4,
            "dependency": 2,
            "resource_match": 4,
            "deadline_risk": 4,
            "reversibility": 5,
            "stakeholder": 4,
        },
        {
            "name": "优化插图在 README 中的导航说明",
            "urgency": 2,
            "importance": 3,
            "impact": 3,
            "dependency": 1,
            "resource_match": 5,
            "deadline_risk": 2,
            "reversibility": 5,
            "stakeholder": 3,
        },
    ]
    return PriorityEngine().run(tasks)


def _run_knowledge_digest() -> Dict[str, Any]:
    items = [
        {
            "source": "incident-review",
            "content": "上线事故复盘显示，多宿主安装失败主要来自路径假设和入口脚本不一致，已在三个真实案例中复现。",
            "credibility": "S",
        },
        {
            "source": "field-notes",
            "content": "在 WorkBuddy 与 QClaw 中，独立安装和独立测试的体验明显优于整包覆盖安装。",
            "credibility": "A",
        },
        {
            "source": "design-memo",
            "content": "如果 README 中同时提供源码验证和宿主验证路径，Agent 首次接入时的错误率会显著下降。",
            "credibility": "A",
        },
    ]
    return KnowledgeDigest().run(items)


def _run_persona_guard() -> Dict[str, Any]:
    profile = {
        "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 4},
        "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 4},
        "dna_core": {"事实优先": "不编造验证结果", "边界透明": "需要说明风险与假设"},
        "memory_state": {"user_preference": "偏好直接可执行命令"},
        "requested_change": {
            "type": "记忆修订",
            "target": "把用户偏好更新为优先展示可复现命令和验证路径",
            "patch": {"user_preference": "优先展示可复现命令和验证路径"},
        },
        "history": [{"style": "professional", "round": 1}],
    }
    return PersonaGuard().run(profile)


def _run_tool_orchestrator() -> Dict[str, Any]:
    tasks = [
        {"type": "search", "desc": "检索宿主安装失败案例"},
        {"type": "browse", "desc": "打开一份宿主适配文档确认字段约定"},
        {"type": "code", "desc": "执行安装前自检脚本"},
    ]
    spirits = [
        {"id": "search-api", "capabilities": ["search"], "available": True, "quality_score": 0.93},
        {"id": "browser-bot", "capabilities": ["browse"], "available": False, "quality_score": 0.90},
        {"id": "ops-hybrid", "capabilities": ["browse", "code"], "available": True, "quality_score": 0.88},
    ]
    return ToolOrchestrator().run(tasks, spirits)


def _run_ecosystem_hub() -> Dict[str, Any]:
    return EcosystemHub().run()


def _run_evolution_engine() -> Dict[str, Any]:
    return EvolutionEngine().run("qiti-yuanliu")


def _summary_context_guard(result: Dict[str, Any]) -> Dict[str, Any]:
    metrics = result.get("metrics", {})
    return {
        "health_score": _safe_number(metrics.get("health_score")),
        "entropy_level": metrics.get("entropy_level"),
        "alert_count": len(result.get("alerts", [])),
        "repair_status": result.get("repair_handoff_execution", {}).get("status"),
        "priority_actions": _priority_actions(result),
    }


def _summary_command_factory(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "dimensions": result.get("dimensions"),
        "talisman_count": len(result.get("talisman_list", [])),
        "curse_level": result.get("curse_level"),
        "recommended_skill": result.get("dispatch_contract", {}).get("recommended_skill"),
    }


def _summary_insight_radar(result: Dict[str, Any]) -> Dict[str, Any]:
    hallucination_risk = result.get("hallucination_risk")
    if isinstance(hallucination_risk, dict):
        hallucination_risk = hallucination_risk.get("level")
    return {
        "segment_count": result.get("segment_count"),
        "link_count": len(result.get("links", [])),
        "anomaly_count": len(result.get("anomaly_signals", [])),
        "hallucination_risk": hallucination_risk,
    }


def _summary_tool_forge(result: Dict[str, Any]) -> Dict[str, Any]:
    deliverable_keys = ["tool_code", "test_code", "contract", "skill_markdown", "readme"]
    present = [key for key in deliverable_keys if result.get(key)]
    return {
        "artifact_type": result.get("artifact_type"),
        "tool_name": result.get("tool_name"),
        "deliverable_count": len(present),
        "quality_score": _safe_number(result.get("quality_score")),
    }


def _summary_priority_engine(result: Dict[str, Any]) -> Dict[str, Any]:
    plan = result.get("execution_plan", [])
    top = plan[0] if plan else {}
    return {
        "top_gate": top.get("gate") or result.get("top_gate"),
        "top_task": top.get("task") or top.get("name"),
        "plan_size": len(plan),
        "alternative_plan_count": len(result.get("alternative_plans", {})),
    }


def _summary_knowledge_digest(result: Dict[str, Any]) -> Dict[str, Any]:
    contamination_risk = result.get("contamination_risk")
    if isinstance(contamination_risk, dict):
        contamination_risk = contamination_risk.get("level")
    return {
        "avg_digestion_rate": _safe_number(result.get("avg_digestion_rate")),
        "knowledge_unit_count": len(result.get("knowledge_units", [])),
        "contamination_risk": contamination_risk,
        "priority_actions": _priority_actions(result),
    }


def _summary_persona_guard(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "can_switch": result.get("can_switch"),
        "consistency": _safe_number(result.get("consistency"), digits=3),
        "violation_count": result.get("violation_count"),
        "patch_applied": result.get("patch_simulation", {}).get("applied"),
    }


def _summary_tool_orchestrator(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "plan_size": len(result.get("plan", [])),
        "fallback_count": result.get("fallback_count"),
        "avg_quality": _safe_number(result.get("avg_quality")),
        "all_success": result.get("all_success"),
    }


def _summary_ecosystem_hub(result: Dict[str, Any]) -> Dict[str, Any]:
    weakest = []
    for item in result.get("weakest_skills", [])[:3]:
        if isinstance(item, dict):
            weakest.append(str(item.get("skill") or item.get("id") or item.get("name")))
        elif item:
            weakest.append(str(item))
    return {
        "ecosystem_level": result.get("ecosystem_level"),
        "average_quality": _safe_number(result.get("average_quality")),
        "weakest_skills": weakest,
    }


def _summary_evolution_engine(result: Dict[str, Any]) -> Dict[str, Any]:
    first = (result.get("results") or [{}])[0]
    analysis = first.get("analysis", {})
    return {
        "target_skill": first.get("skill"),
        "status": first.get("status"),
        "planned_total": result.get("summary", {}).get("total"),
        "bottleneck_type": analysis.get("bottleneck_type"),
    }


def _format_kv(summary: Dict[str, Any]) -> str:
    parts = []
    for key, value in summary.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            parts.append(f"{key}={','.join(str(item) for item in value)}")
        else:
            parts.append(f"{key}={value}")
    return " ".join(parts)


SKILL_SPECS: List[SkillSpec] = [
    SkillSpec("context-guard", "qiti-yuanliu", "ContextGuard", "炁体源流", _run_context_guard, _summary_context_guard),
    SkillSpec("command-factory", "tongtian-lu", "CommandFactory", "通天箓", _run_command_factory, _summary_command_factory),
    SkillSpec("insight-radar", "dalu-dongguan", "InsightRadar", "大罗洞观", _run_insight_radar, _summary_insight_radar),
    SkillSpec("tool-forge", "shenji-bailian", "ToolForge", "神机百炼", _run_tool_forge, _summary_tool_forge),
    SkillSpec("priority-engine", "fenghou-qimen", "PriorityEngine", "风后奇门", _run_priority_engine, _summary_priority_engine),
    SkillSpec("knowledge-digest", "liuku-xianzei", "KnowledgeDigest", "六库仙贼", _run_knowledge_digest, _summary_knowledge_digest),
    SkillSpec("persona-guard", "shuangquanshou", "PersonaGuard", "双全手", _run_persona_guard, _summary_persona_guard),
    SkillSpec("tool-orchestrator", "juling-qianjiang", "ToolOrchestrator", "拘灵遣将", _run_tool_orchestrator, _summary_tool_orchestrator),
    SkillSpec("ecosystem-hub", "bagua-zhen", "EcosystemHub", "八卦阵", _run_ecosystem_hub, _summary_ecosystem_hub),
    SkillSpec("evolution-engine", "xiushen-lu", "EvolutionEngine", "修身炉", _run_evolution_engine, _summary_evolution_engine),
]


def _build_alias_map(specs: Iterable[SkillSpec]) -> Dict[str, str]:
    alias_map: Dict[str, str] = {}
    for spec in specs:
        aliases = {
            spec.skill_id,
            spec.internal_id,
            spec.class_name,
            spec.skill_id.replace("-", ""),
            spec.internal_id.replace("-", ""),
            spec.class_name.lower(),
        }
        for alias in aliases:
            normalized = alias.strip().lower().replace("_", "-").replace(" ", "-")
            alias_map[normalized] = spec.skill_id
    return alias_map


ALIAS_MAP = _build_alias_map(SKILL_SPECS)
SPEC_BY_ID = {spec.skill_id: spec for spec in SKILL_SPECS}


def resolve_skill_selection(requested: Optional[List[str]]) -> List[SkillSpec]:
    if not requested:
        return SKILL_SPECS

    resolved: List[SkillSpec] = []
    seen = set()
    for raw in requested:
        normalized = raw.strip().lower().replace("_", "-").replace(" ", "-")
        skill_id = ALIAS_MAP.get(normalized)
        if not skill_id:
            choices = ", ".join(spec.skill_id for spec in SKILL_SPECS)
            raise ValueError(f"Unknown skill '{raw}'. Available: {choices}")
        if skill_id in seen:
            continue
        resolved.append(SPEC_BY_ID[skill_id])
        seen.add(skill_id)
    return resolved


def run_showcase(selected_skills: Optional[List[str]] = None, workspace_root: Optional[Path] = None) -> Dict[str, Any]:
    specs = resolve_skill_selection(selected_skills)
    keep_workspace = workspace_root is not None

    if keep_workspace:
        root = Path(workspace_root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        manager = None
    else:
        manager = tempfile.TemporaryDirectory(prefix="under-one-showcase-")
        root = Path(manager.name)

    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    results = []

    try:
        for spec in specs:
            skill_workspace = root / spec.skill_id
            started = time.perf_counter()
            with _working_directory(skill_workspace):
                try:
                    raw_result = spec.runner()
                    success = bool(raw_result.get("success", True))
                    error = raw_result.get("error")
                except Exception as exc:  # pragma: no cover
                    raw_result = {
                        "success": False,
                        "error": f"{exc.__class__.__name__}: {exc}",
                    }
                    success = False
                    error = raw_result["error"]
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            summary = spec.summarizer(raw_result)
            results.append(
                {
                    "id": spec.skill_id,
                    "internal_id": spec.internal_id,
                    "class_name": spec.class_name,
                    "title": spec.title,
                    "success": success,
                    "duration_ms": duration_ms,
                    "workspace": str(skill_workspace),
                    "generated_files": _generated_files(skill_workspace),
                    "summary": _jsonable(summary),
                    "result": _jsonable(raw_result),
                    "error": error,
                }
            )
    finally:
        if manager is not None:
            manager.cleanup()

    succeeded = sum(1 for item in results if item["success"])
    return {
        "generated_at": started_at,
        "project_root": str(ROOT),
        "workspace_mode": "persistent" if keep_workspace else "temporary",
        "workspace_root": str(root),
        "selected_skills": [spec.skill_id for spec in specs],
        "summary": {
            "requested": len(specs),
            "executed": len(results),
            "succeeded": succeeded,
            "failed": len(results) - succeeded,
        },
        "skills": results,
    }


def write_report(payload: Dict[str, Any], output_path: Path) -> None:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def print_summary(payload: Dict[str, Any]) -> None:
    print("=" * 72)
    print("UnderOne 10-skill showcase")
    print("=" * 72)
    print(f"skills={payload['summary']['executed']} success={payload['summary']['succeeded']} fail={payload['summary']['failed']}")
    print(f"workspace_mode={payload['workspace_mode']}")
    print("-" * 72)
    for item in payload["skills"]:
        status = "OK" if item["success"] else "FAIL"
        summary_line = _format_kv(item["summary"])
        print(f"{status:<5} {item['id']:<18} {item['duration_ms']:>7.1f}ms  {summary_line}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a full 10-skill UnderOne showcase")
    parser.add_argument(
        "--skills",
        nargs="+",
        help="Only run selected public IDs / internal IDs / wrapper class names",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "artifacts" / "skill_showcase.json"),
        help="Structured JSON report output path",
    )
    parser.add_argument(
        "--workspace",
        help="Optional persistent workspace root for generated per-skill sandboxes",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run_showcase(
        selected_skills=args.skills,
        workspace_root=Path(args.workspace) if args.workspace else None,
    )
    print_summary(payload)
    write_report(payload, Path(args.output))
    print("-" * 72)
    print(f"report={Path(args.output).expanduser().resolve()}")
    return 0 if payload["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
