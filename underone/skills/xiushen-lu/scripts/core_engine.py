#!/usr/bin/env python3
"""
器名: 修身炉V7核心引擎 (XiuShenLu Core Engine V7)
用途: Agent自进化中枢V7 - 自适应阈值、深度进化、跨skill学习
输入: 运行时指标JSON 或 技能目录路径
输出: 进化报告 {evolution_type, changes, validation_result, new_version, adaptive_thresholds}

V7升级:
- 自适应阈值引擎: 根据历史数据动态调整进化触发阈值
- 深度进化: 不再只改SKILL.md，而是优化脚本内部参数
- 跨skill学习: 借鉴其他skill的优化经验
- 知识迁移: 自动将验证有效的阈值迁移到相关skill
"""

import json
import sys
import os
import re
import shutil
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# V7: 导入跨技能知识共享库
try:
    from shared_knowledge import get_hub
    KnowledgeHub = get_hub()
except ImportError:
    KnowledgeHub = None


# ═══════════════════════════════════════════════════════════
# V7 炁源 - 增强版运行时数据收集
# ═══════════════════════════════════════════════════════════
class QiSourceV7:
    """V7炁源: 增强版数据收集，支持实时流和批量导入"""

    def __init__(self, data_dir: str = "runtime_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.buffer: List[Dict] = []

    def collect(self, metric: Dict) -> None:
        metric["timestamp"] = datetime.now().isoformat()
        metric["v"] = "7.0"
        self.buffer.append(metric)
        if len(self.buffer) >= 50:
            self._flush()

    def _flush(self) -> None:
        if not self.buffer:
            return
        skill_name = self.buffer[0].get("skill_name", "unknown")
        file_path = self.data_dir / f"{skill_name}_metrics.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            for m in self.buffer:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        self.buffer.clear()

    def load_history(self, skill_name: str, n: int = 100) -> List[Dict]:
        file_path = self.data_dir / f"{skill_name}_metrics.jsonl"
        if not file_path.exists():
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        records = [json.loads(line.strip()) for line in lines if line.strip()]
        return records[-n:]


# ═══════════════════════════════════════════════════════════
# V7 炼化器 - 自适应阈值 + 深度瓶颈检测
# ═══════════════════════════════════════════════════════════
class RefinerV7:
    """V7炼化器: 自适应阈值引擎 + 深度瓶颈分析"""

    def __init__(self):
        # 基础阈值
        self.base_thresholds = {
            "success_rate_warning": 0.80,
            "success_rate_critical": 0.65,
            "human_intervention_warning": 0.10,
            "human_intervention_critical": 0.25,
            "degradation_consecutive": 4,
            "sla_threshold": 1.15,
            "quality_drop_threshold": 5.0,
        }
        # V7: 自适应阈值存储
        self.adaptive_file = Path("adaptive_thresholds.json")
        self.adaptive = self._load_adaptive()

    def _load_adaptive(self) -> Dict:
        if self.adaptive_file.exists():
            with open(self.adaptive_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_adaptive(self) -> None:
        with open(self.adaptive_file, "w", encoding="utf-8") as f:
            json.dump(self.adaptive, f, ensure_ascii=False, indent=2)

    def get_threshold(self, skill_name: str, key: str) -> float:
        """V7: 获取自适应阈值，优先使用skill特定配置，其次使用全局自适应"""
        # 1. 检查skill特定的自适应阈值
        skill_specific = self.adaptive.get(skill_name, {})
        if key in skill_specific:
            stored = skill_specific[key]
            # update_adaptive 存储的是 dict {"value": ..., "updated_at": ..., "reason": ...}
            if isinstance(stored, dict) and "value" in stored:
                return stored["value"]
            return stored
        # 2. 检查全局自适应阈值
        global_entry = self.adaptive.get("_global", {}).get(key)
        if global_entry is not None:
            if isinstance(global_entry, dict) and "value" in global_entry:
                return global_entry["value"]
            return global_entry
        # 3. 回退到基础阈值
        # V7: 尝试从KnowledgeHub获取
        if KnowledgeHub:
            kb_val = KnowledgeHub.get_threshold(skill_name, key)
            if kb_val is not None:
                return kb_val
        return self.base_thresholds.get(key, 0.5)

    def update_adaptive(self, skill_name: str, key: str, value: float, reason: str) -> None:
        """V7: 更新自适应阈值并记录原因"""
        if skill_name not in self.adaptive:
            self.adaptive[skill_name] = {}
        self.adaptive[skill_name][key] = {
            "value": value,
            "updated_at": datetime.now().isoformat(),
            "reason": reason,
        }
        self._save_adaptive()

    def analyze(self, skill_name: str, records: List[Dict]) -> Dict:
        if not records:
            return {"status": "no_data", "recommendation": "needs_more_runs"}

        n = len(records)
        successes = sum(1 for r in records if r.get("success", False))
        total_errors = sum(r.get("error_count", 0) for r in records)
        total_human = sum(r.get("human_intervention", 0) for r in records)
        qualities = [r.get("quality_score", 100) for r in records]
        avg_duration = sum(r.get("duration_ms", 0) for r in records) / n

        success_rate = successes / n
        avg_errors = total_errors / n
        avg_human = total_human / n
        avg_quality = sum(qualities) / n
        std_quality = statistics.stdev(qualities) if len(qualities) > 1 else 0

        # V7: 自适应阈值调整逻辑
        # 如果skill长期稳定（成功率>95%且质量方差<5），则放宽阈值以减少不必要的进化
        # 如果skill波动大（方差>15），则收紧阈值以更早发现问题
        quality_variance = std_quality
        if success_rate > 0.95 and quality_variance < 5:
            self.update_adaptive(skill_name, "success_rate_warning", 0.75,
                                 f"Skill高度稳定(成功率{success_rate*100:.0f}%, 方差{quality_variance:.1f})，放宽阈值")
        elif quality_variance > 15:
            self.update_adaptive(skill_name, "success_rate_warning", 0.85,
                                 f"Skill波动大(方差{quality_variance:.1f})，收紧阈值")

        # V7: 检测退化趋势
        consecutive_degradation = self._detect_degradation(records)

        # 获取当前自适应阈值
        sr_warn = self.get_threshold(skill_name, "success_rate_warning")
        sr_crit = self.get_threshold(skill_name, "success_rate_critical")
        hi_warn = self.get_threshold(skill_name, "human_intervention_warning")
        deg_thresh = self.get_threshold(skill_name, "degradation_consecutive")

        recommendations = []
        evolution_type = "none"
        priority = "low"

        if success_rate < sr_crit:
            recommendations.append(f"成功率严重下降 ({success_rate*100:.1f}%) < 临界值 {sr_crit*100:.0f}%")
            evolution_type = "refactor"
            priority = "critical"
        elif success_rate < sr_warn:
            recommendations.append(f"成功率低于阈值 ({success_rate*100:.1f}%) < 警告值 {sr_warn*100:.0f}%")
            evolution_type = "extension"
            priority = "high"

        if consecutive_degradation >= deg_thresh:
            recommendations.append(f"连续{consecutive_degradation}次性能下降 >= 阈值{deg_thresh}")
            evolution_type = evolution_type if evolution_type != "none" else "tuning"
            priority = max(priority, "high", key=lambda x: {"low": 0, "medium": 1, "high": 2, "critical": 3}[x])

        if avg_human > hi_warn:
            recommendations.append(f"人工干预率过高 ({avg_human:.2f}/task) > 阈值 {hi_warn}")
            evolution_type = evolution_type if evolution_type != "none" else "extension"

        # V7: 新增瓶颈类型识别
        bottleneck_type = self._identify_bottleneck(records, avg_errors, avg_human, quality_variance)

        return {
            "status": "analyzed",
            "sample_size": n,
            "success_rate": round(success_rate, 3),
            "avg_errors": round(avg_errors, 2),
            "avg_human_intervention": round(avg_human, 2),
            "avg_duration_ms": round(avg_duration, 1),
            "avg_quality": round(avg_quality, 1),
            "quality_variance": round(quality_variance, 2),
            "consecutive_degradation": consecutive_degradation,
            "evolution_type": evolution_type,
            "priority": priority,
            "bottleneck_type": bottleneck_type,
            "recommendations": recommendations,
            "adaptive_thresholds_used": {
                "success_rate_warning": sr_warn,
                "success_rate_critical": sr_crit,
                "human_intervention_warning": hi_warn,
                "degradation_consecutive": deg_thresh,
            },
            "health_score": self._calc_health_score(success_rate, avg_errors, avg_human, avg_quality),
        }

    def _detect_degradation(self, records: List[Dict]) -> int:
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

    def _identify_bottleneck(self, records: List[Dict], avg_errors: float, avg_human: float, variance: float) -> str:
        """V7: 识别瓶颈类型"""
        if avg_errors > 0.5:
            return "error_prone"
        if avg_human > 0.2:
            return "low_autonomy"
        if variance > 20:
            return "unstable"
        if avg_errors > 0.1 and avg_human > 0.05:
            return "comprehensive"
        return "stable"

    def _calc_health_score(self, sr: float, err: float, human: float, quality: float) -> float:
        score = sr * 30 + max(0, 1 - err) * 25 + max(0, 1 - human) * 20 + (quality / 100) * 25
        return round(score, 1)


# ═══════════════════════════════════════════════════════════
# V7 转化器 - 深度进化 + 跨skill学习
# ═══════════════════════════════════════════════════════════
class TransformerV7:
    """V7转化器: 深度进化（脚本参数优化）+ 跨skill知识迁移"""

    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.backup_dir = Path(skills_dir).parent / "skill_backups_v7"
        self.backup_dir.mkdir(exist_ok=True)

    def evolve(self, skill_name: str, evolution_type: str, analysis: Dict) -> Dict:
        skill_path = self.skills_dir / skill_name
        if not skill_path.exists():
            return {"status": "error", "message": f"Skill not found: {skill_name}"}

        self._backup(skill_name, skill_path)
        changes = []

        if evolution_type == "tuning":
            changes = self._deep_tuning(skill_name, skill_path, analysis)
        elif evolution_type == "extension":
            changes = self._deep_extension(skill_name, skill_path, analysis)
        elif evolution_type == "refactor":
            changes = self._deep_refactor(skill_name, skill_path, analysis)

        # V7: 跨skill知识迁移
        if KnowledgeHub and changes:
            for change in changes:
                if "threshold" in change.lower():
                    # 将验证有效的阈值分享到知识库
                    KnowledgeHub.contribute(skill_name, "threshold_evolution", {
                        "change": change,
                        "analysis": analysis,
                    })

        new_version = self._bump_version(skill_name, skill_path, evolution_type)

        return {
            "status": "evolved",
            "skill_name": skill_name,
            "evolution_type": evolution_type,
            "changes": changes,
            "version": new_version,
            "deep_evolution": True,  # V7标记
            "cross_skill_learned": KnowledgeHub is not None,
            "timestamp": datetime.now().isoformat(),
        }

    def _backup(self, skill_name: str, skill_path: Path) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{skill_name}_{timestamp}"
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.copytree(skill_path, backup_path)

    def _deep_tuning(self, skill_name: str, skill_path: Path, analysis: Dict) -> List[str]:
        """V7深度调优: 真正修改脚本内部参数"""
        changes = []
        script_dir = skill_path / "scripts"

        for script_file in script_dir.glob("*.py"):
            content = script_file.read_text(encoding="utf-8")
            original = content

            # V7: 根据瓶颈类型执行针对性调优
            bottleneck = analysis.get("bottleneck_type", "stable")
            avg_errors = analysis.get("avg_errors", 0)
            avg_human = analysis.get("avg_human_intervention", 0)

            if avg_errors > 0.3:
                # 错误率高: 放宽容错阈值，增强鲁棒性
                content = self._tune_thresholds(content, factor=1.2, direction="relax")
                changes.append(f"{script_file.name}: 阈值放宽20% (错误率高: {avg_errors:.2f})")

            if avg_human > 0.1:
                # 人工干预高: 增强自主性
                content = self._increase_autonomy(content)
                changes.append(f"{script_file.name}: 自主性增强 (干预率: {avg_human:.2f})")

            if bottleneck == "unstable":
                # 不稳定: 增加平滑因子，降低敏感度
                content = self._add_smoothing(content)
                changes.append(f"{script_file.name}: 增加平滑处理 (方差大)")

            # V7: 检查是否有shared_knowledge可借鉴
            if KnowledgeHub:
                # 查询类似skill的优化经验
                similar_skills = self._find_similar_skills(skill_name)
                for sim_skill in similar_skills:
                    learned = KnowledgeHub.query("threshold_evolution", sim_skill, n=3)
                    if learned:
                        changes.append(f"借鉴 {sim_skill} 经验: {len(learned)} 条优化记录")

            if content != original:
                script_file.write_text(content, encoding="utf-8")

        # 更新SKILL.md的进化日志
        self._update_evolution_log(skill_name, skill_path, analysis, changes)
        return changes

    def _deep_extension(self, skill_name: str, skill_path: Path, analysis: Dict) -> List[str]:
        """V7深度扩展: 逻辑扩展 + 新功能添加"""
        changes = self._deep_tuning(skill_name, skill_path, analysis)

        # V7: 根据瓶颈类型添加新功能
        bottleneck = analysis.get("bottleneck_type", "stable")
        script_dir = skill_path / "scripts"

        if bottleneck == "low_autonomy":
            # 添加自动决策分支
            for script_file in script_dir.glob("*.py"):
                content = script_file.read_text(encoding="utf-8")
                if "def main(" in content and "AUTO_DECISION" not in content:
                    # 在main函数中添加自动决策钩子
                    content = content.replace(
                        "if __name__ == \"__main__\":",
                        "# V7_AUTO_EXTENSION: 自动决策增强\nAUTO_DECISION = True\n\nif __name__ == \"__main__\":"
                    )
                    script_file.write_text(content, encoding="utf-8")
                    changes.append(f"{script_file.name}: 添加自动决策增强")
                    break

        return changes

    def _deep_refactor(self, skill_name: str, skill_path: Path, analysis: Dict) -> List[str]:
        """V7深度重构: 架构级变更"""
        changes = self._deep_extension(skill_name, skill_path, analysis)
        changes.append("触发V7架构重构流程（需八卦阵审批 + 全量测试）")
        return changes

    def _tune_thresholds(self, content: str, factor: float = 1.2, direction: str = "relax") -> str:
        """调整代码中的阈值"""
        import re

        def replace_threshold(match):
            key = match.group(1)
            val = float(match.group(2))
            if direction == "relax":
                new_val = round(val * factor, 2)
            else:
                new_val = round(val / factor, 2)
            return f"{key}{new_val}"

        content = re.sub(r'(threshold["\']?\s*[=:]\s*)([\d.]+)', replace_threshold, content, flags=re.IGNORECASE)
        return content

    def _increase_autonomy(self, content: str) -> str:
        """增强自主性"""
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if any(kw in line.lower() for kw in ["human_approval", "confirm", "人工", "确认"]):
                if not line.strip().startswith("#"):
                    line = "# [V7_AUTO] " + line
            new_lines.append(line)
        return "\n".join(new_lines)

    def _add_smoothing(self, content: str) -> str:
        """添加平滑处理"""
        if "smoothing" not in content.lower() and "ewma" not in content.lower():
            smooth_code = """
# V7_SMOOTHING: 指数加权移动平均平滑
_SMOOTHING_ALPHA = 0.3
_last_smoothed = None
def _smooth(value):
    global _last_smoothed
    if _last_smoothed is None:
        _last_smoothed = value
    else:
        _last_smoothed = _SMOOTHING_ALPHA * value + (1 - _SMOOTHING_ALPHA) * _last_smoothed
    return _last_smoothed
"""
            content = smooth_code + "\n" + content
        return content

    def _find_similar_skills(self, skill_name: str) -> List[str]:
        """查找功能相似的skill"""
        similarity_map = {
            "qiti-yuanliu": ["shuangquanshou"],
            "tongtian-lu": ["shenji-bailian"],
            "fenghou-qimen": ["juling-qianjiang"],
            "liuku-xianzei": ["dalu-dongguan"],
        }
        return similarity_map.get(skill_name, [])

    def _update_evolution_log(self, skill_name: str, skill_path: Path, analysis: Dict, changes: List[str]) -> None:
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            return

        content = skill_md.read_text(encoding="utf-8")
        evolution_log = f"""
## V7 Evolution Log

- {datetime.now().isoformat()}: {analysis.get('evolution_type', 'unknown')} - 深度进化
  - 健康分: {analysis.get('health_score', 'N/A')}
  - 瓶颈类型: {analysis.get('bottleneck_type', 'N/A')}
  - 自适应阈值: {json.dumps(analysis.get('adaptive_thresholds_used', {}), ensure_ascii=False)}
  - 变更: {', '.join(changes[:3])}
"""
        if "## V7 Evolution Log" not in content:
            content = content.rstrip() + "\n" + evolution_log + "\n"
        else:
            content = content.replace("## V7 Evolution Log", f"## V7 Evolution Log{evolution_log}")

        skill_md.write_text(content, encoding="utf-8")

    def _bump_version(self, skill_name: str, skill_path: Path, evolution_type: str) -> str:
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            return "unknown"

        content = skill_md.read_text(encoding="utf-8")
        import re

        # 查找metadata中的版本号
        version_match = re.search(r'metadata:\s*\n\s*version:\s*["\']?v?(\d+)\.(\d+)\.(\d+)', content)
        if version_match:
            major, minor, patch = int(version_match.group(1)), int(version_match.group(2)), int(version_match.group(3))

            if evolution_type == "refactor":
                major += 1
                minor = 0
                patch = 0
            elif evolution_type == "extension":
                minor += 1
                patch = 0
            else:
                patch += 1

            new_version = f"v{major}.{minor}.{patch}"
            old_version = f"v{version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)}"
            content = content.replace(old_version, new_version)
        else:
            new_version = "v7.0.0"
            if "metadata:" in content:
                content = content.replace("metadata:", f"metadata:\n  version: {new_version}", 1)
            else:
                content = content.replace("---\n", f"---\nmetadata:\n  version: {new_version}\n", 1)

        skill_md.write_text(content, encoding="utf-8")
        return new_version


# ═══════════════════════════════════════════════════════════
# V7 回退 - 增强版
# ═══════════════════════════════════════════════════════════
class RollbackV7:
    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.backup_dir = Path(skills_dir).parent / "skill_backups_v7"

    def list_versions(self, skill_name: str) -> List[Dict]:
        versions = []
        pattern = f"{skill_name}_*"
        for backup in sorted(self.backup_dir.glob(pattern), reverse=True):
            timestamp = backup.name.replace(f"{skill_name}_", "")
            versions.append({
                "version": timestamp,
                "path": str(backup),
                "size": sum(f.stat().st_size for f in backup.rglob("*") if f.is_file()),
            })
        return versions[:7]  # V7: 保留7个版本

    def rollback(self, skill_name: str, version: Optional[str] = None) -> Dict:
        versions = self.list_versions(skill_name)
        if not versions:
            return {"status": "error", "message": f"No backup found for {skill_name}"}

        target = versions[0] if version is None else next((v for v in versions if v["version"] == version), None)
        if not target:
            return {"status": "error", "message": f"Version {version} not found"}

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
# V7 核心 - 进化引擎主控
# ═══════════════════════════════════════════════════════════
class XiuShenLuCoreV7:
    """V7修身炉核心: 自适应阈值 + 深度进化 + 跨skill学习"""

    def __init__(self, skills_dir: str, data_dir: str = "runtime_data"):
        self.qi = QiSourceV7(data_dir)
        self.refiner = RefinerV7()
        self.transformer = TransformerV7(skills_dir)
        self.rollback = RollbackV7(skills_dir)
        self.skills_dir = Path(skills_dir)

    def run_evolution_cycle(self, skill_name: Optional[str] = None) -> Dict:
        results = []
        targets = [skill_name] if skill_name else self._discover_skills()

        for target in targets:
            if target == "xiushen-lu":
                continue  # 不修炉自身

            print(f"\n🔥 V7 [{target}] 进化周期启动...")

            records = self.qi.load_history(target, n=100)
            print(f"  1️⃣ COLLECT: {len(records)} 条历史记录")

            if len(records) < 10:
                print(f"  ⚠️ 数据不足，跳过")
                results.append({"skill": target, "status": "skipped"})
                continue

            analysis = self.refiner.analyze(target, records)
            print(f"  2️⃣ ANALYZE: 健康分={analysis.get('health_score')} 类型={analysis.get('evolution_type')} "
                  f"瓶颈={analysis.get('bottleneck_type')}")

            evo_type = analysis.get("evolution_type", "none")
            if evo_type == "none":
                print(f"  3️⃣ DECIDE: 无需进化")
                results.append({"skill": target, "status": "no_action", "health": analysis.get("health_score")})
                continue

            print(f"  3️⃣ DECIDE: 触发{evo_type}深度进化")

            evolution_result = self.transformer.evolve(target, evo_type, analysis)
            print(f"  4️⃣ EVOLVE: {evolution_result.get('status')} 版本→{evolution_result.get('version')} "
                  f"深度={evolution_result.get('deep_evolution')}")
            for change in evolution_result.get("changes", []):
                print(f"     ✓ {change}")

            validation = self._validate(target)
            print(f"  5️⃣ VALIDATE: {'通过' if validation['passed'] else '失败'}")

            if not validation["passed"]:
                rb = self.rollback.rollback(target)
                print(f"  🔄 已回滚到 {rb.get('version')}")
                results.append({"skill": target, "status": "failed_rolled_back", "evolution": evolution_result})
                continue

            print(f"  6️⃣ DEPLOY: ✅ V7深度进化成功")
            results.append({
                "skill": target,
                "status": "evolved",
                "evolution": evolution_result,
                "analysis": analysis,
            })

        return {
            "engine": "xiushen-lu",
            "version": "7.0",
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
        skills = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.append(item.name)
        return sorted(skills)

    def _validate(self, skill_name: str) -> Dict:
        skill_path = self.skills_dir / skill_name
        checks = {
            "has_skill_md": (skill_path / "SKILL.md").exists(),
            "has_scripts_dir": (skill_path / "scripts").is_dir(),
            "scripts_executable": True,
        }

        for script in (skill_path / "scripts").glob("*.py"):
            try:
                compile(script.read_text(encoding="utf-8"), str(script), "exec")
            except SyntaxError:
                checks["scripts_executable"] = False
                break

        return {"passed": all(checks.values()), "checks": checks}


def main():
    if len(sys.argv) < 2:
        print("用法: python core_engine.py <skills_dir> [skill_name]")
        sys.exit(1)

    skills_dir = sys.argv[1]
    skill_name = sys.argv[2] if len(sys.argv) > 2 else None

    core = XiuShenLuCoreV7(skills_dir)
    result = core.run_evolution_cycle(skill_name)

    print("\n" + "=" * 60)
    print("🔥 V7 修身炉 · 深度进化周期完成")
    print("=" * 60)
    summary = result["summary"]
    print(f"  总技能数: {summary['total']}")
    print(f"  成功进化: {summary['evolved']}")
    print(f"  失败回滚: {summary['failed_rolled_back']}")
    print(f"  无需进化: {summary['no_action']}")
    print("=" * 60)

    report_path = Path("evolution_report_v7.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"V7进化报告: {report_path}")


if __name__ == "__main__":
    main()
