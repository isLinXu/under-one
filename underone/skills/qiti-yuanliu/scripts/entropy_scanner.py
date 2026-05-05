#!/usr/bin/env python3
"""
器名: 上下文熵扫描器 (Entropy Scanner)
用途: 扫描对话上下文，计算健康指标，输出诊断报告
输入: JSON格式的对话上下文 [{role, content, round}]
输出: JSON诊断报告 {entropy, consistency, health_score, alerts}
"""

import json
import sys
import re
from pathlib import Path
from collections import Counter


class QiTiScanner:
    """炁体源流 - 上下文稳态扫描器"""

    CONTRADICTION_KEYWORDS = ["不对", "错了", "矛盾", "之前说", "改回", "重新", "不是这个"]
    HEALTH_THRESHOLDS = {
        "excellent": (90, float("inf")),
        "good": (75, 90),
        "warning": (60, 75),
        "danger": (0, 60),
    }

    def __init__(self, context_data):
        self.context = context_data
        self.alerts = []
        self.metrics = {}

    def scan(self):
        """执行全量扫描"""
        self._calc_entropy()
        self._check_consistency()
        self._check_density()
        self._check_alignment()
        self._check_completeness()
        self._detect_contradictions()
        self._calc_health_score()
        return self._generate_report()

    def _calc_entropy(self):
        """计算上下文熵"""
        conflict_count = len(self._find_contradictions())
        gap_count = self._count_info_gaps()
        redundancy_count = self._count_redundancy()
        entropy = conflict_count * 2 + gap_count * 1.5 + redundancy_count * 0.5
        self.metrics["entropy"] = round(entropy, 2)
        self.metrics["entropy_level"] = "green" if entropy < 3 else "yellow" if entropy < 7 else "red"

    def _find_contradictions(self):
        """检测矛盾关键词"""
        contradictions = []
        for msg in self.context:
            for kw in self.CONTRADICTION_KEYWORDS:
                if kw in msg.get("content", ""):
                    contradictions.append({
                        "round": msg.get("round", 0),
                        "keyword": kw,
                        "preview": msg.get("content", "")[:50] + "..."
                    })
        return contradictions

    def _count_info_gaps(self):
        """统计信息缺口（简化版：检测未闭合的问题）"""
        gaps = 0
        for msg in self.context:
            content = msg.get("content", "")
            if "?" in content or "？" in content or "如何" in content or "什么" in content:
                # 检查后续是否有回答
                idx = self.context.index(msg)
                if idx == len(self.context) - 1:
                    gaps += 1
        return gaps

    def _count_redundancy(self):
        """统计冗余重复"""
        contents = [msg.get("content", "") for msg in self.context]
        duplicates = 0
        for i, c1 in enumerate(contents):
            for c2 in contents[i+1:]:
                if len(c1) > 20 and len(c2) > 20:
                    sim = self._similarity(c1[:100], c2[:100])
                    if sim > 0.7:
                        duplicates += 1
        return duplicates

    def _similarity(self, a, b):
        """简单Jaccard相似度"""
        set_a = set(a.split())
        set_b = set(b.split())
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    def _check_consistency(self):
        """检查上下文一致性"""
        # 简化：基于矛盾数量估算
        contradictions = len(self._find_contradictions())
        consistency = max(0, 100 - contradictions * 15)
        self.metrics["consistency"] = consistency

    def _check_density(self):
        """检查信息密度"""
        total_len = sum(len(msg.get("content", "")) for msg in self.context)
        avg_len = total_len / max(len(self.context), 1)
        density = "high" if avg_len > 200 else "medium" if avg_len > 50 else "low"
        self.metrics["density"] = density

    def _check_alignment(self):
        """检查目标对齐度"""
        # 如果第一轮有明确目标，后续轮次偏离则扣分
        if not self.context:
            self.metrics["alignment"] = 100
            return
        first_goal = self.context[0].get("content", "")[:100]
        drift_score = 100
        for msg in self.context[1:]:
            content = msg.get("content", "")
            if len(content) > 50:
                sim = self._similarity(first_goal, content[:100])
                if sim < 0.1:
                    drift_score -= 5
        self.metrics["alignment"] = max(0, drift_score)

    def _check_completeness(self):
        """检查推理链完整度"""
        # 检测逻辑跳跃：是否缺少中间步骤
        logic_markers = ["因为", "所以", "首先", "然后", "最后", "结论"]
        marker_count = sum(
            1 for msg in self.context
            for m in logic_markers if m in msg.get("content", "")
        )
        completeness = min(100, 50 + marker_count * 5)
        self.metrics["completeness"] = completeness

    def _detect_contradictions(self):
        """生成矛盾警报"""
        for c in self._find_contradictions():
            self.alerts.append({
                "level": "warning",
                "type": "contradiction",
                "round": c["round"],
                "message": f"检测到矛盾关键词 '{c['keyword']}'"
            })
        if self.metrics.get("entropy", 0) > 7:
            self.alerts.append({
                "level": "danger",
                "type": "high_entropy",
                "message": f"上下文熵过高 ({self.metrics['entropy']})，建议立即修复"
            })

    def _calc_health_score(self):
        """计算综合健康分"""
        weights = {
            "consistency": 0.25,
            "alignment": 0.25,
            "completeness": 0.20,
            "entropy_bonus": 0.30,
        }
        entropy_bonus = 100 if self.metrics.get("entropy", 0) < 3 else 60 if self.metrics.get("entropy", 0) < 7 else 20
        score = (
            self.metrics.get("consistency", 100) * weights["consistency"] +
            self.metrics.get("alignment", 100) * weights["alignment"] +
            self.metrics.get("completeness", 100) * weights["completeness"] +
            entropy_bonus * weights["entropy_bonus"]
        )
        self.metrics["health_score"] = round(score, 1)
        self.metrics["health_level"] = self._get_level(score)

    def _get_level(self, score):
        for level, (low, high) in self.HEALTH_THRESHOLDS.items():
            if low <= score < high:
                return level
        return "unknown"

    def _generate_report(self):
        return {
            "scanner": "qiti-yuanliu",
            "version": "5.0",
            "context_length": len(self.context),
            "metrics": self.metrics,
            "alerts": self.alerts,
            "recommendations": self._generate_recommendations(),
            "dna_snapshot": self._generate_dna_snapshot(),
        }

    def _generate_recommendations(self):
        recs = []
        if self.metrics.get("entropy", 0) > 7:
            recs.append("建议立即执行稳态修复（上下文蒸馏+锚点重建）")
        elif self.metrics.get("entropy", 0) > 3:
            recs.append("建议关注，执行轻量炁循环")
        if self.metrics.get("consistency", 100) < 90:
            recs.append("建议检查矛盾点，调用大罗洞观跨段追踪")
        if self.metrics.get("alignment", 100) < 95:
            recs.append("建议重新对齐用户原始目标")
        if not recs:
            recs.append("上下文状态健康，继续正常运行")
        return recs

    def _generate_dna_snapshot(self):
        """生成DNA快照哈希"""
        key_decisions = [msg.get("content", "")[:30] for msg in self.context[-3:]]
        snapshot_raw = "|".join(key_decisions)
        # 简化哈希
        dna_hash = hex(hash(snapshot_raw) & 0xFFFFFF)[2:].zfill(6)
        return {
            "hash": dna_hash,
            "based_on": "last_3_rounds",
            "timestamp": "auto",
        }


def main():
    if len(sys.argv) < 2:
        print("用法: python entropy_scanner.py <context.json>")
        print("  context.json: [{\"role\":\"user\",\"content\":\"...\",\"round\":1}, ...]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"错误: 文件不存在 {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        context_data = json.load(f)

    scanner = QiTiScanner(context_data)
    report = scanner.scan()

    output_path = input_path.with_suffix(".health_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 控制台输出摘要


    print("=" * 50)
    print("📊 炁体源流 · 上下文健康报告")


    print("=" * 50)
    print(f"  对话轮次: {report['context_length']}")
    print(f"  上下文熵: {report['metrics']['entropy']} ({report['metrics']['entropy_level']})")
    print(f"  一致性: {report['metrics']['consistency']}%")
    print(f"  对齐度: {report['metrics']['alignment']}%")
    print(f"  推理完整度: {report['metrics']['completeness']}%")
    print(f"  信息密度: {report['metrics']['density']}")
    print(f"  健康总分: {report['metrics']['health_score']} ({report['metrics']['health_level']})")
    print(f"  DNA快照: {report['dna_snapshot']['hash']}")
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