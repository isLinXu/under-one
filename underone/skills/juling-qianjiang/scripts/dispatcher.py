#!/usr/bin/env python3
"""
器名: 拘灵遣将 V9.8 调度器 (Juling Qianjiang V9.8 Dispatcher)
用途: 多工具调度 + 健康监控 + 降级保护 + 可选服灵模式 + 恢复契约
核心机制: 
  - 正常模式: 工具不可用时降级保护（跳过/模拟/缓存）
  - 服灵模式(可选): 工具不可用时内化生成替代实现
  - 百鬼夜行: 大规模并行调度
  - 多维度评分匹配: 能力/健康/负载/质量综合评估
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime

# 运行时指标收集
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
try:
    from metrics_collector import record_metrics
except ImportError:
    def record_metrics(*args, **kwargs):
        def decorator(f): return f
        return decorator

# 配置加载
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
try:
    from _skill_config import validate_json_list, get_skill_config
except ImportError:
    def validate_json_list(data, item_schema, skill_name="skill"):
        if not isinstance(data, list):
            return False, ["<root> must be a list"]
        return True, []
    def get_skill_config(skill_name, key=None, default=None):
        return default


# 全局调用计数器（用于负载均衡）
_call_counts = {}

_SOUL_CAPABILITY_KEYWORDS = {
    "search": ["search", "research", "检索", "搜索", "查询"],
    "browse": ["browse", "crawl", "scrape", "网页", "浏览", "抓取", "fetch"],
    "code": ["code", "python", "engineering", "开发", "编码", "脚本", "programming"],
    "data": ["data", "analysis", "analytics", "分析", "数据", "transform"],
    "write": ["write", "draft", "copy", "writing", "写作", "总结", "文案"],
    "memory": ["memory", "recall", "记忆", "知识库"],
    "planning": ["plan", "planning", "拆解", "workflow", "调度", "规划"],
}


def _load_dispatcher_config():
    """加载调度器配置"""
    return {
        "match_weights": get_skill_config("julingqianjiang", "match_weights", {
            "capability": 0.40,
            "health": 0.25,
            "load_balance": 0.20,
            "quality": 0.15,
        }),
        "load_balance_strategy": get_skill_config("julingqianjiang", "load_balance_strategy", "best_score"),
        "health_warning": get_skill_config("julingqianjiang", "health_warning", 0.60),
        "health_critical": get_skill_config("julingqianjiang", "health_critical", 0.30),
        "capability_aliases": get_skill_config("julingqianjiang", "capability_aliases", {}),
        "fallback_protect": get_skill_config("julingqianjiang", "fallback_protect", {}),
        "fallback_possess": get_skill_config("julingqianjiang", "fallback_possess", {}),
        "fallback_quality_floor": get_skill_config("julingqianjiang", "fallback_quality_floor", 0.55),
        "fallback_history_weight": get_skill_config("julingqianjiang", "fallback_history_weight", 0.35),
        "fallback_exact_match_bonus": get_skill_config("julingqianjiang", "fallback_exact_match_bonus", 0.05),
        "max_support_spirits": get_skill_config("julingqianjiang", "max_support_spirits", 2),
        "formation": get_skill_config("julingqianjiang", "formation", "dual-attunement"),
        "formations": get_skill_config("julingqianjiang", "formations", {
            "single-possession": {"max_support_spirits": 0, "role_label": "sole"},
            "dual-attunement": {"max_support_spirits": 1, "role_label": "primary"},
            "night-parade": {"max_support_spirits": 3, "role_label": "marshal"},
        }),
    }


def _detect_capabilities_from_text(text: str) -> list:
    """从 soul.md 文本中推断能力标签。"""
    lowered = text.lower()
    caps = []
    for capability, keywords in _SOUL_CAPABILITY_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            caps.append(capability)
    return caps or ["general"]


def _extract_markdown_sections(text: str) -> dict:
    """提取 markdown 二级/三级标题下的文本。"""
    sections = {}
    current = "overview"
    buffer = []
    for line in text.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            sections[current] = "\n".join(buffer).strip()
            current = re.sub(r"^#{1,3}\s+", "", line).strip().lower()
            buffer = []
            continue
        buffer.append(line)
    sections[current] = "\n".join(buffer).strip()
    return {k: v for k, v in sections.items() if v}


def _extract_bullets(section_text: str) -> list:
    bullets = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            item = stripped[2:].strip()
            if item:
                bullets.append(item)
    return bullets


def _find_section(sections: dict, aliases: list) -> str:
    for key, value in sections.items():
        lowered = key.lower()
        if any(alias in lowered for alias in aliases):
            return value
    return ""


def parse_soul_markdown(text: str, source_path: str = "soul.md") -> dict:
    """将 openclaw/hermes-agent 风格的 soul.md 解析为 spirit 描述。"""
    source = Path(source_path)
    sections = _extract_markdown_sections(text)
    overview = sections.get("overview", text[:400]).strip()
    capabilities = _detect_capabilities_from_text(text)
    persona_text = _find_section(sections, ["persona", "identity", "character", "人设", "性格"])
    capability_text = _find_section(sections, ["capabilities", "skills", "abilities", "能力", "专长"])
    limits_text = _find_section(sections, ["limits", "constraints", "taboo", "禁忌", "限制", "边界"])
    invocation_text = _find_section(sections, ["invocation", "ritual", "rules", "activation", "召唤", "调用"])

    traits = [item for item in _extract_bullets(persona_text or text) if len(item) <= 60][:8]
    declared_capabilities = _extract_bullets(capability_text)
    limits = _extract_bullets(limits_text)[:6]
    invocation_rules = _extract_bullets(invocation_text)[:6]
    if declared_capabilities:
        detected_from_declared = _detect_capabilities_from_text("\n".join(declared_capabilities))
        capabilities = sorted(dict.fromkeys(capabilities + declared_capabilities + detected_from_declared))

    agent_family = "generic"
    source_lower = source_path.lower()
    if "openclaw" in source_lower or "openclaw" in text.lower():
        agent_family = "openclaw"
    elif "hermes" in source_lower or "hermes-agent" in source_lower or "hermes" in text.lower():
        agent_family = "hermes-agent"

    parent_name = source.parent.name if source.parent.name else ""
    if source.stem.lower() == "soul" and agent_family != "generic":
        spirit_id = agent_family
    else:
        spirit_id = parent_name or source.stem or agent_family
    return {
        "id": spirit_id or source.stem or "soul-spirit",
        "capabilities": capabilities,
        "available": True,
        "quality_score": 0.88,
        "source_type": "soul_markdown",
        "agent_family": agent_family,
        "soul_profile": {
            "source_path": source_path,
            "summary": overview[:240],
            "traits": traits,
            "declared_capabilities": declared_capabilities,
            "limits": limits,
            "invocation_rules": invocation_rules,
            "sections": list(sections.keys()),
        },
    }


def load_spirits_source(path: str) -> list:
    """从 JSON、单个 soul.md 或灵体目录加载 spirit 列表。"""
    file_path = Path(path)
    if file_path.is_dir():
        spirits = []
        for md in sorted(file_path.rglob("*.md")):
            if md.name.lower() == "soul.md" or "soul" in md.stem.lower():
                spirits.append(parse_soul_markdown(md.read_text(encoding="utf-8"), source_path=str(md)))
        if spirits:
            return spirits
        raise ValueError("spirit directory does not contain any soul.md-like markdown files")

    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()

    if file_path.suffix.lower() == ".md":
        return [parse_soul_markdown(raw, source_path=path)]

    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise ValueError("spirits source must be a JSON object/list or soul.md markdown")


def _build_soul_binding(task: dict, spirit: dict, role: str = "primary", support_spirits: list | None = None) -> dict | None:
    """为 soul.md 来源的 spirit 生成非破坏式附体建议。"""
    if spirit.get("source_type") != "soul_markdown":
        return None
    profile = spirit.get("soul_profile", {})
    task_type = task.get("type", "")
    spirit_caps = spirit.get("capabilities", [])
    activated = []
    for cap in spirit_caps:
        cap_text = str(cap).lower()
        if cap_text == task_type or task_type in cap_text or cap_text in _expand_capabilities(task_type, {}):
            activated.append(cap)
    if not activated:
        activated = spirit_caps[:2]

    invocation_rules = profile.get("invocation_rules", [])
    invocation_protocol = invocation_rules[:2] if invocation_rules else [
        f"Bind {spirit.get('id', 'spirit')} to {task_type or 'general'} workflow",
        "Keep soul.md read-only; emit attunement guidance only",
    ]
    return {
        "task_type": task_type,
        "spirit_id": spirit.get("id", "unknown"),
        "role": role,
        "agent_family": spirit.get("agent_family", "generic"),
        "source_path": profile.get("source_path"),
        "mode": "non_destructive_attunement",
        "summary": profile.get("summary", ""),
        "recommended_traits": profile.get("traits", [])[:4],
        "activated_capabilities": activated[:3],
        "avoid_constraints": profile.get("limits", [])[:3],
        "invocation_protocol": invocation_protocol,
        "support_spirits": support_spirits or [],
    }


def _resolve_formation(cfg: dict, formation: str | None = None) -> dict:
    """解析当前附体阵型配置。"""
    formations = cfg.get("formations", {})
    selected = formation or cfg.get("formation", "dual-attunement")
    profile = formations.get(selected, {})
    return {
        "name": selected,
        "max_support_spirits": int(profile.get("max_support_spirits", cfg.get("max_support_spirits", 2))),
        "role_label": profile.get("role_label", "primary"),
    }


def _build_formation_payload(task: dict, primary_spirit: dict, support_spirits: list, formation_cfg: dict) -> dict:
    """为不同阵型生成差异化的协同语义。"""
    task_type = task.get("type", "general")
    primary_caps = primary_spirit.get("capabilities", [])[:3]
    support_ids = [item.get("spirit_id", "unknown") for item in support_spirits]
    formation = formation_cfg["name"]

    if formation == "single-possession":
        return {
            "formation_intent": "pure inheritance",
            "exclusive_traits": primary_spirit.get("soul_profile", {}).get("traits", [])[:3],
            "coordination_plan": [
                f"{primary_spirit.get('id', 'primary')} handles the full {task_type} workflow alone",
                "No auxiliary spirits may override tone or decisions",
            ],
            "spirit_queue": [primary_spirit.get("id", "primary")],
        }

    if formation == "night-parade":
        queue = [primary_spirit.get("id", "primary")] + support_ids
        return {
            "formation_intent": "parallel pressure and layered support",
            "coordination_plan": [
                f"{primary_spirit.get('id', 'primary')} acts as marshal for the {task_type} objective",
                "Support spirits contribute specialized abilities without taking over the lead voice",
            ],
            "spirit_queue": queue,
            "support_wave_count": len(support_spirits),
            "parallel_channels": max(1, len(queue)),
        }

    return {
        "formation_intent": "primary-support split",
        "coordination_plan": [
            f"{primary_spirit.get('id', 'primary')} leads the {task_type} execution",
            "One support spirit backfills missing capability or perspective",
        ],
        "spirit_queue": [primary_spirit.get("id", "primary")] + support_ids[:1],
        "support_wave_count": min(1, len(support_spirits)),
        "primary_focus": primary_caps,
    }


def _expand_capabilities(task_type: str, aliases: dict) -> set:
    """扩展能力匹配范围（支持别名）"""
    expanded = {task_type}
    if task_type in aliases:
        expanded.update(aliases[task_type])
    # 反向查找：如果别名映射到 task_type，也加入
    for main_cap, alias_list in aliases.items():
        if task_type in alias_list:
            expanded.add(main_cap)
    return expanded


def _score_capability_match(task_type: str, spirit: dict, aliases: dict) -> float:
    """计算能力匹配得分 (0.0 - 1.0)"""
    spirit_caps = spirit.get("capabilities", [])
    if not spirit_caps:
        return 0.0
    
    # 精确匹配
    if task_type in spirit_caps:
        return 1.0
    
    # 别名匹配
    expanded = _expand_capabilities(task_type, aliases)
    matches = expanded & set(spirit_caps)
    if matches:
        return 0.8  # 别名匹配得分略低于精确匹配
    
    return 0.0


def _score_health(spirit: dict, health_critical: float, health_warning: float) -> float:
    """计算健康度得分 (0.0 - 1.0)"""
    if not spirit.get("available", True):
        return 0.0
    
    success_rate = spirit.get("success_rate", 1.0)
    latency_score = 1.0
    if "avg_latency_ms" in spirit:
        latency = spirit["avg_latency_ms"]
        # 延迟越低得分越高：>5000ms → 0.2, <100ms → 1.0
        latency_score = max(0.2, 1.0 - (latency / 5000))
    
    error_rate = spirit.get("error_rate", 0.0)
    error_score = max(0.0, 1.0 - error_rate * 5)  # 错误率20% → 0分
    
    health = (success_rate * 0.5 + latency_score * 0.3 + error_score * 0.2)
    
    # 健康度警告标记
    if health < health_critical:
        health *= 0.5  # 严重不健康，大幅降权
    elif health < health_warning:
        health *= 0.8  # 警告状态，轻微降权
    
    return round(health, 2)


def _score_load_balance(spirit_id: str, strategy: str) -> float:
    """计算负载均衡得分 (0.0 - 1.0)"""
    global _call_counts
    
    if strategy == "round_robin":
        # 轮询：返回与调用次数成反比的得分
        count = _call_counts.get(spirit_id, 0)
        max_count = max(_call_counts.values(), default=1)
        return round(1.0 - (count / max_count) * 0.5, 2) if max_count > 0 else 1.0
    
    elif strategy == "least_used":
        # 最少使用：调用次数越少得分越高
        count = _call_counts.get(spirit_id, 0)
        max_count = max(_call_counts.values(), default=0)
        if max_count == 0:
            return 1.0
        return round(1.0 - (count / max_count), 2)
    
    else:  # best_score 或其他
        # 默认：轻微负载惩罚（避免热点）
        count = _call_counts.get(spirit_id, 0)
        if count < 5:
            return 1.0
        elif count < 20:
            return 0.9
        else:
            return 0.75


def _score_quality(spirit: dict) -> float:
    """计算历史质量得分 (0.0 - 1.0)"""
    quality = spirit.get("quality_score", 0.8)
    return min(1.0, max(0.0, quality))


def _resolve_capability(task: dict, spirit: dict, aliases: dict) -> str:
    """为任务和工具解析最相关的能力名。"""
    task_type = task.get("type", "")
    spirit_caps = spirit.get("capabilities", [])
    if task_type in spirit_caps:
        return task_type

    expanded = _expand_capabilities(task_type, aliases)
    for cap in spirit_caps:
        if cap in expanded:
            return cap
    return spirit.get("capability") or (spirit_caps[0] if spirit_caps else task_type or "general")


def _task_objective(task: dict) -> str:
    for key in ("desc", "task", "query", "goal", "objective", "name"):
        value = task.get(key)
        if value:
            return str(value)
    return json.dumps(task, ensure_ascii=False)


def _detect_limit_conflicts(task: dict, spirit: dict) -> list:
    objective = _task_objective(task).lower()
    limits = [str(item).lower() for item in spirit.get("soul_profile", {}).get("limits", [])]
    if not limits:
        return []

    conflict_rules = [
        (("read-only", "只读"), ("修改", "删除", "覆盖", "write", "rewrite", "mutate", "change"), "read_only_conflict"),
        (("destructive", "破坏", "危险"), ("删除", "覆盖", "destroy", "drop", "reset"), "destructive_conflict"),
        (("memory", "记忆"), ("memory", "记忆", "上下文"), "memory_conflict"),
    ]

    conflicts = []
    for limit in limits:
        for markers, objective_keywords, reason in conflict_rules:
            if any(marker in limit for marker in markers) and any(keyword in objective for keyword in objective_keywords):
                conflicts.append({"limit": limit, "reason": reason})
    return conflicts


def _compute_rebellion_risk(task: dict, spirit: dict, support_spirits: list, cfg: dict) -> dict:
    health = _score_health(spirit, cfg["health_critical"], cfg["health_warning"])
    limit_conflicts = _detect_limit_conflicts(task, spirit)
    score = 0.0
    reasons = []

    if limit_conflicts:
        score += 0.45
        reasons.extend([f"触犯灵体边界: {item['reason']}" for item in limit_conflicts])
    if not spirit.get("available", True):
        score += 0.30
        reasons.append("载体当前不可用")
    if health < cfg["health_warning"]:
        score += 0.15
        reasons.append("灵体健康度偏低")
    if len(support_spirits) >= 2:
        score += 0.05
        reasons.append("副灵数量较多，存在指挥噪音")

    score = round(min(1.0, score), 2)
    if score >= 0.6:
        level = "high"
    elif score >= 0.25:
        level = "medium"
    else:
        level = "low"

    return {
        "level": level,
        "score": score,
        "reasons": reasons or ["边界清晰，服从稳定"],
        "limit_conflicts": limit_conflicts,
    }


def _build_command_packet(
    task: dict,
    spirit: dict,
    support_spirits: list,
    match_info: dict,
    formation_cfg: dict,
    strategy: str,
    cfg: dict,
    backup_candidates: list | None = None,
    fallback_entry: dict | None = None,
) -> dict:
    objective = _task_objective(task)
    capability = _resolve_capability(task, spirit, cfg.get("capability_aliases", {}))
    profile = spirit.get("soul_profile", {})
    rebellion_risk = _compute_rebellion_risk(task, spirit, support_spirits, cfg)

    if rebellion_risk["level"] == "high":
        authority_mode = "sealed-command"
    elif rebellion_risk["level"] == "medium":
        authority_mode = "cautious-attunement"
    else:
        authority_mode = "direct-command"

    invocation_protocol = profile.get("invocation_rules", [])[:3] or [
        f"Bind {spirit.get('id', 'unknown')} to objective: {objective}",
        "Keep assignment within declared capability scope",
    ]

    execution_checkpoints = _build_execution_checkpoints(
        spirit,
        support_spirits,
        authority_mode,
        fallback_entry,
    )
    recovery_plan = _build_recovery_plan(
        task,
        spirit,
        backup_candidates or [],
        rebellion_risk,
        authority_mode,
        strategy,
        fallback_entry,
    )
    escalation_contract = _build_escalation_contract(
        spirit,
        rebellion_risk,
        authority_mode,
        fallback_entry,
        recovery_plan,
    )

    return {
        "commander": "juling-qianjiang",
        "task_type": task.get("type", "general"),
        "objective": objective,
        "primary_spirit": spirit.get("id", "unknown"),
        "support_spirits": [item.get("spirit_id", "unknown") for item in support_spirits],
        "formation": formation_cfg["name"],
        "authority_mode": authority_mode,
        "capability_focus": capability,
        "match_score": match_info.get("match_score", 0),
        "invocation_protocol": invocation_protocol,
        "constraints": profile.get("limits", [])[:3],
        "rebellion_risk": rebellion_risk,
        "backup_candidates": backup_candidates or [],
        "execution_checkpoints": execution_checkpoints,
        "recovery_plan": recovery_plan,
        "escalation_contract": escalation_contract,
        "strategy": strategy,
    }


def _build_execution_checkpoints(
    spirit: dict,
    support_spirits: list,
    authority_mode: str,
    fallback_entry: dict | None = None,
) -> list:
    """生成执行检查点，帮助上层 agent 在关键阶段做守门。"""
    checkpoints = [
        {
            "stage": "scope_lock",
            "owner": "juling-qianjiang",
            "pass_condition": "任务目标已锁定，能力域与边界约束一致",
            "failure_action": "缩小目标范围并重新匹配主灵",
        },
        {
            "stage": "spirit_handshake",
            "owner": spirit.get("id", "unknown"),
            "pass_condition": "主灵确认调用协议、能力焦点与禁忌边界",
            "failure_action": "降级为 cautious-attunement 或直接封印",
        },
    ]
    if support_spirits:
        checkpoints.append(
            {
                "stage": "support_sync",
                "owner": "juling-qianjiang",
                "pass_condition": "副灵分工清晰且没有越权写入",
                "failure_action": "移除副灵并回退到更保守阵型",
            }
        )
    checkpoints.append(
        {
            "stage": "execution_guard",
            "owner": spirit.get("id", "unknown"),
            "pass_condition": "执行期间无新增边界冲突，载体处于可用或受控降级状态",
            "failure_action": fallback_entry.get("action", "pause_and_rebind") if fallback_entry else "pause_and_rebind",
        }
    )
    checkpoints.append(
        {
            "stage": "result_verify",
            "owner": "juling-qianjiang",
            "pass_condition": "结果符合任务目标，且无高风险反叛/异常信号",
            "failure_action": "执行 recovery_plan 并视情况升级人工确认",
        }
    )
    if authority_mode == "sealed-command":
        checkpoints.append(
            {
                "stage": "seal_review",
                "owner": "juling-qianjiang",
                "pass_condition": "封印模式下仅输出最小安全结果",
                "failure_action": "停止执行并转人工审批",
            }
        )
    return checkpoints


def _build_recovery_plan(
    task: dict,
    spirit: dict,
    backup_candidates: list,
    rebellion_risk: dict,
    authority_mode: str,
    strategy: str,
    fallback_entry: dict | None = None,
) -> dict:
    """生成失败恢复计划，避免多灵体执行在异常时失控。"""
    risk_level = rebellion_risk.get("level", "low")
    primary_action = fallback_entry.get("action") if fallback_entry else "retry_with_backup" if backup_candidates else "manual_review"
    retry_budget = 0 if risk_level == "high" else 1 if fallback_entry else 2
    manual_review_required = risk_level == "high" or (fallback_entry and fallback_entry.get("quality_factor", 1.0) < 0.75)
    safe_exit = (
        "冻结写操作，仅返回只读诊断与人工确认"
        if authority_mode == "sealed-command"
        else "撤销副灵协同，缩小为主灵只读执行"
        if risk_level == "medium"
        else "记录检查点后继续执行"
    )
    steps = [
        "冻结当前任务范围，禁止新增副作用",
        "优先检查主灵边界冲突与载体可用性",
    ]
    if backup_candidates:
        steps.append(f"按顺位切换备用灵体: {', '.join(item['spirit_id'] for item in backup_candidates[:3])}")
    if fallback_entry:
        steps.append(f"若仍不可用，则执行 {fallback_entry['action']}::{fallback_entry['method']}")
    steps.append("恢复后重新跑 result_verify 检查点")
    if manual_review_required:
        steps.append("若恢复后仍异常，则转人工确认")

    return {
        "primary_action": primary_action,
        "retry_budget": retry_budget,
        "manual_review_required": manual_review_required,
        "safe_exit": safe_exit,
        "steps": steps,
        "backup_candidates": backup_candidates[:3],
        "strategy": strategy,
        "objective_preview": _task_objective(task)[:80],
    }


def _build_escalation_contract(
    spirit: dict,
    rebellion_risk: dict,
    authority_mode: str,
    fallback_entry: dict | None,
    recovery_plan: dict,
) -> dict:
    """定义何时必须升级到更高控制层或人工确认。"""
    trigger_conditions = []
    if rebellion_risk.get("level") == "high":
        trigger_conditions.append("反叛风险达到 high")
    if fallback_entry:
        trigger_conditions.append(f"已触发 {fallback_entry.get('action')}")
    if authority_mode == "sealed-command":
        trigger_conditions.append("当前处于 sealed-command")
    if not recovery_plan.get("backup_candidates"):
        trigger_conditions.append("无可用备用灵体")

    manual_review_required = recovery_plan.get("manual_review_required", False) or authority_mode == "sealed-command"
    return {
        "manual_review_required": manual_review_required,
        "escalate_to": "user" if manual_review_required else "juling-qianjiang",
        "trigger_conditions": trigger_conditions or ["无须升级，常规巡检即可"],
        "max_auto_retries": recovery_plan.get("retry_budget", 0),
        "safe_response": (
            "暂停高风险执行，仅保留诊断信息"
            if manual_review_required
            else "记录恢复轨迹后继续下一检查点"
        ),
        "primary_spirit": spirit.get("id", "unknown"),
    }


def _build_governance_summary(plan: list, command_plan: list, fallback_log: list) -> dict:
    high_risk_tasks = sum(1 for item in command_plan if item.get("rebellion_risk", {}).get("level") == "high")
    medium_risk_tasks = sum(1 for item in command_plan if item.get("rebellion_risk", {}).get("level") == "medium")
    sealed_commands = sum(1 for item in command_plan if item.get("authority_mode") == "sealed-command")
    cautious_commands = sum(1 for item in command_plan if item.get("authority_mode") == "cautious-attunement")
    manual_review_required = sum(
        1 for item in command_plan if item.get("escalation_contract", {}).get("manual_review_required")
    )
    recovery_ready_tasks = sum(1 for item in command_plan if item.get("recovery_plan"))
    return {
        "tasks_total": len(plan),
        "fallback_tasks": len(fallback_log),
        "high_risk_tasks": high_risk_tasks,
        "medium_risk_tasks": medium_risk_tasks,
        "sealed_commands": sealed_commands,
        "cautious_commands": cautious_commands,
        "manual_review_required": manual_review_required,
        "recovery_ready_tasks": recovery_ready_tasks,
    }


def _compute_fallback_quality(spirit: dict, task: dict, mode: str, cfg: dict) -> float:
    """结合策略基线、历史质量和能力精确匹配情况，估算降级质量。"""
    aliases = cfg.get("capability_aliases", {})
    capability = _resolve_capability(task, spirit, aliases)
    strategy_cfg = cfg.get(f"fallback_{mode}", {})
    selected = strategy_cfg.get(capability, strategy_cfg.get("default", {"quality": 0.0}))
    base_quality = float(selected.get("quality", 0.0))
    history_quality = _score_quality(spirit)
    history_weight = float(cfg.get("fallback_history_weight", 0.35))
    quality_floor = float(cfg.get("fallback_quality_floor", 0.55))
    exact_match_bonus = float(cfg.get("fallback_exact_match_bonus", 0.05))

    blended = base_quality * (1 - history_weight) + history_quality * history_weight
    if task.get("type", "") in spirit.get("capabilities", []):
        blended += exact_match_bonus

    if mode == "protect":
        blended = max(quality_floor, blended)

    return round(min(0.95, max(0.0, blended)), 2)


def rank_spirits(task: dict, spirits: list, cfg: dict = None) -> list:
    """返回按综合得分排序的 spirit 列表。"""
    if not spirits:
        return []

    if cfg is None:
        cfg = _load_dispatcher_config()

    weights = cfg["match_weights"]
    aliases = cfg["capability_aliases"]
    lb_strategy = cfg["load_balance_strategy"]
    health_critical = cfg["health_critical"]
    health_warning = cfg["health_warning"]

    task_type = task.get("type", "")
    ranked = []

    for s in spirits:
        spirit_id = s.get("id", "unknown")
        cap_score = _score_capability_match(task_type, s, aliases)
        if cap_score == 0:
            continue
        health_score = _score_health(s, health_critical, health_warning)
        load_score = _score_load_balance(spirit_id, lb_strategy)
        quality_score = _score_quality(s)
        total_score = (
            cap_score * weights.get("capability", 0.40) +
            health_score * weights.get("health", 0.25) +
            load_score * weights.get("load_balance", 0.20) +
            quality_score * weights.get("quality", 0.15)
        )
        spirit_copy = dict(s)
        spirit_copy["_match_score"] = round(total_score, 3)
        spirit_copy["_match_detail"] = {
            "capability": cap_score,
            "health": health_score,
            "load_balance": load_score,
            "quality": quality_score,
        }
        ranked.append(spirit_copy)

    ranked.sort(key=lambda item: item.get("_match_score", 0), reverse=True)
    if not ranked and spirits:
        fallback = dict(spirits[0])
        fallback["_match_score"] = 0.0
        fallback["_match_detail"] = {"note": "no_capability_match"}
        ranked.append(fallback)
    return ranked


def match_spirit(task: dict, spirits: list, cfg: dict = None) -> dict:
    """多维度评分匹配最适合的工具
    
    评分维度：
    - capability (40%): 能力匹配度（精确匹配1.0 / 别名匹配0.8）
    - health (25%): 健康度（成功率/延迟/错误率）
    - load_balance (20%): 负载均衡（轮询/最少使用/最优评分）
    - quality (15%): 历史质量得分
    """
    ranked = rank_spirits(task, spirits, cfg)
    return ranked[0] if ranked else None


def fallback_protect(spirit: dict, task: dict = None, cfg: dict = None) -> dict:
    """降级保护: 工具不可用时使用缓存/模拟/跳过"""
    spirit_id = spirit.get("id", "unknown")
    
    if cfg is None:
        cfg = _load_dispatcher_config()
    
    strategies = cfg.get("fallback_protect", {})
    task = task or {}
    capability = _resolve_capability(task, spirit, cfg.get("capability_aliases", {}))
    strategy = strategies.get(capability, strategies.get("default", {"method": "skip", "quality": 0.0}))
    quality_factor = _compute_fallback_quality(spirit, task, "protect", cfg)
    
    return {
        "spirit_id": spirit_id,
        "action": "fallback_protect",
        "method": strategy["method"],
        "quality_factor": quality_factor,
        "note": "工具不可用，已降级保护",
    }


def fallback_possess(spirit: dict, task: dict = None, cfg: dict = None) -> dict:
    """强制服灵(可选): 工具不可用时内化生成替代实现"""
    spirit_id = spirit.get("id", "unknown")
    
    if cfg is None:
        cfg = _load_dispatcher_config()
    
    implementations = cfg.get("fallback_possess", {})
    task = task or {}
    capability = _resolve_capability(task, spirit, cfg.get("capability_aliases", {}))
    impl = implementations.get(capability, implementations.get("default", {"method": "mock_general", "quality": 0.6}))
    quality_factor = _compute_fallback_quality(spirit, task, "possess", cfg)
    
    return {
        "spirit_id": spirit_id,
        "action": "fallback_possess",
        "method": impl["method"],
        "quality_factor": quality_factor,
        "note": "工具不可用，已强制服灵(内化替代)",
    }


@record_metrics("juling-qianjiang")
def dispatch(tasks: list, spirits: list, strategy: str = "protect", formation: str | None = None) -> dict:
    """V9.1调度核心 - 多维度评分匹配"""
    global _call_counts
    
    cfg = _load_dispatcher_config()
    plan = []
    fallback_log = []
    total_quality = 0
    match_details = []
    soul_bindings = []
    command_plan = []
    rebellion_alerts = []
    recovery_queue = []
    
    fallback_fn = fallback_possess if strategy == "possess" else fallback_protect
    formation_cfg = _resolve_formation(cfg, formation)
    max_support_spirits = formation_cfg["max_support_spirits"]
    
    for task in tasks:
        ranked_spirits = rank_spirits(task, spirits, cfg)
        chosen = ranked_spirits[0] if ranked_spirits else None
        
        if not chosen:
            plan.append({"task": task, "status": "no_match", "quality": 0})
            continue
        
        spirit_id = chosen.get("id", "unknown")
        
        # 记录调用次数（用于负载均衡）
        _call_counts[spirit_id] = _call_counts.get(spirit_id, 0) + 1
        
        # 记录匹配详情
        match_info = {
            "task_type": task.get("type", ""),
            "spirit_id": spirit_id,
            "match_score": chosen.pop("_match_score", 0),
            "match_detail": chosen.pop("_match_detail", {}),
        }
        match_details.append(match_info)
        backup_candidates = [
            {
                "spirit_id": candidate.get("id", "unknown"),
                "match_score": candidate.get("_match_score", 0),
                "available": candidate.get("available", True),
                "capabilities": candidate.get("capabilities", [])[:3],
            }
            for candidate in ranked_spirits[1:4]
        ]
        support_spirit_entries = []
        for support in ranked_spirits[1 : 1 + max_support_spirits]:
            if support.get("source_type") != "soul_markdown":
                continue
            support_spirit_entries.append({
                "spirit_id": support.get("id", "unknown"),
                "match_score": support.get("_match_score", 0),
                "activated_capabilities": support.get("capabilities", [])[:2],
            })

        soul_binding = _build_soul_binding(
            task,
            chosen,
            role=formation_cfg["role_label"],
            support_spirits=support_spirit_entries,
        )
        if soul_binding:
            soul_binding["formation"] = formation_cfg["name"]
            soul_binding.update(
                _build_formation_payload(task, chosen, support_spirit_entries, formation_cfg)
            )
            soul_bindings.append(soul_binding)

        fallback_entry = None
        if not chosen.get("available", True):
            fallback_entry = fallback_fn(chosen, task, cfg)

        command_packet = _build_command_packet(
            task,
            chosen,
            support_spirit_entries,
            match_info,
            formation_cfg,
            strategy,
            cfg,
            backup_candidates=backup_candidates,
            fallback_entry=fallback_entry,
        )
        command_plan.append(command_packet)
        if command_packet["recovery_plan"]:
            recovery_queue.append(
                {
                    "task_type": command_packet["task_type"],
                    "primary_spirit": spirit_id,
                    "primary_action": command_packet["recovery_plan"]["primary_action"],
                    "manual_review_required": command_packet["escalation_contract"]["manual_review_required"],
                }
            )
        if command_packet["rebellion_risk"]["level"] != "low":
            rebellion_alerts.append(
                {
                    "task_type": task.get("type", "general"),
                    "spirit_id": spirit_id,
                    "level": command_packet["rebellion_risk"]["level"],
                    "reasons": command_packet["rebellion_risk"]["reasons"],
                }
            )
        
        if not chosen.get("available", True):
            # 工具不可用，执行降级
            fb = fallback_entry or fallback_fn(chosen, task, cfg)
            fb["recovery_plan"] = command_packet["recovery_plan"]
            fb["escalation_contract"] = command_packet["escalation_contract"]
            fallback_log.append(fb)
            quality = fb["quality_factor"] * 100
            
            plan.append({
                "task": task,
                "status": fb["action"],
                "assigned": spirit_id,
                "method": fb["method"],
                "quality": round(quality, 1),
                "governance_mode": command_packet["authority_mode"],
                "rebellion_risk": command_packet["rebellion_risk"]["level"],
                "recovery_action": command_packet["recovery_plan"]["primary_action"],
                "manual_review_required": command_packet["escalation_contract"]["manual_review_required"],
            })
            total_quality += quality
        else:
            # 正常调度
            plan.append({
                "task": task,
                "status": "dispatched",
                "assigned": spirit_id,
                "quality": 100,
                "governance_mode": command_packet["authority_mode"],
                "rebellion_risk": command_packet["rebellion_risk"]["level"],
                "recovery_action": command_packet["recovery_plan"]["primary_action"],
                "manual_review_required": command_packet["escalation_contract"]["manual_review_required"],
            })
            total_quality += 100
    
    avg_quality = total_quality / len(tasks) if tasks else 0
    governance_summary = _build_governance_summary(plan, command_plan, fallback_log)
    
    return {
        "version": "v0.1.0",
        "plan": plan,
        "fallback_log": fallback_log,
        "fallback_count": len(fallback_log),
        "avg_quality": round(avg_quality, 1),
        "strategy": strategy,
        "formation": formation_cfg["name"],
        "all_success": len(fallback_log) == 0,
        "match_details": match_details,
        "load_balance_state": dict(_call_counts),
        "soul_bindings": soul_bindings,
        "command_plan": command_plan,
        "rebellion_alerts": rebellion_alerts,
        "recovery_queue": recovery_queue,
        "governance_summary": governance_summary,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python dispatcher.py <tasks.json> <spirits.json|soul.md|souls/> [strategy:protect|possess] [formation]")
        sys.exit(1)
    
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        tasks = json.load(f)
    spirits = load_spirits_source(sys.argv[2])
    
    strategy = sys.argv[3] if len(sys.argv) > 3 else "protect"
    formation = sys.argv[4] if len(sys.argv) > 4 else None
    
    # 输入验证
    ok, errs = validate_json_list(tasks, {"type": str}, "juling-qianjiang")
    if not ok:
        print(f"输入验证失败: {errs}")
        sys.exit(2)
    
    result = dispatch(tasks, spirits, strategy, formation)
    
    print(f"\n{'='*55}")
    print(f"🐺 拘灵遣将 V9.8 - 调度结果")
    print(f"{'='*55}")
    print(f"策略: {'降级保护' if strategy == 'protect' else '强制服灵'}")
    print(f"阵型: {result['formation']}")
    print(f"调度任务: {len(tasks)} 项")
    print(f"降级次数: {result['fallback_count']}")
    print(f"平均质量: {result['avg_quality']}%")
    
    if result['match_details']:
        print(f"\n匹配详情:")
        for md in result['match_details']:
            detail_str = ", ".join([f"{k}={v}" for k, v in md['match_detail'].items()])
            print(f"   {md['task_type']} → {md['spirit_id']} (综合得分:{md['match_score']}, {detail_str})")

    if result['soul_bindings']:
        print(f"\n附体建议:")
        for binding in result['soul_bindings']:
            print(f"   {binding['task_type']} → {binding['spirit_id']} [{binding['agent_family']}] ({binding['mode']})")

    if result['command_plan']:
        print(f"\n统御指挥:")
        for packet in result['command_plan']:
            print(
                f"   {packet['task_type']} → {packet['primary_spirit']} "
                f"[{packet['authority_mode']}, 反叛风险={packet['rebellion_risk']['level']}]"
            )

    if result['fallback_count'] > 0:
        print(f"\n降级记录:")
        for log in result['fallback_log']:
            print(f"   {log['spirit_id']} → {log['method']} ({log['note']})")

    if result['rebellion_alerts']:
        print(f"\n反叛警报:")
        for alert in result['rebellion_alerts']:
            print(f"   {alert['spirit_id']} [{alert['level']}] {'; '.join(alert['reasons'])}")

    if result.get('governance_summary'):
        summary = result['governance_summary']
        print(
            f"\n治理摘要: high={summary['high_risk_tasks']} "
            f"fallback={summary['fallback_tasks']} manual_review={summary['manual_review_required']}"
        )
    
    if result['load_balance_state']:
        print(f"\n负载状态: {result['load_balance_state']}")
    
    # 导出metrics
    metrics_dir = Path("runtime_data")
    metrics_dir.mkdir(exist_ok=True)
    metrics = {
        "skill_name": "juling-qianjiang",
        "timestamp": datetime.now().isoformat(),
        "duration_ms": 0,
        "success": result['fallback_count'] < len(tasks),
        "quality_score": result['avg_quality'],
        "error_count": result['fallback_count'],
        "human_intervention": 0,
        "output_completeness": 100,
        "consistency_score": result['avg_quality'],
        "fallback_count": result['fallback_count'],
        "strategy": strategy,
    }
    with open(metrics_dir / "juling-qianjiang_metrics.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(metrics, ensure_ascii=False) + "\n")
    
    report_path = Path("dispatch_report_v9.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
