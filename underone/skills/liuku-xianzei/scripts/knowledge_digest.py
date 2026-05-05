#!/usr/bin/env python3
"""
器名: 知识消化器 (Knowledge Digest)
用途: 评估信息消化率，生成知识单元，计算保鲜期
输入: JSON [{"source":"来源","content":"文本","credibility":"S"}]
输出: JSON {digest_rate,knowledge_units,freshness_schedule}
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta


class KnowledgeDigest:
    CREDIBILITY_WEIGHT = {"S": 1.5, "A": 1.2, "B": 1.0, "C": 0.6}
    FRESHNESS_RULES = {
        "技术方案": timedelta(days=90),
        "行业数据": timedelta(days=180),
        "基础理论": timedelta(days=1095),
        "法律法规": timedelta(days=7),
        "社区经验": timedelta(days=90),
        "默认": timedelta(days=180),
    }

    def __init__(self, info_items):
        self.items = info_items
        self.units = []

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

        # 评估消化率 - V5.2 短文本智能适配
        CORE_CLAIM_KEYWORDS = ["是", "为", "指", "提出", "表明", "证明", "发现", "结论", "显示", "研究", "通过", "实现", "解决", "提升", "降低", "改进", "验证", "基于", "核心", "本质"]
        EVIDENCE_KEYWORDS = ["数据", "统计", "研究表明", "因为", "实验", "测试", "结果", "证据", "报告", "分析", "量化", "对比"]
        APPLICATION_KEYWORDS = ["用于", "应用", "场景", "案例", "实践", "部署", "实施", "落地", "适用于", "在...中"]
        SHORT_TEXT_KEYWORDS = ["推荐", "版本", "使用", "支持", "需要", "建议", "依赖", "兼容", "要求", "配置"]
        
        # 短文本适配：长度<50时降低核心论点检测阈值，增加短文本专用关键词
        is_short = len(text) <= 50
        if is_short:
            has_core_claim = any(k in text for k in SHORT_TEXT_KEYWORDS) or any(k in text for k in CORE_CLAIM_KEYWORDS)
        else:
            has_core_claim = any(k in text for k in CORE_CLAIM_KEYWORDS)
        has_evidence = any(k in text for k in EVIDENCE_KEYWORDS) or is_short  # 短文本默认给予证据分（存在即合理）
        has_application = any(k in text for k in APPLICATION_KEYWORDS) or is_short

        digestion_score = 0
        if has_core_claim: digestion_score += 40
        if has_evidence: digestion_score += 30
        if has_application: digestion_score += 30

        # 加权可信度
        weight = self.CREDIBILITY_WEIGHT.get(credibility, 1.0)
        effective_digestion = min(100, digestion_score * weight)

        # 保鲜期
        freshness = self.FRESHNESS_RULES.get(category, self.FRESHNESS_RULES["默认"])
        expire = datetime.now() + freshness

        # 知识单元
        return {
            "concept": text[:30] + "..." if len(text) > 30 else text,
            "source": source,
            "credibility": credibility,
            "digestion_rate": round(effective_digestion, 1),
            "digestion_level": "高" if effective_digestion > 80 else "中" if effective_digestion > 50 else "低",
            "category": category,
            "freshness_days": freshness.days,
            "expires": expire.strftime("%Y-%m-%d"),
            "key_claim": has_core_claim,
            "has_evidence": has_evidence,
            "has_application": has_application,
        }

    def _build_report(self):
        rates = [u["digestion_rate"] for u in self.units]
        avg_rate = sum(rates) / len(rates) if rates else 0
        high_count = sum(1 for u in self.units if u["digestion_level"] == "高")
        medium_count = sum(1 for u in self.units if u["digestion_level"] == "中")
        low_count = sum(1 for u in self.units if u["digestion_level"] == "低")

        # 反刍调度
        review_schedule = []
        for u in self.units:
            if u["digestion_level"] == "低":
                review_schedule.append({"concept": u["concept"], "review_in": "4小时", "reason": "低消化率"})
            elif u["digestion_level"] == "中":
                review_schedule.append({"concept": u["concept"], "review_in": "1天", "reason": "待补充"})

        return {
            "digester": "liuku-xianzei",
            "version": "5.0",
            "input_count": len(self.items),
            "avg_digestion_rate": round(avg_rate, 1),
            "distribution": {"高": high_count, "中": medium_count, "低": low_count},
            "knowledge_units": self.units,
            "review_schedule": review_schedule,
            "recommendation": "对低消化单元进行二次炼化" if low_count > 0 else "全部消化良好",
        }


def main():
    if len(sys.argv) < 2:
        print("用法: python knowledge_digest.py <info.json>")
        print('  info: [{"source":"博客","content":"文本","credibility":"A","category":"技术方案"}, ...]')
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        items = json.load(f)

    digester = KnowledgeDigest(items)
    result = digester.digest()

    out = Path("digest_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 50)
    print("🍃 六库仙贼 · 知识消化报告")
    print("=" * 50)
    print(f"  输入条数: {result['input_count']}")
    print(f"  平均消化率: {result['avg_digestion_rate']}%")
    print(f"  分布: 高{result['distribution']['高']} 中{result['distribution']['中']} 低{result['distribution']['低']}")
    print("-" * 50)
    for u in result["knowledge_units"][:5]:
        emoji = "🟢" if u["digestion_level"] == "高" else "🟡" if u["digestion_level"] == "中" else "🔴"
        print(f"  {emoji} [{u['digestion_level']}] {u['concept']:<20} | 来源:{u['source']} | 保鲜:{u['freshness_days']}天")
    print("-" * 50)
    print(f"💡 {result['recommendation']}")
    if result["review_schedule"]:
        print("📅 反刍调度:")
        for r in result["review_schedule"][:3]:
            print(f"    • {r['concept'][:20]}... -> {r['review_in']} ({r['reason']})")
    print("=" * 50)


    print(f"详细报告: {out}")


if __name__ == "__main__":
    main()