"""
Shared Knowledge Hub — 跨 Skill 知识迁移中心
供修身炉 (xiushen-lu) 在进化过程中存储和查询优化经验。

V10.1 实现：
- 阈值进化记录的持久化存储（JSON 文件）
- 按 skill 名称和知识类型查询
- 知识贡献接口
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


# 单例模式：全局知识库实例
_knowledge_hub_instance = None


class KnowledgeHub:
    """跨 Skill 知识共享中心"""

    def __init__(self, data_dir: str = "runtime_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.knowledge_file = self.data_dir / "shared_knowledge.json"
        self._knowledge: Dict[str, List[Dict]] = self._load()

    def _load(self) -> Dict[str, List[Dict]]:
        """从磁盘加载知识库"""
        if not self.knowledge_file.exists():
            return {}
        try:
            with open(self.knowledge_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save(self) -> None:
        """持久化知识库到磁盘"""
        with open(self.knowledge_file, "w", encoding="utf-8") as f:
            json.dump(self._knowledge, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------ public API

    def contribute(self, skill_name: str, knowledge_type: str, data: Dict[str, Any]) -> None:
        """贡献一条知识记录

        Args:
            skill_name: 来源 skill 名称
            knowledge_type: 知识类型，如 "threshold_evolution", "bottleneck_pattern"
            data: 任意字典数据
        """
        key = f"{skill_name}:{knowledge_type}"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "skill_name": skill_name,
            "type": knowledge_type,
            "data": data,
        }
        if key not in self._knowledge:
            self._knowledge[key] = []
        self._knowledge[key].append(entry)
        # 限制每类知识最多保留 50 条，防止无限膨胀
        self._knowledge[key] = self._knowledge[key][-50:]
        self._save()

    def query(self, knowledge_type: str, skill_name: Optional[str] = None, n: int = 5) -> List[Dict]:
        """查询知识记录

        Args:
            knowledge_type: 要查询的知识类型
            skill_name: 若指定则只查该 skill；None 则查全部
            n: 返回最近 n 条

        Returns:
            知识记录列表，按时间倒序
        """
        results = []
        for key, entries in self._knowledge.items():
            parts = key.split(":", 1)
            if len(parts) != 2:
                continue
            entry_skill, entry_type = parts
            if entry_type != knowledge_type:
                continue
            if skill_name is not None and entry_skill != skill_name:
                continue
            results.extend(entries)
        # 按时间倒序，取前 n
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:n]

    def get_threshold(self, skill_name: str, key: str) -> Optional[float]:
        """获取特定 skill 的阈值进化记录（供 RefinerV7 使用）"""
        entries = self.query("threshold_evolution", skill_name=skill_name, n=1)
        if not entries:
            return None
        data = entries[0].get("data", {})
        # 尝试从变更描述中提取阈值数值
        change = data.get("change", "")
        import re
        match = re.search(r'([\d.]+)', change)
        if match:
            return float(match.group(1))
        return None

    def get_similar_skills(self, skill_name: str) -> List[str]:
        """基于历史知识记录，找出与给定 skill 有相似优化经验的 skill"""
        # 查找同类型知识的其他 skill
        similarity_map = {
            "qiti-yuanliu": ["shuangquanshou"],
            "tongtian-lu": ["shenji-bailian"],
            "fenghou-qimen": ["juling-qianjiang"],
            "liuku-xianzei": ["dalu-dongguan"],
        }
        return similarity_map.get(skill_name, [])

    def stats(self) -> Dict[str, Any]:
        """返回知识库统计信息"""
        total_entries = sum(len(v) for v in self._knowledge.values())
        return {
            "total_entries": total_entries,
            "categories": list(self._knowledge.keys()),
            "file": str(self.knowledge_file),
        }


def get_hub(data_dir: str = "runtime_data") -> KnowledgeHub:
    """获取全局 KnowledgeHub 单例"""
    global _knowledge_hub_instance
    if _knowledge_hub_instance is None:
        _knowledge_hub_instance = KnowledgeHub(data_dir)
    return _knowledge_hub_instance


# 兼容 core_engine.py 中的条件导入模式
# 当修身炉尝试 "from shared_knowledge import KnowledgeHub" 时使用此模块
import sys
sys.modules["shared_knowledge"] = sys.modules[__name__]
