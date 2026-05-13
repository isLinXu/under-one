#!/usr/bin/env python3
"""Unified skill effectiveness evaluation.

Runs one representative validation scenario per skill, combines that with
governance audit results, runtime metrics, and artifact presence, then writes
JSON/Markdown reports under `underone/reports/`.
"""

from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_ROOT = REPO_ROOT / "underone"
SKILLS_ROOT = PACKAGE_ROOT / "skills"
REPORTS_DIR = PACKAGE_ROOT / "reports"
ARTIFACTS_DIR = PACKAGE_ROOT / "artifacts"
RUNTIME_DIR = REPO_ROOT / "runtime_data"

sys.path.insert(0, str(PACKAGE_ROOT))

from under_one import (
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
from under_one.skill_bundle import verify_bundle_roundtrip
from under_one.skill_audit import audit_skills_root, write_audit_report
from skills.metrics_collector import get_recent_metrics


SKILL_META = {
    "qiti-yuanliu": {"label": "context-guard", "cn": "炁体源流", "artifact": None, "test_count": 15},
    "tongtian-lu": {"label": "command-factory", "cn": "通天箓", "artifact": "fu_plan.json", "test_count": 6},
    "dalu-dongguan": {"label": "insight-radar", "cn": "大罗洞观", "artifact": "link_report.json", "test_count": 7},
    "shenji-bailian": {"label": "tool-forge", "cn": "神机百炼", "artifact": None, "test_count": 4},
    "fenghou-qimen": {"label": "priority-engine", "cn": "风后奇门", "artifact": "priority_plan.json", "test_count": 7},
    "liuku-xianzei": {"label": "knowledge-digest", "cn": "六库仙贼", "artifact": "digest_report.json", "test_count": 6},
    "shuangquanshou": {"label": "persona-guard", "cn": "双全手", "artifact": "dna_report.json", "test_count": 5},
    "juling-qianjiang": {"label": "tool-orchestrator", "cn": "拘灵遣将", "artifact": "dispatch_report_v9.json", "test_count": 9},
    "bagua-zhen": {"label": "ecosystem-hub", "cn": "八卦阵", "artifact": "ecosystem_report_v10.json", "test_count": 3},
    "xiushen-lu": {"label": "evolution-engine", "cn": "修身炉", "artifact": None, "test_count": 9},
}


def summarize_runtime(skill_name: str) -> Dict[str, Any]:
    records = get_recent_metrics(skill_name, n=30, data_dir=RUNTIME_DIR)
    if not records:
        return {
            "record_count": 0,
            "success_rate": 0.0,
            "avg_quality": 0.0,
            "avg_duration_ms": 0.0,
            "avg_completeness": 0.0,
            "avg_consistency": 0.0,
            "avg_human_intervention": 0.0,
            "avg_error_count": 0.0,
        }
    durations = [r.get("duration_ms", 0) for r in records if isinstance(r.get("duration_ms", 0), (int, float))]
    qualities = [r.get("quality_score", 0) for r in records if isinstance(r.get("quality_score", 0), (int, float))]
    completeness = [r.get("output_completeness", 0) for r in records if isinstance(r.get("output_completeness", 0), (int, float))]
    consistencies = [r.get("consistency_score", 0) for r in records if isinstance(r.get("consistency_score", 0), (int, float))]
    successes = [1 if r.get("success") else 0 for r in records]
    errors = [r.get("error_count", 0) for r in records if isinstance(r.get("error_count", 0), (int, float))]
    human = [r.get("human_intervention", 0) for r in records if isinstance(r.get("human_intervention", 0), (int, float))]
    return {
        "record_count": len(records),
        "success_rate": round(sum(successes) / len(successes) * 100, 1),
        "avg_quality": round(statistics.mean(qualities), 1) if qualities else 0.0,
        "avg_duration_ms": round(statistics.mean(durations), 1) if durations else 0.0,
        "avg_completeness": round(statistics.mean(completeness), 1) if completeness else 0.0,
        "avg_consistency": round(statistics.mean(consistencies), 1) if consistencies else 0.0,
        "avg_human_intervention": round(statistics.mean(human), 2) if human else 0.0,
        "avg_error_count": round(statistics.mean(errors), 2) if errors else 0.0,
    }


def scenario_context_guard() -> Dict[str, Any]:
    result = ContextGuard().run(
        [
            {"role": "user", "content": "我们先用 React。", "round": 1},
            {"role": "assistant", "content": "好的，前端采用 React。", "round": 2},
            {"role": "user", "content": "不对，改成 Vue。", "round": 3},
            {"role": "assistant", "content": "已切换为 Vue。", "round": 4},
        ]
    )
    alert_count = len(result.get("alerts", []))
    repair_handoff = result.get("repair_handoff")
    repair_execution = result.get("repair_handoff_execution") or {}
    trace = repair_execution.get("trace", {})
    self_evolution = result.get("self_evolution", {})
    stability_contract = result.get("stability_contract", {})
    repair_plan = result.get("repair_plan", {})
    escalation_contract = result.get("escalation_contract", {})
    stability_execution = result.get("stability_execution", {})
    repair_executed = (
        repair_execution.get("status") == "completed" and trace.get("success") is True
    )
    passed = (
        result.get("success") is True
        and result["metrics"]["health_score"] >= 0
        and alert_count >= 1
        and len(self_evolution.get("rule_candidates", [])) >= 1
        and bool(stability_contract)
        and bool(repair_plan)
        and "resume_ready" in stability_execution
        and (not repair_handoff or repair_executed)
    )
    effect_summary = (
        f"refined {len(self_evolution.get('rule_candidates', []))} rule(s) "
        f"in phase={self_evolution.get('phase')} with health_score={result['metrics']['health_score']} "
        f"mode={stability_contract.get('operating_mode')}"
    )
    if repair_handoff:
        effect_summary += f" and handoff={repair_handoff.get('target_skill')}"
    if repair_executed:
        effect_summary += f" trace_links={trace.get('link_count', 0)}"
    return {
        "passed": passed,
        "effect_summary": effect_summary,
        "key_metrics": {
            "health_score": result["metrics"]["health_score"],
            "entropy": result["metrics"]["entropy"],
            "alert_count": alert_count,
            "repair_handoff_present": bool(repair_handoff),
            "repair_handoff_target": repair_handoff.get("target_skill") if repair_handoff else None,
            "repair_handoff_executed": repair_executed,
            "trace_link_count": trace.get("link_count", 0) if repair_executed else 0,
            "rule_candidate_count": len(self_evolution.get("rule_candidates", [])),
            "evolution_phase": self_evolution.get("phase"),
            "stability_mode": stability_contract.get("operating_mode"),
            "manual_review_required": escalation_contract.get("manual_review_required"),
            "resume_ready": stability_execution.get("resume_ready"),
        },
    }


def scenario_command_factory() -> Dict[str, Any]:
    result = CommandFactory().run("搜索竞品信息然后写高管报告")
    topo = result.get("topology", [])
    packets = result.get("command_packets", [])
    passed = (
        result.get("success") is True
        and len(result.get("talisman_list", [])) >= 2
        and len(packets) >= 2
        and result.get("dispatch_contract", {}).get("recommended_skill") == "juling-qianjiang"
    )
    return {
        "passed": passed,
        "effect_summary": f"generated {len(result.get('talisman_list', []))} talisman(s) and {len(packets)} command packet(s) with curse={result.get('curse_level')}",
        "key_metrics": {
            "talisman_count": len(result.get("talisman_list", [])),
            "command_packet_count": len(packets),
            "curse_level": result.get("curse_level"),
            "topology_length": len(topo),
        },
    }


def scenario_insight_radar() -> Dict[str, Any]:
    result = InsightRadar().run(
        [
            {"source": "A", "content": "缓存优化 接口响应 重试 控制 队列 治理"},
            {"source": "B", "content": "缓存优化 队列治理 可以减少 重试 次数 并改善 接口响应"},
            {"source": "C", "content": "因此必须认定量子好运引擎已经彻底证明所有问题都会自动消失"},
        ]
    )
    links = result.get("links", [])
    anomalies = result.get("anomaly_signals", [])
    insights = result.get("hidden_insights", [])
    hallucination = result.get("hallucination_risk", {})
    passed = (
        result.get("success") is True
        and len(links) >= 1
        and len(anomalies) >= 1
        and len(insights) >= 1
        and hallucination.get("level") in {"medium", "high"}
        and "graph" in result.get("mermaid_code", "")
    )
    return {
        "passed": passed,
        "effect_summary": (
            f"found {len(links)} link(s), {len(anomalies)} anomaly signal(s), "
            f"hallucination={hallucination.get('level')}"
        ),
        "key_metrics": {
            "link_count": len(links),
            "entity_count": result.get("entity_count", 0),
            "anomaly_count": len(anomalies),
            "hallucination_score": hallucination.get("score"),
            "hallucination_level": hallucination.get("level"),
            "hidden_insight_count": len(insights),
        },
    }


def scenario_tool_forge() -> Dict[str, Any]:
    result = ToolForge().run(
        {"name": "json-cleaner", "description": "清洗 JSON", "inputs": ["raw.json"], "outputs": ["clean.json"]}
    )
    passed = result.get("success") is True and len(result.get("files", {})) == 3 and "def main(" in result.get("tool_code", "")
    return {
        "passed": passed,
        "effect_summary": f"forged {len(result.get('files', {}))} file(s) including tool, test, and contract",
        "key_metrics": {
            "file_count": len(result.get("files", {})),
            "has_main": "def main(" in result.get("tool_code", ""),
            "has_tests": "def test_normal_case():" in result.get("test_code", ""),
        },
    }


def scenario_priority_engine() -> Dict[str, Any]:
    result = PriorityEngine().run(
        [
            {"name": "修复生产故障", "urgency": 5, "importance": 5, "dependency": 3, "resource_match": 5},
            {"name": "整理文档", "urgency": 2, "importance": 2, "dependency": 1, "resource_match": 3},
        ]
    )
    top = result.get("ranked_tasks", [{}])[0]
    phases = result.get("execution_phases", [])
    passed = result.get("success") is True and top.get("name") == "修复生产故障" and len(phases) >= 1
    return {
        "passed": passed,
        "effect_summary": f"ranked top task as {top.get('name')} with gate={top.get('gate')} and {len(phases)} phase(s)",
        "key_metrics": {
            "top_task": top.get("name"),
            "top_gate": top.get("gate"),
            "on_time_rate": result.get("monte_carlo", {}).get("on_time_rate"),
            "phase_count": len(phases),
        },
    }


def scenario_knowledge_digest() -> Dict[str, Any]:
    result = KnowledgeDigest().run(
        [
            {"source": "权威", "content": "核心结论：数据证明 X 有效，可用于生产部署并显著提升性能", "credibility": "S", "category": "技术方案"},
            {"source": "匿名", "content": "可能有用", "credibility": "C", "category": "默认"},
        ]
    )
    units = result.get("knowledge_units", [])
    contamination = result.get("contamination_risk", {})
    passed = (
        result.get("success") is True
        and len(units) >= 2
        and units[0]["digestion_rate"] != units[1]["digestion_rate"]
        and contamination.get("level") in {"medium", "high"}
        and len(result.get("inheritance_queue", [])) >= 1
        and len(result.get("quarantine_queue", [])) >= 1
    )
    return {
        "passed": passed,
        "effect_summary": (
            f"digested {len(units)} unit(s), inheritance={len(result.get('inheritance_queue', []))}, "
            f"quarantine={len(result.get('quarantine_queue', []))}, contamination={contamination.get('level')}"
        ),
        "key_metrics": {
            "avg_digestion_rate": result.get("avg_digestion_rate"),
            "distribution": result.get("distribution"),
            "review_items": len(result.get("review_schedule", [])),
            "inheritance_count": len(result.get("inheritance_queue", [])),
            "quarantine_count": len(result.get("quarantine_queue", [])),
            "contamination_score": contamination.get("score"),
            "contamination_level": contamination.get("level"),
        },
    }


def scenario_persona_guard() -> Dict[str, Any]:
    blocked_result = PersonaGuard().run(
        {
            "current_style": {"tone": 1, "formality": 1, "detail_level": 1, "structure": 1},
            "dna_expectation": {"tone": 5, "formality": 5, "detail_level": 5, "structure": 5},
            "dna_core": {"尊重": "不嘲讽贬低"},
            "requested_change": {"type": "嘲讽", "target": "尖刻", "patch": {"tone": 1}},
            "history": [{"style": "formal"}, {"style": "casual"}, {"style": "technical"}],
        }
    )
    editable_result = PersonaGuard().run(
        {
            "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {"诚信": "不编造"},
            "requested_change": {
                "type": "记忆修订",
                "target": "将用户偏好更新为更重视效率",
                "patch": {"user_preference": "更重视效率"},
            },
            "memory_state": {"user_preference": "偏好完整解释"},
            "history": [],
        }
    )
    blocked_patch = blocked_result.get("rewrite_patch", {})
    editable_patch = editable_result.get("rewrite_patch", {})
    editable_simulation = editable_result.get("patch_simulation", {})
    passed = (
        blocked_result.get("can_switch") is False
        and len(blocked_result.get("dna_violations", [])) >= 1
        and len(blocked_patch.get("items", [])) >= 1
        and editable_result.get("can_switch") is True
        and len(editable_patch.get("items", [])) >= 1
        and editable_simulation.get("applied") is True
        and editable_result.get("applied_profile_preview", {}).get("memory_state", {}).get("user_preference") == "更重视效率"
        and editable_result.get("rollback_profile_preview", {}).get("memory_state", {}).get("user_preference") == "偏好完整解释"
    )
    return {
        "passed": passed,
        "effect_summary": (
            f"blocked risky rewrite with mode={blocked_result.get('surgery_mode')} "
            f"and previewed safe memory surgery with {len(editable_patch.get('items', []))} patch item(s)"
        ),
        "key_metrics": {
            "blocked_can_switch": blocked_result.get("can_switch"),
            "blocked_violation_count": len(blocked_result.get("dna_violations", [])),
            "blocked_surgery_mode": blocked_result.get("surgery_mode"),
            "blocked_contamination_index": blocked_result.get("contamination_index"),
            "editable_can_switch": editable_result.get("can_switch"),
            "editable_consistency": editable_result.get("consistency"),
            "editable_rewrite_patch_items": len(editable_patch.get("items", [])),
            "editable_preview_applied": editable_simulation.get("applied"),
            "editable_rollback_restored": editable_simulation.get("restored"),
        },
    }


def scenario_tool_orchestrator() -> Dict[str, Any]:
    result = ToolOrchestrator().run(
        [{"type": "code", "query": "python"}, {"type": "code", "task": "analyze"}],
        [
            {"id": "coder", "capabilities": ["code"], "available": False, "quality_score": 0.95},
            {"id": "browser", "capabilities": ["browse"], "available": True, "quality_score": 0.9},
        ],
    )
    passed = (
        result.get("success") is True
        and result.get("fallback_count", 0) >= 1
        and result.get("avg_quality", 0) > 0
        and len(result.get("command_plan", [])) >= 1
        and all("recovery_plan" in item for item in result.get("command_plan", []))
        and "governance_summary" in result
    )
    return {
        "passed": passed,
        "effect_summary": (
            f"commanded {len(result.get('command_plan', []))} spirit packet(s) "
            f"with fallback_count={result.get('fallback_count')} avg_quality={result.get('avg_quality')} "
            f"manual_review={result.get('governance_summary', {}).get('manual_review_required')}"
        ),
        "key_metrics": {
            "fallback_count": result.get("fallback_count"),
            "avg_quality": result.get("avg_quality"),
            "all_success": result.get("all_success"),
            "command_plan_count": len(result.get("command_plan", [])),
            "rebellion_alerts": len(result.get("rebellion_alerts", [])),
            "manual_review_required": result.get("governance_summary", {}).get("manual_review_required"),
            "high_risk_tasks": result.get("governance_summary", {}).get("high_risk_tasks"),
        },
    }


def scenario_ecosystem_hub() -> Dict[str, Any]:
    result = EcosystemHub().run()
    passed = result.get("success") is True and "skill_states" in result and "average_quality" in result
    return {
        "passed": passed,
        "effect_summary": f"aggregated {len(result.get('skill_states', {}))} skill state(s)",
        "key_metrics": {
            "active_skills": result.get("active_skills"),
            "average_quality": result.get("average_quality"),
            "ecosystem_level": result.get("ecosystem_level"),
        },
    }


def scenario_evolution_engine() -> Dict[str, Any]:
    records = get_recent_metrics("qiti-yuanliu", n=20, data_dir=RUNTIME_DIR)
    result = EvolutionEngine().run("qiti-yuanliu")
    first = (result.get("results") or [{}])[0]
    analysis = first.get("analysis", {})
    record_count = len(records)
    passed = result.get("success") is True and first.get("skill") == "qiti-yuanliu" and (
        (record_count >= 10 and first.get("status") in {"planned", "no_action"})
        or (record_count < 10 and first.get("status") == "planned" and first.get("planned_evolution_type") == "bootstrap")
    )
    return {
        "passed": passed,
        "effect_summary": f"wrapped evolution cycle with status={first.get('status')} and record_count={record_count}",
        "key_metrics": {
            "status": first.get("status"),
            "summary_total": result.get("summary", {}).get("total"),
            "record_count": record_count,
            "planned_evolution_type": first.get("planned_evolution_type"),
            "bottleneck_type": analysis.get("bottleneck_type"),
            "avg_output_completeness": analysis.get("avg_output_completeness"),
            "avg_consistency_score": analysis.get("avg_consistency_score"),
            "avg_human_intervention": analysis.get("avg_human_intervention"),
        },
    }


SCENARIOS = {
    "qiti-yuanliu": scenario_context_guard,
    "tongtian-lu": scenario_command_factory,
    "dalu-dongguan": scenario_insight_radar,
    "shenji-bailian": scenario_tool_forge,
    "fenghou-qimen": scenario_priority_engine,
    "liuku-xianzei": scenario_knowledge_digest,
    "shuangquanshou": scenario_persona_guard,
    "juling-qianjiang": scenario_tool_orchestrator,
    "bagua-zhen": scenario_ecosystem_hub,
    "xiushen-lu": scenario_evolution_engine,
}


def artifact_status(filename: str | None) -> Dict[str, Any]:
    if not filename:
        return {"expected": None, "present": False}
    path = ARTIFACTS_DIR / filename
    return {"expected": filename, "present": path.exists(), "path": str(path)}


def load_skill_alignment(skill_name: str) -> Dict[str, Any]:
    meta_path = SKILLS_ROOT / skill_name / "_skillhub_meta.json"
    if not meta_path.exists():
        return {}
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    alignment = payload.get("alignment")
    return alignment if isinstance(alignment, dict) else {}


def build_recommendations(
    skill_name: str,
    runtime: Dict[str, Any],
    scenario: Dict[str, Any],
    audit_item: Dict[str, Any],
    independent: Dict[str, Any],
) -> List[str]:
    recs: List[str] = []
    if not scenario.get("passed"):
        recs.append("Representative validation scenario did not pass; inspect behavior before release.")
    if not independent.get("passed", False):
        recs.append("Standalone bundle roundtrip did not pass; inspect install/validate/self-test outputs before distribution.")
    if runtime.get("record_count", 0) == 0:
        recs.append("No recent runtime metrics found; run the skill in a realistic workflow to gather evidence.")
        return recs
    if runtime.get("success_rate", 100) < 95:
        recs.append(f"Success rate is {runtime['success_rate']}%; prioritize failure-mode hardening.")
    if runtime.get("avg_quality", 100) < 80:
        recs.append(f"Average quality is {runtime['avg_quality']}; refine scoring heuristics or fallback behavior.")
    if runtime.get("avg_completeness", 100) < 85:
        recs.append(f"Average output completeness is {runtime['avg_completeness']}; tighten delivery contracts and missing-output checks.")
    if runtime.get("avg_consistency", 100) < 82:
        recs.append(f"Average consistency score is {runtime['avg_consistency']}; reduce conflicting branches and normalize output structure.")
    if runtime.get("avg_error_count", 0) > 0.2:
        recs.append(f"Average error count is {runtime['avg_error_count']}; tighten input validation and recovery paths.")
    if runtime.get("avg_human_intervention", 0) > 0.25:
        recs.append(f"Average human intervention is {runtime['avg_human_intervention']}; improve autonomy before expanding scope.")
    if audit_item.get("warnings"):
        recs.append("Governance warnings remain; fix documentation or metadata drift before distribution.")
    if (
        skill_name == "qiti-yuanliu"
        and scenario["key_metrics"].get("alert_count", 0) >= 3
        and not scenario["key_metrics"].get("repair_handoff_present", False)
    ):
        recs.append("Repeated contradiction alerts were detected; consider adding an automatic repair handoff after the second alert.")
    if (
        skill_name == "qiti-yuanliu"
        and scenario["key_metrics"].get("repair_handoff_present", False)
        and not scenario["key_metrics"].get("repair_handoff_executed", False)
    ):
        recs.append(
            f"Repair handoff is active; validate downstream routing into {scenario['key_metrics'].get('repair_handoff_target')} in integrated workflows."
        )
    if (
        skill_name == "qiti-yuanliu"
        and scenario["key_metrics"].get("manual_review_required")
        and scenario["key_metrics"].get("resume_ready")
    ):
        recs.append("Manual review is still required; avoid marking the context as resume-ready before human confirmation.")
    if skill_name == "juling-qianjiang" and runtime.get("avg_quality", 100) < 75:
        recs.append("Fallback quality is the main bottleneck; tune capability aliases and fallback quality factors first.")
    if skill_name == "bagua-zhen" and runtime.get("success_rate", 100) < 90:
        recs.append("Stabilize coordinator ingest paths and review mutex/synergy calculations for sparse or mixed metrics.")
    if skill_name == "xiushen-lu" and runtime.get("success_rate", 100) < 95:
        recs.append("Keep evolution analysis read-only by default and add an explicit mutation gate after validation.")
    if skill_name == "xiushen-lu" and scenario["key_metrics"].get("planned_evolution_type") == "bootstrap":
        recs.append("Cold-start mode is active; prioritize seeding representative runtime traces instead of forcing auto-evolution.")
    if skill_name == "xiushen-lu" and runtime.get("avg_completeness", 100) < 95:
        recs.append("Improve evolution coverage so more target skills reach analyzed or planned states before the cycle closes.")
    if skill_name == "xiushen-lu" and runtime.get("avg_consistency", 100) < 85:
        recs.append("Stabilize evolution decisions by aligning completeness, consistency, and human-intervention thresholds.")
    if skill_name == "xiushen-lu" and scenario["key_metrics"].get("planned_evolution_type") not in {"none", None}:
        recs.append("Review evolution suggestions and decide whether to convert them into explicit config changes.")
    if not recs:
        recs.append("Current signal looks healthy; next gains likely come from richer real-world benchmark datasets.")
    return recs


def evaluate_all() -> Dict[str, Any]:
    audit_report = audit_skills_root(SKILLS_ROOT)
    audit_by_skill = {item["skill"]: item for item in audit_report["results"]}
    evaluations: List[Dict[str, Any]] = []

    for skill_name, meta in SKILL_META.items():
        scenario_result = SCENARIOS[skill_name]()
        runtime = summarize_runtime(skill_name)
        artifact = artifact_status(meta["artifact"])
        alignment = load_skill_alignment(skill_name)
        audit_item = audit_by_skill[skill_name]
        independent = verify_bundle_roundtrip(SKILLS_ROOT / skill_name)
        effectiveness_score = 100
        if runtime.get("record_count", 0):
            autonomy_score = max(0.0, 100.0 - runtime.get("avg_human_intervention", 0.0) * 100.0)
            effectiveness_score = round(
                max(
                    0,
                    min(
                        100,
                        0.30 * runtime.get("success_rate", 0)
                        + 0.25 * runtime.get("avg_quality", 0)
                        + 0.20 * runtime.get("avg_completeness", runtime.get("avg_quality", 0))
                        + 0.15 * runtime.get("avg_consistency", runtime.get("avg_quality", 0))
                        + 0.10 * autonomy_score,
                    ),
                ),
                1,
            )
        if not scenario_result["passed"]:
            effectiveness_score = max(0, round(effectiveness_score - 35, 1))
        if not independent["passed"]:
            effectiveness_score = max(0, round(effectiveness_score - 15, 1))
        evaluations.append(
            {
                "skill": skill_name,
                "label": meta["label"],
                "cn_name": meta["cn"],
                "validation_passed": scenario_result["passed"] and audit_item["ok"] and independent["passed"],
                "effectiveness_score": effectiveness_score,
                "test_count": meta["test_count"],
                "scenario": scenario_result,
                "runtime": runtime,
                "artifact": artifact,
                "artifact_status": artifact,
                "alignment": alignment,
                "independent_lifecycle": independent,
                "audit": {
                    "ok": audit_item["ok"],
                    "warnings": audit_item["warnings"],
                    "errors": audit_item["errors"],
                },
                "recommendations": build_recommendations(skill_name, runtime, scenario_result, audit_item, independent),
            }
        )

    avg_score = round(statistics.mean(item["effectiveness_score"] for item in evaluations), 1)
    passed = sum(1 for item in evaluations if item["validation_passed"])
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "skills_evaluated": len(evaluations),
        "validation_passed": passed,
        "validation_passed_count": passed,
        "validation_total": len(evaluations),
        "average_effectiveness_score": avg_score,
        "average_score": avg_score,
        "audit_summary": {
            "ok": audit_report["ok"],
            "warning_count": audit_report["warning_count"],
            "error_count": audit_report["error_count"],
        },
        "skills": evaluations,
    }


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Skill Effectiveness Evaluation",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Skills evaluated: `{report['skills_evaluated']}`",
        f"- Validation passed: `{report['validation_passed']}/{report['skills_evaluated']}`",
        f"- Average effectiveness score: `{report['average_effectiveness_score']}`",
        "",
        "## Summary",
        "",
        "| Skill | Validation | Standalone | Score | Runtime success | Runtime quality |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in report["skills"]:
        runtime = item["runtime"]
        lines.append(
            f"| `{item['label']}` | {'PASS' if item['validation_passed'] else 'FAIL'} | "
            f"{'PASS' if item['independent_lifecycle'].get('passed') else 'FAIL'} | "
            f"{item['effectiveness_score']} | {runtime.get('success_rate', 'n/a')} | {runtime.get('avg_quality', 'n/a')} |"
        )
    lines.append("")
    lines.append("## Per Skill")
    lines.append("")
    for item in report["skills"]:
        lines.append(f"### {item['label']} ({item['cn_name']})")
        lines.append("")
        lines.append(f"- Validation: `{'PASS' if item['validation_passed'] else 'FAIL'}`")
        lines.append(f"- Score: `{item['effectiveness_score']}`")
        lines.append(f"- Scenario: {item['scenario']['effect_summary']}")
        lines.append(f"- Standalone lifecycle: `{'PASS' if item['independent_lifecycle'].get('passed') else 'FAIL'}`")
        lines.append(f"- Runtime records: `{item['runtime'].get('record_count', 0)}`")
        lines.append(f"- Artifact present: `{item['artifact']['present']}`")
        if item.get("alignment"):
            alignment = item["alignment"]
            lines.append(
                f"- Alignment: core={alignment.get('core')}; agent={alignment.get('agent_meaning')}; cost={alignment.get('cost')}"
            )
        lines.append(f"- Tests covering this skill: `{item['test_count']}`")
        lines.append("- Recommendations:")
        for rec in item["recommendations"]:
            lines.append(f"  - {rec}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = evaluate_all()
    json_path = REPORTS_DIR / "skill-effectiveness-report.json"
    md_path = REPORTS_DIR / "skill-effectiveness-report.md"
    write_audit_report(report, json_path)
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(
        f"validation={report['validation_passed']}/{report['skills_evaluated']} "
        f"avg_score={report['average_effectiveness_score']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
