---
metadata:
  name: "shenji-bailian"
  version: "5.0"
  author: "under-one"
  description: "神机百炼 - 工具工厂（代码生成）"
  language: "zh"
  tags: ["code-generation", "tool-factory", "scaffolding", "template"]
  icon: "🔨"
  color: "#ffa657"
---

# 神机百炼 (ShenJi-BaiLian)

## 触发词
- 生成工具
- 代码脚手架
- 工具模板
- 锻造工具
- 生成脚本框架

## 用途
根据需求描述自动生成可执行的Python脚本框架、测试脚本和契约文档。

## 输入
JSON规格说明：
```json
{
  "name": "json_cleaner",
  "description": "清洗JSON数据",
  "inputs": ["raw.json"],
  "outputs": ["clean.json"]
}
```

## 输出
```json
{
  "tool_code": "...",
  "test_code": "...",
  "contract": "...",
  "files": {
    "json_cleaner.py": "...",
    "test_json_cleaner.py": "...",
    "json_cleaner.contract.md": "..."
  }
}
```

## 生成内容
| 文件 | 说明 |
|------|------|
| `{name}.py` | 主工具脚本（含argparse、日志、异常处理） |
| `test_{name}.py` | 测试脚本（正常/空输入/边界） |
| `{name}.contract.md` | 输入/输出/性能/异常契约 |

## 用法
```bash
python scripts/tool_factory.py <spec.json>
```

## 依赖
- Python 3.8+
- 无外部依赖
