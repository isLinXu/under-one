#!/usr/bin/env python3
"""
器名: 知识消化器 (Knowledge Digest)
用途: 评估信息消化率，生成知识单元，计算保鲜期
输入: JSON [{"source":"来源","content":"文本","credibility":"S"}]
输出: JSON {digest_rate,knowledge_units,freshness_schedule}
版本: V5.4 — 配置化重构 + 梯度评分 + 信息密度因子 + 污染风险分层
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# ── 路径设置 ───────────────────────────────────────────────
SKILL_ROOT = Path(__file__).resolve().parent.parent  # liuku-xianzei/
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


class KnowledgeDigest:
    """V5.4 知识消化器 — 配置化 + 梯度评分 + 信息密度因子 + 污染风险分层"""

    # ── 硬编码默认值（配置不可用时回退） ────────────────────
    _DEFAULT_CREDIBILITY_WEIGHT = {"S": 1.5, "A": 1.2, "B": 1.0, "C": 0.6}
    _DEFAULT_FRESHNESS_DAYS = {
        "技术方案": 90,
        "行业数据": 180,
        "基础理论": 1095,
        "法律法规": 7,
        "社区经验": 90,
        "默认": 180,
    }
    _DEFAULT_KEYWORDS = {
        "core_claim": ["是", "为", "指", "提出", "表明", "证明", "发现", "结论", "显示", "研究", "通过", "实现", "解决", "提升", "降低", "改进", "验证", "基于", "核心", "本质"],
        "evidence": ["数据", "统计", "研究表明", "因为", "实验", "测试", "结果", "证据", "报告", "分析", "量化", "对比"],
        "application": ["用于", "应用", "场景", "案例", "实践", "部署", "实施", "落地", "适用于", "在...中"],
        "short_text": ["推荐", "版本", "使用", "支持", "需要", "建议", "依赖", "兼容", "要求", "配置"],
    }
    _DEFAULT_SEMANTIC_HINTS = {
        "summary_openers": ["结论", "总结", "关键发现", "核心观点", "观察", "建议", "说明", "意味着"],
        "evidence_markers": ["样本", "监控", "日志", "反馈", "回归", "实验", "测试", "统计", "对比", "结果", "验证", "指标"],
        "application_markers": ["上线", "部署", "落地", "接入", "复用", "适用", "适合", "实践", "方案", "优化"],
        "causal_markers": ["因此", "所以", "说明", "意味着", "从而", "使得", "由此", "可见"],
        "domain_terms": ["性能", "延迟", "成本", "用户", "转化", "缓存", "稳定性", "接口", "生产", "检索", "召回", "准确率"],
    }
    _DEFAULT_ELEMENT_WEIGHTS = {"core_claim": 0.40, "evidence": 0.30, "application": 0.30}
    _DEFAULT_DIGESTION_THRESHOLDS = {"high": 80, "medium": 50}
    _DEFAULT_SCORING_GRADIENT = {"core_claim_max": 5, "evidence_max": 4, "application_max": 4}
    _DEFAULT_DENSITY_FACTOR = {
        "short_text_limit": 50,
        "short_bonus": 1.05,
        "optimal_min": 80,
        "optimal_max": 500,
        "optimal_bonus": 1.10,
        "long_penalty_threshold": 1000,
        "long_penalty": 0.95,
    }
    _DEFAULT_REVIEW_SCHEDULE = [
        {"level": "低", "min_rate": 0, "max_rate": 50, "time": "4小时", "reason": "低消化率，需尽快复习"},
        {"level": "中", "min_rate": 50, "max_rate": 80, "time": "1天", "reason": "待补充理解"},
        {"level": "高", "min_rate": 80, "max_rate": 100, "time": "7天", "reason": "巩固记忆"},
    ]
    _DEFAULT_CONTAMINATION_WEIGHTS = {
        "credibility": 0.35,
        "rate_gap": 0.30,
        "signal_gap": 0.20,
        "short_text": 0.15,
    }
    _DEFAULT_INHERITANCE_RULES = {
        "min_rate": 80,
        "trusted_credibilities": ["S", "A"],
        "max_risk": 0.35,
    }

    def __init__(self, info_items):
        self.items = info_items
        self.units = []
        self.inheritance_queue = []
        self.quarantine_queue = []
        self.contamination_risk = {}
        # 加载配置
        self._load_config()

    def _load_config(self):
        """从 under-one.yaml 加载 liukuxianzei 配置段"""
        cfg = get_skill_config("liukuxianzei", default={})

        # 可信度权重
        cw = cfg.get("credibility_weights", {})
        self.credibility_weight = {k: float(v) for k, v in cw.items()} if cw else self._DEFAULT_CREDIBILITY_WEIGHT.copy()

        # 保鲜期（天 → timedelta）
        fd = cfg.get("freshness_days", {})
        self.freshness_rules = {
            k: timedelta(days=int(v))
            for k, v in (fd if fd else self._DEFAULT_FRESHNESS_DAYS).items()
        }

        # 关键词
        kw = cfg.get("keywords", {})
        self.keywords = {
            cat: list(kw.get(cat, self._DEFAULT_KEYWORDS.get(cat, [])))
            for cat in ("core_claim", "evidence", "application", "short_text")
        }

        # 三要素权重
        ew = cfg.get("element_weights", {})
        self.element_weights = {
            k: float(v)
            for k, v in (ew if ew else self._DEFAULT_ELEMENT_WEIGHTS).items()
        }

        # 消化率阈值
        dt = cfg.get("digestion_thresholds", {})
        self.digestion_thresholds = {
            k: int(v)
            for k, v in (dt if dt else self._DEFAULT_DIGESTION_THRESHOLDS).items()
        }

        # 评分梯度（最大期望匹配数）
        sg = cfg.get("scoring_gradient", {})
        self.scoring_gradient = {
            k: int(v)
            for k, v in (sg if sg else self._DEFAULT_SCORING_GRADIENT).items()
        }

        # 信息密度因子
        df = cfg.get("density_factor", {})
        self.density_factor = {
            k: (float(v) if isinstance(v, (int, float)) else int(v))
            for k, v in (df if df else self._DEFAULT_DENSITY_FACTOR).items()
        }

        # 反刍调度规则
        rs = cfg.get("review_schedule", [])
        self.review_schedule_rules = list(rs if rs else self._DEFAULT_REVIEW_SCHEDULE)

        # 污染风险与继承门槛
        self.contamination_weights = {
            k: float(v)
            for k, v in (cfg.get("contamination_weights", {}) or self._DEFAULT_CONTAMINATION_WEIGHTS).items()
        }
        self.inheritance_rules = {
            "min_rate": int((cfg.get("inheritance_rules", {}) or {}).get("min_rate", self._DEFAULT_INHERITANCE_RULES["min_rate"])),
            "trusted_credibilities": list((cfg.get("inheritance_rules", {}) or {}).get("trusted_credibilities", self._DEFAULT_INHERITANCE_RULES["trusted_credibilities"])),
            "max_risk": float((cfg.get("inheritance_rules", {}) or {}).get("max_risk", self._DEFAULT_INHERITANCE_RULES["max_risk"])),
        }
        hints = cfg.get("semantic_hints", {})
        self.semantic_hints = {
            key: list(hints.get(key, self._DEFAULT_SEMANTIC_HINTS.get(key, [])))
            for key in self._DEFAULT_SEMANTIC_HINTS
        }

    # ── 核心算法：梯度评分 + 信息密度 ─────────────────────────

    def _count_matches(self, text, keywords):
        """统计文本中匹配的关键词数量（去重计数）"""
        matched = set()
        for kw in keywords:
            if kw in text:
                matched.add(kw)
        return len(matched)

    def _gradient_score(self, match_count, max_expected, full_score):
        """梯度评分：按匹配比例分配分数，上限 full_score"""
        if max_expected <= 0:
            return full_score if match_count > 0 else 0
        ratio = min(1.0, match_count / max_expected)
        # 非线性：前50%匹配给80%分，后50%给20%分（鼓励多维度覆盖）
        if ratio <= 0.5:
            nonlinear = ratio * 1.6  # 0.5 → 0.8
        else:
            nonlinear = 0.8 + (ratio - 0.5) * 0.4  # 1.0 → 1.0
        return round(full_score * min(1.0, nonlinear), 1)

    def _density_multiplier(self, text_length):
        """信息密度因子：短文本补偿 / 最优长度奖励 / 超长惩罚"""
        df = self.density_factor
        short_limit = df.get("short_text_limit", 50)
        short_bonus = df.get("short_bonus", 1.05)
        optimal_min = df.get("optimal_min", 80)
        optimal_max = df.get("optimal_max", 500)
        optimal_bonus = df.get("optimal_bonus", 1.10)
        long_threshold = df.get("long_penalty_threshold", 1000)
        long_penalty = df.get("long_penalty", 0.95)

        if text_length <= short_limit:
            return short_bonus
        if optimal_min <= text_length <= optimal_max:
            return optimal_bonus
        if text_length >= long_threshold:
            return long_penalty
        return 1.0

    def _semantic_profile(self, text):
        """中文摘要风格的语义信号扫描，降低纯关键词评估的误伤率。"""
        text = text or ""
        normalized = text.replace("：", ":")
        sentence_count = len([seg for seg in re.split(r"[。！？!?；;]\s*", text) if seg.strip()])
        numeric_markers = len(re.findall(r"\d+(?:\.\d+)?(?:%|倍|次|人|ms|秒|天|周|月|年)?", normalized))
        summary_anchor_count = sum(1 for marker in self.semantic_hints["summary_openers"] if marker in normalized)
        evidence_marker_count = sum(1 for marker in self.semantic_hints["evidence_markers"] if marker in normalized)
        application_marker_count = sum(1 for marker in self.semantic_hints["application_markers"] if marker in normalized)
        causal_marker_count = sum(1 for marker in self.semantic_hints["causal_markers"] if marker in normalized)
        domain_term_count = sum(1 for marker in self.semantic_hints["domain_terms"] if marker in normalized)
        has_structured_summary = ":" in normalized and any(marker in normalized for marker in self.semantic_hints["summary_openers"])
        evidence_strength = evidence_marker_count + min(2, numeric_markers) + (1 if causal_marker_count else 0)
        application_strength = application_marker_count + (1 if "建议" in normalized else 0)
        core_strength = summary_anchor_count + (1 if sentence_count >= 2 else 0) + (1 if domain_term_count >= 2 else 0)
        semantic_bonus = min(
            18,
            summary_anchor_count * 3
            + min(6, numeric_markers * 2)
            + min(4, evidence_marker_count * 2)
            + min(4, application_marker_count * 2)
            + (2 if causal_marker_count else 0)
            + (2 if has_structured_summary else 0)
            + (2 if sentence_count >= 2 and domain_term_count >= 2 else 0),
        )
        signal_count = sum(
            1
            for flag in (
                core_strength > 0,
                evidence_strength > 0,
                application_strength > 0,
                has_structured_summary,
            )
            if flag
        )
        return {
            "summary_anchor_count": summary_anchor_count,
            "numeric_markers": numeric_markers,
            "evidence_marker_count": evidence_marker_count,
            "application_marker_count": application_marker_count,
            "causal_marker_count": causal_marker_count,
            "domain_term_count": domain_term_count,
            "has_structured_summary": has_structured_summary,
            "sentence_count": sentence_count,
            "semantic_bonus": semantic_bonus,
            "signal_count": signal_count,
            "core_strength": core_strength,
            "evidence_strength": evidence_strength,
            "application_strength": application_strength,
        }

    def _compute_digestion_rate(self, text, credibility, is_short):
        """V5.3 消化率计算：梯度评分 + 可信度加权 + 密度因子"""
        kw = self.keywords
        sg = self.scoring_gradient
        ew = self.element_weights
        semantic_profile = self._semantic_profile(text)

        # 短文本适配：核心论点检测合并短文本关键词
        core_keywords = kw["core_claim"]
        if is_short:
            core_keywords = list(set(kw["core_claim"] + kw["short_text"]))

        # 三要素匹配计数
        core_matches = self._count_matches(text, core_keywords)
        evidence_matches = self._count_matches(text, kw["evidence"])
        app_matches = self._count_matches(text, kw["application"])

        # 语义信号补偿：中文摘要和证据型表达不应只靠字面关键词存活。
        if semantic_profile["core_strength"] > 0:
            core_matches = max(core_matches, min(sg.get("core_claim_max", 5), semantic_profile["core_strength"]))
        if semantic_profile["evidence_strength"] > 0:
            evidence_matches = max(evidence_matches, min(sg.get("evidence_max", 4), semantic_profile["evidence_strength"]))
        if semantic_profile["application_strength"] > 0:
            app_matches = max(app_matches, min(sg.get("application_max", 4), semantic_profile["application_strength"]))

        # 短文本默认给予基础证据/应用分（存在即合理，但不白给满分）
        if is_short:
            evidence_matches = max(1, evidence_matches)
            app_matches = max(1, app_matches)

        # 按 element_weights 分配满分比例（默认 40/30/30 = 100）
        total_w = sum(ew.values())
        core_full = 100 * ew.get("core_claim", 0.40) / total_w
        ev_full = 100 * ew.get("evidence", 0.30) / total_w
        app_full = 100 * ew.get("application", 0.30) / total_w

        # 梯度评分
        core_score = self._gradient_score(core_matches, sg.get("core_claim_max", 5), core_full)
        evidence_score = self._gradient_score(evidence_matches, sg.get("evidence_max", 4), ev_full)
        app_score = self._gradient_score(app_matches, sg.get("application_max", 4), app_full)

        # 三要素分数直接相加（满分100）
        digestion_score = core_score + evidence_score + app_score + semantic_profile["semantic_bonus"]

        # 信息密度因子
        density_mult = self._density_multiplier(len(text))
        digestion_score = min(100, digestion_score * density_mult)

        # 可信度加权
        weight = self.credibility_weight.get(credibility, 1.0)
        effective_digestion = min(100, digestion_score * weight)

        return (
            round(effective_digestion, 1),
            core_matches,
            evidence_matches,
            app_matches,
            semantic_profile,
        )

    def _digestion_level(self, rate):
        """根据配置阈值判定消化等级"""
        th = self.digestion_thresholds
        high = th.get("high", 80)
        medium = th.get("medium", 50)
        if rate > high:
            return "高"
        if rate > medium:
            return "中"
        return "低"

    def _review_plan(self, level, rate, concept):
        """根据配置规则生成反刍计划"""
        for rule in self.review_schedule_rules:
            min_r = rule.get("min_rate", 0)
            max_r = rule.get("max_rate", 100)
            if min_r <= rate <= max_r:
                return {
                    "concept": concept,
                    "review_in": rule.get("time", "1天"),
                    "reason": rule.get("reason", "待复习"),
                    "level": rule.get("level", level),
                }
        # 兜底
        return {"concept": concept, "review_in": "1天", "reason": "待复习", "level": level}

    def _contamination_score(self, text, credibility, rate, core_matches, evidence_matches, application_matches, is_short, semantic_profile=None):
        """评估单元污染风险：可信度越低、消化越差、信号越少，风险越高。"""
        semantic_profile = semantic_profile or {}
        cred_map = {"S": 0.05, "A": 0.15, "B": 0.35, "C": 0.55}
        signal_count = max(
            core_matches + evidence_matches + application_matches,
            int(semantic_profile.get("signal_count", 0)),
        )
        signal_gap = 0.0 if signal_count >= 3 else 0.15 if signal_count == 2 else 0.28 if signal_count == 1 else 0.42
        short_penalty = 0.08 if is_short and rate < 60 else 0.0
        risk = (
            cred_map.get(credibility, 0.35) * self.contamination_weights.get("credibility", 0.35)
            + max(0.0, 1.0 - rate / 100.0) * self.contamination_weights.get("rate_gap", 0.30)
            + signal_gap * self.contamination_weights.get("signal_gap", 0.20)
            + short_penalty * self.contamination_weights.get("short_text", 0.15)
        )
        risk = min(1.0, risk)
        if risk >= 0.7:
            level = "high"
        elif risk >= 0.4:
            level = "medium"
        else:
            level = "low"
        reasons = []
        if credibility == "C":
            reasons.append("低可信度来源")
        elif credibility == "B":
            reasons.append("中等可信度来源")
        if rate < 50:
            reasons.append("消化率偏低")
        if signal_count == 0:
            reasons.append("缺少三要素支撑")
        if is_short:
            reasons.append("短文本噪声放大")
        return round(risk, 2), level, reasons

    def _inheritance_ready(self, unit):
        """判断知识单元是否适合写入长期继承队列。"""
        return (
            unit["digestion_rate"] >= self.inheritance_rules["min_rate"]
            and unit["credibility"] in self.inheritance_rules["trusted_credibilities"]
            and unit["contamination_risk"] <= self.inheritance_rules["max_risk"]
        )

    @staticmethod
    def _priority_rank(level):
        return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(level, 4)

    def _build_portfolio_diagnostics(self):
        source_counts = Counter(unit["source"] for unit in self.units)
        credibility_mix = Counter(unit["credibility"] for unit in self.units)
        category_mix = Counter(unit["category"] for unit in self.units)
        unique_sources = len(source_counts)
        total_units = len(self.units) or 1
        dominant_source, dominant_count = ("", 0)
        if source_counts:
            dominant_source, dominant_count = source_counts.most_common(1)[0]
        dominant_ratio = round(dominant_count / total_units, 2) if dominant_count else 0.0
        source_concentration = (
            "high" if dominant_ratio >= 0.65 and unique_sources >= 1
            else "medium" if dominant_ratio >= 0.45 and unique_sources >= 1
            else "low"
        )

        evidence_ready = [
            unit for unit in self.units
            if unit.get("evidence_matches", 0) > 0 or unit.get("semantic_profile", {}).get("numeric_markers", 0) > 0
        ]
        application_ready = [unit for unit in self.units if unit.get("application_matches", 0) > 0]
        thin_units = [
            unit["concept"]
            for unit in self.units
            if unit.get("semantic_signal_count", 0) < 3 or unit.get("digestion_level") == "低"
        ][:5]

        avg_freshness = (
            round(sum(unit.get("freshness_days", 0) for unit in self.units) / len(self.units), 1)
            if self.units else 0.0
        )
        expiring_soon = sum(1 for unit in self.units if unit.get("freshness_days", 0) <= 14)
        inheritance_ready_rate = round(len(self.inheritance_queue) / total_units * 100, 1)

        return {
            "source_diversity": {
                "unique_sources": unique_sources,
                "diversity_ratio": round(unique_sources / total_units, 2),
                "dominant_source": dominant_source,
                "dominant_ratio": dominant_ratio,
                "concentration_level": source_concentration,
            },
            "credibility_mix": dict(credibility_mix),
            "category_mix": dict(category_mix),
            "evidence_coverage": {
                "coverage_rate": round(len(evidence_ready) / total_units * 100, 1),
                "application_coverage_rate": round(len(application_ready) / total_units * 100, 1),
                "thin_units": thin_units,
            },
            "freshness_profile": {
                "average_freshness_days": avg_freshness,
                "expiring_soon_count": expiring_soon,
            },
            "inheritance_readiness": {
                "ready_rate": inheritance_ready_rate,
                "quarantine_rate": round(len(self.quarantine_queue) / total_units * 100, 1),
            },
        }

    def _build_refinement_queue(self):
        queue = []
        for unit in self.units:
            reason = []
            next_step = "整理成结构化摘要并进入下轮复习。"
            priority = "low"

            if unit.get("contamination_level") == "high":
                priority = "critical"
                reason.append("污染风险高")
                next_step = "先隔离来源并补做可信度复核，再决定是否继承。"
            elif unit.get("digestion_level") == "低":
                priority = "high"
                reason.append("消化率低")
                next_step = "补充核心论点、证据和应用场景后再二次炼化。"
            elif unit.get("contamination_level") == "medium":
                priority = "high"
                reason.append("存在中等污染风险")
                next_step = "补一层来源交叉验证，降低污染再继承。"

            if unit.get("evidence_matches", 0) == 0 and unit.get("semantic_profile", {}).get("numeric_markers", 0) == 0:
                reason.append("缺少证据支撑")
                if priority == "low":
                    priority = "medium"
                if "补充核心论点、证据和应用场景后再二次炼化。" not in next_step:
                    next_step = "补充数据、实验或案例证据，再重新评估消化率。"

            if unit.get("application_matches", 0) == 0:
                reason.append("缺少可执行场景")
                if priority == "low":
                    priority = "medium"

            if unit.get("is_short_text"):
                reason.append("短文本上下文不足")
                if priority == "low":
                    priority = "medium"

            if priority == "low" and unit.get("inheritance_ready"):
                continue

            queue.append(
                {
                    "concept": unit["concept"],
                    "source": unit["source"],
                    "priority": priority,
                    "retention_action": unit.get("retention_action"),
                    "reason": " / ".join(reason) if reason else "建议做一次轻量复盘后再继承。",
                    "next_step": next_step,
                }
            )

        queue.sort(key=lambda item: (self._priority_rank(item.get("priority")), item.get("concept", "")))
        return queue

    def _build_priority_actions(self, portfolio_diagnostics, refinement_queue):
        actions = []
        if self.quarantine_queue:
            top_risk = self.contamination_risk.get("drivers", [{}])[0]
            actions.append(
                {
                    "id": "review-quarantine",
                    "priority": "critical" if self.contamination_risk.get("level") == "high" else "high",
                    "owner": "liuku-xianzei",
                    "action": "优先复核隔离队列中的高风险知识单元。",
                    "reason": f"最高风险单元来自 {top_risk.get('source', 'unknown')}。",
                }
            )

        if refinement_queue:
            actions.append(
                {
                    "id": "run-refinement-queue",
                    "priority": refinement_queue[0].get("priority", "medium"),
                    "owner": "liuku-xianzei",
                    "action": "按 refinement_queue 顺序执行补证据、补场景和二次炼化。",
                    "reason": f"当前共有 {len(refinement_queue)} 个单元需要继续炼化。",
                }
            )

        if portfolio_diagnostics["source_diversity"]["concentration_level"] in {"high", "medium"}:
            actions.append(
                {
                    "id": "diversify-sources",
                    "priority": "medium",
                    "owner": "liuku-xianzei",
                    "action": "补充更多独立来源，降低单一来源主导风险。",
                    "reason": (
                        f"来源集中于 {portfolio_diagnostics['source_diversity']['dominant_source']} "
                        f"({portfolio_diagnostics['source_diversity']['dominant_ratio']:.0%})."
                    ),
                }
            )

        if self.inheritance_queue:
            actions.append(
                {
                    "id": "promote-inheritance",
                    "priority": "medium" if self.contamination_risk.get("level") != "high" else "low",
                    "owner": "liuku-xianzei",
                    "action": "把继承队列中的高质量知识转写为长期记忆或可复用规则。",
                    "reason": f"当前已有 {len(self.inheritance_queue)} 个单元满足继承门槛。",
                }
            )

        actions.sort(key=lambda item: (self._priority_rank(item.get("priority")), item.get("id", "")))
        return actions

    # ── 公共接口 ──────────────────────────────────────────────

    @record_metrics("liuku-xianzei")
    def digest(self):
        for item in self.items:
            unit = self._process(item)
            self.units.append(unit)
        return self._build_report()

    def _process(self, item):
        text = item.get("content", "")
        credibility = item.get("credibility", "B")
        source = item.get("source", "unknown")
        category = item.get("category", "默认")

        is_short = len(text) <= self.density_factor.get("short_text_limit", 50)

        # V5.3 梯度评分
        effective_digestion, core_matches, ev_matches, app_matches, semantic_profile = self._compute_digestion_rate(
            text, credibility, is_short
        )

        # 保鲜期
        freshness = self.freshness_rules.get(category, self.freshness_rules.get("默认", timedelta(days=180)))
        expire = datetime.now() + freshness

        # 消化等级
        level = self._digestion_level(effective_digestion)
        contamination_risk, contamination_level, contamination_reasons = self._contamination_score(
            text, credibility, effective_digestion, core_matches, ev_matches, app_matches, is_short, semantic_profile
        )

        # 知识单元
        return {
            "concept": text[:30] + "..." if len(text) > 30 else text,
            "source": source,
            "credibility": credibility,
            "digestion_rate": effective_digestion,
            "digestion_level": level,
            "category": category,
            "freshness_days": freshness.days,
            "expires": expire.strftime("%Y-%m-%d"),
            "key_claim_matches": core_matches,
            "evidence_matches": ev_matches,
            "application_matches": app_matches,
            "is_short_text": is_short,
            "density_multiplier": self._density_multiplier(len(text)),
            "semantic_bonus": semantic_profile["semantic_bonus"],
            "semantic_signal_count": semantic_profile["signal_count"],
            "semantic_profile": {
                "summary_anchor_count": semantic_profile["summary_anchor_count"],
                "numeric_markers": semantic_profile["numeric_markers"],
                "evidence_marker_count": semantic_profile["evidence_marker_count"],
                "application_marker_count": semantic_profile["application_marker_count"],
                "sentence_count": semantic_profile["sentence_count"],
                "has_structured_summary": semantic_profile["has_structured_summary"],
            },
            "contamination_risk": contamination_risk,
            "contamination_level": contamination_level,
            "contamination_reasons": contamination_reasons,
            "inheritance_ready": False,
            "retention_action": "quarantine",
        }

    def _build_report(self):
        rates = [u["digestion_rate"] for u in self.units]
        avg_rate = sum(rates) / len(rates) if rates else 0
        avg_risk = sum(u.get("contamination_risk", 0) for u in self.units) / len(self.units) if self.units else 0
        peak_risk = max((u.get("contamination_risk", 0) for u in self.units), default=0)
        high_count = sum(1 for u in self.units if u["digestion_level"] == "高")
        medium_count = sum(1 for u in self.units if u["digestion_level"] == "中")
        low_count = sum(1 for u in self.units if u["digestion_level"] == "低")

        for unit in self.units:
            ready = self._inheritance_ready(unit)
            unit["inheritance_ready"] = ready
            unit["retention_action"] = "inherit" if ready else "quarantine"

        self.inheritance_queue = [
            {
                "concept": unit["concept"],
                "source": unit["source"],
                "digestion_rate": unit["digestion_rate"],
                "contamination_risk": unit["contamination_risk"],
                "reason": "高消化率且低污染风险，适合写入长期记忆",
            }
            for unit in self.units
            if unit["inheritance_ready"]
        ]
        self.quarantine_queue = [
            {
                "concept": unit["concept"],
                "source": unit["source"],
                "digestion_rate": unit["digestion_rate"],
                "contamination_risk": unit["contamination_risk"],
                "reason": "污染风险偏高，建议先复核再继承",
            }
            for unit in self.units
            if not unit["inheritance_ready"]
        ]
        summary_risk = max(avg_risk, peak_risk * 0.9)
        self.contamination_risk = {
            "score": round(summary_risk, 2),
            "level": "high" if summary_risk >= 0.55 else "medium" if summary_risk >= 0.30 else "low",
            "avg_score": round(avg_risk, 2),
            "peak_score": round(peak_risk, 2),
            "quarantine_count": len(self.quarantine_queue),
            "inheritance_count": len(self.inheritance_queue),
            "drivers": sorted(
                (
                    {
                        "source": unit["source"],
                        "concept": unit["concept"],
                        "risk": unit["contamination_risk"],
                    }
                    for unit in self.units
                ),
                key=lambda item: item["risk"],
                reverse=True,
            )[:3],
        }

        # 反刍调度（所有非高消化单元 + 高消化单元的长期复习）
        review_schedule = []
        for u in self.units:
            plan = self._review_plan(u["digestion_level"], u["digestion_rate"], u["concept"])
            review_schedule.append(plan)
        self.review_schedule = review_schedule

        # 质量摘要
        quality_tags = []
        if low_count > 0:
            quality_tags.append("需二次炼化")
        if any(u.get("is_short_text") for u in self.units):
            quality_tags.append("含短文本")
        if avg_rate >= 85:
            quality_tags.append("整体优质")
        if self.contamination_risk["level"] != "low":
            quality_tags.append("需污染复核")

        portfolio_diagnostics = self._build_portfolio_diagnostics()
        refinement_queue = self._build_refinement_queue()
        priority_actions = self._build_priority_actions(portfolio_diagnostics, refinement_queue)

        return {
            "digester": "liuku-xianzei",
            "version": "v0.1.0",
            "input_count": len(self.items),
            "avg_digestion_rate": round(avg_rate, 1),
            "distribution": {"高": high_count, "中": medium_count, "低": low_count},
            "knowledge_units": self.units,
            "review_schedule": review_schedule,
            "inheritance_queue": self.inheritance_queue,
            "quarantine_queue": self.quarantine_queue,
            "contamination_risk": self.contamination_risk,
            "portfolio_diagnostics": portfolio_diagnostics,
            "refinement_queue": refinement_queue,
            "priority_actions": priority_actions,
            "recommendation": (
                "优先净化高污染单元后再继承"
                if self.contamination_risk["level"] == "high"
                else "对低消化单元进行二次炼化"
                if low_count > 0
                else "全部消化良好"
            ),
            "quality_tags": quality_tags,
            "quality_score": round(
                max(
                    0.0,
                    min(
                        100.0,
                        avg_rate - self.contamination_risk["score"] * 18.0 + len(self.inheritance_queue) * 2.5,
                    ),
                ),
                1,
            ),
            "human_intervention": 1 if self.contamination_risk["level"] == "high" else 0,
            "output_completeness": round(min(100.0, 70.0 + len(review_schedule) * 3.0 + len(self.units) * 2.0), 1),
            "consistency_score": round(max(0.0, 100.0 - self.contamination_risk["score"] * 50.0), 1),
        }


# ── CLI ─────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("用法: python knowledge_digest.py <info.json>")
        print('  info: [{"source":"博客","content":"文本","credibility":"A","category":"技术方案"}, ...]')
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        items = json.load(f)

    # 输入验证
    ok, errs = validate_json_list(items, {"content": str}, "liuku-xianzei")
    if not ok:
        print(f"输入验证失败: {errs}")
        sys.exit(2)
    if not items:
        print("错误: 知识列表不能为空")
        sys.exit(2)
    for i, item in enumerate(items):
        if not item.get("content"):
            print(f"错误: 条目[{i}] 缺少内容")
            sys.exit(2)
        cred = item.get("credibility", "B")
        if cred not in ("S", "A", "B", "C"):
            print(f"错误: 条目[{i}] 可信度必须是 S/A/B/C 之一")
            sys.exit(2)

    digester = KnowledgeDigest(items)
    result = digester.digest()

    out = Path("digest_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 50)
    print("🍃 六库仙贼 · 知识消化报告  V5.4")
    print("=" * 50)
    print(f"  输入条数: {result['input_count']}")
    print(f"  平均消化率: {result['avg_digestion_rate']}%")
    print(f"  分布: 高{result['distribution']['高']} 中{result['distribution']['中']} 低{result['distribution']['低']}")
    print(f"  污染风险: {result['contamination_risk']['level']} ({result['contamination_risk']['score']})")
    if result.get("quality_tags"):
        print(f"  质量标签: {' | '.join(result['quality_tags'])}")
    print("-" * 50)
    for u in result["knowledge_units"][:5]:
        emoji = "🟢" if u["digestion_level"] == "高" else "🟡" if u["digestion_level"] == "中" else "🔴"
        short_flag = " [短]" if u.get("is_short_text") else ""
        print(f"  {emoji} [{u['digestion_level']}] {u['concept']:<20}{short_flag} | 来源:{u['source']} | 保鲜:{u['freshness_days']}天")
    print("-" * 50)
    print(f"💡 {result['recommendation']}")
    if result.get("inheritance_queue"):
        print(f"📥 可继承单元: {len(result['inheritance_queue'])}")
    if result.get("quarantine_queue"):
        print(f"🛑 待复核单元: {len(result['quarantine_queue'])}")
    if result["review_schedule"]:
        print("📅 反刍调度:")
        for r in result["review_schedule"][:5]:
            print(f"    • {r['concept'][:20]}... -> {r['review_in']} ({r['reason']})")
    print("=" * 50)
    print(f"详细报告: {out}")


if __name__ == "__main__":
    main()
