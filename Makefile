.PHONY: clean audit audit-report evaluate-skills test coverage check bundles install bench status help

help:
	@echo "UnderOne · 常用命令"
	@echo ""
	@echo "  make audit     审计 10 个 skills 的结构、元数据与文档规范"
	@echo "  make audit-report  生成机器可读的 skills 审计报告（JSON）"
	@echo "  make evaluate-skills  运行 10 个 skills 的统一效果评估并生成报告"
	@echo "  make clean     清理临时产物（.DS_Store / __pycache__ / *.health_report.json 等）"
	@echo "  make test      运行 pytest 测试套件"
	@echo "  make coverage  运行测试并生成覆盖率报告（需要 pytest-cov）"
	@echo "  make check     运行默认质量门禁（audit + test + bundles --check）"
	@echo "  make bundles   重新构建 dist/ 下 10 个 .skill 分发包"
	@echo "  make bench     运行效能基准测试"
	@echo "  make install   pip install -e underone/"
	@echo "  make status    查看十技生态状态"

clean:
	find . -name ".DS_Store" -delete 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.health_report.json" -delete 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ 清理完成"

audit:
	cd underone && python -m under_one.cli audit

audit-report:
	mkdir -p underone/reports
	cd underone && python -m under_one.cli audit --json --output reports/skills-audit.json > reports/skills-audit.stdout.json

evaluate-skills:
	mkdir -p underone/reports
	python underone/scripts/evaluate_skills.py

test:
	cd underone && python -m pytest tests/ -v

coverage:
	cd underone && python -m pytest tests/ \
		--cov=under_one \
		--cov-report=term-missing \
		--cov-report=html:htmlcov

check: audit test
	cd underone && python scripts/build_skill_bundles.py --check

bundles:
	cd underone && python scripts/build_skill_bundles.py

bench:
	cd underone && python examples/efficiency_benchmark.py

install:
	cd underone && pip install -e .

status:
	cd underone && python -m under_one.cli status
