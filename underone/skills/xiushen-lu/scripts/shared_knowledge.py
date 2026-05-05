#!/usr/bin/env python3
"""
器名: 跨技能知识共享库 (Cross-Skill Knowledge Hub)
用途: 让skill之间共享进化经验、关键词库、优化策略
输入: skill_name, knowledge_type, data
输出: 共享知识文件

V7特性: 一个skill发现的新关键词/阈值/策略，可被其他skill借鉴
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

SHARED_DIR = Path("shared_knowledge")
SHARED_DIR.mkdir(exist_ok=True)


class KnowledgeHub:
    """跨技能知识共享中心"""

    SHARED_KEYWORDS = {
        "contradiction": ["不对", "错了", "矛盾", "之前说", "改回", "重新", "改主意", "变卦"],
        "creation": ["写", "生成", "创建", "改写", "润色", "翻译", "生成", "撰写", "起草"],
        "high_risk": ["删除", "覆盖", "资金", "医疗", "法律", "生产环境", "销毁", "清空"],
        "evidence": ["数据", "统计", "研究表明", "实验", "测试", "结果", "证据", "证明"],
        "logic_markers": ["因为", "所以", "首先", "然后", "最后", "结论", "因此", "综上"],
    }

    SHARED_THRESHOLDS = {
        "default": {
            "success_rate_warning": 0.80,
            "success_rate_critical": 0.65,
            "human_intervention_warning": 0.10,
            "degradation_consecutive": 4,
        },
        "qiti-yuanliu": {
            "entropy_warning": 3.0,
            "entropy_critical": 7.0,
            "consistency_threshold": 90,
        },
        "tongtian-lu": {
            "curse_high": ["删除", "覆盖", "资金", "医疗", "法律", "生产环境", "销毁"],
            "curse_medium": ["发布", "发送", "配置", "权限", "变更"],
        },
        "fenghou-qimen": {
            "gate_open": 4.5,
            "gate_life": 4.0,
            "gate_view": 3.2,
            "gate_block": 2.5,
        },
        "liuku-xianzei": {
            "core_claim_weight": 40,
            "evidence_weight": 30,
            "application_weight": 30,
        },
    }

    @classmethod
    def contribute(cls, skill_name: str, knowledge_type: str, data: Any) -> None:
        """skill贡献新知识"""
        file_path = SHARED_DIR / f"{knowledge_type}.jsonl"
        entry = {
            "skill": skill_name,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    @classmethod
    def query(cls, knowledge_type: str, skill_filter: str = None, n: int = 10) -> List[Dict]:
        """查询共享知识"""
        file_path = SHARED_DIR / f"{knowledge_type}.jsonl"
        if not file_path.exists():
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        records = [json.loads(l) for l in lines if l.strip()]
        if skill_filter:
            records = [r for r in records if r["skill"] == skill_filter]
        return records[-n:]

    @classmethod
    def get_keywords(cls, category: str) -> List[str]:
        """获取共享关键词"""
        return cls.SHARED_KEYWORDS.get(category, [])

    @classmethod
    def get_threshold(cls, skill_name: str, key: str) -> Any:
        """获取共享阈值配置"""
        defaults = cls.SHARED_THRESHOLDS.get("default", {})
        skill_specific = cls.SHARED_THRESHOLDS.get(skill_name, {})
        return skill_specific.get(key, defaults.get(key))

    @classmethod
    def migrate_threshold(cls, from_skill: str, to_skill: str, threshold_key: str) -> Any:
        """跨skill阈值迁移：将A技能验证有效的阈值迁移到B技能"""
        value = cls.SHARED_THRESHOLDS.get(from_skill, {}).get(threshold_key)
        if value is not None:
            cls.SHARED_THRESHOLDS.setdefault(to_skill, {})[threshold_key] = value
            cls.contribute("xiushen-lu", "threshold_migration", {
                "from": from_skill,
                "to": to_skill,
                "key": threshold_key,
                "value": value,
            })
        return value


if __name__ == "__main__":
    KnowledgeHub.contribute("qiti-yuanliu", "new_pattern", {"keyword": "改主意", "type": "contradiction"})
    print("Knowledge shared:", KnowledgeHub.query("new_pattern"))
    print("Keywords:", KnowledgeHub.get_keywords("contradiction"))
