#!/usr/bin/env python3
"""
器名: 关联检测器 (Link Detector)
用途: 从多段文本中检测关联关系，输出关联图谱
输入: JSON [{"source": "段落名", "content": "文本"}]
输出: JSON {links, entity_map, knowledge_graph, mermaid_code}
"""

import json
import sys
import re
from pathlib import Path
from collections import defaultdict


class LinkDetector:
    RELATION_TYPES = ["因果", "对比", "包含", "依赖", "指代"]
    CONFIDENCE_WEIGHTS = {
        "semantic": 0.30,
        "cooccurrence": 0.25,
        "temporal": 0.20,
        "source_consistency": 0.15,
        "causal": 0.10,
    }

    def __init__(self, segments):
        self.segments = segments
        self.links = []
        self.entities = defaultdict(list)

    def detect(self):
        self._extract_entities()
        self._semantic_links()
        self._cooccurrence_links()
        self._temporal_links()
        self._causal_links()
        self._prune_weak_links()
        return self._build_output()

    def _extract_entities(self):
        """提取实体（简化：名词短语）"""
        for seg in self.segments:
            text = seg.get("content", "")
            # 简单提取引号内内容和大写字母开头词
            entities = re.findall(r'[\"「]([^\"」]+)[\"」]', text)
            entities += re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
            # 中文实体：常见技术/业务名词
            cn_entities = re.findall(r'(?:竞品|文档|数据|用户|性能|加载|延迟|引擎|渲染|AI|技术|方案|系统|服务|报告|分析|验证|决策|检索|转换|创作|知识|信息|指标|模式|趋势|异常|风险|缺口|关联|洞察)', text)
            entities += cn_entities
            for e in entities:
                if e.strip():
                    self.entities[e.strip()].append(seg.get("source", "unknown"))

    def _semantic_links(self):
        """语义相似度关联"""
        for i, seg_a in enumerate(self.segments):
            for j, seg_b in enumerate(self.segments[i+1:], i+1):
                sim = self._text_similarity(seg_a["content"], seg_b["content"])
                if sim > 0.3:
                    self._add_link(seg_a["source"], seg_b["source"], "语义关联", sim)

    def _cooccurrence_links(self):
        """共现实体关联"""
        for entity, sources in self.entities.items():
            if len(sources) >= 2:
                for i in range(len(sources)-1):
                    self._add_link(sources[i], sources[i+1], "实体共现", 0.7)

    def _temporal_links(self):
        """时序关联"""
        time_markers = ["首先", "然后", "接着", "最后", "之前", "之后"]
        for i, seg_a in enumerate(self.segments):
            text_a = seg_a.get("content", "")
            if any(m in text_a for m in time_markers):
                if i < len(self.segments) - 1:
                    self._add_link(seg_a["source"], self.segments[i+1]["source"], "时序关联", 0.6)

    def _causal_links(self):
        """因果关联"""
        causal_markers = ["因为", "所以", "导致", "因此", "由于"]
        for seg in self.segments:
            text = seg.get("content", "")
            if any(m in text for m in causal_markers):
                # 简化：与前面最近的一段建立因果
                idx = self.segments.index(seg)
                if idx > 0:
                    self._add_link(self.segments[idx-1]["source"], seg["source"], "因果关系", 0.5)

    def _add_link(self, src, dst, rel_type, strength):
        # 去重
        for existing in self.links:
            if existing["source"] == src and existing["target"] == dst and existing["type"] == rel_type:
                existing["strength"] = max(existing["strength"], strength)
                return
        self.links.append({
            "source": src,
            "target": dst,
            "type": rel_type,
            "strength": round(strength, 2),
            "confidence": "A" if strength > 0.8 else "B" if strength > 0.5 else "C",
        })

    def _prune_weak_links(self):
        self.links = [l for l in self.links if l["strength"] > 0.3]

    def _text_similarity(self, a, b):
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / len(words_a | words_b)

    def _build_output(self):
        mermaid = self._generate_mermaid()
        return {
            "detector": "dalu-dongguan",
            "version": "5.0",
            "segment_count": len(self.segments),
            "entity_count": len(self.entities),
            "link_count": len(self.links),
            "links": self.links,
            "entity_map": dict(self.entities),
            "knowledge_graph": {
                "nodes": list(self.entities.keys()),
                "edges": self.links,
            },
            "mermaid_code": mermaid,
        }

    def _generate_mermaid(self):
        lines = ["graph TD"]
        for link in self.links:
            label = f"|{link['type']} ({link['confidence']})|"
            lines.append(f"    {link['source']}[{link['source']}] -->{label} {link['target']}[{link['target']}]")
        return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python link_detector.py <segments.json>")
        print('  segments: [{"source":"A段","content":"文本..."}, ...]')
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        segments = json.load(f)

    detector = LinkDetector(segments)
    result = detector.detect()

    out = Path("link_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 50)
    print("🔭 大罗洞观 · 关联检测报告")
    print("=" * 50)
    print(f"  段落数: {result['segment_count']}")
    print(f"  实体数: {result['entity_count']}")
    print(f"  关联数: {result['link_count']}")
    print("-" * 50)
    for link in result["links"][:10]:
        emoji = "🔒" if link["confidence"] == "A" else "🔗" if link["confidence"] == "B" else "📎"
        print(f"  {emoji} [{link['confidence']}] {link['source']} --({link['type']})--> {link['target']} |强度:{link['strength']}")
    if len(result["links"]) > 10:
        print(f"  ... 等共 {len(result['links'])} 条关联")
    print("-" * 50)
    print("📊 Mermaid认知地图代码已生成")
    print(result["mermaid_code"][:200] + "...")
    print("=" * 50)


    print(f"详细报告: {out}")


if __name__ == "__main__":
    main()