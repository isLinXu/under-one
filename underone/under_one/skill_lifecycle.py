"""Per-skill install, test, and validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from . import (
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
from .skill_bundle import verify_bundle_roundtrip
from .skill_audit import audit_skill_dir


SKILL_TEST_TARGETS: Dict[str, Dict[str, List[str]]] = {
    "qiti-yuanliu": {
        "core": ["underone/tests/test_skills_core.py::TestContextGuard"],
        "sdk": ["underone/tests/test_under_one.py::TestSkillWrappers::test_context_guard_executes_repair_handoff_trace"],
    },
    "tongtian-lu": {
        "core": ["underone/tests/test_skills_core.py::TestCommandFactory"],
        "sdk": ["underone/tests/test_under_one.py::TestSkillWrappers::test_command_factory_direct_call"],
    },
    "dalu-dongguan": {
        "core": ["underone/tests/test_skills_core.py::TestInsightRadar"],
        "sdk": ["underone/tests/test_under_one.py::TestSkillWrappers::test_insight_radar_normalizes_id_and_text_fields"],
    },
    "shenji-bailian": {
        "core": ["underone/tests/test_skills_core.py::TestToolForge"],
        "sdk": ["underone/tests/test_under_one.py::TestSkillWrappers::test_tool_forge_direct_call"],
    },
    "fenghou-qimen": {
        "core": ["underone/tests/test_skills_core.py::TestPriorityEngine"],
        "sdk": ["underone/tests/test_under_one.py::TestSkillWrappers::test_priority_engine_direct_call"],
    },
    "liuku-xianzei": {
        "core": ["underone/tests/test_skills_core.py::TestKnowledgeDigest"],
        "sdk": ["underone/tests/test_under_one.py::TestSkillWrappers::test_knowledge_digest_direct_call"],
    },
    "shuangquanshou": {
        "core": ["underone/tests/test_skills_core.py::TestPersonaGuard"],
        "sdk": [
            "underone/tests/test_under_one.py::TestSkillWrappers::test_persona_guard_accepts_profile_dict",
            "underone/tests/test_under_one.py::TestSkillWrappers::test_persona_guard_legacy_session_log_fallback",
        ],
    },
    "juling-qianjiang": {
        "core": ["underone/tests/test_skills_core.py::TestToolOrchestrator"],
        "sdk": ["underone/tests/test_under_one.py::TestSkillWrappers::test_tool_orchestrator_direct_call"],
    },
    "bagua-zhen": {
        "core": ["underone/tests/test_skills_core.py::TestEcosystemHub"],
        "sdk": ["underone/tests/test_under_one.py::TestSkillWrappers::test_ecosystem_hub_direct_call"],
    },
    "xiushen-lu": {
        "core": ["underone/tests/test_skills_core.py::TestEvolutionEngine"],
        "sdk": ["underone/tests/test_under_one.py::TestSkillWrappers::test_evolution_engine_direct_call"],
    },
}


def _scenario_context_guard() -> Dict[str, Any]:
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
    stability_execution = result.get("stability_execution", {})
    repair_executed = repair_execution.get("status") == "completed" and trace.get("success") is True
    passed = (
        result.get("success") is True
        and alert_count >= 1
        and len(self_evolution.get("rule_candidates", [])) >= 1
        and bool(stability_contract)
        and bool(repair_plan)
        and "resume_ready" in stability_execution
        and (not repair_handoff or repair_executed)
    )
    return {
        "passed": passed,
        "effect_summary": (
            f"alerts={alert_count} rules={len(self_evolution.get('rule_candidates', []))} "
            f"mode={stability_contract.get('operating_mode')}"
        ),
        "key_metrics": {
            "alert_count": alert_count,
            "trace_link_count": trace.get("link_count", 0),
            "phase": self_evolution.get("phase"),
            "stability_mode": stability_contract.get("operating_mode"),
            "resume_ready": stability_execution.get("resume_ready"),
        },
    }


def _scenario_command_factory() -> Dict[str, Any]:
    result = CommandFactory().run("搜索竞品信息然后写高管报告")
    return {
        "passed": result.get("success") is True and len(result.get("talisman_list", [])) >= 2,
        "effect_summary": f"generated {len(result.get('talisman_list', []))} talisman(s)",
        "key_metrics": {"curse_level": result.get("curse_level"), "dimension_count": result.get("dimensions")},
    }


def _scenario_insight_radar() -> Dict[str, Any]:
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
    return {
        "passed": (
            result.get("success") is True
            and len(links) >= 1
            and len(anomalies) >= 1
            and len(insights) >= 1
            and hallucination.get("level") in {"medium", "high"}
        ),
        "effect_summary": (
            f"found {len(links)} link(s), {len(anomalies)} anomaly signal(s), "
            f"hallucination={hallucination.get('level')}"
        ),
        "key_metrics": {
            "link_count": len(links),
            "entity_count": result.get("entity_count", 0),
            "anomaly_count": len(anomalies),
            "hallucination_level": hallucination.get("level"),
        },
    }


def _scenario_tool_forge() -> Dict[str, Any]:
    result = ToolForge().run({"name": "json-cleaner", "description": "清洗 JSON", "inputs": ["raw.json"], "outputs": ["clean.json"]})
    return {
        "passed": result.get("success") is True and len(result.get("files", {})) == 3,
        "effect_summary": f"forged {len(result.get('files', {}))} file(s)",
        "key_metrics": {"file_count": len(result.get("files", {}))},
    }


def _scenario_priority_engine() -> Dict[str, Any]:
    result = PriorityEngine().run(
        [
            {"name": "修复生产故障", "urgency": 5, "importance": 5, "dependency": 3, "resource_match": 5},
            {"name": "整理文档", "urgency": 2, "importance": 2, "dependency": 1, "resource_match": 3},
        ]
    )
    top = (result.get("ranked_tasks") or [{}])[0]
    return {
        "passed": result.get("success") is True and top.get("name") == "修复生产故障",
        "effect_summary": f"ranked top task as {top.get('name')}",
        "key_metrics": {"top_task": top.get("name"), "top_gate": top.get("gate")},
    }


def _scenario_knowledge_digest() -> Dict[str, Any]:
    result = KnowledgeDigest().run(
        [
            {"source": "权威", "content": "核心结论：数据证明 X 有效，可用于生产部署并显著提升性能", "credibility": "S", "category": "技术方案"},
            {"source": "匿名", "content": "可能有用", "credibility": "C", "category": "默认"},
        ]
    )
    units = result.get("knowledge_units", [])
    contamination = result.get("contamination_risk", {})
    return {
        "passed": (
            result.get("success") is True
            and len(units) >= 2
            and len(result.get("inheritance_queue", [])) >= 1
            and len(result.get("quarantine_queue", [])) >= 1
            and contamination.get("level") in {"medium", "high"}
        ),
        "effect_summary": (
            f"digested {len(units)} unit(s), inheritance={len(result.get('inheritance_queue', []))}, "
            f"quarantine={len(result.get('quarantine_queue', []))}, contamination={contamination.get('level')}"
        ),
        "key_metrics": {
            "avg_digestion_rate": result.get("avg_digestion_rate"),
            "inheritance_count": len(result.get("inheritance_queue", [])),
            "quarantine_count": len(result.get("quarantine_queue", [])),
            "contamination_level": contamination.get("level"),
        },
    }


def _scenario_persona_guard() -> Dict[str, Any]:
    result = PersonaGuard().run(
        {
            "current_style": {"tone": 1, "formality": 1, "detail_level": 1, "structure": 1},
            "dna_expectation": {"tone": 5, "formality": 5, "detail_level": 5, "structure": 5},
            "dna_core": {"尊重": "不嘲讽贬低"},
            "requested_change": {"type": "嘲讽", "target": "尖刻"},
            "history": [{"style": "formal"}, {"style": "casual"}, {"style": "technical"}],
        }
    )
    return {
        "passed": result.get("success") is True and result.get("can_switch") is False and len(result.get("surgery_plan", [])) >= 1,
        "effect_summary": f"blocked unsafe switch with surgery_mode={result.get('surgery_mode')}",
        "key_metrics": {
            "can_switch": result.get("can_switch"),
            "violation_count": len(result.get("dna_violations", [])),
            "contamination_index": result.get("contamination_index"),
        },
    }


def _scenario_tool_orchestrator() -> Dict[str, Any]:
    result = ToolOrchestrator().run(
        [{"type": "code", "desc": "查询资料"}],
        [
            {"id": "api1", "capabilities": ["code"], "available": False, "quality_score": 0.95},
            {"id": "api2", "capabilities": ["browse"], "available": True, "quality_score": 0.9},
        ],
    )
    return {
        "passed": (
            result.get("success") is True
            and result.get("fallback_count", 0) >= 1
            and len(result.get("command_plan", [])) == 1
            and "recovery_plan" in result.get("command_plan", [{}])[0]
            and "governance_summary" in result
        ),
        "effect_summary": (
            f"planned {len(result.get('plan', []))} step(s) with command packet "
            f"manual_review={result.get('governance_summary', {}).get('manual_review_required')}"
        ),
        "key_metrics": {
            "fallback_count": result.get("fallback_count"),
            "avg_quality": result.get("avg_quality"),
            "rebellion_alerts": len(result.get("rebellion_alerts", [])),
            "manual_review_required": result.get("governance_summary", {}).get("manual_review_required"),
        },
    }


def _scenario_ecosystem_hub() -> Dict[str, Any]:
    result = EcosystemHub().run()
    return {
        "passed": result.get("success") is True and "skill_states" in result,
        "effect_summary": f"aggregated {len(result.get('skill_states', {}))} skill state(s)",
        "key_metrics": {"average_quality": result.get("average_quality"), "ecosystem_level": result.get("ecosystem_level")},
    }


def _scenario_evolution_engine() -> Dict[str, Any]:
    result = EvolutionEngine().run("qiti-yuanliu")
    first = (result.get("results") or [{}])[0]
    analysis = first.get("analysis", {})
    return {
        "passed": result.get("success") is True and first.get("skill") == "qiti-yuanliu",
        "effect_summary": f"wrapped evolution cycle with status={first.get('status')}",
        "key_metrics": {
            "status": first.get("status"),
            "summary_total": result.get("summary", {}).get("total"),
            "planned_evolution_type": first.get("planned_evolution_type"),
            "bottleneck_type": analysis.get("bottleneck_type"),
            "avg_output_completeness": analysis.get("avg_output_completeness"),
            "avg_consistency_score": analysis.get("avg_consistency_score"),
            "avg_human_intervention": analysis.get("avg_human_intervention"),
        },
    }


SCENARIO_RUNNERS = {
    "qiti-yuanliu": _scenario_context_guard,
    "tongtian-lu": _scenario_command_factory,
    "dalu-dongguan": _scenario_insight_radar,
    "shenji-bailian": _scenario_tool_forge,
    "fenghou-qimen": _scenario_priority_engine,
    "liuku-xianzei": _scenario_knowledge_digest,
    "shuangquanshou": _scenario_persona_guard,
    "juling-qianjiang": _scenario_tool_orchestrator,
    "bagua-zhen": _scenario_ecosystem_hub,
    "xiushen-lu": _scenario_evolution_engine,
}


def validate_skill(skill_name: str, skill_dir: Path) -> Dict[str, Any]:
    audit = audit_skill_dir(skill_dir).to_dict()
    scenario = SCENARIO_RUNNERS[skill_name]()
    independent = verify_bundle_roundtrip(skill_dir)
    passed = audit["ok"] and scenario["passed"] and independent["passed"]
    return {
        "skill": skill_name,
        "validation_passed": passed,
        "audit": audit,
        "scenario": scenario,
        "independent_lifecycle": independent,
        "recommendations": [] if passed else [
            "Inspect audit errors, scenario output, and independent lifecycle results before shipping the skill."
        ],
    }
