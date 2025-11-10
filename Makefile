# Parameters
PROJECT            = infrastructure-template
ENV_FILE           = .env
COMPOSE_SERVICE   ?= pulumi

# Executables
DOCKER_COMPOSE    = docker compose

# Misc
.DEFAULT_GOAL     = help
.RECIPEPREFIX    +=
.PHONY: $(filter-out vendor node_modules,$(MAKECMDGOALS))

help:
	@printf "\033[33mUsage:\033[0m\n  make [target] [arg=\"val\"...]\n\n\033[33mTargets:\033[0m\n"
	@grep -E '^[-a-zA-Z0-9_\.\/]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[32m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Initialize and start the Pulumi development environment.
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) up -d

pulumi-preview: ## Preview infrastructure changes from inside the Pulumi container.
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) run --rm $(COMPOSE_SERVICE) pulumi preview

pulumi-up: ## Apply the current Pulumi infrastructure plan.
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) run --rm $(COMPOSE_SERVICE) pulumi up

pulumi-refresh: ## Sync the Pulumi stack with live cloud resources.
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) run --rm $(COMPOSE_SERVICE) pulumi refresh

pulumi-destroy: ## Tear down the Pulumi stack (irreversible; use with caution).
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) run --rm $(COMPOSE_SERVICE) pulumi destroy

sh: ## Open a shell inside the Pulumi container.
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) run --rm $(COMPOSE_SERVICE) sh

down: ## Stop the Docker Compose environment.
	$(DOCKER_COMPOSE) down
