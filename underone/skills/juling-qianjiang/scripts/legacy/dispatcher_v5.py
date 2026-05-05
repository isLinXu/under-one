#!/usr/bin/env python3
"""
器名: 灵体调度器 (Spirit Dispatcher)
用途: 模拟多灵体调度，SLA监控，降级处理
输入: JSON {"tasks":[{...}], "spirits":[{...}]}
输出: JSON {dispatch_plan, sla_log, fallback_count, health_report}
"""

import json
import sys
from pathlib import Path


class SpiritDispatcher:
    def __init__(self, tasks, spirits):
        self.tasks = tasks
        self.spirits = {s["name"]: s for s in spirits}
        self.plan = []
        self.sla_log = []
        self.fallback_count = 0

    def dispatch(self):
        for task in self.tasks:
            assignment = self._assign(task)
            self.plan.append(assignment)
            self._log_sla(assignment)
        return self._build_report()

    def _assign(self, task):
        spirit_type = task.get("required_spirit", "工具灵")
        candidates = [s for s in self.spirits.values() if s["type"] == spirit_type]
        
        if not candidates:
            return {
                "task": task["name"],
                "status": "failed",
                "reason": "无可用灵体",
                "fallback": "跳过",
            }

        # 选择最健康的
        primary = max(candidates, key=lambda s: s.get("health_score", 100))
        
        assignment = {
            "task": task["name"],
            "spirit": primary["name"],
            "health": primary.get("health_score", 100),
            "sla": task.get("sla", 30),
            "status": "assigned",
            "fallback": primary.get("fallback", "跳过"),
        }

        # 模拟超时
        if primary.get("health_score", 100) < 80:
            assignment["status"] = "degraded"
            assignment["reason"] = "灵体健康度低，启用降级"
            self.fallback_count += 1

        return assignment

    def _log_sla(self, assignment):
        self.sla_log.append({
            "task": assignment["task"],
            "spirit": assignment.get("spirit", "none"),
            "status": assignment["status"],
            "sla_met": assignment["status"] in ["assigned", "completed"],
        })

    def _build_report(self):
        sla_met = sum(1 for s in self.sla_log if s["sla_met"])
        sla_total = len(self.sla_log)
        
        return {
            "dispatcher": "juling-qianjiang",
            "version": "5.0",
            "task_count": len(self.tasks),
            "dispatch_plan": self.plan,
            "sla_log": self.sla_log,
            "sla_rate": round(sla_met / sla_total * 100, 1) if sla_total else 0,
            "fallback_count": self.fallback_count,
            "health_report": self._health_summary(),
        }

    def _health_summary(self):
        summary = {}
        for name, spirit in self.spirits.items():
            score = spirit.get("health_score", 100)
            summary[name] = {
                "score": score,
                "status": "优秀" if score > 95 else "良好" if score > 80 else "警戒" if score > 60 else "病态",
            }
        return summary


def main():
    if len(sys.argv) < 3:
        print("用法: python dispatcher.py <tasks.json> <spirits.json>")
        print('  tasks: [{"name":"任务A","required_spirit":"搜索灵","sla":15}, ...]')
        print('  spirits: [{"name":"搜索灵-1","type":"搜索灵","health_score":95,"fallback":"跳过"}, ...]')
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        tasks = json.load(f)
    with open(sys.argv[2], "r", encoding="utf-8") as f:
        spirits = json.load(f)

    dispatcher = SpiritDispatcher(tasks, spirits)
    result = dispatcher.dispatch()

    out = Path("dispatch_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 50)
    print("👻 拘灵遣将 · 灵体调度报告")
    print("=" * 50)
    print(f"  任务数: {result['task_count']}")
    print(f"  SLA达成率: {result['sla_rate']}%")
    print(f"  降级次数: {result['fallback_count']}")
    print("-" * 50)
    print("📋 调度计划:")
    for p in result["dispatch_plan"]:
        emoji = "✅" if p["status"] == "assigned" else "⚠️" if p["status"] == "degraded" else "❌"
        print(f"  {emoji} {p['task']:<12} -> {p.get('spirit','无')} ({p['status']})")
    print("-" * 50)
    print("🏥 灵体健康度:")
    for name, h in result["health_report"].items():
        emoji = "🟢" if h["status"] == "优秀" else "🟡" if h["status"] == "良好" else "🟠" if h["status"] == "警戒" else "🔴"
        print(f"  {emoji} {name}: {h['score']} ({h['status']})")
    print("=" * 50)


    print(f"详细报告: {out}")


if __name__ == "__main__":
    main()