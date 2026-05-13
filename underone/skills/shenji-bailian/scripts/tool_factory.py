#!/usr/bin/env python3
"""
器名: 工具工厂 (Tool Factory) V6.5
用途: 根据自然语言或结构化规格智能锻造 skill、tool、测试与契约
输入: 自然语言描述 | JSON 规格
输出: {files, forge_summary, inferred_spec}
V6.5升级:
- 支持自然语言直出 tool / skill 规格
- 新增 artifact_type：tool / skill
- 可生成 SKILL.md 与 _skillhub_meta.json
- 专精类型开始影响生成脚本骨架
- 保持 V5.x 结构化 spec 与 tool 输出兼容
"""

import json
import re
import sys
from pathlib import Path

# ── 路径设置 ───────────────────────────────────────────────
SKILL_ROOT = Path(__file__).resolve().parent.parent  # shenji-bailian/
SKILLS_ROOT = SKILL_ROOT.parent                       # skills/
sys.path.insert(0, str(SKILLS_ROOT))

# ── 依赖导入（带降级） ─────────────────────────────────────
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


# ═══════════════════════════════════════════════════════════
# V5.3: 模板从配置加载，支持外部扩展
# ═══════════════════════════════════════════════════════════

def _load_templates():
    """从 under-one.yaml 加载模板定义"""
    cfg = get_skill_config("shenjibailian", default={})
    templates = cfg.get("templates", {})
    generic = cfg.get("generic", {})

    result = {}
    for name, tmpl in templates.items():
        result[name] = {
            "keywords": tmpl.get("keywords", []),
            "transform_code": tmpl.get("transform_code", ""),
            "test_cases": tmpl.get("test_cases", ""),
            "sample_input": tmpl.get("sample_input", '{"key": "value"}'),
        }

    generic_transform = generic.get("transform_code", '')
    generic_test = generic.get("test_cases", '')
    generic_sample = generic.get("sample_input", '{"key": "value"}')

    return result, generic_transform, generic_test, generic_sample


# 加载模板
TEMPLATES, GENERIC_TRANSFORM, GENERIC_TEST, GENERIC_SAMPLE = _load_templates()


# ═══════════════════════════════════════════════════════════
# 代码模板
# ═══════════════════════════════════════════════════════════

TOOL_TEMPLATE = '''#!/usr/bin/env python3
"""
器名: {name}
用途: {description}
输入: {input_desc}
输出: {output_desc}
版本: 0.1
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── 配置加载（V5.3 自动生成） ──────────────────────────────
SKILL_ROOT = Path(__file__).resolve().parent
SKILLS_ROOT = SKILL_ROOT.parent.parent  # skills/
sys.path.insert(0, str(SKILL_ROOT))
sys.path.insert(0, str(SKILLS_ROOT))
try:
    from _skill_config import get_skill_config
except ImportError:
    def get_skill_config(skill_name: str, key: str = None, default=None):
        return default


def main() -> None:
    """CLI入口"""
    parser = argparse.ArgumentParser(description="{description}")
    parser.add_argument("input", help="输入文件路径")
    parser.add_argument("-o", "--output", default="output.json", help="输出路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细日志")
    parser.add_argument("--dry-run", action="store_true", help="试运行不保存")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        result = process(args.input)
        if not args.dry_run:
            save_output(result, args.output)
        logger.info("处理完成")
    except FileNotFoundError as e:
        logger.error(f"失败: {{e}}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {{e}}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"未预期错误: {{e}}")
        sys.exit(1)


def process(input_path: str) -> Dict[str, Any]:
    """核心处理逻辑"""
    logger.info(f"处理: {{input_path}}")
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"输入文件不存在: {{input_path}}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = transform(data)
    return result


__TRANSFORM_CODE__


def save_output(data: Dict[str, Any], output_path: str) -> None:
    """保存输出到JSON文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"输出已保存: {{output_path}}")


if __name__ == "__main__":
    main()
'''


SOURCE_ADAPTER_TEMPLATE = '''#!/usr/bin/env python3
"""Shared source adapter for generated skills."""

import json
import urllib.parse
import urllib.request
from pathlib import Path


def merge_headers(headers=None):
    base = {"Accept": "application/json, text/plain;q=0.9, */*;q=0.8"}
    if isinstance(headers, dict):
        base.update({str(key): str(value) for key, value in headers.items()})
    return base


def fetch_text_from_url(url, timeout=5, headers=None):
    try:
        request = urllib.request.Request(url, headers=merge_headers(headers))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            text = response.read().decode(charset, errors="ignore")
        return text, None
    except Exception as exc:
        return "", {"source": url, "reason": f"fetch_failed:{exc.__class__.__name__}"}


def build_document_record(index, source_type, title, content, tags=None, location="", remote_score=0.0):
    return {
        "id": f"{source_type}-{index+1}",
        "title": title or f"Document {index+1}",
        "content": content or "",
        "tags": tags or [],
        "source_type": source_type,
        "location": location,
        "remote_score": remote_score,
    }


def normalize_inline_documents(raw_documents):
    normalized = []
    for index, item in enumerate(raw_documents):
        if isinstance(item, str):
            normalized.append(build_document_record(index, "inline_document", f"Document {index+1}", item))
        elif isinstance(item, dict):
            normalized.append(
                {
                    "id": item.get("id") or f"inline-document-{index+1}",
                    "title": item.get("title") or item.get("name") or f"Document {index+1}",
                    "content": item.get("content") or item.get("text") or "",
                    "tags": item.get("tags", []),
                    "source_type": item.get("source_type", "inline_document"),
                    "location": item.get("location", ""),
                    "remote_score": float(item.get("remote_score", item.get("score", 0.0)) or 0.0),
                }
            )
    return normalized


def load_documents_from_paths(paths):
    loaded = []
    errors = []
    for index, raw_path in enumerate(paths):
        path = Path(raw_path).expanduser()
        if not path.exists():
            errors.append({"source": str(path), "reason": "path_not_found"})
            continue
        try:
            if path.suffix.lower() == ".json":
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                items = payload if isinstance(payload, list) else [payload]
                for offset, item in enumerate(items):
                    if isinstance(item, str):
                        loaded.append(build_document_record(offset, "local_path", path.stem, item, location=str(path)))
                    elif isinstance(item, dict):
                        loaded.append(
                            {
                                "id": item.get("id") or f"{path.stem}-{offset+1}",
                                "title": item.get("title") or item.get("name") or f"{path.stem}-{offset+1}",
                                "content": item.get("content") or item.get("text") or "",
                                "tags": item.get("tags", []),
                                "source_type": "local_path",
                                "location": str(path),
                                "remote_score": float(item.get("remote_score", item.get("score", 0.0)) or 0.0),
                            }
                        )
            else:
                text = path.read_text(encoding="utf-8")
                loaded.append(build_document_record(index, "local_path", path.stem, text, location=str(path)))
        except Exception as exc:
            errors.append({"source": str(path), "reason": f"load_failed:{exc.__class__.__name__}"})
    return loaded, errors


def load_documents_from_urls(urls, timeout=5, headers=None):
    loaded = []
    errors = []
    for index, raw_url in enumerate(urls):
        text, error = fetch_text_from_url(raw_url, timeout=timeout, headers=headers)
        if error:
            errors.append(error)
            continue
        loaded.append(build_document_record(index, "remote_url", raw_url, text, location=raw_url))
    return loaded, errors


def extract_external_items(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("results", "documents", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    hits = payload.get("hits")
    if isinstance(hits, list):
        return hits
    if isinstance(hits, dict):
        for key in ("hits", "results", "items"):
            value = hits.get(key)
            if isinstance(value, list):
                return value
    return []


def normalize_external_result(index, item, endpoint):
    if isinstance(item, str):
        return build_document_record(index, "external_retriever", f"Remote Result {index+1}", item, location=endpoint)
    if not isinstance(item, dict):
        return None
    title = item.get("title") or item.get("name") or item.get("id") or f"Remote Result {index+1}"
    content = item.get("content") or item.get("text") or item.get("snippet") or item.get("body") or ""
    tags = item.get("tags", []) if isinstance(item.get("tags", []), list) else []
    raw_score = item.get("score", item.get("_score", item.get("rank_score", 0.0)))
    try:
        remote_score = float(raw_score or 0.0)
    except (TypeError, ValueError):
        remote_score = 0.0
    return {
        "id": item.get("id") or f"external-result-{index+1}",
        "title": title,
        "content": content,
        "tags": tags,
        "source_type": "external_retriever",
        "location": endpoint,
        "remote_score": remote_score,
    }


def fetch_external_retriever_results(query, payload):
    endpoint = payload.get("retriever_endpoint") or payload.get("external_retriever", {}).get("endpoint") or ""
    if not endpoint:
        return [], []

    method = str(payload.get("retriever_method") or payload.get("external_retriever", {}).get("method") or "POST").upper()
    external_cfg = payload.get("external_retriever", {}) if isinstance(payload.get("external_retriever", {}), dict) else {}
    headers = merge_headers(external_cfg.get("headers", {}) or {})
    headers.update(merge_headers(payload.get("retriever_headers", {}) or {}))

    request_payload = {"query": query, "top_k": int(payload.get("top_k", 3) or 3)}
    if isinstance(external_cfg.get("payload"), dict):
        request_payload.update(external_cfg.get("payload", {}))
    if isinstance(payload.get("retriever_payload"), dict):
        request_payload.update(payload.get("retriever_payload", {}))

    request_data = None
    request_url = endpoint
    if method == "GET":
        query_string = urllib.parse.urlencode(request_payload, doseq=True)
        if query_string:
            request_url = endpoint + ("&" if "?" in endpoint else "?") + query_string
    else:
        headers["Content-Type"] = "application/json"
        request_data = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")

    timeout = int(payload.get("timeout") or external_cfg.get("timeout", 5) or 5)

    try:
        request = urllib.request.Request(request_url, data=request_data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw_text = response.read().decode(charset, errors="ignore")
        response_payload = json.loads(raw_text)
    except Exception as exc:
        return [], [{"source": endpoint, "reason": f"retriever_failed:{exc.__class__.__name__}"}]

    documents = []
    for index, item in enumerate(extract_external_items(response_payload)):
        normalized = normalize_external_result(index, item, endpoint)
        if normalized is not None:
            documents.append(normalized)
    return documents, []


def deduplicate_documents(documents):
    deduped = []
    seen = set()
    for document in documents:
        key = (
            document.get("title", "").strip(),
            document.get("content", "").strip(),
            document.get("location", "").strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(document)
    return deduped


def load_records_from_paths(paths):
    records = []
    errors = []
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if not path.exists():
            errors.append({"source": str(path), "reason": "path_not_found"})
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, list):
                records.extend([item for item in payload if isinstance(item, dict)])
            elif isinstance(payload, dict):
                records.append(payload)
        except Exception as exc:
            errors.append({"source": str(path), "reason": f"load_failed:{exc.__class__.__name__}"})
    return records, errors


def load_records_from_urls(urls, timeout=5, headers=None):
    records = []
    errors = []
    for raw_url in urls:
        text, error = fetch_text_from_url(raw_url, timeout=timeout, headers=headers)
        if error:
            errors.append(error)
            continue
        try:
            payload = json.loads(text)
            if isinstance(payload, list):
                records.extend([item for item in payload if isinstance(item, dict)])
            elif isinstance(payload, dict):
                records.append(payload)
        except Exception as exc:
            errors.append({"source": raw_url, "reason": f"decode_failed:{exc.__class__.__name__}"})
    return records, errors
'''


TEST_TEMPLATE = '''#!/usr/bin/env python3
"""
测试脚本: {name}
用途: 验证工具核心功能
版本: V5.3 五类测试（正常/空/边界/异常/配置加载）
"""

import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from {module_name} import process, transform


# ── 1. 正常输入测试 ────────────────────────────────────────

def test_normal_case():
    """正常输入测试"""
    result = transform(__SAMPLE_INPUT__)
    assert result is not None
    assert result.get("status") == "ok"
    print("正常输入测试通过")


# ── 2. 空/边界输入测试 ─────────────────────────────────────

def test_empty_input():
    """空输入/边界输入测试"""
    result = transform(dict())
    assert result.get("status") == "ok"
    print("空输入测试通过")


def test_empty_list():
    """空列表输入测试"""
    result = transform([])
    assert result.get("status") == "ok"
    print("空列表测试通过")


# ── 3. 边界条件测试 ────────────────────────────────────────

def test_boundary_large_input():
    """大输入边界测试"""
    large_data = [dict(id=i, value=i*2) for i in range(1000)]
    result = transform(large_data)
    assert result.get("status") == "ok"
    print("大输入边界测试通过")


def test_boundary_nested():
    """嵌套结构边界测试"""
    nested = dict(level1=dict(level2=dict(level3="deep")))
    result = transform(nested)
    assert result.get("status") == "ok"
    print("嵌套结构边界测试通过")


# ── 4. 异常输入测试 ────────────────────────────────────────

def test_exception_invalid_type():
    """异常类型输入测试"""
    result = transform(None)
    assert result.get("status") == "ok"
    print("异常类型测试通过")


def test_exception_missing_file():
    """文件不存在异常测试"""
    try:
        process("/nonexistent/path/file.json")
        assert False, "应该抛出FileNotFoundError"
    except FileNotFoundError:
        print("文件不存在异常测试通过")


# ── 5. 配置加载测试 ────────────────────────────────────────

def test_config_loader():
    """配置加载器可用性测试"""
    try:
        from _skill_config import get_skill_config
        cfg = get_skill_config("shenjibailian", default=dict())
        assert cfg is not None
        print("配置加载测试通过")
    except ImportError:
        print("配置加载器未安装，跳过")


# ── 6. 核心转换逻辑测试 ────────────────────────────────────

__TEST_CASES__


# ── 主入口 ─────────────────────────────────────────────────

if __name__ == "__main__":
    test_normal_case()
    test_empty_input()
    test_empty_list()
    test_boundary_large_input()
    test_boundary_nested()
    test_exception_invalid_type()
    test_exception_missing_file()
    test_config_loader()
    test_transform()
    print("全部测试通过")
'''


STANDALONE_SMOKE_TEMPLATE = '''from __future__ import annotations


SAMPLE_INPUT = __SAMPLE_INPUT__


def run_smoke(root, load_entry, load_meta):
    mod = load_entry()
    meta = load_meta()
    result = mod.transform(SAMPLE_INPUT)
    assert isinstance(result, dict)
    assert result.get("status") == "ok"
    contract = meta.get("standalone_validation", {})
    assert contract.get("kind") == "python-script"
    assert contract.get("path") == "tests/standalone_smoke.py"
    summary_keys = ("hit_count", "record_count", "step_count", "count", "document_count")
    summary_parts = [f"status={result.get('status')}"]
    for key in summary_keys:
        if key in result:
            summary_parts.append(f"{key}={result[key]}")
            break
    return " ".join(summary_parts)
'''


CONTRACT_TEMPLATE = '''# 契约文档: {name}-v0.1

## 输入契约

### 格式要求
- 输入格式: JSON
- 编码: UTF-8
- 必需字段: [{inputs}]
- 建议字段: 根据具体业务需求扩展

### 输入验证Schema
```json
{{
  "type": "object",
  "required": [{input_schema_required}],
  "properties": {{
    "status": {{ "type": "string", "enum": ["ok", "error"] }},
    "data": {{ "type": ["object", "array", "string", "number"] }},
    "count": {{ "type": "integer", "minimum": 0 }},
    "message": {{ "type": "string" }}
  }}
}}
```

## 输出契约

### 格式要求
- 输出格式: JSON
- 编码: UTF-8

### 固定字段
| 字段 | 类型 | 说明 | 必需 |
|------|------|------|------|
| `status` | string | "ok" / "error" | 是 |
| `data` | any | 处理后的数据 | 是 |
| `count` | integer | 数据条目数 | 否 |
| `message` | string | 错误信息 | 否 |

## 性能契约

| 指标 | 基准 | 说明 |
|------|------|------|
| 时间复杂度 | O(n) | 线性遍历 |
| 空间复杂度 | O(n) | 与输入数据量成正比 |
| 最大输入大小 | 100MB | 超过建议分块处理 |
| 处理速度 | >10MB/s | 标准硬件环境 |

## 异常契约

| 场景 | 异常类型 | 退出码 | 行为 |
|------|----------|--------|------|
| 输入文件不存在 | FileNotFoundError | 1 | 记录错误日志 |
| JSON格式错误 | json.JSONDecodeError | 1 | 记录错误日志 |
| 处理异常 | Exception | 1 | 记录错误日志 |
| 权限不足 | PermissionError | 1 | 记录错误日志 |

## 边界条件

| 条件 | 预期行为 |
|------|----------|
| 空输入 {{}} | 返回 status="ok", data={{}} |
| 空列表 [] | 返回 status="ok", count=0 |
| None输入 | 返回 status="ok", data=None |
| 超大输入 (>100MB) | 可能内存溢出，建议分块 |
| 嵌套深度 >10 | 正常处理，无递归限制 |

## 使用示例

### 命令行
```bash
python {module_name}.py input.json -o result.json
python {module_name}.py input.json --dry-run
python {module_name}.py input.json -v
```

### Python API
```python
from {module_name} import process, transform

# 直接处理数据
result = transform({{"key": "value"}})
print(result["status"])  # "ok"

# 从文件处理
result = process("input.json")
```

## 测试方法

```bash
# 运行全部测试
python test_{module_name}.py

# 使用pytest
python -m pytest test_{module_name}.py -v
```

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.1 | 当前 | 初始版本，由神机百炼 V5.3 自动生成 |
'''


SKILL_DOC_TEMPLATE = '''---
metadata:
  name: "{skill_name}"
  version: "v0.1.0"
  author: "shenji-bailian"
  description: "{description}"
  language: "zh"
  tags: {tags}
  icon: "🛠"
  color: "#58a6ff"
---

# {display_name}

> {description}

## 触发词

{triggers}

## 功能概述

{description}

## 专精类型

{specialization}

## 专精说明

{specialization_notes}

```mermaid
graph LR
    A["输入: {input_desc}"] --> B["scripts/{entry_script}"]
    B --> C["输出: {output_desc}"]
```

## 工作流程

1. 读取输入并识别任务意图
2. 执行核心逻辑
3. 输出结构化结果
4. 在需要时给出验证或后续建议

## 输入输出

### 输入

{input_desc}

### 输出

{output_desc}

## API接口

- CLI: `python scripts/{entry_script} sample_input.json`
- Python: `from scripts.{module_name} import transform`
- 入口: `scripts/{entry_script}`

## 使用示例

```bash
python scripts/{entry_script} sample_input.json
```

## 测试方法

```bash
python tests/standalone_smoke.py
python scripts/test_{module_name}.py
```
'''


SKILL_META_TEMPLATE = '''{{
  "id": "{skill_name}",
  "name": "{display_name}",
  "version": "v0.1.0",
  "type": "script",
  "entry": "scripts/{entry_script}",
  "language": "python",
  "description": "{description}",
  "author": "shenji-bailian",
  "tags": {tags_json},
  "permissions": ["read:input", "write:output"],
  "triggers": {triggers_json},
  "inputs": {inputs_json},
  "outputs": {outputs_json},
  "dependencies": [],
  "standalone_validation": {{"kind": "python-script", "path": "tests/standalone_smoke.py"}},
  "min_python": "3.8"
}}
'''


class ToolFactory:
    """V6.5 工具工厂 — 自然语言锻造 + 专精运行框架"""

    def __init__(self, spec):
        self.raw_spec = spec
        # 加载配置
        cfg = get_skill_config("shenjibailian", default={})
        self.contract_cfg = cfg.get("contract", {})
        self.test_cfg = cfg.get("test_generation", {})
        self.quality_cfg = cfg.get("code_quality", {})
        self.forge_cfg = cfg.get("forge_modes", {})
        self.inference_cfg = cfg.get("natural_language_inference", {})
        self.spec = self._normalize_spec(spec)

    def _ensure_str(self, value):
        """确保值为字符串（YAML可能解析为dict/list）"""
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    def _render_sample_literal(self, sample_input):
        """把 JSON 风格示例输入转成可直接嵌入 Python 脚本的字面量。"""
        if not isinstance(sample_input, str):
            return repr(sample_input)
        try:
            parsed = json.loads(sample_input)
        except json.JSONDecodeError:
            return repr(sample_input)
        return repr(parsed)

    def _normalize_spec(self, spec):
        """兼容自然语言、扁平 spec 与结构化 spec。"""
        if isinstance(spec, str):
            return self._infer_spec_from_prompt(spec)

        if not isinstance(spec, dict):
            return {
                "name": "untitled_tool",
                "description": "未描述",
                "inputs": [],
                "outputs": [],
                "artifact_type": "tool",
                "forge_mode": "battle-ready",
                "sections": {},
            }

        if "tool" in spec or "io_contract" in spec or "persona_contract" in spec or "artifact_type" in spec:
            tool = spec.get("tool", {})
            io_contract = spec.get("io_contract", {})
            persona = spec.get("persona_contract", {})
            safety = spec.get("safety_contract", {})
            verification = spec.get("verification_contract", {})
            artifact = spec.get("artifact_type", tool.get("artifact_type", "tool"))
            return {
                "name": tool.get("name", spec.get("name", "untitled_tool")),
                "description": tool.get("description", spec.get("description", "未描述")),
                "inputs": io_contract.get("inputs", spec.get("inputs", [])),
                "outputs": io_contract.get("outputs", spec.get("outputs", [])),
                "artifact_type": artifact,
                "forge_mode": spec.get("forge_mode", "battle-ready"),
                "sections": {
                    "persona_contract": persona,
                    "tool_contract": tool,
                    "io_contract": io_contract,
                    "safety_contract": safety,
                    "verification_contract": verification,
                },
            }

        return {
            "name": spec.get("name", "untitled_tool"),
            "description": spec.get("description", "未描述"),
            "inputs": spec.get("inputs", []),
            "outputs": spec.get("outputs", []),
            "artifact_type": spec.get("artifact_type", "tool"),
            "forge_mode": spec.get("forge_mode", "battle-ready"),
            "sections": {
                "persona_contract": spec.get("persona_contract", {}),
                "tool_contract": spec,
                "io_contract": {
                    "inputs": spec.get("inputs", []),
                    "outputs": spec.get("outputs", []),
                },
                "safety_contract": spec.get("safety_contract", {}),
                "verification_contract": spec.get("verification_contract", {}),
            },
        }

    def _slugify_name(self, text):
        text = (text or "untitled_tool").strip().lower()
        text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", text)
        text = text.strip("_")
        return text or "untitled_tool"

    def _guess_name_from_prompt(self, prompt, artifact_type):
        stop_words = {"skill", "tool", "cli", "agent"}
        english = [
            token
            for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", prompt)
            if token.lower() not in stop_words
        ]
        if english:
            return self._slugify_name(english[0])
        if artifact_type == "skill":
            if "检索" in prompt:
                return "retrieval_skill"
            if "总结" in prompt or "摘要" in prompt:
                return "summary_skill"
            return "custom_skill"
        if "校验" in prompt or "验证" in prompt:
            return "validator_tool"
        if "清洗" in prompt:
            return "cleaner_tool"
        return "generated_tool"

    def _extract_inputs_outputs(self, prompt, artifact_type):
        lower = prompt.lower()
        inputs = []
        outputs = []
        io_patterns = self.inference_cfg.get("io_patterns", {})
        known_inputs = io_patterns.get("inputs", {})
        known_outputs = io_patterns.get("outputs", {})
        for label, keywords in known_inputs.items():
            if any(keyword in prompt or keyword in lower for keyword in keywords):
                inputs.append(label)
        for label, keywords in known_outputs.items():
            if any(keyword in prompt or keyword in lower for keyword in keywords):
                outputs.append(label)

        explicit_files = re.findall(r'([A-Za-z0-9_-]+\.(?:json|csv|txt|md|yaml|yml|py))', prompt, re.IGNORECASE)
        for file_name in explicit_files:
            if any(file_name.lower().endswith(ext) for ext in (".json", ".csv", ".txt", ".md", ".yaml", ".yml")):
                inputs.append(file_name)
        if artifact_type == "tool":
            if not inputs:
                inputs = ["input.json"]
            if not outputs:
                if "报告" in prompt:
                    outputs = ["report.json"]
                elif "校验" in prompt or "验证" in prompt:
                    outputs = ["validation_result.json"]
                else:
                    outputs = ["output.json"]
        else:
            if not inputs:
                inputs = ["任务描述", "输入数据"]
            outputs.extend(["SKILL.md", "_skillhub_meta.json", "scripts/*.py"])

        # 去重并保持顺序
        inputs = list(dict.fromkeys(inputs))
        outputs = list(dict.fromkeys(outputs))
        return inputs, outputs

    def _infer_specialization(self, prompt, artifact_type):
        prompt_lower = prompt.lower()
        retrieval_keywords = ["检索", "召回", "搜索", "知识库", "文档库", "问答"]
        browser_markers = ["网页", "页面", "链接", "url", "网址", "抓取"]
        if artifact_type == "skill" and any(keyword in prompt or keyword in prompt_lower for keyword in retrieval_keywords):
            if not any(marker in prompt or marker in prompt_lower for marker in browser_markers):
                return "retrieval-skill"
        specialization_map = self.inference_cfg.get("specialization_map", {})
        pool = specialization_map.get(artifact_type, {})
        for specialization, keywords in pool.items():
            if any(keyword in prompt or keyword in prompt_lower for keyword in keywords):
                return specialization
        return "general-skill" if artifact_type == "skill" else "general-tool"

    def _extract_triggers(self, prompt, artifact_type, name):
        trigger_keywords = []
        trigger_cfg = self.inference_cfg.get("trigger_keywords", {})
        common = trigger_cfg.get("common", [])
        tool_words = trigger_cfg.get("tool", [])
        skill_words = trigger_cfg.get("skill", [])
        trigger_keywords.extend(common)
        trigger_keywords.extend(skill_words if artifact_type == "skill" else tool_words)
        inferred = [name.replace("_", "-")]
        inferred.extend([word for word in trigger_keywords if word in prompt][:4])
        if "检索" in prompt:
            inferred.append("检索")
        if "总结" in prompt or "摘要" in prompt:
            inferred.append("总结")
        if "校验" in prompt or "验证" in prompt:
            inferred.append("校验")
        return list(dict.fromkeys([item for item in inferred if item]))

    def _extract_tags(self, prompt, artifact_type):
        tags = ["generated"]
        if artifact_type == "skill":
            tags.append("generated-skill")
        else:
            tags.append("generated-tool")
        tag_map = self.inference_cfg.get("tag_map", {})
        for tag, keywords in tag_map.items():
            if any(keyword in prompt for keyword in keywords):
                tags.append(tag)
        return list(dict.fromkeys(tags))

    def _extract_script_role(self, prompt, artifact_type, specialization=None):
        if specialization == "retrieval-skill":
            return "retrieval_runtime"
        if specialization == "browser-skill":
            return "browser_automation"
        if specialization == "analysis-skill":
            return "analysis_pipeline"
        if specialization == "workflow-skill":
            return "workflow_runtime"
        if specialization == "data-tool":
            return "data_processor"
        if specialization == "cli-tool":
            return "cli_runtime"
        if artifact_type == "skill":
            if "检索" in prompt and ("总结" in prompt or "摘要" in prompt):
                return "retrieval_and_summary"
            if "检索" in prompt:
                return "retrieval"
            return "skill_runtime"
        if "校验" in prompt or "验证" in prompt:
            return "validator"
        if "清洗" in prompt:
            return "cleaner"
        if "分析" in prompt:
            return "analyzer"
        return "generic_processor"

    def _infer_spec_from_prompt(self, prompt):
        prompt = prompt.strip()
        artifact_type = "skill" if "skill" in prompt.lower() or "技能" in prompt else "tool"
        forge_mode = "battle-ready"
        if "脚手架" in prompt or "骨架" in prompt:
            forge_mode = "scaffold-only"
        elif "契约" in prompt:
            forge_mode = "contract-first"
        name = self._guess_name_from_prompt(prompt, artifact_type)
        specialization = self._infer_specialization(prompt, artifact_type)
        inputs, outputs = self._extract_inputs_outputs(prompt, artifact_type)
        if specialization == "retrieval-skill":
            if "query" not in inputs:
                inputs.insert(0, "query")
            if "documents" not in inputs:
                inputs.append("documents")
            if "document_paths" not in inputs:
                inputs.append("document_paths")
            if "source_text" not in inputs:
                inputs.append("source_text")
            if "source_urls" not in inputs:
                inputs.append("source_urls")
            if "retriever_endpoint" not in inputs:
                inputs.append("retriever_endpoint")
            if "retrieval_report.json" not in outputs:
                outputs.insert(0, "retrieval_report.json")
        if specialization == "browser-skill" and "webpage_url" not in inputs:
            inputs.insert(0, "webpage_url")
        if specialization == "analysis-skill":
            if "records" not in inputs:
                inputs.insert(0, "records")
            if "record_paths" not in inputs:
                inputs.append("record_paths")
            if "record_urls" not in inputs:
                inputs.append("record_urls")
            if "report.json" not in outputs:
                outputs.insert(0, "report.json")
        if specialization == "workflow-skill" and "workflow_state.json" not in outputs:
            outputs.insert(0, "workflow_state.json")
        triggers = self._extract_triggers(prompt, artifact_type, name)
        tags = self._extract_tags(prompt, artifact_type)
        tags.append(specialization)
        tags = list(dict.fromkeys(tags))
        script_role = self._extract_script_role(prompt, artifact_type, specialization)
        verification_checks = ["smoke test", "input validation", "output contract"]
        if artifact_type == "skill":
            verification_checks.append("skill metadata consistency")
        return {
            "name": name,
            "description": prompt,
            "inputs": inputs,
            "outputs": outputs,
            "artifact_type": artifact_type,
            "forge_mode": forge_mode,
            "sections": {
                "persona_contract": {"role": "natural-language-forger", "style": "practical"},
                "tool_contract": {
                    "name": name,
                    "description": prompt,
                    "artifact_type": artifact_type,
                    "specialization": specialization,
                    "triggers": triggers,
                    "tags": tags,
                    "script_role": script_role,
                },
                "io_contract": {"inputs": inputs, "outputs": outputs},
                "safety_contract": {"rules": ["preserve backward compatibility", "emit readable scaffolds"]},
                "verification_contract": {"checks": verification_checks},
                "inference_contract": {
                    "source": "natural_language_prompt",
                    "triggers": triggers,
                    "tags": tags,
                    "script_role": script_role,
                    "specialization": specialization,
                },
            },
        }

    def _resolve_mode(self):
        mode = self.spec.get("forge_mode", "battle-ready")
        modes = self.forge_cfg.get("modes", {})
        defaults = {
            "scaffold-only": {"include_tests": False, "include_contract": False, "intent": "rapid scaffolding"},
            "contract-first": {"include_tests": True, "include_contract": True, "intent": "contract-led forging"},
            "battle-ready": {"include_tests": True, "include_contract": True, "intent": "deployable forging"},
        }
        merged = defaults.get(mode, defaults["battle-ready"]).copy()
        merged.update(modes.get(mode, {}))
        merged["name"] = mode
        return merged

    def _build_forge_summary(self, template_key, mode_cfg):
        sections = self.spec.get("sections", {})
        persona = sections.get("persona_contract", {})
        safety = sections.get("safety_contract", {})
        verification = sections.get("verification_contract", {})
        verification_steps = verification.get("checks", []) if isinstance(verification.get("checks", []), list) else []
        safety_rules = safety.get("rules", []) if isinstance(safety.get("rules", []), list) else []
        return {
            "forge_mode": mode_cfg["name"],
            "forge_intent": mode_cfg.get("intent", "deployable forging"),
            "artifact_type": self.spec.get("artifact_type", "tool"),
            "specialization": sections.get("tool_contract", {}).get("specialization", "general"),
            "template_matched": template_key,
            "persona_alignment": persona.get("style") or persona.get("role") or "generic",
            "safety_rules": safety_rules[:4],
            "verification_plan": verification_steps[:5],
            "contracts_present": [key for key, value in sections.items() if value],
        }

    def _render_skill_doc(self, skill_name, description, inputs, outputs, module_name):
        display_name = skill_name.replace("_", "-")
        tool_contract = self.spec.get("sections", {}).get("tool_contract", {})
        tags = tool_contract.get("tags", ["generated-skill", "automation", "tooling"])
        triggers = tool_contract.get("triggers", [display_name, "自动化", "生成", "处理"])
        trigger_lines = "\n".join(f"- {item}" for item in triggers)
        notes = self._specialization_notes(tool_contract.get("specialization", "general-skill"))
        return SKILL_DOC_TEMPLATE.format(
            skill_name=display_name,
            display_name=display_name,
            description=description,
            tags=json.dumps(tags, ensure_ascii=False),
            triggers=trigger_lines,
            specialization=tool_contract.get("specialization", "general-skill"),
            specialization_notes=notes,
            input_desc=", ".join(inputs) if inputs else "任务描述",
            output_desc=", ".join(outputs) if outputs else "结构化结果",
            entry_script=f"{module_name}.py",
            module_name=module_name,
        )

    def _render_skill_meta(self, skill_name, description, inputs, outputs, module_name):
        display_name = skill_name.replace("_", "-")
        tool_contract = self.spec.get("sections", {}).get("tool_contract", {})
        tags = tool_contract.get("tags", ["generated-skill", "automation", "tooling"])
        triggers = tool_contract.get("triggers", [display_name, "自动化", "处理", "生成"])
        return SKILL_META_TEMPLATE.format(
            skill_name=display_name,
            display_name=display_name,
            entry_script=f"{module_name}.py",
            description=description,
            tags_json=json.dumps(tags, ensure_ascii=False),
            triggers_json=json.dumps(triggers, ensure_ascii=False),
            inputs_json=json.dumps(inputs, ensure_ascii=False),
            outputs_json=json.dumps(outputs, ensure_ascii=False),
        )

    def _build_specialized_bundle(self, specialization, module_name):
        bundles = {
            "retrieval-skill": {
                "transform_code": '''
import urllib.parse
import urllib.request


def build_document_record(index, source_type, title, content, tags=None, location="", remote_score=0.0):
    return {
        "id": f"{source_type}-{index+1}",
        "title": title or f"Document {index+1}",
        "content": content or "",
        "tags": tags or [],
        "source_type": source_type,
        "location": location,
        "remote_score": remote_score,
    }


def normalize_inline_documents(raw_documents):
    normalized = []
    for index, item in enumerate(raw_documents):
        if isinstance(item, str):
            normalized.append(build_document_record(index, "inline_document", f"Document {index+1}", item))
        elif isinstance(item, dict):
            normalized.append(
                {
                    "id": item.get("id") or f"inline-document-{index+1}",
                    "title": item.get("title") or item.get("name") or f"Document {index+1}",
                    "content": item.get("content") or item.get("text") or "",
                    "tags": item.get("tags", []),
                    "source_type": item.get("source_type", "inline_document"),
                    "location": item.get("location", ""),
                    "remote_score": float(item.get("remote_score", item.get("score", 0.0)) or 0.0),
                }
            )
    return normalized


def load_documents_from_paths(paths):
    loaded = []
    errors = []
    for index, raw_path in enumerate(paths):
        path = Path(raw_path).expanduser()
        if not path.exists():
            errors.append({"source": str(path), "reason": "path_not_found"})
            continue
        try:
            if path.suffix.lower() == ".json":
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                items = payload if isinstance(payload, list) else [payload]
                for offset, item in enumerate(items):
                    if isinstance(item, str):
                        loaded.append(build_document_record(offset, "local_path", path.stem, item, location=str(path)))
                    elif isinstance(item, dict):
                        loaded.append(
                            {
                                "id": item.get("id") or f"{path.stem}-{offset+1}",
                                "title": item.get("title") or item.get("name") or f"{path.stem}-{offset+1}",
                                "content": item.get("content") or item.get("text") or "",
                                "tags": item.get("tags", []),
                                "source_type": "local_path",
                                "location": str(path),
                            }
                        )
            else:
                text = path.read_text(encoding="utf-8")
                loaded.append(build_document_record(index, "local_path", path.stem, text, location=str(path)))
        except Exception as exc:
            errors.append({"source": str(path), "reason": f"load_failed:{exc.__class__.__name__}"})
    return loaded, errors


def load_documents_from_urls(urls, timeout=5):
    loaded = []
    errors = []
    for index, raw_url in enumerate(urls):
        try:
            with urllib.request.urlopen(raw_url, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                text = response.read().decode(charset, errors="ignore")
            loaded.append(build_document_record(index, "remote_url", raw_url, text, location=raw_url))
        except Exception as exc:
            errors.append({"source": raw_url, "reason": f"fetch_failed:{exc.__class__.__name__}"})
    return loaded, errors


def extract_external_items(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("results", "documents", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    hits = payload.get("hits")
    if isinstance(hits, list):
        return hits
    if isinstance(hits, dict):
        for key in ("hits", "results", "items"):
            value = hits.get(key)
            if isinstance(value, list):
                return value
    return []


def normalize_external_result(index, item, endpoint):
    if isinstance(item, str):
        return build_document_record(index, "external_retriever", f"Remote Result {index+1}", item, location=endpoint)
    if not isinstance(item, dict):
        return None
    title = item.get("title") or item.get("name") or item.get("id") or f"Remote Result {index+1}"
    content = item.get("content") or item.get("text") or item.get("snippet") or item.get("body") or ""
    tags = item.get("tags", []) if isinstance(item.get("tags", []), list) else []
    raw_score = item.get("score", item.get("_score", item.get("rank_score", 0.0)))
    try:
        remote_score = float(raw_score or 0.0)
    except (TypeError, ValueError):
        remote_score = 0.0
    return {
        "id": item.get("id") or f"external-result-{index+1}",
        "title": title,
        "content": content,
        "tags": tags,
        "source_type": "external_retriever",
        "location": endpoint,
        "remote_score": remote_score,
    }


def fetch_external_retriever_results(query, payload):
    endpoint = payload.get("retriever_endpoint") or payload.get("external_retriever", {}).get("endpoint") or ""
    if not endpoint:
        return [], []

    method = str(payload.get("retriever_method") or payload.get("external_retriever", {}).get("method") or "POST").upper()
    headers = {"Accept": "application/json"}
    external_cfg = payload.get("external_retriever", {})
    header_payload = {}
    if isinstance(external_cfg, dict):
        header_payload.update(external_cfg.get("headers", {}) or {})
    header_payload.update(payload.get("retriever_headers", {}) or {})
    headers.update({str(key): str(value) for key, value in header_payload.items()})

    request_payload = {"query": query, "top_k": int(payload.get("top_k", 3) or 3)}
    if isinstance(external_cfg, dict) and isinstance(external_cfg.get("payload"), dict):
        request_payload.update(external_cfg.get("payload", {}))
    if isinstance(payload.get("retriever_payload"), dict):
        request_payload.update(payload.get("retriever_payload", {}))

    request_data = None
    request_url = endpoint
    if method == "GET":
        query_string = urllib.parse.urlencode(request_payload, doseq=True)
        if query_string:
            request_url = endpoint + ("&" if "?" in endpoint else "?") + query_string
    else:
        headers.setdefault("Content-Type", "application/json")
        request_data = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")

    timeout = int(payload.get("timeout") or external_cfg.get("timeout", 5) or 5)

    try:
        request = urllib.request.Request(request_url, data=request_data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw_text = response.read().decode(charset, errors="ignore")
        response_payload = json.loads(raw_text)
    except Exception as exc:
        return [], [{"source": endpoint, "reason": f"retriever_failed:{exc.__class__.__name__}"}]

    items = extract_external_items(response_payload)
    documents = []
    for index, item in enumerate(items):
        normalized = normalize_external_result(index, item, endpoint)
        if normalized is not None:
            documents.append(normalized)
    return documents, []


def deduplicate_documents(documents):
    deduped = []
    seen = set()
    for document in documents:
        key = (
            document.get("title", "").strip(),
            document.get("content", "").strip(),
            document.get("location", "").strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(document)
    return deduped


def normalize_documents(payload):
    """兼容内联文档、本地文件、纯文本和 URL 形式的知识条目。"""
    raw_documents = payload.get("documents") or payload.get("knowledge_base") or []
    normalized = normalize_inline_documents(raw_documents)
    source_summary = {
        "inline_document_count": len(normalized),
        "inline_text_count": 0,
        "local_path_count": 0,
        "url_count": 0,
        "external_retriever_count": 0,
        "error_count": 0,
        "errors": [],
    }

    source_text = payload.get("source_text") or payload.get("context_text") or ""
    if source_text:
        normalized.append(
            build_document_record(
                len(normalized),
                "inline_text",
                payload.get("source_title", "Inline Text"),
                source_text,
                location="payload.source_text",
            )
        )
        source_summary["inline_text_count"] = 1

    document_paths = payload.get("document_paths") or payload.get("paths") or []
    if document_paths:
        path_docs, path_errors = load_documents_from_paths(document_paths)
        normalized.extend(path_docs)
        source_summary["local_path_count"] = len(path_docs)
        source_summary["errors"].extend(path_errors)

    source_urls = payload.get("source_urls") or payload.get("urls") or payload.get("webpage_urls") or []
    if source_urls:
        remote_docs, remote_errors = load_documents_from_urls(source_urls, timeout=int(payload.get("timeout", 5) or 5))
        normalized.extend(remote_docs)
        source_summary["url_count"] = len(remote_docs)
        source_summary["errors"].extend(remote_errors)

    external_docs, external_errors = fetch_external_retriever_results(payload.get("query") or payload.get("task") or payload.get("question") or "", payload)
    if external_docs:
        normalized.extend(external_docs)
        source_summary["external_retriever_count"] = len(external_docs)
    source_summary["errors"].extend(external_errors)

    source_summary["error_count"] = len(source_summary["errors"])
    return deduplicate_documents(normalized), source_summary


def tokenize(text):
    return [token for token in re.findall(r'[\\u4e00-\\u9fff]{2,}|[a-zA-Z0-9_]+', str(text).lower()) if token]


def score_document(query, query_tokens, document):
    content_tokens = tokenize(document.get("content", ""))
    title_tokens = tokenize(document.get("title", ""))
    tag_tokens = tokenize(" ".join(document.get("tags", [])))
    if not query_tokens or not (content_tokens or title_tokens or tag_tokens):
        return 0.0
    content_overlap = len(set(query_tokens) & set(content_tokens))
    title_overlap = len(set(query_tokens) & set(title_tokens))
    tag_overlap = len(set(query_tokens) & set(tag_tokens))
    ordered_hits = sum(1 for token in query_tokens if token in document.get("content", ""))
    normalized_query = str(query or "").replace(" ", "")
    normalized_content = str(document.get("content", "")).replace(" ", "")
    exact_phrase = 1 if normalized_query and normalized_query in normalized_content else 0
    remote_score = 0.0
    try:
        remote_score = float(document.get("remote_score", 0.0) or 0.0)
    except (TypeError, ValueError):
        remote_score = 0.0
    return round(content_overlap * 1.2 + title_overlap * 1.5 + tag_overlap * 0.8 + ordered_hits * 0.4 + exact_phrase * 1.5 + remote_score * 0.35, 2)


def retrieve_records(query, documents, top_k=3):
    query_tokens = tokenize(query)
    scored = []
    for document in documents:
        score = score_document(query, query_tokens, document)
        if score > 0:
            snippet = document.get("content", "")[:120]
            scored.append(
                {
                    "id": document.get("id"),
                    "title": document.get("title"),
                    "score": score,
                    "snippet": snippet,
                    "tags": document.get("tags", []),
                    "source_type": document.get("source_type", "inline_document"),
                    "location": document.get("location", ""),
                }
            )
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def summarize_hits(query, hits, source_summary):
    if not hits:
        return f"未命中与 {query} 相关的知识条目"
    top_titles = " / ".join(hit["title"] for hit in hits[:3] if hit.get("title"))
    source_parts = []
    if source_summary.get("local_path_count"):
        source_parts.append(f"{source_summary['local_path_count']}个本地文件")
    if source_summary.get("inline_text_count"):
        source_parts.append("1段内联文本")
    if source_summary.get("url_count"):
        source_parts.append(f"{source_summary['url_count']}个远程URL")
    if source_summary.get("external_retriever_count"):
        source_parts.append(f"{source_summary['external_retriever_count']}条外部检索结果")
    source_desc = "，来源包括" + " / ".join(source_parts) if source_parts else ""
    return f"围绕 {query} 共命中 {len(hits)} 条结果，优先参考：{top_titles}{source_desc}"


def transform(data):
    """Retrieval skill 骨架 - 在内联/本地/远程与外部检索结果中检索并生成摘要。"""
    payload = data if isinstance(data, dict) else {"query": str(data)}
    query = payload.get("query") or payload.get("task") or payload.get("question") or ""
    documents, source_summary = normalize_documents(payload)
    hits = retrieve_records(query, documents, top_k=int(payload.get("top_k", 3) or 3))
    return {
        "status": "ok",
        "query": query,
        "document_count": len(documents),
        "hit_count": len(hits),
        "results": hits,
        "source_summary": source_summary,
        "summary": payload.get("summary") or summarize_hits(query, hits, source_summary),
    }
''',
                "test_cases": '''
def test_transform():
    from {module_name} import transform
    result = transform(
        {
            "query": "缓存 延迟",
            "documents": [
                {"title": "缓存优化", "content": "缓存命中率提升后接口延迟下降 35%"},
                {"title": "日志治理", "content": "通过结构化日志降低排查时间"},
            ],
            "source_text": "结论：缓存命中率提升后，延迟进一步下降。",
        }
    )
    assert result["hit_count"] >= 1
    assert result["document_count"] >= 3
    assert result["results"][0]["title"] == "缓存优化"
    print("retrieval skill transform测试通过")
''',
                "sample_input": '{"query": "缓存 延迟", "documents": [{"title": "缓存优化", "content": "缓存命中率提升后接口延迟下降 35%"}], "source_text": "结论：缓存命中率提升后，延迟进一步下降。"}',
            },
            "browser-skill": {
                "transform_code": '''
from source_adapter import fetch_text_from_url


def fetch_page(payload):
    """抓取入口：优先读取已给内容，否则尝试拉取网页正文"""
    webpage_url = payload.get("webpage_url", "")
    raw_content = payload.get("content", "")
    title = payload.get("title", "")
    errors = []
    if not raw_content and webpage_url:
        raw_content, error = fetch_text_from_url(
            webpage_url,
            timeout=int(payload.get("timeout", 5) or 5),
            headers=payload.get("webpage_headers", {}),
        )
        if error:
            errors.append(error)
    return {"webpage_url": webpage_url, "content": raw_content or webpage_url, "title": title, "errors": errors}


def extract_links(text):
    """从文本中提取链接"""
    links = re.findall(r"""https?://[^\\s'"<>]+""", text)
    trailing_link_chars = re.compile(r"""[]'"<>.,;)}]+$""")
    return [trailing_link_chars.sub("", link) for link in links]


def summarize_page(page):
    """页面摘要入口占位"""
    text = page.get("content", "")
    return text[:120] if isinstance(text, str) else ""


def transform(data):
    """Browser skill 骨架 - 读取网页地址或网页内容并提取结构化结果"""
    payload = data if isinstance(data, dict) else {"webpage_url": data}
    page = fetch_page(payload)
    text = page.get("content", "")
    links = extract_links(text)
    title = page.get("title") or (text[:40] if isinstance(text, str) else "")
    return {
        "status": "ok",
        "webpage_url": page.get("webpage_url", ""),
        "title": title,
        "links": links,
        "fetch_errors": page.get("errors", []),
        "summary": payload.get("summary", "") or summarize_page(page),
    }
''',
                "test_cases": '''
def test_transform():
    from {module_name} import transform
    data = {"webpage_url": "https://example.com", "content": "See https://example.com/docs"}
    result = transform(data)
    assert result["webpage_url"] == "https://example.com"
    assert "https://example.com/docs" in result["links"]
    print("browser skill transform测试通过")
''',
                "sample_input": '{"webpage_url": "https://example.com", "content": "See https://example.com/docs"}',
            },
            "workflow-skill": {
                "transform_code": '''
def default_step_handlers():
    """默认步骤处理器映射"""
    return {
        "collect": lambda context: {"step": "collect", "state": "ready", "context": context},
        "process": lambda context: {"step": "process", "state": "ready", "context": context},
        "deliver": lambda context: {"step": "deliver", "state": "ready", "context": context},
    }


def run_step(step, context, handlers):
    """执行单个步骤"""
    handler = handlers.get(step, lambda ctx: {"step": step, "state": "custom", "context": ctx})
    return handler(context)


def transform(data):
    """Workflow skill 骨架 - 编排步骤、状态和执行摘要"""
    payload = data if isinstance(data, dict) else {"task": str(data)}
    steps = payload.get("steps") or ["collect", "process", "deliver"]
    current_state = payload.get("state", "pending")
    handlers = default_step_handlers()
    execution_plan = []
    for index, step in enumerate(steps, start=1):
        result = run_step(step, payload, handlers)
        result["order"] = index
        if current_state != "pending":
            result["state"] = current_state
        execution_plan.append(result)
    return {
        "status": "ok",
        "workflow_state": current_state,
        "step_count": len(execution_plan),
        "execution_plan": execution_plan,
    }
''',
                "test_cases": '''
def test_transform():
    from {module_name} import transform
    result = transform({"steps": ["collect", "review", "publish"], "state": "pending"})
    assert result["step_count"] == 3
    assert result["execution_plan"][0]["step"] == "collect"
    print("workflow skill transform测试通过")
''',
                "sample_input": '{"steps": ["collect", "review", "publish"], "state": "pending"}',
            },
            "analysis-skill": {
                "transform_code": '''
from source_adapter import load_records_from_paths, load_records_from_urls


def metric_registry():
    """指标注册表，占位后可继续扩展更多统计项"""
    return {
        "count": lambda values: len(values),
        "sum": lambda values: round(sum(values), 2),
        "avg": lambda values: round(sum(values) / len(values), 2) if values else 0,
        "max": lambda values: max(values) if values else 0,
        "min": lambda values: min(values) if values else 0,
    }


def generate_insights(metrics):
    """洞察生成入口占位"""
    insights = []
    if metrics.get("avg", 0) > 0:
        insights.append(f"average={metrics.get('avg')}")
    if metrics.get("max", 0) > metrics.get("avg", 0):
        insights.append("max_above_average")
    return insights


def normalize_records(payload):
    records = payload.get("records", []) if isinstance(payload.get("records", []), list) else []
    path_records, path_errors = load_records_from_paths(payload.get("record_paths") or payload.get("records_path") or [])
    url_records, url_errors = load_records_from_urls(
        payload.get("record_urls") or payload.get("records_url") or [],
        timeout=int(payload.get("timeout", 5) or 5),
        headers=payload.get("record_headers", {}),
    )
    summary = {
        "inline_record_count": len(records),
        "local_record_count": len(path_records),
        "remote_record_count": len(url_records),
        "error_count": len(path_errors) + len(url_errors),
        "errors": path_errors + url_errors,
    }
    return records + path_records + url_records, summary


def transform(data):
    """Analysis skill 骨架 - 汇总指标并形成报告"""
    payload = data if isinstance(data, dict) else {"records": data}
    records, source_summary = normalize_records(payload)
    metrics = {}
    if isinstance(records, list):
        numeric_values = []
        for item in records:
            if isinstance(item, dict):
                for value in item.values():
                    if isinstance(value, (int, float)):
                        numeric_values.append(value)
        if numeric_values:
            registry = metric_registry()
            metrics = {name: calc(numeric_values) for name, calc in registry.items()}
    return {
        "status": "ok",
        "report_name": payload.get("report_name", "analysis_report"),
        "record_count": len(records),
        "source_summary": source_summary,
        "metrics": metrics,
        "insights": payload.get("insights", []) or generate_insights(metrics),
    }
''',
                "test_cases": '''
def test_transform():
    from {module_name} import transform
    result = transform({"records": [{"sales": 10}, {"sales": 20}], "report_name": "sales_report"})
    assert result["report_name"] == "sales_report"
    assert result["metrics"]["avg"] == 15.0
    print("analysis skill transform测试通过")
''',
                "sample_input": '{"records": [{"sales": 10}, {"sales": 20}], "report_name": "sales_report"}',
            },
            "cli-tool": {
                "transform_code": '''
def transform(data):
    """CLI tool 骨架 - 读取配置并返回执行结果"""
    payload = data if isinstance(data, dict) else {"input": data}
    command = payload.get("command", "run")
    options = payload.get("options", {})
    return {
        "status": "ok",
        "command": command,
        "options": options,
        "message": f"CLI command {command} prepared",
    }
''',
                "test_cases": '''
def test_transform():
    from {module_name} import transform
    result = transform({"command": "scan", "options": {"verbose": True}})
    assert result["command"] == "scan"
    assert result["options"]["verbose"] is True
    print("cli tool transform测试通过")
''',
                "sample_input": '{"command": "scan", "options": {"verbose": true}}',
            },
            "data-tool": {
                "transform_code": '''
def transform(data):
    """Data tool 骨架 - 清洗记录并输出统计"""
    records = data if isinstance(data, list) else data.get("records", []) if isinstance(data, dict) else []
    cleaned = []
    for item in records:
        if isinstance(item, dict):
            cleaned.append({k: v for k, v in item.items() if v not in (None, "", [])})
    return {
        "status": "ok",
        "count": len(cleaned),
        "cleaned_records": cleaned,
    }
''',
                "test_cases": '''
def test_transform():
    from {module_name} import transform
    result = transform([{"a": 1, "b": None}, {"c": 2, "d": ""}])
    assert result["count"] == 2
    assert "b" not in result["cleaned_records"][0]
    print("data tool transform测试通过")
''',
                "sample_input": '[{"a": 1, "b": null}, {"c": 2, "d": ""}]',
            },
        }
        bundle = bundles.get(specialization)
        if not bundle:
            return None
        resolved = dict(bundle)
        resolved["test_cases"] = resolved["test_cases"].replace("{module_name}", module_name)
        return resolved

    def _specialization_notes(self, specialization):
        notes_map = {
            "retrieval-skill": "- 重点处理 query、知识条目和命中排序\n- 生成的是可执行的检索骨架，支持内联文档、本地文件、可选 URL 与标准 HTTP 检索端点，可继续接搜索 API 或向量检索后端",
            "browser-skill": "- 重点处理网页地址、页面正文和链接提取\n- 建议结合浏览器自动化或页面抓取能力继续扩展",
            "analysis-skill": "- 重点处理记录、指标和报告结构\n- 建议继续补充指标定义、洞察规则和报告格式",
            "workflow-skill": "- 重点处理步骤编排、状态流转和执行计划\n- 建议继续补充步骤依赖、重试策略和失败恢复",
            "cli-tool": "- 重点处理命令、参数和返回结果\n- 建议继续补充子命令和参数校验",
            "data-tool": "- 重点处理记录清洗、转换和统计\n- 建议继续补充字段映射和异常数据处理",
        }
        return notes_map.get(specialization, "- 通用骨架，可继续按具体任务细化")

    def _build_support_files(self, specialization):
        shared_adapter_specializations = {"retrieval-skill", "browser-skill", "analysis-skill"}
        support = {
            "retrieval-skill": {
                "scripts/source_adapter.py": SOURCE_ADAPTER_TEMPLATE,
                "assets/sample_retrieval_input.json": json.dumps(
                    {
                        "query": "缓存 延迟",
                        "documents": [
                            {"id": "doc-1", "title": "缓存优化", "content": "缓存命中率提升后接口延迟下降 35%", "tags": ["performance"]},
                            {"id": "doc-2", "title": "日志治理", "content": "结构化日志帮助缩短排查时间", "tags": ["ops"]},
                        ],
                        "document_paths": ["docs/cache.md", "docs/latency.json"],
                        "source_text": "结论：缓存命中率提升后，平均延迟继续下降。",
                        "retriever_endpoint": "http://127.0.0.1:8080/search",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                "assets/retrieval_schema.json": json.dumps(
                    {
                        "query": "string",
                        "documents": [{"id": "string", "title": "string", "content": "string"}],
                        "document_paths": ["string"],
                        "source_text": "string",
                        "source_urls": ["string"],
                        "retriever_endpoint": "string",
                        "retriever_method": "GET|POST",
                        "retriever_headers": {"Authorization": "string"},
                        "retriever_payload": {"tenant": "string"},
                        "results": ["object"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            },
            "browser-skill": {
                "scripts/source_adapter.py": SOURCE_ADAPTER_TEMPLATE,
                "assets/sample_browser_input.json": json.dumps(
                    {"webpage_url": "https://example.com", "content": "Example content with https://example.com/docs"},
                    ensure_ascii=False,
                    indent=2,
                ),
                "assets/browser_targets.json": json.dumps(
                    {"allowed_domains": ["example.com"], "capture_fields": ["title", "links", "summary"]},
                    ensure_ascii=False,
                    indent=2,
                ),
            },
            "analysis-skill": {
                "scripts/source_adapter.py": SOURCE_ADAPTER_TEMPLATE,
                "assets/sample_analysis_input.json": json.dumps(
                    {
                        "records": [{"sales": 10}, {"sales": 20}],
                        "record_paths": ["data/sales.json"],
                        "report_name": "sales_report",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                "assets/report_schema.json": json.dumps(
                    {
                        "report_name": "string",
                        "record_paths": ["string"],
                        "record_urls": ["string"],
                        "metrics": {"count": "number", "avg": "number"},
                        "insights": ["string"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            },
            "workflow-skill": {
                "assets/sample_workflow_input.json": json.dumps(
                    {"steps": ["collect", "review", "publish"], "state": "pending"},
                    ensure_ascii=False,
                    indent=2,
                ),
                "assets/workflow_template.json": json.dumps(
                    {"workflow_state": "pending", "execution_plan": [{"step": "collect", "order": 1}]},
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        }
        resolved = dict(support.get(specialization, {}))
        if specialization in shared_adapter_specializations:
            resolved.setdefault("scripts/source_adapter.py", SOURCE_ADAPTER_TEMPLATE)
        return resolved

    @record_metrics("shenji-bailian")
    def forge(self):
        """锻造工具或 skill：生成代码 + 测试 + 契约/技能定义"""
        name = self.spec.get("name", "untitled_tool")
        desc = self.spec.get("description", "未描述")
        inputs = ", ".join(self.spec.get("inputs", ["input"]))
        outputs = ", ".join(self.spec.get("outputs", ["output"]))
        module_name = name.replace("-", "_").lower()
        mode_cfg = self._resolve_mode()
        artifact_type = self.spec.get("artifact_type", "tool")
        specialization = self.spec.get("sections", {}).get("tool_contract", {}).get("specialization")

        # V5.3/V6.3: 智能模板匹配 + 专精偏好
        template_key = self._select_template(desc)
        template = TEMPLATES.get(template_key, {})
        specialized_bundle = self._build_specialized_bundle(specialization, module_name)
        active_template = specialized_bundle or template
        transform_code = self._ensure_str(active_template.get("transform_code", GENERIC_TRANSFORM))
        test_cases_raw = self._ensure_str(active_template.get("test_cases", GENERIC_TEST))
        test_cases = test_cases_raw.replace("{module_name}", module_name)
        sample_input = self._ensure_str(active_template.get("sample_input", GENERIC_SAMPLE))
        sample_literal = self._render_sample_literal(sample_input)

        # 生成工具代码（V5.3: 先format简单字段，再replace代码块，避免{}冲突）
        tool_code = TOOL_TEMPLATE.format(
            name=name,
            description=desc,
            input_desc=inputs,
            output_desc=outputs,
        ).replace('__TRANSFORM_CODE__', transform_code)

        # 生成测试代码
        test_code = ""
        if mode_cfg.get("include_tests", True):
            test_code = TEST_TEMPLATE.format(
                name=name,
                module_name=module_name,
            ).replace('__SAMPLE_INPUT__', sample_literal).replace('__TEST_CASES__', test_cases)

        standalone_smoke = ""
        if artifact_type == "skill":
            standalone_smoke = STANDALONE_SMOKE_TEMPLATE.replace('__SAMPLE_INPUT__', sample_literal)

        # 生成契约文档（V5.3 增强版）
        contract = ""
        if mode_cfg.get("include_contract", True):
            contract = self._generate_contract(name, inputs, module_name)

        files = {}
        if artifact_type == "skill":
            skill_doc = self._render_skill_doc(name, desc, self.spec.get("inputs", []), self.spec.get("outputs", []), module_name)
            skill_meta = self._render_skill_meta(name, desc, self.spec.get("inputs", []), self.spec.get("outputs", []), module_name)
            files[f"{module_name}/SKILL.md"] = skill_doc
            files[f"{module_name}/_skillhub_meta.json"] = skill_meta
            files[f"{module_name}/scripts/{module_name}.py"] = tool_code
            for rel_path, content in self._build_support_files(specialization).items():
                files[f"{module_name}/{rel_path}"] = content
            if test_code:
                files[f"{module_name}/scripts/test_{module_name}.py"] = test_code
            if standalone_smoke:
                files[f"{module_name}/tests/standalone_smoke.py"] = standalone_smoke
            if contract:
                files[f"{module_name}/{module_name}.contract.md"] = contract
        else:
            files[f"{module_name}.py"] = tool_code
            if test_code:
                files[f"test_{module_name}.py"] = test_code
            if contract:
                files[f"{module_name}.contract.md"] = contract

        forge_summary = self._build_forge_summary(template_key, mode_cfg)

        return {
            "factory": "shenji-bailian",
            "version": "v0.1.0",
            "tool_name": name,
            "artifact_type": artifact_type,
            "specialization": self.spec.get("sections", {}).get("tool_contract", {}).get("specialization", "general"),
            "template_matched": template_key,
            "forge_mode": mode_cfg["name"],
            "forge_intent": forge_summary["forge_intent"],
            "forge_summary": forge_summary,
            "inferred_spec": self.spec,
            "files": files,
            # 向后兼容：保留 V5.0 的顶级字段
            "tool_code": tool_code,
            "test_code": test_code,
            "contract": contract,
            "quality_score": round(
                max(
                    0.0,
                    min(
                        100.0,
                        72.0
                        + len(files) * 4.0
                        + (6.0 if test_code else 0.0)
                        + (4.0 if contract else 0.0)
                        + (4.0 if artifact_type == "skill" else 0.0)
                    ),
                ),
                1,
            ),
            "human_intervention": 0,
            "output_completeness": round(min(100.0, 65.0 + len(files) * 6.0), 1),
            "consistency_score": 100.0 if files else 0.0,
            "error_count": 0,
        }

    def _select_template(self, description):
        """V5.3/V6.3: 根据description关键词与专精偏好匹配模板"""
        specialization = self.spec.get("sections", {}).get("tool_contract", {}).get("specialization")
        specialization_map = self.inference_cfg.get("specialization_template_map", {})
        if specialization in specialization_map:
            preferred = specialization_map[specialization]
            if preferred in TEMPLATES:
                return preferred
        desc_lower = description.lower()
        scores = {}
        for key, tmpl in TEMPLATES.items():
            score = sum(1 for kw in tmpl.get("keywords", []) if kw in desc_lower)
            if score > 0:
                scores[key] = score
        if not scores:
            return "generic"
        return max(scores, key=scores.get)

    def _generate_contract(self, name, inputs, module_name):
        """V5.3: 生成增强版契约文档"""
        # 构建输入schema
        input_schema_required = '"status", "data"'
        input_validation = self.contract_cfg.get("input_validation", {})
        required = input_validation.get("required_fields", ["status", "data"])
        if required:
            input_schema_required = ", ".join(f'"{f}"' for f in required)

        return CONTRACT_TEMPLATE.format(
            name=name,
            inputs=inputs,
            module_name=module_name,
            input_schema_required=input_schema_required,
        )


def main():
    if len(sys.argv) < 2:
        print("用法: python tool_factory.py <spec.json|prompt.txt|自然语言描述>")
        print('  spec: {"name":"json_cleaner","description":"清洗JSON数据","inputs":["raw.json"],"outputs":["clean.json"]}')
        sys.exit(1)

    arg = sys.argv[1]
    if arg.endswith(".json") and Path(arg).exists():
        spec = json.loads(Path(arg).read_text(encoding="utf-8"))
    elif arg.endswith(".txt") and Path(arg).exists():
        spec = Path(arg).read_text(encoding="utf-8").strip()
    else:
        spec = arg

    if isinstance(spec, dict) and "name" not in spec and "tool" not in spec and "description" not in spec:
        print("错误: 结构化 spec 至少需要 name、tool 或 description")
        sys.exit(2)
    if isinstance(spec, str) and not spec.strip():
        print("错误: 自然语言描述不能为空")
        sys.exit(2)

    factory = ToolFactory(spec)
    result = factory.forge()

    for filename, content in result["files"].items():
        target = Path(filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    print("=" * 55)
    print("神机百炼 · 智能锻造报告 V6.5")
    print("=" * 55)
    print(f"  器名: {result['tool_name']}")
    print(f"  产物类型: {result['artifact_type']}")
    print(f"  锻造模式: {result['forge_mode']}")
    print(f"  锻造意图: {result['forge_intent']}")
    print(f"  匹配模板: {result['template_matched']}")
    print(f"  产出文件:")
    for fname in result["files"]:
        print(f"    • {fname}")
    print("-" * 55)
    print("契约文档预览:")
    contract_name = f"{result['tool_name'].replace('-', '_').lower()}.contract.md"
    if contract_name in result["files"]:
        contract_lines = result["files"][contract_name].split("\n")
        for line in contract_lines[:15]:
            print(f"  {line}")
        print("  ...")
    print("=" * 55)
    print("V6.5智能锻造完成 - 自然语言锻造 + 专精骨架生成")


if __name__ == "__main__":
    main()
