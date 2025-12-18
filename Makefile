.PHONY: all test coverage coverage-html lint format format-check typecheck \
		build check publish publish-test clean

all: test

test:
	@echo "running tests"
	@uv run pytest

coverage:
	@echo "generating test coverage report"
	@uv run pytest --cov-report=term-missing --cov=buildgen tests

coverage-html:
	@echo "generating test coverage report"
	@uv run pytest --cov-report=html:cov_html --cov-report=term-missing --cov=buildgen tests

# Linting and formatting
lint:
	@echo "running ruff check"
	@uv run ruff check src tests

format:
	@echo "formatting code with ruff"
	@uv run ruff format src tests

format-check:
	@echo "checking code formatting"
	@uv run ruff format --check src tests

typecheck:
	@echo "running type checkers"
	@uv run mypy src

# Build and publish
build:
	@echo "building distribution"
	@uv build

check: build
	@echo "checking distribution with twine"
	@uv run twine check dist/*

publish: check
	@echo "publishing to PyPI"
	@uv run twine upload dist/*

publish-test: check
	@echo "publishing to TestPyPI"
	@uv run twine upload --repository testpypi dist/*

clean:
	@find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf
	@rm -rf .pytest_cache
	@rm -rf .coverage cov_html
	@rm -rf dist build *.egg-info
