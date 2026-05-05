# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v10.0.0] - 2025-05-03

### Added - 八奇技完整版

- **炁体源流 (qiti-yuanliu)** — 稳态自愈引擎，Agent状态实时监控与自动修复
- **通天箓 (tongtian-lu)** — 结构化指令工厂，统一Prompt生成与版本管理
- **大罗洞观 (dalu-dongguan)** — 多维洞察雷达，任务执行全过程追踪与瓶颈识别
- **神机百炼 (shenji-bailian)** — 工具锻造系统，面向任务的专用工具生成与测试
- **风后奇门 (fenghou-qimen)** — 动态优先级引擎，多任务自适应调度与资源分配
- **六库仙贼 (liuku-xianzei)** — 知识消化管道，六阶段知识吸收与结构化沉淀
- **双全手 (shuangquanshou)** — 人格守护系统，Agent行为一致性校验与价值观对齐
- **拘灵遣将 (juling-qianjiang)** — 工具调度系统，protect/possess双模式工具管理
- **八卦阵 (bagua-zhen)** — 中央协调器，八奇技互斥管理、状态聚合与协同调度
- **修身炉 (xiushen-lu)** — 自进化引擎，Agent与Skill的自动化迭代优化

### Added - 工程体系

- Python SDK (`under_one`) — 10个Skill的完整Python封装
- 统一CLI (`under-one`) — list/scan/status/evolve 四命令
- pip installable 包 (`pip install under-one-skills`)
- 全局配置文件 (`under-one.yaml`) — 阈值/关键词/策略参数
- pytest 测试套件 (7/7 通过)
- GitHub Actions CI 配置
- MIT License + 文化声明
- CONTRIBUTING.md / Issue模板 / PR模板

### Added - 量化验证

- A/B对照实验框架 (Welch's t-test + Cohen's d)
- 效率量化报告 (EFFICIENCY_QUANTIFICATION_REPORT.md)
- 基准测试脚本 (efficiency_benchmark.py)

### Added - 自进化验证

- 修身炉端到端验证通过
- Universal XiuShenLu策略模式（Code/Instruction/Hybrid）
- 五模块架构：QiSource/Refiner/Transformer/Core/Rollback
- 对任意Skill和agent.md通用

### Fixed - 世界观契合度

- 拘灵遣将："强制吞噬"改为protect(默认)/possess双模式
- 副作用系统：从惩罚机制改为纯世界观彩蛋提醒
- 六库仙贼：六阶段消化管道具象化（胃→小肠→大肠→胆→膀胱→三焦）
- 大罗洞观：增加"观测者"视角与因果追踪

## [v9.0.0] - 2025-05-02

### Changed

- V9版本全面优化：配置标准化、接口统一化
- 八卦阵中央协调器重构
- 修身炉策略模式引入

## [v8.0.0] - 2025-05-02

### Added

- 副作用世界观彩蛋系统（可选提醒）
- 拘灵遣将possess模式
- 世界观契合度审查报告

## [v7.0.0] - 2025-05-02

### Added

- 修身炉Universal模式（对任意Skill通用）
- 端到端自进化验证

## [v1.0-v6.0] - 2025-05-01

### Evolution

- V1: 基础八奇技概念映射
- V2: SKILL.md规范适配
- V3: 场景测试用例补充
- V4: 量化验证框架
- V5: 修身炉控制自进化
- V6: 世界观P0问题修复
