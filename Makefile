.PHONY: clean test coverage bundles install bench status help

help:
	@echo "UnderOne · 常用命令"
	@echo ""
	@echo "  make clean     清理临时产物（.DS_Store / __pycache__ / *.health_report.json 等）"
	@echo "  make test      运行 pytest 测试套件"
	@echo "  make coverage  运行测试并生成覆盖率报告（需要 pytest-cov）"
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

test:
	cd underone && python -m pytest tests/ -v

coverage:
	cd underone && python -m pytest tests/ \
		--cov=under_one \
		--cov-report=term-missing \
		--cov-report=html:htmlcov

bundles:
	cd underone && python scripts/build_skill_bundles.py

bench:
	cd underone && python examples/efficiency_benchmark.py

install:
	cd underone && pip install -e .

status:
	cd underone && python -m under_one.cli status
