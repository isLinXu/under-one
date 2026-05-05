# Contributing to under-one.skills

感谢你对 under-one.skills 的兴趣！无论你是想修复Bug、提交新Skill，还是改进修身炉的自进化算法，这篇指南将帮助你快速融入我们的协作流程。

## 项目理念

本项目以《一人之下》八奇技为世界观灵感，目标是打造**生产级的 Agent Skill 增强框架**。所有贡献应遵循以下原则：

1. **效果优先** — 每个Skill必须有可量化的效果提升验证
2. **世界观尊重** — 借鉴设定而非抄袭，保持文化内涵
3. **向后兼容** — V10接口已稳定，不接受破坏性变更
4. **副作用是彩蛋** — 副作用系统仅作为世界观提醒，不得影响功能

## 贡献方式

### 方式一：提交Bug报告

使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.md) 创建Issue，请确保包含：
- 复现步骤（最小化示例）
- 预期 vs 实际行为
- 运行环境（`under-one status` 输出）
- 相关日志

### 方式二：提交功能请求

使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.md) 创建Issue，请说明：
- 功能的应用场景
- 与现有Skill的关系（协同/独立/冲突）
- 预期效果量化指标

### 方式三：提交代码（PR）

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature-name`
3. 提交变更（遵循提交信息规范，见下方）
4. 确保测试通过：`pytest tests/`
5. 更新相关文档
6. 提交 Pull Request

## 开发环境搭建

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/under-one.skills.git
cd under-one.skills

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 可编辑安装
pip install -e ".[dev]"

# 4. 验证环境
under-one status
pytest tests/
```

## 项目结构

```
under-one.skills/
├── qiti-yuanliu/          # 炁体源流 - 稳态自愈
├── tongtian-lu/           # 通天箓 - 指令工厂
├── dalu-dongguan/         # 大罗洞观 - 洞察雷达
├── shenji-bailian/        # 神机百炼 - 工具锻造
├── fenghou-qimen/         # 风后奇门 - 优先级引擎
├── liuku-xianzei/         # 六库仙贼 - 知识消化
├── shuangquanshou/        # 双全手 - 人格守护
├── juling-qianjiang/      # 拘灵遣将 - 工具调度
├── bagua-zhen/            # 八卦阵 - 中央协调器
├── xiushen-lu/            # 修身炉 - 自进化引擎
├── under_one/             # Python SDK
├── tests/                 # 测试套件
├── demo.py                # 5分钟演示
└── under-one.yaml         # 全局配置
```

## 提交信息规范

采用 `类型: 简短描述` 的格式：

| 类型 | 含义 | 示例 |
|------|------|------|
| `skill` | Skill变更 | `skill: 优化炁体源流稳态检测阈值` |
| `core` | 核心SDK/CLI变更 | `core: CLI添加--json输出格式` |
| `xiu` | 修身炉变更 | `xiu: 新增混合进化策略` |
| `test` | 测试相关 | `test: 补充风后奇门边界用例` |
| `docs` | 文档变更 | `docs: 更新API使用示例` |
| `fix` | Bug修复 | `fix: 修复八卦阵互斥矩阵误判` |
| `chore` | 工程杂项 | `chore: 升级依赖版本` |

## 测试规范

所有PR必须包含测试。测试文件命名：`test_<模块>.py`。

```python
# 最小Skill测试模板
def test_skill_name_scenario():
    """测试场景：xxx情况下，skill应该做yyy"""
    skill = SkillName()
    result = skill.run(input_data)
    assert result.expected_metric > THRESHOLD
```

### 新增Skill的PR需要：

1. **功能测试** — `tests/test_<skill>.py`（至少3个场景）
2. **集成测试** — 与八卦阵的协同测试
3. **量化验证** — A/B对照实验数据（baseline vs with-skill）
4. **世界观审查** — 符合八奇技设定的说明

## Skill开发指南

### 创建新Skill的步骤

1. 复制模板目录：`cp -r _template <skill-kebab-name>`
2. 编写 `SKILL.md`（遵循skill-creator规范）
3. 在 `under_one/__init__.py` 添加SDK类
4. 在 `under_one/cli.py` 注册子命令
5. 添加测试、更新文档
6. 打包验证：`under-one scan <skill-kebab-name>/`

### SKILL.md 写作规范

- Frontmatter必须包含：`name`, `description`, `version`
- 正文控制在3000-5000字
- 必须包含：原理、使用场景、配置参数、示例
- 可选包含：scripts/ 目录下的辅助脚本
- 不包含：README、安装指南、CHANGELOG

### 版本号规则

采用 SemVer + 文化版本：
- `v10.1.0` — 功能新增（如新增Skill）
- `v10.0.1` — Bug修复
- `v11.0.0` — 重大架构变更（需RFC讨论）

## 修身炉贡献特别说明

修身炉（xiushen-lu）是项目的核心差异化能力。如果你想贡献进化算法：

1. 在 `xiushen-lu/scripts/` 下实现新策略类
2. 继承 `BaseEvolutionStrategy`
3. 必须实现：`analyze()`, `evolve()`, `validate()` 三个方法
4. 提供 rollback 支持（进化失败可回退）
5. 在 `under-one.yaml` 注册新策略参数

## 社区行为准则

- 尊重不同技术背景贡献者
- 讨论聚焦技术本身，不评价文化偏好
- 帮助新手入门，耐心解答基础问题
- 禁止泄露真实《一人之下》未公开剧情作为skill设计

## 获取帮助

- 📖 文档：[README.md](README.md) | [FAQ.md](FAQ.md)
- 🐛 Bug报告：[Issue模板](.github/ISSUE_TEMPLATE/bug_report.md)
- 💡 功能请求：[Feature模板](.github/ISSUE_TEMPLATE/feature_request.md)
- 📧 维护者：@maintainer-team

---

**欢迎加入 under-one.skills，一起探索 Agent 能力的极限！**
