# Parameters
PROJECT            = infrastructure-template
ENV_FILE           = .env
EMPTY_ENV_FILE     = .env.empty
COMPOSE_SERVICE   ?= pulumi
PULUMI_DIR        ?= pulumi
EFFECTIVE_ENV_FILE := $(firstword $(wildcard $(ENV_FILE)) $(wildcard $(EMPTY_ENV_FILE)))

COMPOSE_ENV_FILE := $(if $(EFFECTIVE_ENV_FILE),$(EFFECTIVE_ENV_FILE),$(EMPTY_ENV_FILE))
UID ?= $(shell id -u 2>/dev/null || echo 1000)
GID ?= $(shell id -g 2>/dev/null || echo 1000)
USER ?= $(shell id -un 2>/dev/null || echo dev)

export UID
export GID
export USER

# Executables
DOCKER_COMPOSE    = docker compose
COMPOSE_ENV_FLAG  = $(if $(COMPOSE_ENV_FILE),--env-file $(COMPOSE_ENV_FILE),)
COMPOSE           = $(DOCKER_COMPOSE) $(COMPOSE_ENV_FLAG)
PULUMI_CWD_FLAG   = --cwd $(PULUMI_DIR)
COVERAGE_OPTS            ?= --cov=./pulumi --cov-report=term-missing
UNIT_COVERAGE_OPTS       ?= $(COVERAGE_OPTS) --cov-fail-under=100
INTEGRATION_COVERAGE_ENV  = -e COVERAGE_FILE=/workspace/.coverage.integration \
	-e COVERAGE_PROCESS_START=/workspace/.coveragerc \
	-e COVERAGE_RCFILE=/workspace/.coveragerc

# Misc
.DEFAULT_GOAL     = help
.RECIPEPREFIX    +=
.PHONY: help build start pulumi-preview pulumi-up pulumi-refresh pulumi-destroy \
        sh down ci test-quality test-ruff test-ty test-unit test-integration \
        test-pulumi test-mutation test-cli test all clean

all: help ## Display help (default goal).

help:
	@printf "\033[33mUsage:\033[0m\n  make [target] [arg=\"val\"...]\n\n\033[33mTargets:\033[0m\n"
	@grep -E '^[-a-zA-Z0-9_\.\/]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[32m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build the Pulumi development image used by local and CI checks.
	$(COMPOSE) build $(COMPOSE_SERVICE)

start: ## Initialize and start the Pulumi development environment.
	$(COMPOSE) up -d

pulumi-preview: ## Preview infrastructure changes from inside the Pulumi container.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) pulumi $(PULUMI_CWD_FLAG) preview

pulumi-up: ## Apply the current Pulumi infrastructure plan.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) pulumi $(PULUMI_CWD_FLAG) up

pulumi-refresh: ## Sync the Pulumi stack with live cloud resources.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) pulumi $(PULUMI_CWD_FLAG) refresh

pulumi-destroy: ## Tear down the Pulumi stack (irreversible; use with caution).
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) pulumi $(PULUMI_CWD_FLAG) destroy

sh: ## Open a shell inside the Pulumi container.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) sh

down: ## Stop the Docker Compose environment.
	$(DOCKER_COMPOSE) down

test-unit: ## Execute fast unit tests for the Pulumi application layer.
	$(COMPOSE) run --rm -e PYTEST_ADDOPTS="$(UNIT_COVERAGE_OPTS)" \
		$(COMPOSE_SERVICE) uv run pytest -q tests/unit

test-integration: ## Execute Pulumi automation-based integration tests.
	$(COMPOSE) run --rm $(INTEGRATION_COVERAGE_ENV) \
		$(COMPOSE_SERVICE) uv run pytest -q tests/integration
	$(COMPOSE) run --rm -e COVERAGE_FILE=/workspace/.coverage.integration \
		-e COVERAGE_RCFILE=/workspace/.coveragerc \
		$(COMPOSE_SERVICE) uv run coverage combine
	$(COMPOSE) run --rm -e COVERAGE_FILE=/workspace/.coverage.integration \
		-e COVERAGE_RCFILE=/workspace/.coveragerc \
		$(COMPOSE_SERVICE) uv run coverage report --show-missing

test-pulumi: ## Perform structural checks on Pulumi project configuration.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) uv run pytest -q tests/pulumi

test-ruff: ## Run Ruff lint and format checks against Python sources.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) uv run ruff check pulumi tests
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) uv run ruff format --check pulumi tests

test-ty: ## Run the Ty static type checker against Python sources.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) uv run ty check \
		--ignore missing-argument \
		--ignore invalid-argument-type \
		--ignore conflicting-declarations \
		pulumi

test-quality: ## Run Rust-based Python quality gates.
	$(MAKE) test-ruff
	$(MAKE) test-ty

test-mutation: ## Run mutation testing suite against Pulumi components.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) bash -lc "./scripts/run_mutation_tests.sh"

test-cli: ## Validate Makefile front-ends via Bats.
	COMPOSE_TARGET=test $(COMPOSE) run --build --rm $(COMPOSE_SERVICE) bats tests/unit

test: ## Run the faster developer battery without the image build or mutation suite.
	$(MAKE) test-pulumi
	$(MAKE) test-quality
	$(MAKE) test-unit
	$(MAKE) test-integration
	$(MAKE) test-cli

ci: ## Run the full local equivalent of the pull-request CI battery.
	$(MAKE) build
	$(MAKE) test-pulumi
	$(MAKE) test-quality
	$(MAKE) test-unit
	$(MAKE) test-integration
	$(MAKE) test-mutation
	$(MAKE) test-cli

clean: ## Remove Docker Compose artifacts, Python caches, and build artifacts.
	$(DOCKER_COMPOSE) down -v 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .venv dist build *.egg-info 2>/dev/null || true
