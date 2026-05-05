---
name: xiushen-lu
description: Agent self-evolution engine inspired by the XiuShenLu (修身炉) furnace from Hitori no Shita. Use when agent needs to evolve, optimize, or upgrade its own skills autonomously. Triggers include skill pe...
---

## V7 Features

- Self-evolution via XiuShenLu engine
- Runtime metrics export to adaptive thresholds
- Cross-skill knowledge sharing
- Deep parameter optimization
- Linkage protocol for multi-skill orchestration


# XiuShenLu (修身炉) - Agent Self-Evolution Engine

The XiuShenLu is the 10th core component of the under-one.skills framework, functioning as an autonomous self-evolution engine that enables skills to evolve, adapt, and improve based on runtime data. Modeled after Ma Xianhong's furnace that transforms ordinary people into extraordinary ones, this engine transforms static skills into living, learning capabilities.

## Core Architecture

```
XiuShenLu Engine
├── QiSource (炁源)      → Runtime data collection
├── Refiner (炼化器)      → Performance analysis & bottleneck detection
├── Transformer (转化器)  → Automatic skill parameter optimization
├── Core (核心)           → Evolution trigger & decision logic
└── Rollback (回退)       → Safe evolution with version control
```

## Evolution Triggers

Auto-trigger evolution when ANY of these conditions are met:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Success rate drops below baseline for 5 consecutive runs | < 85% | Trigger refinement |
| New task pattern detected (> 3 similar unknown tasks) | N/A | Extend skill coverage |
| Human intervention frequency increases | > 1 per 10 tasks | Parameter tuning |
| Execution time exceeds SLA by > 20% | > 120% SLA | Optimization |
| User explicitly requests improvement | N/A | Full evolution cycle |

## Evolution Cycle (进化周期)

```
1. COLLECT  → Gather execution metrics from all active skills
2. ANALYZE  → Compare current vs baseline performance
3. DECIDE   → Determine evolution type (tuning/extension/refactor)
4. EVOLVE   → Apply changes to skill parameters or logic
5. VALIDATE → Run test suite against evolved skill
6. DEPLOY   → Deploy if validation passes; rollback if fails
7. MONITOR  → Track evolved skill for next 10 runs
```

## Integration with Bagua-Zhen

XiuShenLu operates as a supervised process under Bagua-Zhen:

- Before evolution: Check mutex matrix (evolving skill vs active skills)
- During evolution: Report progress to Bagua-Zhen state bus
- After evolution: Update skill registry and broadcast new version

If Bagua-Zhen detects conflicts during evolution, XiuShenLu pauses and resolves:
- Mutual exclusion conflicts: Queue evolution for non-conflicting time window
- Resource conflicts: Reduce evolution batch size
- Dependency conflicts: Evolve in topological order

## Execution Mode

### Low-Risk Mode (低风险进化)
- Parameter tuning only (thresholds, weights, timeouts)
- Auto-deploy without human review
- Monitor for 10 runs

### Medium-Risk Mode (中风险进化)
- Logic extension (new branches, new keyword detection)
- Requires validation pass
- Monitor for 20 runs

### High-Risk Mode (高风险进化)
- Architecture refactor (new modules, protocol changes)
- Requires Bagua-Zhen approval
- Full test suite required before deploy

## Data Collection

XiuShenLu automatically collects these metrics per skill execution:

```json
{
  "skill_name": "qiti-yuanliu",
  "timestamp": "2026-04-30T12:00:00Z",
  "duration_ms": 600,
  "success": true,
  "quality_score": 95,
  "error_count": 0,
  "human_intervention": 0,
  "input_complexity": "medium",
  "output_completeness": 100,
  "consistency_score": 98
}
```

## Version Control

Every evolution creates a version snapshot:

- Format: `{skill_name}-v{major}.{minor}.{patch}`
- Major: Architecture change
- Minor: Logic extension
- Patch: Parameter tuning

Rollback available for last 5 versions.

## V6 Self-Evolution Hook (修身炉集成)

This skill integrates with the XiuShenLu (修身炉) self-evolution engine for autonomous improvement:

### Runtime Metrics Export
After each execution, the skill automatically reports these metrics to XiuShenLu:
- `duration_ms`: Execution time
- `success`: Task completion status
- `quality_score`: Output quality (0-100)
- `error_count`: Number of errors encountered
- `human_intervention`: Whether human correction was needed
- `output_completeness`: Coverage of requirements (%)
- `consistency_score`: Internal consistency (%)

### Evolution Triggers
When the following conditions are met, XiuShenLu may trigger automatic evolution:
- Success rate drops below 85% for 5 consecutive runs
- Human intervention frequency exceeds 0.1 per task
- Execution time exceeds SLA by 20%
- Quality score trend shows 3 consecutive decreases

### Integration Point
```python
# After skill execution, report metrics:
metrics = {
    "skill_name": "xiushen-lu",
    "duration_ms": execution_time,
    "success": success,
    "quality_score": quality,
    "error_count": errors,
    "human_intervention": human_needed,
    "output_completeness": completeness,
    "consistency_score": consistency
}
# XiuShenLu collects automatically via QiSource
```

### Version History
- v5.0: Base implementation with core functionality
- v5.1-v5.2: Bug fixes and edge case handling
- v6.0: XiuShenLu integration, self-evolution hooks, runtime metrics export

## V8 Features

- **Predictive Maintenance**: Trend analysis predicts degradation before it happens
- **A/B Testing**: Every evolution validated with control group + Welch's t-test
- **Intelligent Memory**: Vectorized experience storage with semantic retrieval
- **Federal Evolution**: Cross-agent evolution experience sharing
- **Safety Sandbox**: Isolated execution environment with permission controls

