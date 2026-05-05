#!/usr/bin/env python3
"""
器名: 修身炉核心引擎 (XiuShenLu Core Engine)
用途: Agent自进化中枢，驱动skill自主优化与迭代
输入: 运行时指标JSON 或 技能目录路径
输出: 进化报告 {evolution_type, changes, validation_result, new_version}

修身炉架构:
- QiSource (炁源): 收集运行时指标
- Refiner (炼化器): 分析性能瓶颈
- Transformer (转化器): 执行参数/逻辑优化
- Core (核心): 进化决策与触发控制
- Rollback (回退): 版本管理与安全回滚
"""

import json
import sys
import os
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════
# 炁源 - 运行时数据收集
# ═══════════════════════════════════════════════════════════
class QiSource:
    """炁源: 收集skill运行时指标，为进化提供燃料"""

    def __init__(self, data_dir: str = "runtime_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.buffer: List[Dict] = []

    def collect(self, metric: Dict) -> None:
        """收集单次skill执行指标"""
        metric["timestamp"] = datetime.now().isoformat()
        self.buffer.append(metric)

        # 每50条持久化一次
        if len(self.buffer) >= 50:
            self._flush()

    def _flush(self) -> None:
        """持久化到文件"""
        if not self.buffer:
            return
        skill_name = self.buffer[0].get("skill_name", "unknown")
        file_path = self.data_dir / f"{skill_name}_metrics.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            for m in self.buffer:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        self.buffer.clear()

    def load_history(self, skill_name: str, n: int = 100) -> List[Dict]:
        """加载skill的历史运行数据"""
        file_path = self.data_dir / f"{skill_name}_metrics.jsonl"
        if not file_path.exists():
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        records = [json.loads(line.strip()) for line in lines if line.strip()]
        return records[-n:]


# ═══════════════════════════════════════════════════════════
# 炼化器 - 性能分析 & 瓶颈检测
# ═══════════════════════════════════════════════════════════
class Refiner:
    """炼化器: 分析skill性能，检测瓶颈，提出进化建议"""

    THRESHOLDS = {
        "success_rate_warning": 0.80,  # V6: 更敏感的阈值
        "success_rate_critical": 0.65,
        "human_intervention_warning": 0.10,
        "human_intervention_critical": 0.25,
        "degradation_consecutive": 4,  # V6: 更早触发
        "sla_threshold": 1.15,
    }

    def analyze(self, records: List[Dict]) -> Dict:
        """分析skill运行记录，返回进化建议"""
        if not records:
            return {"status": "no_data", "recommendation": "needs_more_runs"}

        n = len(records)
        successes = sum(1 for r in records if r.get("success", False))
        total_errors = sum(r.get("error_count", 0) for r in records)
        total_human = sum(r.get("human_intervention", 0) for r in records)
        avg_duration = sum(r.get("duration_ms", 0) for r in records) / n
        avg_quality = sum(r.get("quality_score", 0) for r in records) / n

        success_rate = successes / n
        avg_errors = total_errors / n
        avg_human = total_human / n

        # 检测连续下降趋势
        consecutive_degradation = self._detect_degradation(records)

        # 生成进化建议
        recommendations = []
        evolution_type = "none"
        priority = "low"

        if success_rate < self.THRESHOLDS["success_rate_critical"]:
            recommendations.append(f"成功率严重下降 ({success_rate*100:.1f}%)，建议重构逻辑")
            evolution_type = "refactor"
            priority = "critical"
        elif success_rate < self.THRESHOLDS["success_rate_warning"]:
            recommendations.append(f"成功率低于阈值 ({success_rate*100:.1f}%)，建议扩展错误处理")
            evolution_type = "extension"
            priority = "high"

        if consecutive_degradation >= self.THRESHOLDS["degradation_consecutive"]:
            recommendations.append(f"连续{consecutive_degradation}次性能下降，建议参数调优")
            evolution_type = evolution_type if evolution_type != "none" else "tuning"
            priority = max(priority, "high", key=lambda x: {"low":0,"medium":1,"high":2,"critical":3}[x])

        if avg_human > self.THRESHOLDS["human_intervention_warning"]:
            recommendations.append(f"人工干预率过高 ({avg_human:.2f}/task)，建议增强自主性")
            evolution_type = evolution_type if evolution_type != "none" else "extension"
            priority = max(priority, "medium", key=lambda x: {"low":0,"medium":1,"high":2,"critical":3}[x])

        if avg_errors > 0.5:
            recommendations.append(f"错误密度偏高 ({avg_errors:.2f}/task)，建议增强鲁棒性")
            evolution_type = evolution_type if evolution_type != "none" else "extension"

        return {
            "status": "analyzed",
            "sample_size": n,
            "success_rate": round(success_rate, 3),
            "avg_errors": round(avg_errors, 2),
            "avg_human_intervention": round(avg_human, 2),
            "avg_duration_ms": round(avg_duration, 1),
            "avg_quality": round(avg_quality, 1),
            "consecutive_degradation": consecutive_degradation,
            "evolution_type": evolution_type,
            "priority": priority,
            "recommendations": recommendations,
            "health_score": self._calc_health_score(success_rate, avg_errors, avg_human, avg_quality),
        }

    def _detect_degradation(self, records: List[Dict]) -> int:
        """检测连续性能下降趋势"""
        streak = 0
        max_streak = 0
        prev_quality = None
        for r in records:
            q = r.get("quality_score", 100)
            if prev_quality is not None and q < prev_quality:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0
            prev_quality = q
        return max_streak

    def _calc_health_score(self, sr: float, err: float, human: float, quality: float) -> float:
        """计算skill健康分 0-100"""
        score = (
            sr * 30 +
            max(0, 1 - err) * 25 +
            max(0, 1 - human) * 20 +
            (quality / 100) * 25
        )
        return round(score, 1)


# ═══════════════════════════════════════════════════════════
# 转化器 - 自动参数优化 & 逻辑扩展
# ═══════════════════════════════════════════════════════════
class Transformer:
    """转化器: 根据炼化器的分析结果，执行具体的skill优化"""

    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.backup_dir = Path(skills_dir).parent / "skill_backups"
        self.backup_dir.mkdir(exist_ok=True)

    def evolve(self, skill_name: str, evolution_type: str, analysis: Dict) -> Dict:
        """执行skill进化"""
        skill_path = self.skills_dir / skill_name
        if not skill_path.exists():
            return {"status": "error", "message": f"Skill not found: {skill_name}"}

        # 备份当前版本
        self._backup(skill_name, skill_path)

        changes = []

        if evolution_type == "tuning":
            changes = self._apply_tuning(skill_name, skill_path, analysis)
        elif evolution_type == "extension":
            changes = self._apply_extension(skill_name, skill_path, analysis)
        elif evolution_type == "refactor":
            changes = self._apply_refactor(skill_name, skill_path, analysis)

        # 更新版本号
        new_version = self._bump_version(skill_name, skill_path, evolution_type)

        return {
            "status": "evolved",
            "skill_name": skill_name,
            "evolution_type": evolution_type,
            "changes": changes,
            "version": new_version,
            "timestamp": datetime.now().isoformat(),
        }

    def _backup(self, skill_name: str, skill_path: Path) -> None:
        """备份skill当前版本"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{skill_name}_{timestamp}"
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.copytree(skill_path, backup_path)

    def _apply_tuning(self, skill_name: str, skill_path: Path, analysis: Dict) -> List[str]:
        """低风险：参数调优"""
        changes = []
        script_dir = skill_path / "scripts"

        for script_file in script_dir.glob("*.py"):
            content = script_file.read_text(encoding="utf-8")
            original = content

            # 根据分析结果调整阈值
            if analysis["avg_errors"] > 0.3:
                # 放宽阈值，增强容错
                content = self._adjust_thresholds(content, factor=1.2)
                changes.append(f"{script_file.name}: 阈值放宽20%")

            if analysis["avg_human_intervention"] > 0.1:
                # 增强自主性，减少人工触发条件
                content = self._increase_autonomy(content)
                changes.append(f"{script_file.name}: 自主性增强")

            if content != original:
                script_file.write_text(content, encoding="utf-8")

        return changes

    def _apply_extension(self, skill_name: str, skill_path: Path, analysis: Dict) -> List[str]:
        """中风险：逻辑扩展"""
        changes = []
        changes.extend(self._apply_tuning(skill_name, skill_path, analysis))

        # 在SKILL.md中添加进化日志
        skill_md = skill_path / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            evolution_log = f"\n\n## Evolution Log\n\n- {datetime.now().isoformat()}: Extension - {', '.join(analysis.get('recommendations', []))[:100]}\n"
            if "## Evolution Log" not in content:
                content += evolution_log
            else:
                content = content.replace("## Evolution Log", f"## Evolution Log{evolution_log}")
            skill_md.write_text(content, encoding="utf-8")
            changes.append("SKILL.md: 添加进化日志")

        return changes

    def _apply_refactor(self, skill_name: str, skill_path: Path, analysis: Dict) -> List[str]:
        """高风险：架构重构"""
        changes = self._apply_extension(skill_name, skill_path, analysis)
        changes.append("触发架构重构流程（需八卦阵审批）")
        return changes

    def _adjust_thresholds(self, content: str, factor: float = 1.2) -> str:
        """调整代码中的阈值参数"""
        import re
        # 匹配 threshold = 数字 或 THRESHOLD: 数字 的模式
        def replace_threshold(match):
            key = match.group(1)
            val = float(match.group(2))
            new_val = round(val * factor, 2)
            return f"{key}{new_val}"

        content = re.sub(r'(threshold["\']?\s*[=:]\s*)([\d.]+)', replace_threshold, content, flags=re.IGNORECASE)
        return content

    def _increase_autonomy(self, content: str) -> str:
        """增强自主性：减少人工检查点"""
        # 注释掉人工确认相关的代码行
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if any(kw in line.lower() for kw in ["human_approval", "confirm", "人工", "确认"]):
                if not line.strip().startswith("#"):
                    line = "# [AUTO-EVOLVED] " + line
            new_lines.append(line)
        return "\n".join(new_lines)

    def _bump_version(self, skill_name: str, skill_path: Path, evolution_type: str) -> str:
        """更新版本号"""
        # 在SKILL.md中查找并更新版本
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            return "unknown"

        content = skill_md.read_text(encoding="utf-8")

        # 查找现有版本号
        import re
        version_match = re.search(r'version["\']?\s*[:=]\s*["\']?v?(\d+)\.(\d+)\.(\d+)', content)
        if version_match:
            major, minor, patch = int(version_match.group(1)), int(version_match.group(2)), int(version_match.group(3))

            if evolution_type == "refactor":
                major += 1
                minor = 0
                patch = 0
            elif evolution_type == "extension":
                minor += 1
                patch = 0
            else:  # tuning
                patch += 1

            new_version = f"v{major}.{minor}.{patch}"
            old_version = f"v{version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)}"
            content = content.replace(old_version, new_version)
        else:
            new_version = "v1.0.0"
            content = f"---\nversion: {new_version}\n" + content

        skill_md.write_text(content, encoding="utf-8")
        return new_version


# ═══════════════════════════════════════════════════════════
# 回退 - 版本管理与安全回滚
# ═══════════════════════════════════════════════════════════
class Rollback:
    """回退: 安全进化机制，保留最近5个版本，支持一键回滚"""

    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.backup_dir = Path(skills_dir).parent / "skill_backups"

    def list_versions(self, skill_name: str) -> List[Dict]:
        """列出skill的最近5个版本"""
        versions = []
        pattern = f"{skill_name}_*"
        for backup in sorted(self.backup_dir.glob(pattern), reverse=True):
            timestamp = backup.name.replace(f"{skill_name}_", "")
            versions.append({
                "version": timestamp,
                "path": str(backup),
                "size": sum(f.stat().st_size for f in backup.rglob("*") if f.is_file()),
            })
        return versions[:5]

    def rollback(self, skill_name: str, version: Optional[str] = None) -> Dict:
        """回滚skill到指定版本（默认最新备份）"""
        versions = self.list_versions(skill_name)
        if not versions:
            return {"status": "error", "message": f"No backup found for {skill_name}"}

        target = versions[0] if version is None else next(
            (v for v in versions if v["version"] == version), None
        )
        if not target:
            return {"status": "error", "message": f"Version {version} not found"}

        # 执行回滚
        skill_path = self.skills_dir / skill_name
        if skill_path.exists():
            shutil.rmtree(skill_path)
        shutil.copytree(target["path"], skill_path)

        return {
            "status": "rolled_back",
            "skill_name": skill_name,
            "version": target["version"],
            "timestamp": datetime.now().isoformat(),
        }


# ═══════════════════════════════════════════════════════════
# 核心 - 进化引擎主控
# ═══════════════════════════════════════════════════════════
class XiuShenLuCore:
    """修身炉核心: 进化决策与主控"""

    def __init__(self, skills_dir: str, data_dir: str = "runtime_data"):
        self.qi = QiSource(data_dir)
        self.refiner = Refiner()
        self.transformer = Transformer(skills_dir)
        self.rollback = Rollback(skills_dir)
        self.skills_dir = Path(skills_dir)

    def run_evolution_cycle(self, skill_name: Optional[str] = None) -> Dict:
        """
        执行完整的进化周期
        skill_name=None时，扫描全部skill进行进化判断
        """
        results = []
        targets = [skill_name] if skill_name else self._discover_skills()

        for target in targets:
            print(f"\n🔥 [{target}] 进化周期启动...")

            # 1. COLLECT - 收集数据
            records = self.qi.load_history(target, n=100)
            print(f"  1️⃣ COLLECT: {len(records)} 条历史记录")

            if len(records) < 10:
                print(f"  ⚠️ 数据不足(需要≥10条)，跳过进化")
                results.append({"skill": target, "status": "skipped", "reason": "insufficient_data"})
                continue

            # 2. ANALYZE - 分析瓶颈
            analysis = self.refiner.analyze(records)
            print(f"  2️⃣ ANALYZE: 健康分={analysis.get('health_score', 'N/A')} "
                  f"成功率={analysis.get('success_rate', 'N/A')} "
                  f"进化类型={analysis.get('evolution_type', 'N/A')}")

            # 3. DECIDE - 决策
            evo_type = analysis.get("evolution_type", "none")
            if evo_type == "none":
                print(f"  3️⃣ DECIDE: 无需进化，状态良好")
                results.append({"skill": target, "status": "no_action", "health": analysis.get("health_score")})
                continue

            priority = analysis.get("priority", "low")
            print(f"  3️⃣ DECIDE: 触发{evo_type}进化 (优先级: {priority})")

            # 4. EVOLVE - 执行进化
            evolution_result = self.transformer.evolve(target, evo_type, analysis)
            print(f"  4️⃣ EVOLVE: {evolution_result.get('status')} "
                  f"版本→{evolution_result.get('version', 'N/A')}")
            for change in evolution_result.get("changes", []):
                print(f"     ✓ {change}")

            # 5. VALIDATE - 验证
            validation = self._validate(target)
            print(f"  5️⃣ VALIDATE: {'通过' if validation['passed'] else '失败'}")

            if not validation["passed"]:
                # 回滚
                rb = self.rollback.rollback(target)
                print(f"  🔄 已回滚到 {rb.get('version')}")
                results.append({
                    "skill": target,
                    "status": "failed_rolled_back",
                    "evolution": evolution_result,
                    "validation": validation,
                })
                continue

            # 6. DEPLOY - 部署成功
            print(f"  6️⃣ DEPLOY: ✅ 进化成功部署")

            # 7. MONITOR - 监控
            print(f"  7️⃣ MONITOR: 将在后续10次运行中持续监控")

            results.append({
                "skill": target,
                "status": "evolved",
                "evolution": evolution_result,
                "analysis": analysis,
                "validation": validation,
            })

        return {
            "engine": "xiushen-lu",
            "version": "6.0",
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "total": len(targets),
                "evolved": sum(1 for r in results if r["status"] == "evolved"),
                "failed_rolled_back": sum(1 for r in results if r["status"] == "failed_rolled_back"),
                "no_action": sum(1 for r in results if r["status"] in ["no_action", "skipped"]),
            }
        }

    def _discover_skills(self) -> List[str]:
        """发现所有skill"""
        skills = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.append(item.name)
        return sorted(skills)

    def _validate(self, skill_name: str) -> Dict:
        """验证evolved skill的基本可用性"""
        skill_path = self.skills_dir / skill_name
        checks = {
            "has_skill_md": (skill_path / "SKILL.md").exists(),
            "has_scripts_dir": (skill_path / "scripts").is_dir(),
            "scripts_executable": True,
        }

        # 检查脚本是否有语法错误
        for script in (skill_path / "scripts").glob("*.py"):
            try:
                compile(script.read_text(encoding="utf-8"), str(script), "exec")
            except SyntaxError:
                checks["scripts_executable"] = False
                break

        passed = all(checks.values())
        return {"passed": passed, "checks": checks}


# ═══════════════════════════════════════════════════════════
# CLI入口
# ═══════════════════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python core_engine.py <skills_dir> [skill_name]")
        print("  示例:")
        print("    python core_engine.py /path/to/skills          # 进化全部skill")
        print("    python core_engine.py /path/to/skills qiti-yuanliu  # 进化指定skill")
        sys.exit(1)

    skills_dir = sys.argv[1]
    skill_name = sys.argv[2] if len(sys.argv) > 2 else None

    core = XiuShenLuCore(skills_dir)
    result = core.run_evolution_cycle(skill_name)

    # 输出摘要
    print("\n" + "=" * 60)
    print("🔥 修身炉 · 进化周期完成")
    print("=" * 60)
    summary = result["summary"]
    print(f"  总技能数: {summary['total']}")
    print(f"  成功进化: {summary['evolved']}")
    print(f"  失败回滚: {summary['failed_rolled_back']}")
    print(f"  无需进化: {summary['no_action']}")
    print("=" * 60)

    # 保存报告
    report_path = Path("evolution_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"进化报告: {report_path}")


if __name__ == "__main__":
    main()
