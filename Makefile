PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.DEFAULT_GOAL := help
.PHONY: help setup lint validate index index-check evals test ruff skillsaw site clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Install dev dependencies
	$(PIP) install -q -r requirements-dev.txt

lint: validate index-check evals test ruff ## Everything CI runs

ruff: ## Lint matching CI (astral-sh/ruff defaults)
	$(PYTHON) -m ruff check --output-format concise .

skillsaw: ## Local skillsaw lint (CI runs it via the action)
	uvx skillsaw@0.22.0 lint .

validate: ## Validate all skills (spec + house rules)
	$(PYTHON) scripts/validate_skills.py

index: ## Regenerate README skill table + site-data/skills.json
	$(PYTHON) scripts/generate_index.py

index-check: ## CI mode: fail if README index is stale
	$(PYTHON) scripts/generate_index.py --check

evals: ## Structural validation of eval suites
	$(PYTHON) scripts/check_evals.py

test: ## Run the tooling test suite
	$(PYTHON) -m pytest tests/ -q

site: ## Build the docs site into _site/
	$(PYTHON) docs/build_site.py

clean: ## Remove build/test artifacts
	rm -rf .pytest_cache site-data _site tests/__pycache__ scripts/__pycache__
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
