.PHONY: help install test lint typecheck run clean cov

help:
	@echo "HermesDM - available commands:"
	@echo "  make install    Install dependencies"
	@echo "  make test       Run tests"
	@echo "  make cov       Run tests with coverage report"
	@echo "  make lint       Run ruff linter"
	@echo "  make typecheck  Run mypy type checker"
	@echo "  make run        Start the Telegram bot"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -e ".[dev]"

test:
	PYTHONPATH="" python3 -m pytest tests/ -v

cov:
	PYTHONPATH="" python3 -m pytest tests/ --cov=bot --cov=dm --cov=state --cov-report=term-missing --cov-fail-under=80

lint:
	PYTHONPATH="" ruff check bot dm state

typecheck:
	PYTHONPATH="" mypy bot dm state

run:
	PYTHONPATH="" python3 -m bot.telegram_handler

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
