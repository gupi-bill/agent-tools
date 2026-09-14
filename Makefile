.PHONY: test lint format install dev clean

install:
	pip install -e ".[dev]"

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=agent_tools --cov-report=term-missing --cov-report=html

lint:
	python -m py_compile agent_tools/*.py agent_tools/cmd/*.py

format:
	black agent_tools/ tests/

clean:
	rm -rf build/ dist/ *.egg-info agent_tools.egg-info __pycache__ agent_tools/__pycache__ agent_tools/cmd/__pycache__ tests/__pycache__ .pytest_cache

publish: test lint
	python -m build
	python -m twine upload dist/*