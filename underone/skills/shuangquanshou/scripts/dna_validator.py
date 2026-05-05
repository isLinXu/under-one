#!/usr/bin/env python3
"""
器名: DNA校验器 (DNA Validator)
用途: 计算风格偏离度，检测漂移，校验DNA一致性
输入: JSON {"current_style":{}, "dna":{}, "history":[]}
输出: JSON {deviation_score, drift_level, dna_violations, recommendations}
"""

import json
import sys
from pathlib import Path


class DNAValidator:
    def __init__(self, profile):
        self.profile = profile
        self.violations = []
        self.deviation = 0.0

    def validate(self):
        self._calc_deviation()
        self._check_dna_violations()
        self._detect_drift()
        return self._build_report()

    def _calc_deviation(self):
        current = self.profile.get("current_style", {})
        dna = self.profile.get("dna_expectation", {})
        
        diffs = []
        for key in ["tone", "formality", "detail_level", "structure"]:
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
        """检查text是否被rule禁止"""
        # 简单关键词匹配
        forbidden_keywords = ["医疗", "法律", "投资", "嘲讽", "贬低", "侮辱", "欺骗", "编造"]
        rule_lower = rule.lower()
        text_lower = text.lower()
        # 检查text中是否包含禁止词
        for kw in forbidden_keywords:
            if kw in text_lower and kw in rule_lower:
                return True
        return False

    def _detect_drift(self):
        history = self.profile.get("history", [])
        if len(history) >= 3:
            recent = history[-3:]
            styles = [h.get("style", "") for h in recent]
            unique = len(set(styles))
            if unique >= 3:
                self.violations.append({
                    "principle": "人格分裂防护",
                    "rule": "3轮内风格切换超过3次",
                    "severity": "warning",
                    "action": "标记风格摇摆异常，向用户确认",
                })

    def _build_report(self):
        level = "green" if self.deviation < 0.2 else "yellow" if self.deviation < 0.4 else "red"
        
        return {
            "validator": "shuangquanshou",
            "version": "5.0",
            "deviation_score": round(self.deviation, 3),
            "drift_level": level,
            "dna_violations": self.violations,
            "can_switch": len(self.violations) == 0 and self.deviation < 0.5,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self):
        recs = []
        if self.deviation > 0.4:
            recs.append("漂移严重，立即启动人设校准")
        elif self.deviation > 0.2:
            recs.append("轻微漂移，关注即可")
        if self.violations:
            recs.append(f"检测到{len(self.violations)}项DNA违背，拒绝风格切换")
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
    print("-" * 50)
    if result["dna_violations"]:
        print("🚨 DNA违背:")
        for v in result["dna_violations"]:
            emoji = "🔴" if v["severity"] == "critical" else "🟡"
            print(f"  {emoji} [{v['severity']}] {v['principle']}: {v['action']}")
    else:
        print("✅ 无DNA违背")
    print("-" * 50)
    print("💡 建议:")
    for r in result["recommendations"]:
        print(f"  • {r}")
    print("=" * 50)


    print(f"详细报告: {out}")


if __name__ == "__main__":
    main()