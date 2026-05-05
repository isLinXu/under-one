#!/usr/bin/env python3
"""
器名: 八卦阵中央协调器 (Bagua Coordinator)
用途: 管理八技状态、互斥仲裁、效能聚合、生成全局监控面板
输入: JSON {"skills":[{...}], "active_requests":[{...}]}
输出: JSON {status_bus,arbitration,aggregated_score,dashboard}
"""

import json
import sys
from pathlib import Path
from collections import defaultdict


SKILL_NAMES = [
    "qiti-yuanliu", "tongtian-lu", "dalu-dongguan", "shenji-bailian",
    "fenghou-qimen", "liuku-xianzei", "shuangquanshou", "juling-qianjiang",
    "xiushen-lu",  # 修身炉作为第9核心组件
]

MUTEX_PAIRS = {
    ("tongtian-lu", "shenji-bailian"),  # 符箓 vs 锻造
    ("qiti-yuanliu", "fenghou-qimen"),   # 修复 vs 重排
    ("dalu-dongguan", "liuku-xianzei"),  # 洞察 vs 吸收
}


class BaguaCoordinator:
    def __init__(self, skills_data, requests):
        self.skills = {s["id"]: s for s in skills_data}
        self.requests = requests
        self.queue = defaultdict(list)

    def coordinate(self):
        status_bus = self._scan_status()
        arbitration = self._arbitrate()
        aggregated = self._aggregate_scores()
        evolution_status = self._check_xiushenlu()  # V6: 修身炉状态监控
        dashboard = self._generate_dashboard()
        return {
            "coordinator": "bagua-zhen",
            "version": "6.0",
            "status_bus": status_bus,
            "arbitration": arbitration,
            "aggregated_score": aggregated,
            "evolution_status": evolution_status,  # V6: 新增进化状态
            "dashboard": dashboard,
            "timestamp": "auto",
        }

    def _check_xiushenlu(self):
        """V6: 监控修身炉进化状态，在进化期间对相关skill进行资源保护"""
        xiushenlu = self.skills.get("xiushen-lu", {})
        if not xiushenlu:
            return {"active": False, "message": "修身炉未激活"}

        evolving = xiushenlu.get("evolving_skills", [])
        if evolving:
            return {
                "active": True,
                "evolving": evolving,
                "protection": "进化期间skill只读，仲裁时优先级降级",
                "queue_depth": len(self.requests),
            }
        return {"active": True, "evolving": [], "message": "修身炉运行中，暂无进化任务"}

    def _scan_status(self):
        bus = []
        active_count = 0
        for sid in SKILL_NAMES:
            skill = self.skills.get(sid, {})
            status = skill.get("status", "休眠")
            if status == "激活":
                active_count += 1
            bus.append({
                "id": sid,
                "name": skill.get("name", sid),
                "status": status,
                "round": skill.get("round", "-"),
                "score": skill.get("score", 0),
                "health": skill.get("health", "⚪"),
                "mutex_lock": skill.get("mutex_lock", "无"),
            })
        return {"entries": bus, "active_count": active_count, "sleep_count": 8 - active_count}

    def _arbitrate(self):
        conflicts = []
        active = [sid for sid, s in self.skills.items() if s.get("status") == "激活"]
        for a in active:
            for b in active:
                if a != b and (a, b) in MUTEX_PAIRS:
                    # 仲裁
                    winner, loser = self._judge(a, b)
                    conflicts.append({
                        "pair": (a, b),
                        "winner": winner,
                        "loser": loser,
                        "reason": self._reason(a, b, winner),
                        "action": f"{winner}继续，{loser}排队",
                    })
                    self.queue[loser].append(f"等待{winner}完成")
        return {"conflicts_detected": len(conflicts), "resolutions": conflicts, "queue": dict(self.queue)}

    def _judge(self, a, b):
        score_a = self.skills.get(a, {}).get("score", 0)
        score_b = self.skills.get(b, {}).get("score", 0)
        # 效能分高优先
        if score_a > score_b:
            return a, b
        elif score_b > score_a:
            return b, a
        # 平局：字母序
        return (a, b) if a < b else (b, a)

    def _reason(self, a, b, winner):
        return f"效能分 {self.skills[winner].get('score',0)} > {self.skills[a if winner==b else b].get('score',0)}"

    def _aggregate_scores(self):
        scores = [self.skills.get(sid, {}).get("score", 0) for sid in SKILL_NAMES]
        avg = sum(scores) / len(scores) if scores else 0
        excellent = sum(1 for s in scores if s >= 90)
        health_rate = excellent / 8 * 100
        level = "阵法大成" if avg >= 90 else "阵法稳固" if avg >= 75 else "阵法松动" if avg >= 60 else "阵法破损"
        return {
            "average": round(avg, 1),
            "health_rate": round(health_rate, 1),
            "excellent_count": excellent,
            "level": level,
            "individual": {sid: self.skills.get(sid, {}).get("score", 0) for sid in SKILL_NAMES},
        }

    def _generate_dashboard(self):
        # ASCII 柱状图
        lines = ["【八技效能仪表盘】"]
        for sid in SKILL_NAMES:
            score = self.skills.get(sid, {}).get("score", 0)
            bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
            lines.append(f"  {sid:<15} {bar} {score:.1f}")
        lines.append("")
        # 互斥矩阵可视化
        lines.append("【互斥矩阵】")
        lines.append("  通天箓 <-> 神机百炼 (符箓 vs 锻造)")
        lines.append("  炁体源流 <-> 风后奇门 (修复 vs 重排)")
        lines.append("  大罗洞观 <-> 六库仙贼 (洞察 vs 吸收)")
        return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python coordinator.py <skills.json>")
        print('  skills: [{"id":"qiti-yuanliu","name":"炁体源流","status":"休眠","score":92.5,"health":"🟢"}, ...]')
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    skills = data.get("skills", [])
    requests = data.get("active_requests", [])

    coord = BaguaCoordinator(skills, requests)
    result = coord.coordinate()

    out = Path("bagua_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 55)
    print("☯️ 八卦阵 · 中央协调报告")
    print("=" * 55)
    print(f"  激活技能: {result['status_bus']['active_count']} / 8")
    print(f"  休眠技能: {result['status_bus']['sleep_count']} / 8")
    print(f"  互斥冲突: {result['arbitration']['conflicts_detected']} 对")
    print(f"  全局效能: {result['aggregated_score']['average']:.1f}/100")
    print(f"  全局健康: {result['aggregated_score']['health_rate']:.1f}%")
    print(f"  阵法评级: {result['aggregated_score']['level']}")
    print("-" * 55)
    print(result["dashboard"])
    print("-" * 55)
    if result["arbitration"]["resolutions"]:
        print("⚖️ 仲裁结果:")
        for r in result["arbitration"]["resolutions"]:
            print(f"  {r['pair'][0]} vs {r['pair'][1]} -> 胜:{r['winner']} ({r['reason']})")
    print("=" * 55)
    print(f"详细报告: {out}")


if __name__ == "__main__":
    main()
