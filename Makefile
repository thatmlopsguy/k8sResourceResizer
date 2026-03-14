IMAGE ?= k8sresourceautoresizer
VERSION ?= latest
DOCKERFILE ?= Dockerfile
DOCKER_BUILD_ARGS ?= --no-cache

.PHONY: help
##@ General
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: \033[36m\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: docker-build
##@ Docker
docker-build: ## Build Docker image locally
	@docker build $(DOCKER_BUILD_ARGS) -t $(IMAGE):$(VERSION) -f $(DOCKERFILE) .

## @ Development
.PHONY: pre-commit-run pre-commit-install pre-commit-update
pre-commit-run: ## Run pre-commit hooks
	@uv run prek run --all-files

pre-commit-install: ## Install pre-commit hooks
	@uv run prek install

pre-commit-update: ## Update pre-commit hooks
	@uv run prek autoupdate
