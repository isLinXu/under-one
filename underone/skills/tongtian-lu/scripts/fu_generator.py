#!/usr/bin/env python3
"""
器名: 符箓生成器 (Fu Talisman Generator)
用途: 根据任务描述生成符箓模板、检测冲突、输出执行拓扑
输入: 任务描述字符串
输出: JSON {talisman_list, conflict_matrix, topology, execution_plan}
"""

import json
import sys
import re
from pathlib import Path


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


class FuGenerator:
    def __init__(self, task_desc):
        self.task = task_desc
        self.fu_list = []
        self.conflicts = []
        self.topology = []
        self.curse_level = "low"

    def generate(self):
        self._detect_dimensions()
        self._detect_curse()
        self._detect_conflicts()
        self._build_topology()
        return self._output()

    def _detect_dimensions(self):
        """检测任务维度，生成对应符箓"""
        detected = []
        for dim, keywords in DIMENSION_KEYWORDS.items():
            if any(kw in self.task for kw in keywords):
                detected.append(dim)
        if not detected:
            detected = ["analysis"]  # 默认分析箓
        for dim in detected:
            if dim in FU_TEMPLATES:
                self.fu_list.append(FU_TEMPLATES[dim].copy())

    def _detect_curse(self):
        """检测禁咒等级"""
        for kw in CONSTRAINT_KEYWORDS["高危"]:
            if kw in self.task:
                self.curse_level = "high"
                return
        for kw in CONSTRAINT_KEYWORDS["中危"]:
            if kw in self.task:
                self.curse_level = "medium"

    def _detect_conflicts(self):
        """检测符箓间冲突"""
        for i, fu_a in enumerate(self.fu_list):
            for j, fu_b in enumerate(self.fu_list[i+1:], i+1):
                conflict = self._check_conflict(fu_a, fu_b)
                if conflict:
                    self.conflicts.append({
                        "between": [fu_a["id"], fu_b["id"]],
                        "type": conflict["type"],
                        "severity": conflict["severity"],
                        "resolution": conflict["resolution"],
                    })

    def _check_conflict(self, a, b):
        # 风格冲突检测
        style_clash = {
            ("创作箓", "验证箓"): {"type": "风格矛盾", "severity": "medium", "resolution": "分层处理：创作->验证->风格统一箓"},
            ("分析箓", "创作箓"): {"type": "格式不匹配", "severity": "low", "resolution": "插入转换箓作为适配层"},
        }
        pair = (a["type"], b["type"])
        reverse = (b["type"], a["type"])
        if pair in style_clash:
            return style_clash[pair]
        if reverse in style_clash:
            return style_clash[reverse]
        return None

    def _build_topology(self):
        """构建执行拓扑"""
        # 简化的拓扑排序：检索->分析->决策->创作->验证->转换
        order_map = {
            "检索箓": 1, "分析箓": 2, "决策箓": 3,
            "创作箓": 4, "验证箓": 5, "转换箓": 6,
        }
        sorted_fu = sorted(self.fu_list, key=lambda x: order_map.get(x["type"], 99))
        self.topology = [fu["id"] for fu in sorted_fu]

    def _output(self):
        total_sla = sum(fu.get("avg_sla", 15) for fu in self.fu_list)
        return {
            "generator": "tongtian-lu",
            "version": "5.0",
            "task": self.task[:80],
            "dimension_count": len(self.fu_list),
            "talisman_list": self.fu_list,
            "curse_level": self.curse_level,
            "conflicts": self.conflicts,
            "topology": self.topology,
            "execution_plan": {
                "mode": "serial" if self.conflicts else "parallel_where_possible",
                "estimated_sla": total_sla,
                "adapter_insertions": len(self.conflicts),
            },
        }


def main():
    if len(sys.argv) < 2:
        print("用法: python fu_generator.py '<任务描述>' 或 python fu_generator.py <task.txt>")
        print("示例: python fu_generator.py '分析竞品数据并生成报告'")
        sys.exit(1)

    arg = sys.argv[1]
    # 自动识别文件路径 vs 直接任务描述
    if arg.endswith('.txt') and Path(arg).exists():
        task = Path(arg).read_text(encoding='utf-8').strip()
    else:
        task = arg
    gen = FuGenerator(task)
    result = gen.generate()

    output_file = Path("fu_plan.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 50)
    print("📜 通天箓 · 符箓生成报告")
    print("=" * 50)
    print(f"  任务: {result['task']}")
    print(f"  维度数: {result['dimension_count']}")
    print(f"  禁咒等级: {result['curse_level']}")
    print(f"  符箓列表:")
    for fu in result["talisman_list"]:
        print(f"    • [{fu['type']}] {fu['id']} | SLA:{fu['avg_sla']}s")
    print(f"  拓扑序: {' -> '.join(result['topology'])}")
    print(f"  冲突数: {len(result['conflicts'])}")
    for c in result["conflicts"]:
        print(f"    ⚠️ [{c['severity']}] {c['type']}: {c['resolution']}")
    print(f"  预估耗时: {result['execution_plan']['estimated_sla']}s")
    print(f"  执行模式: {result['execution_plan']['mode']}")
    print("=" * 50)


    print(f"详细计划已保存: {output_file}")


if __name__ == "__main__":
    main()