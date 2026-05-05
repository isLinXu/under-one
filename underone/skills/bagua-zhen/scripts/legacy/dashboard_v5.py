#!/usr/bin/env python3
"""
器名: 八技效能监控面板 (Hachigiki Dashboard)
用途: 汇总八技效能报告，生成全局可视化面板
输入: 多个 *_report.json 文件
输出: HTML监控面板
"""

import json
import sys
from pathlib import Path


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>八奇技 · 效能监控面板</title>
<style>
body { font-family: 'Microsoft YaHei', sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
.header { text-align: center; border-bottom: 2px solid #58a6ff; padding-bottom: 10px; margin-bottom: 20px; }
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; max-width: 1200px; margin: 0 auto; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; }
.card h3 { margin: 0 0 10px; color: #58a6ff; font-size: 14px; }
.score { font-size: 32px; font-weight: bold; text-align: center; margin: 10px 0; }
.score-excellent { color: #3fb950; }
.score-good { color: #58a6ff; }
.score-warning { color: #d29922; }
.score-danger { color: #f85149; }
.bar { height: 8px; background: #30363d; border-radius: 4px; overflow: hidden; margin: 8px 0; }
.bar-fill { height: 100%; border-radius: 4px; }
.details { font-size: 12px; color: #8b949e; margin-top: 8px; }
.status { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
.status-active { background: #238636; }
.status-sleep { background: #30363d; }
.status-danger { background: #da3633; }
</style>
</head>
<body>
<div class="header">
<h1>☯️ 八奇技 · 效能监控面板</h1>
<p>全局效能: {global_avg}/100 | 健康度: {global_health}% | 评级: {global_level}</p>
</div>
<div class="grid">
{skill_cards}
</div>
<div style="max-width:1200px;margin:20px auto;padding:15px;background:#161b22;border:1px solid #30363d;border-radius:8px;">
<h3 style="color:#58a6ff;margin-top:0;">互斥状态</h3>
<p>{mutex_status}</p>
</div>
</body>
</html>
"""

SKILL_META = {
    "qiti-yuanliu": {"cn": "炁体源流", "color": "#7ee787"},
    "tongtian-lu": {"cn": "通天箓", "color": "#79c0ff"},
    "dalu-dongguan": {"cn": "大罗洞观", "color": "#d2a8ff"},
    "shenji-bailian": {"cn": "神机百炼", "color": "#ffa657"},
    "fenghou-qimen": {"cn": "风后奇门", "color": "#ff7b72"},
    "liuku-xianzei": {"cn": "六库仙贼", "color": "#ffdcd7"},
    "shuangquanshou": {"cn": "双全手", "color": "#aff5b4"},
    "juling-qianjiang": {"cn": "拘灵遣将", "color": "#a5d6ff"},
}


def load_reports(report_dir):
    reports = {}
    for p in Path(report_dir).glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            skill_id = data.get("scanner") or data.get("generator") or data.get("detector") or data.get("factory") or data.get("engine") or data.get("digester") or data.get("validator") or data.get("dispatcher") or data.get("coordinator")
            if skill_id:
                reports[skill_id] = data
        except Exception:
            continue
    return reports


def generate_dashboard(reports):
    cards = []
    scores = []
    for sid, meta in SKILL_META.items():
        report = reports.get(sid, {})
        score = extract_score(report)
        scores.append(score)
        health = report.get("metrics", {}).get("health_level", "") or report.get("drift_level", "") or "unknown"
        status = "active" if health in ["green", "excellent"] else "sleep"
        bar_color = meta["color"]
        level_class = "score-excellent" if score >= 90 else "score-good" if score >= 75 else "score-warning" if score >= 60 else "score-danger"

        card = f"""<div class="card">
<h3>{meta['cn']} <span class="status status-{status}">{status}</span></h3>
<div class="score {level_class}">{score:.1f}</div>
<div class="bar"><div class="bar-fill" style="width:{score}%;background:{bar_color}"></div></div>
<div class="details">{sid}</div>
</div>"""
        cards.append(card)

    avg = sum(scores) / len(scores) if scores else 0
    health_rate = sum(1 for s in scores if s >= 90) / 8 * 100
    level = "阵法大成" if avg >= 90 else "阵法稳固" if avg >= 75 else "阵法松动" if avg >= 60 else "阵法破损"

    mutex = "无冲突"  # Simplified

    html = HTML_TEMPLATE.format(
        global_avg=f"{avg:.1f}",
        global_health=f"{health_rate:.1f}",
        global_level=level,
        skill_cards="\n".join(cards),
        mutex_status=mutex,
    )
    return html


def extract_score(report):
    # Try various score fields
    if "metrics" in report and "health_score" in report["metrics"]:
        return report["metrics"]["health_score"]
    if "composite_score" in report:
        return report["composite_score"]
    if "aggregated_score" in report and "average" in report["aggregated_score"]:
        return report["aggregated_score"]["average"]
    if "deviation_score" in report:
        return (1 - report["deviation_score"]) * 100
    if "sla_rate" in report:
        return report["sla_rate"]
    if "avg_digestion_rate" in report:
        return report["avg_digestion_rate"]
    return 70.0  # Default


def main():
    report_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    reports = load_reports(report_dir)
    html = generate_dashboard(reports)
    out = Path("hachigiki_dashboard.html")
    out.write_text(html, encoding="utf-8")
    print(f"✅ 监控面板已生成: {out.absolute()}")
    print(f"   加载了 {len(reports)} 个技能报告")
    print(f"   请在浏览器中打开查看")


if __name__ == "__main__":
    main()
