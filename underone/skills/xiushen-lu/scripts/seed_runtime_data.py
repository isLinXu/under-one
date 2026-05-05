#!/usr/bin/env python3
"""
器名: 数据播种器
用途: 将36场景测试结果注入为修身炉的运行时数据
"""
import json, random
from pathlib import Path

# 自动定位 skills 目录（脚本位于 underone/skills/xiushen-lu/scripts/）
SKILL_DIR = str(Path(__file__).resolve().parent.parent.parent)  # → underone/skills
OUTPUT_DIR = Path("runtime_data")
OUTPUT_DIR.mkdir(exist_ok=True)

# 基于36场景测试结果模拟100条运行时记录 per skill
skill_configs = {
    "qiti-yuanliu": {
        "success_rate": 0.99, "avg_duration": 600, "avg_errors": 0.02, 
        "avg_human": 0.01, "avg_quality": 94, "complexity": "medium"
    },
    "tongtian-lu": {
        "success_rate": 0.95, "avg_duration": 800, "avg_errors": 0.05,
        "avg_human": 0.02, "avg_quality": 92, "complexity": "high"
    },
    "dalu-dongguan": {
        "success_rate": 0.92, "avg_duration": 700, "avg_errors": 0.08,
        "avg_human": 0.05, "avg_quality": 88, "complexity": "medium"
    },
    "shenji-bailian": {
        "success_rate": 0.97, "avg_duration": 1500, "avg_errors": 0.03,
        "avg_human": 0.01, "avg_quality": 95, "complexity": "high"
    },
    "fenghou-qimen": {
        "success_rate": 0.98, "avg_duration": 550, "avg_errors": 0.03,
        "avg_human": 0.01, "avg_quality": 96, "complexity": "medium"
    },
    "liuku-xianzei": {
        "success_rate": 0.90, "avg_duration": 1000, "avg_errors": 0.12,
        "avg_human": 0.08, "avg_quality": 82, "complexity": "high"
    },
    "shuangquanshou": {
        "success_rate": 0.93, "avg_duration": 500, "avg_errors": 0.07,
        "avg_human": 0.04, "avg_quality": 90, "complexity": "low"
    },
    "juling-qianjiang": {
        "success_rate": 0.96, "avg_duration": 1200, "avg_errors": 0.04,
        "avg_human": 0.02, "avg_quality": 93, "complexity": "high"
    },
    "bagua-zhen": {
        "success_rate": 0.99, "avg_duration": 400, "avg_errors": 0.01,
        "avg_human": 0.00, "avg_quality": 97, "complexity": "medium"
    },
}

def generate_records(skill_name, config, n=120):
    records = []
    for i in range(n):
        # 加入一些退化趋势（最后20条记录质量略降，触发进化）
        if i > n - 20:
            quality = max(50, config["avg_quality"] - random.randint(5, 15))
            errors = config["avg_errors"] + random.uniform(0.05, 0.2)
            human = min(1.0, config["avg_human"] + random.uniform(0.05, 0.15))
            success = random.random() < config["success_rate"] * 0.85
        else:
            quality = config["avg_quality"] + random.randint(-5, 5)
            errors = max(0, config["avg_errors"] + random.uniform(-0.02, 0.03))
            human = max(0, config["avg_human"] + random.uniform(-0.01, 0.02))
            success = random.random() < config["success_rate"]

        records.append({
            "skill_name": skill_name,
            "run_id": i,
            "duration_ms": max(100, int(config["avg_duration"] + random.randint(-100, 200))),
            "success": success,
            "quality_score": max(0, min(100, quality)),
            "error_count": max(0, round(errors, 2)),
            "human_intervention": 1 if human > 0.5 else (0 if human < 0.1 else round(human, 2)),
            "input_complexity": config["complexity"],
            "output_completeness": max(60, min(100, 95 + random.randint(-10, 5))),
            "consistency_score": max(50, min(100, quality + random.randint(-5, 5))),
        })
    return records

for skill, config in skill_configs.items():
    records = generate_records(skill, config)
    file_path = OUTPUT_DIR / f"{skill}_metrics.jsonl"
    with open(file_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  Seeded {len(records)} records for {skill} → {file_path}")

print(f"\n✅ 数据播种完成: {len(skill_configs)} skills × 120 records = {len(skill_configs)*120} total")
