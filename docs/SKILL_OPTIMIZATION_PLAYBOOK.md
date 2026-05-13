# Skill Optimization Playbook

这份手册面向人和 Agent，目标只有一个：**一次只优化一个 skill，且每一步都能复现**。

## 稳定 ID

| Stable ID | Source Dir | First Focus |
|---|---|---|
| `qiti-yuanliu` | `underone/skills/qiti-yuanliu` | 上下文漂移、修复阈值 |
| `shuangquanshou` | `underone/skills/shuangquanshou` | 人设一致性、污染边界 |
| `liuku-xianzei` | `underone/skills/liuku-xianzei` | 可信度、保鲜期、消化率 |
| `tongtian-lu` | `underone/skills/tongtian-lu` | 任务拆解、冲突检测 |
| `fenghou-qimen` | `underone/skills/fenghou-qimen` | 排序权重、鲁棒性 |
| `dalu-dongguan` | `underone/skills/dalu-dongguan` | 关联质量、幻觉拦截 |
| `juling-qianjiang` | `underone/skills/juling-qianjiang` | 调度可靠性、降级策略 |
| `shenji-bailian` | `underone/skills/shenji-bailian` | 生成产物质量、测试脚手架 |
| `bagua-zhen` | `underone/skills/bagua-zhen` | 互斥矩阵、生态仲裁 |
| `xiushen-lu` | `underone/skills/xiushen-lu` | 自进化阈值、回滚保护 |

## 单 skill 优化循环

```bash
# 1. 只看这个 skill 的定义是否稳定
cd underone
python -m under_one.cli audit priority-engine --json

# 2. 只验证这个 skill 的行为输出
python -m under_one.cli validate-skill priority-engine --json

# 3. 安装到隔离宿主目录，验证包装层
cd ..
python underone/scripts/install_host_skills.py --host qclaw --dest /tmp/underone-qclaw --skip-source-validation fenghou-qimen

# 4. 直接验证安装后的副本
python /tmp/underone-qclaw/fenghou-qimen/skillctl.py self-test
```

## 推荐优化顺序

1. `qiti-yuanliu`
2. `shuangquanshou`
3. `liuku-xianzei`
4. `tongtian-lu`
5. `fenghou-qimen`
6. `dalu-dongguan`
7. `juling-qianjiang`
8. `shenji-bailian`
9. `bagua-zhen`
10. `xiushen-lu`

## 每个 skill 看什么

- `qiti-yuanliu`：是否过度误报，是否把正常意图修正当成异常。
- `shuangquanshou`：是否误判合理风格变化，是否污染记忆。
- `liuku-xianzei`：摘要是否保留事实密度，是否低估有效信息。
- `tongtian-lu`：拆解步骤是否可执行，是否把冲突放大。
- `fenghou-qimen`：排序是否稳定，是否依赖主观打分过重。
- `dalu-dongguan`：是否过度联想，是否误把噪声当关联。
- `juling-qianjiang`：调度是否可降级，是否出现权责混乱。
- `shenji-bailian`：生成产物是否能独立运行，测试是否能复现。
- `bagua-zhen`：是否正确识别互斥和协同，是否误伤中央控制层。
- `xiushen-lu`：是否只在有数据时进化，是否具备回滚保护。

## 宿主安装

```bash
python underone/scripts/install_host_skills.py --host codex
python underone/scripts/install_host_skills.py --host workbuddy
python underone/scripts/install_host_skills.py --host qclaw
python underone/scripts/install_host_skills.py --host custom --dest /tmp/underone-custom
```

如果只想试一个 skill，就加上 skill 名：

```bash
python underone/scripts/install_host_skills.py --host codex fenghou-qimen
```

第三方类 OpenClaw 产品优先使用原生布局：

```bash
python underone/scripts/install_host_skills.py --host openclaw --dest /path/to/openclaw/skills fenghou-qimen
python underone/scripts/install_host_skills.py --host custom --dest /path/to/product/skills fenghou-qimen
python /path/to/product/skills/fenghou-qimen/skillctl.py self-test
```
