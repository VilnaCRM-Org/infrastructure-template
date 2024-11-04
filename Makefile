# Parameters
PROJECT        = infrastructure-template
ENV_FILE       = .env

# Executables
PULUMI         = pulumi

# Misc
.DEFAULT_GOAL  = help
.RECIPEPREFIX  +=
.PHONY: $(filter-out vendor node_modules,$(MAKECMDGOALS))

help:
	@printf "\033[33mUsage:\033[0m\n  make [target] [arg=\"val\"...]\n\n\033[33mTargets:\033[0m\n"
	@grep -E '^[-a-zA-Z0-9_\.\/]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[32m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Docker container with terraspace and terraform
	pulumi login --local && pulumi install && pulumi up
