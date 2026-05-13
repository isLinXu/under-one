#!/usr/bin/env python3
"""
器名: 关联检测器 (Link Detector) V5.3
用途: 从多段文本中检测5类关联关系，输出知识图谱与Mermaid可视化
输入: JSON [{"source": "段落名", "content": "文本"}]
输出: JSON {links, entity_map, knowledge_graph, mermaid_code, temporal_chain, causal_chain, anomaly_signals, hidden_insights, hallucination_risk}
V5.3升级:
- 新增异常信号、隐藏洞察与幻觉风险评分，更适合Agent做核验与追问
V5.2升级:
- 全部阈值/权重/关键词从 under-one.yaml 配置加载
V5.1升级:
- 实体提取升级为基于后缀/前缀模式匹配
- 时序关联增强：完整时间链条检测+方向性推理
- 因果关联增强：因果标记分类+跨段落推理
- 新增来源一致性检测
- Mermaid丰富：实体节点与段落节点分离，多关系样式
"""

import json
import sys
import re
from pathlib import Path
from collections import defaultdict

SKILLS_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SKILLS_ROOT))
try:
    from metrics_collector import record_metrics
except ImportError:
    def record_metrics(*args, **kwargs):
        def decorator(f): return f
        return decorator

try:
    from _skill_config import get_skill_config
except ImportError:
    def get_skill_config(skill_name, key=None, default=None):
        return default


class LinkDetector:
    RELATION_TYPES = ["语义关联", "实体共现", "时序关联", "来源一致", "因果关系"]
    CONFIDENCE_WEIGHTS = {
        "semantic": 0.30,
        "cooccurrence": 0.25,
        "temporal": 0.20,
        "source_consistency": 0.15,
        "causal": 0.10,
    }

    # V5.1: 常见虚词/连词/助词，不应出现在实体中
    INVALID_WORDS = set("和 与 及 或 的 了 着 过 得 地 之 其 此 彼 所 被 把 让 给 向 从 到 对 将 就 又 也 还 而 但 却 并 且 若 即 则 乃 虽 在 是 有 为 以 于".split())

    FILTER_VERBS = set(
        "是 有 在 为 以 于 与 被 把 让 给 向 从 到 对 将 就 又 也 还 而 但 却 并 且 若 即 则 乃 虽 固然 虽然 尽管 即使 即便 纵然 哪怕 只要 只有 无论 不管 不论 "
        "因为 由于 鉴于 基于 既然 因此 所以 于是 从而 因而 故而 就此 据此 然后 接着 随后 之后 此后 继而 接下来 首先 最后 最初 最终 结果 如果 要是 假如 假设 假若 倘若 若是 除非 除了 除开 除去 "
        "有关 关于 对于 按照 依照 根据 依据 遵照 遵循 本着 随着 趁着 乘势 当着 沿着 顺着 向着 朝着 对着 冲着 照着 按着 由 自从 自打 打从 当 趁 乘 往 朝 至 达 替 为了 为着 "
        "通过 经过 经由 用 拿 靠 凭 依 据 按 照 将 叫 使 令 派 劝 催 逼 求 托 请 邀请 号召 要 要求 请求 乞求 祈求 恳求 央求 哀求 诉求 "
        "降低 优化 表明 反馈 显示 需要 关注 支持 缓解 验证 部署 使用 解决 提高 减少 增加 变化 发展 保持 维护 管理 控制 处理 操作 运行 启动 停止 关闭 打开 建立 创建 删除 修改 更新 替换 插入 提取 转换 翻译 计算 统计 评估 判断 决定 选择 比较 区分 识别 发现 探索 研究 调查 检查 审查 审核 检验 检测 测量 监控 观察 记录 描述 解释 说明 指出 强调 总结 归纳 概括 分析 讨论 探讨 交流 沟通 协商 协调 合作 配合 帮助 协助 辅助 指导 教导 培训 学习 掌握 了解 认识 理解 明白 知道 记得 忘记 想起 想象 思考 考虑 计划 安排 组织 准备 预防 避免 防止 阻止 阻碍 促进 推动 推进 加速 减慢 延迟 提前 延长 缩短 扩大 缩小 增强 减弱 改善 恶化 恢复 保持 维持 稳定 平衡 调整 调节 适应 适合 符合 满足 达到 完成 实现 成功 失败 胜利 战胜 克服 突破 创新 改革 变革 转变 改变 变化 发展 进步 提高 提升 升级 降级 排名 排序 排列 分类 归类 分组 整合 合并 拆分 分离 隔离 保护 保障 确保 保证 担保 负责 承担 承受 忍受 接受 拒绝 否认 承认 确认 肯定 否定 怀疑 相信 信任 依赖 依靠 指望 期待 期望 希望 愿望 要求 需求 请求 申请 提议 建议 意见 看法 观点 态度 立场 主张 坚持 支持 反对 赞成 批判 批评 评价 评论 议论 争论 辩论 辩护 维护 保护 保卫 守护 监督 监管 管理 治理 统治 领导 带领 引导 指导 指挥 控制 操纵 操作 执行 实施 实行 实践 实现 完成 结束 终止 停止 中断 继续 持续 维持 坚持 保留 保存 存储 积累 聚集 集中 分散 分布 传播 传送 传递 传输 转移 移动 运动 活动 行动 行为 动作 作为 表现 表达 表示 表现 体现 反映 反应 响应 回答 答复 回复 反馈 回应 回报 报答 报复 打击 攻击 进攻 防守 防御 保护 救助 救援 拯救 抢救 治疗 治愈 修复 修理 整理 整顿 治理 清理 清除 消除 消灭 销毁 毁灭 破坏 损坏 损害 伤害 杀害 杀死 处决 判决 审判 审判 判定 断定 判断 评估 评价 评论 批评 批判 指责 责备 责怪 埋怨 抱怨 怨恨 仇恨 憎恨 厌恶 讨厌 喜欢 喜爱 爱好 热爱 疼爱 关心 关怀 照顾 照料 看护 保护 爱护 珍惜 珍重 重视 看重 轻视 忽视 忽略 省略 删除 去掉 除去 去除 排除 排斥 拒绝 抵制 抵抗 反抗 反对 反驳 批驳 驳斥 斥责 训斥 教训 教育 培养 培育 训练 锻炼 磨练 考验 检验 测验 测试 考试 考核 考察 考查 检查 检验 审查 审核 审计 监督 监管 监视 监控 观察 视察 参观 访问 拜访 探访 探索 探求 寻求 寻找 找寻 追求 追逐 追赶 追踪 跟踪 跟随 追随 随从 服从 听从 顺从 屈服 投降 投降 认输 承认 供认 坦白 交代 交代的"
        .split()
    )
    CN_NOUN_SUFFIXES = [
        "技术", "方案", "系统", "服务", "平台", "引擎", "工具", "框架", "模型", "算法",
        "数据", "信息", "指标", "报告", "分析", "验证", "测试", "优化", "改进", "提升",
        "性能", "加载", "延迟", "速度", "效率", "质量", "体验", "用户", "客户", "产品",
        "功能", "模块", "组件", "接口", "协议", "标准", "规范", "流程", "策略", "决策",
        "问题", "风险", "异常", "错误", "缺陷", "漏洞", "瓶颈", "缺口", "痛点", "难点",
        "趋势", "模式", "规律", "关联", "影响", "结果", "效果", "成果", "产出", "收益",
        "方法", "手段", "途径", "方式", "形式", "结构", "架构", "设计", "实现", "部署",
        "版本", "迭代", "周期", "阶段", "步骤", "环节", "过程", "操作", "动作", "行为",
        "团队", "人员", "角色", "职责", "能力", "技能", "经验", "知识", "资源", "资产",
        "市场", "竞品", "行业", "领域", "场景", "案例", "实例", "样本", "试点", "标杆",
    ]

    # V5.1: 中文前缀模式
    CN_NOUN_PREFIXES = [
        "用户", "系统", "数据", "性能", "代码", "业务", "产品", "技术", "服务", "平台",
        "缓存", "数据库", "服务器", "客户端", "前端", "后端", "接口", "模块", "功能",
        "加载", "渲染", "网络", "存储", "计算", "查询", "索引", "日志", "监控", "告警",
    ]

    # V5.1: 时间标记词
    TEMPORAL_MARKERS = {
        "start": ["首先", "最初", "一开始", "前期", "第一步"],
        "progress": ["然后", "接着", "随后", "之后", "此后", "继而", "接下来", "第二步", "第三步"],
        "end": ["最后", "最终", "终于", "结果", "结尾", "末期", "最后一步"],
        "before": ["之前", "以前", "先前", "事先", "预先"],
        "after": ["之后", "以后", "后来", "随后", "事后"],
    }

    # V5.1: 因果标记词
    CAUSE_MARKERS = ["因为", "由于", "鉴于", "基于", "因", "既然", "考虑到", "源于", "归因于"]
    EFFECT_MARKERS = ["所以", "因此", "导致", "致使", "引起", "造成", "使得", "从而", "结果", "故", "于是", "就此", "据此"]
    CLAIM_MARKERS = ["必须", "一定", "显然", "证明", "毫无疑问", "完全稳定", "不会失败", "唯一"]

    def __init__(self, segments):
        self.segments = segments
        self.links = []
        self.entities = defaultdict(list)
        self.temporal_chain = []
        self.causal_chain = []
        self.anomaly_signals = []
        self.hidden_insights = []
        self.hallucination_risk = {}
        self._entity_confidence = {}
        # V5.2: 从 under-one.yaml 加载配置
        self._load_config()

    def _load_config(self):
        """V5.2: 从配置加载参数，未配置时回退到默认值"""
        cfg = get_skill_config("daludongguan", default={})

        # 关联权重
        weights = cfg.get("confidence_weights", {})
        self.CONFIDENCE_WEIGHTS = {
            "semantic": weights.get("semantic", 0.30),
            "cooccurrence": weights.get("cooccurrence", 0.25),
            "temporal": weights.get("temporal", 0.20),
            "source_consistency": weights.get("source_consistency", 0.15),
            "causal": weights.get("causal", 0.10),
        }

        # 阈值
        th = cfg.get("thresholds", {})
        self.SEMANTIC_SIMILARITY_THRESHOLD = th.get("semantic_similarity", 0.12)
        self.SOURCE_SIMILARITY_THRESHOLD = th.get("source_similarity", 0.15)
        self.LINK_PRUNE_THRESHOLD = th.get("link_prune", 0.3)
        self.ENTITY_MIN_LENGTH = th.get("entity_min_length", 2)
        self.ENTITY_MAX_LENGTH = th.get("entity_max_length", 25)
        self.ENTITY_MAX_COUNT = th.get("entity_max_count", 40)

        # 置信度分级
        levels = cfg.get("confidence_levels", {})
        self.CONFIDENCE_A = levels.get("A", 0.8)
        self.CONFIDENCE_B = levels.get("B", 0.5)

        # 关键词列表（配置可覆盖）
        self.INVALID_WORDS = set(cfg.get("invalid_words", list(self.INVALID_WORDS)))
        self.CN_NOUN_SUFFIXES = cfg.get("noun_suffixes", self.CN_NOUN_SUFFIXES)
        self.CN_NOUN_PREFIXES = cfg.get("noun_prefixes", self.CN_NOUN_PREFIXES)
        self.TEMPORAL_MARKERS = cfg.get("temporal_markers", self.TEMPORAL_MARKERS)
        causal_cfg = cfg.get("causal_markers", {})
        self.CAUSE_MARKERS = causal_cfg.get("cause", self.CAUSE_MARKERS)
        self.EFFECT_MARKERS = causal_cfg.get("effect", self.EFFECT_MARKERS)

    @record_metrics("dalu-dongguan")
    def detect(self):
        self._extract_entities()
        self._semantic_links()
        self._cooccurrence_links()
        self._temporal_links()
        self._causal_links()
        self._source_consistency_links()
        self._prune_weak_links()
        self.anomaly_signals = self._collect_anomaly_signals()
        self.hidden_insights = self._build_hidden_insights()
        self.hallucination_risk = self._build_hallucination_risk()
        return self._build_output()

    # ═══════════════════════════════════════════════════════════
    # V5.1: 基于模式匹配的精准实体提取
    # ═══════════════════════════════════════════════════════════
    def _extract_entities(self):
        for seg in self.segments:
            text = seg.get("content", "")
            source = seg.get("source", "unknown")
            seg_entities = []

            # 1. 引号内内容（高置信度）
            for q in re.findall(r'[""""]([^""""]+)[""""]', text):
                q = q.strip()
                if 2 <= len(q) <= 20:
                    seg_entities.append((q, "quoted", 1.0))

            # 2. 英文专有名词
            for e in re.findall(r'\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*){0,2}\b', text):
                e = e.strip()
                if len(e) >= 2:
                    seg_entities.append((e, "english", 0.85))

            # 3. 数字+单位
            for n in re.findall(r'\d+(?:\.\d+)?\s*[个条项次倍帧秒分小时天月年GBMBKB%]', text):
                seg_entities.append((n.strip(), "num_unit", 0.7))

            # 4. 中文后缀名词（如"缓存技术", "性能优化"）
            for suffix in self.CN_NOUN_SUFFIXES:
                pattern = r'([\u4e00-\u9fff]{1,4})' + re.escape(suffix)
                for m in re.finditer(pattern, text):
                    phrase = m.group(1) + suffix
                    if len(phrase) >= 3:
                        modifier = m.group(1)
                        # V5.1: 修饰语过长（>2字）时检查质量
                        if len(modifier) > 2:
                            mod_verbs = sum(1 for v in self.FILTER_VERBS if v in modifier)
                            if mod_verbs >= 1:
                                continue
                        # V5.1: 修饰语以虚词开头/结尾则跳过
                        if modifier[0] in self.INVALID_WORDS or modifier[-1] in self.INVALID_WORDS:
                            continue
                        seg_entities.append((phrase, "cn_suffix", 0.75))

            # 5. 中文前缀名词（如"用户体验", "系统架构"）
            for prefix in self.CN_NOUN_PREFIXES:
                pattern = re.escape(prefix) + r'([\u4e00-\u9fff]{1,2})'
                for m in re.finditer(pattern, text):
                    phrase = prefix + m.group(1)
                    if len(phrase) >= 3:
                        # V5.1: 过滤包含虚词的phrase
                        suffix_part = m.group(1)
                        if suffix_part[0] in self.INVALID_WORDS or suffix_part[-1] in self.INVALID_WORDS:
                            continue
                        seg_entities.append((phrase, "cn_prefix", 0.7))

            # 6. 技术缩写
            for abbr in re.findall(r'\b[A-Z]{2,5}\b', text):
                seg_entities.append((abbr, "abbr", 0.6))

            # 记录
            for entity, etype, confidence in seg_entities:
                entity = entity.strip()
                if not entity or len(entity) > 25:
                    continue
                self.entities[entity].append(source)
                if entity not in self._entity_confidence or confidence > self._entity_confidence[entity]:
                    self._entity_confidence[entity] = confidence

        self._filter_entities()

    def _filter_entities(self):
        """实体过滤与降噪"""
        scored = []
        for entity, sources in self.entities.items():
            freq = len(set(sources))
            conf = self._entity_confidence.get(entity, 0.5)
            length = len(entity)

            if length < self.ENTITY_MIN_LENGTH or length > self.ENTITY_MAX_LENGTH:
                continue
            if re.match(r'^[\d\s]+$', entity):
                continue
            if freq == 1 and length < 4 and conf < 0.8:
                continue

            # V5.1: 过滤包含动词的实体（引号高置信度除外）
            verb_count = sum(1 for v in self.FILTER_VERBS if v in entity)
            if verb_count >= 1 and conf < 0.85:
                continue

            # V5.1: 过滤以动词开头的实体
            starts_with_verb = False
            for v in self.FILTER_VERBS:
                if len(v) >= 2 and entity.startswith(v):
                    starts_with_verb = True
                    break
            if starts_with_verb and conf < 0.9:
                continue

            score = conf * 0.5 + min(1.0, freq / 3.0) * 0.3 + min(1.0, length / 8.0) * 0.2
            scored.append((entity, sources, score, conf, freq))

        scored.sort(key=lambda x: x[2], reverse=True)
        scored = scored[:self.ENTITY_MAX_COUNT]

        self.entities = defaultdict(list)
        self._entity_confidence = {}
        for entity, sources, _, conf, _ in scored:
            self.entities[entity] = sources
            self._entity_confidence[entity] = conf

    def _semantic_links(self):
        """语义相似度关联"""
        for i, seg_a in enumerate(self.segments):
            for j, seg_b in enumerate(self.segments[i+1:], i+1):
                sim = self._text_similarity(seg_a["content"], seg_b["content"])
                # V5.1: 短文本场景降低阈值，并将strength映射到更高范围避免被剪枝
                if sim > self.SEMANTIC_SIMILARITY_THRESHOLD:
                    mapped_strength = min(0.95, sim * 2.0 + 0.15)
                    self._add_link(seg_a["source"], seg_b["source"], "语义关联", mapped_strength)

    def _cooccurrence_links(self):
        """共现实体关联——同一实体出现在>=2段中"""
        for entity, sources in self.entities.items():
            unique = list(dict.fromkeys(sources))
            if len(unique) >= 2:
                for i in range(len(unique) - 1):
                    self._add_link(unique[i], unique[i+1], "实体共现",
                                   min(0.95, 0.5 + len(unique) * 0.1))
            elif len(sources) >= 2:
                # V5.1: 同一source出现多次也产生弱共现
                self._add_link(unique[0], unique[0], "实体共现", 0.45)

    def _temporal_links(self):
        signals = []
        for i, seg in enumerate(self.segments):
            text = seg.get("content", "")
            source = seg.get("source", "")
            markers_found = []
            for cat, markers in self.TEMPORAL_MARKERS.items():
                for m in markers:
                    if m in text:
                        markers_found.append((cat, m))
            if markers_found:
                prio = {"start": 0, "before": 1, "progress": 2, "after": 3, "end": 4}
                markers_found.sort(key=lambda x: prio.get(x[0], 5))
                signals.append({"index": i, "source": source, "cat": markers_found[0][0]})

        signals.sort(key=lambda x: (x["index"], {"start": 0, "before": 1, "progress": 2, "after": 3, "end": 4}.get(x["cat"], 5)))

        self.temporal_chain = []
        for i in range(len(signals) - 1):
            curr, nxt = signals[i], signals[i + 1]
            strength = 0.6
            if nxt["index"] - curr["index"] == 1:
                strength = 0.8
            if curr["cat"] == "start" and nxt["cat"] == "end":
                strength = 0.9
            self._add_link(curr["source"], nxt["source"], "时序关联", strength)
            self.temporal_chain.append({"from": curr["source"], "to": nxt["source"], "strength": strength})

    def _causal_links(self):
        """V5.1: 因果关联——因果标记分类+跨段落推理"""
        # 标记每个段落的因果属性
        seg_causal = []
        for i, seg in enumerate(self.segments):
            text = seg.get("content", "")
            has_cause = any(m in text for m in self.CAUSE_MARKERS)
            has_effect = any(m in text for m in self.EFFECT_MARKERS)
            seg_causal.append({"index": i, "source": seg["source"], "has_cause": has_cause, "has_effect": has_effect, "text": text})

        self.causal_chain = []
        for i, curr in enumerate(seg_causal):
            if curr["has_effect"]:
                # 优先找前面最近的含"因"标记的段落
                best_prev = None
                best_score = 0
                for prev in reversed(seg_causal[:i]):
                    sim = self._text_similarity(prev["text"], curr["text"])
                    score = sim
                    if prev["has_cause"]:
                        score += 0.3
                    if score > best_score:
                        best_score = score
                        best_prev = prev
                if best_prev and best_score > 0.0:
                    strength = min(0.95, 0.45 + best_score * 0.4)
                    self._add_link(best_prev["source"], curr["source"], "因果关系", strength)
                    self.causal_chain.append({"cause": best_prev["source"], "effect": curr["source"], "strength": round(strength, 2)})

    def _source_consistency_links(self):
        """V5.1: 来源一致性——检测同一来源的多段文本之间的自洽性"""
        source_groups = defaultdict(list)
        for seg in self.segments:
            source_groups[seg.get("source", "unknown")].append(seg)

        for source, segs in source_groups.items():
            if len(segs) >= 2:
                for i in range(len(segs) - 1):
                    sim = self._text_similarity(segs[i]["content"], segs[i+1]["content"])
                    # 同来源用更低阈值
                    if sim > self.SOURCE_SIMILARITY_THRESHOLD:
                        self._add_link(segs[i]["source"], segs[i+1]["source"], "来源一致",
                                       min(0.85, 0.35 + sim * 0.5))

    def _add_link(self, src, dst, rel_type, strength):
        for existing in self.links:
            if existing["source"] == src and existing["target"] == dst and existing["type"] == rel_type:
                existing["strength"] = round(max(existing["strength"], strength), 2)
                return
        self.links.append({
            "source": src, "target": dst, "type": rel_type,
            "strength": round(strength, 2),
            "confidence": "A" if strength > self.CONFIDENCE_A else "B" if strength > self.CONFIDENCE_B else "C",
        })

    def _prune_weak_links(self):
        self.links = [l for l in self.links if l["strength"] > self.LINK_PRUNE_THRESHOLD]

    def _text_similarity(self, a, b):
        def _tokenize(text):
            tokens = set()
            tokens.update(re.findall(r'[a-zA-Z]+', text.lower()))
            cn_chars = re.findall(r'[\u4e00-\u9fff]', text)
            tokens.update(cn_chars)
            for i in range(len(text) - 1):
                if '\u4e00' <= text[i] <= '\u9fff' and '\u4e00' <= text[i+1] <= '\u9fff':
                    tokens.add(text[i:i+2])
            return tokens
        words_a = _tokenize(a)
        words_b = _tokenize(b)
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / len(words_a | words_b)

    def _generate_mermaid(self):
        lines = ["graph TD"]
        # 段落节点
        for seg in self.segments:
            src = seg.get("source", "")
            sid = re.sub(r'[^\w]', '_', src)
            lines.append(f'    {sid}["{src}"]')
        # 实体节点
        for entity in self.entities:
            eid = re.sub(r'[^\w\u4e00-\u9fff]', '_', entity)
            if eid[0].isdigit():
                eid = "E" + eid
            lines.append(f'    {eid}(("{entity}"))')
        # 关系
        style_arrow = {
            "语义关联": "-->", "实体共现": "-.->",
            "时序关联": "==>", "来源一致": "-->", "因果关系": "-->",
        }
        for link in self.links:
            src = re.sub(r'[^\w]', '_', link["source"])
            dst = re.sub(r'[^\w]', '_', link["target"])
            arrow = style_arrow.get(link["type"], "-->")
            label = f"|{link['type']} {link['strength']}|"
            lines.append(f"    {src} {arrow}{label} {dst}")
        # 实体归属
        for entity, sources in self.entities.items():
            eid = re.sub(r'[^\w\u4e00-\u9fff]', '_', entity)
            if eid[0].isdigit():
                eid = "E" + eid
            for src in set(sources):
                sid = re.sub(r'[^\w]', '_', src)
                lines.append(f'    {eid} -.->|出现在| {sid}')
        # 样式
        lines.append('    classDef segment fill:#e6f1fb,stroke:#378add')
        lines.append('    classDef entity fill:#fbeaf0,stroke:#d4537e')
        for seg in self.segments:
            sid = re.sub(r'[^\w]', '_', seg.get("source", ""))
            lines.append(f'    class {sid} segment')
        for entity in self.entities:
            eid = re.sub(r'[^\w\u4e00-\u9fff]', '_', entity)
            if eid[0].isdigit():
                eid = "E" + eid
            lines.append(f'    class {eid} entity')
        return "\n".join(lines)

    def _segment_entity_map(self):
        mapping = defaultdict(set)
        for entity, sources in self.entities.items():
            for source in sources:
                mapping[source].add(entity)
        return {source: sorted(values) for source, values in mapping.items()}

    def _segment_link_stats(self):
        degree = defaultdict(int)
        total_strength = defaultdict(float)
        neighbors = defaultdict(set)
        for link in self.links:
            src = link["source"]
            dst = link["target"]
            weight = float(link.get("strength", 0.0) or 0.0)

            degree[src] += 1
            total_strength[src] += weight
            neighbors[src].add(dst)

            if dst != src:
                degree[dst] += 1
                total_strength[dst] += weight
                neighbors[dst].add(src)

        return degree, total_strength, neighbors

    def _severity_label(self, score):
        if score >= 0.75:
            return "high"
        if score >= 0.5:
            return "medium"
        return "low"

    def _effect_markers_in_text(self, text):
        return [marker for marker in self.EFFECT_MARKERS if marker in text]

    def _claim_markers_in_text(self, text):
        return [marker for marker in self.CLAIM_MARKERS if marker in text]

    def _collect_anomaly_signals(self):
        anomaly_signals = []
        segment_entities = self._segment_entity_map()
        degree_map, _, _ = self._segment_link_stats()
        causal_effect_sources = {item.get("effect") for item in self.causal_chain}

        for seg in self.segments:
            source = seg.get("source", "")
            text = seg.get("content", "")
            entities = segment_entities.get(source, [])
            degree = degree_map.get(source, 0)
            effect_markers = self._effect_markers_in_text(text)
            claim_markers = self._claim_markers_in_text(text)

            if effect_markers and source not in causal_effect_sources:
                score = min(0.95, 0.58 + 0.08 * min(2, len(effect_markers)) + (0.12 if degree == 0 else 0.0))
                anomaly_signals.append(
                    {
                        "type": "effect_without_support",
                        "severity": self._severity_label(score),
                        "score": round(score, 2),
                        "source": source,
                        "reason": "出现结果/结论标记，但未形成稳定因果支撑",
                        "evidence": {
                            "markers": effect_markers[:3],
                            "link_degree": degree,
                            "entities": entities[:4],
                        },
                    }
                )

            if degree == 0 and len(self.segments) > 1 and len(text.strip()) >= 6:
                score = min(0.9, 0.42 + 0.08 * min(4, len(entities)) + (0.1 if claim_markers else 0.0))
                anomaly_signals.append(
                    {
                        "type": "isolated_segment",
                        "severity": self._severity_label(score),
                        "score": round(score, 2),
                        "source": source,
                        "reason": "该段信息未与其他证据形成有效连接",
                        "evidence": {
                            "link_degree": degree,
                            "entity_count": len(entities),
                            "claim_markers": claim_markers[:3],
                        },
                    }
                )

            if len(entities) >= 3 and degree <= 1:
                score = min(0.88, 0.48 + 0.06 * min(4, len(entities) - 2))
                anomaly_signals.append(
                    {
                        "type": "dense_unintegrated_segment",
                        "severity": self._severity_label(score),
                        "score": round(score, 2),
                        "source": source,
                        "reason": "实体较密集，但没有足够图谱支撑，可能存在跳跃推断",
                        "evidence": {
                            "entities": entities[:5],
                            "entity_count": len(entities),
                            "link_degree": degree,
                        },
                    }
                )

            if claim_markers and degree == 0:
                score = min(0.92, 0.62 + 0.08 * min(3, len(claim_markers)))
                anomaly_signals.append(
                    {
                        "type": "unsupported_claim",
                        "severity": self._severity_label(score),
                        "score": round(score, 2),
                        "source": source,
                        "reason": "出现强断言表达，但缺乏交叉验证支撑",
                        "evidence": {
                            "markers": claim_markers[:4],
                            "link_degree": degree,
                        },
                    }
                )

        for entity, sources in self.entities.items():
            unique_sources = list(dict.fromkeys(sources))
            confidence = round(self._entity_confidence.get(entity, 0.5), 2)
            degree = degree_map.get(unique_sources[0], 0) if unique_sources else 0
            if len(unique_sources) == 1 and confidence < 0.75:
                score = min(0.85, 0.4 + (0.75 - confidence) * 0.8 + (0.08 if degree == 0 else 0.0))
                anomaly_signals.append(
                    {
                        "type": "weak_single_source_entity",
                        "severity": self._severity_label(score),
                        "score": round(score, 2),
                        "entity": entity,
                        "source": unique_sources[0] if unique_sources else None,
                        "reason": "实体仅出现于单一片段且置信度偏低，容易带偏整体判断",
                        "evidence": {
                            "source_count": len(unique_sources),
                            "entity_confidence": confidence,
                            "link_degree": degree,
                        },
                    }
                )

        deduped = {}
        for signal in anomaly_signals:
            key = (signal.get("type"), signal.get("source"), signal.get("entity"))
            current = deduped.get(key)
            if current is None or signal.get("score", 0) > current.get("score", 0):
                deduped[key] = signal
        return sorted(deduped.values(), key=lambda item: item.get("score", 0), reverse=True)[:10]

    def _build_hidden_insights(self):
        insights = []
        segment_entities = self._segment_entity_map()
        degree_map, total_strength, neighbors = self._segment_link_stats()

        bridge_candidates = [
            (
                source,
                len(peers),
                degree_map.get(source, 0),
                round(total_strength.get(source, 0.0), 2),
                sorted(peers),
            )
            for source, peers in neighbors.items()
            if len(peers) >= 2
        ]
        bridge_candidates.sort(key=lambda item: (item[1], item[2], item[3]), reverse=True)
        if bridge_candidates:
            source, peer_count, degree, strength, peer_list = bridge_candidates[0]
            confidence = min(0.95, 0.46 + peer_count * 0.08 + min(0.2, strength / 8))
            insights.append(
                {
                    "type": "bridge_segment",
                    "focus": source,
                    "confidence": round(confidence, 2),
                    "summary": f"{source} 是当前图谱的桥接节点，适合作为下一轮追问与验证中心",
                    "support": {
                        "connected_sources": peer_list[:4],
                        "degree": degree,
                        "entity_count": len(segment_entities.get(source, [])),
                    },
                }
            )

        stable_entities = [
            (
                entity,
                sorted(set(sources)),
                round(self._entity_confidence.get(entity, 0.5), 2),
            )
            for entity, sources in self.entities.items()
            if len(set(sources)) >= 2
        ]
        stable_entities.sort(key=lambda item: (len(item[1]), item[2], len(item[0])), reverse=True)
        if stable_entities:
            entity, sources, confidence = stable_entities[0]
            insight_confidence = min(0.95, 0.42 + len(sources) * 0.12 + confidence * 0.2)
            insights.append(
                {
                    "type": "stable_entity",
                    "focus": entity,
                    "confidence": round(insight_confidence, 2),
                    "summary": f"{entity} 跨 {len(sources)} 个片段重复出现，是相对稳固的主线实体",
                    "support": {
                        "sources": sources[:4],
                        "source_count": len(sources),
                        "entity_confidence": confidence,
                    },
                }
            )

        temporal_nodes = {item.get("from") for item in self.temporal_chain} | {item.get("to") for item in self.temporal_chain}
        causal_nodes = {item.get("cause") for item in self.causal_chain} | {item.get("effect") for item in self.causal_chain}
        overlap = sorted(node for node in (temporal_nodes & causal_nodes) if node)
        if overlap:
            focus = overlap[0]
            insights.append(
                {
                    "type": "chain_convergence",
                    "focus": focus,
                    "confidence": 0.74,
                    "summary": f"{focus} 同时位于时序链与因果链中，可能是关键转折节点",
                    "support": {
                        "temporal_chain_size": len(self.temporal_chain),
                        "causal_chain_size": len(self.causal_chain),
                    },
                }
            )

        if self.anomaly_signals:
            top_signal = self.anomaly_signals[0]
            focus = top_signal.get("source") or top_signal.get("entity")
            insights.append(
                {
                    "type": "verification_target",
                    "focus": focus,
                    "confidence": round(top_signal.get("score", 0.0), 2),
                    "summary": f"优先核验 {focus}：{top_signal.get('reason')}",
                    "support": {
                        "anomaly_type": top_signal.get("type"),
                        "severity": top_signal.get("severity"),
                    },
                }
            )

        if not insights and self.segments:
            fallback = self.segments[0].get("source", "段1")
            insights.append(
                {
                    "type": "baseline_observation",
                    "focus": fallback,
                    "confidence": 0.35,
                    "summary": f"{fallback} 暂未暴露显著异常，但仍需要更多交叉证据才能稳固结论",
                    "support": {"segment_count": len(self.segments)},
                }
            )

        insights.sort(key=lambda item: item.get("confidence", 0), reverse=True)
        return insights[:4]

    def _build_hallucination_risk(self):
        if not self.segments:
            return {
                "score": 0.0,
                "level": "low",
                "drivers": [],
                "suspect_sources": [],
                "verification_targets": [],
            }

        anomaly_scores = [item.get("score", 0.0) for item in self.anomaly_signals]
        avg_anomaly = sum(anomaly_scores) / len(anomaly_scores) if anomaly_scores else 0.0
        isolated_count = sum(
            1
            for item in self.anomaly_signals
            if item.get("type") in {"isolated_segment", "effect_without_support", "unsupported_claim", "dense_unintegrated_segment"}
        )
        weak_entity_count = sum(1 for item in self.anomaly_signals if item.get("type") == "weak_single_source_entity")

        segment_ratio = min(1.0, isolated_count / max(1, len(self.segments)))
        entity_ratio = min(1.0, weak_entity_count / max(1, len(self.entities) or 1))
        score = min(1.0, avg_anomaly * 0.55 + segment_ratio * 0.25 + entity_ratio * 0.2)
        level = "low" if score < 0.34 else "medium" if score < 0.67 else "high"

        source_scores = defaultdict(float)
        for item in self.anomaly_signals:
            source = item.get("source")
            if source:
                source_scores[source] = max(source_scores[source], float(item.get("score", 0.0) or 0.0))

        drivers = []
        seen_types = set()
        for item in self.anomaly_signals:
            signal_type = item.get("type")
            if signal_type in seen_types:
                continue
            seen_types.add(signal_type)
            drivers.append(
                {
                    "type": signal_type,
                    "severity": item.get("severity"),
                    "reason": item.get("reason"),
                }
            )
            if len(drivers) >= 3:
                break

        verification_targets = []
        for item in self.anomaly_signals[:3]:
            target = item.get("source") or item.get("entity")
            if target and target not in verification_targets:
                verification_targets.append(target)

        return {
            "score": round(score, 2),
            "level": level,
            "drivers": drivers,
            "suspect_sources": [
                source
                for source, _ in sorted(source_scores.items(), key=lambda item: item[1], reverse=True)[:3]
            ],
            "verification_targets": verification_targets,
            "recommended_action": "先核验高风险节点，再做归纳总结" if level != "low" else "可继续扩充证据后再做综合判断",
        }

    def _build_output(self):
        mermaid = self._generate_mermaid()
        return {
            "detector": "dalu-dongguan", "version": "v0.1.0",
            "segment_count": len(self.segments), "entity_count": len(self.entities),
            "link_count": len(self.links), "links": self.links,
            "entity_map": dict(self.entities),
            "temporal_chain": self.temporal_chain, "causal_chain": self.causal_chain,
            "anomaly_signals": self.anomaly_signals,
            "hidden_insights": self.hidden_insights,
            "hallucination_risk": self.hallucination_risk,
            "quality_score": round(
                max(
                    0.0,
                    min(
                        100.0,
                        76.0
                        + len(self.links) * 2.5
                        + len(self.hidden_insights) * 3.0
                        - self.hallucination_risk.get("score", 0.0) * 28.0
                    ),
                ),
                1,
            ),
            "human_intervention": 1 if self.hallucination_risk.get("level") == "high" else 0,
            "output_completeness": 100.0 if self.segments else 0.0,
            "consistency_score": round(max(0.0, 100.0 - self.hallucination_risk.get("score", 0.0) * 40.0), 1),
            "knowledge_graph": {
                "nodes": [{"id": e, "type": "entity", "frequency": len(set(s))} for e, s in self.entities.items()]
                         + [{"id": seg.get("source", ""), "type": "segment"} for seg in self.segments],
                "edges": [{"source": l["source"], "target": l["target"], "relation": l["type"], "weight": l["strength"]} for l in self.links],
            },
            "mermaid_code": mermaid,
        }


def main():
    if len(sys.argv) < 2:
        print("用法: python link_detector.py <segments.json>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        segments = json.load(f)
    if not isinstance(segments, list):
        print("错误: 输入必须是JSON数组")
        sys.exit(2)
    for i, seg in enumerate(segments):
        if not isinstance(seg, dict) or "content" not in seg:
            print(f"错误: 第{i}项缺少 'content' 字段")
            sys.exit(2)
        if "source" not in seg:
            seg["source"] = f"段{i}"

    detector = LinkDetector(segments)
    result = detector.detect()
    out = Path("link_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 55)
    print("🔭 大罗洞观 · 关联检测报告 V5.3")
    print("=" * 55)
    print(f"  段落数: {result['segment_count']}")
    print(f"  实体数: {result['entity_count']}")
    print(f"  关联数: {result['link_count']}")
    print(f"  时序链: {len(result['temporal_chain'])} 段")
    print(f"  因果链: {len(result['causal_chain'])} 段")
    print(f"  异常信号: {len(result['anomaly_signals'])} 条")
    print(f"  幻觉风险: {result['hallucination_risk']['level']} ({result['hallucination_risk']['score']})")
    print("-" * 55)
    for link in result["links"][:12]:
        emoji = "🔒" if link["confidence"] == "A" else "🔗" if link["confidence"] == "B" else "📎"
        print(f"  {emoji} [{link['confidence']}] {link['source']} --({link['type']})--> {link['target']} |强度:{link['strength']}")
    if len(result["links"]) > 12:
        print(f"  ... 等共 {len(result['links'])} 条关联")
    print("-" * 55)
    print("📊 Mermaid代码已生成")
    print(result["mermaid_code"][:250])
    print("=" * 55)
    print(f"详细报告: {out}")


if __name__ == "__main__":
    main()
