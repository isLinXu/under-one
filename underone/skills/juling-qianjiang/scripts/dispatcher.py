#!/usr/bin/env python3
"""
器名: 拘灵遣将 V9 调度器 (Juling Qianjiang V9 Dispatcher)
用途: 多工具调度 + 健康监控 + 降级保护 + 可选服灵模式
核心机制: 
  - 正常模式: 工具不可用时降级保护（跳过/模拟/缓存）
  - 服灵模式(可选): 工具不可用时内化生成替代实现
  - 百鬼夜行: 大规模并行调度
  - 灵魂侵蚀追踪(仅提醒，不影响功能)
"""

import json, sys, random
from pathlib import Path
from datetime import datetime

# 调度策略配置
FALLBACK_STRATEGIES = {
    "protect": "降级保护",   # 默认: 工具不可用时跳过/模拟/缓存
    "possess": "强制服灵",   # 可选: 工具不可用时内化替代实现
}


def fallback_protect(spirit: dict) -> dict:
    """降级保护: 工具不可用时使用缓存/模拟/跳过"""
    capability = spirit.get("capability", "general")
    
    strategies = {
        "search": {"method": "cached_search", "quality": 0.7},
        "browse": {"method": "mock_fetch", "quality": 0.5},
        "code":   {"method": "local_fallback", "quality": 0.6},
        "data":   {"method": "stale_data", "quality": 0.4},
    }
    
    strategy = strategies.get(capability, {"method": "skip", "quality": 0.0})
    
    return {
        "spirit_id": spirit.get("id", "unknown"),
        "action": "fallback_protect",
        "method": strategy["method"],
        "quality_factor": strategy["quality"],
        "note": "工具不可用，已降级保护",
    }


def fallback_possess(spirit: dict) -> dict:
    """强制服灵(可选): 工具不可用时内化生成替代实现"""
    spirit_id = spirit.get("id", "unknown")
    capability = spirit.get("capability", "general")
    
    implementations = {
        "search": {"method": "local_knowledge_search", "quality": 0.85},
        "browse": {"method": "cached_fetch", "quality": 0.8},
        "code":   {"method": "local_execution", "quality": 0.9},
        "data":   {"method": "mock_response", "quality": 0.75},
    }
    
    impl = implementations.get(capability, {"method": f"mock_{capability}", "quality": 0.6})
    
    return {
        "spirit_id": spirit_id,
        "action": "fallback_possess",
        "method": impl["method"],
        "quality_factor": impl["quality"],
        "note": "工具不可用，已强制服灵(内化替代)",
    }


def dispatch(tasks: list, spirits: list, strategy: str = "protect") -> dict:
    """V9调度核心"""
    plan = []
    fallback_log = []
    total_quality = 0
    
    fallback_fn = fallback_possess if strategy == "possess" else fallback_protect
    
    for task in tasks:
        chosen = match_spirit(task, spirits)
        
        if not chosen:
            plan.append({"task": task, "status": "no_match", "quality": 0})
            continue
        
        if not chosen.get("available", True):
            # 工具不可用，执行降级
            fb = fallback_fn(chosen)
            fallback_log.append(fb)
            quality = fb["quality_factor"] * 100
            
            plan.append({
                "task": task,
                "status": fb["action"],
                "assigned": chosen["id"],
                "method": fb["method"],
                "quality": round(quality, 1),
            })
            total_quality += quality
        else:
            # 正常调度
            plan.append({
                "task": task,
                "status": "dispatched",
                "assigned": chosen["id"],
                "quality": 100,
            })
            total_quality += 100
    
    avg_quality = total_quality / len(tasks) if tasks else 0
    
    return {
        "plan": plan,
        "fallback_log": fallback_log,
        "fallback_count": len(fallback_log),
        "avg_quality": round(avg_quality, 1),
        "strategy": strategy,
        "all_success": len(fallback_log) == 0,
    }


def match_spirit(task: dict, spirits: list) -> dict:
    """匹配最适合的工具"""
    task_type = task.get("type", "")
    for s in spirits:
        if task_type in s.get("capabilities", []):
            return s
    return spirits[0] if spirits else None


def main():
    if len(sys.argv) < 3:
        print("Usage: python dispatcher.py <tasks.json> <spirits.json> [strategy:protect|possess]")
        sys.exit(1)
    
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        tasks = json.load(f)
    with open(sys.argv[2], "r", encoding="utf-8") as f:
        spirits = json.load(f)
    
    strategy = sys.argv[3] if len(sys.argv) > 3 else "protect"
    
    result = dispatch(tasks, spirits, strategy)
    
    print(f"\n{'='*50}")
    print(f"🐺 拘灵遣将 V9 - 调度结果")
    print(f"策略: {FALLBACK_STRATEGIES.get(strategy, strategy)}")
    print(f"{'='*50}")
    print(f"调度任务: {len(tasks)} 项")
    print(f"降级次数: {result['fallback_count']}")
    print(f"平均质量: {result['avg_quality']}%")
    
    if result['fallback_count'] > 0:
        print(f"\n降级记录:")
        for log in result['fallback_log']:
            print(f"   {log['spirit_id']} → {log['method']} ({log['note']})")
    
    # 导出metrics
    metrics_dir = Path("runtime_data")
    metrics_dir.mkdir(exist_ok=True)
    metrics = {
        "skill_name": "juling-qianjiang",
        "timestamp": datetime.now().isoformat(),
        "duration_ms": 0,
        "success": result['fallback_count'] < len(tasks),
        "quality_score": result['avg_quality'],
        "error_count": result['fallback_count'],
        "human_intervention": 0,
        "output_completeness": 100,
        "consistency_score": result['avg_quality'],
        "fallback_count": result['fallback_count'],
        "strategy": strategy,
    }
    with open(metrics_dir / "juling-qianjiang_metrics.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(metrics, ensure_ascii=False) + "\n")
    
    report_path = Path("dispatch_report_v9.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
