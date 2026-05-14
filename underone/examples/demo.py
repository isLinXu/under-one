#!/usr/bin/env python3
"""
under-one.skills 5分钟Demo
一行命令体验八奇技Agent运维框架

Usage:
    python underone/examples/demo.py

效果：自动运行5个核心skill的示例任务，展示完整输出
"""

import json
import sys
from pathlib import Path

# 允许从仓库根目录直接运行，无需先安装 editable package。
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from under_one import (
    PriorityEngine, ContextGuard,
    ToolOrchestrator, CommandFactory,
    EcosystemHub,
)


def demo_priority():
    """风后奇门：任务优先级排序"""
    print("\n" + "=" * 60)
    print("风后奇门 — 九维度任务优先级排序")
    print("=" * 60)

    tasks = [
        {"name": "修复生产环境P0故障", "urgency": 5, "importance": 5, "impact": 5, "dependency": 1, "resource_match": 5, "deadline_risk": 5, "reversibility": 5, "stakeholder": 5},
        {"name": "撰写本周团队周报", "urgency": 3, "importance": 2, "impact": 2, "dependency": 1, "resource_match": 4, "deadline_risk": 3, "reversibility": 5, "stakeholder": 2},
        {"name": "重构订单模块代码", "urgency": 2, "importance": 4, "impact": 4, "dependency": 3, "resource_match": 3, "deadline_risk": 2, "reversibility": 3, "stakeholder": 3},
        {"name": "准备Q3产品规划PPT", "urgency": 4, "importance": 5, "impact": 5, "dependency": 2, "resource_match": 4, "deadline_risk": 4, "reversibility": 4, "stakeholder": 5},
    ]

    engine = PriorityEngine()
    result = engine.run(tasks)

    print(f"任务数: {len(tasks)}")
    plan = result.get("execution_plan", [])
    for item in plan[:3]:
        gate = item.get("gate", "?")
        name = item.get("task") or item.get("name", "?")
        score = item.get("score", 0)
        print(f"  [{gate}] {name} (score={score:.2f})")


def demo_context():
    """炁体源流：上下文健康扫描"""
    print("\n" + "=" * 60)
    print("炁体源流 — 上下文稳态健康扫描")
    print("=" * 60)

    context = [
        {"role": "user", "content": "我们要用React做前端"},
        {"role": "assistant", "content": "好的，React方案已确定"},
        {"role": "user", "content": "我改主意了，用Vue吧"},
        {"role": "assistant", "content": "已切换为Vue方案"},
        {"role": "user", "content": "算了还是React吧"},
    ]

    guard = ContextGuard()
    result = guard.run(context)

    alerts = result.get("alerts", [])
    if alerts:
        print(f"发现 {len(alerts)} 个上下文问题:")
        for a in alerts[:2]:
            print(f"  [{a.get('level', '?')}] {a.get('message', a.get('msg', 'unknown'))}")
    else:
        print("上下文状态良好，无漂移检测")


def demo_orchestrator():
    """拘灵遣将：多工具调度"""
    print("\n" + "=" * 60)
    print("拘灵遣将 — 多工具调度+降级保护")
    print("=" * 60)

    tasks = [
        {"type": "search", "desc": "搜索最新AI论文"},
        {"type": "browse", "desc": "浏览arxiv摘要"},
        {"type": "code", "desc": "运行数据分析脚本"},
    ]
    spirits = [
        {"id": "search-api", "capabilities": ["search"], "available": True},
        {"id": "browse-bot", "capabilities": ["browse"], "available": False},
        {"id": "code-runner", "capabilities": ["code"], "available": True},
    ]

    orch = ToolOrchestrator()
    result = orch.run(tasks, spirits)

    plan = result.get("plan", [])
    for p in plan:
        status = p.get("status", "?")
        task = p.get("task", {}).get("type", "?")
        assigned = p.get("assigned", "?")
        quality = p.get("quality", "?")
        icon = " " if status == "dispatched" else " "
        print(f"  {icon}{task} → {assigned} [{status}] q={quality}")


def demo_command():
    """通天箓：任务拆解"""
    print("\n" + "=" * 60)
    print("通天箓 — 复杂任务自动拆解")
    print("=" * 60)

    task = "分析竞品数据并生成高管摘要报告"
    factory = CommandFactory()
    result = factory.run(task)

    print(f"任务: {task}")
    print(f"维度数: {result.get('dimension_count', result.get('dimensions', 0))}")
    print(f"禁咒等级: {result.get('curse_level', 'low')}")


def demo_ecosystem():
    """八卦阵：生态全景"""
    print("\n" + "=" * 60)
    print("八卦阵 — 十技生态全景")
    print("=" * 60)

    hub = EcosystemHub()
    result = hub.run()

    level = result.get("ecosystem_level", "未知")
    avg = result.get("average_quality", 0)
    active = result.get("active_skills", 0)
    print(f"生态评级: {level}")
    print(f"平均质量: {avg:.1f}")
    print(f"活跃技能: {active}/10")


def main():
    print("\n" + "=" * 60)
    print("  under-one.skills V10 — 八奇技Agent运维框架")
    print("  5分钟Demo: 5个核心技能自动运行")
    print("=" * 60)

    try:
        demo_priority()
        demo_context()
        demo_orchestrator()
        demo_command()
        demo_ecosystem()

        print("\n" + "=" * 60)
        print("  Demo 完成! 所有5个核心技能成功运行")
        print("  下一步: from under_one import * 开始在你的Agent中使用")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n  Demo运行遇到错误: {e}")
        print("  请确认当前在仓库根目录，或已正确安装 editable package。")
        print("  推荐命令: python underone/examples/demo.py\n")


if __name__ == "__main__":
    main()
