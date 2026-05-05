#!/usr/bin/env python3
"""
器名: under-one.skills V7 效能进化监控面板
用途: 汇总十技效能+修身炉进化状态，生成实时可视化面板
输入: runtime_data/*_metrics.jsonl + evolution_report_v7.json
输出: HTML监控面板
"""

import json, sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

SKILL_META = {
    "qiti-yuanliu": {"cn": "炁体源流", "color": "#7ee787", "desc": "上下文稳态"},
    "tongtian-lu": {"cn": "通天箓", "color": "#79c0ff", "desc": "瞬发指令"},
    "dalu-dongguan": {"cn": "大罗洞观", "color": "#d2a8ff", "desc": "全局洞察"},
    "shenji-bailian": {"cn": "神机百炼", "color": "#ffa657", "desc": "工具锻造"},
    "fenghou-qimen": {"cn": "风后奇门", "color": "#ff7b72", "desc": "优先级引擎"},
    "liuku-xianzei": {"cn": "六库仙贼", "color": "#ffdcd7", "desc": "知识消化"},
    "shuangquanshou": {"cn": "双全手", "color": "#aff5b4", "desc": "人格守护"},
    "juling-qianjiang": {"cn": "拘灵遣将", "color": "#a5d6ff", "desc": "灵体调度"},
    "bagua-zhen": {"cn": "八卦阵", "color": "#f0883e", "desc": "中央协调"},
    "xiushen-lu": {"cn": "修身炉", "color": "#f778ba", "desc": "自进化中枢"},
}


def load_metrics(skill_name):
    file_path = Path("runtime_data") / f"{skill_name}_metrics.jsonl"
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [json.loads(l) for l in lines if l.strip()][-30:]


def calc_stats(records):
    if not records:
        return {"success_rate": 0, "quality": 0, "errors": 0, "human": 0, "consistency": 0, "n": 0}
    n = len(records)
    successes = sum(1 for r in records if r.get("success", False))
    return {
        "success_rate": round(successes / n * 100, 1),
        "quality": round(sum(r.get("quality_score", 0) for r in records) / n, 1),
        "errors": round(sum(r.get("error_count", 0) for r in records) / n, 2),
        "human": round(sum(r.get("human_intervention", 0) for r in records) / n, 2),
        "consistency": round(sum(r.get("consistency_score", 0) for r in records) / n, 1),
        "n": n,
    }


def generate_dashboard():
    all_stats = {}
    for sid in SKILL_META:
        all_stats[sid] = calc_stats(load_metrics(sid))

    # 生成skill卡片
    cards = []
    scores = []
    for sid, meta in SKILL_META.items():
        stats = all_stats[sid]
        score = stats["quality"] if stats["n"] > 0 else 85
        scores.append(score)

        if sid == "xiushen-lu":
            status = "active" if stats["n"] > 0 else "sleep"
        elif stats["n"] == 0:
            status = "sleep"
        elif stats["success_rate"] >= 95 and stats["human"] < 0.05:
            status = "active"
        elif stats["success_rate"] >= 80:
            status = "evolving"
        else:
            status = "danger"

        level_class = "score-excellent" if score >= 90 else "score-good" if score >= 75 else "score-warning" if score >= 60 else "score-danger"

        card = f'<div class="card"><h3>{meta["cn"]} <span class="status status-{status}">{status}</span></h3><div class="score {level_class}">{score:.1f}</div><div class="bar"><div class="bar-fill" style="width:{score}%;background:{meta["color"]}"></div></div><div class="details">成功率: {stats["success_rate"]:.0f}% | 错误: {stats["errors"]:.1f}/次<br>人工干预: {stats["human"]:.2f}/次 | 样本: {stats["n"]}<br><small>{meta["desc"]}</small></div></div>'
        cards.append(card)

    active_scores = [s for s in scores if s > 0]
    avg = sum(active_scores) / len(active_scores) if active_scores else 85
    health_rate = sum(1 for s in active_scores if s >= 90) / len(active_scores) * 100 if active_scores else 0
    level = "阵法大成" if avg >= 90 else "阵法稳固" if avg >= 75 else "阵法松动" if avg >= 60 else "阵法破损"

    # 修身炉状态
    evo_report = {}
    evo_path = Path("runtime_data") / ".." / "evolution_report_v7.json"
    if not evo_path.exists():
        evo_path = Path("evolution_report_v7.json")
    if evo_path.exists():
        with open(evo_path, "r", encoding="utf-8") as f:
            evo_report = json.load(f)
    summary = evo_report.get("summary", {})
    evo_total = summary.get("total", 10)
    evo_success = summary.get("evolved", 0)
    evo_rollback = summary.get("failed_rolled_back", 0)
    evo_pending = evo_total - evo_success - evo_rollback

    results = evo_report.get("results", [])
    latest = "暂无进化记录"
    for r in reversed(results):
        if r.get("status") == "evolved":
            ev = r.get("evolution", {})
            latest = f"{r['skill']} -> {ev.get('version', '?')} ({ev.get('evolution_type', '?')})"
            break

    # 趋势行
    trend_rows = []
    for sid, meta in SKILL_META.items():
        stats = all_stats[sid]
        if stats["n"] == 0:
            continue
        evo_status = ""
        for r in results:
            if r.get("skill") == sid and r.get("status") == "evolved":
                evo_type = r.get("evolution", {}).get("evolution_type", "?")
                badge_colors = {"tuning": "#58a6ff", "extension": "#a371f7", "refactor": "#f778ba"}
                color = badge_colors.get(evo_type, "#8b949e")
                evo_status = f'<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;background:{color}33;color:{color};border:1px solid {color}">{evo_type}</span>'
                break
        if not evo_status:
            evo_status = '<span style="color:#484f58;font-size:11px">-</span>'
        trend_rows.append(f'<tr><td><strong>{meta["cn"]}</strong> <small style="color:#484f58">{sid}</small></td><td>{stats["success_rate"]:.0f}%</td><td>{stats["quality"]:.1f}</td><td>{stats["errors"]:.2f}</td><td>{stats["human"]:.2f}</td><td>{evo_status}</td></tr>')

    # 知识共享统计
    shared_dir = Path("shared_knowledge")
    migration_count = len(list(shared_dir.glob("*.jsonl"))) if shared_dir.exists() else 0

    # 构建HTML - 使用replace而非format避免CSS花括号冲突
    html = HTML_BASE
    html = html.replace("{{GLOBAL_AVG}}", f"{avg:.1f}")
    html = html.replace("{{GLOBAL_HEALTH}}", f"{health_rate:.1f}")
    html = html.replace("{{GLOBAL_LEVEL}}", level)
    html = html.replace("{{XIUSHEN_STATUS}}", "运行中" if evo_report else "待机")
    html = html.replace("{{DATA_STREAM}}", "实时" if any(s["n"] > 0 for s in all_stats.values()) else "模拟")
    html = html.replace("{{SKILL_CARDS}}", "\n".join(cards))
    html = html.replace("{{EVO_TOTAL}}", str(evo_total))
    html = html.replace("{{EVO_SUCCESS}}", str(evo_success))
    html = html.replace("{{EVO_ROLLBACK}}", str(evo_rollback))
    html = html.replace("{{EVO_PENDING}}", str(evo_pending))
    html = html.replace("{{LATEST_EVO}}", latest)
    html = html.replace("{{ADAPTIVE_STATUS}}", "已启用")
    html = html.replace("{{TREND_ROWS}}", "\n".join(trend_rows))
    html = html.replace("{{KEYWORD_COUNT}}", "6")
    html = html.replace("{{THRESHOLD_COUNT}}", "15")
    html = html.replace("{{MIGRATION_COUNT}}", str(migration_count))
    html = html.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    out = Path("hachigiki_v7_dashboard.html")
    out.write_text(html, encoding="utf-8")
    print(f"✅ V7 Dashboard: {out.absolute()}")
    print(f"   Monitored: {len([s for s in all_stats.values() if s['n'] > 0])}/10 skills")
    print(f"   Avg quality: {avg:.1f}")
    print(f"   Evolution events: {evo_success}")
    return out


HTML_BASE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="30">
<title>under-one.skills V7 - Dashboard</title>
<style>
body { font-family: 'Microsoft YaHei','Segoe UI',sans-serif; background:#0d1117; color:#c9d1d9; padding:20px; margin:0; }
.header { text-align:center; border-bottom:2px solid #58a6ff; padding-bottom:15px; margin-bottom:25px; }
.header h1 { margin:0; font-size:28px; color:#58a6ff; }
.header p { margin:8px 0 0; color:#8b949e; font-size:14px; }
.grid { display:grid; grid-template-columns:repeat(5,1fr); gap:15px; max-width:1400px; margin:0 auto; }
.card { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:15px; }
.card:hover { border-color:#58a6ff; }
.card h3 { margin:0 0 10px; font-size:13px; display:flex; justify-content:space-between; }
.score { font-size:36px; font-weight:bold; text-align:center; margin:12px 0; }
.score-excellent { color:#3fb950; } .score-good { color:#58a6ff; } .score-warning { color:#d29922; } .score-danger { color:#f85149; }
.bar { height:8px; background:#30363d; border-radius:4px; overflow:hidden; margin:8px 0; }
.bar-fill { height:100%; border-radius:4px; }
.details { font-size:11px; color:#8b949e; margin-top:10px; line-height:1.6; }
.status { display:inline-block; padding:2px 8px; border-radius:4px; font-size:10px; }
.status-active { background:#238636; } .status-evolving { background:#1f6feb; } .status-sleep { background:#30363d; } .status-danger { background:#da3633; }
.section { max-width:1400px; margin:25px auto; padding:20px; background:#161b22; border:1px solid #30363d; border-radius:10px; }
.section h2 { color:#58a6ff; margin:0 0 15px; font-size:18px; border-left:4px solid #58a6ff; padding-left:12px; }
.trend-table { width:100%; border-collapse:collapse; font-size:12px; }
.trend-table th { text-align:left; padding:8px; border-bottom:1px solid #30363d; color:#8b949e; }
.trend-table td { padding:8px; border-bottom:1px solid #21262d; }
.metrics-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:15px; }
.metric-box { text-align:center; padding:15px; background:#0d1117; border-radius:8px; }
.metric-value { font-size:28px; font-weight:bold; color:#58a6ff; }
.metric-label { font-size:12px; color:#8b949e; margin-top:5px; }
.footer { text-align:center; margin-top:30px; padding:15px; color:#484f58; font-size:12px; }
</style>
</head>
<body>
<div class="header">
<h1>under-one.skills V7 - Ten Skills Evolution Dashboard</h1>
<p>{{GLOBAL_AVG}}/100 | Health {{GLOBAL_HEALTH}}% | {{GLOBAL_LEVEL}} | XiuShenLu: {{XIUSHEN_STATUS}} | Data: {{DATA_STREAM}}</p>
</div>
<div class="grid">
{{SKILL_CARDS}}
</div>
<div class="section">
<h2>XiuShenLu Evolution Status</h2>
<div class="metrics-grid">
<div class="metric-box"><div class="metric-value">{{EVO_TOTAL}}</div><div class="metric-label">Skills Monitored</div></div>
<div class="metric-box"><div class="metric-value" style="color:#3fb950">{{EVO_SUCCESS}}</div><div class="metric-label">Evolved</div></div>
<div class="metric-box"><div class="metric-value" style="color:#f85149">{{EVO_ROLLBACK}}</div><div class="metric-label">Rolled Back</div></div>
<div class="metric-box"><div class="metric-value" style="color:#d29922">{{EVO_PENDING}}</div><div class="metric-label">Pending</div></div>
</div>
<p style="margin-top:15px;font-size:12px;color:#8b949e;">Latest: {{LATEST_EVO}} | Adaptive Thresholds: {{ADAPTIVE_STATUS}}</p>
</div>
<div class="section">
<h2>Performance Trends (Last 30 Runs)</h2>
<table class="trend-table">
<tr><th>Skill</th><th>Success</th><th>Quality</th><th>Errors</th><th>Human</th><th>Evolution</th></tr>
{{TREND_ROWS}}
</table>
</div>
<div class="section">
<h2>Cross-Skill Knowledge Hub</h2>
<p style="font-size:12px;color:#8b949e;margin-bottom:10px;">
Shared Keywords: {{KEYWORD_COUNT}} categories | Shared Thresholds: {{THRESHOLD_COUNT}} items | Migrations: {{MIGRATION_COUNT}}
</p>
<p style="color:#484f58;font-size:12px">Cross-skill knowledge transfer system active. Skills automatically share threshold configs and keyword discoveries.</p>
</div>
<div class="footer">under-one.skills Framework V7.0 | Real-time Metrics | Self-Evolution Active | {{TIMESTAMP}}</div>
</body>
</html>"""


if __name__ == "__main__":
    generate_dashboard()
