---
metadata:
  name: "juling-qianjiang"
  version: "9.0"
  author: "under-one"
  description: "拘灵遣将 - 多工具调度器（灵体调度）"
  language: "zh"
  tags: ["dispatch", "tool-orchestration", "fallback", "resilience"]
  icon: "🐺"
  color: "#a5d6ff"
---

# 拘灵遣将 (Juling-Qianjiang)

## 触发词
- 工具调度
- 多工具协调
- 降级保护
- 服灵模式
- 百鬼夜行
- 工具编排

## 用途
多工具调度与健康监控，工具不可用时执行降级保护（跳过/模拟/缓存），可选服灵模式内化生成替代实现。

## 输入
JSON任务列表 + 工具（灵体）列表：
```bash
python scripts/dispatcher.py <tasks.json> <spirits.json> [strategy:protect|possess]
```

## 输出
JSON调度报告：
```json
{
  "plan": [
    {"task": "...", "status": "dispatched", "assigned": "tool_1", "quality": 100}
  ],
  "fallback_log": [],
  "fallback_count": 0,
  "avg_quality": 95.0,
  "all_success": true
}
```

## 调度策略
| 策略 | 说明 |
|------|------|
| protect | 降级保护（默认）：工具不可用时跳过/模拟/缓存 |
| possess | 强制服灵：工具不可用时内化替代实现 |

## 降级方法
| 能力 | protect | possess |
|------|---------|---------|
| search | cached_search (0.7) | local_knowledge_search (0.85) |
| browse | mock_fetch (0.5) | cached_fetch (0.8) |
| code | local_fallback (0.6) | local_execution (0.9) |
| data | stale_data (0.4) | mock_response (0.75) |

## 用法
```bash
python scripts/dispatcher.py tasks.json spirits.json protect
```

## 依赖
- Python 3.8+
- 无外部依赖
