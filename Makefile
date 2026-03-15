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

.PHONY: pre-commit-run pre-commit-install pre-commit-update lint format test run
## @ Development
pre-commit-run: ## Run pre-commit hooks
	@uv run prek run --all-files

pre-commit-install: ## Install pre-commit hooks
	@uv run prek install
	@uv run prek install --hook-type commit-msg

pre-commit-update: ## Update pre-commit hooks
	@uv run prek autoupdate

lint: ## Run linters
	@uv run ruff check .

format: ## Run code formatters
	@uv run ruff format
	@uv run isort .

test: ## Run pytest with coverage
	@uv run pytest --cov=src --cov-report=term-missing

run: ## Run the application locally
	@uv run python -m src.main

apply-kustomize: ## Apply kustomize applications to cluster
	@kubectl apply -f tests/integration/kustomize/applications

apply-helm: ## Apply helm applications to cluster
	@kubectl apply -f tests/integration/helm/applications

clean: ## Clean build artifacts and caches
	@rm -rf dist build *.egg-info
	@rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage
	@rm -rf tmp/
	@rm -rf logs/*.log
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

.PHONY: grafana-vm-ui grafana-vm-password grafana-ui grafana-password prometheus-ui vm-ui
##@ Observability
grafana-vm-ui: ## Access grafana ui
	@kubectl port-forward svc/victoria-metrics-k8s-stack-grafana -n monitoring 3000:80

grafana-vm-password: ## Get grafana password
	@kubectl get secret -n monitoring victoria-metrics-k8s-stack-grafana -o jsonpath="{.data.admin-password}" | base64 --decode; echo

grafana-ui: ## Access grafana ui
	@kubectl port-forward svc/kube-prometheus-stack-grafana -n monitoring 3000:80

grafana-password: ## Get grafana password (default: prom-operator)
	@kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 --decode; echo

prometheus-ui: ## Access prometheus ui
	@kubectl port-forward svc/kube-prometheus-stack-prometheus -n monitoring 9090:9090

vm-ui: ## Access victoria metrics ui
	@kubectl port-forward svc/vmsingle-victoria-metrics-k8s-stack -n monitoring 8429:8429

.PHONY: argo-cd-password argo-cd-ui argo-cd-login argo-cd-apps
## @ Argo CD
argo-cd-password: ## Get Argo CD initial admin password
	@kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo

argo-cd-ui: ## Access argocd ui
	@kubectl port-forward svc/argocd-server -n argocd 8088:443

argo-cd-login: ## Login to argocd
	@argocd login --insecure localhost:8088 --username admin --password $(shell kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

argo-cd-apps: ## List argocd apps
	@argocd app list

.PHONY: bump-version bump-preview
##@ Release
bump-version: ## Bump project version
	@uv run cz bump

bump-preview: ## Preview next version and changelog (dry-run)
	@uv run cz bump --get-next
	@uv run cz changelog --dry-run
