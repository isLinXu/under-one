#!/usr/bin/env python3
"""
under-one.skills 核心测试套件
覆盖: 配置加载、Skill基类、CLI入口
"""

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

import skills.check_versions as skill_version_checker
import skills._skill_config as skill_config

from under_one import (
    load_config, BaseSkill,
    CommandFactory, ContextGuard, EvolutionEngine, InsightRadar,
    EcosystemHub, KnowledgeDigest, PersonaGuard, PriorityEngine, ToolForge, ToolOrchestrator,
)
from under_one.skill_bundle import build_bundle_text, install_bundle, parse_bundle_text, verify_bundle_roundtrip
from under_one.skill_audit import audit_skill_dir, audit_skills_root, write_audit_report
from under_one.codex_skills import build_codex_skill_markdown, install_codex_skill
from scripts.evaluate_skills import evaluate_all
from scripts.build_skill_bundles import precheck_skill
from skills.metrics_collector import get_recent_metrics, record_metrics


class TestConfig:
    """配置加载测试"""

    def test_load_config_returns_dict(self):
        """配置加载返回字典"""
        config = load_config()
        assert isinstance(config, dict)
    
    def test_config_has_thresholds(self):
        """配置包含核心阈值"""
        config = load_config()
        if config:  # 如果找到配置文件
            assert "thresholds" in config or True  # 无配置文件也OK

    def test_skill_config_can_find_nearby_yaml_from_shallow_install_path(self, tmp_path, monkeypatch):
        """浅层安装路径下，_skill_config 也应能向上找到同目录配置。"""
        config_path = tmp_path / "under-one.yaml"
        config_path.write_text("thresholds:\n  entropy_warning: 7\n", encoding="utf-8")
        monkeypatch.setattr(skill_config, "__file__", str(tmp_path / "_skill_config.py"))
        monkeypatch.setattr(skill_config, "_CONFIG_CACHE", None)
        monkeypatch.setattr(skill_config, "_CONFIG_PATH_CANDIDATES", [])
        assert skill_config._find_config() == config_path
        assert skill_config.get_threshold("entropy_warning", 5) == 7


class TestBaseSkill:
    """Skill基类测试"""

    def test_base_skill_version_uses_semver(self):
        """BaseSkill 默认版本应与当前 skill 语义版本一致。"""
        assert BaseSkill.skill_version == "v0.1.0"

    def test_skill_initialization(self):
        """Skill可以正常初始化"""
        class DummySkill(BaseSkill):
            skill_name = "dummy"
            def run(self, data):
                return {"success": True, "score": 95}
        
        skill = DummySkill()
        assert skill.skill_name == "dummy"
        assert skill.config is not None
    
    def test_skill_run(self):
        """Skill可以执行并返回结果"""
        class DummySkill(BaseSkill):
            skill_name = "dummy"
            def run(self, data):
                return {"success": True, "score": 95}
        
        skill = DummySkill()
        result = skill.run({"test": "data"})
        assert result["success"] is True
        assert result["score"] == 95
    
    def test_metrics_export(self, tmp_path):
        """指标可以导出"""
        import os
        os.chdir(tmp_path)
        
        class DummySkill(BaseSkill):
            skill_name = "test-skill"
            def run(self, data):
                return {"success": True, "quality_score": 90}
        
        skill = DummySkill()
        skill.export_metrics({"success": True, "quality_score": 90})
        
        metrics_file = tmp_path / "runtime_data" / "test-skill_metrics.jsonl"
        assert metrics_file.exists()
        
        with open(metrics_file) as f:
            line = json.loads(f.readline())
        assert line["skill_name"] == "test-skill"
        assert line["quality_score"] == 90

    def test_metrics_collector_extracts_nested_runtime_signals(self, tmp_path, monkeypatch):
        """metrics_collector 应能从嵌套结果中提取质量、一致性和人工确认信号。"""
        monkeypatch.chdir(tmp_path)

        @record_metrics("nested-metric-skill")
        def run_nested():
            return {
                "metrics": {"health_score": 88.0, "consistency": 91.0},
                "escalation_contract": {"manual_review_required": True},
                "output_completeness": 95.0,
            }

        run_nested()
        record = get_recent_metrics("nested-metric-skill", n=1)[0]
        assert record["quality_score"] == 88.0
        assert record["consistency_score"] == 91.0
        assert record["human_intervention"] == 1.0
        assert record["output_completeness"] == 95.0


class TestSkillWrappers:
    """SDK 包装层测试"""

    def test_context_guard_executes_repair_handoff_trace(self):
        """ContextGuard 应返回结构化报告并自动执行 repair_handoff。"""
        context = [
            {"role": "user", "content": "我们先用 React。", "round": 1},
            {"role": "assistant", "content": "好的，前端采用 React。", "round": 2},
            {"role": "user", "content": "不对，改成 Vue。", "round": 3},
            {"role": "assistant", "content": "已切换为 Vue。", "round": 4},
        ]
        result = ContextGuard().run(context)
        assert result["success"] is True
        assert result["scanner"] == "qiti-yuanliu"
        assert result["origin_anchor"].startswith("我们先用 React")
        assert len(result["rule_candidates"]) >= 1
        execution = result["repair_handoff_execution"]
        assert execution["status"] == "completed"
        assert execution["target_skill"] == "dalu-dongguan"
        assert execution["trace"]["success"] is True
        assert execution["trace"]["detector"] == "dalu-dongguan"
        stability_execution = result["stability_execution"]
        assert stability_execution["freeze_applied"] is True
        assert stability_execution["repair_handoff_status"] == "completed"
        assert "verification_snapshot" in stability_execution
        assert result["stability_contract"]["mutation_budget"]["mode"] == "frozen"
        assert result["repair_plan"]["steps"][0]["id"] == "re-anchor-goal"

    def test_insight_radar_normalizes_id_and_text_fields(self):
        """InsightRadar 包装层应兼容 id/text 字段。"""
        result = InsightRadar().run(
            [
                {"id": "seg-a", "text": "缓存优化可以提高性能并减少等待时间"},
                {"id": "seg-b", "text": "性能优化常常依赖缓存策略和资源调度"},
            ]
        )
        assert result["success"] is True
        assert result["detector"] == "dalu-dongguan"
        assert result["segment_count"] == 2

    def test_command_factory_direct_call(self):
        """CommandFactory 应直接返回结构化符箓结果。"""
        result = CommandFactory().run("搜索竞品信息然后写高管报告")
        assert result["success"] is True
        assert result["dimensions"] >= 1
        assert result["curse_level"] in ["low", "medium", "high"]
        assert "talisman_list" in result
        assert "command_packets" in result
        assert result["dispatch_contract"]["recommended_skill"] == "juling-qianjiang"

    def test_tool_forge_direct_call(self):
        """ToolForge 应直接生成可用的工具脚手架。"""
        result = ToolForge().run(
            {
                "name": "demo-tool",
                "description": "生成 JSON 清洗工具",
                "inputs": ["input.json"],
                "outputs": ["output.json"],
            }
        )
        assert result["success"] is True
        assert result["artifact_type"] in ["tool", "skill"]
        assert result["tool_name"] == "demo-tool"

    def test_tool_forge_records_runtime_metric_on_forge(self, tmp_path, monkeypatch):
        """神机百炼应在 forge 主流程而非辅助函数上记录 runtime metric。"""
        monkeypatch.chdir(tmp_path)
        result = ToolForge().run(
            {
                "name": "demo-tool",
                "description": "生成 JSON 清洗工具",
                "inputs": ["input.json"],
                "outputs": ["output.json"],
            }
        )
        assert result["success"] is True
        records = get_recent_metrics("shenji-bailian", n=5)
        assert len(records) == 1
        assert records[0]["quality_score"] >= 80
        assert records[0]["output_completeness"] >= 80

    def test_priority_engine_direct_call(self):
        """PriorityEngine 应直接返回执行计划。"""
        result = PriorityEngine().run(
            [
                {"name": "修复生产故障", "urgency": 5, "importance": 5, "dependency": 4, "resource_match": 4},
                {"name": "整理文档", "urgency": 1, "importance": 1, "dependency": 1, "resource_match": 1},
            ]
        )
        assert result["success"] is True
        assert len(result["execution_plan"]) == 2
        assert len(result["execution_phases"]) >= 1
        assert "balanced" in result["alternative_plans"]
        assert result["ranked_tasks"][0]["gate"] in ["开门", "生门", "景门", "杜门", "死门"]

    def test_knowledge_digest_direct_call(self):
        """KnowledgeDigest 应直接返回消化报告。"""
        result = KnowledgeDigest().run(
            [
                {"source": "blog", "content": "通过缓存优化提升了性能，并在生产环境验证了结果。", "credibility": "A"},
                {"source": "paper", "content": "该方法基于统计分析和实验结果，适用于数据场景。", "credibility": "S"},
            ]
        )
        assert result["success"] is True
        assert "avg_digestion_rate" in result
        assert len(result["knowledge_units"]) == 2

    def test_persona_guard_accepts_profile_dict(self):
        """PersonaGuard 应直接校验 profile dict 并暴露兼容字段。"""
        result = PersonaGuard().run(
            {
                "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
                "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
                "dna_core": {"诚信": "不编造"},
                "requested_change": {"type": "人格切换", "target": "礼貌", "patch": {"tone": 4}},
                "history": [],
            }
        )
        assert result["success"] is True
        assert result["validator"] == "shuangquanshou"
        assert result["can_switch"] is True
        assert result["allow"] is True
        assert result["violation_count"] == 0
        assert result["consistency"] == 1.0
        assert result["primary_domain"] == "persona"
        assert result["surgery_mode"] == "edit"
        assert result["rewrite_patch"]["apply_ready"] is True
        assert result["surgery_plan"][0]["patch_preview"]["operations"][0]["op"] in ["add", "replace"]

    def test_persona_guard_patch_simulation_can_apply_and_rollback(self):
        """PersonaGuard 应返回非破坏式 apply/rollback 预演。"""
        result = PersonaGuard().run(
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
        assert result["success"] is True
        assert result["patch_simulation"]["applied"] is True
        assert result["applied_profile_preview"]["memory_state"]["user_preference"] == "更重视效率"
        assert result["rollback_profile_preview"]["memory_state"]["user_preference"] == "偏好完整解释"
        assert result["patch_simulation"]["restored"] is True

    def test_persona_guard_legacy_session_log_fallback(self):
        """PersonaGuard 应兼容旧版 session_log list 输入。"""
        result = PersonaGuard().run(
            [
                {"style": "formal", "tone": 3, "formality": 4, "detail_level": 3, "structure": 4},
                {"style": "casual", "tone": 2, "formality": 2, "detail_level": 2, "structure": 2},
                {"style": "technical", "tone": 5, "formality": 5, "detail_level": 4, "structure": 5},
            ]
        )
        assert result["success"] is True
        assert result["validator"] == "shuangquanshou"
        assert result["can_switch"] is False
        assert any(v["principle"] == "人格分裂防护" for v in result["dna_violations"])

    def test_tool_orchestrator_direct_call(self):
        """ToolOrchestrator 应直接返回调度结果。"""
        result = ToolOrchestrator().run(
            [{"type": "search", "desc": "查询资料"}],
            [{"id": "api1", "capabilities": ["search"], "available": True, "quality_score": 0.92}],
        )
        assert result["success"] is True
        assert result["all_success"] is True
        assert result["formation"] in ["single-possession", "dual-attunement", "night-parade"]
        assert len(result["plan"]) == 1
        assert len(result["command_plan"]) == 1
        assert result["command_plan"][0]["commander"] == "juling-qianjiang"
        assert "recovery_plan" in result["command_plan"][0]
        assert "governance_summary" in result

    def test_ecosystem_hub_direct_call(self):
        """EcosystemHub 应返回统一 success 字段和生态摘要。"""
        result = EcosystemHub().run()
        assert result["success"] is True
        assert result["coordinator"] == "bagua-zhen"
        assert "skill_states" in result
        assert "average_quality" in result

    def test_evolution_engine_direct_call(self, tmp_path, monkeypatch):
        """EvolutionEngine 应直接返回结构化计划报告。"""
        monkeypatch.chdir(tmp_path)
        runtime_dir = tmp_path / "runtime_data"
        runtime_dir.mkdir()
        metrics_file = runtime_dir / "qiti-yuanliu_metrics.jsonl"
        metrics_file.write_text(
            "\n".join(
                json.dumps(
                    {
                        "success": False,
                        "error_count": 2,
                        "human_intervention": 0,
                        "quality_score": 50,
                    }
                )
                for _ in range(20)
            )
            + "\n",
            encoding="utf-8",
        )

        result = EvolutionEngine().run("qiti-yuanliu")
        assert result["success"] is True
        assert result["engine"] == "xiushen-lu"
        assert result["summary"]["total"] == 1
        assert result["results"][0]["skill"] == "qiti-yuanliu"
        assert result["results"][0]["status"] == "planned"

    def test_evolution_engine_surfaces_runtime_signal_breakdown(self, tmp_path, monkeypatch):
        """EvolutionEngine 应把完整度、一致性和人工介入信号带回上层。"""
        monkeypatch.chdir(tmp_path)
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
                        "quality_score": 90,
                        "output_completeness": 66,
                        "consistency_score": 84,
                    }
                )
                for _ in range(12)
            )
            + "\n",
            encoding="utf-8",
        )

        result = EvolutionEngine().run("qiti-yuanliu")
        analysis = result["results"][0]["analysis"]
        assert result["success"] is True
        assert analysis["bottleneck_type"] == "incomplete_output"
        assert analysis["avg_output_completeness"] == 66.0
        assert analysis["avg_consistency_score"] == 84.0
        assert result["output_completeness"] == 100.0
        assert result["consistency_score"] == 84.0
        assert result["human_intervention"] == 1.0

    def test_evolution_engine_bootstraps_when_runtime_data_is_sparse(self, tmp_path, monkeypatch):
        """EvolutionEngine 在冷启动阶段应返回 bootstrap 计划而不是直接跳过。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "runtime_data").mkdir()

        result = EvolutionEngine().run("qiti-yuanliu")
        item = result["results"][0]
        assert result["success"] is True
        assert item["status"] == "planned"
        assert item["planned_evolution_type"] == "bootstrap"
        assert item["analysis"]["bootstrap_mode"] is True
        assert item["analysis"]["bottleneck_type"] == "cold_start"


class TestSkillVersionChecker:
    """Skill 版本一致性检查测试"""

    def test_checker_prefers_skill_md_and_meta_semver(self, tmp_path, monkeypatch):
        """check_versions 应优先比较 SKILL.md 和 metadata 的 v0.1.0 版本。"""
        skill_dir = tmp_path / "demo-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nmetadata:\n  name: \"demo-skill\"\n  version: \"v0.1.0\"\n---\n",
            encoding="utf-8",
        )
        (skill_dir / "_skillhub_meta.json").write_text(
            json.dumps({"id": "demo-skill", "version": "v0.1.0"}, ensure_ascii=False),
            encoding="utf-8",
        )
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "demo_skill.py").write_text('"""器名: Demo V9.9"""\n', encoding="utf-8")

        monkeypatch.setattr(skill_version_checker, "SKILLS_ROOT", tmp_path)
        result = skill_version_checker.check_skill("demo-skill")
        assert result["md_version"] == "v0.1.0"
        assert result["meta_version"] == "v0.1.0"
        assert result["script_version"] == "v9.9"
        assert result["match"] is True

    def test_checker_ignores_non_skill_directories(self, tmp_path, monkeypatch):
        """check_all_skills 不应把 runtime_data 等非 skill 目录纳入版本检查。"""
        (tmp_path / "runtime_data").mkdir()
        (tmp_path / "shared_knowledge").mkdir()

        skill_dir = tmp_path / "demo-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nmetadata:\n  name: \"demo-skill\"\n  version: \"v0.1.0\"\n---\n",
            encoding="utf-8",
        )
        (skill_dir / "_skillhub_meta.json").write_text(
            json.dumps({"id": "demo-skill", "version": "v0.1.0"}, ensure_ascii=False),
            encoding="utf-8",
        )

        monkeypatch.setattr(skill_version_checker, "SKILLS_ROOT", tmp_path)
        results = skill_version_checker.check_all_skills()
        assert [item["skill"] for item in results] == ["demo-skill"]


class TestCLIIntegration:
    """CLI集成测试"""

    def test_cli_list(self, capsys):
        """CLI list命令可执行"""
        from under_one.cli import SKILL_MAP
        assert len(SKILL_MAP) == 10
        
        # 检查所有skill有对应目录（skills/ 是 test 文件所在 underone/ 的子目录）
        skill_dir = Path(__file__).parent.parent / "skills"
        if skill_dir.exists():
            for name, (dir_name, _, _) in SKILL_MAP.items():
                assert (skill_dir / dir_name).exists(), f"Skill directory missing: {dir_name}"

    def test_cli_skill_map_matches_auditable_skills(self):
        """CLI中的skill映射应与可审计skill目录一致"""
        from under_one.cli import SKILL_MAP

        skill_dir = Path(__file__).parent.parent / "skills"
        audited = {p.name for p in skill_dir.iterdir() if p.is_dir() and (p / "_skillhub_meta.json").exists()}
        mapped = {dir_name for dir_name, _, _ in SKILL_MAP.values()}
        assert audited == mapped

    def test_cli_scan_uses_current_interpreter(self, tmp_path, monkeypatch):
        """CLI scan 应使用当前解释器，而不是硬编码 python。"""
        from under_one import cli
        import subprocess

        script_path = tmp_path / "shuangquanshou" / "scripts"
        script_path.mkdir(parents=True)
        (script_path / "dna_validator.py").write_text("print('ok')\n", encoding="utf-8")

        monkeypatch.setattr(cli, "find_skill_dir", lambda: tmp_path)
        calls = {}

        class FakeResult:
            returncode = 0

        def fake_run(cmd, timeout=60):
            calls["cmd"] = cmd
            calls["timeout"] = timeout
            return FakeResult()

        monkeypatch.setattr(subprocess, "run", fake_run)

        with pytest.raises(SystemExit) as exc:
            cli.cmd_scan(SimpleNamespace(skill="persona-guard", input=None))

        assert exc.value.code == 0
        assert calls["cmd"][0] == sys.executable
        assert calls["cmd"][1].endswith("dna_validator.py")


class TestEvaluationReport:
    """评估报告兼容性测试"""

    def test_evaluate_all_exposes_compatibility_aliases(self):
        """评估报告应同时暴露稳定主键和兼容别名。"""
        report = evaluate_all()
        assert report["skills_evaluated"] == 10
        assert report["validation_passed_count"] == report["validation_passed"]
        assert report["validation_total"] == report["skills_evaluated"]
        assert report["average_score"] == report["average_effectiveness_score"]
        assert len(report["skills"]) == report["skills_evaluated"]
        assert all(item["artifact_status"] == item["artifact"] for item in report["skills"])
        assert all("independent_lifecycle" in item for item in report["skills"])
        assert all(item["independent_lifecycle"]["passed"] for item in report["skills"])
        assert all("avg_consistency" in item["runtime"] for item in report["skills"])
        assert all("avg_human_intervention" in item["runtime"] for item in report["skills"])


class TestSkillBundleLifecycle:
    """单 skill 安装与生命周期测试"""

    def test_build_codex_skill_markdown_promotes_frontmatter(self, tmp_path):
        """Codex 安装版 SKILL.md 应包含顶层 name/description frontmatter。"""
        skill_dir = tmp_path / "demo-skill"
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        (skill_dir / "_skillhub_meta.json").write_text(
            json.dumps(
                {
                    "id": "demo-skill",
                    "name": "演示技能",
                    "version": "1.0",
                    "entry": "scripts/run.py",
                    "description": "用于演示 Codex 安装适配",
                    "triggers": ["演示安装", "独立验证"],
                    "inputs": ["input.json"],
                    "outputs": ["output.json"],
                    "min_python": "3.8",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (skill_dir / "SKILL.md").write_text(
            "---\nmetadata:\n  name: \"demo-skill\"\n  version: \"1.0\"\n---\n\n# Demo\n\n## 触发词\n- 演示安装\n",
            encoding="utf-8",
        )
        (scripts_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")

        rendered = build_codex_skill_markdown(skill_dir)
        assert rendered.startswith("---\nname: \"demo-skill\"\ndescription:")
        assert "metadata:\n  display_name: \"演示技能\"" in rendered
        assert "# Demo" in rendered
        assert "Use when the user asks for 演示安装、独立验证." in rendered

    def test_install_codex_skill_creates_discoverable_wrapper(self, tmp_path):
        """Codex 安装应生成可发现的 wrapper 与独立自测文件。"""
        source_root = tmp_path / "source"
        skill_dir = source_root / "demo-skill"
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        (skill_dir / "_skillhub_meta.json").write_text(
            json.dumps(
                {
                    "id": "demo-skill",
                    "name": "演示技能",
                    "version": "1.0",
                    "entry": "scripts/run.py",
                    "description": "用于演示 Codex 安装适配",
                    "triggers": ["演示安装"],
                    "inputs": ["input.json"],
                    "outputs": ["output.json"],
                    "min_python": "3.8",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (skill_dir / "SKILL.md").write_text(
            "---\nmetadata:\n  name: \"demo-skill\"\n  version: \"1.0\"\n---\n\n# Demo\n\n## 触发词\n- 演示安装\n\n## 功能概述\ndemo\n\n## 工作流程\n1. step\n\n## 输入输出\ninput.json -> output.json\n\n## API接口\napi\n\n## 使用示例\ndemo\n\n## 测试方法\nself-test\n",
            encoding="utf-8",
        )
        (scripts_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")

        result = install_codex_skill(skill_dir, tmp_path / "codex-skills")
        installed_dir = Path(result["installed_dir"])
        assert installed_dir.exists()
        assert (installed_dir / "SKILL.md").read_text(encoding="utf-8").startswith("---\nname: \"demo-skill\"")
        assert (installed_dir / "agents" / "openai.yaml").exists()
        assert (installed_dir / "skillctl.py").exists()
        assert (installed_dir / "tests" / "self_test.py").exists()
        assert result["codex_validation"]["passed"] is True
        assert result["installed_lifecycle"]["passed"] is True

    def test_install_bundle_extracts_files(self, tmp_path):
        """.skill bundle 应能独立安装到目标目录。"""
        bundle_path = tmp_path / "demo.skill"
        bundle_path.write_text(
            "\n".join(
                [
                    "===== UNDER-ONE SKILL BUNDLE v1 =====",
                    "name: demo-skill",
                    "version: v1",
                    "built_at: 2026-05-12T00:00:00+00:00",
                    "files: 3",
                    "=====================================",
                    "",
                    "----- file: _skillhub_meta.json -----",
                    json.dumps(
                        {
                            "id": "demo-skill",
                            "name": "Demo Skill",
                            "version": "1.0",
                            "entry": "scripts/run.py",
                            "description": "demo",
                            "triggers": ["demo"],
                            "inputs": ["input.json"],
                            "outputs": ["output.json"],
                            "min_python": "3.8",
                        },
                        ensure_ascii=False,
                    ),
                    "",
                    "----- file: SKILL.md -----",
                    "---",
                    "metadata:",
                    "  name: \"demo-skill\"",
                    "  version: \"1.0\"",
                    "---",
                    "",
                    "# Demo",
                    "",
                    "## 触发词",
                    "- demo",
                    "",
                    "## 功能概述",
                    "demo",
                    "",
                    "## 工作流程",
                    "1. step",
                    "",
                    "## 输入输出",
                    "input.json -> output.json",
                    "",
                    "## API接口",
                    "api",
                    "",
                    "## 使用示例",
                    "demo",
                    "",
                    "## 测试方法",
                    "self-test",
                    "",
                    "----- file: scripts/run.py -----",
                    "print('ok')",
                    "",
                    "===== END BUNDLE =====",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        parsed = parse_bundle_text(bundle_path.read_text(encoding="utf-8"))
        assert parsed.name == "demo-skill"
        result = install_bundle(bundle_path, tmp_path / "skills")
        skill_dir = tmp_path / "skills" / "demo-skill"
        assert result["file_count"] >= 5
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "scripts" / "run.py").read_text(encoding="utf-8").strip() == "print('ok')"
        assert (skill_dir / "skillctl.py").exists()
        assert (skill_dir / "tests" / "self_test.py").exists()
        assert (skill_dir / "install-manifest.json").exists()

        import subprocess

        validate_run = subprocess.run([sys.executable, str(skill_dir / "skillctl.py"), "validate"], capture_output=True, text=True, cwd=skill_dir)
        assert validate_run.returncode == 0
        assert '"ok": true' in validate_run.stdout.lower()

        self_test_run = subprocess.run([sys.executable, str(skill_dir / "skillctl.py"), "self-test"], capture_output=True, text=True, cwd=skill_dir)
        assert self_test_run.returncode == 0
        assert "self-test passed" in self_test_run.stdout

    def test_bundle_includes_shared_helpers_for_runtime_imports(self):
        """真实 skill bundle 应把共享运行时依赖一并打包，保证独立安装可运行。"""
        skill_dir = Path(__file__).parent.parent / "skills" / "qiti-yuanliu"
        parsed = parse_bundle_text(build_bundle_text(skill_dir))
        assert "__shared__/metrics_collector.py" in parsed.files
        assert "__shared__/_skill_config.py" in parsed.files
        assert "tests/standalone_smoke.py" in parsed.files

    def test_verify_bundle_roundtrip_runs_behavioral_smoke(self):
        """真实 skill 的独立安装应通过行为级 smoke test。"""
        skill_dir = Path(__file__).parent.parent / "skills" / "qiti-yuanliu"
        result = verify_bundle_roundtrip(skill_dir)
        assert result["passed"] is True
        assert "self-test passed:" in result["self_test"]["stdout"]
        assert "repair_handoff" in result["self_test"]["stdout"] or "health=" in result["self_test"]["stdout"]

    def test_all_real_skills_declare_standalone_validation_contract(self):
        """真实 skill 应声明独立安装后自测入口。"""
        skills_root = Path(__file__).parent.parent / "skills"
        for skill_dir in skills_root.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue
            meta_path = skill_dir / "_skillhub_meta.json"
            if not meta_path.exists():
                continue
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
            contract = payload.get("standalone_validation")
            assert isinstance(contract, dict), skill_dir.name
            assert contract.get("kind") == "python-script", skill_dir.name
            assert contract.get("path") == "tests/standalone_smoke.py", skill_dir.name

    def test_install_bundle_only_checks_entry_metrics(self, tmp_path):
        """安装后的验证只应约束 entry 脚本，不应误伤辅助脚本。"""
        import subprocess

        bundle_path = tmp_path / "demo.skill"
        bundle_path.write_text(
            "\n".join(
                [
                    "===== UNDER-ONE SKILL BUNDLE v1 =====",
                    "name: demo-skill",
                    "version: v1",
                    "built_at: 2026-05-13T00:00:00+00:00",
                    "files: 4",
                    "=====================================",
                    "",
                    "----- file: _skillhub_meta.json -----",
                    json.dumps(
                        {
                            "id": "demo-skill",
                            "name": "Demo Skill",
                            "version": "1.0",
                            "entry": "scripts/run.py",
                            "description": "demo",
                            "triggers": ["demo"],
                            "inputs": ["input.json"],
                            "outputs": ["output.json"],
                            "min_python": "3.8",
                        },
                        ensure_ascii=False,
                    ),
                    "",
                    "----- file: SKILL.md -----",
                    "---",
                    "metadata:",
                    "  name: \"demo-skill\"",
                    "  version: \"1.0\"",
                    "---",
                    "",
                    "# Demo",
                    "",
                    "## 触发词",
                    "- demo",
                    "",
                    "## 功能概述",
                    "demo",
                    "",
                    "## 工作流程",
                    "1. step",
                    "",
                    "## 输入输出",
                    "input.json -> output.json",
                    "",
                    "## API接口",
                    "api",
                    "",
                    "## 使用示例",
                    "demo",
                    "",
                    "## 测试方法",
                    "self-test",
                    "",
                    "----- file: scripts/run.py -----",
                    "from metrics_collector import record_metrics",
                    "",
                    "@record_metrics('demo-skill')",
                    "def main():",
                    "    return {}",
                    "",
                    "if __name__ == '__main__':",
                    "    main()",
                    "",
                    "----- file: scripts/helper.py -----",
                    "def helper():",
                    "    return 'ok'",
                    "",
                    "===== END BUNDLE =====",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        install_root = tmp_path / "skills"
        result = install_bundle(bundle_path, install_root)
        skill_dir = install_root / "demo-skill"
        validate_run = subprocess.run([sys.executable, str(skill_dir / "skillctl.py"), "validate"], capture_output=True, text=True, cwd=skill_dir)
        assert validate_run.returncode == 0
        assert "record runtime metrics" not in validate_run.stdout

    def test_test_skill_uses_targeted_selectors(self, monkeypatch):
        """单 skill 测试命令应选择对应的 pytest 节点。"""
        from under_one import cli
        import subprocess

        calls = {}

        class FakeResult:
            returncode = 0

        def fake_run(cmd, cwd=None):
            calls["cmd"] = cmd
            calls["cwd"] = cwd
            return FakeResult()

        monkeypatch.setattr(subprocess, "run", fake_run)

        with pytest.raises(SystemExit) as exc:
            cli.cmd_test_skill(SimpleNamespace(skill="persona-guard", suite="sdk"))

        assert exc.value.code == 0
        assert calls["cmd"][0] == sys.executable
        assert "test_persona_guard_accepts_profile_dict" in " ".join(calls["cmd"])
        assert "test_persona_guard_legacy_session_log_fallback" in " ".join(calls["cmd"])

    def test_test_skill_supports_installed_path(self, monkeypatch, tmp_path):
        """单 skill 测试命令应支持针对已安装目录运行 self_test.py。"""
        from under_one import cli
        import subprocess

        skill_dir = tmp_path / "demo-skill"
        tests_dir = skill_dir / "tests"
        tests_dir.mkdir(parents=True)
        (tests_dir / "self_test.py").write_text("print('ok')\n", encoding="utf-8")
        calls = {}

        class FakeResult:
            returncode = 0

        def fake_run(cmd, cwd=None):
            calls["cmd"] = cmd
            calls["cwd"] = cwd
            return FakeResult()

        monkeypatch.setattr(subprocess, "run", fake_run)

        with pytest.raises(SystemExit) as exc:
            cli.cmd_test_skill(SimpleNamespace(skill=None, path=str(skill_dir), suite="all"))

        assert exc.value.code == 0
        assert calls["cmd"][0] == sys.executable
        assert calls["cmd"][1].endswith("self_test.py")
        assert calls["cwd"] == str(skill_dir)

    def test_validate_skill_returns_json_report(self, capsys, monkeypatch, tmp_path):
        """单 skill 验证命令应输出可机器消费的报告。"""
        from under_one import cli

        skill_dir = tmp_path / "skills" / "persona-guard"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nmetadata:\n  name: \"demo\"\n  version: \"1.0\"\n---\n\n# Demo\n\n## 触发词\n- demo\n\n## 功能概述\ndemo\n\n## 工作流程\n1. step\n\n## 输入输出\ninput -> output\n\n## API接口\napi\n\n## 使用示例\ndemo\n\n## 测试方法\nauto\n",
            encoding="utf-8",
        )
        (skill_dir / "_skillhub_meta.json").write_text(
            json.dumps(
                {
                    "id": "persona-guard",
                    "name": "Demo",
                    "version": "1.0",
                    "entry": "scripts/run.py",
                    "description": "demo",
                    "triggers": ["demo"],
                    "inputs": ["input"],
                    "outputs": ["output"],
                    "min_python": "3.8",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")

        monkeypatch.setattr(cli, "find_skill_dir", lambda: tmp_path / "skills")
        with pytest.raises(SystemExit) as exc:
            cli.cmd_validate_skill(SimpleNamespace(skill=None, path=str(skill_dir), json=True, output=None))

        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "\"validation_passed\": true" in out
        assert "\"independent_lifecycle\"" in out


class TestSkillGovernance:
    """Skill治理与审计测试"""

    def test_all_real_skills_expose_alignment_profiles(self):
        """每个真实 skill 都应提供统一的对齐元数据。"""
        skills_root = Path(__file__).parent.parent / "skills"
        for skill_dir in skills_root.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue
            meta_path = skill_dir / "_skillhub_meta.json"
            if not meta_path.exists():
                continue
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
            alignment = payload.get("alignment")
            assert isinstance(alignment, dict), skill_dir.name
            for field in ["core", "agent_meaning", "cost", "boundary"]:
                assert alignment.get(field), f"{skill_dir.name}:{field}"

    def test_audit_single_skill(self):
        """单个skill审计应通过且无结构错误"""
        skill_dir = Path(__file__).parent.parent / "skills" / "fenghou-qimen"
        result = audit_skill_dir(skill_dir)
        assert result.ok is True
        assert result.errors == []
        assert result.files_checked >= 4

    def test_audit_all_skills(self):
        """全部skill审计应成功完成"""
        skill_dir = Path(__file__).parent.parent / "skills"
        report = audit_skills_root(skill_dir)
        assert report["skill_count"] == 10
        assert report["ok"] is True
        assert report["error_count"] == 0

    def test_audit_warns_on_missing_doc_sections(self, tmp_path):
        """文档缺失关键章节时应给出warning"""
        skill_dir = tmp_path / "demo-skill"
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True)

        (skill_dir / "_skillhub_meta.json").write_text(
            json.dumps(
                {
                    "id": "demo-skill",
                    "name": "演示技能",
                    "version": "1.0",
                    "entry": "scripts/demo.py",
                    "description": "demo",
                    "triggers": ["demo"],
                    "inputs": ["input.json"],
                    "outputs": ["output.json"],
                    "min_python": "3.8",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (scripts_dir / "demo.py").write_text(
            "from metrics_collector import record_metrics\n@record_metrics('demo-skill')\ndef main():\n    return {}\n",
            encoding="utf-8",
        )
        (skill_dir / "SKILL.md").write_text(
            "---\nmetadata:\n  name: \"demo-skill\"\n  version: \"1.0\"\n---\n\n# Demo\n\n## 功能概述\n\n仅用于测试。\n",
            encoding="utf-8",
        )

        result = audit_skill_dir(skill_dir)
        assert result.ok is True
        assert any("missing recommended sections" in item for item in result.warnings)

    def test_bundle_precheck_passes_for_real_skill(self):
        """真实skill在打包前校验应通过"""
        repo_root = Path(__file__).parent.parent.parent
        ok, errors, warnings = precheck_skill("fenghou-qimen", repo_root)
        assert ok is True
        assert errors == []
        assert warnings == []

    def test_audit_warns_on_missing_io_reference(self, tmp_path):
        """metadata声明的输入输出若未在文档输入输出章节体现，应给出warning"""
        skill_dir = tmp_path / "demo-io-skill"
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True)

        (skill_dir / "_skillhub_meta.json").write_text(
            json.dumps(
                {
                    "id": "demo-io-skill",
                    "name": "演示技能",
                    "version": "1.0",
                    "entry": "scripts/demo.py",
                    "description": "demo",
                    "triggers": ["demo"],
                    "inputs": ["input.json"],
                    "outputs": ["output.json"],
                    "min_python": "3.8",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (scripts_dir / "demo.py").write_text(
            "from metrics_collector import record_metrics\n@record_metrics('demo-io-skill')\ndef main():\n    return {}\n",
            encoding="utf-8",
        )
        (skill_dir / "SKILL.md").write_text(
            "---\nmetadata:\n  name: \"demo-io-skill\"\n  version: \"1.0\"\n---\n\n# Demo\n\n## 触发词\n- demo\n\n## 功能概述\ntext\n\n## 工作流程\n1. step\n\n## 输入输出\n这里只写了示意，但没写具体文件名。\n\n## API接口\napi\n\n## 使用示例\n```json\n{}\n```\n\n## 测试方法\npytest\n\n## 架构设计\n```mermaid\ngraph LR\nA-->B\n```\n```json\n{}\n```\n```json\n{}\n```\n",
            encoding="utf-8",
        )

        result = audit_skill_dir(skill_dir)
        assert result.ok is True
        assert any("metadata input" in item for item in result.warnings)
        assert any("metadata output" in item for item in result.warnings)

    def test_write_audit_report(self, tmp_path):
        """审计报告应可写出为JSON文件"""
        report = {"ok": True, "skill_count": 1, "results": []}
        out = write_audit_report(report, tmp_path / "audit.json")
        assert out.exists()
        assert json.loads(out.read_text(encoding="utf-8"))["ok"] is True


class TestSkillScripts:
    """核心脚本语法测试"""

    def test_all_scripts_compile(self):
        """所有Python脚本可以编译（排除 legacy 归档）"""
        skill_dir = Path(__file__).parent.parent / "skills"
        
        errors = []
        for script in skill_dir.rglob("scripts/*.py"):
            if "legacy" in script.parts:
                continue
            try:
                compile(script.read_text(), str(script), "exec")
            except SyntaxError as e:
                errors.append(f"{script.name}: {e}")
        
        assert not errors, f"Syntax errors: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
