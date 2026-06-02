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
from typing import Optional

# 运行时指标收集
try:
    from under_one.config import get_skill_config
    from under_one.metrics import record_metrics, resolve_runtime_data_dir
    from under_one.validation import validate_json_list
except ImportError:
    SKILLS_ROOT = Path(__file__).resolve().parent.parent.parent
    if str(SKILLS_ROOT) not in sys.path:
        sys.path.insert(0, str(SKILLS_ROOT))
    from metrics_compat import record_metrics, resolve_runtime_data_dir

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


def _build_soul_binding(task: dict, spirit: dict, role: str = "primary", support_spirits: Optional[list] = None) -> Optional[dict]:
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


def _resolve_formation(cfg: dict, formation: Optional[str] = None) -> dict:
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
    backup_candidates: Optional[list] = None,
    fallback_entry: Optional[dict] = None,
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
    fallback_entry: Optional[dict] = None,
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
    fallback_entry: Optional[dict] = None,
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
    fallback_entry: Optional[dict],
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


# ══════════════════════════════════════════════════════════════
# V9.9 灵契：服灵永久强化 + 灵体弱点识别
# ══════════════════════════════════════════════════════════════
_SOUL_PACTS = {}            # {"spirit_id::task_type": success_count}
_SOUL_PACT_STEP = 0.03      # 每次成功服灵的精度增益
_SOUL_PACT_CAP = 0.15       # 灵契加成上限（永久强化但有顶）


def _soul_pact_key(spirit_id, task_type):
    return f"{spirit_id}::{task_type or 'general'}"


def record_soul_pact(spirit_id, task_type, success=True):
    """服灵：一次成功使用后积累灵契经验值，永久提升匹配精度。

    呼应漫画"服灵=吃掉灵获得永久性强化"。仅记录成功（失败不削弱已有灵契）。
    Returns: 当前累计成功次数。
    """
    key = _soul_pact_key(spirit_id, task_type)
    if not success:
        return _SOUL_PACTS.get(key, 0)
    _SOUL_PACTS[key] = _SOUL_PACTS.get(key, 0) + 1
    return _SOUL_PACTS[key]


def soul_pact_bonus(spirit_id, task_type):
    """根据累计灵契经验值返回匹配加成（0 ~ _SOUL_PACT_CAP）。"""
    count = _SOUL_PACTS.get(_soul_pact_key(spirit_id, task_type), 0)
    return round(min(_SOUL_PACT_CAP, count * _SOUL_PACT_STEP), 3)


def reset_soul_pacts():
    """清空内存灵契（测试/重置用）。"""
    _SOUL_PACTS.clear()


def identify_spirit_weakness(spirit, required_capabilities=None):
    """灵体弱点识别（呼应"灵体本质上是不完整的"）。

    从能力覆盖、可用性、历史质量三方面刻画灵体的不完整之处，便于扬长避短。
    """
    caps = set(spirit.get("capabilities", []) or [])
    required = set(required_capabilities or [])
    weaknesses = []

    missing = sorted(required - caps)
    if missing:
        weaknesses.append({"type": "capability_gap", "detail": missing,
                           "note": "缺失所需能力，需请其他灵补位"})
    if not spirit.get("available", True):
        weaknesses.append({"type": "unavailable", "detail": spirit.get("id", "unknown"),
                           "note": "当前不可用，需降级或服灵替代"})
    q = spirit.get("quality_score")
    if isinstance(q, (int, float)) and not isinstance(q, bool) and q < 0.6:
        weaknesses.append({"type": "low_quality", "detail": q,
                           "note": "历史质量偏低，反叛/失控风险较高"})
    if not caps:
        weaknesses.append({"type": "no_capability", "detail": spirit.get("id", "unknown"),
                           "note": "未声明任何能力，本质高度不完整"})

    coverage = 1.0 if not required else round(len(required & caps) / len(required), 3)
    return {
        "spirit_id": spirit.get("id", "unknown"),
        "completeness": coverage,
        "weaknesses": weaknesses,
        "is_complete": not weaknesses,
        "lore": "灵体本质不完整，识别弱点方能扬长避短" if weaknesses else "暂未发现明显弱点",
    }


def extract_soul_essence(spirit: dict) -> dict:
    """服灵·抽魂：抽取一个 agent/expert 灵魂的本质。

    呼应漫画"拘灵遣将"的核心——不是简单调度，而是把灵的本质（身份、
    系统提示/人设、能力边界、行为模式）抽出来为己所用。soul.md 来源抽取最完整，
    普通灵体退化抽取。
    """
    profile = spirit.get("soul_profile", {}) or {}
    caps = sorted(dict.fromkeys(spirit.get("capabilities", []) or []))
    traits = list(profile.get("traits", []) or [])
    limits = list(profile.get("limits", []) or [])
    invocation = list(profile.get("invocation_rules", []) or [])
    summary = (profile.get("summary") or spirit.get("summary") or "").strip()
    return {
        "spirit_id": spirit.get("id", "unknown"),
        "agent_family": spirit.get("agent_family", "generic"),
        "identity": {"summary": summary[:240], "traits": traits[:8]},
        "system_prompt_digest": summary[:240],
        "capabilities": caps,
        "boundaries": {"limits": limits, "invocation_rules": invocation},
        "behavior_patterns": traits[:8],
        "essence_quality": round(float(spirit.get("quality_score", 0.0) or 0.0), 3),
        "extractable": spirit.get("source_type") == "soul_markdown" or bool(caps),
    }


def aggregate_souls(spirits: list) -> dict:
    """服灵·聚魂：把多个 agent/expert 的灵魂聚合成"魂库"。

    建立能力→来源灵体的倒排索引（provenance），合并能力并集与边界并集，
    检测"某灵能力恰为他灵明令禁忌"的魂相冲。呼应"魂库"——抽取的灵魂归档备役。
    """
    essences = [extract_soul_essence(s) for s in (spirits or [])]
    capability_index = {}
    boundary_union = []
    seen_boundaries = set()
    for ess in essences:
        for cap in ess["capabilities"]:
            capability_index.setdefault(cap, []).append(ess["spirit_id"])
        for limit in ess["boundaries"]["limits"]:
            key = limit.strip().lower()
            if key and key not in seen_boundaries:
                seen_boundaries.add(key)
                boundary_union.append(limit)
    unified = sorted(capability_index.keys())
    conflicts = []
    for cap in unified:
        cap_low = cap.lower()
        for limit in boundary_union:
            if cap_low and cap_low in limit.lower():
                conflicts.append({
                    "capability": cap,
                    "violates_boundary": limit,
                    "provided_by": capability_index[cap],
                })
                break
    return {
        "soul_count": len(essences),
        "souls": [e["spirit_id"] for e in essences],
        "unified_capabilities": unified,
        "capability_index": capability_index,
        "boundary_union": boundary_union,
        "conflicts": conflicts,
        "coverage": len(unified),
        "lore": "聚魂入库：抽取诸灵之本质归档备役，能力并集即'拘灵遣将'之兵备",
    }


def absorb_souls(host_id: str, spirits: list, will_not: Optional[list] = None) -> dict:
    """服灵·吞并：以一个灵为宿主，吞并其余灵的能力为己所用。

    呼应漫画"服灵=吃掉灵获得永久强化"。被天条(will_not)禁止、或与宿主自身禁忌
    冲突的能力不会被吞并，只列入 rejected；吞并越多、冲突越多，反噬风险越高。
    """
    will_not_low = [str(w).lower() for w in (will_not or []) if str(w).strip()]
    spirits = spirits or []
    by_id = {s.get("id", f"spirit-{i}"): s for i, s in enumerate(spirits)}
    host = by_id.get(host_id)
    if host is None and spirits:
        host = max(spirits, key=lambda s: s.get("quality_score", 0) or 0)
        host_id = host.get("id", "host")
    if host is None:
        return {
            "host": None, "absorbed": [], "absorbed_count": 0, "rejected": [],
            "composite_capabilities": [], "provenance": {},
            "backlash_risk": {"level": "low", "score": 0.0, "note": "无灵可吞"},
            "lore": "无灵可吞",
        }

    host_ess = extract_soul_essence(host)
    host_caps = set(host_ess["capabilities"])
    host_limits = [l.lower() for l in host_ess["boundaries"]["limits"]]

    absorbed, rejected, provenance = [], [], {}
    for s in spirits:
        if s.get("id") == host_id:
            continue
        ess = extract_soul_essence(s)
        for cap in ess["capabilities"]:
            if cap in host_caps:
                continue
            cap_low = cap.lower()
            forbidden_by = next((w for w in will_not_low if w in cap_low), None)
            conflict = next((l for l in host_limits if l and (l in cap_low or cap_low in l)), None)
            if forbidden_by:
                rejected.append({"capability": cap, "from": ess["spirit_id"],
                                 "reason": "天条禁止(will_not)", "rule": forbidden_by})
            elif conflict:
                rejected.append({"capability": cap, "from": ess["spirit_id"],
                                 "reason": "与宿主禁忌冲突", "rule": conflict})
            else:
                host_caps.add(cap)
                absorbed.append({"capability": cap, "from": ess["spirit_id"]})
                provenance[cap] = ess["spirit_id"]

    score = min(1.0, len(absorbed) * 0.08 + len(rejected) * 0.12)
    level = "high" if score >= 0.6 else "medium" if score >= 0.3 else "low"
    return {
        "host": host_id,
        "absorbed": absorbed,
        "absorbed_count": len(absorbed),
        "rejected": rejected,
        "composite_capabilities": sorted(host_caps),
        "provenance": provenance,
        "backlash_risk": {
            "level": level,
            "score": round(score, 3),
            "note": "吞并越多、冲突越多，人格越不稳，反噬风险越高" if level != "low" else "吞并稳健，反噬可控",
        },
        "lore": "服灵·吞并：化他灵之能为己用，然天条所禁者不可食，食之必反噬",
    }


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
        pact_bonus = soul_pact_bonus(spirit_id, task_type)
        total_score = (
            cap_score * weights.get("capability", 0.40) +
            health_score * weights.get("health", 0.25) +
            load_score * weights.get("load_balance", 0.20) +
            quality_score * weights.get("quality", 0.15)
        ) + pact_bonus
        spirit_copy = dict(s)
        spirit_copy["_match_score"] = round(total_score, 3)
        spirit_copy["_match_detail"] = {
            "capability": cap_score,
            "health": health_score,
            "load_balance": load_score,
            "quality": quality_score,
            "soul_pact": pact_bonus,
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
def dispatch(tasks: list, spirits: list, strategy: str = "protect", formation: Optional[str] = None) -> dict:
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
        "version": "v9.9",
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
        "soul_registry": aggregate_souls(spirits),
        "command_plan": command_plan,
        "rebellion_alerts": rebellion_alerts,
        "recovery_queue": recovery_queue,
        "governance_summary": governance_summary,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python dispatcher.py <tasks.json> <spirits.json|soul.md|souls/> [strategy:protect|possess] [formation] [--absorb <host_id>]")
        sys.exit(1)

    # 解析 --absorb <host_id>（服灵·吞并）
    argv = list(sys.argv)
    absorb_host = None
    if "--absorb" in argv:
        idx = argv.index("--absorb")
        absorb_host = argv[idx + 1] if idx + 1 < len(argv) else ""
        del argv[idx:idx + 2]

    with open(argv[1], "r", encoding="utf-8") as f:
        tasks = json.load(f)
    spirits = load_spirits_source(argv[2])

    strategy = argv[3] if len(argv) > 3 else "protect"
    formation = argv[4] if len(argv) > 4 else None
    
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

    registry = result.get('soul_registry', {})
    if registry.get('soul_count'):
        print(
            f"\n魂库(聚魂): {registry['soul_count']} 灵 · 能力并集 {registry['coverage']} 项 · "
            f"魂相冲 {len(registry.get('conflicts', []))} 处"
        )

    if absorb_host is not None:
        absorption = absorb_souls(absorb_host, spirits, will_not=None)
        result["absorption"] = absorption
        print(
            f"\n服灵·吞并 → 宿主 {absorption['host']}: 吞并 {absorption['absorbed_count']} 能力, "
            f"拒食 {len(absorption['rejected'])} 项, 反噬风险 {absorption['backlash_risk']['level']}"
        )

    if result.get('governance_summary'):
        summary = result['governance_summary']
        print(
            f"\n治理摘要: high={summary['high_risk_tasks']} "
            f"fallback={summary['fallback_tasks']} manual_review={summary['manual_review_required']}"
        )
    
    if result['load_balance_state']:
        print(f"\n负载状态: {result['load_balance_state']}")
    
    # 导出metrics
    metrics_dir = resolve_runtime_data_dir()
    metrics_dir.mkdir(parents=True, exist_ok=True)
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
