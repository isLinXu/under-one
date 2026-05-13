#!/usr/bin/env python3
"""
器名: 上下文熵扫描器 (Entropy Scanner)
用途: 扫描对话上下文，计算语义级健康指标，输出诊断报告
输入: JSON格式的对话上下文 [{role, content, round}]
输出: JSON诊断报告 {entropy, consistency, health_score, alerts}
版本: V6.1 — 语义级熵计算 + 稳态修复契约
"""

import json
import sys
import re
from pathlib import Path
from collections import Counter

# ── 路径设置 ───────────────────────────────────────────────
SKILL_ROOT = Path(__file__).resolve().parent.parent  # qiti-yuanliu/
SKILLS_ROOT = SKILL_ROOT.parent                       # skills/
sys.path.insert(0, str(SKILLS_ROOT))

# ── 依赖导入（带降级） ─────────────────────────────────────
try:
    from metrics_collector import record_metrics
except ImportError:
    def record_metrics(*args, **kwargs):
        def decorator(f): return f
        return decorator

try:
    from _skill_config import validate_json_list, get_skill_config
except ImportError:
    def validate_json_list(data, item_schema, skill_name="skill"):
        if not isinstance(data, list):
            return False, ["<root> must be a list"]
        return True, []

    def get_skill_config(skill_name, key=None, default=None):
        return default


class QiTiScanner:
    """V6.1 炁体源流 — 本源自省器 — 语义级熵计算 + 稳态修复契约"""

    # 硬编码默认值（配置不可用时回退）
    _DEFAULT_CONTRADICTION_KW = ["不对", "错了", "矛盾", "之前说", "改回", "重新", "不是这个", "相反", "不一致"]
    _DEFAULT_NEGATION_PREFIXES = ["不", "没", "无", "非", "勿", "别", "未", "否"]
    _DEFAULT_REVERSAL_PATTERNS = [
        ["是", "不是"], ["要", "不要"], ["能", "不能"], ["会", "不会"],
        ["对", "不对"], ["好", "不好"], ["行", "不行"], ["可以", "不可以"],
    ]
    _DEFAULT_CLARIFICATION_MARKERS = ["我说的是", "我的意思是", "准确来说", "更准确地说", "这里指的是", "补充一下", "更正一下", "具体来说"]
    _DEFAULT_HARD_RESET_MARKERS = ["改回", "重新理解", "不是这个方案", "完全不是", "之前的目标也不准确", "推翻", "重做", "换成"]
    _DEFAULT_TRANSITION_WORDS = ["但是", "然而", "不过", "却", "反而", "其实", "实际上", "话说回来"]
    _DEFAULT_LOGIC_MARKERS = ["因为", "所以", "首先", "然后", "最后", "结论", "因此", "总之", "综上所述"]
    _DEFAULT_HEALTH_THRESHOLDS = {
        "excellent": (90, float("inf")),
        "good": (75, 90),
        "warning": (60, 75),
        "danger": (0, 60),
    }

    def __init__(self, context_data):
        self.context = context_data
        self.alerts = []
        self.metrics = {}
        self._load_config()

    def _load_config(self):
        """从 under-one.yaml 加载 qitiyuanliu 配置段"""
        cfg = get_skill_config("qitiyuanliu", default={})

        # 熵权重
        ew = cfg.get("entropy_weights", {})
        self.entropy_weights = {
            "conflict": float(ew.get("conflict", 2.0)),
            "gap": float(ew.get("gap", 1.5)),
            "redundancy": float(ew.get("redundancy", 0.5)),
            "topic_drift": float(ew.get("topic_drift", 1.8)),
            "intent_shift": float(ew.get("intent_shift", 1.2)),
        }

        # 熵阈值
        et = cfg.get("entropy_thresholds", {})
        self.entropy_warning = float(et.get("warning", 3.0))
        self.entropy_critical = float(et.get("critical", 7.0))

        # 矛盾检测
        ct = cfg.get("contradiction", {})
        self.contradiction_keywords = list(ct.get("keywords", self._DEFAULT_CONTRADICTION_KW))
        self.negation_prefixes = list(ct.get("negation_prefixes", self._DEFAULT_NEGATION_PREFIXES))
        raw_patterns = ct.get("reversal_patterns", self._DEFAULT_REVERSAL_PATTERNS)
        self.reversal_patterns = [list(p) for p in raw_patterns]
        self.clarification_markers = list(ct.get("clarification_markers", self._DEFAULT_CLARIFICATION_MARKERS))
        self.hard_reset_markers = list(ct.get("hard_reset_markers", self._DEFAULT_HARD_RESET_MARKERS))

        # 意图漂移
        ist = cfg.get("intent_shift", {})
        self.shift_density_threshold = float(ist.get("shift_density_threshold", 2.0))
        self.transition_words = list(ist.get("transition_words", self._DEFAULT_TRANSITION_WORDS))
        self.negation_density_threshold = float(ist.get("negation_density_threshold", 3.0))

        # 信息密度
        sd = cfg.get("semantic_density", {})
        self.density_high = float(sd.get("high_threshold", 0.55))
        self.density_medium = float(sd.get("medium_threshold", 0.35))

        # 推理链完整度
        comp = cfg.get("completeness", {})
        self.logic_markers = list(comp.get("logic_markers", self._DEFAULT_LOGIC_MARKERS))
        self.completeness_base = int(comp.get("base_score", 50))
        self.completeness_per_marker = int(comp.get("per_marker", 5))
        self.completeness_max = int(comp.get("max_score", 100))

        # 健康分权重
        hw = cfg.get("health_weights", {})
        self.health_weights = {
            "consistency": float(hw.get("consistency", 0.25)),
            "alignment": float(hw.get("alignment", 0.25)),
            "completeness": float(hw.get("completeness", 0.20)),
            "entropy_bonus": float(hw.get("entropy_bonus", 0.30)),
        }

        # 健康等级阈值
        ht = cfg.get("health_thresholds", {})
        self.health_thresholds = {
            "excellent": (float(ht.get("excellent", 90)), float("inf")),
            "good": (float(ht.get("good", 75)), float(ht.get("excellent", 90))),
            "warning": (float(ht.get("warning", 60)), float(ht.get("good", 75))),
            "danger": (0, float(ht.get("warning", 60))),
        }

        # 对齐度
        al = cfg.get("alignment", {})
        self.first_goal_length = int(al.get("first_goal_length", 150))
        self.min_msg_length = int(al.get("min_msg_length", 30))
        self.low_overlap_threshold = float(al.get("low_overlap_threshold", 0.2))
        self.drift_penalty = int(al.get("drift_penalty", 8))

        # DNA快照
        dna = cfg.get("dna_snapshot", {})
        self.dna_rounds = int(dna.get("rounds", 3))
        self.dna_preview = int(dna.get("preview_length", 30))

        # 自动修复交接
        rh = cfg.get("repair_handoff", {})
        self.repair_handoff_threshold = max(1, int(rh.get("contradiction_threshold", 2)))
        self.repair_handoff_target = str(rh.get("target_skill", "dalu-dongguan"))
        self.repair_handoff_action = str(rh.get("action", "cross_segment_trace"))
        self.repair_handoff_reason = str(rh.get("reason", "repeated_contradictions"))
        self.repair_handoff_evidence_limit = max(1, int(rh.get("evidence_limit", 3)))

    # ── 语义级工具方法 ──────────────────────────────────────

    def _extract_keywords(self, text: str) -> list:
        """提取语义关键词：中文名词/动词/形容词 + 英文单词"""
        keywords = []
        # 中文实词（2-4字，常见名词/动词/形容词模式）
        keywords += re.findall(r'[\u4e00-\u9fff]{2,4}', text)
        # 英文单词
        keywords += re.findall(r'[a-zA-Z]{3,}', text.lower())
        # 数字+单位
        keywords += re.findall(r'\d+[\u4e00-\u9fff%]*', text)
        return keywords

    def _extract_content_words(self, text: str) -> tuple:
        """提取实词与虚词，返回 (实词列表, 虚词列表)
        简化版：基于常见虚词表反向推断实词"""
        # 常见中文虚词
        function_words = set(
            "的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 自己 这 那 之 与 及 或 而 但 若 虽 因为 所以 因此 如果 即使 虽然 尽管 然而 可是 不过 只是 仅 仅只 罢了 而已 么 呢 吧 啊 哇 呀 哪 哦 哈 哟 呗 哩 啰 嘛 咧 呐 嗯 唉 哎 嗨 哼 哼 嘻 嘿 嘘 呜 呕 嗷 嗡 嘟 啧 嗟 喔 嗬 嗯 哎 唉".split()
        )
        # 分词（简化：按字和常见词）
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+', text)
        content = []
        function = []
        for w in words:
            if len(w) == 1:
                if w in function_words:
                    function.append(w)
                else:
                    content.append(w)
            else:
                # 多字词：检查是否全由虚词组成
                if all(c in function_words for c in w):
                    function.append(w)
                else:
                    content.append(w)
        return content, function

    def _semantic_similarity(self, a: str, b: str) -> float:
        """语义相似度：基于关键词重叠 + Jaccard 混合"""
        kw_a = set(self._extract_keywords(a))
        kw_b = set(self._extract_keywords(b))
        if not kw_a or not kw_b:
            return 0.0
        jaccard = len(kw_a & kw_b) / len(kw_a | kw_b)
        # 额外奖励：如果一方关键词完全包含于另一方
        containment = 0.0
        if kw_a and kw_b:
            if kw_a.issubset(kw_b) or kw_b.issubset(kw_a):
                containment = 0.1
        return min(1.0, jaccard + containment)

    def _classify_correction_mode(self, content: str, role: str = ""):
        """识别用户纠偏是正常澄清还是高风险推翻。"""
        if not content:
            return None
        normalized = content.strip()
        trigger_markers = (
            self.contradiction_keywords
            + self.clarification_markers
            + self.hard_reset_markers
        )
        has_trigger = any(marker in normalized for marker in trigger_markers)
        if not has_trigger:
            return None
        if any(marker in normalized for marker in self.hard_reset_markers):
            return "hard_reset"
        if role == "user" and any(marker in normalized for marker in self.clarification_markers):
            return "clarification"
        return "correction" if role == "user" else "hard_reset"

    def _collect_correction_events(self):
        """收集用户纠偏/澄清事件，用于规则生长而非一律视作异常。"""
        events = []
        for msg in self.context:
            content = msg.get("content", "")
            mode = self._classify_correction_mode(content, msg.get("role", ""))
            if not mode:
                continue
            events.append(
                {
                    "round": msg.get("round", 0),
                    "role": msg.get("role", ""),
                    "mode": mode,
                    "preview": content[:60] + "..." if len(content) > 60 else content,
                }
            )
        return events

    def _calc_topic_drift(self):
        """主题漂移检测：基于语义相似度的渐进偏移"""
        if len(self.context) < 2:
            return 0.0

        # 提取首轮目标语义关键词
        first_content = self.context[0].get("content", "")[:self.first_goal_length]
        first_keywords = set(self._extract_keywords(first_content))
        if not first_keywords:
            return 0.0

        drift_score = 0.0
        for msg in self.context[1:]:
            content = msg.get("content", "")
            if len(content) < self.min_msg_length:
                continue

            msg_keywords = set(self._extract_keywords(content[:self.first_goal_length]))
            if not msg_keywords:
                continue

            similarity = self._semantic_similarity(
                " ".join(first_keywords), " ".join(msg_keywords)
            )
            # 相似度低 → 漂移高
            if similarity < self.low_overlap_threshold:
                drift_score += 1.0
            elif similarity < 0.4:
                drift_score += 0.5

        return drift_score

    def _calc_intent_shift(self):
        """意图偏移检测：基于转折词密度"""
        total_shift_score = 0.0
        for msg in self.context:
            content = msg.get("content", "")
            if not content:
                continue
            if self._classify_correction_mode(content, msg.get("role", "")) == "clarification":
                continue

            # 转折词计数
            transition_count = sum(1 for tw in self.transition_words if tw in content)
            # 密度（每百字）
            density = (transition_count / max(1, len(content))) * 100
            if density > self.shift_density_threshold:
                total_shift_score += 1.0

        return total_shift_score

    def _calc_semantic_density(self):
        """语义信息密度：实词比例"""
        if not self.context:
            return "medium"

        total_content = 0
        total_function = 0
        for msg in self.context:
            content = msg.get("content", "")
            c_words, f_words = self._extract_content_words(content)
            total_content += len(c_words)
            total_function += len(f_words)

        total = total_content + total_function
        if total == 0:
            return "low"

        ratio = total_content / total
        if ratio >= self.density_high:
            return "high"
        if ratio >= self.density_medium:
            return "medium"
        return "low"

    # ── 核心扫描方法 ─────────────────────────────────────────

    @record_metrics("qiti-yuanliu")
    def scan(self):
        """执行全量语义级扫描"""
        self._calc_entropy()
        self._check_consistency()
        self._check_density()
        self._check_alignment()
        self._check_completeness()
        self._detect_contradictions()
        self._calc_health_score()
        return self._generate_report()

    def _calc_entropy(self):
        """V5.3 语义级熵计算"""
        # 基础熵组件
        conflict_count = len(self._count_semantic_contradictions())
        gap_count = self._count_info_gaps()
        redundancy_count = self._count_redundancy()

        # 语义级熵组件
        topic_drift = self._calc_topic_drift()
        intent_shift = self._calc_intent_shift()

        ew = self.entropy_weights
        entropy = (
            conflict_count * ew.get("conflict", 2.0) +
            gap_count * ew.get("gap", 1.5) +
            redundancy_count * ew.get("redundancy", 0.5) +
            topic_drift * ew.get("topic_drift", 1.8) +
            intent_shift * ew.get("intent_shift", 1.2)
        )

        self.metrics["entropy"] = round(entropy, 2)
        self.metrics["entropy_level"] = (
            "green" if entropy < self.entropy_warning
            else "yellow" if entropy < self.entropy_critical
            else "red"
        )
        # 记录组件详情
        self.metrics["entropy_components"] = {
            "conflict": conflict_count,
            "gap": gap_count,
            "redundancy": redundancy_count,
            "topic_drift": round(topic_drift, 2),
            "intent_shift": round(intent_shift, 2),
            "clarification_events": len([event for event in self._collect_correction_events() if event["mode"] == "clarification"]),
        }

    def _count_semantic_contradictions(self):
        """语义矛盾计数（去重后）。"""
        all_contra = self._detect_all_contradictions()
        # 按 round + type 去重
        seen = set()
        unique = []
        for c in all_contra:
            key = (c.get("round"), c.get("type"), c.get("keyword", c.get("pattern", "")))
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def _detect_all_contradictions(self):
        """详细语义矛盾检测（单一真源实现）。"""
        contradictions = []
        for msg in self.context:
            content = msg.get("content", "")
            round_num = msg.get("round", 0)
            correction_mode = self._classify_correction_mode(content, msg.get("role", ""))

            # 1. 直接关键词匹配
            for kw in self.contradiction_keywords:
                if correction_mode == "clarification" and kw in {"不对", "错了"}:
                    continue
                if kw in content:
                    contradictions.append({
                        "round": round_num,
                        "type": "keyword",
                        "keyword": kw,
                        "preview": content[:50] + "..." if len(content) > 50 else content,
                    })

            # 2. 否定前缀 + 肯定词 → 语义反转
            for pos, _ in self.reversal_patterns:
                for prefix in self.negation_prefixes:
                    pattern = prefix + pos
                    if correction_mode == "clarification" and pattern in content:
                        continue
                    if pattern in content:
                        contradictions.append({
                            "round": round_num,
                            "type": "semantic_reversal",
                            "pattern": f"{prefix}+{pos}",
                            "preview": content[:50] + "..." if len(content) > 50 else content,
                        })

            # 3. 高否定密度检测
            negation_count = sum(1 for prefix in self.negation_prefixes if prefix in content)
            content_len = max(1, len(content))
            negation_density = (negation_count / content_len) * 100
            if correction_mode != "clarification" and negation_density > self.negation_density_threshold:
                contradictions.append({
                    "round": round_num,
                    "type": "high_negation_density",
                    "density": round(negation_density, 2),
                    "preview": content[:50] + "..." if len(content) > 50 else content,
                })

        return contradictions

    def _count_info_gaps(self):
        """统计信息缺口"""
        gaps = 0
        for i, msg in enumerate(self.context):
            content = msg.get("content", "")
            if "?" in content or "？" in content or "如何" in content or "什么" in content:
                if i == len(self.context) - 1:
                    gaps += 1
        return gaps

    def _count_redundancy(self):
        """统计语义冗余"""
        contents = [msg.get("content", "") for msg in self.context]
        duplicates = 0
        for i, c1 in enumerate(contents):
            for c2 in contents[i+1:]:
                if len(c1) > 20 and len(c2) > 20:
                    sim = self._semantic_similarity(c1[:100], c2[:100])
                    if sim > 0.7:
                        duplicates += 1
        return duplicates

    def _check_consistency(self):
        """检查上下文一致性 (基于语义矛盾数)"""
        contradictions = len(self._count_semantic_contradictions())
        consistency = max(0, 100 - contradictions * 15)
        self.metrics["consistency"] = consistency

    def _check_density(self):
        """V5.3 语义信息密度"""
        density = self._calc_semantic_density()
        self.metrics["density"] = density
        # 记录实词比例
        total_content = 0
        total_function = 0
        for msg in self.context:
            content = msg.get("content", "")
            c_words, f_words = self._extract_content_words(content)
            total_content += len(c_words)
            total_function += len(f_words)
        total = total_content + total_function
        self.metrics["content_word_ratio"] = round(total_content / max(1, total), 2) if total > 0 else 0.0

    def _check_alignment(self):
        """V5.3 语义目标对齐度"""
        if not self.context:
            self.metrics["alignment"] = 100
            return

        first_goal = self.context[0].get("content", "")[:self.first_goal_length]
        goal_keywords = set(self._extract_keywords(first_goal))

        total_drift = 0
        for msg in self.context[1:]:
            content = msg.get("content", "")
            if len(content) < self.min_msg_length:
                continue

            msg_keywords = set(self._extract_keywords(content[:self.first_goal_length]))
            if goal_keywords and msg_keywords:
                similarity = self._semantic_similarity(
                    " ".join(goal_keywords), " ".join(msg_keywords)
                )
                if similarity < self.low_overlap_threshold:
                    total_drift += 1

        drift_score = max(0, 100 - total_drift * self.drift_penalty)
        self.metrics["alignment"] = drift_score

    def _check_completeness(self):
        """检查推理链完整度"""
        marker_count = sum(
            1 for msg in self.context
            for m in self.logic_markers if m in msg.get("content", "")
        )
        completeness = min(self.completeness_max, self.completeness_base + marker_count * self.completeness_per_marker)
        self.metrics["completeness"] = completeness

    def _detect_contradictions(self):
        """生成语义矛盾警报"""
        for c in self._count_semantic_contradictions():
            msg = f"检测到{c['type']}"
            if c.get("keyword"):
                msg += f" '{c['keyword']}'"
            if c.get("pattern"):
                msg += f" 模式 '{c['pattern']}'"
            if c.get("density"):
                msg += f" (密度 {c['density']})"
            self.alerts.append({
                "level": "warning",
                "type": c["type"],
                "round": c["round"],
                "message": msg,
            })

        if self.metrics.get("entropy", 0) > self.entropy_critical:
            self.alerts.append({
                "level": "danger",
                "type": "high_entropy",
                "message": f"上下文熵过高 ({self.metrics['entropy']})，建议立即修复",
            })
        elif self.metrics.get("entropy", 0) > self.entropy_warning:
            self.alerts.append({
                "level": "warning",
                "type": "elevated_entropy",
                "message": f"上下文熵升高 ({self.metrics['entropy']})，建议关注",
            })

    def _calc_health_score(self):
        """V5.3 综合健康分"""
        hw = self.health_weights
        entropy_bonus = (
            100 if self.metrics.get("entropy", 0) < self.entropy_warning
            else 60 if self.metrics.get("entropy", 0) < self.entropy_critical
            else 20
        )
        score = (
            self.metrics.get("consistency", 100) * hw.get("consistency", 0.25) +
            self.metrics.get("alignment", 100) * hw.get("alignment", 0.25) +
            self.metrics.get("completeness", 100) * hw.get("completeness", 0.20) +
            entropy_bonus * hw.get("entropy_bonus", 0.30)
        )
        self.metrics["health_score"] = round(score, 1)
        self.metrics["health_level"] = self._get_level(score)

    def _get_level(self, score):
        for level, (low, high) in self.health_thresholds.items():
            if low <= score < high:
                return level
        return "unknown"

    def _generate_report(self):
        repair_handoff = self._build_repair_handoff()
        self_evolution = self._build_self_evolution(repair_handoff)
        stability_contract = self._build_stability_contract(repair_handoff, self_evolution)
        repair_plan = self._build_repair_plan(repair_handoff, self_evolution, stability_contract)
        escalation_contract = self._build_escalation_contract(
            repair_handoff, self_evolution, stability_contract, repair_plan
        )
        stability_checkpoints = self._build_stability_checkpoints(
            repair_handoff, stability_contract, repair_plan, escalation_contract
        )
        risk_hotspots = self._build_risk_hotspots(
            repair_handoff, self_evolution, stability_contract, escalation_contract
        )
        priority_actions = self._build_priority_actions(
            repair_handoff,
            self_evolution,
            stability_contract,
            repair_plan,
            escalation_contract,
            risk_hotspots,
        )
        execution_contract = self._build_execution_contract(
            repair_handoff,
            self_evolution,
            stability_contract,
            repair_plan,
            escalation_contract,
            priority_actions,
            risk_hotspots,
        )
        return {
            "scanner": "qiti-yuanliu",
            "version": "v0.1.0",
            "context_length": len(self.context),
            "metrics": self.metrics,
            "alerts": self.alerts,
            "recommendations": self._generate_recommendations(
                repair_handoff, self_evolution, stability_contract, escalation_contract
            ),
            "repair_handoff": repair_handoff,
            "origin_core": self_evolution["origin_core"],
            "self_evolution": self_evolution,
            "stability_contract": stability_contract,
            "repair_plan": repair_plan,
            "escalation_contract": escalation_contract,
            "stability_checkpoints": stability_checkpoints,
            "risk_hotspots": risk_hotspots,
            "priority_actions": priority_actions,
            "execution_contract": execution_contract,
            "quality_score": self.metrics.get("health_score", 0),
            "human_intervention": 1 if escalation_contract.get("manual_review_required") else 0,
            "output_completeness": 100.0 if stability_checkpoints.get("checkpoint_count") else 0.0,
            "consistency_score": self.metrics.get("consistency", 0),
            "dna_snapshot": self._generate_dna_snapshot(),
        }

    def _generate_recommendations(
        self,
        repair_handoff=None,
        self_evolution=None,
        stability_contract=None,
        escalation_contract=None,
    ):
        recs = []
        self_evolution = self_evolution or self._build_self_evolution(repair_handoff)
        stability_contract = stability_contract or self._build_stability_contract(repair_handoff, self_evolution)
        escalation_contract = escalation_contract or self._build_escalation_contract(
            repair_handoff,
            self_evolution,
            stability_contract,
            self._build_repair_plan(repair_handoff, self_evolution, stability_contract),
        )
        if self.metrics.get("entropy", 0) > self.entropy_critical:
            recs.append("建议立即执行稳态修复（上下文蒸馏+锚点重建）")
        elif self.metrics.get("entropy", 0) > self.entropy_warning:
            recs.append("建议关注，执行轻量炁循环")
        if repair_handoff:
            recs.append(
                f"已生成 repair_handoff，建议调用{repair_handoff['target_skill']}执行跨段追踪与锚点重建"
            )
        elif self.metrics.get("consistency", 100) < 90:
            recs.append("建议检查矛盾点，调用大罗洞观跨段追踪")
        if self.metrics.get("alignment", 100) < 95:
            recs.append("建议重新对齐用户原始目标")
        # V5.3 新增语义级建议
        components = self.metrics.get("entropy_components", {})
        if components.get("clarification_events", 0) > 0 and self.metrics.get("consistency", 100) >= 85:
            recs.append("检测到用户澄清/纠偏，建议更新目标锚点，但无需按异常处理")
        if components.get("topic_drift", 0) > 1:
            recs.append("检测到主题漂移，建议回顾原始目标")
        if components.get("intent_shift", 0) > 1:
            recs.append("检测到意图偏移，建议确认用户需求")
        if stability_contract.get("freeze_self_evolution"):
            recs.append("当前已进入稳态冻结，先执行 repair_plan 再恢复自演化")
        if escalation_contract.get("manual_review_required"):
            recs.append("当前修复链路需要人工确认后方可恢复自演化")
        if self_evolution.get("next_cycle"):
            recs.append(
                f"建议进入 {self_evolution['phase']} 炁循环："
                + " / ".join(self_evolution["next_cycle"][:3])
            )
        if not recs:
            recs.append("上下文状态健康，继续正常运行")
        return recs

    @staticmethod
    def _severity_rank(level):
        return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(level, 4)

    def _build_risk_hotspots(
        self,
        repair_handoff=None,
        self_evolution=None,
        stability_contract=None,
        escalation_contract=None,
    ):
        self_evolution = self_evolution or self._build_self_evolution(repair_handoff)
        stability_contract = stability_contract or self._build_stability_contract(repair_handoff, self_evolution)
        escalation_contract = escalation_contract or self._build_escalation_contract(
            repair_handoff,
            self_evolution,
            stability_contract,
            self._build_repair_plan(repair_handoff, self_evolution, stability_contract),
        )

        hotspots = []
        components = self.metrics.get("entropy_components", {})
        entropy = self.metrics.get("entropy", 0)
        consistency = self.metrics.get("consistency", 100)
        alignment = self.metrics.get("alignment", 100)
        info_gaps = self._count_info_gaps()

        if repair_handoff:
            hotspots.append(
                {
                    "id": "repair-handoff",
                    "severity": "critical",
                    "blocking": True,
                    "owner": repair_handoff.get("target_skill", "dalu-dongguan"),
                    "signal": f"{repair_handoff.get('observed_alerts', 0)}/{repair_handoff.get('alert_threshold', 0)} contradictions",
                    "reason": repair_handoff.get("summary"),
                    "action": repair_handoff.get("action"),
                }
            )

        if entropy >= self.entropy_critical:
            hotspots.append(
                {
                    "id": "entropy-red-zone",
                    "severity": "critical",
                    "blocking": True,
                    "owner": "qiti-yuanliu",
                    "signal": entropy,
                    "reason": "上下文熵进入红区，继续扩写会放大漂移。",
                    "action": "先压缩噪声并重建目标锚点。",
                }
            )
        elif entropy >= self.entropy_warning:
            hotspots.append(
                {
                    "id": "entropy-elevated",
                    "severity": "high",
                    "blocking": False,
                    "owner": "qiti-yuanliu",
                    "signal": entropy,
                    "reason": "上下文熵升高，后续输出稳定性会下降。",
                    "action": "执行轻量炁循环并限制新增规则数量。",
                }
            )

        if alignment < 85:
            hotspots.append(
                {
                    "id": "goal-anchor-drift",
                    "severity": "critical",
                    "blocking": True,
                    "owner": "qiti-yuanliu",
                    "signal": alignment,
                    "reason": "目标锚点对齐度过低，自动改写风险不可接受。",
                    "action": "回放用户原始目标并冻结自动目标重写。",
                }
            )
        elif alignment < 95:
            hotspots.append(
                {
                    "id": "alignment-soft-drift",
                    "severity": "medium",
                    "blocking": False,
                    "owner": "qiti-yuanliu",
                    "signal": alignment,
                    "reason": "目标对齐开始松动。",
                    "action": "在输出前追加一次目标回钩检查。",
                }
            )

        if consistency < 85:
            hotspots.append(
                {
                    "id": "consistency-break",
                    "severity": "high",
                    "blocking": True,
                    "owner": "qiti-yuanliu",
                    "signal": consistency,
                    "reason": "当前认知链冲突较多，继续推进会扩大偏差。",
                    "action": "先隔离冲突轮次，再恢复执行链。",
                }
            )
        elif consistency < 90:
            hotspots.append(
                {
                    "id": "consistency-watch",
                    "severity": "medium",
                    "blocking": False,
                    "owner": "qiti-yuanliu",
                    "signal": consistency,
                    "reason": "一致性有轻微波动。",
                    "action": "检查分支回答是否与用户纠偏一致。",
                }
            )

        if components.get("topic_drift", 0) > 1:
            hotspots.append(
                {
                    "id": "topic-drift",
                    "severity": "high",
                    "blocking": False,
                    "owner": "qiti-yuanliu",
                    "signal": components.get("topic_drift", 0),
                    "reason": "主题漂移已超过单轮可容忍范围。",
                    "action": "重新挂钩首轮目标并删去偏航上下文。",
                }
            )

        if components.get("intent_shift", 0) > 1:
            hotspots.append(
                {
                    "id": "intent-shift",
                    "severity": "medium",
                    "blocking": False,
                    "owner": "qiti-yuanliu",
                    "signal": components.get("intent_shift", 0),
                    "reason": "用户意图出现转向迹象。",
                    "action": "在重写计划前先确认最新需求。",
                }
            )

        if info_gaps > 0:
            hotspots.append(
                {
                    "id": "information-gap",
                    "severity": "medium",
                    "blocking": False,
                    "owner": "qiti-yuanliu",
                    "signal": info_gaps,
                    "reason": "存在未闭合问题，会阻断稳定恢复。",
                    "action": "将缺口转成显式待回答问题后再推进。",
                }
            )

        if escalation_contract.get("manual_review_required"):
            hotspots.append(
                {
                    "id": "manual-review-gate",
                    "severity": "critical",
                    "blocking": True,
                    "owner": "user",
                    "signal": escalation_contract.get("severity"),
                    "reason": "当前修复链路需要人工确认才能继续。",
                    "action": "等待人工确认后再恢复自演化。",
                }
            )

        hotspots.sort(
            key=lambda item: (
                self._severity_rank(item.get("severity")),
                0 if item.get("blocking") else 1,
                item.get("id", ""),
            )
        )
        return hotspots

    def _build_priority_actions(
        self,
        repair_handoff=None,
        self_evolution=None,
        stability_contract=None,
        repair_plan=None,
        escalation_contract=None,
        hotspots=None,
    ):
        self_evolution = self_evolution or self._build_self_evolution(repair_handoff)
        stability_contract = stability_contract or self._build_stability_contract(repair_handoff, self_evolution)
        repair_plan = repair_plan or self._build_repair_plan(repair_handoff, self_evolution, stability_contract)
        escalation_contract = escalation_contract or self._build_escalation_contract(
            repair_handoff, self_evolution, stability_contract, repair_plan
        )
        hotspots = hotspots or self._build_risk_hotspots(
            repair_handoff, self_evolution, stability_contract, escalation_contract
        )

        hotspot_map = {item["owner"]: item for item in hotspots if item.get("blocking")}
        actions = []
        for step in repair_plan.get("steps", []):
            blocking = bool(
                step.get("status") == "required"
                and step.get("id") in {"re-anchor-goal", "execute-handoff", "verify-resume"}
            )
            priority = "high" if step.get("status") == "required" else "medium"
            if blocking and (
                step.get("id") == "execute-handoff"
                or self.metrics.get("alignment", 100) < 85
                or self.metrics.get("entropy", 0) >= self.entropy_critical
            ):
                priority = "critical"
            owner = step.get("owner", "qiti-yuanliu")
            blocker_reason = hotspot_map.get(owner, {}).get("reason")
            actions.append(
                {
                    "id": step.get("id"),
                    "title": step.get("title"),
                    "priority": priority,
                    "blocking": blocking,
                    "owner": owner,
                    "action": step.get("action"),
                    "success_signal": step.get("completion_signal"),
                    "depends_on": [] if step.get("order", 0) <= 1 else [repair_plan["steps"][step["order"] - 2]["id"]],
                    "reason": blocker_reason or step.get("title"),
                }
            )

        if escalation_contract.get("manual_review_required"):
            actions.append(
                {
                    "id": "manual-review",
                    "title": "人工确认恢复门",
                    "priority": "critical",
                    "blocking": True,
                    "owner": "user",
                    "action": "确认当前修复结果是否允许恢复自演化。",
                    "success_signal": "manual_review_required=False",
                    "depends_on": ["verify-resume"],
                    "reason": "修复链路已进入人工确认门。",
                }
            )

        deduped = []
        seen = set()
        for item in sorted(
            actions,
            key=lambda entry: (
                self._severity_rank(entry.get("priority")),
                0 if entry.get("blocking") else 1,
                entry.get("depends_on", []),
            ),
        ):
            key = item.get("id")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _build_execution_contract(
        self,
        repair_handoff=None,
        self_evolution=None,
        stability_contract=None,
        repair_plan=None,
        escalation_contract=None,
        priority_actions=None,
        hotspots=None,
    ):
        self_evolution = self_evolution or self._build_self_evolution(repair_handoff)
        stability_contract = stability_contract or self._build_stability_contract(repair_handoff, self_evolution)
        repair_plan = repair_plan or self._build_repair_plan(repair_handoff, self_evolution, stability_contract)
        escalation_contract = escalation_contract or self._build_escalation_contract(
            repair_handoff, self_evolution, stability_contract, repair_plan
        )
        priority_actions = priority_actions or self._build_priority_actions(
            repair_handoff,
            self_evolution,
            stability_contract,
            repair_plan,
            escalation_contract,
        )
        hotspots = hotspots or self._build_risk_hotspots(
            repair_handoff, self_evolution, stability_contract, escalation_contract
        )

        next_action = priority_actions[0] if priority_actions else None
        blocking_actions = [item["id"] for item in priority_actions if item.get("blocking")]
        return {
            "operating_mode": stability_contract.get("operating_mode"),
            "autonomy_budget": stability_contract.get("mutation_budget", {}).get("mode"),
            "resume_ready": not stability_contract.get("freeze_self_evolution")
            and not escalation_contract.get("manual_review_required")
            and not repair_handoff,
            "manual_review_required": escalation_contract.get("manual_review_required", False),
            "queue_depth": len(priority_actions),
            "blocking_actions": blocking_actions,
            "blocking_action_count": len(blocking_actions),
            "next_owner": next_action.get("owner") if next_action else "qiti-yuanliu",
            "next_action_id": next_action.get("id") if next_action else None,
            "next_action": next_action.get("action") if next_action else "继续当前炁循环",
            "max_parallel_actions": 1 if repair_handoff or stability_contract.get("freeze_self_evolution") else 2,
            "dispatch_hint": repair_handoff.get("target_skill") if repair_handoff else "qiti-yuanliu",
            "hotspot_count": len(hotspots),
            "halt_conditions": escalation_contract.get("escalation_triggers", []),
            "resume_gate": stability_contract.get("resume_conditions", []),
        }

    def _goal_anchor(self):
        for msg in self.context:
            if msg.get("role") == "user" and msg.get("content"):
                return msg.get("content", "")[: self.first_goal_length]
        if not self.context:
            return ""
        return self.context[0].get("content", "")[: self.first_goal_length]

    def _extract_directive_fragments(self, text: str) -> list:
        if not text:
            return []
        directive_markers = ("不要", "别", "禁止", "必须", "优先", "保持", "只", "先", "改成", "改回", "需要")
        directives = []
        for clause in re.split(r"[，。；;,.!?？！]\s*", text):
            clause = clause.strip()
            if clause and any(marker in clause for marker in directive_markers):
                directives.append(clause[:28])
        return directives[:3]

    def _derive_decision_style(self):
        traits = []
        if self.metrics.get("completeness", 0) >= 70:
            traits.append("链式推理")
        if self.metrics.get("density") == "high":
            traits.append("高密表达")
        if self.metrics.get("alignment", 0) >= 95:
            traits.append("目标锁定")
        if self.metrics.get("entropy_level") == "red":
            traits.append("失稳待修")
        return traits or ["通用执行"]

    def _collect_origin_core(self):
        goal_anchor = self._goal_anchor()
        constraints = []
        user_keywords = Counter()
        for msg in self.context:
            content = msg.get("content", "")
            if msg.get("role") == "user":
                constraints.extend(self._extract_directive_fragments(content))
                for kw in self._extract_keywords(content):
                    if len(kw) >= 2 and not kw.isdigit():
                        user_keywords[kw] += 1

        recurring_intents = [kw for kw, _ in user_keywords.most_common(5)]
        unique_constraints = []
        for item in constraints:
            if item not in unique_constraints:
                unique_constraints.append(item)

        return {
            "goal_anchor": goal_anchor,
            "active_constraints": unique_constraints[:5],
            "recurring_intents": recurring_intents,
            "decision_style": self._derive_decision_style(),
        }

    def _build_rule_candidates(self, repair_handoff=None):
        origin_core = self._collect_origin_core()
        components = self.metrics.get("entropy_components", {})
        contradictions = self._count_semantic_contradictions()
        correction_events = self._collect_correction_events()
        candidates = []

        for constraint in origin_core.get("active_constraints", []):
            candidates.append(
                {
                    "rule": f"持续遵守用户约束：{constraint}",
                    "status": "reinforce",
                    "confidence": "medium",
                    "source": "user_directive",
                    "evidence_rounds": [],
                    "action": "将该约束加入当前炁循环的显式执行规则",
                }
            )

        if contradictions or correction_events:
            rounds = sorted(
                {
                    item.get("round")
                    for item in [*contradictions, *correction_events]
                    if item.get("round") is not None
                }
            )
            candidates.append(
                {
                    "rule": "最近一次用户纠偏高于既有执行惯性",
                    "status": "reinforce",
                    "confidence": "high",
                    "source": "correction_repair",
                    "evidence_rounds": rounds,
                    "action": "冻结最近一次用户纠偏为新的目标锚点",
                }
            )

        if self._count_info_gaps() > 0:
            candidates.append(
                {
                    "rule": "遇到未闭合问题时先补全缺口再推进执行",
                    "status": "grow",
                    "confidence": "medium",
                    "source": "info_gap",
                    "evidence_rounds": [],
                    "action": "将待回答问题提升为当前回合的优先动作",
                }
            )

        if components.get("topic_drift", 0) > 1:
            candidates.append(
                {
                    "rule": "每轮输出前回钩首轮目标锚点",
                    "status": "grow",
                    "confidence": "high",
                    "source": "topic_drift",
                    "evidence_rounds": [],
                    "action": "输出前追加一次目标对齐检查",
                }
            )

        if components.get("intent_shift", 0) > 1:
            candidates.append(
                {
                    "rule": "检测到转折意图时先确认再重写执行路径",
                    "status": "grow",
                    "confidence": "medium",
                    "source": "intent_shift",
                    "evidence_rounds": [],
                    "action": "在计划改写前请求一次需求确认",
                }
            )

        if repair_handoff:
            candidates.append(
                {
                    "rule": "高矛盾密度时触发跨段追踪与锚点重建",
                    "status": "seal",
                    "confidence": "high",
                    "source": "repair_handoff",
                    "evidence_rounds": repair_handoff.get("contradiction_rounds", []),
                    "action": f"调用 {repair_handoff.get('target_skill', 'dalu-dongguan')} 执行锚点修复",
                }
            )

        deduped = []
        seen = set()
        for item in candidates:
            key = item["rule"]
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        return deduped

    def _build_mutation_pressure(self):
        components = self.metrics.get("entropy_components", {})
        contradiction_count = components.get("conflict", 0)
        score = min(
            10.0,
            round(
                self.metrics.get("entropy", 0) * 0.7
                + contradiction_count * 0.8
                + components.get("topic_drift", 0) * 1.2
                + components.get("intent_shift", 0),
                2,
            ),
        )
        if score >= 7:
            level = "high"
        elif score >= 3:
            level = "medium"
        else:
            level = "low"

        drivers = []
        if contradiction_count:
            drivers.append("用户纠偏与既有路径冲突")
        if components.get("topic_drift", 0) > 0:
            drivers.append("目标漂移")
        if components.get("intent_shift", 0) > 0:
            drivers.append("意图转向")
        if self._count_info_gaps() > 0:
            drivers.append("未闭合问题")

        return {"score": score, "level": level, "drivers": drivers}

    def _build_self_evolution(self, repair_handoff=None):
        origin_core = self._collect_origin_core()
        mutation_pressure = self._build_mutation_pressure()
        rule_candidates = self._build_rule_candidates(repair_handoff)
        correction_events = self._collect_correction_events()

        if self.metrics.get("entropy", 0) >= self.entropy_critical or repair_handoff:
            phase = "stabilize"
        elif mutation_pressure["level"] == "medium" or self.metrics.get("alignment", 100) < 95 or correction_events:
            phase = "refine"
        else:
            phase = "advance"

        risk_reasons = []
        if mutation_pressure["level"] == "high":
            risk_reasons.append("过度自我修正可能导致目标偏执")
        if self.metrics.get("alignment", 100) < 90:
            risk_reasons.append("目标锚点松动")
        if self.metrics.get("consistency", 100) < 85:
            risk_reasons.append("既有认知链存在冲突")

        autonomy_risk = {
            "level": "high" if risk_reasons else "medium" if mutation_pressure["level"] == "medium" else "low",
            "reasons": risk_reasons or ["当前自我修正风险可控"],
        }

        next_cycle = [item["action"] for item in rule_candidates[:4]]
        return {
            "phase": phase,
            "origin_core": origin_core,
            "mutation_pressure": mutation_pressure,
            "rule_candidates": rule_candidates,
            "autonomy_risk": autonomy_risk,
            "next_cycle": next_cycle,
            "correction_events": correction_events,
        }

    def _build_stability_contract(self, repair_handoff=None, self_evolution=None):
        self_evolution = self_evolution or self._build_self_evolution(repair_handoff)
        mutation_pressure = self_evolution.get("mutation_pressure", {})
        freeze_reasons = []

        if repair_handoff:
            freeze_reasons.append("重复矛盾已触发跨段修复")
        if self.metrics.get("entropy", 0) >= self.entropy_critical:
            freeze_reasons.append("上下文熵进入红区")
        if self.metrics.get("alignment", 100) < 90:
            freeze_reasons.append("目标锚点对齐度不足")
        if self.metrics.get("consistency", 100) < 85:
            freeze_reasons.append("认知链一致性不足")

        freeze_self_evolution = bool(freeze_reasons)
        if freeze_self_evolution:
            mode = "frozen"
            max_rule_changes = 1
            max_goal_anchor_changes = 0
            allow_new_rules = False
            allow_goal_rewrite = False
        elif mutation_pressure.get("level") == "medium":
            mode = "guarded"
            max_rule_changes = 2
            max_goal_anchor_changes = 0
            allow_new_rules = True
            allow_goal_rewrite = False
        else:
            mode = "adaptive"
            max_rule_changes = 4
            max_goal_anchor_changes = 1
            allow_new_rules = True
            allow_goal_rewrite = True

        allowed_actions = [
            "复述并锁定当前 goal_anchor",
            "整理矛盾轮次与证据",
            "生成有限规则候选",
        ]
        if allow_new_rules:
            allowed_actions.append("执行轻量规则生长")
        if allow_goal_rewrite:
            allowed_actions.append("在低风险场景下调整目标表达")

        blocked_actions = [
            "绕过 goal_anchor 直接改写执行目标",
            "在未校验前扩张规则作用域",
        ]
        if freeze_self_evolution:
            blocked_actions.append("继续自动追加自演化规则")
        if not allow_goal_rewrite:
            blocked_actions.append("未经确认的目标锚点改写")

        return {
            "operating_mode": mode,
            "freeze_self_evolution": freeze_self_evolution,
            "freeze_reasons": freeze_reasons or ["当前上下文允许继续受控自演化"],
            "mutation_budget": {
                "mode": mode,
                "max_rule_changes": max_rule_changes,
                "max_goal_anchor_changes": max_goal_anchor_changes,
                "allow_new_rules": allow_new_rules,
                "allow_goal_rewrite": allow_goal_rewrite,
                "allowed_actions": allowed_actions,
                "blocked_actions": blocked_actions,
            },
            "resume_conditions": [
                {"check": "health_score", "operator": ">=", "target": 75},
                {"check": "consistency", "operator": ">=", "target": 85},
                {"check": "alignment", "operator": ">=", "target": 92},
                {"check": "repair_handoff", "operator": "completed_if_triggered", "target": bool(repair_handoff)},
            ],
            "verification_targets": {
                "health_score_min": 75,
                "consistency_min": 85,
                "alignment_min": 92,
                "allowed_entropy_levels": ["green", "yellow"],
                "requires_handoff_completion": bool(repair_handoff),
            },
        }

    def _build_repair_plan(self, repair_handoff=None, self_evolution=None, stability_contract=None):
        self_evolution = self_evolution or self._build_self_evolution(repair_handoff)
        stability_contract = stability_contract or self._build_stability_contract(repair_handoff, self_evolution)
        origin_core = self_evolution.get("origin_core", {})
        rule_count = len(self_evolution.get("rule_candidates", []))
        contradiction_rounds = repair_handoff.get("contradiction_rounds", []) if repair_handoff else []

        steps = [
            {
                "order": 1,
                "id": "re-anchor-goal",
                "title": "重申目标锚点",
                "status": "required",
                "owner": "qiti-yuanliu",
                "action": f"锁定 goal_anchor 并回放约束：{origin_core.get('goal_anchor', '')[:40]}",
                "completion_signal": "goal_anchor 已显式复述且约束列表已展开",
            },
            {
                "order": 2,
                "id": "isolate-conflicts",
                "title": "隔离矛盾与漂移",
                "status": "required",
                "owner": "qiti-yuanliu",
                "action": (
                    "按轮次整理矛盾、意图转向与未闭合问题"
                    if contradiction_rounds
                    else "整理当前风险信号并确认是否存在潜在漂移"
                ),
                "completion_signal": "已形成冲突轮次清单与风险摘要",
            },
            {
                "order": 3,
                "id": "execute-handoff" if repair_handoff else "lightweight-repair",
                "title": "执行修复路径",
                "status": "required" if repair_handoff else "recommended",
                "owner": repair_handoff.get("target_skill", "qiti-yuanliu") if repair_handoff else "qiti-yuanliu",
                "action": (
                    f"调用 {repair_handoff.get('target_skill')} 执行 {repair_handoff.get('action')}"
                    if repair_handoff
                    else "执行轻量炁循环，对齐目标并压缩上下文噪声"
                ),
                "completion_signal": (
                    "repair_handoff 返回跨段追踪结果"
                    if repair_handoff
                    else "上下文噪声降低且风险信号未继续扩张"
                ),
            },
            {
                "order": 4,
                "id": "rebuild-rules",
                "title": "收敛规则候选",
                "status": "required",
                "owner": "qiti-yuanliu",
                "action": f"在 {stability_contract['mutation_budget']['mode']} 模式下筛选 {rule_count} 条规则候选",
                "completion_signal": "保留的规则候选与目标锚点一致且未越权",
            },
            {
                "order": 5,
                "id": "verify-resume",
                "title": "验证恢复门",
                "status": "required",
                "owner": "qiti-yuanliu",
                "action": "按 verification_targets 重新计算健康分、一致性、对齐度和 handoff 状态",
                "completion_signal": "全部 resume_conditions 满足后才允许恢复自演化",
            },
        ]

        return {
            "mode": "handoff-repair" if repair_handoff else "self-repair",
            "step_count": len(steps),
            "primary_action": steps[2]["action"],
            "steps": steps,
            "resume_gate": stability_contract.get("resume_conditions", []),
            "rollback_point": "回退到 origin_core.goal_anchor 与 active_constraints",
        }

    def _build_escalation_contract(
        self,
        repair_handoff=None,
        self_evolution=None,
        stability_contract=None,
        repair_plan=None,
    ):
        self_evolution = self_evolution or self._build_self_evolution(repair_handoff)
        stability_contract = stability_contract or self._build_stability_contract(repair_handoff, self_evolution)
        repair_plan = repair_plan or self._build_repair_plan(repair_handoff, self_evolution, stability_contract)

        severity = "low"
        if self.metrics.get("health_level") == "danger" or self.metrics.get("alignment", 100) < 85:
            severity = "high"
        elif stability_contract.get("freeze_self_evolution") or self_evolution.get("mutation_pressure", {}).get("level") == "high":
            severity = "medium"

        contradiction_rounds = repair_handoff.get("contradiction_rounds", []) if repair_handoff else []
        blockers = []
        if repair_handoff:
            blockers.append("需要完成跨段追踪并确认修复结果")
        if self.metrics.get("alignment", 100) < 85:
            blockers.append("目标锚点对齐度过低，禁止自动改写目标")
        if self.metrics.get("health_score", 100) < 60:
            blockers.append("健康分过低，需人工确认后再恢复")

        manual_review_required = (
            self.metrics.get("health_score", 100) < 60
            or self.metrics.get("alignment", 100) < 85
            or len(contradiction_rounds) >= 2
        )

        return {
            "severity": severity,
            "manual_review_required": manual_review_required,
            "escalation_targets": ["user"] + ([repair_handoff.get("target_skill")] if repair_handoff else []),
            "current_blockers": blockers,
            "escalation_triggers": [
                {"condition": "health_score < 60", "action": "冻结自演化并升级人工确认"},
                {"condition": "alignment < 85", "action": "禁止自动改写目标锚点"},
                {
                    "condition": "repair_handoff 未完成且 requires_handoff_completion=True",
                    "action": "保持 frozen 模式并等待下游修复结果",
                },
            ],
            "max_auto_retries": 1 if repair_handoff else 0,
            "fallback_mode": "anchor-only",
            "resume_dependency": "verify-resume",
        }

    def _build_stability_checkpoints(
        self,
        repair_handoff=None,
        stability_contract=None,
        repair_plan=None,
        escalation_contract=None,
    ):
        stability_contract = stability_contract or self._build_stability_contract(repair_handoff)
        repair_plan = repair_plan or self._build_repair_plan(repair_handoff, stability_contract=stability_contract)
        escalation_contract = escalation_contract or self._build_escalation_contract(
            repair_handoff,
            stability_contract=stability_contract,
            repair_plan=repair_plan,
        )
        checkpoint_list = [
            {
                "stage": "pre_repair",
                "required": True,
                "objective": "确认 goal_anchor 与 active_constraints 可回放",
                "pass_signal": "origin_core 已锁定且冻结原因已记录",
            },
            {
                "stage": "post_handoff",
                "required": bool(repair_handoff),
                "objective": "确认跨段追踪或轻量修复已完成",
                "pass_signal": "repair_handoff 完成或 repair_plan 第 3 步达成",
            },
            {
                "stage": "pre_resume",
                "required": True,
                "objective": "满足 resume_conditions 后再恢复自演化",
                "pass_signal": "health_score/consistency/alignment 达标且 blocker 清零",
            },
        ]

        return {
            "current_mode": stability_contract.get("operating_mode"),
            "checkpoint_count": len(checkpoint_list),
            "manual_review_required": escalation_contract.get("manual_review_required", False),
            "checkpoints": checkpoint_list,
        }

    def _build_repair_handoff(self):
        """在重复矛盾达到阈值时生成结构化修复交接单。"""
        contradictions = self._count_semantic_contradictions()
        if len(contradictions) < self.repair_handoff_threshold:
            return None

        evidence = []
        for item in contradictions[:self.repair_handoff_evidence_limit]:
            entry = {
                "round": item.get("round"),
                "type": item.get("type"),
            }
            if item.get("keyword"):
                entry["keyword"] = item["keyword"]
            if item.get("pattern"):
                entry["pattern"] = item["pattern"]
            if item.get("density") is not None:
                entry["density"] = item["density"]
            if item.get("preview"):
                entry["preview"] = item["preview"]
            evidence.append(entry)

        contradiction_rounds = sorted(
            {item.get("round") for item in contradictions if item.get("round") is not None}
        )
        observed_alerts = len(contradictions)
        return {
            "triggered": True,
            "target_skill": self.repair_handoff_target,
            "action": self.repair_handoff_action,
            "reason": self.repair_handoff_reason,
            "alert_threshold": self.repair_handoff_threshold,
            "observed_alerts": observed_alerts,
            "contradiction_rounds": contradiction_rounds,
            "summary": (
                f"检测到 {observed_alerts} 条矛盾警报，建议切换至"
                f"{self.repair_handoff_target}执行跨段追踪与锚点修复"
            ),
            "evidence": evidence,
        }

    def _generate_dna_snapshot(self):
        """生成DNA快照哈希"""
        key_decisions = [msg.get("content", "")[:self.dna_preview] for msg in self.context[-self.dna_rounds:]]
        snapshot_raw = "|".join(key_decisions)
        dna_hash = hex(hash(snapshot_raw) & 0xFFFFFF)[2:].zfill(6)
        return {
            "hash": dna_hash,
            "based_on": f"last_{self.dna_rounds}_rounds",
            "timestamp": "auto",
        }


# ── CLI ─────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("用法: python entropy_scanner.py <context.json>")
        print('  context.json: [{"role":"user","content":"...","round":1}, ...]')
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"错误: 文件不存在 {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        context_data = json.load(f)

    # 输入验证
    ok, errs = validate_json_list(context_data, {"content": str}, "qiti-yuanliu")
    if not ok:
        print(f"输入验证失败: {errs}")
        sys.exit(2)

    scanner = QiTiScanner(context_data)
    report = scanner.scan()

    output_path = input_path.with_suffix(".health_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("=" * 50)
    print("📊 炁体源流 · 上下文健康报告  V6.1")
    print("=" * 50)
    print(f"  对话轮次: {report['context_length']}")
    print(f"  上下文熵: {report['metrics']['entropy']} ({report['metrics']['entropy_level']})")
    if report['metrics'].get('entropy_components'):
        comp = report['metrics']['entropy_components']
        print(f"    ├─ 矛盾: {comp['conflict']} | 缺口: {comp['gap']} | 冗余: {comp['redundancy']}")
        print(f"    ├─ 主题漂移: {comp['topic_drift']} | 意图偏移: {comp['intent_shift']}")
    print(f"  一致性: {report['metrics']['consistency']}%")
    print(f"  对齐度: {report['metrics']['alignment']}%")
    print(f"  推理完整度: {report['metrics']['completeness']}%")
    print(f"  信息密度: {report['metrics']['density']} (实词比: {report['metrics'].get('content_word_ratio', 'N/A')})")
    print(f"  健康总分: {report['metrics']['health_score']} ({report['metrics']['health_level']})")
    print(f"  DNA快照: {report['dna_snapshot']['hash']}")
    print(f"  自进化阶段: {report['self_evolution']['phase']}")
    print(f"  稳态模式: {report['stability_contract']['operating_mode']}")
    if report.get("origin_core", {}).get("goal_anchor"):
        print(f"  目标锚点: {report['origin_core']['goal_anchor'][:40]}")
    print(f"  规则候选: {len(report['self_evolution'].get('rule_candidates', []))}")
    print(f"  修复步骤: {report['repair_plan']['step_count']}")
    print("-" * 50)
    print("🚨 警报:")
    for alert in report["alerts"]:
        emoji = "🔴" if alert["level"] == "danger" else "🟡"
        print(f"  {emoji} [{alert['type']}] {alert['message']}")
    if not report["alerts"]:
        print("  ✅ 无警报")
    print("-" * 50)
    print("💡 建议:")
    for rec in report["recommendations"]:
        print(f"  • {rec}")
    print("=" * 50)
    print(f"详细报告已保存: {output_path}")


if __name__ == "__main__":
    main()
