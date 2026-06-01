"""
under-one.skills — 八奇技Agent运维框架

以《一人之下》八奇技为隐喻基底的 Agent-Ops 框架。
十技映射十项异能，每技兼具漫画原作的趣味意象与工程实用性。

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
    "reload_config",
    "redact_config",
    "get_logger",
    "log_span",
    "UnderOneError",
    "SkillExecutionError",
    "InputValidationError",
    "ConfigurationError",
    "LLMProviderError",
    "_clear_skill_cache",
    "RuntimePromptFragment",
    "RuntimePromptCompiler",
    "append_runtime_directives_to_messages",
    "compile_runtime_prompt_messages",
    # 异人风味系统
    "_SKILL_QUOTES",
    "_RESONANCE_TABLE",
    "_get_realm",
    "_get_quote",
    "_check_resonance",
]

import json
import importlib.util
import copy
import io
import sys
import tempfile
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .config import get_script_timeout, load_config, redact_config, reload_config
from .exceptions import (
    ConfigurationError,
    InputValidationError,
    LLMProviderError,
    SkillExecutionError,
    UnderOneError,
)
from .logging import get_logger, log_span
from .metrics import resolve_runtime_data_dir
from .runtime_prompt import (
    RuntimePromptCompiler,
    RuntimePromptFragment,
    append_runtime_directives_to_messages,
    compile_runtime_prompt_messages,
    fragments_to_dicts,
)
from .skill_locator import find_skills_dir

# Module-level logger used to surface in-process skill load failures that would
# otherwise be silently masked by the subprocess fallback path.
_RUNTIME_LOGGER = get_logger("under-one.runtime")


def _find_skill_dir() -> Path:
    """定位 skills 目录。委托给共享的健壮定位器（支持 UNDER_ONE_SKILLS_DIR 覆盖）。"""
    return find_skills_dir()


def _run_script(skill_dir_name: str, script_name: str, *args, input_data=None) -> Dict[str, Any]:
    """统一执行skill脚本的辅助函数"""
    import subprocess
    skill_dir = _find_skill_dir() / skill_dir_name / "scripts"
    script = skill_dir / script_name
    if not script.exists():
        return {"success": False, "error": f"脚本不存在: {script}"}
    cmd = [sys.executable, str(script)] + list(args)
    stdin = json.dumps(input_data) if input_data is not None else None
    timeout = get_script_timeout(skill_dir_name)
    try:
        result = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"脚本执行超时: {script}",
            "timeout_seconds": timeout,
        }
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


def _run_script_with_json(
    skill_dir_name: str,
    script_name: str,
    *payloads: Any,
    extra_args: tuple = (),
) -> Dict[str, Any]:
    """将每个 payload 写入临时 JSON 文件后以文件路径为参数调用脚本，结束后清理临时文件。

    多个 skill 的子进程回退此前各自重复"写临时文件→调用→finally 删除"的样板代码，
    这里集中处理，支持任意数量的 JSON 负载与附加字符串参数。
    """
    tmp_paths: list[str] = []
    try:
        for payload in payloads:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(payload, f)
                tmp_paths.append(f.name)
        return _run_script(skill_dir_name, script_name, *tmp_paths, *extra_args)
    finally:
        for path in tmp_paths:
            Path(path).unlink(missing_ok=True)


@lru_cache(maxsize=16)
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


def _clear_skill_cache() -> None:
    """Clear cached skill modules after runtime evolution or local edits."""

    _load_skill_module.cache_clear()


def _call_silently(fn, *args, **kwargs):
    """执行会打印进度的函数时，静默收集输出。"""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = fn(*args, **kwargs)
    return result


def _invoke_skill(
    skill_dir_name: str,
    script_name: str,
    module_runner: Callable[[Any], Dict[str, Any]],
    fallback: Callable[[], Dict[str, Any]],
) -> Dict[str, Any]:
    """统一的 skill 调用入口：优先在进程内加载脚本模块执行，失败时回退到子进程。

    此前每个 skill 都各自重复 ``try: _load_skill_module(...) except Exception: _run_script(...)``
    的双路回退，且异常被静默吞掉，导致进程内执行失败难以排查。这里集中处理并在回退时
    记录 warning，保留可观测性，同时消除重复代码。

    Args:
        skill_dir_name: skill 目录名（如 ``"tongtian-lu"``）。
        script_name: 脚本文件名（如 ``"fu_generator.py"``）。
        module_runner: 拿到已加载模块后执行核心逻辑、返回结果字典的回调。
        fallback: 进程内执行失败时调用的子进程回退，返回结果字典。
    """
    try:
        mod = _load_skill_module(skill_dir_name, script_name)
        return module_runner(mod)
    except Exception as exc:  # noqa: BLE001 - 故意宽泛捕获以触发子进程回退
        _RUNTIME_LOGGER.warning(
            "in-process load failed for %s/%s (%s: %s); falling back to subprocess",
            skill_dir_name,
            script_name,
            type(exc).__name__,
            exc,
        )
        return fallback()


# ═══════════════════════════════════════════════════════════
# 八奇技异人风味系统 — 语录·境界·共鸣
# ═══════════════════════════════════════════════════════════

# 十技异人语录：每个Skill对应漫画中的经典意象与台词
# 在特定条件下触发，为运行时注入漫画原作的趣味灵魂
_SKILL_QUOTES: Dict[str, Dict[str, Any]] = {
    "qiti-yuanliu": {
        "name_cn": "炁体源流",
        "master": "张怀义",
        "quotes": {
            "excellent": "「炁体源流，万法归一」——先天炁充盈，上下文如明镜止水",
            "good": "「我这一辈子，就做了这一件事」——炁脉尚稳，继续前行",
            "warning": "「炁体污浊，需归本源」——上下文出现裂痕，需诊断修复",
            "danger": "「这股力量……不属于我」——炁场崩塌，立即执行稳态修复",
        },
        "realm_names": {90: "天人合一", 75: "先天炁成", 60: "后天炁聚", 0: "炁脉初开"},
    },
    "tongtian-lu": {
        "name_cn": "通天箓",
        "master": "郑子布",
        "quotes": {
            "quick_cast": "「符到即行，不拘形式」——瞬发符箓，快速拆解",
            "balanced_array": "「列阵通天，符箓连环」——均衡布阵，步步为营",
            "full_ritual": "「通天大阵，六箓齐发」——完整仪式，全链执行",
            "curse_detected": "「此箓有反噬之险」——检测到高风险，需谨慎施法",
        },
        "realm_names": {6: "通天大阵", 4: "符箓连环", 2: "瞬发符箓", 0: "初学画符"},
    },
    "dalu-dongguan": {
        "name_cn": "大罗洞观",
        "master": "周圣",
        "quotes": {
            "deep_insight": "「大罗洞观，洞见一切」——隐藏关联无所遁形",
            "link_found": "「我看到了……那条线」——发现跨段关联",
            "no_link": "「此间无暗线」——各段独立，无隐藏关联",
            "causal_chain": "「因果之线，一拉即出」——检测到因果链",
        },
        "realm_names": {10: "洞观大罗", 5: "明察秋毫", 2: "初窥门径", 0: "凡目未开"},
    },
    "shenji-bailian": {
        "name_cn": "神机百炼",
        "master": "马仙洪",
        "quotes": {
            "forge_start": "「来，让我给你造个更好的」——开始锻造",
            "forge_done": "「神机百炼，无所不能」——锻造完成",
            "contract_first": "「先立契约，再动锤」——契约先行模式",
            "battle_ready": "「这把武器，可以直接上战场」——战备级锻造",
        },
        "realm_names": {5: "百炼成钢", 3: "炉火纯青", 1: "初试锤锻", 0: "生火待炼"},
    },
    "fenghou-qimen": {
        "name_cn": "风后奇门",
        "master": "王也",
        "quotes": {
            "open_gate": "「开门大吉，顺势而为」——气运正旺，立即行动",
            "life_gate": "「生门已开，机不可失」——吉门当值，重点推进",
            "death_gate": "「死门当值，此路不通」——大凶之局，及时止损",
            "monte_carlo": "「蓍草已掷，天机可窥」——蒙特卡洛推演完成",
            "low_robustness": "「气运不顺，需留后手」——鲁棒性不足，增加缓冲",
        },
        "realm_names": {80: "奇门遁甲", 60: "排盘推演", 40: "初识八门", 0: "凡人问卦"},
    },
    "liuku-xianzei": {
        "name_cn": "六库仙贼",
        "master": "巴伦",
        "quotes": {
            "high_digestion": "「六库尽开，万物皆可吞」——消化率极高，知识已内化",
            "medium_digestion": "「消化尚可，还需时日」——部分吸收，待巩固",
            "low_digestion": "「此物难消，先存后议」——消化率低，需反刍复习",
            "quarantine": "「此物有毒，先行隔离」——可疑信息已隔离",
            "contamination": "「知识污染，小心为上」——检测到污染风险",
        },
        "realm_names": {80: "六库全开", 50: "三库初通", 20: "初尝百味", 0: "凡口未开"},
    },
    "shuangquanshou": {
        "name_cn": "双全手",
        "master": "吕良",
        "quotes": {
            "guard_pass": "「双全在手，万法不侵」——人格DNA校验通过",
            "violation": "「有人动了你的记忆」——检测到人格偏离",
            "blocked": "「此路不通，天条在上」——改写请求被护栏阻止",
            "contamination": "「记忆被污染了」——人格污染风险",
            "rewrite": "「让我帮你……改一下」——执行人格改写",
        },
        "realm_names": {0.9: "双全合一", 0.7: "一手遮天", 0.4: "初掌一全", 0.0: "双手空空"},
    },
    "juling-qianjiang": {
        "name_cn": "拘灵遣将",
        "master": "风正豪",
        "quotes": {
            "single": "「一灵镇场，独当一面」——孤魂镇场模式",
            "dual": "「将帅双星，攻守兼备」——双灵协作模式",
            "night_parade": "「百鬼夜行，万灵听令」——全阵出击模式",
            "rebellion": "「灵体反叛！加强拘束」——检测到反叛风险",
            "fallback": "「主灵力竭，副灵接阵」——执行降级切换",
        },
        "realm_names": {3: "百鬼夜行", 1: "将帅双星", 0: "孤魂镇场"},
    },
    "bagua-zhen": {
        "name_cn": "八卦阵",
        "master": "十技共修",
        "quotes": {
            "excellent": "「八卦归位，十技同心」——生态完美，各技协同",
            "healthy": "「阵法运转，气脉通畅」——生态健康，正常运行",
            "warning": "「阵眼松动，需加稳固」——生态预警，需关注",
            "danger": "「阵法将破，速速修补」——生态危急，立即干预",
            "mutex": "「两技相冲，阵法自调」——互斥仲裁生效",
            "synergy": "「奇技共鸣，威力倍增」——协同增益触发",
        },
        "realm_names": {90: "万法归宗", 75: "八卦圆融", 60: "阵法初成", 0: "散沙未阵"},
    },
    "xiushen-lu": {
        "name_cn": "修身炉",
        "master": "马仙洪（造物主）",
        "quotes": {
            "evolved": "「炉火纯青，百炼成钢」——技能已完成一次自进化",
            "planned": "「炉温已到，待开炉门」——进化计划已就绪",
            "rollback": "「炉火失控，紧急回炉」——检测到异常，自动回滚",
            "tuning": "「微调火候，精益求精」——参数微调进化",
            "extension": "「添柴加火，扩展炉膛」——功能扩展进化",
            "refactor": "「推倒重炼，脱胎换骨」——结构重构进化",
        },
        "realm_names": {10: "脱胎换骨", 5: "百炼成钢", 2: "初入炉火", 0: "凡铁未炼"},
    },
}

# 八奇技共鸣表：当特定Skill组合协同工作时触发
_RESONANCE_TABLE = {
    frozenset(["qiti-yuanliu", "dalu-dongguan"]): {
        "name": "炁观共鸣",
        "desc": "炁体源流诊断 + 大罗洞观追踪 = 全链路诊断修复闭环",
        "quote": "「炁体归源，洞观万象——诊断与追踪合一，矛盾无所遁形」",
    },
    frozenset(["tongtian-lu", "shenji-bailian"]): {
        "name": "符炉共鸣",
        "desc": "通天箓拆解 + 神机百炼锻造 = 任务拆解→工具生成全链路",
        "quote": "「符箓引路，神机锻造——指令即出，利器即成」",
    },
    frozenset(["fenghou-qimen", "juling-qianjiang"]): {
        "name": "奇将共鸣",
        "desc": "风后奇门排盘 + 拘灵遣将调度 = 优先级驱动+工具编排",
        "quote": "「奇门定序，遣将执行——排兵布阵，万灵听令」",
    },
    frozenset(["qiti-yuanliu", "shuangquanshou"]): {
        "name": "炁手共鸣",
        "desc": "炁体源流自省 + 双全手护栏 = 上下文健康+人格一致性双重保障",
        "quote": "「内观炁体，外守双全——内外兼修，万法不侵」",
    },
    frozenset(["liuku-xianzei", "dalu-dongguan"]): {
        "name": "贼观共鸣",
        "desc": "六库仙贼消化 + 大罗洞观关联 = 知识消化+关联发现深度理解",
        "quote": "「吞纳万物，洞观其根——消化与洞察合一，知识化为真知」",
    },
}


def _get_realm(skill_name: str, score: float) -> str:
    """根据分数获取修炼境界名称。"""
    skill_info = _SKILL_QUOTES.get(skill_name, {})
    realm_map = skill_info.get("realm_names", {})
    for threshold in sorted(realm_map.keys(), reverse=True):
        if score >= threshold:
            return str(realm_map[threshold])
    return "未入境界"


def _get_quote(skill_name: str, quote_key: str) -> str:
    """获取异人语录。"""
    skill_info = _SKILL_QUOTES.get(skill_name, {})
    return str((skill_info.get("quotes") or {}).get(quote_key, ""))


def _check_resonance(active_skills: list) -> list:
    """检查当前活跃的Skill组合是否触发八奇技共鸣。"""
    active_set = frozenset(active_skills)
    resonances = []
    for pair, info in _RESONANCE_TABLE.items():
        if pair.issubset(active_set):
            resonances.append({"pair": sorted(pair), **info})
    return resonances


# ── Skill基类 ──
class BaseSkill:
    """所有skill的基类，提供统一接口与异人风味"""
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
        metrics_dir = resolve_runtime_data_dir()
        metrics_dir.mkdir(parents=True, exist_ok=True)
        quality_score = result.get("quality_score", result.get("score"))
        entry = {
            "skill_name": self.skill_name,
            "timestamp": datetime.now().isoformat(),
            "success": result.get("success", True),
            "quality_score": quality_score,
            "quality_assessed": quality_score is not None,
            "error_count": result.get("error_count", 0),
        }
        with open(metrics_dir / f"{self.skill_name}_metrics.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _enrich_with_flavor(self, result: Dict[str, Any], quote_key: str, score_key: str = "health_score", score_default: float = 0.0) -> Dict[str, Any]:
        """为结果注入异人风味：语录、境界、共鸣信息。不改变核心逻辑，仅增加趣味层。"""
        score = result.get(score_key, score_default)
        if isinstance(score, dict):
            score = score_default

        result.setdefault("flavor", {
            "skill_cn": _SKILL_QUOTES.get(self.skill_name, {}).get("name_cn", self.skill_name),
            "master": _SKILL_QUOTES.get(self.skill_name, {}).get("master", "未知"),
            "quote": _get_quote(self.skill_name, quote_key),
            "realm": _get_realm(self.skill_name, float(score) if score else 0.0),
        })
        return result


def _short_text(value: Any, max_chars: int = 120) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _fragment(
    source_skill: str,
    priority: int,
    condition: str,
    directive: str,
    *,
    ttl_rounds: int = 3,
    metadata: Optional[Dict[str, Any]] = None,
) -> RuntimePromptFragment:
    return RuntimePromptFragment(
        source_skill=source_skill,
        priority=priority,
        condition=condition,
        directive=directive,
        ttl_rounds=ttl_rounds,
        metadata=metadata or {},
    )


# ── 十技完整实现 ──
class ContextGuard(BaseSkill):
    """炁体源流 — 本源自省与稳态自愈。检测漂移、提炼规则、生成修正路径。
    
    张怀义所悟八奇技之首——炁体源流，可追溯万物本源。
    对话上下文即Agent的"炁脉"，炁场纯净则思路清晰，炁体污浊则需诊断修复。
    """
    skill_name = "qiti-yuanliu"

    def run(self, context: list) -> Dict[str, Any]:
        """
        扫描上下文健康状态——以炁体源流之法，观上下文炁脉。
        Args:
            context: 对话轮次列表 [{"role": "user", "content": "..."}, ...]
        Returns:
            {"health_score": float, "entropy": float, "alerts": list, "success": bool, "flavor": dict}
        """
        self.logger.info(f"扫描{len(context)}轮对话并提炼炁体规则")
        mod = _load_skill_module("qiti-yuanliu", "entropy_scanner.py")
        normalized_context = self._normalize_context(context)
        result: Dict[str, Any] = mod.QiTiScanner(normalized_context).scan()
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
        result["runtime_prompt_fragments"] = fragments_to_dicts(
            self._build_runtime_prompt_fragments(result)
        )

        # 注入异人风味
        health_score = (result.get("metrics") or {}).get("health_score", 0)
        entropy_level = (result.get("metrics") or {}).get("entropy_level", "green")
        if entropy_level in ("red", "danger") or (isinstance(health_score, (int, float)) and health_score < 60):
            quote_key = "danger"
        elif entropy_level == "yellow" or (isinstance(health_score, (int, float)) and health_score < 75):
            quote_key = "warning"
        elif isinstance(health_score, (int, float)) and health_score >= 90:
            quote_key = "excellent"
        else:
            quote_key = "good"
        self._enrich_with_flavor(result, quote_key, score_key="health_score", score_default=health_score or 0)

        return result

    def _build_runtime_prompt_fragments(self, result: Dict[str, Any]) -> list[RuntimePromptFragment]:
        metrics = result.get("metrics") or {}
        fragments: list[RuntimePromptFragment] = []
        entropy = metrics.get("entropy", 0)
        entropy_level = metrics.get("entropy_level")
        if entropy_level == "red":
            fragments.append(
                _fragment(
                    self.skill_name,
                    1,
                    f"entropy={entropy}",
                    f"[ENTROPY-CRITICAL] 上下文混乱度 {entropy}，你必须先总结已知共识，标注不确定处，再回应；不要引入新话题。",
                    metadata={"entropy": entropy, "entropy_level": entropy_level},
                )
            )
        elif entropy_level == "yellow":
            fragments.append(
                _fragment(
                    self.skill_name,
                    2,
                    f"entropy={entropy}",
                    f"[ENTROPY-WARN] 上下文混乱度 {entropy}，先对齐当前目标与约束，再继续执行。",
                    metadata={"entropy": entropy, "entropy_level": entropy_level},
                )
            )

        alignment = metrics.get("alignment", 100)
        origin_goal = result.get("origin_anchor") or (result.get("origin_core") or {}).get("goal_anchor")
        if isinstance(alignment, (int, float)) and alignment < 85:
            fragments.append(
                _fragment(
                    self.skill_name,
                    2,
                    f"alignment={alignment}",
                    f"[DRIFT] 你已偏离原始目标「{_short_text(origin_goal, 90)}」，请回归主线，避免展开无关讨论。",
                    metadata={"alignment": alignment, "origin_goal": origin_goal},
                )
            )

        repair_handoff = result.get("repair_handoff") or {}
        if repair_handoff:
            target_skill = repair_handoff.get("target_skill", "dalu-dongguan")
            fragments.append(
                _fragment(
                    self.skill_name,
                    1,
                    f"repair_handoff:{target_skill}",
                    f"[HANDOFF] 上下文修复已移交 {target_skill}；完成前不要引入新假设，保持与原始目标一致。",
                    ttl_rounds=4,
                    metadata={
                        "target_skill": target_skill,
                        "contradiction_rounds": repair_handoff.get("contradiction_rounds", []),
                    },
                )
            )

        alerts = result.get("alerts") or []
        if alerts:
            first_alert = alerts[0]
            fragments.append(
                _fragment(
                    self.skill_name,
                    2,
                    str(first_alert.get("type") or first_alert.get("level") or "alert"),
                    f"[CONTEXT-ALERT] 检测到「{_short_text(first_alert.get('message'), 120)}」；回复前先澄清立场与依据。",
                    ttl_rounds=2,
                    metadata={"alert": first_alert},
                )
            )
        return fragments

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
    """通天箓 — 瞬发指令工厂。将复杂任务拆解为可执行步骤链。
    
    郑子布所悟八奇技——通天箓，不拘泥于形式，瞬发符箓即可成阵。
    任务拆解如同画符，简单任务一符即成，复杂任务需列阵通天。
    """
    skill_name = "tongtian-lu"

    def run(self, task: str) -> Dict[str, Any]:
        """
        拆解任务为可执行符箓链——以通天箓之法，画符布阵。
        Args:
            task: 自然语言描述的任务，如"分析竞品数据并生成报告"
        Returns:
            {"dimensions": list, "conflicts": list, "curse_level": str, "success": bool, "flavor": dict}
        """
        self.logger.info(f"拆解任务: {task[:50]}")
        result = _invoke_skill(
            "tongtian-lu",
            "fu_generator.py",
            module_runner=lambda mod: {**mod.FuGenerator(task).generate(), "success": True},
            fallback=lambda: _run_script("tongtian-lu", "fu_generator.py", task),
        )

        talisman_list = result.get("talisman_list", [])
        result.setdefault("dimensions", len(talisman_list) if isinstance(talisman_list, list) else 1)
        result.setdefault("curse_level", result.get("curse_level", "low"))

        # 注入异人风味
        dims = result.get("dimensions", 1)
        curse = result.get("curse_level", "low")
        if curse in ("high", "critical"):
            quote_key = "curse_detected"
        elif isinstance(dims, int) and dims >= 6:
            quote_key = "full_ritual"
        elif isinstance(dims, int) and dims >= 4:
            quote_key = "balanced_array"
        else:
            quote_key = "quick_cast"
        self._enrich_with_flavor(result, quote_key, score_key="dimensions", score_default=float(dims) if isinstance(dims, int) else 1.0)

        return result


class InsightRadar(BaseSkill):
    """大罗洞观 — 全局洞察雷达。跨文档/跨轮次发现隐藏关联。
    
    周圣所悟八奇技——大罗洞观，洞见一切暗线。
    如同漫画中周圣能看穿一切隐藏的关联，此技可发现跨段文本间的
    因果链、矛盾点与深层联系。
    """
    skill_name = "dalu-dongguan"

    def run(self, segments: list) -> Dict[str, Any]:
        """
        分析多段文本间的关联——以大罗洞观之法，洞见暗线。
        Args:
            segments: 文本段落列表 [{"id": "s1", "text": "..."}, ...]
        Returns:
            {"links": list, "mermaid": str, "success": bool, "flavor": dict}
        """
        self.logger.info(f"分析{len(segments)}段文本的关联")
        mod = _load_skill_module("dalu-dongguan", "link_detector.py")
        normalized_segments = self._normalize_segments(segments)
        result: Dict[str, Any] = mod.LinkDetector(normalized_segments).detect()
        result["success"] = True

        # 注入异人风味
        links = result.get("links", [])
        link_count = len(links) if isinstance(links, list) else 0
        if link_count >= 10:
            quote_key = "deep_insight"
        elif link_count >= 5:
            quote_key = "causal_chain"
        elif link_count > 0:
            quote_key = "link_found"
        else:
            quote_key = "no_link"
        self._enrich_with_flavor(result, quote_key, score_key="link_count", score_default=float(link_count))

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
    """神机百炼 — 自主工具锻造。需求描述→可运行Python脚本+测试+契约。
    
    马仙洪所悟八奇技——神机百炼，造物之术。
    如同漫画中马仙洪的修身炉可以锻造一切，此技将需求描述
    锻造为可运行的Python工具，附带测试与契约。
    """
    skill_name = "shenji-bailian"

    def run(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据需求生成工具脚本——以神机百炼之法，锻造利器。
        Args:
            requirement: {"name": "工具名", "inputs": [...], "outputs": [...], "description": "..."}
        Returns:
            {"tool_code": str, "test_code": str, "contract": str, "success": bool, "flavor": dict}
        """
        self.logger.info(f"锻造工具: {requirement.get('name', 'unnamed')}")
        result = _invoke_skill(
            "shenji-bailian",
            "tool_factory.py",
            module_runner=lambda mod: {**mod.ToolFactory(requirement).forge(), "success": True},
            fallback=lambda: _run_script("shenji-bailian", "tool_factory.py", input_data=requirement),
        )

        # 注入异人风味
        has_contract = bool(result.get("contract"))
        has_test = bool(result.get("test_code"))
        has_code = bool(result.get("tool_code"))
        if has_contract and has_test and has_code:
            quote_key = "battle_ready"
        elif has_contract:
            quote_key = "contract_first"
        elif has_code:
            quote_key = "forge_done"
        else:
            quote_key = "forge_start"
        self._enrich_with_flavor(result, quote_key, score_key="quality_score", score_default=1.0 if has_code else 0.0)

        return result


class PriorityEngine(BaseSkill):
    """风后奇门 — 任务优先级引擎。九维度评分+八门映射+蒙特卡洛验证。
    
    王也所悟八奇技——风后奇门，推演吉凶、趋吉避凶。
    如同漫画中王也的奇门遁甲排盘，此技以九维度评分映射八门，
    蓍草占卜（蒙特卡洛）推演气运，为任务排兵布阵。
    """
    skill_name = "fenghou-qimen"

    def run(self, tasks: list) -> Dict[str, Any]:
        """
        对任务列表进行优先级排序——以风后奇门之法，排盘推演。
        Args:
            tasks: [{"name": "任务名", "urgency": 1-5, "importance": 1-5, ...}, ...]
        Returns:
            {"execution_plan": list, "top_gate": str, "success": bool, "flavor": dict}
        """
        self.logger.info(f"排序{len(tasks)}个任务")
        result = _invoke_skill(
            "fenghou-qimen",
            "priority_engine.py",
            module_runner=lambda mod: {**mod.PriorityEngine(tasks).run(), "success": True},
            fallback=lambda: _run_script_with_json("fenghou-qimen", "priority_engine.py", tasks),
        )
        result["runtime_prompt_fragments"] = fragments_to_dicts(
            self._build_runtime_prompt_fragments(result)
        )

        # 注入异人风味
        top_gate = result.get("top_gate", "生门")
        on_time_rate = (result.get("monte_carlo") or {}).get("on_time_rate", 0)
        if top_gate == "开门":
            quote_key = "open_gate"
        elif top_gate == "生门":
            quote_key = "life_gate"
        elif top_gate == "死门":
            quote_key = "death_gate"
        elif isinstance(on_time_rate, (int, float)) and on_time_rate < 60:
            quote_key = "low_robustness"
        else:
            quote_key = "monte_carlo"
        self._enrich_with_flavor(result, quote_key, score_key="average_score", score_default=float(on_time_rate) if isinstance(on_time_rate, (int, float)) else 0.0)

        return result

    def _build_runtime_prompt_fragments(self, result: Dict[str, Any]) -> list[RuntimePromptFragment]:
        fragments: list[RuntimePromptFragment] = []
        for task in result.get("ranked_tasks", []):
            if task.get("gate") == "死门":
                fragments.append(
                    _fragment(
                        self.skill_name,
                        3,
                        f"dead_gate:{task.get('name')}",
                        f"[PRIORITY] 任务「{_short_text(task.get('name'), 80)}」被评为死门；除非用户明确要求，否则跳过或延后。",
                        ttl_rounds=2,
                        metadata={"task": task},
                    )
                )
                break

        on_time_rate = (result.get("monte_carlo") or {}).get("on_time_rate")
        if isinstance(on_time_rate, (int, float)) and on_time_rate < 60:
            fragments.append(
                _fragment(
                    self.skill_name,
                    2,
                    f"on_time_rate={on_time_rate}",
                    "[ROBUSTNESS] 执行计划鲁棒性不足；为任务预留缓冲，遇到阻塞立即上报，不要强行推进。",
                    ttl_rounds=3,
                    metadata={"on_time_rate": on_time_rate},
                )
            )
        return fragments


class KnowledgeDigest(BaseSkill):
    """六库仙贼 — 知识消化器。可信度分级+消化率评估+保鲜期追踪。
    
    巴伦所悟八奇技——六库仙贼，吞纳万物。
    如同漫画中巴伦可以吞噬一切，此技对知识条目进行消化率评估，
    可信度分级如同辨别食材品质，隔离可疑信息如同隔离毒物。
    """
    skill_name = "liuku-xianzei"

    def run(self, items: list) -> Dict[str, Any]:
        """
        评估知识条目的消化质量——以六库仙贼之法，吞纳消化。
        Args:
            items: [{"source": "来源", "content": "内容", "credibility": "S/A/B/C"}, ...]
        Returns:
            {"avg_digestion_rate": float, "distribution": dict, "success": bool, "flavor": dict}
        """
        self.logger.info(f"消化{len(items)}条知识")
        result = _invoke_skill(
            "liuku-xianzei",
            "knowledge_digest.py",
            module_runner=lambda mod: {**mod.KnowledgeDigest(items).digest(), "success": True},
            fallback=lambda: _run_script_with_json("liuku-xianzei", "knowledge_digest.py", items),
        )
        result["runtime_prompt_fragments"] = fragments_to_dicts(
            self._build_runtime_prompt_fragments(result)
        )

        # 注入异人风味
        avg_digestion = result.get("avg_digestion_rate", 0)
        if isinstance(avg_digestion, (int, float)) and avg_digestion >= 80:
            quote_key = "high_digestion"
        elif isinstance(avg_digestion, (int, float)) and avg_digestion >= 50:
            quote_key = "medium_digestion"
        elif isinstance(avg_digestion, (int, float)) and avg_digestion > 0:
            quote_key = "low_digestion"
        elif result.get("quarantine_queue"):
            quote_key = "quarantine"
        else:
            quote_key = "contamination"
        self._enrich_with_flavor(result, quote_key, score_key="avg_digestion_rate", score_default=float(avg_digestion) if isinstance(avg_digestion, (int, float)) else 0.0)

        return result

    def _build_runtime_prompt_fragments(self, result: Dict[str, Any]) -> list[RuntimePromptFragment]:
        fragments: list[RuntimePromptFragment] = []
        quarantine = result.get("quarantine_queue") or []
        if quarantine:
            sources = ", ".join(
                _short_text(item.get("source") or item.get("id") or idx + 1, 24)
                for idx, item in enumerate(quarantine[:3])
                if isinstance(item, dict)
            )
            fragments.append(
                _fragment(
                    self.skill_name,
                    2,
                    f"quarantine={len(quarantine)}",
                    f"[KNOWLEDGE-GUARD] {len(quarantine)} 条信息已隔离（{sources}）；禁止把这些信息当作可靠论据。",
                    ttl_rounds=3,
                    metadata={"quarantine_count": len(quarantine)},
                )
            )

        risk = result.get("contamination_risk") or {}
        risk_level = risk.get("level")
        if risk_level in {"medium", "high"}:
            priority = 2 if risk_level == "high" else 3
            fragments.append(
                _fragment(
                    self.skill_name,
                    priority,
                    f"contamination={risk_level}",
                    f"[CONTAMINATION] 知识污染风险为 {risk_level}；引用任何结论前必须标注来源可信度等级。",
                    ttl_rounds=3,
                    metadata={"contamination_risk": risk},
                )
            )
        return fragments


class PersonaGuard(BaseSkill):
    """双全手 — 记忆/人格手术台。DNA护栏 + 改写方案 + 污染风险控制。
    
    吕良所悟八奇技——双全手，掌控记忆与人格。
    如同漫画中吕良可以改写记忆，此技守护Agent的人格DNA，
    检测偏离如同察觉记忆被篡改，护栏如同天条不可逾越。
    """
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
        result = _invoke_skill(
            "shuangquanshou",
            "dna_validator.py",
            module_runner=lambda mod: {**mod.DNAValidator(normalized_profile).validate(), "success": True},
            fallback=lambda: self._run_cli_fallback(normalized_profile),
        )

        result["allow"] = result.get("can_switch", False)
        result["violation_count"] = len(result.get("dna_violations", []))
        deviation = result.get("deviation_score", 0.0) or 0.0
        result["consistency"] = round(max(0.0, 1.0 - float(deviation)), 3)
        result.setdefault("primary_domain", (result.get("surgery_plan") or [{}])[0].get("domain"))
        patch_simulation = self._simulate_rewrite_patch(normalized_profile, result.get("rewrite_patch", {}))
        result["patch_simulation"] = patch_simulation
        result["applied_profile_preview"] = patch_simulation.get("profile_preview")
        result["rollback_profile_preview"] = patch_simulation.get("rollback_preview")
        result["runtime_prompt_fragments"] = fragments_to_dicts(
            self._build_runtime_prompt_fragments(normalized_profile, result)
        )

        # 注入异人风味
        violations = result.get("dna_violations", [])
        contamination_index = result.get("contamination_index", 0)
        approval_contract = result.get("approval_contract") or {}
        if approval_contract.get("approval_status") == "blocked":
            quote_key = "blocked"
        elif violations:
            quote_key = "violation"
        elif isinstance(contamination_index, (int, float)) and contamination_index >= 0.6:
            quote_key = "contamination"
        elif result.get("rewrite_patch", {}).get("items"):
            quote_key = "rewrite"
        else:
            quote_key = "guard_pass"
        self._enrich_with_flavor(result, quote_key, score_key="consistency", score_default=result.get("consistency", 0.0))

        return result

    def _build_runtime_prompt_fragments(
        self, profile: Dict[str, Any], result: Dict[str, Any]
    ) -> list[RuntimePromptFragment]:
        fragments: list[RuntimePromptFragment] = []
        violations = result.get("dna_violations") or []
        dna_core = profile.get("dna_core") or {}
        requested_change = profile.get("requested_change") or {}
        if violations:
            first_violation = violations[0]
            detail = first_violation.get("principle") or first_violation.get("type") or first_violation
            fragments.append(
                _fragment(
                    self.skill_name,
                    1,
                    f"dna_violation:{detail}",
                    f"[PERSONA-GUARD] 检测到风格或人格边界偏离「{_short_text(detail, 80)}」；必须维持核心约束「{_short_text(dna_core, 90)}」，禁止未经确认的切换。",
                    ttl_rounds=4,
                    metadata={"violation_count": len(violations), "first_violation": first_violation},
                )
            )

        contamination_index = result.get("contamination_index")
        if isinstance(contamination_index, (int, float)) and contamination_index >= 0.6:
            fragments.append(
                _fragment(
                    self.skill_name,
                    2,
                    f"contamination_index={contamination_index}",
                    f"[CONTAMINATION] 人格污染风险指数 {contamination_index:.2f}；不要模仿用户语气，保持专业中立。",
                    ttl_rounds=3,
                    metadata={"contamination_index": contamination_index},
                )
            )

        approval_contract = result.get("approval_contract") or {}
        if approval_contract.get("approval_status") == "blocked":
            fragments.append(
                _fragment(
                    self.skill_name,
                    1,
                    "approval_blocked",
                    f"[PERSONA-BLOCK] 当前改写请求「{_short_text(requested_change, 90)}」被护栏阻止；只提供解释和安全替代方案。",
                    ttl_rounds=3,
                    metadata={"approval_contract": approval_contract},
                )
            )
        return fragments

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
        simulation: Dict[str, Any] = {
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
            try:
                result = subprocess.run(
                    [sys.executable, str(script), str(profile_path)],
                    capture_output=True,
                    text=True,
                    cwd=tmpdir,
                    timeout=get_script_timeout("shuangquanshou"),
                )
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"脚本执行超时: {script}",
                    "timeout_seconds": get_script_timeout("shuangquanshou"),
                }
            report_path = Path(tmpdir) / "dna_report.json"
            if report_path.exists():
                try:
                    parsed: Dict[str, Any] = json.loads(report_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    parsed = {"raw_output": result.stdout.strip()}
            else:
                parsed = {"raw_output": result.stdout.strip()}
            parsed["success"] = result.returncode == 0
            if result.stderr:
                parsed["stderr"] = result.stderr[:500]
            return parsed


class ToolOrchestrator(BaseSkill):
    """拘灵遣将 — 灵体统御中枢。主副灵调度、边界控制与反叛风险监控。
    
    风正豪所悟八奇技——拘灵遣将，驭使万灵。
    如同漫画中风正豪拘押灵体遣将出阵，此技调度工具/子代理，
    孤魂镇场如单兵作战，将帅双星如主副协作，百鬼夜行如全阵出击。
    """
    skill_name = "juling-qianjiang"

    def __init__(self, config=None):
        super().__init__(config)
        jg = self.config.get("julingqianjiang", {})
        self.strategy = jg.get("strategy", "protect")

    def run(self, tasks: list, spirits: list) -> Dict[str, Any]:  # type: ignore[override]
        """
        调度多个工具执行任务——以拘灵遣将之法，遣灵出阵。
        Args:
            tasks: [{"type": "search", "desc": "..."}, ...]
            spirits: [{"id": "api1", "capabilities": ["search"], "available": true}, ...]
        Returns:
            {"plan": list, "fallback_count": int, "avg_quality": float, "success": bool, "flavor": dict}
        """
        self.logger.info(f"调度{len(tasks)}个任务到{len(spirits)}个工具 (策略={self.strategy})")
        formation = self.config.get("julingqianjiang", {}).get("formation")
        result = _invoke_skill(
            "juling-qianjiang",
            "dispatcher.py",
            module_runner=lambda mod: {
                **mod.dispatch(tasks, spirits, strategy=self.strategy, formation=formation),
                "success": True,
            },
            fallback=lambda: _run_script_with_json(
                "juling-qianjiang",
                "dispatcher.py",
                tasks,
                spirits,
                extra_args=(self.strategy,),
            ),
        )

        # 注入异人风味
        formation_name = result.get("formation", "single-possession")
        has_rebellion = any(
            (t.get("rebellion_risk") or "").lower() in ("high", "medium")
            for t in result.get("plan", [])
            if isinstance(t, dict)
        )
        has_fallback = (result.get("fallback_count") or 0) > 0
        if has_rebellion:
            quote_key = "rebellion"
        elif has_fallback:
            quote_key = "fallback"
        elif formation_name == "night-parade":
            quote_key = "night_parade"
        elif formation_name == "dual-attunement":
            quote_key = "dual"
        else:
            quote_key = "single"
        avg_quality = result.get("avg_quality", 0.0)
        self._enrich_with_flavor(result, quote_key, score_key="avg_quality", score_default=float(avg_quality) if isinstance(avg_quality, (int, float)) else 0.0)

        return result


class EcosystemHub(BaseSkill):
    """八卦阵 — 中央协调器。十技状态监控+互斥仲裁+协同增益。
    
    八卦阵非八奇技之一，而是十技共修的阵法中枢。
    如同漫画中各派异人布阵对峙，此技监控十技生态，
    互斥仲裁如同阵法自调，协同增益如同奇技共鸣。
    """
    skill_name = "bagua-zhen"

    def run(self) -> Dict[str, Any]:  # type: ignore[override]
        """
        扫描十技生态全景——以八卦阵之法，观全局气脉。
        Returns:
            {"ecosystem_level": str, "average_quality": float, "skill_states": dict, "success": bool, "flavor": dict}
        """
        self.logger.info("扫描十技生态全景")
        result = _invoke_skill(
            "bagua-zhen",
            "coordinator.py",
            module_runner=lambda mod: {
                **_call_silently(mod.coordinate, str(_find_skill_dir())),
                "success": True,
            },
            fallback=lambda: _run_script("bagua-zhen", "coordinator.py"),
        )
        result["runtime_prompt_fragments"] = fragments_to_dicts(
            self._build_runtime_prompt_fragments(result)
        )

        # 注入异人风味
        level = result.get("ecosystem_level", "unknown")
        has_mutex = bool(result.get("mutex_pairs"))
        if level in ("excellent", "healthy", "stable", "green"):
            quote_key = "excellent" if level in ("excellent", "green") else "healthy"
        elif level in ("warning", "yellow"):
            quote_key = "warning"
        elif level in ("danger", "red", "critical"):
            quote_key = "danger"
        elif has_mutex:
            quote_key = "mutex"
        else:
            quote_key = "healthy"
        avg_quality = result.get("average_quality", 0.0)
        self._enrich_with_flavor(result, quote_key, score_key="average_quality", score_default=float(avg_quality) if isinstance(avg_quality, (int, float)) else 0.0)

        # 检查八奇技共鸣
        active_skills = [
            name for name, state in (result.get("skill_states") or {}).items()
            if isinstance(state, dict) and state.get("status") not in ("error", "unavailable", None)
        ]
        resonances = _check_resonance(active_skills)
        if resonances:
            result["resonances"] = resonances

        return result

    def _build_runtime_prompt_fragments(self, result: Dict[str, Any]) -> list[RuntimePromptFragment]:
        fragments: list[RuntimePromptFragment] = []
        mutex_pairs = result.get("mutex_pairs") or []
        if mutex_pairs:
            pair = mutex_pairs[0]
            a, b = (pair + [None, None])[:2] if isinstance(pair, list) else (None, None)
            fragments.append(
                _fragment(
                    self.skill_name,
                    2,
                    f"mutex_pairs={len(mutex_pairs)}",
                    f"[ECOSYSTEM] {a} 与 {b} 存在互斥风险；不要同时遵循冲突指导，先选择更贴近当前用户目标的一侧。",
                    ttl_rounds=3,
                    metadata={"mutex_pairs": mutex_pairs},
                )
            )

        level = result.get("ecosystem_level")
        avg_quality = result.get("average_quality")
        if level not in (None, "excellent", "healthy", "stable", "green") and level:
            fragments.append(
                _fragment(
                    self.skill_name,
                    3,
                    f"ecosystem_level={level}",
                    f"[ECOSYSTEM-WARN] 十技生态状态为 {level}，平均质量 {avg_quality}；减少并行任务，聚焦单一目标。",
                    ttl_rounds=2,
                    metadata={"ecosystem_level": level, "average_quality": avg_quality},
                )
            )
        return fragments


class EvolutionEngine(BaseSkill):
    """修身炉 — 自进化引擎。运行时指标分析+自动参数优化。
    
    马仙洪所造修身炉——可炼万物，亦可炼己。
    如同漫画中修身炉可以改造异人，此技根据运行时指标
    自动优化参数，微调火候如精益求精，推倒重炼如脱胎换骨。
    """
    skill_name = "xiushen-lu"

    def run(self, target_skill: Optional[str] = None) -> Dict[str, Any]:
        """
        启动自进化周期——以修身炉之法，百炼成钢。
        Args:
            target_skill: 指定进化的skill名称 (None=全部)
        Returns:
            {"evolved": int, "failed": int, "unchanged": int, "success": bool, "flavor": dict}
        """
        self.logger.info(f"启动修身炉进化 (目标={target_skill or '全部'})")
        skill_dir = str(_find_skill_dir())

        def _run_in_process(mod: Any) -> Dict[str, Any]:
            core = mod.XiuShenLuCoreV7(skill_dir, apply_changes=False, persist_adaptive=False)
            return {**_call_silently(core.run_evolution_cycle, target_skill), "success": True}

        def _run_via_script() -> Dict[str, Any]:
            args = [skill_dir]
            if target_skill:
                args.append(target_skill)
            return _run_script("xiushen-lu", "core_engine.py", *args)

        result = _invoke_skill(
            "xiushen-lu",
            "core_engine.py",
            module_runner=_run_in_process,
            fallback=_run_via_script,
        )
        result["runtime_prompt_fragments"] = fragments_to_dicts(
            self._build_runtime_prompt_fragments(result)
        )

        # 注入异人风味
        evolved_count = result.get("evolved", 0)
        failed_count = result.get("failed", 0)
        results_list = result.get("results", [])
        # 判断主要进化类型
        evolution_types = set()
        for item in results_list:
            if isinstance(item, dict):
                evo_type = (item.get("analysis") or {}).get("bottleneck_type") or item.get("planned_evolution_type")
                if evo_type:
                    evolution_types.add(str(evo_type))

        if evolved_count > 0:
            quote_key = "evolved"
        elif failed_count > 0:
            quote_key = "rollback"
        elif "extension" in evolution_types or "feature" in evolution_types:
            quote_key = "extension"
        elif "refactor" in evolution_types or "restructure" in evolution_types:
            quote_key = "refactor"
        elif results_list:
            quote_key = "planned"
        else:
            quote_key = "tuning"
        total = max(evolved_count + result.get("unchanged", 0) + failed_count, 1)
        self._enrich_with_flavor(result, quote_key, score_key="evolved", score_default=float(evolved_count))

        return result

    def _build_runtime_prompt_fragments(self, result: Dict[str, Any]) -> list[RuntimePromptFragment]:
        fragments: list[RuntimePromptFragment] = []
        for item in result.get("results", [])[:3]:
            skill = item.get("skill")
            status = item.get("status")
            analysis = item.get("analysis") or {}
            if status == "evolved":
                changes = item.get("evolution", {}).get("changes", [])
                change_text = "; ".join(str(change) for change in changes[:2]) or "已完成一次受控优化"
                fragments.append(
                    _fragment(
                        self.skill_name,
                        4,
                        f"evolved:{skill}",
                        f"[EVOLVED-RULE] {skill} 已根据近期运行数据优化：{_short_text(change_text, 140)}。",
                        ttl_rounds=5,
                        metadata={"skill": skill, "status": status},
                    )
                )
            elif status == "planned":
                bottleneck = analysis.get("bottleneck_type") or item.get("planned_evolution_type")
                fragments.append(
                    _fragment(
                        self.skill_name,
                        4,
                        f"planned:{skill}:{bottleneck}",
                        f"[EVOLUTION-PLAN] {skill} 近期瓶颈为 {bottleneck}；判断相关结果时提高核验强度。",
                        ttl_rounds=3,
                        metadata={"skill": skill, "status": status, "bottleneck_type": bottleneck},
                    )
                )
        return fragments
