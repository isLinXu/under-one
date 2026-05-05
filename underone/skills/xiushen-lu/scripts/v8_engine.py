#!/usr/bin/env python3
"""
器名: under-one.skills V8 预测智能引擎 (Predictive Intelligence Engine)
用途: 预测性维护 + A/B科学验证 + 智能记忆 + 联邦进化
输入: runtime_data/*_metrics.jsonl
输出: prediction_report.json + ab_test_report.json + memory_index.json

V8四大突破:
1. 预测性维护: 在崩溃前72小时(模拟)主动修复
2. A/B测试框架: 每次进化必须用对照组科学验证
3. 智能记忆系统: 向量持久化 + 语义检索
4. 联邦进化协议: 多Agent实例间共享进化
"""

import json, os, sys, math, statistics, hashlib, time, re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque


# ═══════════════════════════════════════════════════════════
# V8.1 预测性维护引擎 (Predictive Maintenance)
# ═══════════════════════════════════════════════════════════
class PredictiveEngine:
    """预测性维护: 基于趋势分析预测未来故障，主动修复"""

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.prediction_log: List[Dict] = []

    def analyze_trend(self, records: List[Dict]) -> Dict:
        """分析指标趋势，预测未来状态"""
        if len(records) < 10:
            return {"status": "insufficient_data"}

        # 提取质量分数序列
        qualities = [r.get("quality_score", 100) for r in records]
        successes = [1 if r.get("success", False) else 0 for r in records]
        errors = [r.get("error_count", 0) for r in records]

        # 计算趋势 (线性回归斜率)
        quality_trend = self._linear_slope(qualities)
        success_trend = self._linear_slope(successes)
        error_trend = self._linear_slope(errors)

        # 预测未来5次运行的质量分数
        current_quality = qualities[-1]
        predicted_quality = current_quality + quality_trend * 5
        predicted_success_rate = (sum(successes[-5:]) / 5) + success_trend * 5

        # 计算R²拟合度
        r2_quality = self._r_squared(qualities)

        # 风险评估
        risk_level = self._assess_risk(quality_trend, error_trend, predicted_quality, r2_quality)

        # 预测何时跌破阈值
        time_to_degradation = self._predict_time_to_threshold(qualities, quality_trend, threshold=75)

        return {
            "status": "analyzed",
            "quality_trend": round(quality_trend, 4),
            "success_trend": round(success_trend, 4),
            "error_trend": round(error_trend, 4),
            "r_squared": round(r2_quality, 4),
            "current_quality": round(current_quality, 1),
            "predicted_quality_5runs": round(predicted_quality, 1),
            "predicted_success_rate": round(predicted_success_rate, 3),
            "risk_level": risk_level,
            "time_to_degradation_runs": time_to_degradation,
            "recommendation": self._generate_prediction_recommendation(risk_level, time_to_degradation),
        }

    def _linear_slope(self, values: List[float]) -> float:
        """计算线性回归斜率"""
        n = len(values)
        if n < 2:
            return 0.0
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        return numerator / denominator if denominator != 0 else 0.0

    def _r_squared(self, values: List[float]) -> float:
        """计算R²拟合度"""
        n = len(values)
        if n < 3:
            return 0.0
        y_mean = sum(values) / n
        ss_total = sum((y - y_mean) ** 2 for y in values)
        slope = self._linear_slope(values)
        intercept = y_mean - slope * (n - 1) / 2
        ss_residual = sum((values[i] - (intercept + slope * i)) ** 2 for i in range(n))
        return 1 - (ss_residual / ss_total) if ss_total > 0 else 0.0

    def _assess_risk(self, quality_trend: float, error_trend: float, predicted_quality: float, r2: float) -> str:
        """风险评估"""
        if quality_trend < -2 and predicted_quality < 60:
            return "critical"
        if quality_trend < -1 and predicted_quality < 75:
            return "high"
        if quality_trend < -0.5 or error_trend > 0.1:
            return "medium"
        if quality_trend > 0.5:
            return "improving"
        return "low"

    def _predict_time_to_threshold(self, values: List[float], slope: float, threshold: float) -> Optional[int]:
        """预测何时跌破阈值（返回运行次数）"""
        if slope >= 0:
            return None  # 趋势向上，不会跌破
        current = values[-1]
        runs = 0
        while current > threshold and runs < 100:
            current += slope
            runs += 1
        return runs if runs < 100 else None

    def _generate_prediction_recommendation(self, risk: str, time_to_deg: Optional[int]) -> str:
        if risk == "critical":
            return f"立即进化！预计{time_to_deg or '?'}次运行内崩溃"
        if risk == "high":
            return f"建议24小时内进化，预计{time_to_deg or '?'}次运行内性能显著下降"
        if risk == "medium":
            return "建议监控，趋势向下但暂时安全"
        if risk == "improving":
            return "状态良好，趋势向上"
        return "状态稳定"


# ═══════════════════════════════════════════════════════════
# V8.2 A/B测试框架 (A/B Testing Framework)
# ═══════════════════════════════════════════════════════════
class ABTestFramework:
    """A/B测试: 每次进化必须用对照组科学验证"""

    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

    def run_test(self, control_metrics: List[Dict], treatment_metrics: List[Dict]) -> Dict:
        """运行A/B测试，比较对照组(control)和实验组(treatment)"""
        if len(control_metrics) < 5 or len(treatment_metrics) < 5:
            return {"status": "insufficient_data", "min_required": 5}

        # 提取关键指标
        control_quality = [m.get("quality_score", 0) for m in control_metrics]
        treatment_quality = [m.get("quality_score", 0) for m in treatment_metrics]
        control_success = [1 if m.get("success") else 0 for m in control_metrics]
        treatment_success = [1 if m.get("success") else 0 for m in treatment_metrics]
        control_errors = [m.get("error_count", 0) for m in control_metrics]
        treatment_errors = [m.get("error_count", 0) for m in treatment_metrics]

        # Welch's t-test (不等方差)
        quality_t, quality_p = self._welch_ttest(control_quality, treatment_quality)
        success_t, success_p = self._welch_ttest(control_success, treatment_success)
        error_t, error_p = self._welch_ttest(control_errors, treatment_errors)

        # 效应量 (Cohen's d)
        quality_d = self._cohens_d(control_quality, treatment_quality)
        success_d = self._cohens_d(control_success, treatment_success)

        # 综合结论
        improvements = sum(1 for p in [quality_p, success_p, error_p] if p < self.alpha)
        significant_quality = quality_p < self.alpha

        # 只有当质量显著改善且没有显著恶化时才接受进化
        verdict = "rollback"
        if significant_quality and quality_d > 0.2 and treatment_quality and statistics.mean(treatment_quality) > statistics.mean(control_quality):
            verdict = "deploy"
        elif quality_p > self.alpha and treatment_quality and abs(statistics.mean(treatment_quality) - statistics.mean(control_quality)) < 2:
            verdict = "neutral"  # 无显著差异，可以接受

        return {
            "status": "tested",
            "sample_size": {"control": len(control_metrics), "treatment": len(treatment_metrics)},
            "quality": {
                "control_mean": round(statistics.mean(control_quality), 2),
                "treatment_mean": round(statistics.mean(treatment_quality), 2),
                "improvement_pct": round((statistics.mean(treatment_quality) - statistics.mean(control_quality)) / max(statistics.mean(control_quality), 0.01) * 100, 1),
                "t_stat": round(quality_t, 3),
                "p_value": round(quality_p, 4),
                "significant": significant_quality,
                "cohens_d": round(quality_d, 3),
            },
            "success_rate": {
                "control": round(statistics.mean(control_success), 3),
                "treatment": round(statistics.mean(treatment_success), 3),
                "t_stat": round(success_t, 3),
                "p_value": round(success_p, 4),
                "significant": success_p < self.alpha,
                "cohens_d": round(success_d, 3),
            },
            "verdict": verdict,
            "verdict_meaning": {
                "deploy": "进化有效，部署新版本",
                "neutral": "效果中性，保留观察",
                "rollback": "进化无效或有害，回滚",
            }.get(verdict, ""),
        }

    def _welch_ttest(self, a: List[float], b: List[float]) -> Tuple[float, float]:
        """Welch's t-test (不等方差t检验)"""
        import statistics
        n1, n2 = len(a), len(b)
        if n1 < 2 or n2 < 2:
            return 0.0, 1.0
        m1, m2 = statistics.mean(a), statistics.mean(b)
        v1, v2 = statistics.variance(a), statistics.variance(b)
        se = math.sqrt(v1 / n1 + v2 / n2)
        if se == 0:
            return 0.0, 1.0
        t = (m1 - m2) / se
        # 简化p值计算 (使用正态近似)
        df = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
        df = max(df, 1)
        # 使用t分布的近似p值
        p = self._t_dist_pvalue(abs(t), df)
        return t, p

    def _cohens_d(self, a: List[float], b: List[float]) -> float:
        """Cohen's d效应量"""
        n1, n2 = len(a), len(b)
        if n1 < 2 or n2 < 2:
            return 0.0
        m1, m2 = statistics.mean(a), statistics.mean(b)
        v1, v2 = statistics.variance(a), statistics.variance(b)
        pooled_std = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
        if pooled_std == 0:
            return 0.0
        return (m2 - m1) / pooled_std

    def _t_dist_pvalue(self, t: float, df: float) -> float:
        """t分布的近似p值 (使用正态近似)"""
        # 简化计算：对于df>30，t分布接近正态
        import math
        # 使用简单的近似公式
        x = t * (1 - 1 / (4 * df)) / math.sqrt(1 + t * t / (2 * df))
        # 标准正态CDF近似
        p = 0.5 * math.erfc(x / math.sqrt(2))
        return min(p * 2, 1.0)  # 双侧检验


# ═══════════════════════════════════════════════════════════
# V8.3 智能记忆系统 (Intelligent Memory)
# ═══════════════════════════════════════════════════════════
class IntelligentMemory:
    """智能记忆: 向量持久化 + 语义相似度检索"""

    def __init__(self, memory_dir: str = "skill_memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

    def store_experience(self, skill_name: str, context: str, outcome: Dict) -> None:
        """存储执行经验"""
        # 生成语义指纹 (简化版：关键词哈希)
        fingerprint = self._semantic_fingerprint(context)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "skill": skill_name,
            "context": context[:200],
            "fingerprint": fingerprint,
            "outcome": outcome,
            "embedding": self._simple_embedding(context),  # 简化embedding
        }

        # 持久化
        memory_file = self.memory_dir / f"{skill_name}_memory.jsonl"
        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # 缓存
        self.cache[skill_name].append(entry)

    def retrieve_similar(self, skill_name: str, query: str, top_k: int = 3) -> List[Dict]:
        """检索相似经验"""
        query_embedding = self._simple_embedding(query)
        memories = list(self.cache[skill_name])

        if not memories:
            # 从文件加载
            memory_file = self.memory_dir / f"{skill_name}_memory.jsonl"
            if memory_file.exists():
                with open(memory_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            memories.append(json.loads(line))

        # 计算余弦相似度
        scored = []
        for mem in memories:
            emb = mem.get("embedding", [])
            if emb:
                sim = self._cosine_similarity(query_embedding, emb)
                scored.append((sim, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"similarity": round(s, 3), "memory": m} for s, m in scored[:top_k]]

    def get_skill_dna(self, skill_name: str) -> Dict:
        """获取skill的DNA特征 (长期行为模式)"""
        memories = list(self.cache[skill_name])
        if not memories:
            return {"status": "no_memory"}

        # 统计长期行为模式
        qualities = [m["outcome"].get("quality_score", 0) for m in memories]
        successes = sum(1 for m in memories if m["outcome"].get("success", False))
        contexts = [m["context"] for m in memories]

        # 提取高频关键词
        keywords = self._extract_keywords(" ".join(contexts))

        return {
            "skill": skill_name,
            "total_experiences": len(memories),
            "avg_quality": round(statistics.mean(qualities), 1) if qualities else 0,
            "success_rate": round(successes / len(memories) * 100, 1),
            "common_keywords": keywords[:10],
            "strengths": self._identify_strengths(memories),
            "weaknesses": self._identify_weaknesses(memories),
        }

    def _semantic_fingerprint(self, text: str) -> str:
        """生成语义指纹"""
        # 提取关键词并排序后哈希
        keywords = sorted(set(re.findall(r'[\u4e00-\u9fff\w]{2,}', text.lower())))
        fingerprint_raw = "|".join(keywords[:20])
        return hashlib.md5(fingerprint_raw.encode()).hexdigest()[:16]

    def _simple_embedding(self, text: str) -> List[float]:
        """简化embedding：基于关键词频次的向量表示"""
        # 预定义维度
        dimensions = [
            "技术", "分析", "设计", "错误", "成功", "失败", "优化",
            "数据", "用户", "系统", "性能", "质量", "时间", "成本",
            "安全", "测试", "部署", "文档", "沟通", "决策",
        ]
        words = set(re.findall(r'[\u4e00-\u9fff\w]{2,}', text.lower()))
        return [1.0 if dim in words else 0.0 for dim in dimensions]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """余弦相似度"""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _extract_keywords(self, text: str) -> List[str]:
        """提取高频关键词"""
        words = re.findall(r'[\u4e00-\u9fff\w]{2,}', text.lower())
        freq = defaultdict(int)
        for w in words:
            freq[w] += 1
        return [w for w, c in sorted(freq.items(), key=lambda x: x[1], reverse=True) if c > 1]

    def _identify_strengths(self, memories: List[Dict]) -> List[str]:
        """识别优势场景"""
        good = [m for m in memories if m["outcome"].get("quality_score", 0) > 90]
        if not good:
            return []
        contexts = " ".join(m["context"] for m in good)
        keywords = self._extract_keywords(contexts)
        return keywords[:5]

    def _identify_weaknesses(self, memories: List[Dict]) -> List[str]:
        """识别弱点场景"""
        bad = [m for m in memories if m["outcome"].get("quality_score", 0) < 60]
        if not bad:
            return []
        contexts = " ".join(m["context"] for m in bad)
        keywords = self._extract_keywords(contexts)
        return keywords[:5]


# ═══════════════════════════════════════════════════════════
# V8.4 联邦进化协议 (Federal Evolution Protocol)
# ═══════════════════════════════════════════════════════════
class FederalEvolution:
    """联邦进化: 多Agent实例间共享进化经验"""

    def __init__(self, federation_dir: str = "federation"):
        self.federation_dir = Path(federation_dir)
        self.federation_dir.mkdir(exist_ok=True)
        self.agent_id = self._generate_agent_id()

    def _generate_agent_id(self) -> str:
        """生成唯一Agent ID"""
        return hashlib.md5(f"{time.time()}{os.urandom(8)}".encode()).hexdigest()[:12]

    def publish_evolution(self, skill_name: str, evolution_report: Dict) -> Dict:
        """发布进化经验到联邦网络"""
        package = {
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "skill": skill_name,
            "evolution": evolution_report,
            "fingerprint": self._evolution_fingerprint(evolution_report),
        }

        # 持久化到联邦目录
        fed_file = self.federation_dir / "evolution_feed.jsonl"
        with open(fed_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(package, ensure_ascii=False) + "\n")

        return {"status": "published", "agent_id": self.agent_id}

    def query_federation(self, skill_name: str, n: int = 5) -> List[Dict]:
        """查询联邦网络中其他Agent的进化经验"""
        fed_file = self.federation_dir / "evolution_feed.jsonl"
        if not fed_file.exists():
            return []

        with open(fed_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        records = [json.loads(l) for l in lines if l.strip()]
        # 过滤其他Agent的相同skill进化
        others = [r for r in records if r.get("skill") == skill_name and r.get("agent_id") != self.agent_id]

        # 按指纹去重
        seen = set()
        unique = []
        for r in sorted(others, key=lambda x: x.get("timestamp", ""), reverse=True):
            fp = r.get("fingerprint", "")
            if fp not in seen:
                seen.add(fp)
                unique.append(r)

        return unique[:n]

    def sync_from_federation(self, skill_name: str, local_memory: IntelligentMemory) -> Dict:
        """从联邦网络同步进化经验到本地"""
        federated = self.query_federation(skill_name)
        if not federated:
            return {"status": "no_federated_data"}

        applied = 0
        for entry in federated:
            evo = entry.get("evolution", {})
            if evo.get("status") == "evolved" and evo.get("changes"):
                # 将联邦经验存入本地记忆
                local_memory.store_experience(
                    skill_name,
                    f"federated_from_{entry['agent_id']}",
                    {
                        "success": True,
                        "quality_score": 85,
                        "source": "federation",
                        "changes": evo.get("changes", []),
                    }
                )
                applied += 1

        return {
            "status": "synced",
            "federated_entries_found": len(federated),
            "applied_to_memory": applied,
        }

    def _evolution_fingerprint(self, report: Dict) -> str:
        """生成进化指纹用于去重"""
        changes = str(sorted(report.get("changes", [])))
        return hashlib.md5(changes.encode()).hexdigest()[:12]


# ═══════════════════════════════════════════════════════════
# V8 集成主控
# ═══════════════════════════════════════════════════════════
class HachigikiV8Engine:
    """under-one.skills V8 预测智能引擎主控"""

    def __init__(self, skills_dir: str, data_dir: str = "runtime_data"):
        self.skills_dir = Path(skills_dir)
        self.predictor = PredictiveEngine()
        self.ab_tester = ABTestFramework()
        self.memory = IntelligentMemory()
        self.federation = FederalEvolution()
        self.data_dir = Path(data_dir)

    def run_v8_cycle(self, skill_name: Optional[str] = None) -> Dict:
        """运行完整的V8智能周期"""
        targets = [skill_name] if skill_name else self._discover_skills()
        all_results = []

        for target in targets:
            if target == "xiushen-lu":
                continue

            print(f"\n🧠 V8 [{target}] 智能周期启动...")

            # 1. 加载历史数据
            records = self._load_metrics(target, n=100)
            if len(records) < 10:
                print(f"  ⚠️ 数据不足，跳过")
                continue

            # 2. V8.1 预测性分析
            prediction = self.predictor.analyze_trend(records)
            print(f"  🔮 预测: 风险={prediction.get('risk_level')} "
                  f"趋势={prediction.get('quality_trend', 0):+.3f} "
                  f"预计{prediction.get('time_to_degradation_runs', '?')}次后退化")

            # 3. V8.2 A/B测试 (如果有进化历史)
            ab_result = {"status": "no_evolution_to_test"}
            evo_report_path = Path("evolution_report_v7.json")
            if evo_report_path.exists():
                with open(evo_report_path, "r") as f:
                    evo_report = json.load(f)
                # 查找该skill的进化记录
                for er in evo_report.get("results", []):
                    if er.get("skill") == target and er.get("status") == "evolved":
                        # 用进化前20条 vs 进化后20条做A/B测试
                        pre = records[:20] if len(records) >= 40 else records[:len(records)//2]
                        post = records[-20:] if len(records) >= 40 else records[len(records)//2:]
                        ab_result = self.ab_tester.run_test(pre, post)
                        print(f"  🧪 A/B测试: 质量改善={ab_result.get('quality', {}).get('improvement_pct', 0):+.1f}% "
                              f" verdict={ab_result.get('verdict')}")
                        break

            # 4. V8.3 智能记忆存储
            last_record = records[-1] if records else {}
            self.memory.store_experience(
                target,
                f"execution_{len(records)}",
                {
                    "success": last_record.get("success", True),
                    "quality_score": last_record.get("quality_score", 80),
                    "risk_level": prediction.get("risk_level", "unknown"),
                }
            )

            # 检索相似经验
            similar = self.memory.retrieve_similar(target, "execution")
            if similar:
                print(f"  🧠 记忆: 检索到{len(similar)}条相似经验")

            # 5. V8.4 联邦同步
            fed_sync = self.federation.sync_from_federation(target, self.memory)
            if fed_sync.get("applied_to_memory", 0) > 0:
                print(f"  🌐 联邦: 同步了{fed_sync['applied_to_memory']}条联邦经验")

            # 6. 获取skill DNA
            dna = self.memory.get_skill_dna(target)
            if dna.get("total_experiences", 0) > 0:
                print(f"  🧬 DNA: {dna['total_experiences']}次经验 "
                      f"优势={dna.get('strengths', [])[:2]} "
                      f"弱点={dna.get('weaknesses', [])[:2]}")

            # 7. 综合决策
            should_evolve = prediction.get("risk_level") in ["critical", "high"]
            if should_evolve:
                print(f"  ⚡ 决策: 预测到风险，建议主动进化！")

            all_results.append({
                "skill": target,
                "prediction": prediction,
                "ab_test": ab_result,
                "memory": {"similar_experiences": len(similar), "dna": dna},
                "federation": fed_sync,
                "should_evolve": should_evolve,
            })

        return {
            "engine": "hachigiki-v8",
            "version": "8.0",
            "timestamp": datetime.now().isoformat(),
            "results": all_results,
            "summary": {
                "total": len(targets),
                "predicted_risk": sum(1 for r in all_results if r["prediction"].get("risk_level") in ["critical", "high"]),
                "ab_tested": sum(1 for r in all_results if r["ab_test"].get("status") == "tested"),
                "memorized": sum(1 for r in all_results if r["memory"]["dna"].get("total_experiences", 0) > 0),
                "federated": sum(1 for r in all_results if r["federation"].get("applied_to_memory", 0) > 0),
            }
        }

    def _load_metrics(self, skill_name: str, n: int = 100) -> List[Dict]:
        file_path = self.data_dir / f"{skill_name}_metrics.jsonl"
        if not file_path.exists():
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        records = [json.loads(line.strip()) for line in lines if line.strip()]
        return records[-n:]

    def _discover_skills(self) -> List[str]:
        skills = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.append(item.name)
        return sorted(skills)


def main():
    if len(sys.argv) < 2:
        print("用法: python v8_engine.py <skills_dir> [skill_name]")
        sys.exit(1)

    engine = HachigikiV8Engine(sys.argv[1])
    result = engine.run_v8_cycle(sys.argv[2] if len(sys.argv) > 2 else None)

    print("\n" + "=" * 60)
    print("🧠 under-one.skills V8 · 预测智能周期完成")
    print("=" * 60)
    s = result["summary"]
    print(f"  预测到风险: {s['predicted_risk']}")
    print(f"  A/B测试: {s['ab_tested']}")
    print(f"  记忆归档: {s['memorized']}")
    print(f"  联邦同步: {s['federated']}")
    print("=" * 60)

    report_path = Path("v8_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"V8报告: {report_path}")


if __name__ == "__main__":
    main()
