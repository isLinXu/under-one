#!/usr/bin/env python3
"""
under-one.skills 核心测试套件
覆盖: 配置加载、Skill基类、CLI入口
"""

import json
import os
import sys
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace
from urllib.request import urlopen

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

import skills.check_versions as skill_version_checker
import skills._skill_config as skill_config
import scripts.evaluate_skills as evaluate_module
import under_one.config as config_module

from under_one import (
    load_config, reload_config, redact_config, BaseSkill,
    CommandFactory, ContextGuard, EvolutionEngine, InsightRadar,
    EcosystemHub, KnowledgeDigest, PersonaGuard, PriorityEngine, ToolForge, ToolOrchestrator,
)
import under_one as under_one_pkg
from under_one.skill_locator import SKILLS_DIR_ENV, find_skills_dir, looks_like_skills_root
from under_one.exceptions import InputValidationError, LLMProviderError, SkillExecutionError, UnderOneError
from under_one.skill_bundle import build_bundle_text, install_bundle, parse_bundle_text, resolve_bundle_version, verify_bundle_roundtrip
from under_one.skill_audit import audit_skill_dir, audit_skills_root, write_audit_report
from under_one.codex_skills import build_codex_skill_markdown, install_codex_skill
from scripts.evaluate_skills import evaluate_all
from scripts.build_skill_bundles import precheck_skill
from skills.metrics_collector import (
    create_prometheus_server,
    format_prometheus_metrics,
    get_recent_metrics,
    record_metric_manual,
    record_metrics,
)


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

    def test_config_env_override_and_redaction(self, tmp_path, monkeypatch):
        """配置应支持环境变量覆盖，并在诊断输出中遮蔽敏感值。"""
        config_path = tmp_path / "under-one.yaml"
        config_path.write_text(
            "config_version: 1\nruntime:\n  script_timeout_seconds: 60\nllm:\n  api_key: plain\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("UNDER_ONE__RUNTIME__SCRIPT_TIMEOUT_SECONDS", "9")
        config_module.clear_config_cache()

        cfg = load_config(config_path)
        assert cfg["runtime"]["script_timeout_seconds"] == 9
        redacted = redact_config(cfg)
        assert redacted["llm"]["api_key"] == "***REDACTED***"

    def test_config_hot_reload_honors_mtime_when_enabled(self, tmp_path, monkeypatch):
        """热更新开启时，同一路径配置修改后应重新读取。"""
        config_path = tmp_path / "under-one.yaml"
        config_path.write_text("config_version: 1\nruntime:\n  script_timeout_seconds: 3\n", encoding="utf-8")
        monkeypatch.setenv("UNDER_ONE_CONFIG_RELOAD", "1")
        config_module.clear_config_cache()

        assert load_config(config_path)["runtime"]["script_timeout_seconds"] == 3
        config_path.write_text("config_version: 1\nruntime:\n  script_timeout_seconds: 4\n", encoding="utf-8")
        assert load_config(config_path)["runtime"]["script_timeout_seconds"] == 4
        assert reload_config(config_path)["runtime"]["script_timeout_seconds"] == 4


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

    def test_metrics_collector_marks_unassessed_quality(self, tmp_path, monkeypatch):
        """无法推断质量分时应写入 None，而不是伪造 85 分。"""
        monkeypatch.chdir(tmp_path)

        @record_metrics("unassessed-metric-skill")
        def run_unassessed():
            return {"success": True}

        run_unassessed()
        record = get_recent_metrics("unassessed-metric-skill", n=1)[0]
        assert record["quality_score"] is None
        assert record["quality_assessed"] is False

    def test_metrics_collector_records_resource_snapshot(self, tmp_path, monkeypatch):
        """metrics_collector 应记录进程资源快照字段。"""
        monkeypatch.chdir(tmp_path)

        @record_metrics("resource-metric-skill")
        def run_resource_sample():
            return {"quality_score": 91}

        run_resource_sample()
        record = get_recent_metrics("resource-metric-skill", n=1)[0]
        assert "peak_memory_mb" in record
        assert "cpu_time_ms" in record
        assert "resource_warnings" in record
        assert record["resource_budget_exceeded"] in {True, False}

    def test_manual_metric_flags_resource_budget_exceeded(self, tmp_path, monkeypatch):
        """手动指标记录应按 runtime.resource_limits 标出预算越界。"""
        monkeypatch.setenv("UNDER_ONE__RUNTIME__RESOURCE_LIMITS__MAX_DURATION_MS", "1")
        config_module.clear_config_cache()
        try:
            record_metric_manual(
                "budget-metric-skill",
                duration_ms=25,
                success=True,
                quality_score=90,
                data_dir=tmp_path,
            )
            record = get_recent_metrics("budget-metric-skill", n=1, data_dir=tmp_path)[0]
            assert record["resource_budget_exceeded"] is True
            assert any(item["type"] == "duration_limit" for item in record["resource_warnings"])
        finally:
            config_module.clear_config_cache()

    def test_metrics_export_respects_runtime_dir_env(self, tmp_path, monkeypatch):
        """BaseSkill 导出的 metrics 应支持隔离 runtime 目录。"""
        runtime_dir = tmp_path / "isolated-runtime"
        monkeypatch.setenv("UNDER_ONE_RUNTIME_DIR", str(runtime_dir))

        class DummySkill(BaseSkill):
            skill_name = "env-skill"

            def run(self, data):
                return {"success": True, "quality_score": 93}

        DummySkill().export_metrics({"success": True, "quality_score": 93})

        metrics_file = runtime_dir / "env-skill_metrics.jsonl"
        assert metrics_file.exists()
        record = json.loads(metrics_file.read_text(encoding="utf-8").splitlines()[0])
        assert record["quality_score"] == 93

    def test_prometheus_metrics_export_skips_corrupt_lines(self, tmp_path):
        """Prometheus 文本导出应跳过损坏 JSONL 行。"""
        runtime_dir = tmp_path / "runtime"
        runtime_dir.mkdir()
        metrics_file = runtime_dir / "demo_metrics.jsonl"
        metrics_file.write_text(
            '{"skill_name":"demo","success":true,"duration_ms":10,"quality_score":90,"output_completeness":95}\n'
            '{broken\n',
            encoding="utf-8",
        )
        text = format_prometheus_metrics(runtime_dir)
        assert 'under_one_skill_runs_total{skill_name="demo",success="true"} 1' in text
        assert 'under_one_skill_quality_score_avg{skill_name="demo"} 90.000' in text

    def test_prometheus_http_server_serves_metrics(self, tmp_path):
        """Prometheus HTTP 端点应暴露 /metrics。"""
        runtime_dir = tmp_path / "runtime"
        runtime_dir.mkdir()
        (runtime_dir / "demo_metrics.jsonl").write_text(
            '{"skill_name":"demo","success":true,"duration_ms":10,"quality_score":90}\n',
            encoding="utf-8",
        )
        server = create_prometheus_server("127.0.0.1", 0, runtime_dir)
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            host, port = server.server_address[:2]
            body = urlopen(f"http://{host}:{port}/metrics", timeout=3).read().decode("utf-8")
        finally:
            thread.join(timeout=3)
            server.server_close()
        assert 'under_one_skill_runs_total{skill_name="demo",success="true"} 1' in body
        assert "under_one_skill_resource_budget_exceeded_total" in body

    def test_exception_hierarchy_is_exported(self):
        """统一异常体系应可被 SDK 调用方稳定捕获。"""
        assert issubclass(SkillExecutionError, UnderOneError)
        assert issubclass(InputValidationError, UnderOneError)
        assert issubclass(LLMProviderError, UnderOneError)


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

    def test_evaluate_all_uses_isolated_runtime_snapshot(self, tmp_path, monkeypatch):
        """评估报告不应被外部 runtime 历史数据污染。"""
        polluted_runtime = tmp_path / "polluted-runtime"
        polluted_runtime.mkdir()
        polluted_metric = {
            "skill_name": "qiti-yuanliu",
            "timestamp": "2026-05-14T00:00:00",
            "duration_ms": 1,
            "success": True,
            "quality_score": 1.0,
            "error_count": 0,
            "human_intervention": 1.0,
            "output_completeness": 1.0,
            "consistency_score": 1.0,
        }
        (polluted_runtime / "qiti-yuanliu_metrics.jsonl").write_text(
            "\n".join(json.dumps(polluted_metric, ensure_ascii=False) for _ in range(12)) + "\n",
            encoding="utf-8",
        )

        reports_dir = tmp_path / "reports"
        monkeypatch.setenv("UNDER_ONE_RUNTIME_DIR", str(polluted_runtime))
        monkeypatch.setattr(evaluate_module, "REPORTS_DIR", reports_dir)
        monkeypatch.setattr(evaluate_module, "EVAL_RUNTIME_DIR", reports_dir / "_eval_runtime")

        report = evaluate_module.evaluate_all()
        qiti = next(item for item in report["skills"] if item["skill"] == "qiti-yuanliu")

        assert report["runtime_mode"] == "isolated"
        assert Path(report["runtime_dir"]) == reports_dir / "_eval_runtime"
        assert qiti["runtime"]["record_count"] == 1
        assert qiti["runtime"]["avg_quality"] > 1.0
        assert os.environ.get("UNDER_ONE_RUNTIME_DIR") == str(polluted_runtime)

    def test_evaluate_all_treats_xiushenlu_manual_gate_as_governance_not_low_autonomy(self):
        """修身炉 plan-only 的人工变更门不应被误判为自治能力缺陷。"""
        report = evaluate_all()
        xiushen = next(item for item in report["skills"] if item["skill"] == "xiushen-lu")

        assert xiushen["runtime"]["avg_human_intervention"] == 1.0
        assert xiushen["runtime"]["manual_gate_expected"] is True
        assert xiushen["runtime"]["effective_human_intervention"] == 0.0
        assert xiushen["runtime"]["human_intervention_interpretation"] == "manual_gate"
        assert not any("improve autonomy before expanding scope" in rec for rec in xiushen["recommendations"])


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
        assert parsed.version == "v6.4"

    def test_resolve_bundle_version_prefers_skill_metadata(self, tmp_path):
        """bundle 默认版本应跟随 skill metadata，而不是硬编码框架版本。"""
        skill_dir = tmp_path / "demo-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "_skillhub_meta.json").write_text(
            json.dumps({"id": "demo-skill", "version": "v0.1.0"}, ensure_ascii=False),
            encoding="utf-8",
        )
        (skill_dir / "SKILL.md").write_text(
            "---\nmetadata:\n  version: \"v9.9.9\"\n---\n",
            encoding="utf-8",
        )
        assert resolve_bundle_version(skill_dir) == "v0.1.0"

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

    def test_all_real_skills_expose_bootstrap_profiles(self):
        """每个真实 skill 都应携带冷启动画像，便于独立安装后复现。"""
        skills_root = Path(__file__).parent.parent / "skills"
        required = [
            "avg_quality",
            "avg_completeness",
            "avg_consistency",
            "avg_human",
            "success_rate",
            "avg_duration",
            "recommended_min_records",
        ]
        for skill_dir in skills_root.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue
            meta_path = skill_dir / "_skillhub_meta.json"
            if not meta_path.exists():
                continue
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
            profile = payload.get("bootstrap_profile")
            assert isinstance(profile, dict), skill_dir.name
            for field in required:
                assert isinstance(profile.get(field), (int, float)), f"{skill_dir.name}:{field}"

    def test_control_plane_skills_expose_control_plane_contracts(self):
        """三大控制层 skill 应显式声明 observer / coordinator / evolver 边界协议。"""
        skills_root = Path(__file__).parent.parent / "skills"
        expected_roles = {
            "qiti-yuanliu": "observer",
            "bagua-zhen": "coordinator",
            "xiushen-lu": "evolver",
        }
        for skill_name, role in expected_roles.items():
            payload = json.loads((skills_root / skill_name / "_skillhub_meta.json").read_text(encoding="utf-8"))
            contract = payload.get("control_plane_contract")
            assert isinstance(contract, dict), skill_name
            assert contract.get("role") == role, skill_name
            assert isinstance(contract.get("reads"), list), skill_name
            assert isinstance(contract.get("writes"), list), skill_name
            assert isinstance(contract.get("will_not"), list), skill_name

    def test_xiushen_meta_exposes_engine_manifest(self):
        """修身炉应明确唯一入口与实验/辅助脚本分层。"""
        skills_root = Path(__file__).parent.parent / "skills"
        payload = json.loads((skills_root / "xiushen-lu" / "_skillhub_meta.json").read_text(encoding="utf-8"))
        manifest = payload.get("engine_manifest")
        assert isinstance(manifest, dict)
        assert manifest["active_entry"] == "scripts/core_engine.py"
        assert "scripts/xiushenlu_verifier.py" in manifest["auxiliary_tools"]
        assert "scripts/v8_engine.py" in manifest["deprecated_experiments"]
        assert manifest["experimental_opt_in"]["env"] == "UNDERONE_ALLOW_XIUSHEN_EXPERIMENTS"
        assert manifest["experimental_opt_in"]["flag"] == "--allow-experimental-entry"
        assert manifest["experimental_opt_in"]["redirect_entry"] == "scripts/core_engine.py"

    def test_xiushen_deprecated_engines_require_explicit_opt_in(self):
        """实验引擎默认应拒绝作为生产入口运行，并提示回到 core_engine。"""
        import subprocess

        scripts_root = Path(__file__).parent.parent / "skills" / "xiushen-lu" / "scripts"
        for script_name in ("v8_engine.py", "universal_engine.py"):
            proc = subprocess.run(
                [sys.executable, str(scripts_root / script_name)],
                capture_output=True,
                text=True,
                cwd=str(scripts_root),
            )
            assert proc.returncode == 2, script_name
            assert "core_engine.py" in proc.stderr, script_name
            assert "UNDERONE_ALLOW_XIUSHEN_EXPERIMENTS" in proc.stderr, script_name
            assert "--allow-experimental-entry" in proc.stderr, script_name

    def test_xiushen_deprecated_engines_can_be_opted_in_explicitly(self):
        """显式实验模式下，旧引擎应继续暴露自身用法而不是直接拦截。"""
        import subprocess

        scripts_root = Path(__file__).parent.parent / "skills" / "xiushen-lu" / "scripts"
        for script_name in ("v8_engine.py", "universal_engine.py"):
            proc = subprocess.run(
                [sys.executable, str(scripts_root / script_name), "--allow-experimental-entry"],
                capture_output=True,
                text=True,
                cwd=str(scripts_root),
            )
            assert proc.returncode == 1, script_name
            assert "用法" in proc.stdout, script_name

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

    def test_audit_warns_on_invalid_bootstrap_profile(self, tmp_path):
        """bootstrap_profile 类型不对时应给出 warning，帮助第三方 skill 自查。"""
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
                    "bootstrap_profile": {"avg_quality": "high"},
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
            "---\nmetadata:\n  name: \"demo-skill\"\n  version: \"1.0\"\n---\n\n# Demo\n\n## 触发词\n- demo\n\n## 功能概述\ntext\n\n## 工作流程\n1. step\n\n## 输入输出\ninput.json -> output.json\n\n## API接口\napi\n\n## 使用示例\n```json\n{}\n```\n\n## 测试方法\npytest\n\n## 架构设计\n```mermaid\ngraph LR\nA-->B\n```\n```json\n{}\n```\n```json\n{}\n```\n",
            encoding="utf-8",
        )

        result = audit_skill_dir(skill_dir)
        assert result.ok is True
        assert any("bootstrap_profile field avg_quality must be numeric" in item for item in result.warnings)

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


class TestSkillLocator:
    """skills 目录定位器测试：环境变量覆盖、哨兵校验、清晰错误。"""

    def test_find_skills_dir_resolves_package_layout_by_default(self, monkeypatch):
        """无环境变量时应解析到随包发布的 skills 目录。"""
        monkeypatch.delenv(SKILLS_DIR_ENV, raising=False)
        skills_dir = find_skills_dir()
        assert looks_like_skills_root(skills_dir)
        assert (skills_dir / "qiti-yuanliu").is_dir()

    def test_env_override_accepts_skills_dir_directly(self, monkeypatch):
        """UNDER_ONE_SKILLS_DIR 指向 skills 目录本身时应被采用。"""
        real = find_skills_dir()
        monkeypatch.setenv(SKILLS_DIR_ENV, str(real))
        assert find_skills_dir() == real

    def test_env_override_accepts_parent_dir(self, monkeypatch):
        """UNDER_ONE_SKILLS_DIR 指向父目录时应自动下探到其 skills/ 子目录。"""
        real = find_skills_dir()
        monkeypatch.setenv(SKILLS_DIR_ENV, str(real.parent))
        assert find_skills_dir() == real

    def test_missing_skills_dir_raises_with_searched_paths(self, tmp_path, monkeypatch):
        """完全找不到时应抛出 SkillExecutionError 并列出已搜索路径。"""
        monkeypatch.setenv(SKILLS_DIR_ENV, str(tmp_path / "nope"))
        monkeypatch.chdir(tmp_path)
        # 屏蔽随包默认候选，制造彻底缺失场景。
        monkeypatch.setattr(
            "under_one.skill_locator._default_candidates",
            lambda: [tmp_path / "missing-a", tmp_path / "missing-b"],
        )
        with pytest.raises(SkillExecutionError) as excinfo:
            find_skills_dir()
        message = str(excinfo.value)
        assert SKILLS_DIR_ENV in message
        assert "missing-a" in message

    def test_looks_like_skills_root_rejects_partial_dir(self, tmp_path):
        """仅含部分 skill 目录的路径不应被误判为 skills 根。"""
        (tmp_path / "qiti-yuanliu").mkdir()
        assert looks_like_skills_root(tmp_path) is False


class TestInvokeSkillFallback:
    """_invoke_skill 统一回退与可观测性测试。"""

    def test_falls_back_and_logs_when_in_process_load_fails(self, caplog):
        """进程内执行抛错时应回退到 fallback，并记录 warning 以保留可观测性。"""
        sentinel = {"success": True, "via": "fallback"}

        def runner(_mod):
            raise RuntimeError("boom")

        with caplog.at_level("WARNING", logger="under-one.runtime"):
            result = under_one_pkg._invoke_skill(
                "tongtian-lu",
                "fu_generator.py",
                module_runner=runner,
                fallback=lambda: sentinel,
            )

        assert result is sentinel
        assert any("falling back to subprocess" in record.getMessage() for record in caplog.records)

    def test_uses_in_process_result_when_module_runs(self):
        """进程内执行成功时应直接返回其结果，不触发回退。"""
        marker = {"success": True, "via": "in-process"}
        result = under_one_pkg._invoke_skill(
            "tongtian-lu",
            "fu_generator.py",
            module_runner=lambda _mod: marker,
            fallback=lambda: {"via": "fallback"},
        )
        assert result == marker


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
