#!/usr/bin/env python3
"""
器名: DNA校验器 (DNA Validator) V5.2
用途: 计算风格偏离度，检测漂移，校验DNA一致性
输入: JSON {"current_style":{}, "dna":{}, "history":[]}
输出: JSON {deviation_score, drift_level, dna_violations, recommendations}
V5.2升级:
- 禁止词/否定前缀/风格维度/漂移阈值从 under-one.yaml 配置加载
"""

import json
import sys
import hashlib
from pathlib import Path

# 运行时指标收集
SKILLS_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SKILLS_ROOT))
try:
    from metrics_collector import record_metrics
except ImportError:
    def record_metrics(*args, **kwargs):
        def decorator(f): return f
        return decorator

# 输入验证
try:
    from _skill_config import get_skill_config, validate_json_input
except ImportError:
    def get_skill_config(skill_name, key=None, default=None):
        return default

    def validate_json_input(data, required_fields, skill_name="skill"):
        if not isinstance(data, dict):
            return False, ["<root> must be an object"]
        missing = [f for f in required_fields if f not in data or data[f] is None]
        return len(missing) == 0, missing


class DNAValidator:
    def __init__(self, profile):
        self.profile = profile
        self.violations = []
        self.deviation = 0.0
        self.surgery_plan = []
        # V5.2: 从 under-one.yaml 加载配置
        self._load_config()

    def _load_config(self):
        """V5.2: 从配置加载禁止词和否定前缀"""
        cfg = get_skill_config("shuangquanshou", default={})
        # 禁止词类别
        forbidden_cfg = cfg.get("forbidden_categories", {})
        self.FORBIDDEN_SEMANTICS = {k: v for k, v in forbidden_cfg.items()}
        # 否定前缀
        self.NEGATION_PREFIXES = cfg.get("negation_prefixes", [
            "不", "不要", "禁止", "避免", "别", "不能", "不可以", "勿", "拒绝", "反对", "防止"
        ])
        # 风格维度
        self.STYLE_DIMENSIONS = cfg.get("style_dimensions", ["tone", "formality", "detail_level", "structure"])
        # 漂移阈值
        self.DRIFT_THRESHOLDS = cfg.get("drift_thresholds", {"green": 0.2, "yellow": 0.4, "red": 0.5})
        # 人格分裂检测
        self.SPLIT_ROUNDS = cfg.get("split_detection", {}).get("rounds", 3)
        self.SPLIT_UNIQUE = cfg.get("split_detection", {}).get("unique_styles", 3)
        self.EDITABLE_DOMAINS = cfg.get("editable_domains", ["memory", "persona", "emotion", "perception"])
        self.CONTAMINATION_WEIGHTS = cfg.get(
            "contamination_weights",
            {"deviation": 0.45, "critical": 0.35, "warning": 0.15, "surgery_complexity": 0.05},
        )

    @record_metrics("shuangquanshou")
    def validate(self):
        self.violations = []
        self.surgery_plan = []
        self._calc_deviation()
        self._check_dna_violations()
        self._detect_drift()
        self._build_surgery_plan()
        return self._build_report()

    def _calc_deviation(self):
        current = self.profile.get("current_style", {})
        dna = self.profile.get("dna_expectation", {})
        
        diffs = []
        for key in self.STYLE_DIMENSIONS:
            cur = current.get(key, 0)
            exp = dna.get(key, 0)
            if exp > 0:
                diff = abs(cur - exp) / exp
                diffs.append(diff)
        
        self.deviation = sum(diffs) / len(diffs) if diffs else 0

    def _check_dna_violations(self):
        request = self.profile.get("requested_change", {})
        dna_core = self.profile.get("dna_core", {})
        req_type = request.get("type", "")
        req_target = request.get("target", "")
        
        # 检查是否违背核心DNA - 关键词匹配
        for principle, rule in dna_core.items():
            violated = False
            # 检查请求类型是否直接匹配原则名
            if req_type == principle:
                violated = True
            # 检查请求内容是否被规则禁止
            if rule and req_type and self._is_forbidden(req_type, rule):
                violated = True
            if rule and req_target and self._is_forbidden(req_target, rule):
                violated = True
            if violated:
                self.violations.append({
                    "principle": principle,
                    "rule": rule,
                    "severity": "critical",
                    "action": "拒绝切换，保持核心DNA",
                })

    def _is_forbidden(self, text, rule):
        """V5.1: 语义级禁止检测，支持否定语义识别和同义词扩展
        V5.2: 从配置加载禁止词和否定前缀"""
        text_lower = text.lower()
        rule_lower = rule.lower()

        # 步骤1: 在规则文本(rule)中查找哪些语义类别是被禁止的
        forbidden_categories = set()
        for category, synonyms in self.FORBIDDEN_SEMANTICS.items():
            if any(syn in rule_lower for syn in synonyms):
                forbidden_categories.add(category)

        # 如果rule中没有明确禁止任何语义类别，回退到简单匹配
        if not forbidden_categories:
            simple_keywords = list(self.FORBIDDEN_SEMANTICS.keys())
            for kw in simple_keywords:
                if kw in text_lower and kw in rule_lower:
                    return True
            return False

        # 步骤2: 在请求文本(text)中检查是否有禁止类别的语义，且没有否定前缀
        for category in forbidden_categories:
            synonyms = self.FORBIDDEN_SEMANTICS.get(category, [category])
            for syn in synonyms:
                # 在text中查找该同义词的位置
                idx = text_lower.find(syn)
                while idx != -1:
                    # 提取该词前面的上下文（最多10个字符）
                    context_start = max(0, idx - 10)
                    context = text_lower[context_start:idx]
                    # 检查是否有否定前缀
                    has_negation = any(context.endswith(neg) for neg in self.NEGATION_PREFIXES)
                    # 检查整个句子是否以否定意图开头
                    sentence_start = text_lower[:idx].rfind("，")
                    if sentence_start == -1:
                        sentence_start = text_lower[:idx].rfind("。")
                    if sentence_start == -1:
                        sentence_start = 0
                    else:
                        sentence_start += 1
                    sentence_prefix = text_lower[sentence_start:idx].strip()
                    has_sentence_negation = any(sentence_prefix.startswith(neg) for neg in self.NEGATION_PREFIXES)

                    if not has_negation and not has_sentence_negation:
                        # 确认命中：关键词在text中出现，且没有否定前缀
                        return True

                    # 继续查找下一个出现位置
                    idx = text_lower.find(syn, idx + 1)

        return False

    def _detect_drift(self):
        history = self.profile.get("history", [])
        if len(history) >= self.SPLIT_ROUNDS:
            recent = history[-self.SPLIT_ROUNDS:]
            styles = [h.get("style", "") for h in recent]
            unique = len(set(styles))
            if unique >= self.SPLIT_UNIQUE:
                self.violations.append({
                    "principle": "人格分裂防护",
                    "rule": f"{self.SPLIT_ROUNDS}轮内风格切换超过{self.SPLIT_UNIQUE}次",
                    "severity": "warning",
                    "action": "标记风格摇摆异常，向用户确认",
                })

    def _requested_change_text(self):
        request = self.profile.get("requested_change", {})
        parts = [request.get("domain"), request.get("type"), request.get("operation"), request.get("target"), request.get("intent")]
        return " ".join(str(part) for part in parts if part).lower()

    def _infer_domain(self):
        text = self._requested_change_text()
        domain_map = {
            "memory": ["memory", "记忆", "上下文", "事实", "偏好"],
            "persona": ["persona", "人格", "人设", "角色", "风格", "语气"],
            "emotion": ["emotion", "情绪", "心境", "共情"],
            "perception": ["perception", "感知", "视角", "认知", "观察"],
        }
        for domain, keywords in domain_map.items():
            if any(keyword in text for keyword in keywords):
                return domain
        return "persona"

    def _domain_state(self, domain):
        if domain == "memory":
            return self.profile.get("memory_state") or self.profile.get("memory") or {}
        if domain == "persona":
            return self.profile.get("persona_state") or self.profile.get("current_style") or {}
        if domain == "emotion":
            return self.profile.get("emotion_state") or {}
        if domain == "perception":
            return self.profile.get("perception_state") or {}
        return {}

    def _summarize_state(self, state):
        if isinstance(state, dict):
            if not state:
                return "empty"
            items = [f"{k}={v}" for k, v in list(state.items())[:4]]
            return ", ".join(items)
        if isinstance(state, list):
            return f"{len(state)} item(s)"
        return str(state or "empty")

    def _operation_name(self, request, domain):
        if request.get("operation"):
            return str(request["operation"])
        if domain == "memory":
            return "rewrite"
        if domain == "emotion":
            return "tune"
        if domain == "perception":
            return "reframe"
        return "persona-shift"

    def _rewrite_preview(self, request, domain):
        patch = request.get("patch")
        if isinstance(patch, dict) and patch:
            return self._summarize_state(patch)
        if request.get("target"):
            return str(request.get("target"))
        if request.get("value"):
            return str(request.get("value"))
        if domain == "memory":
            return "写入新的记忆锚点"
        if domain == "emotion":
            return "调整情绪权重"
        if domain == "perception":
            return "切换观察滤镜"
        return "调整人格与风格参数"

    def _target_path(self, domain):
        return {
            "memory": "memory_state",
            "persona": "current_style",
            "emotion": "emotion_state",
            "perception": "perception_state",
        }.get(domain, "current_style")

    def _infer_patch(self, request, domain):
        patch = request.get("patch")
        if isinstance(patch, dict) and patch:
            return patch

        explicit_key = request.get("key") or request.get("field") or request.get("slot")
        if explicit_key is not None and "value" in request:
            return {str(explicit_key): request.get("value")}

        target = request.get("target")
        if not target:
            return {}

        if domain == "memory":
            return {"memory_anchor": str(target)}
        if domain == "emotion":
            return {"emotion_target": str(target)}
        if domain == "perception":
            return {"perception_target": str(target)}
        return {"persona_target": str(target)}

    def _preview_state(self, state, patch):
        if not isinstance(state, dict):
            return patch if isinstance(patch, dict) else {}
        preview = dict(state)
        for key, value in patch.items():
            if value is None:
                preview.pop(key, None)
            else:
                preview[key] = value
        return preview

    def _patch_operations(self, state, patch):
        if not isinstance(patch, dict) or not patch:
            return []
        base_state = state if isinstance(state, dict) else {}
        ops = []
        for key, value in patch.items():
            existed = key in base_state
            if value is None and existed:
                op = "remove"
            elif existed:
                op = "replace"
            else:
                op = "add"
            ops.append(
                {
                    "op": op,
                    "path": key,
                    "before": base_state.get(key),
                    "after": value,
                }
            )
        return ops

    def _build_patch_preview(self, domain, request):
        state = self._domain_state(domain)
        patch = self._infer_patch(request, domain)
        preview_state = self._preview_state(state, patch)
        return {
            "target_path": self._target_path(domain),
            "operations": self._patch_operations(state, patch),
            "preview_state": preview_state,
            "reversible": True,
        }

    def _build_rollback_token(self, domain, patch_preview):
        payload = json.dumps(
            {
                "domain": domain,
                "target_path": patch_preview.get("target_path"),
                "operations": patch_preview.get("operations", []),
                "preview_state": patch_preview.get("preview_state"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]

    def _rewrite_patch_bundle(self):
        items = []
        for item in self.surgery_plan:
            patch_preview = item.get("patch_preview") or {}
            if not patch_preview.get("operations") and not patch_preview.get("preview_state"):
                continue
            items.append(
                {
                    "domain": item.get("domain"),
                    "target_path": item.get("target_path"),
                    "status": item.get("status"),
                    "operations": patch_preview.get("operations", []),
                    "preview_state": patch_preview.get("preview_state"),
                    "rollback_token": item.get("rollback_token"),
                }
            )
        return {
            "mode": self._surgery_mode(),
            "apply_ready": any(item.get("status") == "planned" for item in self.surgery_plan),
            "items": items,
        }

    def _build_surgery_plan(self):
        request = self.profile.get("requested_change", {}) or {}
        critical = any(v.get("severity") == "critical" for v in self.violations)
        warning = any(v.get("severity") == "warning" for v in self.violations)

        if not request:
            if self.deviation > 0 or self.violations:
                self.surgery_plan.append(
                    {
                        "domain": "persona",
                        "operation": "stabilize",
                        "status": "observe",
                        "before": self._summarize_state(self.profile.get("current_style", {})),
                        "after": self._summarize_state(self.profile.get("dna_expectation", {})),
                        "risk": "medium" if warning or self.deviation >= self.DRIFT_THRESHOLDS["yellow"] else "low",
                        "reason": "检测到漂移，建议先做校准而不是直接改写",
                    }
                )
            return

        domain = self._infer_domain()
        status = "planned"
        if critical:
            status = "blocked"
        elif warning or self.deviation >= self.DRIFT_THRESHOLDS["yellow"]:
            status = "review"

        patch_preview = self._build_patch_preview(domain, request)
        rollback_token = self._build_rollback_token(domain, patch_preview)

        self.surgery_plan.append(
            {
                "domain": domain,
                "operation": self._operation_name(request, domain),
                "status": status,
                "before": self._summarize_state(self._domain_state(domain)),
                "after": self._rewrite_preview(request, domain),
                "risk": "high" if critical else "medium" if warning or self.deviation >= self.DRIFT_THRESHOLDS["yellow"] else "low",
                "reason": "触发核心DNA保护" if critical else "存在漂移或摇摆，建议人工复核" if status == "review" else "允许执行局部人格/记忆手术",
                "target_path": patch_preview["target_path"],
                "patch_preview": patch_preview,
                "rollback_token": rollback_token,
                "requires_confirmation": status != "planned",
            }
        )

    def _contamination_index(self):
        weights = self.CONTAMINATION_WEIGHTS
        critical_count = sum(1 for item in self.violations if item.get("severity") == "critical")
        warning_count = sum(1 for item in self.violations if item.get("severity") == "warning")
        request = self.profile.get("requested_change", {}) or {}
        patch = request.get("patch")
        surgery_complexity = 0.0
        if isinstance(patch, dict):
            surgery_complexity = min(1.0, len(patch) / 5)
        elif request:
            surgery_complexity = 0.4

        score = (
            self.deviation * weights.get("deviation", 0.45)
            + critical_count * weights.get("critical", 0.35)
            + warning_count * weights.get("warning", 0.15)
            + surgery_complexity * weights.get("surgery_complexity", 0.05)
        )
        return round(min(1.0, score), 3)

    def _surgery_mode(self):
        if any(item.get("status") == "blocked" for item in self.surgery_plan):
            return "seal"
        if any(item.get("status") == "review" for item in self.surgery_plan):
            return "review"
        if any(item.get("status") == "planned" for item in self.surgery_plan):
            return "edit"
        return "observe"

    @staticmethod
    def _priority_rank(level):
        return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(level, 4)

    def _build_operation_checklist(self):
        mode = self._surgery_mode()
        target_path = self.surgery_plan[0].get("target_path") if self.surgery_plan else None
        return [
            {
                "id": "lock-immutable-core",
                "stage": "preflight",
                "required": True,
                "owner": "shuangquanshou",
                "action": "锁定 immutable_core，确认核心 DNA 不在本次改写作用域内。",
            },
            {
                "id": "preview-patch-scope",
                "stage": "preflight",
                "required": bool(self.surgery_plan),
                "owner": "shuangquanshou",
                "action": f"检查 patch_preview 是否只覆盖 {target_path or '目标域'}。",
            },
            {
                "id": "confirm-approval-gate",
                "stage": "pre_apply",
                "required": mode in {"review", "seal"},
                "owner": "user" if mode in {"review", "seal"} else "shuangquanshou",
                "action": "确认审批门是否通过；未通过则保持 seal/review 模式。",
            },
            {
                "id": "apply-rewrite",
                "stage": "apply",
                "required": mode == "edit",
                "owner": "shuangquanshou",
                "action": "按 rewrite_patch 执行局部记忆/人格手术，不越过 editable_domains。",
            },
            {
                "id": "verify-integrity",
                "stage": "post_apply",
                "required": True,
                "owner": "shuangquanshou",
                "action": "重新计算 contamination_index、identity_integrity，并验证回滚令牌可用。",
            },
        ]

    def _build_safety_contract(self, contamination_index):
        mode = self._surgery_mode()
        blocked_reasons = [item.get("reason") for item in self.surgery_plan if item.get("status") == "blocked"]
        review_reasons = [item.get("reason") for item in self.surgery_plan if item.get("status") == "review"]
        risk_level = (
            "critical" if mode == "seal"
            else "high" if contamination_index >= 0.6 or mode == "review"
            else "medium" if contamination_index >= 0.35
            else "low"
        )
        return {
            "mode": mode,
            "risk_level": risk_level,
            "immutable_core_locked": True,
            "editable_domains": list(self.EDITABLE_DOMAINS),
            "target_domains": sorted({item.get("domain") for item in self.surgery_plan if item.get("domain")}),
            "rollback_ready": all(bool(item.get("rollback_token")) for item in self.surgery_plan if item.get("patch_preview")),
            "requires_confirmation": any(item.get("requires_confirmation") for item in self.surgery_plan),
            "blocked_reasons": blocked_reasons or review_reasons,
            "allowed_operations": [item.get("operation") for item in self.surgery_plan if item.get("status") == "planned"],
            "forbidden_operations": [item.get("operation") for item in self.surgery_plan if item.get("status") == "blocked"],
        }

    def _build_approval_contract(self, contamination_index, can_switch):
        mode = self._surgery_mode()
        rollback_tokens = [item.get("rollback_token") for item in self.surgery_plan if item.get("rollback_token")]
        requires_user_confirmation = mode in {"review", "seal"}
        safe_to_apply = mode == "edit" and can_switch and contamination_index < 0.75
        approval_status = "blocked" if mode == "seal" else "pending" if requires_user_confirmation else "approved"
        return {
            "approval_status": approval_status,
            "manual_review_required": requires_user_confirmation,
            "requires_user_confirmation": requires_user_confirmation,
            "safe_to_apply": safe_to_apply,
            "blocking_violations": len(self.violations),
            "rollback_tokens": rollback_tokens,
            "reason": (
                "存在核心 DNA 违背，禁止执行记忆/人格手术。"
                if mode == "seal"
                else "存在漂移或摇摆，需人工复核后执行。"
                if requires_user_confirmation
                else "手术范围受控，可按 patch_preview 执行。"
            ),
        }

    def _build_priority_actions(self, safety_contract, approval_contract):
        actions = []
        for item in self.surgery_plan:
            status = item.get("status")
            priority = "critical" if status == "blocked" else "high" if status == "review" else "medium"
            action = (
                "停止执行并保持当前人格/记忆状态。"
                if status == "blocked"
                else "等待人工确认后再执行局部手术。"
                if status == "review"
                else f"将 patch_preview 应用到 {item.get('target_path')}。"
            )
            actions.append(
                {
                    "id": f"{item.get('domain', 'persona')}-{item.get('operation', 'operate')}",
                    "priority": priority,
                    "owner": "user" if status in {"blocked", "review"} else "shuangquanshou",
                    "blocking": status in {"blocked", "review"},
                    "action": action,
                    "reason": item.get("reason"),
                }
            )

        if approval_contract.get("safe_to_apply"):
            actions.append(
                {
                    "id": "verify-post-op-integrity",
                    "priority": "medium",
                    "owner": "shuangquanshou",
                    "blocking": False,
                    "action": "执行后再次校验 identity_integrity 和 rollback_token。",
                    "reason": "保证记忆/人格改写没有引入污染。",
                }
            )

        actions.sort(key=lambda item: (self._priority_rank(item.get("priority")), item.get("id", "")))
        return actions

    def _build_report(self):
        th = self.DRIFT_THRESHOLDS
        level = "green" if self.deviation < th["green"] else "yellow" if self.deviation < th["yellow"] else "red"
        contamination_index = self._contamination_index()
        can_switch = len(self.violations) == 0 and self.deviation < th["red"] and contamination_index < 0.75
        safety_contract = self._build_safety_contract(contamination_index)
        approval_contract = self._build_approval_contract(contamination_index, can_switch)
        operation_checklist = self._build_operation_checklist()
        priority_actions = self._build_priority_actions(safety_contract, approval_contract)

        return {
            "validator": "shuangquanshou",
            "version": "v0.1.0",
            "deviation_score": round(self.deviation, 3),
            "drift_level": level,
            "dna_violations": self.violations,
            "editable_domains": list(self.EDITABLE_DOMAINS),
            "immutable_core": list(self.profile.get("dna_core", {}).keys()),
            "surgery_mode": self._surgery_mode(),
            "surgery_plan": self.surgery_plan,
            "rewrite_patch": self._rewrite_patch_bundle(),
            "contamination_index": contamination_index,
            "identity_integrity": round(max(0.0, 1.0 - contamination_index), 3),
            "safety_contract": safety_contract,
            "approval_contract": approval_contract,
            "operation_checklist": operation_checklist,
            "priority_actions": priority_actions,
            "can_switch": can_switch,
            "can_operate": can_switch,
            "quality_score": round(
                max(
                    0.0,
                    min(
                        100.0,
                        (1.0 - contamination_index) * 100.0 - len(self.violations) * 4.0 + (3.0 if can_switch else 0.0),
                    ),
                ),
                1,
            ),
            "human_intervention": 1 if self._surgery_mode() in {"review", "seal"} else 0,
            "output_completeness": 100.0 if self.surgery_plan is not None else 80.0,
            "consistency_score": round(max(0.0, (1.0 - contamination_index) * 100.0), 1),
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self):
        recs = []
        th = self.DRIFT_THRESHOLDS
        if self.deviation > th["yellow"]:
            recs.append("漂移严重，立即启动人设校准")
        elif self.deviation > th["green"]:
            recs.append("轻微漂移，关注即可")
        if self.violations:
            recs.append(f"检测到{len(self.violations)}项DNA违背，拒绝风格切换")
        if self.surgery_plan:
            domains = ",".join(item["domain"] for item in self.surgery_plan)
            recs.append(f"当前建议操作域：{domains}（模式: {self._surgery_mode()}）")
        if not recs:
            recs.append("DNA一致，允许风格调整")
        return recs


def main():
    if len(sys.argv) < 2:
        print("用法: python dna_validator.py <profile.json>")
        print('  profile: {"current_style":{"tone":3},"dna_expectation":{"tone":3},"dna_core":{"诚信":"不编造"}, "history":[...]}')
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        profile = json.load(f)

    # 输入验证
    ok, missing = validate_json_input(profile, ["current_style", "dna_expectation"], "shuangquanshou")
    if not ok:
        print(f"输入验证失败，缺少字段: {missing}")
        sys.exit(2)
    if not isinstance(profile.get("current_style"), dict):
        print("错误: current_style 必须是对象")
        sys.exit(2)
    if not isinstance(profile.get("dna_expectation"), dict):
        print("错误: dna_expectation 必须是对象")
        sys.exit(2)

    validator = DNAValidator(profile)
    result = validator.validate()

    out = Path("dna_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 50)
    print("✋ 双全手 · DNA校验报告")
    print("=" * 50)
    print(f"  偏离度: {result['deviation_score']:.3f} ({result['drift_level']})")
    print(f"  允许切换: {'✅ 是' if result['can_switch'] else '❌ 否'}")
    print(f"  手术模式: {result['surgery_mode']}")
    print(f"  污染指数: {result['contamination_index']}")
    print("-" * 50)
    if result["dna_violations"]:
        print("🚨 DNA违背:")
        for v in result["dna_violations"]:
            emoji = "🔴" if v["severity"] == "critical" else "🟡"
            print(f"  {emoji} [{v['severity']}] {v['principle']}: {v['action']}")
    else:
        print("✅ 无DNA违背")
    if result["surgery_plan"]:
        print("🩺 手术方案:")
        for item in result["surgery_plan"]:
            print(f"  • {item['domain']} / {item['operation']} / {item['status']} -> {item['after']}")
    print("-" * 50)
    print("💡 建议:")
    for r in result["recommendations"]:
        print(f"  • {r}")
    print("=" * 50)


    print(f"详细报告: {out}")


if __name__ == "__main__":
    main()
