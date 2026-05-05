---
metadata:
  name: "dalu-dongguan"
  version: "5.0"
  author: "under-one"
  description: "大罗洞观 - 关联检测器（全局洞察）"
  language: "zh"
  tags: ["link-detection", "knowledge-graph", "entity-extraction", "insight"]
  icon: "🔭"
  color: "#d2a8ff"
---

# 大罗洞观 (DaLu-DongGuan)

## 触发词
- 检测关联
- 知识图谱
- 实体提取
- 关联分析
- 文本关联
- Mermaid图谱

## 用途
从多段文本中检测语义关联、共现实体、时序关系和因果关系，输出关联图谱和Mermaid可视化代码。

## 输入
JSON段落列表：
```json
[
  {"source": "A段", "content": "文本内容..."},
  {"source": "B段", "content": "相关文本..."}
]
```

## 输出
JSON关联报告：
```json
{
  "links": [
    {"source": "A段", "target": "B段", "type": "语义关联", "strength": 0.65}
  ],
  "entity_map": {"实体名": ["A段", "B段"]},
  "knowledge_graph": {"nodes": [...], "edges": [...]},
  "mermaid_code": "graph TD\n..."
}
```

## 关联类型
| 类型 | 检测方式 | 置信度权重 |
|------|----------|-----------|
| 语义关联 | Jaccard相似度 > 0.3 | 30% |
| 实体共现 | 同一实体多段出现 | 25% |
| 时序关联 | 时间标记词 | 20% |
| 因果关系 | 因果标记词 | 10% |
| 来源一致性 | - | 15% |

## 用法
```bash
python scripts/link_detector.py <segments.json>
```

## 依赖
- Python 3.8+
- 无外部依赖
