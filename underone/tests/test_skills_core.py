"""
Skill 核心算法单元测试
覆盖 10 个 skill 的核心计算逻辑，不依赖外部文件/网络。
"""

import importlib.util
import json
import sys
from pathlib import Path

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


# ---------------------------------------------------------------------------
# 动态导入所有 skill 模块
# ---------------------------------------------------------------------------
entropy_scanner = _import_skill("qiti_yuanliu.scripts.entropy_scanner")
QiTiScanner = entropy_scanner.QiTiScanner

priority_engine = _import_skill("fenghou_qimen.scripts.priority_engine")
PriorityEngine = priority_engine.PriorityEngine

link_detector = _import_skill("dalu_dongguan.scripts.link_detector")
LinkDetector = link_detector.LinkDetector

knowledge_digest = _import_skill("liuku_xianzei.scripts.knowledge_digest")
KnowledgeDigest = knowledge_digest.KnowledgeDigest

dna_validator = _import_skill("shuangquanshou.scripts.dna_validator")
DNAValidator = dna_validator.DNAValidator

dispatcher = _import_skill("juling_qianjiang.scripts.dispatcher")
dispatch = dispatcher.dispatch
match_spirit = dispatcher.match_spirit

tool_factory = _import_skill("shenji_bailian.scripts.tool_factory")
ToolFactory = tool_factory.ToolFactory

fu_generator = _import_skill("tongtian_lu.scripts.fu_generator")
FuGenerator = fu_generator.FuGenerator

coordinator = _import_skill("bagua_zhen.scripts.coordinator")
calc_stats = coordinator.calc_stats
coordinate = coordinator.coordinate

core_engine = _import_skill("xiushen_lu.scripts.core_engine")
QiSourceV7 = core_engine.QiSourceV7
RefinerV7 = core_engine.RefinerV7
RollbackV7 = core_engine.RollbackV7
XiuShenLuCoreV7 = core_engine.XiuShenLuCoreV7


# ---------------------------------------------------------------------------
# 1. 炁体源流 (context-guard)
# ---------------------------------------------------------------------------

class TestContextGuard:
    """上下文稳态扫描器测试"""

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


# ---------------------------------------------------------------------------
# 2. 风后奇门 (priority-engine)
# ---------------------------------------------------------------------------

class TestPriorityEngine:
    """优先级引擎测试"""

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


# ---------------------------------------------------------------------------
# 4. 六库仙贼 (knowledge-digest)
# ---------------------------------------------------------------------------

class TestKnowledgeDigest:
    """知识消化器测试"""

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


# ---------------------------------------------------------------------------
# 5. 双全手 (persona-guard)
# ---------------------------------------------------------------------------

class TestPersonaGuard:
    """人格DNA守护测试"""

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


# ---------------------------------------------------------------------------
# 6. 拘灵遣将 (tool-orchestrator)
# ---------------------------------------------------------------------------

class TestToolOrchestrator:
    """多工具调度测试"""

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

    def test_empty_tasks(self):
        """空任务列表应返回0质量"""
        result = dispatch([], [])
        assert result["avg_quality"] == 0


# ---------------------------------------------------------------------------
# 7. 神机百炼 (tool-forge)
# ---------------------------------------------------------------------------

class TestToolForge:
    """工具锻造测试"""

    def test_forge_generates_files(self):
        """应生成3个文件"""
        spec = {"name": "json-cleaner", "description": "清洗JSON", "inputs": ["raw.json"], "outputs": ["clean.json"]}
        factory = ToolFactory(spec)
        result = factory.forge()
        assert len(result["files"]) == 3
        assert "json_cleaner.py" in result["files"]
        assert "test_json_cleaner.py" in result["files"]

    def test_tool_code_has_main(self):
        """工具代码应含main函数"""
        spec = {"name": "test-tool", "description": "测试", "inputs": [], "outputs": []}
        factory = ToolFactory(spec)
        result = factory.forge()
        assert "def main():" in result["tool_code"]
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


# ---------------------------------------------------------------------------
# 8. 通天箓 (command-factory)
# ---------------------------------------------------------------------------

class TestCommandFactory:
    """任务拆解测试"""

    def test_detect_analysis_dimension(self):
        """分析关键词应产生分析箓"""
        gen = FuGenerator("分析竞品数据")
        result = gen.generate()
        assert any(f["type"] == "分析箓" for f in result["talisman_list"])

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

    def test_calc_stats_with_data(self):
        """有数据时应计算正确均值"""
        records = [
            {"success": True, "quality_score": 90, "error_count": 0},
            {"success": False, "quality_score": 70, "error_count": 2},
        ]
        stats = calc_stats(records)
        assert stats["success_rate"] == 50.0
        assert stats["quality"] == 80.0
        assert stats["errors"] == 1.0

    def test_coordinate_output_structure(self):
        """协调输出应含关键字段"""
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            report = coordinate(skills_dir="/dev/null")
            assert "ecosystem_level" in report
            assert "average_quality" in report
            assert "skill_states" in report
            assert report["coordinator"] == "bagua-zhen"


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

    def test_refiner_detects_degradation(self, tmp_path):
        """连续退化应被检测"""
        import os
        os.chdir(tmp_path)
        refiner = RefinerV7()
        records = [{"success": True, "error_count": 0, "human_intervention": 0, "quality_score": 100 - i*5} for i in range(10)]
        result = refiner.analyze("test", records)
        assert result["consecutive_degradation"] >= 4

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
