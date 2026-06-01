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
try:
    from under_one.config import get_skill_config
    from under_one.metrics import record_metrics
    from under_one.validation import validate_json_list
except ImportError:
    SKILLS_ROOT = Path(__file__).resolve().parent.parent.parent
    if str(SKILLS_ROOT) not in sys.path:
        sys.path.insert(0, str(SKILLS_ROOT))
    from metrics_compat import record_metrics

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

    # 完整七门体系（原著奇门遁甲八门：开/生/休/景/惊/杜/死，伤门合并入杜门）
    DEFAULT_GATES = {
        (4.5, float("inf")): "开门",  # 大吉，可出行征战
        (4.2, 4.5): "生门",           # 吉，利谋生求财
        (3.6, 4.2): "休门",           # 半吉，宜休整蓄势
        (3.2, 3.6): "景门",           # 中平，文书利
        (2.8, 3.2): "惊门",           # 半凶，变化动荡
        (2.5, 2.8): "杜门",           # 凶，阻塞封堵
        (0.0, 2.5): "死门",           # 大凶，终结收场
    }

    DEFAULT_ACTIONS = {
        "开门": "立即启动",
        "生门": "重点推进",
        "休门": "稳步推进，择机而动",
        "景门": "审视后执行",
        "惊门": "谨慎评估，防范变局",
        "杜门": "绕过障碍/延后",
        "死门": "终止释放资源",
    }

    TASK_TYPE_KEYWORDS = {
        "urgency_priority": ["紧急", "故障", "事故", "宕机", "hotfix", "incident", "blocker", "bug"],
        "quality_priority": ["质量", "测试", "安全", "合规", "审计", "重构", "验证", "quality", "security", "test"],
        "resource_limited": ["资源", "成本", "预算", "人手", "排期", "resource", "budget", "cost"],
        "team_driven": ["团队", "协作", "评审", "沟通", "干系人", "stakeholder", "team", "review"],
    }

    def __init__(self, tasks, template=None, task_history=None):
        """初始化引擎。
        
        Args:
            tasks: 任务列表
            template: 权重模板名称（如 'urgency_priority', 'quality_priority'）
                     为 None 时使用默认权重
            task_history: 可选历史任务样本，用于自适应权重微调
        """
        self.tasks = tasks
        self.task_history = task_history or []
        self.ranked = []
        self.monte_carlo = {}
        self.burn_mode_enabled = False
        self.adaptive_weighting = {
            "enabled": False,
            "selected_template": None,
            "reason": "disabled",
            "adjustments": {},
        }
        
        # 加载配置
        self._load_config(template)

    def _load_config(self, template=None):
        """从 under-one.yaml 加载配置。"""
        # 加载权重
        weights_cfg = get_skill_config("fenghouqimen", "weights", self.DEFAULT_WEIGHTS)
        templates_cfg = get_skill_config("fenghouqimen", "weight_templates", {})
        adaptive_cfg = get_skill_config("fenghouqimen", "adaptive_weights", {})
        
        # 调试输出（验证配置加载）
        # print(f"[DEBUG] template={template}, templates_keys={list(templates_cfg.keys()) if isinstance(templates_cfg, dict) else 'N/A'}")
        
        if template == "adaptive" or (not template and adaptive_cfg.get("enabled", False)):
            self.weights, self.active_template = self._adaptive_weights(weights_cfg, templates_cfg, adaptive_cfg)
        elif template and template in templates_cfg:
            self.weights = dict(templates_cfg[template])
            self.active_template = template
        else:
            self.weights = dict(weights_cfg)
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

    def _infer_task_type(self):
        if not self.tasks:
            return "balanced", "empty_task_list"

        joined = " ".join(
            str(task.get("name", "")) + " "
            + str(task.get("description", "")) + " "
            + " ".join(str(tag) for tag in task.get("tags", []))
            for task in self.tasks
        ).lower()
        for template, keywords in self.TASK_TYPE_KEYWORDS.items():
            if any(keyword.lower() in joined for keyword in keywords):
                return template, f"keyword:{template}"

        avg_urgency = sum(float(task.get("urgency", 3) or 3) for task in self.tasks) / len(self.tasks)
        avg_resource = sum(float(task.get("resource_match", 3) or 3) for task in self.tasks) / len(self.tasks)
        avg_team = sum(float(task.get("stakeholder_support", 3) or 3) for task in self.tasks) / len(self.tasks)
        if avg_urgency >= 4.0:
            return "urgency_priority", "high_avg_urgency"
        if avg_resource <= 2.2:
            return "resource_limited", "low_resource_match"
        if avg_team >= 4.0:
            return "team_driven", "high_stakeholder_support"
        return "balanced", "fallback"

    @staticmethod
    def _normalized_weights(weights, target_total):
        total = sum(float(value) for value in weights.values())
        if total <= 0:
            return weights
        return {key: round(float(value) / total * target_total, 4) for key, value in weights.items()}

    def _adaptive_weights(self, base_weights, templates_cfg, adaptive_cfg):
        selected_template, reason = self._infer_task_type()
        candidate = dict(templates_cfg.get(selected_template, base_weights))
        target_total = sum(float(value) for value in base_weights.values())
        adjustments = {}

        all_samples = self.task_history + self.tasks
        history_values = [
            float(item.get("history_success"))
            for item in all_samples
            if isinstance(item.get("history_success"), (int, float))
        ]
        if history_values:
            avg_history = sum(history_values) / len(history_values)
            low_success_threshold = float(adaptive_cfg.get("low_success_threshold", 2.6))
            high_success_threshold = float(adaptive_cfg.get("high_success_threshold", 4.2))
            boost = float(adaptive_cfg.get("history_boost", 0.05))
            if avg_history < low_success_threshold:
                candidate["dependency"] = candidate.get("dependency", 0.15) + boost
                candidate["environment_readiness"] = candidate.get("environment_readiness", 0.05) + boost / 2
                candidate["urgency"] = max(0.05, candidate.get("urgency", 0.25) - boost)
                adjustments["history_success"] = "boost_readiness_for_low_success"
            elif avg_history > high_success_threshold:
                candidate["importance"] = candidate.get("importance", 0.35) + boost / 2
                candidate["resource_match"] = candidate.get("resource_match", 0.10) + boost / 2
                candidate["dependency"] = max(0.05, candidate.get("dependency", 0.15) - boost / 2)
                adjustments["history_success"] = "lean_into_successful_pattern"

        normalized = self._normalized_weights(candidate, target_total)
        self.adaptive_weighting = {
            "enabled": True,
            "selected_template": selected_template,
            "reason": reason,
            "adjustments": adjustments,
        }
        return normalized, f"adaptive:{selected_template}"

    @record_metrics("fenghou-qimen")
    def run(self, burn=False):
        """执行评分、映射、模拟和计划生成。

        Args:
            burn: 是否点燃"龟蝇体"燃烧模式（紧急下牺牲质量换速度）。默认关闭。
        """
        self.burn_mode_enabled = bool(burn)
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
            "version": "v5.2",
            "task_count": len(self.tasks),
            "active_template": self.active_template,
            "weights_used": self.weights,
            "adaptive_weighting": self.adaptive_weighting,
            "ranked_tasks": self.ranked,
            "execution_plan": plan,
            "execution_phases": execution_phases,
            "alternative_plans": alternative_plans,
            "global_strategy": global_strategy,
            "luan_jin_tuo": self._build_luan_jin_tuo(plan),
            "gui_ying_ti": self._build_gui_ying_ti(plan),
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

    # ── V5.2 标志性招式：乱金柝（冻结）/ 龟蝇体（燃烧） ──────────
    def _build_luan_jin_tuo(self, plan):
        """乱金柝（扭曲时空 → 冻结资源）。

        当气运逆（鲁棒性低）或存在大凶死门/阻塞杜门任务时，冻结这些低优先
        任务的资源分配，令时间/资源向高优先任务集中——如同乱金柝冻结目标。
        """
        on_time = self.monte_carlo.get("on_time_rate", 100)
        frozen = [
            {"task": item["task"], "gate": item["gate"],
             "reason": "大凶/阻塞，冻结资源以聚焦高优先"}
            for item in plan if item["gate"] in ("死门", "杜门")
        ]
        triggered = on_time < self.robustness_medium or bool(frozen)
        return {
            "technique": "乱金柝",
            "triggered": triggered,
            "frozen_tasks": [f["task"] for f in frozen],
            "frozen_detail": frozen,
            "focus_tasks": [item["task"] for item in plan if item["gate"] in ("开门", "生门")],
            "lore": (
                "扭曲局部时空，冻结低优先任务，集中力量于关键命脉"
                if triggered else "气运尚顺，无需冻结"
            ),
        }

    def _build_gui_ying_ti(self, plan):
        """龟蝇体（燃烧生命换爆发 → 燃烧模式）。

        紧急模式下牺牲质量换速度：仅保留最高优先（开门/生门）任务、跳过验证
        尾阵，全力冲刺。默认关闭，run(burn=True) 时点燃。
        """
        enabled = getattr(self, "burn_mode_enabled", False)
        sprint = [item["task"] for item in plan if item["gate"] in ("开门", "生门")]
        if not sprint and plan:
            sprint = [plan[0]["task"]]
        return {
            "technique": "龟蝇体",
            "enabled": enabled,
            "sprint_tasks": sprint if enabled else [],
            "sacrificed": "质量与验证尾阵（牺牲生命换机能爆发）" if enabled else None,
            "lore": "燃烧生命，全力冲刺关键任务" if enabled else "未点燃，常态运行",
        }

    def _phase_bucket(self, task):
        gate = task.get("gate")
        dependency = task.get("dependency", 3)
        # 开门/生门 + 依赖简单 → 先手突破（气运顺，立即出手）
        if gate in {"开门", "生门"} and dependency <= 3:
            return ("phase-1", "先手突破")
        # 开门/生门/休门/景门 → 稳态推进（整体局势可为）
        if gate in {"开门", "生门", "休门", "景门"}:
            return ("phase-2", "稳态推进")
        # 惊门/杜门 → 障碍清理（局势有阻，需化解）
        if gate in {"惊门", "杜门"}:
            return ("phase-3", "障碍清理")
        # 死门 → 冻结观察（大凶，暂不动）
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
        print("用法: python priority_engine.py <tasks.json> [template] [--burn]")
        print('  tasks: [{"name":"任务A","urgency":5,"importance":5,...}, ...]')
        print('  template: balanced | urgency_priority | quality_priority | resource_limited | team_driven')
        print('  --burn: 点燃龟蝇体燃烧模式（紧急下牺牲质量换速度）')
        sys.exit(1)

    burn = "--burn" in sys.argv[2:]
    rest = [a for a in sys.argv[2:] if a != "--burn"]
    template = rest[0] if rest else None

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
    result = engine.run(burn=burn)

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
        emoji = {"开门":"🟢","生门":"🟢","休门":"🟢","景门":"🟡","惊门":"🟠","杜门":"🟠","死门":"🔴"}.get(item["gate"], "⚪")
        print(f"  {emoji} [{item['gate']}] {item['task']:<12} 得分:{item['score']:<5} -> {item['action']}")
    print("=" * 60)

    print(f"详细计划: {out}")


if __name__ == "__main__":
    main()
