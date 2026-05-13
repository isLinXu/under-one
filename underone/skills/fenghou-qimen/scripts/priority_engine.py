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

# 运行时指标收集
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
try:
    from metrics_collector import record_metrics
except ImportError:
    def record_metrics(*args, **kwargs):
        def decorator(f): return f
        return decorator

# 输入验证与配置加载
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
try:
    from _skill_config import validate_json_list, get_skill_config
except ImportError:
    def validate_json_list(data, item_schema, skill_name="skill"):
        if not isinstance(data, list):
            return False, ["<root> must be a list"]
        return True, []
    def get_skill_config(skill_name, key=None, default=None):
        return default


class PriorityEngine:
    """风后奇门 - 优先级引擎 V5.1
    
    支持从 under-one.yaml 配置加载权重、阈值和模板。
    """

    # 默认配置（当 under-one.yaml 不可用时回退）
    DEFAULT_WEIGHTS = {
        "urgency": 0.25,
        "importance": 0.35,
        "dependency": 0.15,
        "resource_match": 0.10,
        "time_pressure": 0.10,
        "environment_readiness": 0.05,
        "team_match": 0.05,
    }

    DEFAULT_GATES = {
        (4.5, float("inf")): "开门",
        (4.0, 4.5): "生门",
        (3.2, 4.0): "景门",
        (2.5, 3.2): "杜门",
        (0.0, 2.5): "死门",
    }

    DEFAULT_ACTIONS = {
        "开门": "立即启动",
        "生门": "重点推进",
        "景门": "审视后执行",
        "杜门": "绕过障碍/延后",
        "死门": "终止释放资源",
    }

    def __init__(self, tasks, template=None):
        """初始化引擎。
        
        Args:
            tasks: 任务列表
            template: 权重模板名称（如 'urgency_priority', 'quality_priority'）
                     为 None 时使用默认权重
        """
        self.tasks = tasks
        self.ranked = []
        self.monte_carlo = {}
        
        # 加载配置
        self._load_config(template)

    def _load_config(self, template=None):
        """从 under-one.yaml 加载配置。"""
        # 加载权重
        weights_cfg = get_skill_config("fenghouqimen", "weights", self.DEFAULT_WEIGHTS)
        templates_cfg = get_skill_config("fenghouqimen", "weight_templates", {})
        
        # 调试输出（验证配置加载）
        # print(f"[DEBUG] template={template}, templates_keys={list(templates_cfg.keys()) if isinstance(templates_cfg, dict) else 'N/A'}")
        
        if template and template in templates_cfg:
            self.weights = templates_cfg[template]
            self.active_template = template
        else:
            self.weights = weights_cfg
            self.active_template = "default"
        
        # 加载八门阈值
        gates_cfg = get_skill_config("fenghouqimen", "gates", {})
        if gates_cfg:
            self.gates = {}
            for gate_name, (low, high) in gates_cfg.items():
                self.gates[(float(low), float(high))] = gate_name
        else:
            self.gates = self.DEFAULT_GATES.copy()
        
        # 加载蒙特卡洛参数
        self.mc_simulations = get_skill_config("fenghouqimen", "monte_carlo_simulations", 100)
        self.mc_variance = get_skill_config("fenghouqimen", "time_variance", 0.2)
        self.default_estimated_time = get_skill_config("fenghouqimen", "default_estimated_time", 30)
        self.mc_on_time_multiplier = get_skill_config("fenghouqimen", "on_time_multiplier", 1.2)
        
        # 加载鲁棒性评估阈值
        self.robustness_high = get_skill_config("fenghouqimen", "robustness_high", 80)
        self.robustness_medium = get_skill_config("fenghouqimen", "robustness_medium", 60)
        
        # 加载缓冲建议阈值
        self.buffer_threshold = get_skill_config("fenghouqimen", "buffer_threshold", 80)
        self.buffer_low = get_skill_config("fenghouqimen", "buffer_recommendation_low", "增加20%应急资源")
        self.buffer_high = get_skill_config("fenghouqimen", "buffer_recommendation_high", "无需额外缓冲")

    @record_metrics("fenghou-qimen")
    def run(self):
        """执行评分、映射、模拟和计划生成。"""
        self._score_all()
        self._assign_gates()
        self._monte_carlo()
        return self._build_plan()

    def _score_all(self):
        """九维度综合评分。"""
        w = self.weights
        for t in self.tasks:
            # 兼容 "important" 和 "importance" 两种字段名
            importance_val = t.get("importance") if t.get("importance") is not None else t.get("important", 3)
            
            # 基础维度（直接取值）
            base = (
                t.get("urgency", 3) * w.get("urgency", 0.25) +
                importance_val * w.get("importance", 0.35) +
                t.get("dependency", 3) * w.get("dependency", 0.15) +
                t.get("resource_match", 3) * w.get("resource_match", 0.10)
            )
            
            # 时间压力（三个子字段平均）
            timing = (
                t.get("deadline_pressure", 3) +
                t.get("dependency_ready", 3) +
                t.get("window", 3)
            ) / 3 * w.get("time_pressure", 0.10)
            
            # 环境就绪（三个子字段平均）
            env = (
                t.get("context_ready", 3) +
                t.get("tool_available", 3) +
                t.get("tech_debt", 3)
            ) / 3 * w.get("environment_readiness", 0.05)
            
            # 团队匹配（三个子字段平均）
            team = (
                t.get("skill_match", 3) +
                t.get("stakeholder_support", 3) +
                t.get("history_success", 3)
            ) / 3 * w.get("team_match", 0.05)
            
            t["composite_score"] = round(base + timing + env + team, 2)

        self.ranked = sorted(self.tasks, key=lambda x: x["composite_score"], reverse=True)

    def _assign_gates(self):
        """八门映射。"""
        for t in self.ranked:
            score = t["composite_score"]
            for (low, high), gate in self.gates.items():
                if low <= score < high:
                    t["gate"] = gate
                    break
            else:
                t["gate"] = "死门"

    def _monte_carlo(self):
        """蒙特卡洛鲁棒性测试。"""
        on_time_count = 0
        total_estimated = sum(t.get("estimated_time", self.default_estimated_time) for t in self.ranked)
        threshold = total_estimated * self.mc_on_time_multiplier
        
        for _ in range(self.mc_simulations):
            total_time = 0
            for t in self.ranked:
                base_time = t.get("estimated_time", self.default_estimated_time)
                actual = base_time * random.uniform(1 - self.mc_variance, 1 + self.mc_variance)
                total_time += actual
            if total_time <= threshold:
                on_time_count += 1
        
        robustness = on_time_count / self.mc_simulations * 100
        self.monte_carlo = {
            "simulations": self.mc_simulations,
            "on_time_rate": round(robustness, 1),
            "assessment": (
                "高鲁棒" if robustness > self.robustness_high 
                else "中鲁棒" if robustness > self.robustness_medium 
                else "低鲁棒"
            ),
        }

    def _build_plan(self):
        """生成执行计划。"""
        plan = []
        for t in self.ranked:
            action = self.DEFAULT_ACTIONS.get(t["gate"], "待定")
            plan.append({
                "task": t["name"],
                "score": t["composite_score"],
                "gate": t["gate"],
                "action": action,
                "estimated_time": t.get("estimated_time", self.default_estimated_time),
            })

        execution_phases = self._build_execution_phases(plan)
        alternative_plans = self._build_alternative_plans()
        global_strategy = self._build_global_strategy(execution_phases)

        return {
            "engine": "fenghou-qimen",
            "version": "v0.1.0",
            "task_count": len(self.tasks),
            "active_template": self.active_template,
            "weights_used": self.weights,
            "ranked_tasks": self.ranked,
            "execution_plan": plan,
            "execution_phases": execution_phases,
            "alternative_plans": alternative_plans,
            "global_strategy": global_strategy,
            "monte_carlo": self.monte_carlo,
            "buffer_recommendation": self.buffer_low if self.monte_carlo["on_time_rate"] < self.buffer_threshold else self.buffer_high,
            "quality_score": round(
                max(
                    0.0,
                    min(
                        100.0,
                        self.monte_carlo["on_time_rate"] * 0.7
                        + len(execution_phases) * 5.0
                        + min(12.0, len(plan) * 2.0)
                    ),
                ),
                1,
            ),
            "human_intervention": 1 if self.monte_carlo["on_time_rate"] < self.robustness_medium else 0,
            "output_completeness": round(
                min(100.0, 65.0 + len(plan) * 5.0 + len(alternative_plans) * 3.0 + len(execution_phases) * 4.0),
                1,
            ),
            "consistency_score": round(max(0.0, min(100.0, self.monte_carlo["on_time_rate"])), 1),
        }

    def _phase_bucket(self, task):
        gate = task.get("gate")
        dependency = task.get("dependency", 3)
        if gate in {"开门", "生门"} and dependency <= 3:
            return ("phase-1", "先手突破")
        if gate in {"开门", "生门", "景门"}:
            return ("phase-2", "稳态推进")
        if gate == "杜门":
            return ("phase-3", "障碍清理")
        return ("phase-4", "冻结观察")

    def _build_execution_phases(self, plan):
        buckets = {
            "phase-1": {"phase": "phase-1", "intent": "先手突破", "tasks": []},
            "phase-2": {"phase": "phase-2", "intent": "稳态推进", "tasks": []},
            "phase-3": {"phase": "phase-3", "intent": "障碍清理", "tasks": []},
            "phase-4": {"phase": "phase-4", "intent": "冻结观察", "tasks": []},
        }
        ranked_lookup = {item["name"]: item for item in self.ranked}
        for item in plan:
            ranked = ranked_lookup.get(item["task"], {})
            phase, intent = self._phase_bucket(ranked)
            buckets[phase]["intent"] = intent
            buckets[phase]["tasks"].append(item)

        phases = []
        for phase_name in ("phase-1", "phase-2", "phase-3", "phase-4"):
            bucket = buckets[phase_name]
            if not bucket["tasks"]:
                continue
            phases.append(
                {
                    "phase": bucket["phase"],
                    "intent": bucket["intent"],
                    "task_names": [task["task"] for task in bucket["tasks"]],
                    "task_count": len(bucket["tasks"]),
                    "estimated_time": sum(task["estimated_time"] for task in bucket["tasks"]),
                    "parallelizable": bucket["phase"] in {"phase-1", "phase-2"},
                    "gates": [task["gate"] for task in bucket["tasks"]],
                }
            )
        return phases

    def _build_alternative_plans(self):
        if not self.tasks:
            return {"balanced": [], "fast_track": [], "risk_averse": []}

        balanced = [task["name"] for task in self.ranked]
        fast_track = [
            task["name"]
            for task in sorted(
                self.ranked,
                key=lambda item: (
                    -item.get("urgency", 3),
                    item.get("estimated_time", self.default_estimated_time),
                    -item.get("resource_match", 3),
                ),
            )
        ]
        risk_averse = [
            task["name"]
            for task in sorted(
                self.ranked,
                key=lambda item: (
                    -item.get("resource_match", 3),
                    -item.get("dependency_ready", 3),
                    -item.get("stakeholder_support", 3),
                    -item.get("history_success", 3),
                ),
            )
        ]
        return {
            "balanced": balanced,
            "fast_track": fast_track,
            "risk_averse": risk_averse,
        }

    def _build_global_strategy(self, execution_phases):
        if not execution_phases:
            return "idle"
        if self.monte_carlo.get("on_time_rate", 0) < self.robustness_medium:
            return "staggered-push"
        first_phase = execution_phases[0]
        if first_phase["task_count"] >= 2 and first_phase["parallelizable"]:
            return "parallel-breakthrough"
        if any(phase["phase"] == "phase-4" for phase in execution_phases):
            return "containment-first"
        return "steady-advance"


def main():
    if len(sys.argv) < 2:
        print("用法: python priority_engine.py <tasks.json> [template]")
        print('  tasks: [{"name":"任务A","urgency":5,"importance":5,...}, ...]')
        print('  template: balanced | urgency_priority | quality_priority | resource_limited | team_driven')
        sys.exit(1)

    template = sys.argv[2] if len(sys.argv) > 2 else None

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        tasks = json.load(f)

    # 输入验证
    ok, errs = validate_json_list(tasks, {"name": str}, "fenghou-qimen")
    if not ok:
        print(f"输入验证失败: {errs}")
        sys.exit(2)
    if not tasks:
        print("错误: 任务列表不能为空")
        sys.exit(2)
    for i, t in enumerate(tasks):
        for field in ["urgency", "importance", "important"]:
            val = t.get(field)
            if val is not None and not isinstance(val, (int, float)):
                print(f"错误: 任务[{i}].{field} 必须是数值")
                sys.exit(2)
        if not t.get("name"):
            print(f"错误: 任务[{i}] 缺少名称")
            sys.exit(2)

    engine = PriorityEngine(tasks, template=template)
    result = engine.run()

    out = Path("priority_plan.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("🧭 风后奇门 · 优先级排盘报告")
    print("=" * 60)
    print(f"  任务数: {result['task_count']}")
    if result['active_template'] != 'default':
        print(f"  权重模板: {result['active_template']}")
    print(f"  蒙特卡洛: {result['monte_carlo']['simulations']}次模拟")
    print(f"  按时完成率: {result['monte_carlo']['on_time_rate']}% ({result['monte_carlo']['assessment']})")
    print(f"  {result['buffer_recommendation']}")
    print("-" * 60)
    for item in result["execution_plan"]:
        emoji = {"开门":"🟢","生门":"🟢","景门":"🟡","杜门":"🟠","死门":"🔴"}.get(item["gate"], "⚪")
        print(f"  {emoji} [{item['gate']}] {item['task']:<12} 得分:{item['score']:<5} -> {item['action']}")
    print("=" * 60)

    print(f"详细计划: {out}")


if __name__ == "__main__":
    main()
