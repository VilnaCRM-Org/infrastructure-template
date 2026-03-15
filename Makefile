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
GITHUB_TOKEN ?= $(shell gh auth token 2>/dev/null)

export UID
export GID
export USER
export GITHUB_TOKEN

# Executables
DOCKER_COMPOSE    = docker compose
COMPOSE_ENV_FLAG  = $(if $(COMPOSE_ENV_FILE),--env-file $(COMPOSE_ENV_FILE),)
COMPOSE           = $(DOCKER_COMPOSE) $(COMPOSE_ENV_FLAG)
PULUMI_CWD_FLAG   = --cwd $(PULUMI_DIR)
POLICY_PACK_DIR   = /workspace/policy
POLICY_PACK_FLAG  = --policy-pack $(POLICY_PACK_DIR)
DEFAULT_PULUMI_STACK ?= $(shell find $(PULUMI_DIR) -maxdepth 1 -type f -name 'Pulumi.*.yaml' ! -name 'Pulumi.yaml' -printf '%f\n' 2>/dev/null | sed -E 's/^Pulumi\.(.+)\.yaml$$/\1/' | sort | head -n 1)
PULUMI_STACK     ?= $(DEFAULT_PULUMI_STACK)
PULUMI_LOGIN_CMD  = export PULUMI_CONFIG_PASSPHRASE="$${PULUMI_CONFIG_PASSPHRASE-}"; \
	pulumi $(PULUMI_CWD_FLAG) login "$${PULUMI_BACKEND_URL:-file:///workspace/.pulumi-backend}" >/dev/null
COVERAGE_OPTS            ?= --cov=./pulumi --cov-report=term-missing
UNIT_COVERAGE_INCLUDE    ?= pulumi/*,scripts/*
UNIT_COVERAGE_OPTS       ?= $(COVERAGE_OPTS) --cov=./scripts
POLICY_COVERAGE_OPTS     ?= --cov=./policy --cov-report=
INTEGRATION_COVERAGE_INCLUDE ?= pulumi/__main__.py,pulumi/app/*
INTEGRATION_COVERAGE_ENV  = -e COVERAGE_FILE=/workspace/.coverage.integration \
	-e COVERAGE_PROCESS_START=/workspace/.coveragerc \
	-e COVERAGE_RCFILE=/workspace/.coveragerc
UNIT_COVERAGE_ENV         = -e COVERAGE_FILE=/workspace/.coverage.unit \
	-e COVERAGE_RCFILE=/workspace/.coveragerc
POLICY_COVERAGE_ENV       = -e COVERAGE_FILE=/workspace/.coverage.policy \
	-e COVERAGE_RCFILE=/workspace/.coveragerc

# Misc
.DEFAULT_GOAL     = help
.RECIPEPREFIX    +=
.PHONY: help doctor build start pulumi-preview pulumi-up pulumi-refresh \
        pulumi-destroy sh down ci ci-pr test-quality test-ruff test-ty \
        test-actionlint test-deps-security test-destructive-diff test-drift \
        test-guardrails test-iam-validation test-preview test-security test-secrets \
        test-unit test-integration test-pulumi test-policy test-mutation \
        test-battery \
        test-cli test all clean

all: help ## Display help (default goal).

help:
	@printf "\033[33mUsage:\033[0m\n  make [target] [arg=\"val\"...]\n\n\033[33mTargets:\033[0m\n"
	@grep -E '^[-a-zA-Z0-9_\.\/]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[32m%-15s\033[0m %s\n", $$1, $$2}'

doctor: ## Check local prerequisites and effective paths without printing secrets.
	@set -eu; \
	if ! command -v docker >/dev/null 2>&1; then \
		echo "docker: missing" >&2; \
		exit 1; \
	fi; \
	if ! docker compose version >/dev/null 2>&1; then \
		echo "docker compose: missing" >&2; \
		exit 1; \
	fi; \
	printf "docker: %s\n" "$$(docker --version)"; \
	printf "docker compose: %s\n" "$$(docker compose version --short)"; \
	printf "effective env file: %s\n" "$(COMPOSE_ENV_FILE)"; \
	printf "compose service: %s\n" "$(COMPOSE_SERVICE)"; \
	printf "pulumi directory: %s\n" "$(PULUMI_DIR)"; \
	if [ -f "$(COMPOSE_ENV_FILE)" ]; then \
		printf "env file present: yes\n"; \
	else \
		printf "env file present: no\n" >&2; \
		exit 1; \
	fi

build: ## Build the Pulumi development image used by local and CI checks.
	$(COMPOSE) build $(COMPOSE_SERVICE)

start: ## Initialize and start the Pulumi development environment.
	$(COMPOSE) up -d

pulumi-preview: ## Preview infrastructure changes from inside the Pulumi container.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) bash -lc '$(PULUMI_LOGIN_CMD); stack="$${PULUMI_STACK:-$(PULUMI_STACK)}"; if [ -z "$$stack" ]; then echo "error: set PULUMI_STACK or commit pulumi/Pulumi.<stack>.yaml" >&2; exit 1; fi; pulumi $(PULUMI_CWD_FLAG) stack select "$$stack" --create --non-interactive >/dev/null; ./scripts/prepare_policy_pack.sh && pulumi $(PULUMI_CWD_FLAG) preview --stack "$$stack" $(POLICY_PACK_FLAG)'

pulumi-up: ## Apply the current Pulumi infrastructure plan.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) bash -lc '$(PULUMI_LOGIN_CMD); stack="$${PULUMI_STACK:-$(PULUMI_STACK)}"; if [ -z "$$stack" ]; then echo "error: set PULUMI_STACK or commit pulumi/Pulumi.<stack>.yaml" >&2; exit 1; fi; pulumi $(PULUMI_CWD_FLAG) stack select "$$stack" --create --non-interactive >/dev/null; ./scripts/prepare_policy_pack.sh && pulumi $(PULUMI_CWD_FLAG) up --stack "$$stack" $(POLICY_PACK_FLAG)'

pulumi-refresh: ## Sync the Pulumi stack with live cloud resources.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) bash -lc '$(PULUMI_LOGIN_CMD); stack="$${PULUMI_STACK:-$(PULUMI_STACK)}"; if [ -z "$$stack" ]; then echo "error: set PULUMI_STACK or commit pulumi/Pulumi.<stack>.yaml" >&2; exit 1; fi; pulumi $(PULUMI_CWD_FLAG) stack select "$$stack" --create --non-interactive >/dev/null; pulumi $(PULUMI_CWD_FLAG) refresh --stack "$$stack"'

pulumi-destroy: ## Tear down the Pulumi stack (irreversible; use with caution).
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) bash -lc '$(PULUMI_LOGIN_CMD); stack="$${PULUMI_STACK:-$(PULUMI_STACK)}"; if [ -z "$$stack" ]; then echo "error: set PULUMI_STACK or commit pulumi/Pulumi.<stack>.yaml" >&2; exit 1; fi; pulumi $(PULUMI_CWD_FLAG) stack select "$$stack" --create --non-interactive >/dev/null; pulumi $(PULUMI_CWD_FLAG) destroy --stack "$$stack"'

sh: ## Open a shell inside the Pulumi container.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) sh

down: ## Stop the Docker Compose environment.
	$(DOCKER_COMPOSE) down

test-unit: ## Execute fast unit tests for the Pulumi application layer.
	rm -f .coverage.unit .coverage.unit.*
	$(COMPOSE) run --rm $(UNIT_COVERAGE_ENV) -e PYTEST_ADDOPTS="$(UNIT_COVERAGE_OPTS)" \
		$(COMPOSE_SERVICE) uv run pytest -q tests/unit
	$(COMPOSE) run --rm $(UNIT_COVERAGE_ENV) \
		$(COMPOSE_SERVICE) uv run coverage report --show-missing --include='$(UNIT_COVERAGE_INCLUDE)' --fail-under=100

test-integration: ## Execute Pulumi automation-based integration tests.
	rm -f .coverage.integration .coverage.integration.*
	$(COMPOSE) run --rm $(INTEGRATION_COVERAGE_ENV) \
		$(COMPOSE_SERVICE) uv run pytest -q tests/integration
	$(COMPOSE) run --rm -e COVERAGE_FILE=/workspace/.coverage.integration \
		-e COVERAGE_RCFILE=/workspace/.coveragerc \
		$(COMPOSE_SERVICE) uv run coverage combine
	$(COMPOSE) run --rm -e COVERAGE_FILE=/workspace/.coverage.integration \
		-e COVERAGE_RCFILE=/workspace/.coveragerc \
		$(COMPOSE_SERVICE) uv run coverage report --show-missing --fail-under=100 --include='$(INTEGRATION_COVERAGE_INCLUDE)'

test-pulumi: ## Perform structural checks on Pulumi project configuration.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) uv run pytest -q tests/pulumi

test-policy: ## Execute Pulumi policy-pack tests and guardrail coverage.
	rm -f .coverage.policy .coverage.policy.*
	$(COMPOSE) run --rm $(POLICY_COVERAGE_ENV) -e PYTEST_ADDOPTS="$(POLICY_COVERAGE_OPTS)" \
		$(COMPOSE_SERVICE) uv run pytest -q tests/policies
	$(COMPOSE) run --rm $(POLICY_COVERAGE_ENV) \
		$(COMPOSE_SERVICE) uv run coverage report --show-missing --include='policy/*' --fail-under=100

test-ruff: ## Run Ruff lint and format checks against Python sources.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) uv run ruff check pulumi policy scripts tests
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) uv run ruff format --check pulumi policy scripts tests

test-ty: ## Run the Ty static type checker against Python sources.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) uv run ty check \
		--extra-search-path policy \
		--ignore missing-argument \
		--ignore invalid-argument-type \
		--ignore conflicting-declarations \
		pulumi policy scripts

test-actionlint: ## Lint GitHub Actions workflows with actionlint.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) actionlint -color

test-secrets: ## Scan the working tree for accidentally committed secrets.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) gitleaks dir . --config .gitleaks.toml --no-banner --redact

test-deps-security: ## Audit Python dependencies for known vulnerabilities.
	$(COMPOSE) run --rm -e XDG_CACHE_HOME=/tmp/xdg-cache $(COMPOSE_SERVICE) uv run pip-audit --strict

test-preview: ## Generate non-destructive Pulumi previews for configured stacks.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) bash -lc "./scripts/run_pulumi_preview.sh"

test-destructive-diff: ## Fail when Pulumi previews delete or replace critical resources.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) bash -lc '\
		if ! compgen -G ".artifacts/pulumi-preview/*.json" >/dev/null; then \
			./scripts/run_pulumi_preview.sh >/dev/null; \
		fi; \
		uv run python ./scripts/pulumi_ci_guardrails.py destructive-gate .artifacts/pulumi-preview/*.json'

test-iam-validation: ## Validate previewed IAM policies with AWS IAM Access Analyzer.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) bash -lc '\
		if ! compgen -G ".artifacts/pulumi-preview/*.json" >/dev/null; then \
			./scripts/run_pulumi_preview.sh >/dev/null; \
		fi; \
		uv run python ./scripts/pulumi_ci_guardrails.py validate-iam .artifacts/pulumi-preview/*.json'

test-security: ## Run secret, dependency, and workflow security checks.
	$(MAKE) test-secrets
	$(MAKE) test-deps-security
	$(MAKE) test-actionlint

test-guardrails: ## Run preview, destructive diff, and IAM validation guardrails.
	$(MAKE) test-preview
	$(MAKE) test-destructive-diff
	$(MAKE) test-iam-validation

test-drift: ## Perform a non-destructive drift check against configured shared stacks.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) bash -lc "./scripts/run_pulumi_drift_check.sh"

test-quality: ## Run Rust-based Python quality gates.
	$(MAKE) test-ruff
	$(MAKE) test-ty

test-mutation: ## Run mutation testing suite against Pulumi components.
	$(COMPOSE) run --rm $(COMPOSE_SERVICE) bash -lc "./scripts/run_mutation_tests.sh"

test-cli: ## Validate Makefile front-ends via Bats.
	COMPOSE_TARGET=test $(COMPOSE) run --build --rm $(COMPOSE_SERVICE) bats tests/unit

test-battery:
	$(MAKE) test-pulumi
	$(MAKE) test-policy
	$(MAKE) test-quality
	$(MAKE) test-unit
	$(MAKE) test-integration
	$(MAKE) test-cli

test: ## Run the faster developer battery without the image build or mutation suite.
	$(MAKE) doctor
	$(MAKE) test-battery

ci-pr: ## Run the GitHub PR battery except the dedicated mutation workflow.
	$(MAKE) doctor
	$(MAKE) build
	$(MAKE) test-battery
	$(MAKE) test-security
	$(MAKE) test-guardrails

ci: ## Run the full local equivalent of all GitHub checks, including mutation.
	$(MAKE) ci-pr
	$(MAKE) test-mutation

clean: ## Remove Docker Compose artifacts, Python caches, and build artifacts.
	$(DOCKER_COMPOSE) down -v 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .venv dist build *.egg-info 2>/dev/null || true
