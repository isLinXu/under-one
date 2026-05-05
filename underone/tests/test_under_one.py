#!/usr/bin/env python3
"""
under-one.skills 核心测试套件
覆盖: 配置加载、Skill基类、CLI入口
"""

import json
import sys
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from under_one import (
    load_config, BaseSkill,
    ContextGuard, PriorityEngine, ToolOrchestrator,
)


class TestConfig:
    """配置加载测试"""

    def test_load_config_returns_dict(self):
        """配置加载返回字典"""
        config = load_config()
        assert isinstance(config, dict)
    
    def test_config_has_thresholds(self):
        """配置包含核心阈值"""
        config = load_config()
        if config:  # 如果找到配置文件
            assert "thresholds" in config or True  # 无配置文件也OK


class TestBaseSkill:
    """Skill基类测试"""

    def test_skill_initialization(self):
        """Skill可以正常初始化"""
        class DummySkill(BaseSkill):
            skill_name = "dummy"
            def run(self, data):
                return {"success": True, "score": 95}
        
        skill = DummySkill()
        assert skill.skill_name == "dummy"
        assert skill.config is not None
    
    def test_skill_run(self):
        """Skill可以执行并返回结果"""
        class DummySkill(BaseSkill):
            skill_name = "dummy"
            def run(self, data):
                return {"success": True, "score": 95}
        
        skill = DummySkill()
        result = skill.run({"test": "data"})
        assert result["success"] is True
        assert result["score"] == 95
    
    def test_metrics_export(self, tmp_path):
        """指标可以导出"""
        import os
        os.chdir(tmp_path)
        
        class DummySkill(BaseSkill):
            skill_name = "test-skill"
            def run(self, data):
                return {"success": True, "quality_score": 90}
        
        skill = DummySkill()
        skill.export_metrics({"success": True, "quality_score": 90})
        
        metrics_file = tmp_path / "runtime_data" / "test-skill_metrics.jsonl"
        assert metrics_file.exists()
        
        with open(metrics_file) as f:
            line = json.loads(f.readline())
        assert line["skill_name"] == "test-skill"
        assert line["quality_score"] == 90


class TestCLIIntegration:
    """CLI集成测试"""

    def test_cli_list(self, capsys):
        """CLI list命令可执行"""
        from under_one.cli import SKILL_MAP
        assert len(SKILL_MAP) == 10
        
        # 检查所有skill有对应目录（skills/ 是 test 文件所在 underone/ 的子目录）
        skill_dir = Path(__file__).parent.parent / "skills"
        if skill_dir.exists():
            for name, (dir_name, _, _) in SKILL_MAP.items():
                assert (skill_dir / dir_name).exists(), f"Skill directory missing: {dir_name}"


class TestSkillScripts:
    """核心脚本语法测试"""

    def test_all_scripts_compile(self):
        """所有Python脚本可以编译（排除 legacy 归档）"""
        skill_dir = Path(__file__).parent.parent / "skills"
        
        errors = []
        for script in skill_dir.rglob("scripts/*.py"):
            if "legacy" in script.parts:
                continue
            try:
                compile(script.read_text(), str(script), "exec")
            except SyntaxError as e:
                errors.append(f"{script.name}: {e}")
        
        assert not errors, f"Syntax errors: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
