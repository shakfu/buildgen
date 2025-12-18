.PHONY: all web test coverage coverage-html clean

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

clean:
	@find . | grep -E "(__pycache__|\.pyc|\.pyo$/)" | xargs rm -rf
	@rm -rf .pytest_cache
	@rm -rf .coverage cov_html
	@rm -rf dist build


