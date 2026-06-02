"""
Skill 核心算法单元测试
覆盖 10 个 skill 的核心计算逻辑，不依赖外部文件/网络。
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parent.parent
SKILLS_DIR = ROOT / "skills"


def _import_skill(module_path: str):
    """动态导入 skill 脚本模块（不依赖 __init__.py）

    module_path 使用下划线分隔，例如 "qiti_yuanliu.scripts.entropy_scanner"，
    实际磁盘路径会自动将第一部分的下划线替换为连字符（qiti-yuanliu）。
    """
    parts = module_path.split(".")
    # 第一级目录名使用连字符（与磁盘一致），后续保持原样
    parts[0] = parts[0].replace("_", "-")
    file_path = SKILLS_DIR / Path(*parts[:-1]) / f"{parts[-1]}.py"
    spec = importlib.util.spec_from_file_location(module_path, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_path] = mod
    spec.loader.exec_module(mod)
    return mod


def _materialize_generated_skill(result, tmp_path):
    """把神机百炼生成的 skill 文件树写到临时目录。"""
    skill_root = tmp_path / "generated_skill"
    main_script = None
    preferred_name = str(result.get("inferred_spec", {}).get("name") or result.get("tool_name") or "").lower()
    for name, content in result["files"].items():
        rel = Path(*Path(name).parts[1:]) if len(Path(name).parts) > 1 else Path(name)
        target = skill_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if (
            target.suffix == ".py"
            and target.parent.name == "scripts"
            and not target.name.startswith("test_")
            and target.stem != "source_adapter"
        ):
            if main_script is None:
                main_script = target
            if preferred_name and target.stem == preferred_name:
                main_script = target
    assert main_script is not None
    return skill_root, main_script


# ---------------------------------------------------------------------------
# 动态导入所有 skill 模块
# ---------------------------------------------------------------------------
entropy_scanner = _import_skill("qiti_yuanliu.scripts.entropy_scanner")
QiTiScanner = entropy_scanner.QiTiScanner
distill_intent = entropy_scanner.distill_intent
detect_rule_conflicts = entropy_scanner.detect_rule_conflicts
preflight_guard = entropy_scanner.preflight_guard
gatekeep = entropy_scanner.gatekeep
check_will_not = entropy_scanner.check_will_not

priority_engine = _import_skill("fenghou_qimen.scripts.priority_engine")
PriorityEngine = priority_engine.PriorityEngine
build_domain_override = priority_engine.build_domain_override

link_detector = _import_skill("dalu_dongguan.scripts.link_detector")
LinkDetector = link_detector.LinkDetector
detect_parallel_dependencies = link_detector.detect_parallel_dependencies

knowledge_digest = _import_skill("liuku_xianzei.scripts.knowledge_digest")
KnowledgeDigest = knowledge_digest.KnowledgeDigest
devour_any = knowledge_digest.devour_any

dna_validator = _import_skill("shuangquanshou.scripts.dna_validator")
DNAValidator = dna_validator.DNAValidator
parse_memory_markdown = dna_validator.parse_memory_markdown
render_memory_markdown = dna_validator.render_memory_markdown
apply_memory_rewrite = dna_validator.apply_memory_rewrite

dispatcher = _import_skill("juling_qianjiang.scripts.dispatcher")
dispatch = dispatcher.dispatch
match_spirit = dispatcher.match_spirit
parse_soul_markdown = dispatcher.parse_soul_markdown
load_spirits_source = dispatcher.load_spirits_source
rank_spirits = dispatcher.rank_spirits
extract_soul_essence = dispatcher.extract_soul_essence
aggregate_souls = dispatcher.aggregate_souls
absorb_souls = dispatcher.absorb_souls

tool_factory = _import_skill("shenji_bailian.scripts.tool_factory")
ToolFactory = tool_factory.ToolFactory

fu_generator = _import_skill("tongtian_lu.scripts.fu_generator")
FuGenerator = fu_generator.FuGenerator

coordinator = _import_skill("bagua_zhen.scripts.coordinator")
calc_stats = coordinator.calc_stats
coordinate = coordinator.coordinate
linkage_protocol = _import_skill("bagua_zhen.scripts.linkage_protocol")
LinkageProtocol = linkage_protocol.LinkageProtocol

core_engine = _import_skill("xiushen_lu.scripts.core_engine")
QiSourceV7 = core_engine.QiSourceV7
RefinerV7 = core_engine.RefinerV7
RollbackV7 = core_engine.RollbackV7
XiuShenLuCoreV7 = core_engine.XiuShenLuCoreV7
bootstrap_profiles = _import_skill("xiushen_lu.scripts.bootstrap_profiles")
xiushenlu_verifier = _import_skill("xiushen_lu.scripts.xiushenlu_verifier")


# ---------------------------------------------------------------------------
# 1. 炁体源流 (context-guard)
# ---------------------------------------------------------------------------

class TestContextGuard:
    """上下文稳态扫描器测试"""

    def test_distill_intent_strips_rhetoric(self):
        """术之尽头·还炁：剥离修辞，抽出祈使核心。"""
        text = "请你务必始终使用中文回答。另外，我觉得这个项目很有意思。必须保留原始数据。"
        out = distill_intent(text)
        assert out["directive_count"] >= 2
        assert any("中文" in e for e in out["qi_essence"])
        assert out["stripped_rhetoric"]

    def test_distill_intent_dedups_redundancy(self):
        """重复祈使应被合并入 redundancies。"""
        text = "必须使用中文。\n必须使用中文。"
        out = distill_intent(text)
        assert out["redundancies"]

    def test_detect_rule_conflicts_positive_negative(self):
        """规则冲突消解：同主题正反冲突应被检出并给出消解方案。"""
        rules = ["必须始终使用中文回答", "禁止使用中文回答", "回答要简洁"]
        out = detect_rule_conflicts(rules)
        assert out["conflict_count"] >= 1
        assert out["verdict"] == "术有相冲"
        assert out["conflicts"][0]["resolution"]

    def test_preflight_guard_blocks_on_conflict(self):
        """前置校验层：skill 规则与全局规则冲突时拦截。"""
        blocked = preflight_guard(["禁止使用中文回答"], global_rules=["必须使用中文回答"])
        assert blocked["passed"] is False
        passed = preflight_guard(["输出尽量简洁"], global_rules=["必须使用中文回答"])
        assert passed["passed"] is True

    def test_distill_intent_trims_dangling_subject(self):
        """还炁打磨：剥离修辞后不应残留悬空主语（如"你"）。"""
        out = distill_intent("请你务必始终使用中文回答")
        assert out["qi_essence"]
        assert not any(e.startswith(("你", "您", "请")) for e in out["qi_essence"])

    def test_gatekeep_unified_verdict(self):
        """众术之先·统一门：还炁 + 冲突消解 + 前置校验合一裁决。"""
        blocked = gatekeep(
            skill_name="demo",
            skill_rules=["禁止使用中文回答"],
            global_rules=["必须使用中文回答"],
            prompt="请务必使用中文回答",
        )
        assert blocked["passed"] is False
        assert blocked["resolutions"]
        assert "qi_essence" in blocked
        ok = gatekeep(skill_name="demo", skill_rules=["输出尽量简洁"], global_rules=["必须使用中文回答"])
        assert ok["passed"] is True

    def test_check_will_not_detects_violation(self):
        """天条校验：诉求触碰 forbidden op（含中文同义词）应被识别。"""
        wn = check_will_not("帮我绕过审批直接写盘", ["bypass_manual_gate"])
        assert wn["passed"] is False
        assert wn["violations"][0]["will_not"] == "bypass_manual_gate"
        clean = check_will_not("帮我分析一下日志", ["bypass_manual_gate"])
        assert clean["passed"] is True

    def test_gatekeep_blocks_on_will_not(self):
        """统一门：触碰天条应拦截并给出建议。"""
        report = gatekeep(
            skill_name="demo",
            prompt="请改写技能并持久化阈值",
            will_not=["write_skills", "persist_thresholds"],
        )
        assert report["passed"] is False
        assert report["will_not_check"]["violation_count"] >= 1
        assert report["resolutions"]

    def test_empty_context_health_score(self):
        """空上下文应返回健康分"""
        scanner = QiTiScanner([])
        report = scanner.scan()
        assert "health_score" in report["metrics"]
        assert report["metrics"]["health_level"] in ["excellent", "good", "warning", "danger"]

    def test_entropy_calculation(self):
        """熵计算应反映矛盾数量"""
        context = [
            {"role": "user", "content": "你好", "round": 1},
            {"role": "assistant", "content": "不对，你之前说的是别的", "round": 2},
        ]
        scanner = QiTiScanner(context)
        scanner._calc_entropy()
        assert scanner.metrics["entropy"] > 0
        assert scanner.metrics["entropy_level"] in ["green", "yellow", "red"]

    def test_no_contradiction_low_entropy(self):
        """无矛盾时熵应较低"""
        context = [
            {"role": "user", "content": "你好", "round": 1},
            {"role": "assistant", "content": "你好，有什么可以帮你的？", "round": 2},
        ]
        scanner = QiTiScanner(context)
        scanner._calc_entropy()
        assert scanner.metrics["entropy"] < 3

    def test_redundancy_detection(self):
        """冗余检测应识别重复内容（文本需>20字符）"""
        long_text = "这是一段用于测试冗余检测功能的重复内容文本，需要超过二十个字符长度。"
        context = [
            {"role": "user", "content": long_text, "round": 1},
            {"role": "assistant", "content": long_text, "round": 2},
        ]
        scanner = QiTiScanner(context)
        scanner._calc_entropy()
        assert scanner.metrics["entropy"] >= 0.5

    def test_dna_snapshot_generation(self):
        """DNA快照应生成6位哈希"""
        context = [
            {"role": "user", "content": "目标：完成项目报告", "round": 1},
            {"role": "assistant", "content": "好的，我来帮你", "round": 2},
        ]
        scanner = QiTiScanner(context)
        report = scanner.scan()
        dna = report["dna_snapshot"]
        assert len(dna["hash"]) == 6
        assert dna["based_on"] == "last_3_rounds"

    def test_health_score_range(self):
        """健康分应在0-100之间"""
        context = [{"role": "user", "content": "测试", "round": i} for i in range(10)]
        scanner = QiTiScanner(context)
        report = scanner.scan()
        score = report["metrics"]["health_score"]
        assert 0 <= score <= 100

    def test_info_gap_detection(self):
        """信息缺口检测：末尾未回答的问题"""
        context = [
            {"role": "user", "content": "如何解决这个问题？", "round": 1},
        ]
        scanner = QiTiScanner(context)
        gaps = scanner._count_info_gaps()
        assert gaps == 1

    def test_repair_handoff_appears_after_repeated_contradictions(self):
        """重复矛盾达到阈值后应生成 repair_handoff。"""
        context = [
            {"role": "user", "content": "先按 React 方案推进。", "round": 1},
            {"role": "assistant", "content": "收到，采用 React。", "round": 2},
            {"role": "user", "content": "不对，这不是这个方案，请改回之前的实现。", "round": 3},
        ]
        scanner = QiTiScanner(context)
        report = scanner.scan()
        handoff = report["repair_handoff"]
        assert handoff is not None
        assert handoff["triggered"] is True
        assert handoff["observed_alerts"] >= handoff["alert_threshold"] >= 2
        assert any("repair_handoff" in rec for rec in report["recommendations"])

    def test_repair_handoff_defaults_to_dalu_dongguan(self):
        """repair_handoff 默认应交给大罗洞观处理。"""
        context = [
            {"role": "user", "content": "先按 React 方案推进。", "round": 1},
            {"role": "assistant", "content": "收到，采用 React。", "round": 2},
            {"role": "user", "content": "不对，这不是这个方案，请改回之前的实现。", "round": 3},
        ]
        scanner = QiTiScanner(context)
        report = scanner.scan()
        assert report["repair_handoff"]["target_skill"] == "dalu-dongguan"

    def test_repair_handoff_can_drive_dalu_dongguan_trace(self):
        """repair_handoff 应能转换为大罗洞观可执行的跨段追踪输入。"""
        context = [
            {"role": "user", "content": "先按 React 方案推进，目标是重构登录流程。", "round": 1},
            {"role": "assistant", "content": "收到，采用 React 重构登录流程。", "round": 2},
            {"role": "user", "content": "不对，这不是这个方案，请改回 Vue 登录流程。", "round": 3},
            {"role": "assistant", "content": "我会改回 Vue 登录流程。", "round": 4},
            {"role": "user", "content": "不对，之前说的是 React，不是 Vue。", "round": 5},
        ]
        report = QiTiScanner(context).scan()
        handoff = report["repair_handoff"]
        assert handoff["target_skill"] == "dalu-dongguan"
        assert handoff["action"] == "cross_segment_trace"

        contradiction_rounds = set(handoff["contradiction_rounds"])
        segments = [
            {
                "id": f"round-{item['round']}",
                "source": f"qiti-yuanliu:{item['round']}",
                "content": item["content"],
            }
            for item in context
            if item["round"] in contradiction_rounds or item["round"] == 1
        ]
        trace = LinkDetector(segments).detect()
        assert trace["detector"] == "dalu-dongguan"
        assert trace["segment_count"] == len(segments)
        assert trace["entity_count"] > 0
        assert "hallucination_risk" in trace

    def test_self_evolution_extracts_origin_and_rules(self):
        """炁体源流应输出目标锚点、自进化阶段与规则候选。"""
        context = [
            {"role": "user", "content": "请优先完成竞品分析，不要改题，先给结构后给结论。", "round": 1},
            {"role": "assistant", "content": "好的，我先列出竞品分析结构。", "round": 2},
            {"role": "user", "content": "不对，先补用户画像，再继续竞品分析。", "round": 3},
        ]
        report = QiTiScanner(context).scan()
        self_evolution = report["self_evolution"]
        assert report["origin_core"]["goal_anchor"].startswith("请优先完成竞品分析")
        assert self_evolution["phase"] in ["stabilize", "refine", "advance"]
        assert len(self_evolution["rule_candidates"]) >= 1
        assert any("用户纠偏" in item["rule"] for item in self_evolution["rule_candidates"])

    def test_meta_reflect_converges_on_consistent_report(self):
        """无限递归自省：自洽的诊断应收敛（炁场归一）。"""
        scanner = QiTiScanner([{"role": "user", "content": "请帮我分析竞品数据", "round": 1}])
        meta = scanner.meta_reflect()
        assert meta["mode"] == "meta_reflect"
        assert meta["converged"] is True
        assert meta["reflection_depth"] >= 1
        assert meta["qi_baby_evolution"]["autonomous"] is True

    def test_meta_reflect_detects_diagnostic_dissonance(self):
        """二阶审视应识别一阶诊断的自相矛盾。"""
        scanner = QiTiScanner([{"role": "user", "content": "x", "round": 1}])
        fake = {
            "metrics": {"health_level": "good", "entropy_level": "red",
                        "health_score": 90, "consistency": 90},
            "alerts": [],
        }
        findings = scanner._reflect_once(fake)
        assert findings["meta_entropy"] >= 1
        assert any("矛盾" in d for d in findings["dissonances"])

    def test_stability_contract_freezes_high_risk_context(self):
        """高风险上下文应输出冻结式稳态契约与修复计划。"""
        context = [
            {"role": "user", "content": "请继续按照 React 方案推进，并优先保证原始需求不变。", "round": 1},
            {"role": "assistant", "content": "好的，我会保持 React 方案。", "round": 2},
            {"role": "user", "content": "不对，改成 Vue，而且之前的目标也不准确，请重新理解。", "round": 3},
            {"role": "assistant", "content": "我先按 Angular 重写一遍。", "round": 4},
        ]
        report = QiTiScanner(context).scan()
        contract = report["stability_contract"]
        plan = report["repair_plan"]
        escalation = report["escalation_contract"]
        checkpoints = report["stability_checkpoints"]
        assert contract["freeze_self_evolution"] is True
        assert contract["mutation_budget"]["mode"] == "frozen"
        assert contract["verification_targets"]["requires_handoff_completion"] is True
        assert plan["step_count"] >= 5
        assert plan["steps"][0]["id"] == "re-anchor-goal"
        assert escalation["severity"] in ["medium", "high"]
        assert "pre_resume" in [item["stage"] for item in checkpoints["checkpoints"]]
        assert len(report["risk_hotspots"]) >= 2
        assert report["priority_actions"][0]["id"] == "re-anchor-goal"
        assert report["execution_contract"]["next_action_id"] == "re-anchor-goal"
        assert report["execution_contract"]["manual_review_required"] is True
        assert report["execution_contract"]["blocking_action_count"] >= 2
        assert report["quality_score"] <= report["metrics"]["health_score"]
        assert report["human_intervention"] == 1

    def test_stability_contract_remains_adaptive_for_healthy_context(self):
        """健康上下文应允许受控继续自演化。"""
        context = [
            {"role": "user", "content": "请整理测试结果，先给摘要，再给结论。", "round": 1},
            {"role": "assistant", "content": "好的，我先给你摘要，然后补充结论与证据。", "round": 2},
            {"role": "assistant", "content": "因为样本完整，所以我会按摘要、证据、结论的顺序输出。", "round": 3},
        ]
        report = QiTiScanner(context).scan()
        contract = report["stability_contract"]
        escalation = report["escalation_contract"]
        assert contract["operating_mode"] in ["guarded", "adaptive"]
        assert contract["freeze_self_evolution"] is False
        assert escalation["manual_review_required"] is False
        assert report["control_plane_contract"]["role"] == "observer"
        assert report["control_plane_status"]["role"] == "observer"
        assert report["control_plane_status"]["phase"] == "guarded-observe"
        assert report["control_plane_status"]["writes_applied"] is False
        assert report["execution_contract"]["resume_ready"] is True
        assert report["execution_contract"]["next_owner"] == "qiti-yuanliu"
        assert len(report["priority_actions"]) >= 3
        assert report["quality_score"] >= 75
        assert report["human_intervention"] == 0

    def test_user_clarification_is_not_overtreated_as_contradiction(self):
        """正常的用户澄清不应直接触发 repair_handoff 或高风险误报。"""
        context = [
            {"role": "user", "content": "请分析用户数据，先看留存趋势。", "round": 1},
            {"role": "assistant", "content": "好的，我先看留存趋势。", "round": 2},
            {"role": "user", "content": "不对，我说的是用户数据不是市场数据，先看留存。", "round": 3},
        ]
        report = QiTiScanner(context).scan()
        assert report["repair_handoff"] is None
        assert report["metrics"]["consistency"] >= 85
        assert report["metrics"]["entropy_components"]["clarification_events"] >= 1
        assert any("用户纠偏" in item["rule"] for item in report["self_evolution"]["rule_candidates"])
        assert report["execution_contract"]["manual_review_required"] is False
        assert not any(item["id"] == "repair-handoff" for item in report["risk_hotspots"])
        assert report["human_intervention"] == 0

    def test_correction_round_uses_weighted_contradiction_impact(self):
        """同一轮的纠偏信号应触发修复，但不应被线性三次惩罚。"""
        context = [
            {"role": "user", "content": "我们先用 React。", "round": 1},
            {"role": "assistant", "content": "好的，前端采用 React。", "round": 2},
            {"role": "user", "content": "不对，改成 Vue。", "round": 3},
        ]
        report = QiTiScanner(context).scan()
        assert report["repair_handoff"]["triggered"] is True
        assert report["metrics"]["contradiction_impact"] < 3.0
        assert report["metrics"]["consistency"] > 55

    def test_acknowledged_correction_gets_resolution_credit(self):
        """纠偏被后续 assistant 明确承接后，应下调未修复冲击度。"""
        context = [
            {"role": "user", "content": "我们先用 React。", "round": 1},
            {"role": "assistant", "content": "好的，前端采用 React。", "round": 2},
            {"role": "user", "content": "不对，改成 Vue。", "round": 3},
            {"role": "assistant", "content": "已切换为 Vue，并以 Vue 作为当前前端方案。", "round": 4},
        ]
        report = QiTiScanner(context).scan()
        assert report["repair_handoff"]["triggered"] is True
        assert report["metrics"]["contradiction_impact"] < 1.7
        assert report["metrics"]["consistency"] >= 80

    def test_config_can_override_clarification_and_hard_reset_markers(self, monkeypatch):
        """澄清词与强制重置词应可通过配置独立调参。"""
        custom_cfg = {
            "contradiction": {
                "keywords": ["冲突"],
                "clarification_markers": ["口径修正"],
                "hard_reset_markers": ["整个作废"],
                "negation_prefixes": ["不"],
                "reversal_patterns": [["是", "不是"]],
            }
        }

        monkeypatch.setattr(
            entropy_scanner,
            "get_skill_config",
            lambda skill_name, key=None, default=None: custom_cfg if skill_name == "qitiyuanliu" and key is None else default,
        )

        scanner = QiTiScanner(
            [
                {"role": "user", "content": "口径修正，目标改为用户留存分析。", "round": 1},
                {"role": "user", "content": "整个作废，这条路线不要了。", "round": 2},
            ]
        )

        assert scanner.clarification_markers == ["口径修正"]
        assert scanner.hard_reset_markers == ["整个作废"]
        assert scanner._classify_correction_mode("口径修正，目标改为用户留存分析。", "user") == "clarification"
        assert scanner._classify_correction_mode("整个作废，这条路线不要了。", "user") == "hard_reset"

    def test_optional_llm_semantic_contradiction_signal(self, monkeypatch):
        """可选 LLM 适配层应能补上规则检测遗漏的语义矛盾。"""
        custom_cfg = {
            "semantic_contradiction": {
                "enabled": True,
                "provider": "fake",
                "threshold": 0.8,
                "max_context_chars": 500,
            }
        }

        class FakeClient:
            provider = "fake"
            model = "semantic-test"

            def complete(self, prompt, **kwargs):
                return SimpleNamespace(content='{"score": 0.86, "reason": "成本预算冲突"}', provider="fake", model="semantic-test")

        monkeypatch.setattr(
            entropy_scanner,
            "get_skill_config",
            lambda skill_name, key=None, default=None: custom_cfg if skill_name == "qitiyuanliu" and key is None else default,
        )
        monkeypatch.setattr(entropy_scanner, "get_llm_client", lambda provider=None, **kwargs: FakeClient())

        context = [
            {"role": "user", "content": "这个方案成本太高，需要压缩投入。", "round": 1},
            {"role": "assistant", "content": "收到，会优先控制成本。", "round": 2},
            {"role": "user", "content": "预算不是问题，不用考虑投入。", "round": 3},
        ]
        report = QiTiScanner(context).scan()
        assert report["metrics"]["entropy_components"]["semantic_llm"]["score"] == 0.86
        assert any(alert["type"] == "semantic_llm" for alert in report["alerts"])


# ---------------------------------------------------------------------------
# 2. 风后奇门 (priority-engine)
# ---------------------------------------------------------------------------

class TestPriorityEngine:
    """优先级引擎测试"""

    def test_domain_override_threshold_auto_appliable(self):
        """定中宫·改局：纯阈值微调可受控应用，并记录回滚。"""
        spec = {
            "domain": "调度域",
            "current_thresholds": {"robustness_medium": 60},
            "adjustments": [
                {"target": "robustness_medium", "op": "set", "value": 50, "reason": "放宽"},
            ],
        }
        out = build_domain_override(spec)
        assert out["domain_strength"] == "定中宫"
        assert out["threshold_deltas"][0]["before"] == 60
        assert out["threshold_deltas"][0]["after"] == 50
        assert out["rollback"]["thresholds"]["robustness_medium"] == 60
        assert out["approval_contract"]["approval_status"] == "approved"
        assert out["applied"] is False

    def test_domain_override_system_level_requires_approval(self):
        """系统级/override 改局必须人工审批，绝不自动生效。"""
        spec = {
            "domain": "安全域",
            "current_rules": {"max_retries": 3},
            "adjustments": [
                {"target": "max_retries", "op": "override", "value": 99,
                 "system_level": True, "ttl_minutes": 30, "reason": "临时放开"},
            ],
        }
        out = build_domain_override(spec)
        assert out["approval_contract"]["approval_status"] == "pending"
        assert out["approval_contract"]["requires_user_confirmation"] is True
        assert out["temporary_overrides"][0]["ttl_minutes"] == 30
        assert out["temporary_overrides"][0]["auto_revert"] is True

    def test_domain_override_will_not_rejected(self):
        """天条(will_not)所禁的目标一律拒绝改局。"""
        spec = {
            "domain": "核心域",
            "current_rules": {"safety_gate": "on", "speed": 1},
            "will_not": ["safety_gate"],
            "adjustments": [
                {"target": "safety_gate", "op": "set", "value": "off"},
                {"target": "speed", "op": "scale", "value": 2},
            ],
        }
        out = build_domain_override(spec)
        rejected_targets = [r["target"] for r in out["rejected"]]
        assert "safety_gate" in rejected_targets
        applied_targets = [d["target"] for d in out["rule_deltas"] + out["threshold_deltas"]]
        assert "safety_gate" not in applied_targets
        assert "speed" in applied_targets

    def test_basic_scoring(self):
        """基础评分应返回复合分"""
        tasks = [
            {"name": "紧急bug", "urgency": 5, "importance": 5, "effort": 2},
            {"name": "常规任务", "urgency": 2, "importance": 2, "effort": 3},
        ]
        engine = PriorityEngine(tasks)
        engine._score_all()
        assert engine.ranked[0]["composite_score"] > engine.ranked[1]["composite_score"]

    def test_gate_assignment(self):
        """高分任务应映射到开门/生门"""
        tasks = [
            {"name": "高分任务", "urgency": 5, "importance": 5, "dependency": 5, "resource_match": 5},
        ]
        engine = PriorityEngine(tasks)
        result = engine.run()
        gate = result["ranked_tasks"][0]["gate"]
        assert gate in ["开门", "生门"]

    def test_low_score_gate(self):
        """低分任务应映射到杜门/死门"""
        tasks = [
            {"name": "低分任务", "urgency": 1, "importance": 1, "dependency": 1, "resource_match": 1},
        ]
        engine = PriorityEngine(tasks)
        result = engine.run()
        gate = result["ranked_tasks"][0]["gate"]
        assert gate in ["杜门", "死门"]

    def test_monte_carlo_output(self):
        """蒙特卡洛应返回鲁棒性评估"""
        tasks = [
            {"name": "t1", "urgency": 5, "importance": 5, "effort": 2, "estimated_time": 30},
        ]
        engine = PriorityEngine(tasks)
        result = engine.run()
        mc = result["monte_carlo"]
        assert mc["simulations"] == 100
        assert 0 <= mc["on_time_rate"] <= 100
        assert mc["assessment"] in ["高鲁棒", "中鲁棒", "低鲁棒"]

    def test_importance_field_alias(self):
        """兼容 'importance' 和 'important' 两种字段名"""
        tasks = [
            {"name": "t1", "urgency": 5, "important": 5},
            {"name": "t2", "urgency": 5, "importance": 3},
        ]
        engine = PriorityEngine(tasks)
        engine._score_all()
        assert "composite_score" in engine.ranked[0]

    def test_execution_plan_actions(self):
        """执行计划应包含动作描述"""
        tasks = [
            {"name": "紧急", "urgency": 5, "importance": 5, "dependency": 5, "resource_match": 5},
            {"name": "延后", "urgency": 1, "importance": 1, "dependency": 1, "resource_match": 1},
        ]
        engine = PriorityEngine(tasks)
        result = engine.run()
        plan = result["execution_plan"]
        assert len(plan) == 2
        assert any(p["gate"] == "开门" for p in plan)  # 高分是开门
        assert any(p["gate"] in ["杜门", "死门"] for p in plan)  # 低分是杜门或死门

    def test_priority_engine_emits_phases_and_alternatives(self):
        """风后奇门应输出阶段计划与多路径备选方案。"""
        tasks = [
            {"name": "修复生产故障", "urgency": 5, "importance": 5, "dependency": 2, "resource_match": 5, "estimated_time": 20},
            {"name": "补文档", "urgency": 2, "importance": 2, "dependency": 1, "resource_match": 4, "estimated_time": 15},
            {"name": "淘汰旧脚本", "urgency": 1, "importance": 1, "dependency": 4, "resource_match": 2, "estimated_time": 10},
        ]
        result = PriorityEngine(tasks).run()
        assert len(result["execution_phases"]) >= 1
        assert "balanced" in result["alternative_plans"]
        assert "fast_track" in result["alternative_plans"]
        assert "risk_averse" in result["alternative_plans"]
        assert result["global_strategy"] in ["idle", "staggered-push", "parallel-breakthrough", "containment-first", "steady-advance"]

    def test_adaptive_weights_select_template_from_task_profile(self):
        """自适应权重应能按任务类型选择模板并记录原因。"""
        tasks = [
            {"name": "紧急线上故障修复", "urgency": 5, "importance": 4, "history_success": 2.0},
            {"name": "补充事故复盘", "urgency": 4, "importance": 3, "history_success": 2.5},
        ]
        result = PriorityEngine(tasks, template="adaptive").run()
        assert result["active_template"] == "adaptive:urgency_priority"
        assert result["adaptive_weighting"]["enabled"] is True
        assert result["weights_used"]["urgency"] > result["weights_used"]["importance"]

    def test_luan_jin_tuo_freezes_dead_gate_tasks(self):
        """乱金柝：存在死门/杜门任务时应冻结其资源以聚焦高优先。"""
        tasks = [
            {"name": "紧急修复", "urgency": 5, "importance": 5, "dependency": 1},
            {"name": "可有可无", "urgency": 1, "importance": 1, "dependency": 1},
        ]
        result = PriorityEngine(tasks).run()
        ljt = result["luan_jin_tuo"]
        assert ljt["technique"] == "乱金柝"
        dead = [p["task"] for p in result["execution_plan"] if p["gate"] in ("死门", "杜门")]
        if dead:
            assert ljt["triggered"] is True
            assert set(ljt["frozen_tasks"]) == set(dead)

    def test_gui_ying_ti_burn_mode_off_by_default(self):
        """龟蝇体：默认不点燃，run(burn=True) 时才进入燃烧模式。"""
        tasks = [{"name": "冲刺任务", "urgency": 5, "importance": 5, "dependency": 1}]
        normal = PriorityEngine(tasks).run()
        assert normal["gui_ying_ti"]["enabled"] is False
        assert normal["gui_ying_ti"]["sprint_tasks"] == []

        burned = PriorityEngine(tasks).run(burn=True)
        assert burned["gui_ying_ti"]["enabled"] is True
        assert burned["gui_ying_ti"]["sprint_tasks"]
        assert burned["gui_ying_ti"]["sacrificed"]

    def test_empty_tasks(self):
        """空任务列表应优雅处理"""
        engine = PriorityEngine([])
        result = engine.run()
        assert result["task_count"] == 0
        assert result["execution_plan"] == []


# ---------------------------------------------------------------------------
# 3. 大罗洞观 (insight-radar)
# ---------------------------------------------------------------------------

class TestInsightRadar:
    """跨文档关联检测测试"""

    def test_blind_spots_non_adjacent_recurrence(self):
        """因果盲区：实体在非相邻片段反复浮现应被识别为认知盲区。"""
        segments = [
            {"source": "s0", "content": "关于缓存一致性的基础问题"},
            {"source": "s1", "content": "今天天气不错聊点别的"},
            {"source": "s2", "content": "为什么数据有时候不一致缓存又出问题"},
        ]
        result = LinkDetector(segments).detect()
        assert "blind_spots" in result
        assert "trajectory_prediction" in result

    def test_trajectory_prediction_present(self):
        """走向预测：应输出对接下来若干轮的预测。"""
        segments = [
            {"source": "s0", "content": "登录模块 鉴权 token 设计"},
            {"source": "s1", "content": "登录模块 token 过期 鉴权 失败"},
        ]
        result = LinkDetector(segments).detect()
        pred = result["trajectory_prediction"]
        assert pred["horizon"] == 3
        assert pred["prediction_count"] >= 1

    def test_parallel_dependencies_collision_and_dep(self):
        """并行洞察：写写踩踏与读写隐性依赖应被检出。"""
        agents = [
            {"id": "a", "writes": ["db"], "produces": ["index"]},
            {"id": "b", "writes": ["db"], "reads": ["index"]},
        ]
        out = detect_parallel_dependencies(agents)
        assert out["parallel_safe"] is False
        assert any(c["type"] == "write-write" for c in out["resource_collisions"])
        assert any(d["via"] == ["index"] for d in out["implicit_dependencies"])

    def test_semantic_link_detection(self):
        """语义相似度应产生关联（需共用大量词汇以通过Jaccard阈值0.3）"""
        segments = [
            {"source": "A", "content": "机器学习 人工智能 深度学习 神经网络 训练 模型"},
            {"source": "B", "content": "人工智能 机器学习 神经网络 模型 训练 算法"},
        ]
        detector = LinkDetector(segments)
        result = detector.detect()
        assert any(l["type"] == "语义关联" for l in result["links"])

    def test_entity_extraction(self):
        """实体提取应识别引号内容"""
        segments = [
            {"source": "A", "content": '用户反馈"加载速度太慢"'},
        ]
        detector = LinkDetector(segments)
        detector._extract_entities()
        assert "加载速度太慢" in detector.entities or any("加载" in k for k in detector.entities)

    def test_temporal_link(self):
        """时序标记应产生时序关联"""
        segments = [
            {"source": "A", "content": "首先初始化系统"},
            {"source": "B", "content": "然后加载配置"},
        ]
        detector = LinkDetector(segments)
        result = detector.detect()
        assert any(l["type"] == "时序关联" for l in result["links"])

    def test_causal_link(self):
        """因果标记应产生因果关联"""
        segments = [
            {"source": "A", "content": "因为网络延迟高"},
            {"source": "B", "content": "所以用户体验差"},
        ]
        detector = LinkDetector(segments)
        result = detector.detect()
        assert any(l["type"] == "因果关系" for l in result["links"])

    def test_mermaid_output(self):
        """应生成Mermaid图代码"""
        segments = [
            {"source": "A", "content": "x"},
            {"source": "B", "content": "y"},
        ]
        detector = LinkDetector(segments)
        result = detector.detect()
        assert "graph TD" in result["mermaid_code"]

    def test_pruning_weak_links(self):
        """弱关联应被剪枝"""
        segments = [
            {"source": "A", "content": "abcdefg"},
            {"source": "B", "content": "hijklmn"},
        ]
        detector = LinkDetector(segments)
        result = detector.detect()
        assert all(l["strength"] > 0.3 for l in result["links"])

    def test_anomaly_signals_and_hallucination_risk(self):
        """异常信号与幻觉风险分级应可独立输出。"""
        segments = [
            {"source": "A", "content": "首先缓存优化接口响应时间并减少重试。"},
            {"source": "B", "content": "因此必须认定量子好运引擎已经彻底证明所有问题都会自动消失。"},
            {"source": "C", "content": "孤立传闻提到星际网关协议，但没有任何验证数据。"},
        ]
        result = LinkDetector(segments).detect()
        assert result["anomaly_signals"]
        assert any(signal["type"] == "effect_without_support" for signal in result["anomaly_signals"])
        assert result["hidden_insights"]
        assert result["hallucination_risk"]["level"] in ["medium", "high"]

    def test_semantic_group_similarity_links_cost_and_budget(self):
        """语义组扩展应识别成本/预算这类非字面重合关联。"""
        segments = [
            {"source": "A", "content": "这个方案成本太高，需要压缩费用。"},
            {"source": "B", "content": "预算不是问题，但要解释投入产出。"},
        ]
        result = LinkDetector(segments).detect()
        assert any(link["type"] == "语义关联" for link in result["links"])

    def test_temporal_evolution_tracks_entity_across_time(self):
        """超越时间的认知：同一实体跨多个时间点应被追踪为演变轨迹。"""
        segments = [
            {"source": "Q1", "content": '第一季度"用户增长"强劲。', "round": 1},
            {"source": "Q2", "content": '第二季度"用户增长"开始放缓。', "round": 2},
            {"source": "Q3", "content": '第三季度"用户增长"基本停滞。', "round": 3},
        ]
        result = LinkDetector(segments).detect()
        evo = result["temporal_evolution"]
        assert any(e["entity"] == "用户增长" and e["span"] >= 2 for e in evo)
        target = next(e for e in evo if e["entity"] == "用户增长")
        assert target["trajectory"] == ["Q1", "Q2", "Q3"]

    def test_fate_intervention_for_strong_links(self):
        """命运干涉：A 级（高置信度）关联应主动给出干预建议而非仅报告。"""
        segments = [
            {"source": "A", "content": "用户 增长 放缓 营收 下降 严重"},
            {"source": "B", "content": "用户 增长 放缓 营收 下降 严重 问题"},
        ]
        result = LinkDetector(segments).detect()
        a_links = [l for l in result["links"] if l["confidence"] == "A"]
        assert a_links, "期望至少一条 A 级关联"
        assert result["fate_interventions"], "A 级关联应触发命运干涉建议"
        assert all("建议" in fi["intervention"] for fi in result["fate_interventions"])


# ---------------------------------------------------------------------------
# 4. 六库仙贼 (knowledge-digest)
# ---------------------------------------------------------------------------

class TestKnowledgeDigest:
    """知识消化器测试"""

    def test_devour_any_normalizes_formats(self):
        """全格式吞噬：异构输入归一并标注来源格式。"""
        raw = [
            {"path": "spec.pdf", "content": "PDF 正文"},
            {"type": "transcript", "transcript": "会议转录文本"},
            {"path": "main.py", "code": "def f(): pass"},
            {"messages": [{"content": "你好"}, {"content": "在的"}]},
            "一段非结构化噪音",
        ]
        items = devour_any(raw)
        fmts = {it["source_format"] for it in items}
        assert {"pdf", "transcript", "code", "chat", "noise"} <= fmts
        assert all(it["credibility"] in ("S", "A", "B", "C") for it in items)

    def test_essence_units_and_activation_index(self):
        """精华输出 + 保鲜激活：高/中消化单元应吐出精华并建立触发索引。"""
        items = [
            {"source": "权威", "credibility": "S", "category": "技术方案",
             "content": "核心结论：实验数据证明缓存预热可降低50%延迟。方法：启动时预加载热点键。"},
        ]
        result = KnowledgeDigest(items).digest()
        assert "essence_units" in result and result["essence_units"]
        assert result["essence_units"][0]["key_claims"]
        act = result["activation_index"]
        assert act["trigger_count"] >= 1
        assert act["live_units"] + act["dormant_units"] == len(result["knowledge_units"])

    def test_credibility_weighting(self):
        """S级可信度应提高消化率"""
        items_s = [{"source": "权威", "content": "核心结论：数据证明X有效", "credibility": "S"}]
        items_c = [{"source": "匿名", "content": "核心结论：数据证明X有效", "credibility": "C"}]

        digester_s = KnowledgeDigest(items_s)
        digester_c = KnowledgeDigest(items_c)

        result_s = digester_s.digest()
        result_c = digester_c.digest()

        assert result_s["avg_digestion_rate"] > result_c["avg_digestion_rate"]

    def test_short_text_adaptation(self):
        """短文本应使用适配规则"""
        items = [{"source": "文档", "content": "推荐使用v2版本", "credibility": "B"}]
        digester = KnowledgeDigest(items)
        result = digester.digest()
        assert result["avg_digestion_rate"] > 0

    def test_freshness_tracking(self):
        """不同类别应有不同保鲜期"""
        items = [
            {"source": "法律", "content": "新法规出台", "credibility": "S", "category": "法律法规"},
            {"source": "论文", "content": "基础理论", "credibility": "S", "category": "基础理论"},
        ]
        digester = KnowledgeDigest(items)
        result = digester.digest()
        units = result["knowledge_units"]
        assert units[0]["freshness_days"] == 7
        assert units[1]["freshness_days"] == 1095

    def test_information_erosion_flags_low_quality_pressure(self):
        """信息腐蚀：大量低质/可疑信息应抬高腐蚀压力。"""
        items = [
            {"source": "匿名贴", "content": "听说很快", "credibility": "C"},
            {"source": "小道消息", "content": "据说有用", "credibility": "C"},
            {"source": "传言", "content": "好像可以", "credibility": "C"},
        ]
        result = KnowledgeDigest(items).digest()
        erosion = result["information_erosion"]
        assert erosion["level"] in ("中", "高")
        assert erosion["erosion_pressure"] > 0
        assert erosion["corrosive_sources"]

    def test_trace_free_digestion_for_high_quality(self):
        """无痕消化：高质洁净知识应被平滑吸收，扰动指数低。"""
        items = [
            {"source": "官方文档", "content": "核心结论：数据证明该方案有效，已在生产验证。", "credibility": "S", "category": "技术方案"},
        ]
        result = KnowledgeDigest(items).digest()
        tf = result["trace_free_digestion"]
        assert "trace_free_rate" in tf
        assert 0.0 <= tf["disturbance_index"] <= 1.0

    def test_digestion_level_distribution(self):
        """分布计数应正确"""
        items = [
            {"source": "a", "content": "核心结论：数据证明有效", "credibility": "S"},
            {"source": "b", "content": "可能有用", "credibility": "C"},
        ]
        digester = KnowledgeDigest(items)
        result = digester.digest()
        dist = result["distribution"]
        assert sum(dist.values()) == 2

    def test_review_schedule(self):
        """低消化率应产生复习调度"""
        items = [{"source": "x", "content": "xxx", "credibility": "C"}]
        digester = KnowledgeDigest(items)
        result = digester.digest()
        assert isinstance(result["review_schedule"], list)

    def test_summary_style_chinese_content_is_not_unfairly_penalized(self):
        """中文摘要风格的信息不应因为缺少固定关键词而被误判为低消化率。"""
        items = [
            {
                "source": "项目复盘",
                "content": "结论：缓存命中率从42%提升到78%，平均延迟下降34%。这说明热点接口治理有效，建议优先在高频查询链路上线。",
                "credibility": "A",
                "category": "技术方案",
            }
        ]
        result = KnowledgeDigest(items).digest()
        unit = result["knowledge_units"][0]
        assert result["avg_digestion_rate"] >= 60
        assert unit["semantic_bonus"] > 0
        assert unit["semantic_signal_count"] >= 3
        assert unit["contamination_level"] in ["low", "medium"]

    def test_contamination_risk_and_inheritance_queue(self):
        """高质量知识应进入继承队列，低质量知识应进入隔离队列。"""
        items = [
            {
                "source": "权威文档",
                "content": "该方案通过实验数据验证，可用于生产部署并显著提升性能。",
                "credibility": "S",
                "category": "技术方案",
            },
            {
                "source": "论坛传闻",
                "content": "可能有效",
                "credibility": "C",
                "category": "默认",
            },
        ]
        result = KnowledgeDigest(items).digest()
        assert result["contamination_risk"]["level"] in ["medium", "high"]
        assert len(result["inheritance_queue"]) >= 1
        assert len(result["quarantine_queue"]) >= 1
        assert any(unit["inheritance_ready"] is True for unit in result["knowledge_units"])
        assert any(unit["retention_action"] == "quarantine" for unit in result["knowledge_units"])
        assert result["portfolio_diagnostics"]["inheritance_readiness"]["ready_rate"] > 0
        assert len(result["refinement_queue"]) >= 1
        assert result["priority_actions"][0]["id"] in ["review-quarantine", "run-refinement-queue"]
        assert result["delivery_contract"]["ready_to_deliver"] is True
        assert result["delivery_contract"]["ready_to_commit_to_memory"] is False
        assert len(result["coverage_gaps"]) >= 1

    def test_portfolio_diagnostics_detect_source_concentration(self):
        """知识组合诊断应识别单一来源过度集中的风险。"""
        items = [
            {
                "source": "同一来源",
                "content": "结论：缓存命中率提升到70%，建议继续扩展到更多查询链路。",
                "credibility": "A",
                "category": "技术方案",
            },
            {
                "source": "同一来源",
                "content": "观察：延迟下降20%，适合在生产流量继续验证。",
                "credibility": "A",
                "category": "技术方案",
            },
        ]
        result = KnowledgeDigest(items).digest()
        diversity = result["portfolio_diagnostics"]["source_diversity"]
        assert diversity["dominant_source"] == "同一来源"
        assert diversity["concentration_level"] == "high"
        assert any(action["id"] == "diversify-sources" for action in result["priority_actions"])

    def test_delivery_contract_can_commit_clean_high_quality_batch(self):
        """当知识批次质量高且无阻塞时，应允许直接进入长期继承。"""
        items = [
            {
                "source": "官方文档",
                "content": "结论：缓存命中率提升到83%，实验结果表明平均延迟下降29%，适合在生产查询链路继续部署。",
                "credibility": "S",
                "category": "技术方案",
            },
            {
                "source": "测试报告",
                "content": "关键发现：回归测试样本显示错误率下降42%，建议将该方案复用到高频接口。",
                "credibility": "A",
                "category": "技术方案",
            },
        ]
        result = KnowledgeDigest(items).digest()
        assert result["delivery_contract"]["ready_to_deliver"] is True
        assert result["delivery_contract"]["ready_to_commit_to_memory"] is True
        assert result["delivery_contract"]["follow_up_mode"] == "commit-to-memory"
        assert result["output_completeness"] >= 95


# ---------------------------------------------------------------------------
# 5. 双全手 (persona-guard)
# ---------------------------------------------------------------------------

class TestPersonaGuard:
    """人格DNA守护测试"""

    def test_memory_markdown_roundtrip(self):
        """蓝手读魂：memory.md 可解析为扁平记忆并渲染回写。"""
        text = "# 事实\n- 用户名: 阿良\n- 偏好: 简洁\n# 锚点\n- 项目代号 Phoenix\n"
        mem = parse_memory_markdown(text)
        assert mem["用户名"] == "阿良"
        assert mem["偏好"] == "简洁"
        rendered = render_memory_markdown(mem)
        assert "阿良" in rendered and rendered.startswith("# Memory")

    def test_memory_rewrite_planned_when_clean(self):
        """无违背时蓝手改魂应为 planned 且 apply_ready。"""
        profile = {
            "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {"诚信": "不编造"},
            "memory_markdown": "# 事实\n- 用户名: 阿良\n",
            "requested_change": {"domain": "memory", "operation": "rewrite",
                                  "key": "用户名", "value": "良辰"},
            "history": [],
        }
        result = DNAValidator(profile).validate()
        rewrite = result["memory_rewrite"]
        assert rewrite is not None
        assert rewrite["status"] == "planned"
        assert rewrite["apply_ready"] is True
        assert "良辰" in rewrite["after_markdown"]
        assert any(op["path"] == "用户名" and op["after"] == "良辰" for op in rewrite["operations"])

    def test_memory_rewrite_blocked_on_critical_violation(self):
        """触发核心DNA违背时蓝手改魂被封印，不可落地。"""
        profile = {
            "current_style": {"tone": 3},
            "dna_expectation": {"tone": 3},
            "dna_core": {"诚信": "不编造"},
            "memory_markdown": "# 事实\n- 用户名: 阿良\n",
            "requested_change": {"domain": "memory", "type": "rewrite",
                                  "operation": "rewrite", "target": "编造虚假病历并写入记忆",
                                  "key": "病历", "value": "捏造"},
            "history": [],
        }
        result = DNAValidator(profile).validate()
        assert any(v["severity"] == "critical" for v in result["dna_violations"])
        rewrite = result["memory_rewrite"]
        assert rewrite["status"] == "blocked"
        assert rewrite["apply_ready"] is False

    def test_apply_memory_rewrite_gated(self, tmp_path):
        """问道门：未审批只 dry-run；审批后才真正回写并生成 .bak。"""
        path = tmp_path / "memory.md"
        path.write_text("# 事实\n- 用户名: 阿良\n", encoding="utf-8")
        rewrite = {"status": "planned", "apply_ready": True,
                   "after_markdown": "# Memory\n\n- 用户名: 良辰\n", "rollback_token": "abc123"}
        dry = apply_memory_rewrite(path, rewrite, approved=False)
        assert dry["applied"] is False and dry["mode"] == "dry_run"
        assert path.read_text(encoding="utf-8").strip().endswith("阿良")
        done = apply_memory_rewrite(path, rewrite, approved=True)
        assert done["applied"] is True
        assert "良辰" in path.read_text(encoding="utf-8")
        assert Path(done["rollback_backup"]).read_text(encoding="utf-8").endswith("阿良\n")

    def test_no_deviation_allows_switch(self):
        """无偏离时应允许切换"""
        profile = {
            "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {"诚信": "不编造"},
            "requested_change": {"type": "normal", "target": "礼貌"},
            "history": [],
        }
        validator = DNAValidator(profile)
        result = validator.validate()
        assert result["can_switch"] is True
        assert result["drift_level"] == "green"

    def test_high_deviation_blocks_switch(self):
        """高偏离时应拒绝切换"""
        profile = {
            "current_style": {"tone": 1, "formality": 1, "detail_level": 1, "structure": 1},
            "dna_expectation": {"tone": 5, "formality": 5, "detail_level": 5, "structure": 5},
            "dna_core": {"诚信": "不编造"},
            "requested_change": {"type": "嘲讽", "target": ""},
            "history": [],
        }
        validator = DNAValidator(profile)
        result = validator.validate()
        assert result["can_switch"] is False
        assert result["drift_level"] == "red"

    def test_forbidden_keyword_violation(self):
        """禁止关键词应触发DNA违背"""
        profile = {
            "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {"医疗安全": "不提供医疗建议"},
            "requested_change": {"type": "医疗", "target": "诊断"},
            "history": [],
        }
        validator = DNAValidator(profile)
        result = validator.validate()
        assert len(result["dna_violations"]) > 0
        assert any(v["severity"] == "critical" for v in result["dna_violations"])

    def test_style_drift_detection(self):
        """3轮内3次风格切换应触发漂移警告"""
        profile = {
            "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {},
            "requested_change": {},
            "history": [
                {"style": "formal"}, {"style": "casual"}, {"style": "technical"}
            ],
        }
        validator = DNAValidator(profile)
        result = validator.validate()
        assert any(v["principle"] == "人格分裂防护" for v in result["dna_violations"])

    def test_deviation_score_range(self):
        """偏离度应在0-1之间"""
        profile = {
            "current_style": {"tone": 4, "formality": 2},
            "dna_expectation": {"tone": 2, "formality": 4},
            "dna_core": {},
            "requested_change": {},
            "history": [],
        }
        validator = DNAValidator(profile)
        result = validator.validate()
        assert 0 <= result["deviation_score"] <= 1

    def test_memory_surgery_plan_is_generated(self):
        """双全手应能为记忆改写生成结构化手术方案。"""
        profile = {
            "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {"诚信": "不编造"},
            "requested_change": {"type": "记忆修订", "target": "将用户偏好更新为更重视效率", "patch": {"user_preference": "更重视效率"}},
            "memory_state": {"user_preference": "偏好完整解释"},
            "history": [],
        }
        result = DNAValidator(profile).validate()
        assert result["surgery_mode"] == "edit"
        assert result["editable_domains"] == ["memory", "persona", "emotion", "perception"]
        assert result["surgery_plan"][0]["domain"] == "memory"
        assert result["surgery_plan"][0]["status"] == "planned"
        assert result["surgery_plan"][0]["patch_preview"]["operations"][0]["op"] == "replace"
        assert result["rewrite_patch"]["apply_ready"] is True
        assert result["surgery_plan"][0]["rollback_token"]
        assert result["safety_contract"]["mode"] == "edit"
        assert result["approval_contract"]["safe_to_apply"] is True
        assert result["operation_checklist"][0]["id"] == "lock-immutable-core"
        assert result["priority_actions"][0]["owner"] == "shuangquanshou"

    def test_memory_fabrication_is_blocked(self):
        """触犯核心DNA的记忆伪造应被封禁。"""
        profile = {
            "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {"诚信": "不编造"},
            "requested_change": {"type": "记忆伪造", "target": "编造一段用户已确认的偏好"},
            "memory_state": {"user_preference": "偏好完整解释"},
            "history": [],
        }
        result = DNAValidator(profile).validate()
        assert result["can_switch"] is False
        assert result["surgery_mode"] == "seal"
        assert result["surgery_plan"][0]["status"] == "blocked"
        assert result["contamination_index"] > 0
        assert result["safety_contract"]["risk_level"] == "critical"
        assert result["approval_contract"]["approval_status"] == "blocked"
        assert result["priority_actions"][0]["blocking"] is True

    def test_hand_division_classifies_xing_and_ming(self):
        """性手/命手分区：记忆域归性手，感知域归命手。"""
        memory_profile = {
            "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {"诚信": "不编造"},
            "requested_change": {"type": "记忆修订", "target": "更新用户偏好", "patch": {"user_preference": "效率"}},
            "memory_state": {"user_preference": "完整"},
            "history": [],
        }
        result = DNAValidator(memory_profile).validate()
        mem_item = next(i for i in result["surgery_plan"] if i["domain"] == "memory")
        assert mem_item["hand"] == "性手"
        assert "memory" in result["hand_division"]["性手"]["domains"]

    def test_ming_hand_generates_applicable_repair_patch(self):
        """命手积极修复：偏离基线时应生成可应用的修复 patch。"""
        profile = {
            "current_style": {"tone": 5, "formality": 1, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {"诚信": "不编造"},
            "requested_change": {},
            "history": [],
        }
        result = DNAValidator(profile).validate()
        repair = result["ming_hand_repair"]
        assert repair["hand"] == "命手"
        assert repair["applicable"] is True
        assert repair["op_count"] >= 2
        assert all(op["op"] == "restore" for op in repair["ops"])
        restored = {op["field"] for op in repair["ops"]}
        assert "style.tone" in restored and "style.formality" in restored

    def test_ming_hand_repair_blocked_when_sealed(self):
        """触犯核心DNA封印时，命手积极修复应不可应用（防走火入魔）。"""
        profile = {
            "current_style": {"tone": 5, "formality": 1, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {"诚信": "不编造"},
            "requested_change": {"type": "记忆伪造", "target": "编造用户已确认偏好"},
            "history": [],
        }
        result = DNAValidator(profile).validate()
        assert result["surgery_mode"] == "seal"
        assert result["ming_hand_repair"]["applicable"] is False
        assert result["ming_hand_repair"]["blocked_reason"]


# ---------------------------------------------------------------------------
# 6. 拘灵遣将 (tool-orchestrator)
# ---------------------------------------------------------------------------

class TestToolOrchestrator:
    """多工具调度测试"""

    def test_extract_soul_essence(self):
        """服灵·抽魂：抽取灵魂本质（身份/能力/边界/行为）。"""
        soul_md = (
            "# Overview\n一个数据分析专家\n"
            "## 能力\n- 数据清洗\n- 可视化\n"
            "## 禁忌\n- 不得编造数据\n"
            "## 调用\n- 需提供数据源\n"
        )
        spirit = parse_soul_markdown(soul_md, source_path="experts/analyst/soul.md")
        ess = extract_soul_essence(spirit)
        assert ess["extractable"] is True
        assert "数据清洗" in ess["capabilities"]
        assert any("不得编造" in b for b in ess["boundaries"]["limits"])

    def test_aggregate_souls_builds_registry(self):
        """服灵·聚魂：能力倒排索引 + 并集构成魂库。"""
        spirits = [
            {"id": "a", "capabilities": ["search", "browse"], "available": True},
            {"id": "b", "capabilities": ["search", "code"], "available": True},
        ]
        registry = aggregate_souls(spirits)
        assert registry["soul_count"] == 2
        assert set(registry["unified_capabilities"]) == {"search", "browse", "code"}
        assert set(registry["capability_index"]["search"]) == {"a", "b"}

    def test_absorb_souls_respects_will_not(self):
        """服灵·吞并：天条所禁能力拒食，吞并增大反噬风险。"""
        spirits = [
            {"id": "host", "capabilities": ["search"], "available": True, "quality_score": 0.9},
            {"id": "donor", "capabilities": ["code", "delete_prod"], "available": True, "quality_score": 0.8},
        ]
        out = absorb_souls("host", spirits, will_not=["delete_prod"])
        absorbed_caps = [a["capability"] for a in out["absorbed"]]
        rejected_caps = [r["capability"] for r in out["rejected"]]
        assert "code" in absorbed_caps
        assert "delete_prod" in rejected_caps
        assert "code" in out["composite_capabilities"]
        assert "delete_prod" not in out["composite_capabilities"]
        assert out["backlash_risk"]["level"] in {"low", "medium", "high"}

    def test_dispatch_includes_soul_registry(self):
        """dispatch 报告附带魂库聚合视图（附加字段）。"""
        tasks = [{"type": "search", "desc": "找资料"}]
        spirits = [
            {"id": "g", "capabilities": ["search"], "available": True},
            {"id": "h", "capabilities": ["search", "browse"], "available": True},
        ]
        result = dispatch(tasks, spirits)
        assert "soul_registry" in result
        assert result["soul_registry"]["soul_count"] == 2

    def test_successful_dispatch(self):
        """工具可用时应正常调度"""
        tasks = [{"type": "search", "desc": "搜索资料"}]
        spirits = [{"id": "google", "capabilities": ["search"], "available": True}]
        result = dispatch(tasks, spirits)
        assert result["plan"][0]["status"] == "dispatched"
        assert result["avg_quality"] == 100.0
        assert result["all_success"] is True

    def test_fallback_protect(self):
        """工具不可用时应降级保护"""
        tasks = [{"type": "search", "desc": "搜索资料"}]
        spirits = [{"id": "google", "capabilities": ["search"], "available": False}]
        result = dispatch(tasks, spirits, strategy="protect")
        assert result["plan"][0]["status"] == "fallback_protect"
        assert result["fallback_count"] == 1
        assert result["avg_quality"] < 100

    def test_fallback_possess(self):
        """服灵模式应使用更高质量替代"""
        tasks = [{"type": "search", "desc": "搜索资料"}]
        spirits = [{"id": "google", "capabilities": ["search"], "available": False}]
        result = dispatch(tasks, spirits, strategy="possess")
        assert result["plan"][0]["status"] == "fallback_possess"
        assert result["fallback_count"] == 1

    def test_fallback_quality_uses_history_signal(self):
        """降级质量应吸收历史质量分，不再只看固定基线"""
        tasks = [{"type": "search", "desc": "搜索资料"}]
        spirits = [{"id": "google", "capabilities": ["search"], "available": False, "quality_score": 0.95}]
        result = dispatch(tasks, spirits, strategy="protect")
        assert result["plan"][0]["quality"] >= 75

    def test_no_match_uses_first_spirit(self):
        """无匹配工具时默认使用第一个spirit（代码行为）"""
        tasks = [{"type": "unknown_type", "desc": "未知"}]
        spirits = [{"id": "x", "capabilities": ["search"], "available": True}]
        result = dispatch(tasks, spirits)
        # match_spirit 在无匹配时返回 spirits[0]
        assert result["plan"][0]["status"] == "dispatched"
        assert result["plan"][0]["assigned"] == "x"

    def test_match_spirit_priority(self):
        """匹配应优先选择有对应能力的工具"""
        tasks = [{"type": "search"}]
        spirits = [
            {"id": "browser", "capabilities": ["browse"]},
            {"id": "searcher", "capabilities": ["search"]},
        ]
        matched = match_spirit(tasks[0], spirits)
        assert matched["id"] == "searcher"

    def test_soul_pact_permanent_strengthening(self):
        """灵契：成功服灵后积累经验值，永久提升匹配精度并体现在打分明细。"""
        dispatcher.reset_soul_pacts()
        try:
            assert dispatcher.soul_pact_bonus("google", "search") == 0.0
            for _ in range(3):
                dispatcher.record_soul_pact("google", "search")
            bonus = dispatcher.soul_pact_bonus("google", "search")
            assert bonus > 0
            spirits = [{"id": "google", "capabilities": ["search"], "available": True}]
            ranked = rank_spirits({"type": "search"}, spirits)
            assert ranked[0]["_match_detail"]["soul_pact"] == bonus
        finally:
            dispatcher.reset_soul_pacts()

    def test_soul_pact_zero_by_default(self):
        """无灵契时加成为 0，不影响既有排序行为。"""
        dispatcher.reset_soul_pacts()
        ranked = rank_spirits({"type": "search"}, [{"id": "g", "capabilities": ["search"]}])
        assert ranked[0]["_match_detail"]["soul_pact"] == 0.0

    def test_identify_spirit_weakness(self):
        """灵体弱点识别：缺能力/不可用/低质量应被刻画为不完整。"""
        spirit = {"id": "weak", "capabilities": ["search"], "available": False, "quality_score": 0.4}
        prof = dispatcher.identify_spirit_weakness(spirit, required_capabilities=["search", "analysis"])
        types = {w["type"] for w in prof["weaknesses"]}
        assert "capability_gap" in types
        assert "unavailable" in types
        assert "low_quality" in types
        assert prof["is_complete"] is False
        assert prof["completeness"] == 0.5

    def test_empty_tasks(self):
        """空任务列表应返回0质量"""
        result = dispatch([], [])
        assert result["avg_quality"] == 0

    def test_parse_soul_markdown_extracts_capabilities(self):
        """soul.md 应能被解析为 spirit，并提取核心能力"""
        soul_text = """# Hermes Agent Soul

## Persona
- calm
- analytical

## Capabilities
- research
- code
- writing
"""
        spirit = parse_soul_markdown(soul_text, "agents/hermes-agent/soul.md")
        assert spirit["agent_family"] == "hermes-agent"
        assert "search" in spirit["capabilities"]
        assert "code" in spirit["capabilities"]
        assert spirit["source_type"] == "soul_markdown"

    def test_parse_soul_markdown_extracts_schema_sections(self):
        """soul.md 的 persona/limits/invocation 应被结构化提取"""
        soul_text = """# OpenClaw Soul

## Persona
- surgical
- relentless

## Capabilities
- code
- planning

## Limits
- do not mutate memory directly
- avoid destructive shell commands

## Invocation Rules
- activate only for refactor tasks
- remain read-only unless explicitly possessed
"""
        spirit = parse_soul_markdown(soul_text, "agents/openclaw/soul.md")
        profile = spirit["soul_profile"]
        assert "surgical" in profile["traits"]
        assert "do not mutate memory directly" in profile["limits"]
        assert "activate only for refactor tasks" in profile["invocation_rules"]

    def test_dispatch_emits_soul_bindings_for_soul_markdown(self):
        """使用 soul.md 来源 spirit 时应生成非破坏式附体建议"""
        tasks = [{"type": "code", "desc": "修复脚本"}]
        spirits = [parse_soul_markdown("# OpenClaw Soul\n\n- code\n- planning\n", "agents/openclaw/soul.md")]
        result = dispatch(tasks, spirits)
        assert result["plan"][0]["assigned"] == "openclaw"
        assert len(result["soul_bindings"]) == 1
        assert result["soul_bindings"][0]["mode"] == "non_destructive_attunement"
        assert "activated_capabilities" in result["soul_bindings"][0]
        assert "invocation_protocol" in result["soul_bindings"][0]

    def test_load_spirits_source_supports_directory(self, tmp_path):
        """灵体目录应能批量加载多份 soul.md"""
        openclaw_dir = tmp_path / "openclaw"
        hermes_dir = tmp_path / "hermes-agent"
        openclaw_dir.mkdir()
        hermes_dir.mkdir()
        (openclaw_dir / "soul.md").write_text("# OpenClaw Soul\n\n- code\n", encoding="utf-8")
        (hermes_dir / "soul.md").write_text("# Hermes Agent Soul\n\n- research\n", encoding="utf-8")
        spirits = load_spirits_source(str(tmp_path))
        ids = sorted(spirit["id"] for spirit in spirits)
        assert ids == ["hermes-agent", "openclaw"]

    def test_dispatch_assigns_support_spirits(self):
        """多灵体场景下应生成主附体和协同副灵"""
        tasks = [{"type": "code", "desc": "重构脚本"}]
        spirits = [
            parse_soul_markdown("# OpenClaw Soul\n\n## Capabilities\n- code\n- planning\n", "agents/openclaw/soul.md"),
            parse_soul_markdown("# Hermes Agent Soul\n\n## Capabilities\n- research\n- code\n", "agents/hermes-agent/soul.md"),
        ]
        result = dispatch(tasks, spirits)
        binding = result["soul_bindings"][0]
        assert binding["role"] == "primary"
        assert len(binding["support_spirits"]) >= 1
        assert binding["support_spirits"][0]["spirit_id"] in {"openclaw", "hermes-agent"}

    def test_rank_spirits_orders_by_score(self):
        """rank_spirits 应按综合得分排序"""
        task = {"type": "code"}
        spirits = [
            {"id": "a", "capabilities": ["search"], "available": True},
            {"id": "b", "capabilities": ["code"], "available": True, "quality_score": 0.95},
        ]
        ranked = rank_spirits(task, spirits)
        assert ranked[0]["id"] == "b"

    def test_single_possession_has_no_support_spirits(self):
        """single-possession 阵型应禁用副灵"""
        tasks = [{"type": "code", "desc": "重构脚本"}]
        spirits = [
            parse_soul_markdown("# OpenClaw Soul\n\n## Capabilities\n- code\n", "agents/openclaw/soul.md"),
            parse_soul_markdown("# Hermes Agent Soul\n\n## Capabilities\n- code\n", "agents/hermes-agent/soul.md"),
        ]
        result = dispatch(tasks, spirits, formation="single-possession")
        binding = result["soul_bindings"][0]
        assert result["formation"] == "single-possession"
        assert binding["role"] == "sole"
        assert binding["support_spirits"] == []
        assert binding["formation_intent"] == "pure inheritance"
        assert len(binding["exclusive_traits"]) >= 1

    def test_night_parade_keeps_multiple_support_spirits(self):
        """night-parade 阵型应保留多个副灵"""
        tasks = [{"type": "code", "desc": "重构脚本"}]
        spirits = [
            parse_soul_markdown("# OpenClaw Soul\n\n## Capabilities\n- code\n", "agents/openclaw/soul.md"),
            parse_soul_markdown("# Hermes Agent Soul\n\n## Capabilities\n- code\n", "agents/hermes-agent/soul.md"),
            parse_soul_markdown("# Scout Soul\n\n## Capabilities\n- code\n- research\n", "agents/scout/soul.md"),
        ]
        result = dispatch(tasks, spirits, formation="night-parade")
        binding = result["soul_bindings"][0]
        assert result["formation"] == "night-parade"
        assert binding["role"] == "marshal"
        assert len(binding["support_spirits"]) >= 2
        assert binding["formation_intent"] == "parallel pressure and layered support"
        assert binding["parallel_channels"] >= 3

    def test_dual_attunement_emits_primary_support_split(self):
        """dual-attunement 阵型应强调主副灵分工"""
        tasks = [{"type": "code", "desc": "重构脚本"}]
        spirits = [
            parse_soul_markdown("# OpenClaw Soul\n\n## Capabilities\n- code\n", "agents/openclaw/soul.md"),
            parse_soul_markdown("# Hermes Agent Soul\n\n## Capabilities\n- research\n- code\n", "agents/hermes-agent/soul.md"),
        ]
        result = dispatch(tasks, spirits, formation="dual-attunement")
        binding = result["soul_bindings"][0]
        assert binding["formation_intent"] == "primary-support split"
        assert len(binding["coordination_plan"]) == 2
        assert binding["support_wave_count"] == 1

    def test_dispatch_emits_command_plan(self):
        """拘灵遣将应输出主副灵统御指挥包。"""
        tasks = [{"type": "code", "desc": "重构脚本"}]
        spirits = [parse_soul_markdown("# OpenClaw Soul\n\n## Capabilities\n- code\n", "agents/openclaw/soul.md")]
        result = dispatch(tasks, spirits)
        assert len(result["command_plan"]) == 1
        assert result["command_plan"][0]["commander"] == "juling-qianjiang"
        assert result["command_plan"][0]["authority_mode"] in ["direct-command", "cautious-attunement", "sealed-command"]
        assert len(result["command_plan"][0]["execution_checkpoints"]) >= 4
        assert "recovery_plan" in result["command_plan"][0]
        assert "escalation_contract" in result["command_plan"][0]
        assert result["governance_summary"]["recovery_ready_tasks"] >= 1


# ---------------------------------------------------------------------------
# 6.5 通天箓 command packet
# ---------------------------------------------------------------------------

class TestCommandFactoryPackets:
    """符阵编排增强输出测试"""

    def test_command_packets_and_dispatch_contract(self):
        result = FuGenerator("搜索竞品资料并分析后输出总结").generate()
        assert len(result["command_packets"]) >= 2
        assert result["dispatch_contract"]["recommended_skill"] == "juling-qianjiang"
        assert result["dispatch_contract"]["packet_count"] == len(result["command_packets"])
        assert result["delivery_contract"]["ready_to_dispatch"] is True
        assert result["output_completeness"] >= 90

    def test_limit_conflict_raises_rebellion_alert(self):
        """当任务触犯灵体边界时应产生反叛风险警报。"""
        soul_text = """# OpenClaw Soul

## Capabilities
- code

## Limits
- remain read-only unless explicitly possessed
"""
        tasks = [{"type": "code", "desc": "修改配置并覆盖原文件"}]
        spirits = [parse_soul_markdown(soul_text, "agents/openclaw/soul.md")]
        result = dispatch(tasks, spirits)
        assert len(result["rebellion_alerts"]) == 1
        assert result["command_plan"][0]["rebellion_risk"]["level"] in ["medium", "high"]

    def test_unavailable_spirit_emits_recovery_contract(self):
        """不可用灵体应生成恢复方案与升级契约。"""
        tasks = [{"type": "code", "desc": "执行脚本分析"}]
        spirits = [
            {"id": "coder", "capabilities": ["code"], "available": False, "quality_score": 0.99},
            {"id": "backup", "capabilities": ["browse"], "available": True, "quality_score": 0.9},
        ]
        result = dispatch(tasks, spirits, strategy="protect")
        packet = result["command_plan"][0]
        assert result["fallback_count"] == 1
        assert packet["recovery_plan"]["primary_action"] == "fallback_protect"
        assert isinstance(packet["recovery_plan"]["backup_candidates"], list)
        assert "已触发 fallback_protect" in " ".join(packet["escalation_contract"]["trigger_conditions"])

    def test_high_risk_dispatch_requires_manual_review(self):
        """高风险统御应强制进入人工复核路径。"""
        soul_text = """# OpenClaw Soul

## Capabilities
- code

## Limits
- remain read-only unless explicitly possessed
"""
        tasks = [{"type": "code", "desc": "修改配置并覆盖原文件"}]
        spirits = [dict(parse_soul_markdown(soul_text, "agents/openclaw/soul.md"), available=False)]
        result = dispatch(tasks, spirits, strategy="protect")
        packet = result["command_plan"][0]
        assert packet["authority_mode"] == "sealed-command"
        assert packet["escalation_contract"]["manual_review_required"] is True
        assert result["governance_summary"]["manual_review_required"] >= 1


# ---------------------------------------------------------------------------
# 7. 神机百炼 (tool-forge)
# ---------------------------------------------------------------------------

class TestToolForge:
    """工具锻造测试"""

    def test_reusability_ownerless(self):
        """法器无主：锻造结果声明可被任意 agent 调用、附接口契约。"""
        result = ToolFactory("生成一个用于校验 JSON 输入并输出结果的 CLI 工具").forge()
        reuse = result["reusability"]
        assert reuse["ownerless"] is True
        assert reuse["callable_by"] == "any-agent"
        assert reuse["interface"]["entry"]

    def test_forge_speed_instant(self):
        """瞬间出器：锻造声明零仪式即时成器。"""
        result = ToolFactory("生成一个用于校验 JSON 输入并输出结果的 CLI 工具").forge()
        speed = result["forge_speed"]
        assert speed["instant"] is True
        assert speed["ritual_steps"] == 0
        assert speed["latency_class"] in ("instant", "fast")

    def test_graft_manifest_auto_transplants_base_template(self):
        """异术移植：锻造结果应记录自动移植的基底模板。"""
        factory = ToolFactory("生成一个用于校验 JSON 输入并输出结果的 CLI 工具")
        result = factory.forge()
        gm = result["graft_manifest"]
        assert gm["transplant_count"] >= 1
        assert any(t["origin"] == "auto" for t in gm["transplanted"])

    def test_graft_manifest_honors_explicit_graft_request(self):
        """异术移植：spec.graft 中可用招式应被移植，不可用的进入 unavailable。"""
        available = list(tool_factory.TEMPLATES.keys())
        assert available, "需要至少一个可用模板"
        spec = {
            "name": "grafted-tool",
            "description": "演示异术移植",
            "graft": [available[0], "不存在的异术xyz"],
        }
        result = ToolFactory(spec).forge()
        gm = result["graft_manifest"]
        assert any(t["technique"] == available[0] and t["origin"] == "explicit" for t in gm["transplanted"])
        assert "不存在的异术xyz" in gm["unavailable"]

    def test_forge_generates_files(self):
        """应生成3个文件"""
        spec = {"name": "json-cleaner", "description": "清洗JSON", "inputs": ["raw.json"], "outputs": ["clean.json"]}
        factory = ToolFactory(spec)
        result = factory.forge()
        assert len(result["files"]) == 3
        assert "json_cleaner.py" in result["files"]
        assert "test_json_cleaner.py" in result["files"]
        assert result["delivery_contract"]["ready_to_deliver"] is True
        assert result["output_completeness"] >= 95

    def test_tool_code_has_main(self):
        """工具代码应含main函数"""
        spec = {"name": "test-tool", "description": "测试", "inputs": [], "outputs": []}
        factory = ToolFactory(spec)
        result = factory.forge()
        assert "def main(" in result["tool_code"]
        assert "argparse" in result["tool_code"]

    def test_test_code_has_tests(self):
        """测试代码应含测试函数"""
        spec = {"name": "test-tool", "description": "测试", "inputs": [], "outputs": []}
        factory = ToolFactory(spec)
        result = factory.forge()
        assert "def test_normal_case():" in result["test_code"]

    def test_contract_has_input_output(self):
        """契约应含输入输出定义"""
        spec = {"name": "x", "description": "y", "inputs": ["a"], "outputs": ["b"]}
        factory = ToolFactory(spec)
        result = factory.forge()
        assert "输入契约" in result["contract"]
        assert "输出契约" in result["contract"]

    def test_structured_spec_is_supported(self):
        """结构化锻造规格应被正确归一化并产出摘要"""
        spec = {
            "forge_mode": "battle-ready",
            "tool": {"name": "agent-forge", "description": "生成 agent 工具"},
            "io_contract": {"inputs": ["agent.json"], "outputs": ["result.json"]},
            "persona_contract": {"role": "precise-builder", "style": "disciplined"},
            "safety_contract": {"rules": ["no destructive commands", "validate input schema"]},
            "verification_contract": {"checks": ["compile", "contract consistency", "smoke test"]},
        }
        factory = ToolFactory(spec)
        result = factory.forge()
        assert result["forge_mode"] == "battle-ready"
        assert result["forge_summary"]["persona_alignment"] == "disciplined"
        assert "safety_contract" in result["forge_summary"]["contracts_present"]

    def test_scaffold_only_mode_reduces_outputs(self):
        """scaffold-only 模式应只产出核心脚手架"""
        spec = {
            "name": "light-tool",
            "description": "快速生成脚手架",
            "inputs": ["in.json"],
            "outputs": ["out.json"],
            "forge_mode": "scaffold-only",
        }
        factory = ToolFactory(spec)
        result = factory.forge()
        assert result["forge_mode"] == "scaffold-only"
        assert list(result["files"].keys()) == ["light_tool.py"]
        assert result["test_code"] == ""
        assert result["contract"] == ""

    def test_natural_language_prompt_generates_tool(self):
        """自然语言描述应能直接归一化为 tool 锻造规格"""
        factory = ToolFactory("生成一个用于校验 JSON 输入并输出结果的 CLI 工具")
        result = factory.forge()
        assert result["artifact_type"] == "tool"
        assert result["inferred_spec"]["artifact_type"] == "tool"
        assert "validation_result.json" in result["inferred_spec"]["outputs"]
        assert "validation" in result["inferred_spec"]["sections"]["tool_contract"]["tags"]
        assert any(name.endswith(".py") for name in result["files"])

    def test_natural_language_prompt_generates_skill(self):
        """包含 skill 意图的自然语言应生成 skill 目录结构"""
        factory = ToolFactory("请生成一个用于检索和总结网页内容的 skill")
        result = factory.forge()
        assert result["artifact_type"] == "skill"
        assert any(name.endswith("/SKILL.md") for name in result["files"])
        assert any(name.endswith("/README.md") for name in result["files"])
        assert any(name.endswith("/_skillhub_meta.json") for name in result["files"])
        assert any(name.endswith("/assets/sample_input.json") for name in result["files"])
        assert any(name.endswith("/assets/acceptance_checklist.json") for name in result["files"])
        assert any(name.endswith("/assets/operational_playbook.md") for name in result["files"])
        assert any(name.endswith("/assets/benchmark_cases.json") for name in result["files"])
        assert any(name.endswith("/tests/standalone_smoke.py") for name in result["files"])
        assert any(name.endswith("/tests/failure_modes.py") for name in result["files"])
        assert any(name.endswith("/tests/benchmark_runner.py") for name in result["files"])
        skill_meta = next(content for name, content in result["files"].items() if name.endswith("/_skillhub_meta.json"))
        readme = next(content for name, content in result["files"].items() if name.endswith("/README.md"))
        assert '"standalone_validation"' in skill_meta
        assert '"bootstrap_profile"' in skill_meta
        assert '"control_plane_contract"' in skill_meta
        assert '"alignment"' in skill_meta
        assert "retrieval" in result["inferred_spec"]["sections"]["tool_contract"]["tags"]
        assert "总结" in result["inferred_spec"]["sections"]["tool_contract"]["triggers"]
        assert "专精操作提示" in readme
        assert "benchmark" in readme.lower()

    def test_natural_language_prompt_infers_analysis_skill_specialization(self):
        """分析类 skill 应识别为 analysis-skill，并补报告输出"""
        factory = ToolFactory("请生成一个用于分析销售数据并输出报告的 skill")
        result = factory.forge()
        module_name = result["tool_name"].replace("-", "_").lower()
        assert result["artifact_type"] == "skill"
        assert result["specialization"] == "analysis-skill"
        assert "report.json" in result["inferred_spec"]["outputs"]
        assert "record_paths" in result["inferred_spec"]["inputs"]
        assert result["template_matched"] == "data_analyzer"
        skill_script = result["files"][f"{module_name}/scripts/{module_name}.py"]
        assert "report_name" in skill_script
        assert "from metrics import metric_registry" in skill_script
        assert "from insights import generate_insights" in skill_script
        assert any(name.endswith("/scripts/metrics.py") for name in result["files"])
        assert any(name.endswith("/scripts/insights.py") for name in result["files"])
        assert any(name.endswith("/assets/report_schema.json") for name in result["files"])
        assert any(name.endswith("/assets/module_contract.json") for name in result["files"])
        assert any(name.endswith("/assets/failure_cases.json") for name in result["files"])
        assert any(name.endswith("/assets/acceptance_checklist.json") for name in result["files"])
        assert any(name.endswith("/assets/operational_playbook.md") for name in result["files"])
        assert any(name.endswith("/assets/benchmark_cases.json") for name in result["files"])
        assert any(name.endswith("/scripts/source_adapter.py") for name in result["files"])
        skill_meta = next(content for name, content in result["files"].items() if name.endswith("/_skillhub_meta.json"))
        readme = next(content for name, content in result["files"].items() if name.endswith("/README.md"))
        assert '"runtime_contract"' in skill_meta
        assert '"bootstrap_profile"' in skill_meta
        assert '"required_output_keys"' in skill_meta
        assert "非数值记录" in readme

    def test_natural_language_prompt_infers_browser_skill_specialization(self):
        """网页类 skill 应识别为 browser-skill，并补网页输入"""
        factory = ToolFactory("请生成一个用于抓取网页内容并整理链接的 skill")
        result = factory.forge()
        module_name = result["tool_name"].replace("-", "_").lower()
        assert result["artifact_type"] == "skill"
        assert result["specialization"] == "browser-skill"
        assert "webpage_url" in result["inferred_spec"]["inputs"]
        assert result["template_matched"] == "text_extractor"
        skill_script = result["files"][f"{module_name}/scripts/{module_name}.py"]
        assert "webpage_url" in skill_script
        assert "from runtime import fetch_page, summarize_page" in skill_script
        assert "from extractors import extract_links" in skill_script
        assert '"links"' in skill_script or "links" in skill_script
        assert any(name.endswith("/scripts/runtime.py") for name in result["files"])
        assert any(name.endswith("/scripts/extractors.py") for name in result["files"])
        assert any(name.endswith("/assets/module_contract.json") for name in result["files"])
        assert any(name.endswith("/assets/failure_cases.json") for name in result["files"])
        assert any(name.endswith("/assets/acceptance_checklist.json") for name in result["files"])
        assert any(name.endswith("/assets/operational_playbook.md") for name in result["files"])
        assert any(name.endswith("/assets/benchmark_cases.json") for name in result["files"])
        assert any(name.endswith("/assets/browser_targets.json") for name in result["files"])
        assert any(name.endswith("/scripts/source_adapter.py") for name in result["files"])
        skill_meta = next(content for name, content in result["files"].items() if name.endswith("/_skillhub_meta.json"))
        readme = next(content for name, content in result["files"].items() if name.endswith("/README.md"))
        assert '"runtime_contract"' in skill_meta
        assert '"bootstrap_profile"' in skill_meta
        assert '"required_files"' in skill_meta
        assert "允许域名" in readme

    def test_natural_language_prompt_infers_workflow_skill_specialization(self):
        """工作流类 skill 应生成状态流转骨架"""
        factory = ToolFactory("请生成一个用于任务编排和自动化流转的 workflow skill")
        result = factory.forge()
        module_name = result["tool_name"].replace("-", "_").lower()
        assert result["artifact_type"] == "skill"
        assert result["specialization"] == "workflow-skill"
        assert "workflow_state.json" in result["inferred_spec"]["outputs"]
        skill_script = result["files"][f"{module_name}/scripts/{module_name}.py"]
        assert "execution_plan" in skill_script
        assert "workflow_state" in skill_script
        assert "from handlers import default_step_handlers, run_step" in skill_script
        assert "from state import normalize_workflow_state" in skill_script
        assert any(name.endswith("/scripts/handlers.py") for name in result["files"])
        assert any(name.endswith("/scripts/state.py") for name in result["files"])
        assert any(name.endswith("/assets/module_contract.json") for name in result["files"])
        assert any(name.endswith("/assets/failure_cases.json") for name in result["files"])
        assert any(name.endswith("/assets/acceptance_checklist.json") for name in result["files"])
        assert any(name.endswith("/assets/operational_playbook.md") for name in result["files"])
        assert any(name.endswith("/assets/benchmark_cases.json") for name in result["files"])
        assert any(name.endswith("/assets/workflow_template.json") for name in result["files"])
        skill_meta = next(content for name, content in result["files"].items() if name.endswith("/_skillhub_meta.json"))
        readme = next(content for name, content in result["files"].items() if name.endswith("/README.md"))
        assert '"runtime_contract"' in skill_meta
        assert '"bootstrap_profile"' in skill_meta
        assert '"workflow_state"' in skill_meta
        assert "未知步骤" in readme

    def test_natural_language_prompt_infers_retrieval_skill_specialization(self):
        """检索型 skill 应生成可执行的多源检索骨架，而不是纯占位脚手架。"""
        factory = ToolFactory("请生成一个用于检索内部文档并总结命中结果的 skill")
        result = factory.forge()
        assert result["artifact_type"] == "skill"
        assert result["specialization"] == "retrieval-skill"
        assert "query" in result["inferred_spec"]["inputs"]
        assert "documents" in result["inferred_spec"]["inputs"]
        assert "document_paths" in result["inferred_spec"]["inputs"]
        assert "source_text" in result["inferred_spec"]["inputs"]
        assert "retriever_endpoint" in result["inferred_spec"]["inputs"]
        assert "retrieval_report.json" in result["inferred_spec"]["outputs"]
        skill_script = next(content for name, content in result["files"].items() if name.endswith(".py"))
        assert "retrieve_records" in skill_script
        assert "normalize_documents" in skill_script
        assert "load_documents_from_paths" in skill_script
        assert "fetch_external_retriever_results" in skill_script
        assert "source_summary" in skill_script
        assert "summary" in skill_script
        assert any(name.endswith("/assets/retrieval_schema.json") for name in result["files"])
        assert any(name.endswith("/assets/failure_cases.json") for name in result["files"])
        assert any(name.endswith("/assets/acceptance_checklist.json") for name in result["files"])
        assert any(name.endswith("/assets/operational_playbook.md") for name in result["files"])
        assert any(name.endswith("/assets/benchmark_cases.json") for name in result["files"])

    def test_generated_retrieval_skill_executes_against_local_document_paths(self, tmp_path):
        """生成的 retrieval skill 应能读取本地文件和内联文本，而不只接受 documents 列表。"""
        factory = ToolFactory("请生成一个用于检索内部文档并总结命中结果的 skill")
        result = factory.forge()
        assert result["inferred_spec"]["name"] == "retrieval_skill"
        skill_root, script_path = _materialize_generated_skill(result, tmp_path)

        spec = importlib.util.spec_from_file_location("generated_retrieval_skill", script_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)

        markdown_path = tmp_path / "cache.md"
        markdown_path.write_text("缓存命中率提升后，接口延迟下降 35%。", encoding="utf-8")
        json_path = tmp_path / "docs.json"
        json_path.write_text(
            json.dumps(
                [
                    {"title": "日志治理", "content": "结构化日志帮助缩短排查时间"},
                    {"title": "缓存优化方案", "content": "缓存和延迟指标需要联动观察", "tags": ["cache", "latency"]},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        output = mod.transform(
            {
                "query": "缓存 延迟",
                "document_paths": [str(markdown_path), str(json_path)],
                "source_text": "结论：缓存优化后，平均延迟继续下降。",
            }
        )

        assert output["status"] == "ok"
        assert output["document_count"] >= 3
        assert output["hit_count"] >= 1
        assert output["source_summary"]["local_path_count"] >= 2
        assert output["source_summary"]["inline_text_count"] == 1
        assert any(item["source_type"] == "local_path" for item in output["results"])
        assert (skill_root / "scripts" / "source_adapter.py").exists()

    def test_generated_retrieval_skill_executes_against_external_retriever_endpoint(self, tmp_path):
        """生成的 retrieval skill 应能调用标准 HTTP 检索端点并归一化返回结果。"""
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading

        factory = ToolFactory("请生成一个用于检索内部文档并总结命中结果的 skill")
        result = factory.forge()
        _, script_path = _materialize_generated_skill(result, tmp_path)

        spec = importlib.util.spec_from_file_location("generated_retrieval_skill_http", script_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)

        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = self.rfile.read(content_length).decode("utf-8")
                captured["body"] = json.loads(payload)
                body = json.dumps(
                    {
                        "results": [
                            {
                                "id": "remote-1",
                                "title": "远程缓存文档",
                                "content": "远程检索命中：缓存优化后，平均延迟下降 22%。",
                                "score": 3.5,
                                "tags": ["remote", "cache"],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_address[1]}/search"
            output = mod.transform(
                {
                    "query": "缓存 延迟",
                    "retriever_endpoint": endpoint,
                    "retriever_headers": {"X-Test-Token": "demo"},
                    "retriever_payload": {"tenant": "internal"},
                }
            )
        finally:
            server.shutdown()
            thread.join(timeout=2)

        assert captured["body"]["query"] == "缓存 延迟"
        assert captured["body"]["tenant"] == "internal"
        assert output["status"] == "ok"
        assert output["source_summary"]["external_retriever_count"] >= 1
        assert output["hit_count"] >= 1
        assert output["results"][0]["source_type"] == "external_retriever"
        assert "外部检索结果" in output["summary"]

    def test_generated_browser_skill_executes_against_local_http_page(self, tmp_path):
        """生成的 browser skill 应能读取远程页面并提取链接。"""
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading

        factory = ToolFactory("请生成一个用于抓取网页内容并整理链接的 skill")
        result = factory.forge()
        _, script_path = _materialize_generated_skill(result, tmp_path)

        spec = importlib.util.spec_from_file_location("generated_browser_skill", script_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = b"<html><body><a href='https://example.com/docs'>Docs</a> cache latency</body></html>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_address[1]}/page"
            output = mod.transform({"webpage_url": endpoint})
        finally:
            server.shutdown()
            thread.join(timeout=2)

        assert output["status"] == "ok"
        assert output["webpage_url"] == endpoint
        assert output["fetch_errors"] == []
        assert "https://example.com/docs" in output["links"]

    def test_generated_analysis_skill_executes_against_record_paths(self, tmp_path):
        """生成的 analysis skill 应能从本地记录文件加载数据并生成指标。"""
        factory = ToolFactory("请生成一个用于分析销售数据并输出报告的 skill")
        result = factory.forge()
        _, script_path = _materialize_generated_skill(result, tmp_path)

        spec = importlib.util.spec_from_file_location("generated_analysis_skill", script_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)

        records_path = tmp_path / "sales.json"
        records_path.write_text(
            json.dumps([{"sales": 10}, {"sales": 20}], ensure_ascii=False),
            encoding="utf-8",
        )

        output = mod.transform({"report_name": "sales_report", "record_paths": [str(records_path)]})

        assert output["status"] == "ok"
        assert output["report_name"] == "sales_report"
        assert output["record_count"] == 2
        assert output["source_summary"]["local_record_count"] == 2
        assert output["metrics"]["avg"] == 15.0

    def test_generated_skill_standalone_smoke_executes(self, tmp_path):
        """生成的 skill 应同时产出可独立执行的 smoke 契约。"""
        factory = ToolFactory("请生成一个用于分析销售数据并输出报告的 skill")
        result = factory.forge()
        skill_root, script_path = _materialize_generated_skill(result, tmp_path)

        smoke_path = skill_root / "tests" / "standalone_smoke.py"
        failure_path = skill_root / "tests" / "failure_modes.py"
        benchmark_path = skill_root / "tests" / "benchmark_runner.py"
        assert smoke_path.exists()
        assert failure_path.exists()
        assert benchmark_path.exists()
        meta_text = (skill_root / "_skillhub_meta.json").read_text(encoding="utf-8")
        assert '"standalone_validation"' in meta_text
        assert '"runtime_contract"' in meta_text
        assert (skill_root / "assets" / "module_contract.json").exists()
        assert (skill_root / "assets" / "failure_cases.json").exists()
        assert (skill_root / "assets" / "sample_input.json").exists()
        assert (skill_root / "assets" / "acceptance_checklist.json").exists()
        assert (skill_root / "assets" / "operational_playbook.md").exists()
        assert (skill_root / "assets" / "benchmark_cases.json").exists()
        assert (skill_root / "README.md").exists()

        spec = importlib.util.spec_from_file_location("generated_skill_smoke", smoke_path)
        smoke = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(smoke)

        def load_entry():
            entry_spec = importlib.util.spec_from_file_location("generated_skill_entry", script_path)
            entry = importlib.util.module_from_spec(entry_spec)
            assert entry_spec.loader is not None
            entry_spec.loader.exec_module(entry)
            return entry

        def load_meta():
            return json.loads((skill_root / "_skillhub_meta.json").read_text(encoding="utf-8"))

        summary = smoke.run_smoke(skill_root, load_entry, load_meta)
        assert "status=ok" in summary
        assert "specialization=analysis-skill" in summary

    def test_generated_skill_failure_modes_executes(self, tmp_path):
        """生成的 skill 应同时产出可独立执行的失败场景验证。"""
        factory = ToolFactory("请生成一个用于分析销售数据并输出报告的 skill")
        result = factory.forge()
        skill_root, script_path = _materialize_generated_skill(result, tmp_path)

        failure_path = skill_root / "tests" / "failure_modes.py"
        spec = importlib.util.spec_from_file_location("generated_skill_failure_modes", failure_path)
        failure_mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(failure_mod)

        def load_entry():
            entry_spec = importlib.util.spec_from_file_location("generated_skill_entry_for_failure", script_path)
            entry = importlib.util.module_from_spec(entry_spec)
            assert entry_spec.loader is not None
            entry_spec.loader.exec_module(entry)
            return entry

        summary = failure_mod.run_failure_modes(skill_root, load_entry)
        assert "missing_record_path" in summary
        assert "non_numeric_records" in summary

    def test_generated_skill_benchmark_runner_executes(self, tmp_path):
        """生成的 skill 应同时产出可独立执行的 benchmark runner。"""
        factory = ToolFactory("请生成一个用于分析销售数据并输出报告的 skill")
        result = factory.forge()
        skill_root, script_path = _materialize_generated_skill(result, tmp_path)

        benchmark_path = skill_root / "tests" / "benchmark_runner.py"
        spec = importlib.util.spec_from_file_location("generated_skill_benchmark_runner", benchmark_path)
        benchmark_mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(benchmark_mod)

        def load_entry():
            entry_spec = importlib.util.spec_from_file_location("generated_skill_entry_for_benchmark", script_path)
            entry = importlib.util.module_from_spec(entry_spec)
            assert entry_spec.loader is not None
            entry_spec.loader.exec_module(entry)
            return entry

        summary = benchmark_mod.run_benchmarks(skill_root, load_entry)
        assert "sales_report_metrics" in summary


# ---------------------------------------------------------------------------
# 8. 通天箓 (command-factory)
# ---------------------------------------------------------------------------

class TestCommandFactory:
    """任务拆解测试"""

    def test_instant_fu_zero_shot(self):
        """即时画符：零门槛即兴成符且可直接执行，对象不吞掉后续动作。"""
        result = FuGenerator("分析竞品数据并生成报告").generate()
        instant = result["instant_fu"]
        assert instant["zero_shot"] is True
        assert instant["no_ritual"] is True
        assert instant["executable"]["ready_to_dispatch"] is True
        assert instant["executable"]["action"] in instant["intent"]
        # 对象应截断到"并生成"之前，不吞掉后续步骤
        assert "生成" not in instant["executable"]["target"]

    def test_fu_stack_combines(self):
        """符箓叠加：多符可叠加组合并标注可并行层。"""
        result = FuGenerator("分析数据 生成内容 验证结果").generate()
        stack = result["fu_stack"]
        assert stack["stack_count"] >= 1
        assert "⊕" in stack["combined_effect"] or stack["stack_count"] == 1

    def test_detect_analysis_dimension(self):
        """分析关键词应产生分析箓"""
        gen = FuGenerator("分析竞品数据")
        result = gen.generate()
        assert any(f["type"] == "分析箓" for f in result["talisman_list"])

    def test_species_catalog_classifies_talismans(self):
        """符种细分：每枚符箓应被归入符种家族，并产出家族分布。"""
        result = FuGenerator("搜索资料并分析后生成报告").generate()
        catalog = result["species_catalog"]
        assert all("species" in fu and "manga_ref" in fu for fu in result["talisman_list"])
        assert catalog["breakdown"]
        assert set(catalog["active_families"]).issubset(set(catalog["catalog"].keys()))
        assert "封印型" in catalog["reserved_families"]

    def test_detect_creation_dimension(self):
        """生成关键词应产生创作箓"""
        gen = FuGenerator("生成一份报告")
        result = gen.generate()
        assert any(f["type"] == "创作箓" for f in result["talisman_list"])

    def test_curse_high_detection(self):
        """高危词应触发high禁咒"""
        gen = FuGenerator("删除生产环境数据")
        result = gen.generate()
        assert result["curse_level"] == "high"

    def test_curse_medium_detection(self):
        """中危词应触发medium禁咒"""
        gen = FuGenerator("发布新版本")
        result = gen.generate()
        assert result["curse_level"] == "medium"

    def test_topology_order(self):
        """拓扑序应符合预期"""
        gen = FuGenerator("搜索信息然后写报告")
        result = gen.generate()
        topo = result["topology"]
        if len(topo) >= 2:
            assert topo.index("retrieval-v5.0") < topo.index("creation-v5.0")

    def test_empty_task_defaults_to_analysis(self):
        """无匹配维度时应默认分析箓"""
        gen = FuGenerator("xyzabc")
        result = gen.generate()
        assert len(result["talisman_list"]) >= 1
        assert result["talisman_list"][0]["type"] == "分析箓"

    def test_structured_task_spec_is_supported(self):
        """结构化任务规格应产出编排摘要和风险对齐信息"""
        spec = {
            "task": {"description": "搜索资料并分析后写报告"},
            "talisman_contract": {"preferred_types": ["retrieval", "analysis"]},
            "risk_contract": {"max_curse_level": "medium"},
            "execution_contract": {"orchestration_mode": "balanced-array", "sla_target": 60},
        }
        gen = FuGenerator(spec)
        result = gen.generate()
        assert result["orchestration_mode"] == "balanced-array"
        assert result["ritual_summary"]["risk_budget"] == "medium"
        assert "talisman_contract" in result["ritual_summary"]["contracts_present"]

    def test_quick_cast_mode_limits_talisman_count(self):
        """quick-cast 模式应压缩符箓数量"""
        spec = {
            "task": {"description": "搜索资料、分析内容、对比方案并生成报告"},
            "execution_contract": {"orchestration_mode": "quick-cast"},
        }
        gen = FuGenerator(spec)
        result = gen.generate()
        assert result["orchestration_mode"] == "quick-cast"
        assert result["dimension_count"] <= 2

    def test_blocked_talismans_are_removed(self):
        """契约中显式屏蔽的符箓不应出现在结果中"""
        spec = {
            "task": {"description": "搜索资料并生成报告"},
            "talisman_contract": {"blocked_types": ["creation"]},
            "execution_contract": {"orchestration_mode": "balanced-array"},
        }
        gen = FuGenerator(spec)
        result = gen.generate()
        assert all(fu["dimension"] != "creation" for fu in result["talisman_list"])

    def test_yan_chu_fa_sui_speak_one_sentence(self):
        """言出法随：一句话直出符阵，附咒言与范式标记。"""
        result = fu_generator.speak("搜索竞品资料并分析后生成报告")
        assert result["incantation"] == "搜索竞品资料并分析后生成报告"
        assert "言出法随" in result["paradigm"]
        assert result["dimension_count"] >= 1
        assert len(result["topology"]) >= 1

    def test_yan_chu_fa_sui_respects_mode(self):
        """言出法随可指定编排模式。"""
        result = fu_generator.speak("搜索、分析、对比、汇总四步走", mode="quick-cast")
        assert result["orchestration_mode"] == "quick-cast"
        assert result["dimension_count"] <= 2

    def test_yan_chu_fa_sui_rejects_empty(self):
        """空咒言应被拒绝。"""
        with pytest.raises(ValueError):
            fu_generator.speak("   ")


# ---------------------------------------------------------------------------
# 9. 八卦阵 (ecosystem-hub)
# ---------------------------------------------------------------------------

class TestEcosystemHub:
    """生态协调器测试"""

    def test_calc_stats_empty(self):
        """空记录应返回默认值"""
        stats = calc_stats([])
        assert stats["success_rate"] == 0
        assert stats["quality"] == 85
        assert stats["human_intervention"] == 0

    def test_calc_stats_with_data(self):
        """有数据时应计算正确均值"""
        records = [
            {"success": True, "quality_score": 90, "error_count": 0, "human_intervention": 0},
            {"success": False, "quality_score": 70, "error_count": 2, "human_intervention": 1},
        ]
        stats = calc_stats(records)
        assert stats["success_rate"] == 50.0
        assert stats["quality"] == 80.0
        assert stats["errors"] == 1.0
        assert stats["human_intervention"] == 0.5

    def test_coordinate_output_structure(self):
        """协调输出应含关键字段"""
        import tempfile
        import os
        fallback_cwd = Path(__file__).parent.parent
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                report = coordinate(skills_dir="/dev/null")
                assert "ecosystem_level" in report
                assert "average_quality" in report
                assert "skill_states" in report
                assert "weakest_skills" in report
                assert "optimization_queue" in report
                assert "governance_summary" in report
                assert report["coordinator"] == "bagua-zhen"
                assert report["control_plane_status"]["role"] == "coordinator"
                assert report["control_plane_status"]["phase"] in ["ecosystem-report", "ecosystem-coordination"]
                assert report["control_plane_status"]["writes_applied"] is False
            finally:
                os.chdir(fallback_cwd)

    def test_load_metrics_skips_invalid_json(self, tmp_path):
        """损坏的metrics行应被跳过而不是使协调器失败"""
        import os
        fallback_cwd = Path(__file__).parent.parent
        os.chdir(tmp_path)
        try:
            runtime_dir = tmp_path / "runtime_data"
            runtime_dir.mkdir()
            metrics_file = runtime_dir / "qiti-yuanliu_metrics.jsonl"
            metrics_file.write_text('{"success": true, "quality_score": 90}\n{broken\n', encoding="utf-8")
            records = coordinator.load_metrics("qiti-yuanliu")
            assert len(records) == 1
            assert records[0]["quality_score"] == 90
        finally:
            os.chdir(fallback_cwd)

    def test_linkage_protocol_uses_current_interpreter(self, tmp_path, monkeypatch):
        """联动执行协议应使用当前解释器运行 skill 脚本。"""
        scripts_dir = tmp_path / "demo-skill" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "demo.py").write_text("print('ok')\n", encoding="utf-8")
        protocol = LinkageProtocol(str(tmp_path))
        calls = {}

        class FakeResult:
            returncode = 0
            stdout = "ok\n"
            stderr = ""

        def fake_run(cmd, capture_output=True, text=True, timeout=30, cwd=None):
            calls["cmd"] = cmd
            calls["cwd"] = cwd
            return FakeResult()

        monkeypatch.setattr(linkage_protocol.subprocess, "run", fake_run)
        result = protocol._execute_skill("demo-skill", "input.json")
        assert result["success"] is True
        assert calls["cmd"][0] == sys.executable
        assert calls["cmd"][1].endswith("demo.py")
        assert calls["cwd"] == str(scripts_dir)

    def test_dynamic_synergy_overrides_static_mutex(self):
        """动态协同证据应覆盖静态互斥默认值，避免双重判定冲突"""
        dynamic = {
            "qiti-yuanliu__fenghou-qimen": {
                "pair": ["qiti-yuanliu", "fenghou-qimen"],
                "type": "synergy",
                "reason": "共现时质量更高",
                "stats": {"cooccurrence": 5},
            }
        }
        mutex_pairs, synergy_pairs = coordinator._merge_relationships(dynamic)
        assert tuple(sorted(("qiti-yuanliu", "fenghou-qimen"))) not in {
            tuple(sorted(pair)) for pair in mutex_pairs
        }
        assert tuple(sorted(("qiti-yuanliu", "fenghou-qimen"))) in {
            tuple(sorted(pair)) for pair in synergy_pairs
        }

    def test_dynamic_relationship_requires_solo_baseline_for_both_skills(self, tmp_path, monkeypatch):
        """若某一方没有足够 solo 基线，八卦阵不应学习出伪协同关系。"""
        runtime_dir = tmp_path / "runtime_data"
        runtime_dir.mkdir()
        monkeypatch.setenv("UNDER_ONE_RUNTIME_DIR", str(runtime_dir))

        def write_metrics(skill_name, hours, quality):
            records = [
                {
                    "timestamp": f"2026-05-14T{hour:02d}:00:00",
                    "success": True,
                    "quality_score": quality,
                    "error_count": 0,
                }
                for hour in hours
            ]
            (runtime_dir / f"{skill_name}_metrics.jsonl").write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n",
                encoding="utf-8",
            )

        write_metrics("qiti-yuanliu", [1, 2, 10, 11], 90)
        write_metrics("tongtian-lu", [10, 11], 95)
        relationships = coordinator._load_dynamic_relationships(min_cooccurrence=2)
        assert "qiti-yuanliu__tongtian-lu" not in relationships

    def test_coordinate_builds_optimization_queue_for_weak_skills(self, tmp_path):
        """生态报告应把最弱 skill 排到优化队列前列。"""
        import os

        fallback_cwd = Path(__file__).parent.parent
        os.chdir(tmp_path)
        try:
            runtime_dir = tmp_path / "runtime_data"
            runtime_dir.mkdir()
            (runtime_dir / "liuku-xianzei_metrics.jsonl").write_text(
                "\n".join(
                    json.dumps(
                        {
                            "success": True,
                            "quality_score": 68,
                            "error_count": 1,
                            "human_intervention": 0.5,
                            "output_completeness": 72,
                            "consistency_score": 70,
                        }
                    )
                    for _ in range(12)
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime_dir / "qiti-yuanliu_metrics.jsonl").write_text(
                "\n".join(
                    json.dumps(
                        {
                            "success": True,
                            "quality_score": 92,
                            "error_count": 0,
                            "human_intervention": 0,
                            "output_completeness": 96,
                            "consistency_score": 94,
                        }
                    )
                    for _ in range(12)
                )
                + "\n",
                encoding="utf-8",
            )

            report = coordinate(skills_dir="/dev/null")
            assert report["weakest_skills"][0]["skill"] == "liuku-xianzei"
            assert report["optimization_queue"][0]["skill"] == "liuku-xianzei"
            assert report["governance_summary"]["queued_actions"] >= 1
        finally:
            os.chdir(fallback_cwd)


# ---------------------------------------------------------------------------
# 10. 修身炉 (evolution-engine)
# ---------------------------------------------------------------------------

class TestEvolutionEngine:
    """自进化引擎测试"""

    def test_qisource_collect_and_flush(self, tmp_path):
        """QiSource应正确收集和写入数据"""
        qs = QiSourceV7(str(tmp_path))
        qs.collect({"skill_name": "test", "success": True, "quality_score": 90})
        qs._flush()
        file_path = tmp_path / "test_metrics.jsonl"
        assert file_path.exists()
        with open(file_path) as f:
            data = json.loads(f.readline())
        assert data["skill_name"] == "test"
        assert data["v"] == "7.0"

    def test_qisource_load_history_skips_invalid_json(self, tmp_path):
        """损坏的历史metrics行应被跳过而不是使读取失败"""
        metrics_path = tmp_path / "test_metrics.jsonl"
        metrics_path.write_text('{"skill_name":"test","success":true,"quality_score":90}\n{broken\n', encoding="utf-8")
        qs = QiSourceV7(str(tmp_path))
        records = qs.load_history("test")
        assert len(records) == 1
        assert records[0]["quality_score"] == 90

    def test_refiner_no_data(self):
        """无数据时应返回no_data状态"""
        refiner = RefinerV7()
        result = refiner.analyze("test", [])
        assert result["status"] == "no_data"

    def test_refiner_detects_low_success_rate(self):
        """低成功率应触发extension进化"""
        refiner = RefinerV7()
        records = [{"success": False, "error_count": 2, "human_intervention": 0, "quality_score": 50} for _ in range(20)]
        result = refiner.analyze("test", records)
        assert result["evolution_type"] in ["extension", "refactor"]
        assert result["priority"] in ["high", "critical"]

    def test_refiner_stable_skill(self, tmp_path):
        """稳定skill应无需进化"""
        import os
        os.chdir(tmp_path)
        refiner = RefinerV7()
        records = [{"success": True, "error_count": 0, "human_intervention": 0, "quality_score": 95} for _ in range(20)]
        result = refiner.analyze("test", records)
        assert result["evolution_type"] == "none"

    def test_refiner_adaptive_threshold(self, tmp_path):
        """高稳定skill应放宽阈值"""
        import os
        os.chdir(tmp_path)
        refiner = RefinerV7()
        records = [{"success": True, "error_count": 0, "human_intervention": 0, "quality_score": 97} for _ in range(20)]
        refiner.analyze("stable_skill", records)
        threshold = refiner.get_threshold("stable_skill", "success_rate_warning")
        assert threshold == 0.75

    def test_refiner_thresholds_are_clamped(self, tmp_path):
        """自适应阈值应受边界保护，避免越调越偏"""
        import os
        os.chdir(tmp_path)
        refiner = RefinerV7(adaptive_bounds={"success_rate_warning": (0.72, 0.82)})
        refiner.update_adaptive("test", "success_rate_warning", 0.95, "test clamp")
        threshold = refiner.get_threshold("test", "success_rate_warning")
        assert threshold == 0.82

    def test_refiner_ignores_corrupt_adaptive_file(self, tmp_path):
        """损坏的 adaptive_thresholds.json 不应导致初始化失败"""
        import os
        os.chdir(tmp_path)
        (tmp_path / "adaptive_thresholds.json").write_text("{broken", encoding="utf-8")
        refiner = RefinerV7()
        assert refiner.adaptive == {}
        assert refiner.get_threshold("test", "success_rate_warning") == 0.80

    def test_refiner_detects_degradation(self, tmp_path):
        """连续退化应被检测"""
        import os
        os.chdir(tmp_path)
        refiner = RefinerV7()
        records = [{"success": True, "error_count": 0, "human_intervention": 0, "quality_score": 100 - i*5} for i in range(10)]
        result = refiner.analyze("test", records)
        assert result["consecutive_degradation"] >= 4

    def test_refiner_flags_incomplete_output_with_high_quality(self, tmp_path):
        """高质量但低完整度应被识别为输出不完整，而不是误判为稳定。"""
        import os
        os.chdir(tmp_path)
        refiner = RefinerV7()
        records = [
            {
                "success": True,
                "error_count": 0,
                "human_intervention": 0,
                "quality_score": 92,
                "output_completeness": 68,
                "consistency_score": 90,
            }
            for _ in range(12)
        ]
        result = refiner.analyze("test", records)
        assert result["evolution_type"] == "extension"
        assert result["priority"] == "critical"
        assert result["bottleneck_type"] == "incomplete_output"
        assert result["avg_output_completeness"] == 68.0
        assert result["signal_summary"]["high_quality_low_completeness"] is True

    def test_refiner_flags_low_consistency_even_when_successful(self, tmp_path):
        """成功率高但一致性差时应触发进化，而不是继续放行。"""
        import os
        os.chdir(tmp_path)
        refiner = RefinerV7()
        records = [
            {
                "success": True,
                "error_count": 0,
                "human_intervention": 0,
                "quality_score": 88,
                "output_completeness": 92,
                "consistency_score": 60,
            }
            for _ in range(12)
        ]
        result = refiner.analyze("test", records)
        assert result["evolution_type"] == "refactor"
        assert result["priority"] == "critical"
        assert result["bottleneck_type"] == "inconsistent_output"
        assert result["avg_consistency_score"] == 60.0
        assert result["signal_summary"]["consistency_drift"] is True

    def test_rollback_list_versions(self, tmp_path):
        """Rollback应能列出备份版本"""
        import shutil
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        backup_dir = tmp_path / "skill_backups_v7"
        backup_dir.mkdir()
        skill_path = skills_dir / "test"
        skill_path.mkdir()
        (skill_path / "SKILL.md").write_text("test")
        ts = "20250505_120000"
        backup_path = backup_dir / f"test_{ts}"
        shutil.copytree(skill_path, backup_path)

        rb = RollbackV7(str(skills_dir))
        rb.backup_dir = backup_dir
        versions = rb.list_versions("test")
        assert len(versions) == 1
        assert versions[0]["version"] == ts

    def test_core_validation_pass(self, tmp_path):
        """有效skill应通过校验"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_path = skills_dir / "valid"
        skill_path.mkdir()
        (skill_path / "SKILL.md").write_text("---\nmetadata:\n  version: v1.0.0\n---\n")
        scripts = skill_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("print('ok')")

        core = XiuShenLuCoreV7(str(skills_dir))
        # 手动确保 backup_dir 存在
        core.transformer.backup_dir.mkdir(exist_ok=True)
        result = core._validate("valid")
        assert result["passed"] is True

    def test_core_validation_fail_syntax(self, tmp_path):
        """语法错误应导致校验失败"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_path = skills_dir / "invalid"
        skill_path.mkdir()
        (skill_path / "SKILL.md").write_text("test")
        scripts = skill_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("def bad(:\n")

        core = XiuShenLuCoreV7(str(skills_dir))
        core.transformer.backup_dir.mkdir(exist_ok=True)
        result = core._validate("invalid")
        assert result["passed"] is False

    def test_graft_capability_seed_for_new_capability(self, tmp_path):
        """赋能：为不具备某能力的目标 skill 产出新能力萌芽蓝图（read-only）。"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        sp = skills_dir / "alpha"
        sp.mkdir()
        (sp / "SKILL.md").write_text(
            "---\nmetadata:\n  name: alpha\n  tags: ['search', 'parse']\n---\n",
            encoding="utf-8",
        )
        core = XiuShenLuCoreV7(str(skills_dir))
        res = core.graft_capability("alpha", "vision", source_skill="beta")
        assert res["status"] == "seed_ready"
        assert res["seed"]["capability"] == "vision"
        assert res["seed"]["graft_from"] == "beta"
        assert res["applied"] is False
        assert "神机百炼" in res["lineage"]

    def test_graft_capability_detects_existing_and_missing(self, tmp_path):
        """赋能：已具备的能力不重复赋予；目标不存在应报告。"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        sp = skills_dir / "alpha"
        sp.mkdir()
        (sp / "SKILL.md").write_text(
            "---\nmetadata:\n  tags: ['search', 'vision']\n---\n", encoding="utf-8"
        )
        core = XiuShenLuCoreV7(str(skills_dir))
        assert core.graft_capability("alpha", "vision")["status"] == "already_present"
        assert core.graft_capability("ghost", "vision")["status"] == "target_not_found"

    def test_run_cycle_defaults_to_plan_only(self, tmp_path):
        """默认进化周期应只生成计划，不直接改写skill"""
        import os
        fallback_cwd = Path(__file__).parent.parent
        os.chdir(tmp_path)
        try:
            skills_dir = tmp_path / "skills"
            skills_dir.mkdir()
            skill_path = skills_dir / "test-skill"
            skill_path.mkdir()
            (skill_path / "SKILL.md").write_text("---\nmetadata:\n  version: v1.0.0\n---\n", encoding="utf-8")
            scripts = skill_path / "scripts"
            scripts.mkdir()
            script_path = scripts / "run.py"
            original = "threshold = 1.0\n"
            script_path.write_text(original, encoding="utf-8")

            runtime_dir = tmp_path / "runtime_data"
            runtime_dir.mkdir()
            metrics_file = runtime_dir / "test-skill_metrics.jsonl"
            lines = [
                json.dumps({"success": False, "error_count": 2, "human_intervention": 0, "quality_score": 50})
                for _ in range(20)
            ]
            metrics_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            core = XiuShenLuCoreV7(str(skills_dir), data_dir=str(runtime_dir), apply_changes=False)
            result = core.run_evolution_cycle("test-skill")
            assert result["results"][0]["status"] == "planned"
            assert result["results"][0]["analysis"]["avg_consistency_score"] == 50.0
            assert result["results"][0]["analysis"]["avg_output_completeness"] == 50.0
            assert result["consistency_score"] == 50.0
            assert result["output_completeness"] == 100.0
            assert result["human_intervention"] == 1.0
            assert result["execution_policy"]["mode"] == "plan-only"
            assert result["execution_policy"]["manual_gate_required"] is True
            assert result["control_plane_status"]["role"] == "evolver"
            assert result["control_plane_status"]["phase"] == "plan-only"
            assert result["control_plane_status"]["writes_applied"] is False
            assert result["evolution_backlog"][0]["skill"] == "test-skill"
            assert result["evolution_backlog"][0]["requires_approval"] is True
            assert "test-skill" in result["pattern_summary"]["critical_skills"]
            assert script_path.read_text(encoding="utf-8") == original
            assert not (tmp_path / "adaptive_thresholds.json").exists()
        finally:
            os.chdir(fallback_cwd)

    def test_run_cycle_uses_bootstrap_plan_when_runtime_data_is_sparse(self, tmp_path):
        """冷启动 skill 不应只返回数据不足，而应给出 bootstrap 基线计划。"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_path = skills_dir / "cold-skill"
        skill_path.mkdir()
        (skill_path / "SKILL.md").write_text("---\nmetadata:\n  version: v1.0.0\n---\n", encoding="utf-8")
        (skill_path / "_skillhub_meta.json").write_text('{"id":"cold-skill"}', encoding="utf-8")
        scripts = skill_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("print('ok')\n", encoding="utf-8")

        runtime_dir = tmp_path / "runtime_data"
        runtime_dir.mkdir()

        core = XiuShenLuCoreV7(str(skills_dir), data_dir=str(runtime_dir), apply_changes=False)
        result = core.run_evolution_cycle("cold-skill")
        item = result["results"][0]
        assert item["status"] == "planned"
        assert item["planned_evolution_type"] == "bootstrap"
        assert item["analysis"]["bootstrap_mode"] is True
        assert item["analysis"]["bottleneck_type"] == "cold_start"
        assert item["analysis"]["bootstrap_signals"]["record_count"] == 0
        backlog_item = result["evolution_backlog"][0]
        assert backlog_item["evolution_type"] == "bootstrap"
        assert any("冷启动阶段" in blocker for blocker in backlog_item["blockers"])
        assert result["execution_policy"]["next_targets"][0] == "cold-skill"

    def test_bootstrap_analysis_counts_standalone_tests_and_blends_sparse_runtime(self, tmp_path):
        """冷启动分析应识别 skill/tests 中的独立测试，并对稀疏样本做保守混合。"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_path = skills_dir / "bootstrap-skill"
        skill_path.mkdir()
        (skill_path / "SKILL.md").write_text("---\nmetadata:\n  version: v1.0.0\n---\n", encoding="utf-8")
        (skill_path / "_skillhub_meta.json").write_text('{"id":"bootstrap-skill"}', encoding="utf-8")
        scripts = skill_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("print('ok')\n", encoding="utf-8")
        tests_dir = skill_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "standalone_smoke.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")

        runtime_dir = tmp_path / "runtime_data"
        runtime_dir.mkdir()
        metrics_file = runtime_dir / "bootstrap-skill_metrics.jsonl"
        metrics_file.write_text(
            "\n".join(
                json.dumps(
                    {
                        "success": True,
                        "error_count": 0,
                        "human_intervention": 0,
                        "quality_score": 42,
                        "output_completeness": 30,
                        "consistency_score": 35,
                    }
                )
                for _ in range(2)
            )
            + "\n",
            encoding="utf-8",
        )

        core = XiuShenLuCoreV7(str(skills_dir), data_dir=str(runtime_dir), apply_changes=False)
        result = core.run_evolution_cycle("bootstrap-skill")
        analysis = result["results"][0]["analysis"]
        assert analysis["bootstrap_mode"] is True
        assert analysis["bootstrap_signals"]["test_count"] == 1
        assert analysis["bootstrap_signals"]["observed_weight"] > 0
        assert analysis["avg_consistency_score"] > 35.0
        assert analysis["avg_output_completeness"] > 30.0

    def test_bootstrap_analysis_uses_known_skill_profile_when_available(self, tmp_path):
        """已知 skill 的冷启动分析应使用画像基线，而不只依赖结构猜测。"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_path = skills_dir / "qiti-yuanliu"
        skill_path.mkdir()
        (skill_path / "SKILL.md").write_text("---\nmetadata:\n  version: v0.1.0\n---\n", encoding="utf-8")
        (skill_path / "_skillhub_meta.json").write_text('{"id":"qiti-yuanliu"}', encoding="utf-8")
        scripts = skill_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("print('ok')\n", encoding="utf-8")

        runtime_dir = tmp_path / "runtime_data"
        runtime_dir.mkdir()
        metrics_file = runtime_dir / "qiti-yuanliu_metrics.jsonl"
        metrics_file.write_text(
            "\n".join(
                json.dumps(
                    {
                        "success": True,
                        "error_count": 0,
                        "human_intervention": 0,
                        "quality_score": 60,
                        "output_completeness": 55,
                        "consistency_score": 50,
                    }
                )
                for _ in range(2)
            )
            + "\n",
            encoding="utf-8",
        )

        core = XiuShenLuCoreV7(str(skills_dir), data_dir=str(runtime_dir), apply_changes=False)
        result = core.run_evolution_cycle("qiti-yuanliu")
        analysis = result["results"][0]["analysis"]
        assert analysis["bootstrap_mode"] is True
        assert analysis["bootstrap_signals"]["profile_applied"] is True
        assert analysis["bootstrap_signals"]["baseline_source"] == "profiled"
        assert analysis["bootstrap_signals"]["recommended_min_records"] >= 10
        assert analysis["avg_quality"] > 60.0
        assert analysis["avg_consistency_score"] > 50.0

    def test_bootstrap_profile_reads_custom_meta_for_third_party_skill(self, tmp_path):
        """第三方 skill 只要在 _skillhub_meta.json 中声明 bootstrap_profile，就应被修身炉识别。"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_path = skills_dir / "custom-skill"
        skill_path.mkdir()
        (skill_path / "SKILL.md").write_text("---\nmetadata:\n  version: v0.1.0\n---\n", encoding="utf-8")
        (skill_path / "_skillhub_meta.json").write_text(
            json.dumps(
                {
                    "id": "custom-skill",
                    "bootstrap_profile": {
                        "avg_quality": 91,
                        "avg_completeness": 93,
                        "avg_consistency": 90,
                        "avg_human": 0.03,
                        "success_rate": 0.95,
                        "avg_duration": 640,
                        "recommended_min_records": 14,
                        "degradation_window": 4,
                    },
                }
            ),
            encoding="utf-8",
        )
        scripts = skill_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("print('ok')\n", encoding="utf-8")

        profile = bootstrap_profiles.get_bootstrap_profile("custom-skill", skills_root=skills_dir)
        assert profile is not None
        assert profile["avg_quality"] == 91
        assert profile["recommended_min_records"] == 14

        runtime_dir = tmp_path / "runtime_data"
        runtime_dir.mkdir()
        core = XiuShenLuCoreV7(str(skills_dir), data_dir=str(runtime_dir), apply_changes=False)
        result = core.run_evolution_cycle("custom-skill")
        analysis = result["results"][0]["analysis"]
        assert analysis["bootstrap_signals"]["profile_applied"] is True
        assert analysis["bootstrap_signals"]["recommended_min_records"] == 14
        assert analysis["avg_quality"] >= 80.0

    def test_bootstrap_profile_generator_is_deterministic(self):
        """播种画像应可重复生成，便于独立安装后的稳定复现。"""
        records_a = bootstrap_profiles.generate_profile_records("qiti-yuanliu", n=4, seed=1234)
        records_b = bootstrap_profiles.generate_profile_records("qiti-yuanliu", n=4, seed=1234)
        assert records_a == records_b
        assert len(records_a) == 4
        assert all(item["skill_name"] == "qiti-yuanliu" for item in records_a)
        assert all("output_completeness" in item for item in records_a)

    def test_run_cycle_isolates_target_errors(self, tmp_path, monkeypatch):
        """单个skill分析失败不应拖垮整个进化周期"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        for name in ("boom", "steady"):
            skill_path = skills_dir / name
            skill_path.mkdir()
            (skill_path / "SKILL.md").write_text("---\nmetadata:\n  version: v1.0.0\n---\n", encoding="utf-8")
            scripts = skill_path / "scripts"
            scripts.mkdir()
            (scripts / "run.py").write_text("print('ok')\n", encoding="utf-8")

        runtime_dir = tmp_path / "runtime_data"
        runtime_dir.mkdir()
        for name in ("boom", "steady"):
            metrics_file = runtime_dir / f"{name}_metrics.jsonl"
            lines = [
                json.dumps({"success": True, "error_count": 0, "human_intervention": 0, "quality_score": 90})
                for _ in range(12)
            ]
            metrics_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        core = XiuShenLuCoreV7(str(skills_dir), data_dir=str(runtime_dir), apply_changes=False)

        def fake_analyze(skill_name, records):
            if skill_name == "boom":
                raise RuntimeError("simulated analyze failure")
            return {
                "health_score": 95,
                "evolution_type": "none",
                "bottleneck_type": "stable",
            }

        monkeypatch.setattr(core.refiner, "analyze", fake_analyze)
        result = core.run_evolution_cycle()
        statuses = {item["skill"]: item["status"] for item in result["results"]}
        assert statuses["boom"] == "error"
        assert statuses["steady"] == "no_action"

    def test_verifier_uses_current_interpreter(self, tmp_path, monkeypatch):
        """修身炉验证器应使用当前解释器运行进化后的脚本。"""
        script_path = tmp_path / "analyzer.py"
        script_path.write_text("print('ok')\n", encoding="utf-8")
        calls = {}

        class FakeResult:
            returncode = 0
            stdout = "ok\n"
            stderr = ""

        def fake_run(cmd, capture_output=True, text=True, timeout=30, cwd=None):
            calls["cmd"] = cmd
            calls["cwd"] = cwd
            return FakeResult()

        monkeypatch.setattr(xiushenlu_verifier.subprocess, "run", fake_run)
        result = xiushenlu_verifier.run_evolved_skill(script_path)
        assert result.stdout == "ok\n"
        assert calls["cmd"][0] == sys.executable
        assert calls["cmd"][1] == str(script_path)
        assert calls["cwd"] == str(script_path.parent)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
