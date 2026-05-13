#!/usr/bin/env python3
"""
器名: 符箓生成器 (Fu Talisman Generator) V5.8
用途: 根据任务描述或结构化任务规格生成符箓模板、检测冲突、输出执行拓扑
输入: 任务描述字符串 | 结构化 JSON 规格
输出: JSON {talisman_list, topology, execution_plan, ritual_summary}
V5.8升级:
- 支持结构化任务规格（task / talisman_contract / risk_contract / execution_contract）
- 新增编排模式：quick-cast / balanced-array / full-ritual
- 输出 ritual_intent / ritual_summary / risk_alignment
- 保持 V5.x 字符串输入向后兼容
"""

import json
import sys
import re
from pathlib import Path

# 运行时指标收集
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from metrics_collector import record_metrics
except ImportError:
    def record_metrics(*args, **kwargs):
        def decorator(f): return f
        return decorator

try:
    from _skill_config import get_skill_config
except ImportError:
    def get_skill_config(skill_name, key=None, default=None):
        return default


FU_TEMPLATES = {
    "analysis": {
        "id": "analysis-v5.0",
        "type": "分析箓",
        "goal": "信息解析与提取",
        "input_ports": [{"type": "raw_text", "required": True}],
        "output_ports": [{"type": "structured_data", "format": "json"}],
        "constraints": ["保留原始语义", "标注置信度"],
        "avg_sla": 10,
    },
    "creation": {
        "id": "creation-v5.0",
        "type": "创作箓",
        "goal": "内容生成与改写",
        "input_ports": [{"type": "structured_data", "required": True}],
        "output_ports": [{"type": "text", "format": "markdown"}],
        "constraints": ["符合目标风格", "字数可控"],
        "avg_sla": 20,
    },
    "verification": {
        "id": "verification-v5.0",
        "type": "验证箓",
        "goal": "逻辑检查与确认",
        "input_ports": [{"type": "text", "required": True}],
        "output_ports": [{"type": "boolean", "format": "pass/fail+reason"}],
        "constraints": ["不修改内容", "仅校验"],
        "avg_sla": 15,
    },
    "transformation": {
        "id": "transformation-v5.0",
        "type": "转换箓",
        "goal": "格式与结构变换",
        "input_ports": [{"type": "any", "required": True}],
        "output_ports": [{"type": "any", "format": "target_format"}],
        "constraints": ["无损转换", "保留完整语义"],
        "avg_sla": 10,
    },
    "retrieval": {
        "id": "retrieval-v5.0",
        "type": "检索箓",
        "goal": "信息查找与关联",
        "input_ports": [{"type": "query", "required": True}],
        "output_ports": [{"type": "list", "format": "results"}],
        "constraints": ["来源可追溯", "去重"],
        "avg_sla": 15,
    },
    "decision": {
        "id": "decision-v5.0",
        "type": "决策箓",
        "goal": "方案评估与选择",
        "input_ports": [{"type": "options", "required": True}],
        "output_ports": [{"type": "ranked_list", "format": "json"}],
        "constraints": ["多维度评估", "透明评分"],
        "avg_sla": 15,
    },
}

DIMENSION_KEYWORDS = {
    "analysis": ["分析", "提取", "解析", "拆解", "关键词", "情感"],
    "creation": ["写", "生成", "创建", "改写", "润色", "翻译"],
    "verification": ["检查", "验证", "确认", "校对", "测试", "审查"],
    "transformation": ["转换", "格式化", "重组", "变成", "转义"],
    "retrieval": ["搜索", "查找", "查询", "检索", "获取"],
    "decision": ["对比", "评估", "选择", "排序", "优先级"],
}

CONSTRAINT_KEYWORDS = {
    "高危": ["删除", "覆盖", "资金", "医疗", "法律", "生产环境"],
    "中危": ["发布", "发送", "配置", "权限", "变更"],
}

# V5.2: 默认拓扑排序顺序（可被配置覆盖）
DEFAULT_ORDER_MAP = {
    "检索箓": 1, "分析箓": 2, "决策箓": 3,
    "创作箓": 4, "验证箓": 5, "转换箓": 6,
}

CAPABILITY_MAP = {
    "analysis": "data",
    "creation": "write",
    "verification": "review",
    "transformation": "transform",
    "retrieval": "search",
    "decision": "planning",
}


class FuGenerator:
    def __init__(self, task_desc):
        self.raw_task = task_desc
        self.spec = self._normalize_task_spec(task_desc)
        self.task = self.spec["description"]
        self.sections = self.spec["sections"]
        self.fu_list = []
        self.conflicts = []
        self.topology = []
        self.curse_level = "low"
        self.mode_cfg = {}
        # V5.2: 从 under-one.yaml 加载配置
        self._load_config()

    def _normalize_task_spec(self, task_desc):
        """兼容字符串任务描述与结构化任务规格。"""
        if isinstance(task_desc, dict):
            task_block = task_desc.get("task", {})
            talisman_contract = task_desc.get("talisman_contract", {})
            risk_contract = task_desc.get("risk_contract", {})
            execution_contract = task_desc.get("execution_contract", {})
            if isinstance(task_block, str):
                description = task_block
                task_block = {"description": task_block}
            else:
                description = task_block.get("description") or task_desc.get("description", "")
            return {
                "description": description,
                "orchestration_mode": (
                    task_desc.get("orchestration_mode")
                    or execution_contract.get("orchestration_mode")
                    or "balanced-array"
                ),
                "sections": {
                    "task": task_block,
                    "talisman_contract": talisman_contract,
                    "risk_contract": risk_contract,
                    "execution_contract": execution_contract,
                },
            }

        return {
            "description": task_desc if isinstance(task_desc, str) else "",
            "orchestration_mode": "balanced-array",
            "sections": {
                "task": {"description": task_desc if isinstance(task_desc, str) else ""},
                "talisman_contract": {},
                "risk_contract": {},
                "execution_contract": {},
            },
        }

    def _load_config(self):
        """V5.2: 从配置加载参数，未配置时回退到默认值"""
        cfg = get_skill_config("tongtianlu", default={})

        # 维度关键词
        dim_cfg = cfg.get("dimension_keywords", {})
        self.DIMENSION_KEYWORDS = {k: v for k, v in DIMENSION_KEYWORDS.items()}
        for k, v in dim_cfg.items():
            if k in self.DIMENSION_KEYWORDS:
                self.DIMENSION_KEYWORDS[k] = v

        # 禁咒关键词
        constraint_cfg = cfg.get("constraint_keywords", {})
        self.CONSTRAINT_KEYWORDS = {k: v for k, v in CONSTRAINT_KEYWORDS.items()}
        if "high_risk" in constraint_cfg:
            self.CONSTRAINT_KEYWORDS["高危"] = constraint_cfg["high_risk"]
        if "medium_risk" in constraint_cfg:
            self.CONSTRAINT_KEYWORDS["中危"] = constraint_cfg["medium_risk"]

        # SLA 预算阈值
        sla_cfg = cfg.get("sla_budget", {})
        self.SLA_WARNING = sla_cfg.get("warning", 90)
        self.SLA_CRITICAL = sla_cfg.get("critical", 120)

        # 拓扑顺序
        order_cfg = cfg.get("order_map", {})
        self.ORDER_MAP = {k: v for k, v in DEFAULT_ORDER_MAP.items()}
        for k, v in order_cfg.items():
            self.ORDER_MAP[k] = v

        mode_cfg = cfg.get("orchestration_modes", {}).get("modes", {})
        self.ORCHESTRATION_MODES = {
            "quick-cast": {
                "max_talismans": 2,
                "include_verification_tail": False,
                "prefer_parallel": True,
                "topology_strategy": "minimal-chain",
                "intent": "rapid decomposition",
            },
            "balanced-array": {
                "max_talismans": 4,
                "include_verification_tail": False,
                "prefer_parallel": True,
                "topology_strategy": "balanced-lattice",
                "intent": "balanced orchestration",
            },
            "full-ritual": {
                "max_talismans": 6,
                "include_verification_tail": True,
                "prefer_parallel": False,
                "topology_strategy": "full-stack ritual",
                "intent": "full-stack execution lattice",
            },
        }
        for mode_name, values in mode_cfg.items():
            if mode_name in self.ORCHESTRATION_MODES:
                self.ORCHESTRATION_MODES[mode_name].update(values)

    @record_metrics("tongtian-lu")
    def generate(self):
        self._detect_dimensions()
        self._apply_contract_preferences()
        self._apply_orchestration_mode()
        self._detect_curse()
        self._check_risk_budget()
        self._detect_conflicts()
        self._build_topology()
        self._check_sequence_conflicts()
        return self._output()

    def _resolve_mode(self):
        mode_name = self.spec.get("orchestration_mode", "balanced-array")
        mode = self.ORCHESTRATION_MODES.get(mode_name, self.ORCHESTRATION_MODES["balanced-array"]).copy()
        mode["name"] = mode_name if mode_name in self.ORCHESTRATION_MODES else "balanced-array"
        return mode

    def _append_talisman(self, dim, reason):
        if dim not in FU_TEMPLATES:
            return
        if any(fu.get("dimension") == dim for fu in self.fu_list):
            return
        fu = FU_TEMPLATES[dim].copy()
        fu["dimension"] = dim
        fu["activation_reason"] = reason
        self.fu_list.append(fu)

    def _detect_dimensions(self):
        """检测任务维度，生成对应符箓"""
        detected = []
        for dim, keywords in self.DIMENSION_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in self.task]
            if matched:
                detected.append(dim)
                self._append_talisman(dim, f"keyword:{matched[0]}")
        if not detected:
            self._append_talisman("analysis", "fallback:default-analysis")

    def _apply_contract_preferences(self):
        talisman_contract = self.sections.get("talisman_contract", {})
        preferred = talisman_contract.get("preferred_types", [])
        blocked = set(talisman_contract.get("blocked_types", []))

        if isinstance(preferred, list):
            for dim in preferred:
                self._append_talisman(dim, "contract:preferred")

        if blocked:
            self.fu_list = [fu for fu in self.fu_list if fu.get("dimension") not in blocked]

        if not self.fu_list:
            self._append_talisman("analysis", "fallback:post-filter")

    def _apply_orchestration_mode(self):
        self.mode_cfg = self._resolve_mode()
        talisman_contract = self.sections.get("talisman_contract", {})
        blocked = set(talisman_contract.get("blocked_types", []))
        preferred = talisman_contract.get("preferred_types", [])

        if self.mode_cfg.get("include_verification_tail") and "verification" not in blocked:
            has_verification = any(fu.get("dimension") == "verification" for fu in self.fu_list)
            if self.fu_list and not has_verification:
                self._append_talisman("verification", "mode:verification-tail")

        max_talismans = self.mode_cfg.get("max_talismans", len(self.fu_list))
        if len(self.fu_list) > max_talismans:
            preferred_set = set(preferred) if isinstance(preferred, list) else set()
            ranked = sorted(
                self.fu_list,
                key=lambda fu: (
                    0 if fu.get("dimension") in preferred_set else 1,
                    self.ORDER_MAP.get(fu.get("type"), 99),
                ),
            )
            self.fu_list = ranked[:max_talismans]

    def _detect_curse(self):
        """检测禁咒等级"""
        for kw in self.CONSTRAINT_KEYWORDS["高危"]:
            if kw in self.task:
                self.curse_level = "high"
                return
        for kw in self.CONSTRAINT_KEYWORDS["中危"]:
            if kw in self.task:
                self.curse_level = "medium"

    def _check_risk_budget(self):
        risk_contract = self.sections.get("risk_contract", {})
        max_curse_level = risk_contract.get("max_curse_level")
        if max_curse_level not in {"low", "medium", "high"}:
            return
        risk_order = {"low": 1, "medium": 2, "high": 3}
        if risk_order[self.curse_level] > risk_order[max_curse_level]:
            self.conflicts.append({
                "between": [fu["id"] for fu in self.fu_list] or ["task"],
                "type": "风险越界",
                "severity": "high",
                "resolution": f"当前禁咒等级为 {self.curse_level}，超出任务允许的 {max_curse_level}，建议降级任务或改用审慎流程",
                "category": "risk",
            })

    def _detect_conflicts(self):
        """检测符箓间冲突：风格冲突、数据流不兼容、约束矛盾、资源竞争"""
        # 1. 基于类型的风格/格式冲突
        for i, fu_a in enumerate(self.fu_list):
            for j, fu_b in enumerate(self.fu_list[i+1:], i+1):
                conflict = self._check_type_conflict(fu_a, fu_b)
                if conflict:
                    self.conflicts.append({
                        "between": [fu_a["id"], fu_b["id"]],
                        "type": conflict["type"],
                        "severity": conflict["severity"],
                        "resolution": conflict["resolution"],
                        "category": "style",
                    })
        # 2. 数据流兼容性检查（基于拓扑顺序的上下游检查）
        self._check_dataflow_compatibility()
        # 3. 约束条件矛盾检查
        self._check_constraint_conflicts()
        # 4. SLA累积超限检查
        self._check_sla_budget()

    def _check_type_conflict(self, a, b):
        """基于符箓类型的风格/格式冲突规则库（扩展版）"""
        style_clash = {
            # 格式/数据不匹配（双向对称）
            ("分析箓", "创作箓"): {"type": "格式不匹配", "severity": "low", "resolution": "插入转换箓作为适配层: structured_data -> text"},
            ("分析箓", "决策箓"): {"type": "格式不匹配", "severity": "low", "resolution": "插入转换箓作为适配层: structured_data -> options"},
            ("检索箓", "创作箓"): {"type": "格式不匹配", "severity": "low", "resolution": "插入转换箓作为适配层: results -> structured_data"},
            ("决策箓", "创作箓"): {"type": "格式不匹配", "severity": "low", "resolution": "插入转换箓作为适配层: ranked_list -> structured_data"},
            # 风格矛盾（双向对称）
            ("创作箓", "验证箓"): {"type": "风格矛盾", "severity": "medium", "resolution": "分层处理：创作->验证->风格统一箓"},
            ("转换箓", "验证箓"): {"type": "风格矛盾", "severity": "low", "resolution": "先验证再转换，避免格式变更后校验失效"},
            # 冗余/重复（双向对称）
            ("分析箓", "检索箓"): {"type": "功能冗余", "severity": "low", "resolution": "考虑合并为检索分析箓，或明确分工：检索->分析"},
            ("决策箓", "验证箓"): {"type": "功能冗余", "severity": "low", "resolution": "决策已含评估逻辑，验证可降级为抽样检查"},
        }
        pair = (a["type"], b["type"])
        reverse = (b["type"], a["type"])
        if pair in style_clash:
            return style_clash[pair]
        if reverse in style_clash:
            return style_clash[reverse]
        return None

    def _check_sequence_conflicts(self):
        """拓扑构建后检查：若存在违反标准执行顺序的符箓对，则报顺序矛盾"""
        # 标准执行顺序：检索箓(1) -> 分析箓(2) -> 决策箓(3) -> 创作箓(4) -> 验证箓(5) -> 转换箓(6)
        sequence_rules = [
            ("分析箓", "验证箓", "分析应在验证之前执行，避免无内容可验证"),
            ("分析箓", "转换箓", "分析应在转换之前执行，避免丢失结构化信息"),
            ("创作箓", "验证箓", "创作应在验证之前执行，验证无内容则无意义"),
            ("检索箓", "分析箓", "检索应在分析之前执行，先获取数据再分析"),
            ("决策箓", "创作箓", "决策应在创作之前执行，先确定方向再生成内容"),
        ]
        # 获取当前拓扑中的位置
        positions = {}
        for idx, fu_id in enumerate(self.topology):
            fu = next((f for f in self.fu_list if f["id"] == fu_id), None)
            if fu:
                positions[fu["type"]] = idx
        for upstream, downstream, reason in sequence_rules:
            if upstream in positions and downstream in positions:
                if positions[upstream] > positions[downstream]:
                    up_id = next(f["id"] for f in self.fu_list if f["type"] == upstream)
                    down_id = next(f["id"] for f in self.fu_list if f["type"] == downstream)
                    self.conflicts.append({
                        "between": [up_id, down_id],
                        "type": "顺序矛盾",
                        "severity": "medium",
                        "resolution": f"调整拓扑：{reason}",
                        "category": "style",
                    })

    def _check_dataflow_compatibility(self):
        """检查拓扑序列中相邻符箓的数据流兼容性"""
        if len(self.fu_list) < 2:
            return
        # 基于当前拓扑序（尚未最终确定，先按类型排序模拟）
        sorted_list = sorted(self.fu_list, key=lambda x: self.ORDER_MAP.get(x["type"], 99))
        type_compat = {
            "raw_text": {"structured_data": "parser", "text": "pass", "any": "pass", "markdown": "pass"},
            "structured_data": {"text": "formatter", "json": "pass", "any": "pass", "options": "extractor", "markdown": "pass"},
            "text": {"markdown": "pass", "target_format": "converter", "any": "pass", "json": "pass"},
            "query": {"list": "pass", "results": "pass", "any": "pass"},
            "options": {"ranked_list": "pass", "json": "pass", "any": "pass", "structured_data": "ranker"},
            "list": {"json": "pass", "structured_data": "aggregator", "any": "pass", "raw_text": "joiner", "options": "picker", "text": "joiner"},
            "ranked_list": {"json": "pass", "structured_data": "unwrap", "any": "pass", "text": "formatter", "options": "pass"},
            "boolean": {"any": "pass", "text": "pass", "json": "pass"},
            "any": {"any": "pass", "text": "pass", "json": "pass", "target_format": "pass", "structured_data": "pass", "markdown": "pass"},
        }
        for i in range(len(sorted_list) - 1):
            upstream = sorted_list[i]
            downstream = sorted_list[i + 1]
            up_outputs = [p.get("type", "any") for p in upstream.get("output_ports", [])]
            down_inputs = [p.get("type", "any") for p in downstream.get("input_ports", [])]
            # 检查是否有直接兼容
            compatible = False
            needed_adapter = None
            for uo in up_outputs:
                for di in down_inputs:
                    if uo == di or di == "any" or uo == "any":
                        compatible = True
                        break
                    if uo in type_compat and di in type_compat[uo]:
                        adapter = type_compat[uo][di]
                        if adapter != "pass":
                            needed_adapter = adapter
                        else:
                            compatible = True
                            break
                if compatible:
                    break
            if not compatible and needed_adapter:
                self.conflicts.append({
                    "between": [upstream["id"], downstream["id"]],
                    "type": "数据流不兼容",
                    "severity": "medium",
                    "resolution": f"需要适配器: {upstream['type']}({uo}) -> {downstream['type']}({di}) 通过 {needed_adapter} 转换",
                    "category": "dataflow",
                })
            elif not compatible:
                self.conflicts.append({
                    "between": [upstream["id"], downstream["id"]],
                    "type": "数据流不兼容",
                    "severity": "high",
                    "resolution": f"严重：{upstream['type']}的输出({uo})无法直接连接到{downstream['type']}的输入({di})，需人工设计转换逻辑",
                    "category": "dataflow",
                })

    def _check_constraint_conflicts(self):
        """检查符箓间的约束条件矛盾"""
        # 约束矛盾矩阵
        constraint_clash = [
            (("创作箓", "字数可控"), ("验证箓", "不修改内容"), "medium", "验证箓要求不修改内容，但创作箓输出字数可控可能需删减"),
            (("转换箓", "无损转换"), ("验证箓", "不修改内容"), "low", "转换箓的无损转换与验证箓的不修改内容兼容，但转换后验证可能误判"),
            (("分析箓", "保留原始语义"), ("创作箓", "内容生成与改写"), "medium", "分析箓要求保留语义，创作箓会改写内容，需插入语义保持箓"),
            (("检索箓", "去重"), ("分析箓", "标注置信度"), "low", "检索去重后分析标注置信度可能信息不足，建议保留原始去重标记"),
        ]
        for fu in self.fu_list:
            fu_type = fu.get("type", "")
            fu_constraints = set(fu.get("constraints", []))
            for other in self.fu_list:
                if other["id"] == fu["id"]:
                    continue
                other_type = other.get("type", "")
                other_constraints = set(other.get("constraints", []))
                for (ct_a, c_a), (ct_b, c_b), severity, resolution in constraint_clash:
                    match = (
                        (fu_type == ct_a and other_type == ct_b and c_a in fu_constraints and c_b in other_constraints)
                        or (fu_type == ct_b and other_type == ct_a and c_b in fu_constraints and c_a in other_constraints)
                    )
                    if match:
                        # 避免重复记录
                        already = any(
                            c.get("type") == "约束矛盾" and set(c.get("between", [])) == {fu["id"], other["id"]}
                            for c in self.conflicts
                        )
                        if not already:
                            self.conflicts.append({
                                "between": [fu["id"], other["id"]],
                                "type": "约束矛盾",
                                "severity": severity,
                                "resolution": resolution,
                                "category": "constraint",
                            })

    def _check_sla_budget(self):
        """检查SLA是否超出合理预算"""
        total_sla = sum(fu.get("avg_sla", 15) for fu in self.fu_list)
        if total_sla > self.SLA_WARNING:
            self.conflicts.append({
                "between": [fu["id"] for fu in self.fu_list],
                "type": "SLA累积超限",
                "severity": "medium" if total_sla <= self.SLA_CRITICAL else "high",
                "resolution": f"预估总SLA为{total_sla}秒，建议拆分为子任务或启用并行执行模式",
                "category": "performance",
            })

    def _build_topology(self):
        """构建执行拓扑"""
        sorted_fu = sorted(self.fu_list, key=lambda x: self.ORDER_MAP.get(x["type"], 99))
        self.topology = [fu["id"] for fu in sorted_fu]

    def _ordered_talismans(self):
        fu_by_id = {fu["id"]: fu for fu in self.fu_list}
        ordered = [fu_by_id[fu_id] for fu_id in self.topology if fu_id in fu_by_id]
        if ordered:
            return ordered
        return sorted(self.fu_list, key=lambda x: self.ORDER_MAP.get(x["type"], 99))

    def _group_for_parallelism(self, fu):
        if not self.mode_cfg.get("prefer_parallel"):
            return 1
        if fu.get("dimension") in {"retrieval", "analysis"}:
            return 1
        if fu.get("dimension") in {"decision", "creation"}:
            return 2
        return 3

    def _build_command_packets(self):
        ordered = self._ordered_talismans()
        packets = []
        previous_by_group = {}
        for index, fu in enumerate(ordered, start=1):
            group = self._group_for_parallelism(fu)
            depends_on = []
            if group in previous_by_group:
                depends_on = [previous_by_group[group]]
            elif group > 1:
                prior_groups = [previous_by_group[g] for g in sorted(previous_by_group) if g < group]
                depends_on = prior_groups[-1:] if prior_groups else []

            related_conflicts = [
                conflict["resolution"]
                for conflict in self.conflicts
                if fu["id"] in conflict.get("between", [])
            ]
            packets.append(
                {
                    "step": index,
                    "talisman_id": fu["id"],
                    "talisman_type": fu["type"],
                    "dimension": fu.get("dimension"),
                    "capability": CAPABILITY_MAP.get(fu.get("dimension"), "general"),
                    "objective": f"{fu.get('goal', fu['type'])} | 任务: {self.task[:120]}",
                    "depends_on": depends_on,
                    "parallel_group": group,
                    "estimated_sla": fu.get("avg_sla", 15),
                    "input_ports": fu.get("input_ports", []),
                    "output_ports": fu.get("output_ports", []),
                    "constraints": fu.get("constraints", []),
                    "activation_reason": fu.get("activation_reason"),
                    "risk_level": self.curse_level,
                    "adapter_hints": related_conflicts,
                }
            )
            previous_by_group[group] = fu["id"]
        return packets

    def _build_dispatch_contract(self, command_packets, mode):
        if self.curse_level == "high" or self.risk_alignment == "exceeds_budget":
            authority_mode = "sealed-command"
            strategy = "protect"
        elif self.conflicts:
            authority_mode = "cautious-attunement"
            strategy = "protect"
        else:
            authority_mode = "direct-command"
            strategy = "possess" if self.mode_cfg.get("prefer_parallel") else "protect"

        if len(command_packets) >= 4:
            formation = "night-parade"
        elif len(command_packets) >= 2:
            formation = "dual-attunement"
        else:
            formation = "single-possession"

        return {
            "recommended_skill": "juling-qianjiang",
            "packet_count": len(command_packets),
            "authority_mode": authority_mode,
            "strategy": strategy,
            "formation": formation,
            "mode": mode,
            "objective": self.task[:120],
        }

    def _output(self):
        total_sla = sum(fu.get("avg_sla", 15) for fu in self.fu_list)
        # adapter_insertions: 只有数据流不兼容和格式不匹配需要插入适配器
        adapter_count = sum(
            1 for c in self.conflicts
            if c.get("category") in ("dataflow", "style") and c.get("type") in ("数据流不兼容", "格式不匹配")
        )
        # 如果有high severity冲突或SLA超限，强制serial模式
        has_high = any(c.get("severity") == "high" for c in self.conflicts)
        mode = "serial" if has_high else ("serial" if self.conflicts else "parallel_where_possible")
        # 若只有low级别冲突，仍可尝试parallel_where_possible
        if self.conflicts and not has_high:
            all_low = all(c.get("severity") == "low" for c in self.conflicts)
            if all_low:
                mode = "parallel_where_possible"
        talisman_contract = self.sections.get("talisman_contract", {})
        risk_contract = self.sections.get("risk_contract", {})
        execution_contract = self.sections.get("execution_contract", {})
        risk_budget = risk_contract.get("max_curse_level", "high")
        risk_alignment = "within_budget"
        risk_order = {"low": 1, "medium": 2, "high": 3}
        if risk_order.get(self.curse_level, 3) > risk_order.get(risk_budget, 3):
            risk_alignment = "exceeds_budget"
        self.risk_alignment = risk_alignment

        ritual_summary = {
            "orchestration_mode": self.mode_cfg.get("name", "balanced-array"),
            "ritual_intent": self.mode_cfg.get("intent", "balanced orchestration"),
            "topology_strategy": self.mode_cfg.get("topology_strategy", "balanced-lattice"),
            "preferred_talismans": talisman_contract.get("preferred_types", []),
            "blocked_talismans": talisman_contract.get("blocked_types", []),
            "risk_budget": risk_budget,
            "risk_alignment": risk_alignment,
            "sla_target": execution_contract.get("sla_target"),
            "contracts_present": [key for key, value in self.sections.items() if value],
            "parallelizable_groups": min(len(self.fu_list), 2 if self.mode_cfg.get("prefer_parallel") else 1),
        }
        command_packets = self._build_command_packets()
        dispatch_contract = self._build_dispatch_contract(command_packets, mode)
        return {
            "generator": "tongtian-lu",
            "version": "v0.1.0",
            "task": self.task[:80],
            "orchestration_mode": self.mode_cfg.get("name", "balanced-array"),
            "ritual_intent": ritual_summary["ritual_intent"],
            "dimension_count": len(self.fu_list),
            "talisman_list": self.fu_list,
            "curse_level": self.curse_level,
            "risk_alignment": risk_alignment,
            "conflicts": self.conflicts,
            "topology": self.topology,
            "command_packets": command_packets,
            "dispatch_contract": dispatch_contract,
            "ritual_summary": ritual_summary,
            "quality_score": round(
                max(
                    0.0,
                    min(
                        100.0,
                        78.0
                        + len(self.fu_list) * 3.0
                        + len(command_packets) * 2.0
                        - len(self.conflicts) * 4.0
                        - (10.0 if risk_alignment == "exceeds_budget" else 0.0)
                    ),
                ),
                1,
            ),
            "human_intervention": 1 if risk_alignment == "exceeds_budget" or any(c.get("severity") == "high" for c in self.conflicts) else 0,
            "output_completeness": round(min(100.0, 60.0 + len(self.topology) * 6.0 + len(command_packets) * 5.0), 1),
            "consistency_score": round(max(0.0, 100.0 - len(self.conflicts) * 8.0), 1),
            "execution_plan": {
                "mode": mode,
                "estimated_sla": total_sla,
                "adapter_insertions": adapter_count,
                "conflict_summary": {
                    "total": len(self.conflicts),
                    "style": sum(1 for c in self.conflicts if c.get("category") == "style"),
                    "dataflow": sum(1 for c in self.conflicts if c.get("category") == "dataflow"),
                    "constraint": sum(1 for c in self.conflicts if c.get("category") == "constraint"),
                    "performance": sum(1 for c in self.conflicts if c.get("category") == "performance"),
                    "risk": sum(1 for c in self.conflicts if c.get("category") == "risk"),
                },
            },
        }


def main():
    if len(sys.argv) < 2:
        print("用法: python fu_generator.py '<任务描述>' 或 python fu_generator.py <task.txt>")
        print("示例: python fu_generator.py '分析竞品数据并生成报告'")
        sys.exit(1)

    arg = sys.argv[1]
    # 自动识别结构化 JSON / 任务文件 / 直接任务描述
    if arg.endswith('.json') and Path(arg).exists():
        task = json.loads(Path(arg).read_text(encoding='utf-8'))
    elif arg.endswith('.txt') and Path(arg).exists():
        task = Path(arg).read_text(encoding='utf-8').strip()
    else:
        task = arg

    # 输入验证
    if isinstance(task, str):
        if not task:
            print("错误: 任务描述不能为空")
            sys.exit(2)
        if len(task) > 2000:
            print(f"错误: 任务描述过长 ({len(task)} 字符)，最大支持 2000 字符")
            sys.exit(2)
    elif isinstance(task, dict):
        description = task.get("description")
        task_block = task.get("task")
        if not description and not task_block:
            print("错误: 结构化任务规格必须包含 task 或 description")
            sys.exit(2)
    else:
        print("错误: 仅支持字符串任务描述、txt 文件或结构化 JSON")
        sys.exit(2)

    gen = FuGenerator(task)
    result = gen.generate()

    output_file = Path("fu_plan.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 55)
    print("通天箓 · 符阵编排报告 V5.8")
    print("=" * 55)
    print(f"  任务: {result['task']}")
    print(f"  编排模式: {result['orchestration_mode']}")
    print(f"  符阵意图: {result['ritual_intent']}")
    print(f"  维度数: {result['dimension_count']}")
    print(f"  禁咒等级: {result['curse_level']}")
    print(f"  风险对齐: {result['risk_alignment']}")
    print(f"  符箓列表:")
    for fu in result["talisman_list"]:
        print(f"    • [{fu['type']}] {fu['id']} | SLA:{fu['avg_sla']}s")
    print(f"  拓扑序: {' -> '.join(result['topology'])}")
    print(f"  冲突数: {len(result['conflicts'])}")
    for c in result["conflicts"]:
        print(f"    ⚠️ [{c['severity']}] {c['type']}: {c['resolution']}")
    print(f"  预估耗时: {result['execution_plan']['estimated_sla']}s")
    print(f"  执行模式: {result['execution_plan']['mode']}")
    print("=" * 55)


    print(f"详细计划已保存: {output_file}")


if __name__ == "__main__":
    main()
