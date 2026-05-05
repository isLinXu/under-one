"""
under-one.skills — 八奇技Agent运维框架

Usage:
    from under_one import ContextGuard, PriorityEngine, ToolOrchestrator
    
    guard = ContextGuard()
    result = guard.scan(conversation_history)
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
import logging
import os
import tempfile
from datetime import datetime
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
    cmd = ["python", str(script)] + list(args)
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


# ── Skill基类 ──
class BaseSkill:
    """所有skill的基类，提供统一接口"""
    skill_name: str = "base"
    skill_version: str = "10.0.0"

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
    """炁体源流 — 上下文稳态自愈。检测对话漂移和矛盾，自动修复。"""
    skill_name = "qiti-yuanliu"

    def run(self, context: list) -> Dict[str, Any]:
        """
        扫描上下文健康状态。
        Args:
            context: 对话轮次列表 [{"role": "user", "content": "..."}, ...]
        Returns:
            {"health_score": float, "entropy": float, "alerts": list, "success": bool}
        """
        self.logger.info(f"扫描{len(context)}轮对话的上下文健康状态")
        return _run_script("qiti-yuanliu", "entropy_scanner.py", input_data=context)


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
        result = _run_script("tongtian-lu", "fu_generator.py", task)
        # 从stdout提取关键信息
        stdout = result.get("raw_output", "")
        dimensions = stdout.count("【") if "【" in stdout else 1
        curse = "high" if "禁咒等级: high" in stdout else "low"
        result["dimensions"] = dimensions
        result["curse_level"] = curse
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
        return _run_script("dalu-dongguan", "link_detector.py", input_data=segments)


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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(tasks, f)
            tmp = f.name
        try:
            result = _run_script("fenghou-qimen", "priority_engine.py", tmp)
        finally:
            Path(tmp).unlink(missing_ok=True)
        return result


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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(items, f)
            tmp = f.name
        try:
            result = _run_script("liuku-xianzei", "knowledge_digest.py", tmp)
        finally:
            Path(tmp).unlink(missing_ok=True)
        return result


class PersonaGuard(BaseSkill):
    """双全手 — 人格与记忆守护。DNA校验+风格漂移拦截。"""
    skill_name = "shuangquanshou"

    def run(self, session_log: list) -> Dict[str, Any]:
        """
        校验会话是否符合人格DNA。
        Args:
            session_log: [{"mode": "模式A"}, {"mode": "模式B"}, ...]
        Returns:
            {"allow": bool, "violation_count": int, "consistency": float, "success": bool}
        """
        self.logger.info(f"校验{len(session_log)}轮会话的人格一致性")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(session_log, f)
            tmp = f.name
        try:
            result = _run_script("shuangquanshou", "dna_validator.py", tmp)
        finally:
            Path(tmp).unlink(missing_ok=True)
        return result


class ToolOrchestrator(BaseSkill):
    """拘灵遣将 — 多工具调度中枢。健康检查+降级保护+SLA监控。"""
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(tasks, tf)
            task_path = tf.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as sf:
            json.dump(spirits, sf)
            spirit_path = sf.name
        try:
            result = _run_script("juling-qianjiang", "dispatcher.py", task_path, spirit_path, self.strategy)
        finally:
            Path(task_path).unlink(missing_ok=True)
            Path(spirit_path).unlink(missing_ok=True)
        return result


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
        args = [skill_dir]
        if target_skill:
            args.append(target_skill)
        return _run_script("xiushen-lu", "core_engine.py", *args)
