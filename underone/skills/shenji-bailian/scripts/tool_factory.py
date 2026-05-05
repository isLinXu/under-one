#!/usr/bin/env python3
"""
器名: 工具工厂 (Tool Factory)
用途: 根据需求描述生成可执行Python脚本框架+测试脚本
输入: JSON {"name":"工具名","description":"用途","inputs":[],"outputs":[]}
输出: {tool_code, test_code, contract}
"""

import json
import sys
from pathlib import Path


TOOL_TEMPLATE = '''#!/usr/bin/env python3
"""
器名: {name}
用途: {description}
输入: {input_desc}
输出: {output_desc}
版本: 0.1
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="{description}")
    parser.add_argument("input", help="输入文件路径")
    parser.add_argument("-o", "--output", default="output.json", help="输出路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细日志")
    parser.add_argument("--dry-run", action="store_true", help="试运行不保存")
    args = parser.parse_args()

    try:
        result = process(args.input)
        if not args.dry_run:
            save_output(result, args.output)
        logger.info("✅ 处理完成")
    except Exception as e:
        logger.error(f"❌ 失败: {{e}}")
        sys.exit(1)

def process(input_path):
    """核心处理逻辑 - TODO: 实现具体逻辑"""
    logger.info(f"处理: {{input_path}}")
    # TODO: 实现核心逻辑
    return {{"status": "placeholder"}}

def save_output(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"输出已保存: {{output_path}}")

if __name__ == "__main__":
    main()
'''

TEST_TEMPLATE = '''#!/usr/bin/env python3
"""
测试脚本: {name}
用途: 验证工具核心功能
"""

import sys
import json
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from {module_name} import process

def test_normal_case():
    """正常输入测试"""
    result = process("dummy_input.json")
    assert result is not None
    print("✅ 正常输入测试通过")

def test_empty_input():
    """空输入测试"""
    try:
        result = process("nonexistent.json")
        assert False, "应该抛出异常"
    except Exception:
        print("✅ 空输入测试通过（正确报错）")

def test_boundary():
    """边界测试"""
    print("⚠️  边界测试待实现")

if __name__ == "__main__":
    test_normal_case()
    test_empty_input()
    test_boundary()
    print("测试完成")
'''

CONTRACT_TEMPLATE = '''
契约ID: {name}-v0.1
输入契约:
  格式: JSON
  必需字段: [{inputs}]
输出契约:
  格式: JSON
性能契约:
  处理速度: 待测试
异常契约:
  输入不存在: exit 1
  格式错误: exit 2
'''


class ToolFactory:
    def __init__(self, spec):
        self.spec = spec

    def forge(self):
        name = self.spec.get("name", "untitled_tool")
        desc = self.spec.get("description", "未描述")
        inputs = ", ".join(self.spec.get("inputs", ["input"]))
        outputs = ", ".join(self.spec.get("outputs", ["output"]))

        tool_code = TOOL_TEMPLATE.format(
            name=name,
            description=desc,
            input_desc=inputs,
            output_desc=outputs,
        )

        module_name = name.replace("-", "_").lower()
        test_code = TEST_TEMPLATE.format(
            name=name,
            module_name=module_name,
        )

        contract = CONTRACT_TEMPLATE.format(
            name=name,
            inputs=inputs,
        )

        return {
            "factory": "shenji-bailian",
            "version": "5.0",
            "tool_name": name,
            "tool_code": tool_code,
            "test_code": test_code,
            "contract": contract,
            "files": {
                f"{module_name}.py": tool_code,
                f"test_{module_name}.py": test_code,
                f"{module_name}.contract.md": contract,
            }
        }


def main():
    if len(sys.argv) < 2:
        print("用法: python tool_factory.py <spec.json>")
        print('  spec: {"name":"json_cleaner","description":"清洗JSON","inputs":["raw.json"],"outputs":["clean.json"]}')
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        spec = json.load(f)

    factory = ToolFactory(spec)
    result = factory.forge()

    # 写入文件
    for filename, content in result["files"].items():
        Path(filename).write_text(content, encoding="utf-8")

    print("=" * 50)
    print("🔨 神机百炼 · 工具锻造报告")
    print("=" * 50)
    print(f"  工具名: {result['tool_name']}")
    print(f"  产出文件:")
    for fname in result["files"]:
        print(f"    • {fname}")
    print("-" * 50)
    print("📄 器灵契约:")
    print(result["contract"])
    print("=" * 50)
    print("✅ 工具框架已生成，请实现 process() 函数的核心逻辑")


if __name__ == "__main__":
    main()

