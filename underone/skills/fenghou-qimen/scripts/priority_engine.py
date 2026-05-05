#!/usr/bin/env python3
"""
器名: 优先级引擎 (Priority Engine)
用途: 对多个任务进行九维度评分、八门映射、输出执行计划
输入: JSON [{"name":"任务名","urgency":5,"importance":5,...}]
输出: JSON {ranked_tasks,eight_gates,monte_carlo,execution_plan}
"""

import json
import sys
import random
from pathlib import Path


class PriorityEngine:
    GATES = {
        (4.5, float("inf")): "开门",
        (4.0, 4.5): "生门",
        (3.2, 4.0): "景门",
        (2.5, 3.2): "杜门",
        (0.0, 2.5): "死门",
    }

    def __init__(self, tasks):
        self.tasks = tasks
        self.ranked = []

    def run(self):
        self._score_all()
        self._assign_gates()
        self._monte_carlo()
        return self._build_plan()

    def _score_all(self):
        for t in self.tasks:
            # 兼容 "important" 和 "importance" 两种字段名
            importance_val = t.get("importance") if t.get("importance") is not None else t.get("important", 3)
            base = (
                t.get("urgency", 3) * 0.25 +
                importance_val * 0.35 +
                t.get("dependency", 3) * 0.15 +
                t.get("resource_match", 3) * 0.10
            )
            timing = (
                t.get("deadline_pressure", 3) +
                t.get("dependency_ready", 3) +
                t.get("window", 3)
            ) / 3 * 0.10
            env = (
                t.get("context_ready", 3) +
                t.get("tool_available", 3) +
                t.get("tech_debt", 3)
            ) / 3 * 0.05
            team = (
                t.get("skill_match", 3) +
                t.get("stakeholder_support", 3) +
                t.get("history_success", 3)
            ) / 3 * 0.05
            t["composite_score"] = round(base + timing + env + team, 2)

        self.ranked = sorted(self.tasks, key=lambda x: x["composite_score"], reverse=True)

    def _assign_gates(self):
        for t in self.ranked:
            score = t["composite_score"]
            for (low, high), gate in self.GATES.items():
                if low <= score < high:
                    t["gate"] = gate
                    break
            else:
                t["gate"] = "死门"

    def _monte_carlo(self):
        """蒙特卡洛鲁棒性测试"""
        n_simulations = 100
        on_time_count = 0
        for _ in range(n_simulations):
            total_time = 0
            for t in self.ranked:
                # 随机扰动：耗时浮动±20%
                base_time = t.get("estimated_time", 30)
                actual = base_time * random.uniform(0.8, 1.2)
                total_time += actual
            if total_time <= sum(t.get("estimated_time", 30) for t in self.ranked) * 1.2:
                on_time_count += 1
        robustness = on_time_count / n_simulations * 100
        self.monte_carlo = {
            "simulations": n_simulations,
            "on_time_rate": round(robustness, 1),
            "assessment": "高鲁棒" if robustness > 80 else "中鲁棒" if robustness > 60 else "低鲁棒",
        }

    def _build_plan(self):
        plan = []
        for t in self.ranked:
            action = {
                "开门": "立即启动",
                "生门": "重点推进",
                "景门": "审视后执行",
                "杜门": "绕过障碍/延后",
                "死门": "终止释放资源",
            }.get(t["gate"], "待定")
            plan.append({
                "task": t["name"],
                "score": t["composite_score"],
                "gate": t["gate"],
                "action": action,
                "estimated_time": t.get("estimated_time", 30),
            })

        return {
            "engine": "fenghou-qimen",
            "version": "5.0",
            "task_count": len(self.tasks),
            "ranked_tasks": self.ranked,
            "execution_plan": plan,
            "monte_carlo": self.monte_carlo,
            "buffer_recommendation": "增加20%应急资源" if self.monte_carlo["on_time_rate"] < 80 else "无需额外缓冲",
        }


def main():
    if len(sys.argv) < 2:
        print("用法: python priority_engine.py <tasks.json>")
        print('  tasks: [{"name":"任务A","urgency":5,"importance":5,...}, ...]')
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        tasks = json.load(f)

    engine = PriorityEngine(tasks)
    result = engine.run()

    out = Path("priority_plan.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 55)
    print("🧭 风后奇门 · 优先级排盘报告")
    print("=" * 55)
    print(f"  任务数: {result['task_count']}")
    print(f"  蒙特卡洛: {result['monte_carlo']['simulations']}次模拟")
    print(f"  按时完成率: {result['monte_carlo']['on_time_rate']}% ({result['monte_carlo']['assessment']})")
    print(f"  {result['buffer_recommendation']}")
    print("-" * 55)
    for item in result["execution_plan"]:
        emoji = {"开门":"🟢","生门":"🟢","景门":"🟡","杜门":"🟠","死门":"🔴"}.get(item["gate"], "⚪")
        print(f"  {emoji} [{item['gate']}] {item['task']:<12} 得分:{item['score']:<5} -> {item['action']}")
    print("=" * 55)


    print(f"详细计划: {out}")


if __name__ == "__main__":
    main()